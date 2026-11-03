"""ProteinMPNN invocation: sequences onto a backbone, and what must not change.

`CLAUDE.md` §9 stage 2 fixes the sampling: eight sequences per backbone at
T = 0.1. Gate G1 then takes the best of those eight, so the count is part of
the gate's definition rather than a tuning knob — asking for four would change
what G1 means while appearing only to change a parameter. Both values come
from :class:`~counterscreen.core.config.GateConfig` and
:class:`~counterscreen.core.config.SamplingConfig`, and a mismatch is refused.

**The guard this module exists for is the fixed-position check.** ProteinMPNN
is given a complex and asked to design one chain of it. If the fixed-position
specification is wrong, it redesigns the target instead of, or as well as, the
binder — and the result is a plausible sequence for a protein that is no
longer HLA-A 11:01. Nothing downstream detects that: the structure folds, the
confidence is fine, the margin is computed against a target the campaign never
meant to screen. So the target sequence is compared before and after, and any
change is refused.

This package must not know about folding or scoring (`DESIGN.md` §1). It emits
candidate sequences and the provenance needed to reproduce them; whether they
are any good is somebody else's question.
"""

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Protocol

from counterscreen.core.config import GateConfig, SamplingConfig
from counterscreen.core.design import Arm, Design
from counterscreen.core.hashing import normalise_sequence

#: The twenty standard amino acids. ProteinMPNN emits only these; anything
#: else indicates a parsing fault rather than an unusual design.
STANDARD_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWY")


class SequenceDesignError(ValueError):
    """Raised when sequence design cannot be run or trusted as specified."""


@dataclasses.dataclass(frozen=True, slots=True)
class SequenceCandidate:
    """One sampled sequence, with the score the designer assigned it."""

    sequence: str
    score: float
    sample_index: int

    def __post_init__(self) -> None:
        """Refuse a candidate that is not a usable protein sequence."""
        if not self.sequence:
            msg = f"candidate {self.sample_index} is empty"
            raise SequenceDesignError(msg)
        unexpected = sorted(set(self.sequence) - STANDARD_RESIDUES)
        if unexpected:
            msg = (
                f"candidate {self.sample_index} contains non-standard residues "
                f"{unexpected}; ProteinMPNN emits only the twenty standard amino acids, "
                "so this indicates a parsing fault"
            )
            raise SequenceDesignError(msg)


class SequenceDesigner(Protocol):
    """A sequence design model behind the common interface."""

    @property
    def name(self) -> str:
        """Designer name, as recorded in provenance."""
        ...

    @property
    def weights_sha256(self) -> str:
        """Checksum of the weights that produced these sequences."""
        ...

    def sample(
        self,
        backbone_id: str,
        /,
        *,
        count: int,
        temperature: float,
        fixed_chains: Mapping[str, str],
        seed: int,
    ) -> tuple[SequenceCandidate, ...]:
        """Sample sequences for the designed chain.

        ``fixed_chains`` maps each chain that must not change to its current
        sequence, so the caller can verify afterwards that it did not.
        """
        ...


def _check_sampling(
    count: int, temperature: float, gates: GateConfig, sampling: SamplingConfig
) -> None:
    if count != gates.g1_mpnn_sequences:
        msg = (
            f"asked for {count} sequences but G1 is defined as best of "
            f"{gates.g1_mpnn_sequences}. Changing the count changes what the gate "
            "means, so it is a registered value and not a parameter"
        )
        raise SequenceDesignError(msg)
    if temperature != sampling.mpnn_temperature:
        msg = (
            f"temperature {temperature} differs from the registered "
            f"{sampling.mpnn_temperature}; sampling temperature sets the diversity "
            "the whole funnel is measured against"
        )
        raise SequenceDesignError(msg)


def verify_fixed_chains(expected: Mapping[str, str], observed: Mapping[str, str]) -> None:
    """Refuse any change to a chain that was supposed to be held fixed.

    The failure this prevents is silent. A redesigned target still folds,
    still scores, and still produces a margin — against a complex the campaign
    never intended to screen.
    """
    missing = sorted(set(expected) - set(observed))
    if missing:
        msg = f"fixed chains absent from the result: {missing}"
        raise SequenceDesignError(msg)
    changed = [
        chain
        for chain, sequence in expected.items()
        if normalise_sequence(observed[chain]) != normalise_sequence(sequence)
    ]
    if changed:
        msg = (
            f"chains {sorted(changed)} were designed but should have been fixed. "
            "The target has been redesigned; every downstream number would be "
            "computed against a complex this campaign never meant to screen"
        )
        raise SequenceDesignError(msg)


def design_sequences(
    backbone_id: str,
    designer: SequenceDesigner,
    *,
    arm: Arm,
    seed: int,
    fixed_chains: Mapping[str, str],
    gates: GateConfig | None = None,
    sampling: SamplingConfig | None = None,
) -> tuple[Design, ...]:
    """Sample the registered number of sequences for one backbone.

    Returns designs in the designer's own order, carrying the arm, the seed
    and a history entry naming the model and its weights. Ordering is not
    ranking: G1 takes the best of these by self-consistency, which this
    package cannot evaluate and must not pretend to.
    """
    gate_config = gates or GateConfig()
    sampling_config = sampling or SamplingConfig()
    count = gate_config.g1_mpnn_sequences
    temperature = sampling_config.mpnn_temperature
    _check_sampling(count, temperature, gate_config, sampling_config)

    candidates = designer.sample(
        backbone_id,
        count=count,
        temperature=temperature,
        fixed_chains=fixed_chains,
        seed=seed,
    )
    if len(candidates) != count:
        msg = f"designer returned {len(candidates)} sequences, expected {count}"
        raise SequenceDesignError(msg)
    indices = [c.sample_index for c in candidates]
    if len(set(indices)) != len(indices):
        msg = f"designer repeated a sample index: {indices}"
        raise SequenceDesignError(msg)

    return tuple(
        Design.create(candidate.sequence, arm=arm, generator=designer.name, seed=seed).record_stage(
            "sequence",
            model=designer.name,
            weights_sha256=designer.weights_sha256,
            backbone=backbone_id,
            temperature=str(temperature),
            sample_index=str(candidate.sample_index),
            score=f"{candidate.score:.6g}",
        )
        for candidate in candidates
    )


def unique_sequences(designs: Sequence[Design]) -> tuple[Design, ...]:
    """Drop duplicates by design id, keeping the first occurrence.

    Sampling at a low temperature converges, so eight samples can contain
    fewer than eight distinct sequences. Carrying duplicates forward would
    inflate every funnel count in `METHODS.md` §8.7 without adding a single
    candidate.
    """
    seen: set[str] = set()
    kept: list[Design] = []
    for design in designs:
        if design.design_id not in seen:
            seen.add(design.design_id)
            kept.append(design)
    return tuple(kept)
