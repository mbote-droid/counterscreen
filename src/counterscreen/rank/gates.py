"""Applying the hard gates in order, and recording where each design died.

`DESIGN.md` section 8b states the ordering as an engineering constraint rather
than a convention: G0 costs seconds and co-folding costs minutes to hours, so
the pipeline must *enforce* cheap-first, not merely document it. A
geometrically invalid structure is not a cheap mistake to fold, it is a wasted
GPU-hour and a number in the results that means nothing.

Two consequences shape this module.

**Evaluation short-circuits.** A design stops at its first failing gate. That
is the whole point of the ordering, and it also makes the gate a design died
at well defined, which `PROTOCOL.md` section 5.4 needs: every negative control
must fail, and fail at its *registered* gate, because a flawed design that
fails for the wrong reason is a gate working by accident.

**A missing evaluator is an error, never a skip.** `PROTOCOL.md` section 12.4b
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
    """What a gate costs to evaluate, which is what fixes its position.

    Classified by expense, not by the kind of input a gate reads.
    ``STRUCTURE`` is local structural arithmetic costing seconds; a search
    against an external database is ``EXTERNAL`` however structural its
    question, because it costs a download and minutes.
    """

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
    # Foldseek against the whole PDB: a multi-gigabyte download and minutes
    # per query, so it is external like G7 and not local structural work.
    Gate.G9: GateCost.EXTERNAL,
}


class GateInput(enum.StrEnum):
    """What a gate has to be given before it can be evaluated at all.

    Cost alone does not fix the order. G6 asks a local structural question --
    buried unsatisfied charges -- but `PROTOCOL.md` section 8 asks it *in the
    T+ complex*, so it cannot run before co-folding however cheap it is. The
    position a gate may take is therefore set by the more expensive of what it
    costs and what it depends on.
    """

    SEQUENCE = "sequence"
    BACKBONE = "backbone"
    REFOLDED_MONOMER = "refolded_monomer"
    COMPLEX = "complex"


#: What each gate reads.
GATE_INPUT: Mapping[Gate, GateInput] = {
    Gate.G0: GateInput.BACKBONE,
    Gate.G1: GateInput.REFOLDED_MONOMER,
    Gate.G2: GateInput.COMPLEX,
    Gate.G3: GateInput.COMPLEX,
    Gate.G4: GateInput.COMPLEX,
    Gate.G5: GateInput.REFOLDED_MONOMER,
    Gate.G6: GateInput.COMPLEX,
    Gate.G7: GateInput.SEQUENCE,
    Gate.G8: GateInput.SEQUENCE,
    Gate.G9: GateInput.BACKBONE,
}

#: Tiers the ordering is non-decreasing in. Equal numbers mean the order
#: between two gates is free; the pipeline fixes one for reproducibility.
_COST_TIER: Mapping[GateCost, int] = {
    GateCost.SEQUENCE: 0,
    GateCost.STRUCTURE: 1,
    GateCost.CHEAP_FOLD: 1,
    GateCost.COFOLD: 2,
    GateCost.EXTERNAL: 3,
}
_INPUT_TIER: Mapping[GateInput, int] = {
    GateInput.SEQUENCE: 0,
    GateInput.BACKBONE: 1,
    GateInput.REFOLDED_MONOMER: 1,
    GateInput.COMPLEX: 2,
}


def effective_tier(gate: Gate) -> int:
    """How early a gate may run: the more expensive of its cost and its input."""
    return max(_COST_TIER[GATE_COST[gate]], _INPUT_TIER[GATE_INPUT[gate]])


#: Order of evaluation: submission constraints, then geometry,
#: self-consistency and the hydrophobic patch, then co-folding, then the
#: remainder. This is the `DESIGN.md` section 8b cascade with G8 moved to the
#: front by amendment A10.
#:
#: Section 8b placed G8 after co-folding, which was the one departure from the
#: cheap-first rule the same section states. G8 is sequence-only -- length,
#: chain count, standard residues, free cysteines -- costing microseconds and
#: needing no structure at all, while every design it rejects had already paid
#: for three targets at two seeds: 360 to 720 GPU-seconds at the 60-120 s per
#: prediction `PROTOCOL.md` section 10 calls realistic. Reordering cannot
#: change which designs survive, because the cascade is a conjunction of
#: predicates and each depends only on the design and on panel-derived
#: thresholds, so the only things that move are the per-stage rejection tallies
#: and the cost. Funnel counts are therefore comparable only within one
#: ordering, which is why the funnel tables are generated from this tuple
#: rather than written by hand.
PIPELINE_ORDER: tuple[Gate, ...] = (
    Gate.G8,
    Gate.G0,
    Gate.G1,
    Gate.G5,
    Gate.G2,
    Gate.G3,
    Gate.G4,
    Gate.G6,
    Gate.G7,
    Gate.G9,
)


class GateEvaluator(Protocol):
    """Decides one gate for one design.

    Returns the verdict and a short reason. The reason is not decoration: it
    becomes the diagnostic code of `PROTOCOL.md` section 5.4.
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
    `PROTOCOL.md` section 12.4b.
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
    """Counts at every stage, which `PROTOCOL.md` section 12.3a requires reported.

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
