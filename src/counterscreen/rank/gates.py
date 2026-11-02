"""Applying the hard gates in order, and recording where each design died.

`DESIGN.md` section 8b states the ordering as an engineering constraint rather
than a convention: G0 costs seconds and co-folding costs minutes to hours, so
the pipeline must *enforce* cheap-first, not merely document it. A
geometrically invalid structure is not a cheap mistake to fold, it is a wasted
GPU-hour and a number in the results that means nothing.

Two consequences shape this module.

**Evaluation short-circuits.** A design stops at its first failing gate. That
is the whole point of the ordering, and it also makes the gate a design died
at well defined, which `CLAUDE.md` section 5.4 needs: every negative control
must fail, and fail at its *registered* gate, because a flawed design that
fails for the wrong reason is a gate working by accident.

**A missing evaluator is an error, never a skip.** `CLAUDE.md` section 12.4b
registers "skip gate G3 entirely" as a mutant a gate contract test must catch.
A runner that silently ignored a gate it had no evaluator for would pass that
mutant, so :func:`run_gates` refuses to run at all unless every registered
gate is supplied.

`rank/` must not know model internals (`DESIGN.md` section 1), so a gate
arrives here as an opaque callable returning a verdict and a reason. How a
contact fraction or a TM-score was obtained is not this package's business.
"""

import dataclasses
import enum
from collections.abc import Mapping, Sequence
from typing import Protocol

from counterscreen.core.design import Design, Gate


class GateError(ValueError):
    """Raised when gates cannot be applied as registered."""


class GateCost(enum.StrEnum):
    """What a gate costs to evaluate, which is what fixes its position."""

    SEQUENCE = "sequence"
    STRUCTURE = "structure"
    CHEAP_FOLD = "cheap_fold"
    COFOLD = "cofold"
    EXTERNAL = "external"


#: What each gate costs. Used to assert the ordering keeps its promise.
GATE_COST: Mapping[Gate, GateCost] = {
    Gate.G0: GateCost.STRUCTURE,
    Gate.G1: GateCost.CHEAP_FOLD,
    Gate.G2: GateCost.COFOLD,
    Gate.G3: GateCost.COFOLD,
    Gate.G4: GateCost.COFOLD,
    Gate.G5: GateCost.STRUCTURE,
    Gate.G6: GateCost.STRUCTURE,
    Gate.G7: GateCost.EXTERNAL,
    Gate.G8: GateCost.SEQUENCE,
    Gate.G9: GateCost.STRUCTURE,
}

#: Order of evaluation, following the `DESIGN.md` section 8b cascade:
#: geometry, self-consistency, hydrophobic patch, then co-folding, then the
#: remainder.
#:
#: One departure from cheap-first is inherited from that diagram and is worth
#: naming rather than quietly fixing. G8 is a sequence-only check -- length,
#: chain count, standard residues, free cysteines -- costing microseconds and
#: needing no structure at all, yet section 8b places it after co-folding. Any
#: design failing G8 was never submittable, so every GPU-second spent on it
#: before that point is wasted. Moving it to the front is a change to a
#: specified ordering, so it is raised as a proposed amendment rather than
#: made here.
PIPELINE_ORDER: tuple[Gate, ...] = (
    Gate.G0,
    Gate.G1,
    Gate.G5,
    Gate.G2,
    Gate.G3,
    Gate.G4,
    Gate.G6,
    Gate.G7,
    Gate.G8,
    Gate.G9,
)


class GateEvaluator(Protocol):
    """Decides one gate for one design.

    Returns the verdict and a short reason. The reason is not decoration: it
    becomes the diagnostic code of `CLAUDE.md` section 5.4.
    """

    def __call__(self, design: Design, /) -> tuple[bool, str]:
        """Evaluate this gate for a design.

        Positional-only: an evaluator is always called positionally, so
        requiring every implementation to name its parameter ``design`` would
        be coupling for nothing.
        """
        ...


@dataclasses.dataclass(frozen=True, slots=True)
class GateResult:
    """How far one design got, and why it stopped."""

    design_id: str
    outcomes: tuple[tuple[Gate, bool, str], ...]

    @property
    def passed(self) -> bool:
        """Whether the design cleared every gate it was put through."""
        return bool(self.outcomes) and all(ok for _, ok, _ in self.outcomes)

    @property
    def failed_at(self) -> Gate | None:
        """The gate this design died at, or ``None`` if it passed everything."""
        for gate, ok, _ in self.outcomes:
            if not ok:
                return gate
        return None

    @property
    def reason(self) -> str:
        """Why it died, or an empty string if it did not."""
        for _, ok, detail in self.outcomes:
            if not ok:
                return detail
        return ""


def run_gates(
    design: Design,
    evaluators: Mapping[Gate, GateEvaluator],
    order: Sequence[Gate] = PIPELINE_ORDER,
) -> GateResult:
    """Apply gates in order, stopping at the first failure.

    Every gate in ``order`` must have an evaluator. A gate silently skipped is
    a gate that never rejects anything, which is the registered mutant in
    `CLAUDE.md` section 12.4b.
    """
    missing = [gate for gate in order if gate not in evaluators]
    if missing:
        msg = (
            f"no evaluator supplied for {[str(g) for g in missing]}; "
            "a gate without an evaluator would be silently skipped"
        )
        raise GateError(msg)

    outcomes: list[tuple[Gate, bool, str]] = []
    current = design
    for gate in order:
        verdict, detail = evaluators[gate](current)
        outcomes.append((gate, verdict, detail))
        current = current.stamp(gate, passed=verdict, detail=detail)
        if not verdict:
            break
    return GateResult(design_id=design.design_id, outcomes=tuple(outcomes))


@dataclasses.dataclass(frozen=True, slots=True)
class Funnel:
    """Counts at every stage, which `CLAUDE.md` section 12.3a requires reported.

    Cherry-picking is reporting the best of a thousand designs without
    reporting the thousand. The drop at each step is a result in itself: a gate
    removing 95% of candidates is either doing real work or is wrong, and the
    reader should be able to tell which.
    """

    generated: int
    rejected_by: tuple[tuple[Gate, int], ...]
    survived_gates: int
    clustered: int
    submitted: int

    def __post_init__(self) -> None:
        """Refuse a funnel whose counts do not add up.

        `DESIGN.md` section 8 calls this test load-bearing: the funnel counts
        must sum consistently stage to stage, or the reported drop at some
        stage is wrong and every conclusion drawn from it is too.
        """
        if self.generated < 0:
            msg = "generated cannot be negative"
            raise GateError(msg)
        rejected = sum(count for _, count in self.rejected_by)
        if self.generated - rejected != self.survived_gates:
            msg = (
                f"funnel does not balance: {self.generated} generated minus "
                f"{rejected} rejected is not {self.survived_gates} survivors"
            )
            raise GateError(msg)
        if not self.generated >= self.survived_gates >= self.clustered >= self.submitted >= 0:
            msg = (
                "funnel counts must not increase down the cascade: "
                f"{self.generated} -> {self.survived_gates} -> "
                f"{self.clustered} -> {self.submitted}"
            )
            raise GateError(msg)

    @classmethod
    def from_results(
        cls,
        results: Sequence[GateResult],
        clustered: int,
        submitted: int,
        order: Sequence[Gate] = PIPELINE_ORDER,
    ) -> "Funnel":
        """Build a funnel from the per-design outcomes."""
        tally: dict[Gate, int] = dict.fromkeys(order, 0)
        survivors = 0
        for result in results:
            failed = result.failed_at
            if failed is None:
                survivors += 1
            else:
                tally[failed] = tally.get(failed, 0) + 1
        return cls(
            generated=len(results),
            rejected_by=tuple((gate, tally[gate]) for gate in order),
            survived_gates=survivors,
            clustered=clustered,
            submitted=submitted,
        )

    def remaining_after(self, gate: Gate, order: Sequence[Gate] = PIPELINE_ORDER) -> int:
        """How many designs were still alive once this gate had run."""
        rejected = dict(self.rejected_by)
        cut = 0
        for candidate in order:
            cut += rejected.get(candidate, 0)
            if candidate is gate:
                return self.generated - cut
        msg = f"{gate} is not in the pipeline order"
        raise GateError(msg)
