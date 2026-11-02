"""The immutable design record that every stage extends and none edits.

`build_rules.pdf` section 2.1 names this directly as the protein analogue of
NeuroSignal's frozen ``Recording``: a value object carrying the sequence hash,
backbone, target complex, generator, seed and model-weight hashes, which every
stage extends and never edits. The consequences it lists carry over exactly.
Raw candidates stay read-only by construction; the record itself answers
"which settings produced this number?"; and an invalid object cannot exist,
because validation happens on creation.

Gate verdicts live here rather than in `rank/` for one specific reason.
`DESIGN.md` section 8b requires that ``fold/`` refuse a candidate which has not
been stamped as G0-passed, and ``fold/`` must not import ``rank/``
(`DESIGN.md` section 1). The stamp therefore has to travel on the design.
"""

import enum
from dataclasses import dataclass, replace
from typing import Self

from counterscreen.core.hashing import normalise_sequence, sequence_id


class Gate(enum.StrEnum):
    """The hard gates of `CLAUDE.md` section 8, in pipeline order.

    G5 is the hydrophobic patch gate registered by amendment A1. It was vacated
    in v0.3 when delta-delta-G_spec was demoted to a ranking feature, and the
    number was reused rather than appending a G10.
    """

    G0 = "G0"
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    G5 = "G5"
    G6 = "G6"
    G7 = "G7"
    G8 = "G8"
    G9 = "G9"


class Arm(enum.StrEnum):
    """The discrimination mechanisms of `CLAUDE.md` section 4.

    The affinity-only control is an arm of its own: it is the design that would
    win if ranked on confidence against T+ alone, and it is submitted precisely
    so that the objective can be shown to have been right or wrong.
    """

    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    AFFINITY_CONTROL = "affinity_control"


@dataclass(frozen=True, slots=True)
class StageRecord:
    """One stage's name and the parameters it ran with."""

    stage: str
    params: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class GateStamp:
    """One gate's verdict on one design."""

    gate: Gate
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class Design:
    """A candidate binder, and everything known about how it was made."""

    sequence: str
    arm: Arm
    generator: str
    seed: int
    backbone_sha256: str | None = None
    target_sha256: str | None = None
    weights_sha256: tuple[tuple[str, str], ...] = ()
    gates: tuple[GateStamp, ...] = ()
    history: tuple[StageRecord, ...] = ()

    def __post_init__(self) -> None:
        """Refuse to build an invalid record.

        The sequence must already be normalised. Normalising silently here
        would mean two records with different ``sequence`` fields comparing
        equal in every way that matters, so the caller is made to use
        :meth:`create`.
        """
        if self.sequence != normalise_sequence(self.sequence):
            msg = (
                "Design.sequence must already be normalised; "
                "use Design.create() to normalise on the way in"
            )
            raise ValueError(msg)
        if self.seed < 0:
            msg = f"seed must be non-negative, got {self.seed}"
            raise ValueError(msg)
        stamped = [stamp.gate for stamp in self.gates]
        if len(set(stamped)) != len(stamped):
            msg = f"a gate is stamped more than once: {stamped}"
            raise ValueError(msg)

    @classmethod
    def create(cls, sequence: str, arm: Arm, generator: str, seed: int) -> "Design":
        """Build a design, normalising the sequence on the way in."""
        return cls(
            sequence=normalise_sequence(sequence),
            arm=arm,
            generator=generator,
            seed=seed,
        )

    @property
    def design_id(self) -> str:
        """The content-addressed id, derived from the sequence alone.

        Derived rather than stored, so a record cannot carry an id that
        disagrees with its own sequence.
        """
        return sequence_id(self.sequence)

    def record_stage(self, stage: str, **params: str) -> Self:
        """Return a copy with one stage appended to the history.

        Parameters are sorted, because `build_rules.pdf` section 4.1 forbids
        dict-order dependence in anything written to an output file.
        """
        entry = StageRecord(stage=stage, params=tuple(sorted(params.items())))
        return replace(self, history=(*self.history, entry))

    def stamp(self, gate: Gate, *, passed: bool, detail: str = "") -> Self:
        """Return a copy carrying this gate's verdict.

        Re-stamping a gate is refused. A gate verdict is evidence about a
        design, and silently overwriting a failure with a later pass is the
        same class of error that `DESIGN.md` section 1 forbids for returned
        measurements.
        """
        if self.verdict(gate) is not None:
            msg = f"{gate} is already stamped on design {self.design_id}"
            raise ValueError(msg)
        return replace(self, gates=(*self.gates, GateStamp(gate, passed, detail)))

    def verdict(self, gate: Gate) -> GateStamp | None:
        """Return this gate's stamp, or ``None`` if it has not run."""
        for stamp in self.gates:
            if stamp.gate is gate:
                return stamp
        return None

    def has_passed(self, gate: Gate) -> bool:
        """Whether this design carries a passing stamp for a gate.

        A gate that has not run is not a pass. This is what lets ``fold/``
        refuse an unstamped candidate (`DESIGN.md` section 8b) instead of
        spending a GPU-hour on a structure that was never checked.
        """
        stamp = self.verdict(gate)
        return stamp is not None and stamp.passed

    def first_failure(self) -> GateStamp | None:
        """Return the earliest gate this design failed, or ``None`` if it failed none.

        The gate a design dies at is a reportable quantity: it is the diagnostic
        code of `CLAUDE.md` section 5.4 and a row of the funnel in
        `METHODS.md` section 8.7.
        """
        for stamp in self.gates:
            if not stamp.passed:
                return stamp
        return None
