"""One interface in front of every folding model, and the gate it enforces.

`DESIGN.md` section 3 fixes the shape -- ``fold(sequence, target, seed, model)
-> FoldResult`` carrying coordinates, a per-metric confidence dict, wall time,
model id and weights checksum -- and gives the reason: the model stack is not
settled, and the Day-1 benchmark may force a substitution. Nothing downstream
should have to change when it does.

**No candidate is folded until G0 has passed it.** `DESIGN.md` section 8b
states this as an engineering constraint rather than a convention: a
geometrically invalid structure is not a cheap mistake to fold, it is a wasted
GPU-hour and a number in the results that means nothing. With 30 GPU-hours a
week and co-folding at 60-120 s a prediction, that is not a rounding error.
:func:`fold` refuses an unstamped design, and refuses one G0 rejected.

**Whether the objective has an input at all is decided here.**
`PROTOCOL.md` section 7.1 scores on "ipSAE or the model's equivalent", and
section 10 flags that this is unresolved: ipSAE is a derived quantity, and
Protenix or Boltz may emit PAE, pTM and ipTM without emitting ipSAE itself.
`SETUP.md` section 5 makes it the pass condition that decides the project --
ipSAE emitted directly, or a PAE matrix plus chain assignments so it can be
computed, and if neither then section 7.1 has no input and the plan changes
before Day 2. An adapter declares what it emits and
:func:`objective_has_an_input` applies that rule, so the decision is made by
code against a declaration rather than by recollection.
"""

import dataclasses
import enum
from collections.abc import Mapping, Sequence
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from counterscreen.core.design import Design, Gate


class FoldError(RuntimeError):
    """Raised when a fold cannot be run as specified."""


class ConfidenceMetric(enum.StrEnum):
    """Confidence quantities an adapter may emit.

    ``PAE_MATRIX`` means the full predicted-aligned-error matrix is available,
    not merely a summary of it. That distinction is the whole question in
    `SETUP.md` section 5: ipSAE is derivable from the matrix plus chain
    assignments, and not from a scalar.
    """

    IPSAE = "ipsae"
    IPTM = "iptm"
    PTM = "ptm"
    PLDDT = "plddt"
    PAE_MATRIX = "pae_matrix"
    CHAIN_ASSIGNMENTS = "chain_assignments"


#: What section 7.1's objective needs: ipSAE directly, or the ingredients.
DERIVABLE_FROM = frozenset({ConfidenceMetric.PAE_MATRIX, ConfidenceMetric.CHAIN_ASSIGNMENTS})


def objective_has_an_input(emits: frozenset[ConfidenceMetric]) -> bool:
    """Whether a model's output can feed the specificity margin.

    The pass condition of `SETUP.md` section 5. If this is false for every
    model in the stack, `PROTOCOL.md` section 7.1 has nothing to score and the
    plan must change before Day 2 rather than be worked around.
    """
    return ConfidenceMetric.IPSAE in emits or emits >= DERIVABLE_FROM


@dataclasses.dataclass(frozen=True, slots=True)
class FoldResult:
    """One prediction, with everything needed to reproduce and provenance it."""

    design_id: str
    target: str
    model: str
    model_weights_sha256: str
    seed: int
    coordinates: NDArray[np.float64]
    confidence: tuple[tuple[str, float], ...]
    chain_ids: tuple[str, ...]
    wall_time_s: float
    has_pae_matrix: bool = False

    def __post_init__(self) -> None:
        """Refuse a result that cannot be traced or trusted."""
        for name, value in (
            ("design_id", self.design_id),
            ("model", self.model),
            ("model_weights_sha256", self.model_weights_sha256),
        ):
            if not str(value).strip():
                msg = f"FoldResult needs a {name}; a prediction without one is untraceable"
                raise FoldError(msg)
        if self.wall_time_s < 0:
            msg = f"wall time cannot be negative, got {self.wall_time_s}"
            raise FoldError(msg)
        names = [metric for metric, _ in self.confidence]
        if len(set(names)) != len(names):
            msg = f"confidence repeats a metric: {names}"
            raise FoldError(msg)
        if list(names) != sorted(names):
            msg = "confidence metrics must be sorted; unsorted output is not reproducible"
            raise FoldError(msg)

    def value(self, metric: str) -> float:
        """One confidence value by name."""
        for name, number in self.confidence:
            if name == metric:
                return number
        msg = f"{metric!r} not emitted; have {[n for n, _ in self.confidence]}"
        raise FoldError(msg)


def confidence_from(values: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    """Freeze a confidence mapping into sorted pairs."""
    return tuple(sorted(values.items()))


class FoldAdapter(Protocol):
    """A folding model behind the common interface."""

    @property
    def name(self) -> str:
        """Adapter name, as registered."""
        ...

    @property
    def emits(self) -> frozenset[ConfidenceMetric]:
        """Confidence quantities this model actually produces."""
        ...

    def predict(self, design: Design, target: str, seed: int, /) -> FoldResult:
        """Run the model. Called only after G0 has passed the design."""
        ...


class AdapterRegistry:
    """Name to adapter, failing loudly on duplicates and unknowns.

    `build_rules.pdf` section 2.3: adding a model means registering one
    function, and duplicates and unknown keys fail with the list of valid
    names rather than silently doing the wrong thing.
    """

    def __init__(self) -> None:
        """Start empty."""
        self._adapters: dict[str, FoldAdapter] = {}

    def register(self, adapter: FoldAdapter) -> None:
        """Add an adapter, refusing a name already taken."""
        if adapter.name in self._adapters:
            msg = f"adapter {adapter.name!r} is already registered"
            raise FoldError(msg)
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> FoldAdapter:
        """Look up an adapter by name."""
        if name not in self._adapters:
            msg = f"unknown model {name!r}; registered: {sorted(self._adapters)}"
            raise FoldError(msg)
        return self._adapters[name]

    def names(self) -> tuple[str, ...]:
        """Every registered adapter name, sorted."""
        return tuple(sorted(self._adapters))

    def usable(self) -> tuple[str, ...]:
        """Adapters whose output can feed the section 7.1 objective."""
        return tuple(
            sorted(
                name
                for name, adapter in self._adapters.items()
                if objective_has_an_input(adapter.emits)
            )
        )


def require_g0(design: Design) -> None:
    """Refuse a design that G0 has not passed.

    `DESIGN.md` section 8b. The check is here, at the boundary of the
    expensive stage, rather than in the caller, because a caller that forgets
    it produces numbers that look ordinary and mean nothing.
    """
    stamp = design.verdict(Gate.G0)
    if stamp is None:
        msg = (
            f"design {design.design_id} has not been through G0. "
            "DESIGN.md section 8b: never spend a fold on a structure that has "
            "not been checked for geometric validity"
        )
        raise FoldError(msg)
    if not stamp.passed:
        msg = f"design {design.design_id} failed G0: {stamp.detail}"
        raise FoldError(msg)


def fold(
    design: Design,
    targets: Sequence[str],
    seeds: Sequence[int],
    adapter: FoldAdapter,
) -> tuple[FoldResult, ...]:
    """Fold one design against every target, at every seed.

    The counter-screen runs the same design against three or more targets and
    scores the difference (`DESIGN.md` section 1), so the same seeds are used
    across targets: margins are paired by seed, and pairing is what removes
    the seed-to-seed component the G4 gate measures against.
    """
    require_g0(design)
    if not targets:
        msg = "a counter-screen needs at least one target"
        raise FoldError(msg)
    if not seeds:
        msg = "folding needs at least one seed"
        raise FoldError(msg)
    if len(set(seeds)) != len(seeds):
        msg = f"seeds must be distinct, got {list(seeds)}"
        raise FoldError(msg)

    return tuple(adapter.predict(design, target, seed) for target in targets for seed in seeds)
