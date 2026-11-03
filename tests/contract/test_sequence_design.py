"""Sequence design contract: registered sampling, and the fixed-chain guard."""

from collections.abc import Mapping
from typing import override

import pytest

from counterscreen.core.config import GateConfig, SamplingConfig
from counterscreen.core.design import Arm, Design
from counterscreen.sequence.mpnn import (
    SequenceCandidate,
    SequenceDesignError,
    design_sequences,
    unique_sequences,
    verify_fixed_chains,
)

HLA = "GSHSMRYFYTSVSRPGRGEPRFIAVGYVDD"
BINDER = "MKTAYIAKQRQISFVKSHFSRQ"
FIXED = {"A": HLA, "C": "VVVGADGVGK"}


class FakeDesigner:
    """Stand-in for ProteinMPNN, so the interface is testable without weights."""

    def __init__(self, sequences: list[str] | None = None, redesign_target: bool = False) -> None:
        """Record what this designer will emit."""
        self._sequences = sequences or [BINDER[:-1] + c for c in "ACDEFGHI"]
        self._redesign = redesign_target
        self.calls: list[dict[str, object]] = []

    @property
    def name(self) -> str:
        return "proteinmpnn"

    @property
    def weights_sha256(self) -> str:
        return "cafebabe"

    def sample(
        self,
        backbone_id: str,
        /,
        *,
        count: int,
        temperature: float,
        fixed_chains: Mapping[str, str],  # noqa: ARG002
        seed: int,
    ) -> tuple[SequenceCandidate, ...]:
        self.calls.append(
            {"backbone": backbone_id, "count": count, "temp": temperature, "seed": seed}
        )
        return tuple(
            SequenceCandidate(sequence=s, score=-1.0 - i / 10, sample_index=i)
            for i, s in enumerate(self._sequences[:count])
        )


def run(designer: FakeDesigner) -> tuple[Design, ...]:
    return design_sequences("bb_001", designer, arm=Arm.M3, seed=7, fixed_chains=FIXED)


# --- The guard this module exists for ---------------------------------------


def test_an_unchanged_target_passes() -> None:
    verify_fixed_chains(FIXED, dict(FIXED))


def test_a_redesigned_target_is_refused() -> None:
    """A redesigned HLA still folds and still scores. Nothing downstream notices."""
    observed = {**FIXED, "A": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}
    with pytest.raises(SequenceDesignError, match="should have been fixed"):
        verify_fixed_chains(FIXED, observed)


def test_a_redesigned_peptide_is_refused() -> None:
    observed = {**FIXED, "C": "VVVGAGGVGK"}
    with pytest.raises(SequenceDesignError, match="should have been fixed"):
        verify_fixed_chains(FIXED, observed)


def test_a_missing_fixed_chain_is_refused() -> None:
    with pytest.raises(SequenceDesignError, match="absent from the result"):
        verify_fixed_chains(FIXED, {"A": HLA})


def test_whitespace_and_case_do_not_count_as_a_change() -> None:
    verify_fixed_chains(FIXED, {"A": HLA.lower(), "C": "vvvga\ndgvgk"})


# --- Registered sampling ----------------------------------------------------


def test_the_registered_count_and_temperature_are_used() -> None:
    designer = FakeDesigner()
    run(designer)
    assert designer.calls[0]["count"] == GateConfig().g1_mpnn_sequences == 8
    assert designer.calls[0]["temp"] == SamplingConfig().mpnn_temperature == 0.1


def test_the_seed_and_backbone_reach_the_designer() -> None:
    designer = FakeDesigner()
    run(designer)
    assert designer.calls[0]["seed"] == 7
    assert designer.calls[0]["backbone"] == "bb_001"


def test_eight_sequences_produce_eight_designs() -> None:
    assert len(run(FakeDesigner())) == 8


def test_a_short_return_is_refused() -> None:
    """G1 is best of eight; six would change what the gate means."""
    designer = FakeDesigner(sequences=[BINDER[:-1] + c for c in "ACD"])
    with pytest.raises(SequenceDesignError, match="expected 8"):
        run(designer)


def test_a_repeated_sample_index_is_refused() -> None:
    class Repeating(FakeDesigner):
        @override
        def sample(
            self,
            backbone_id: str,
            /,
            **kwargs: object,
        ) -> tuple[SequenceCandidate, ...]:
            return tuple(
                SequenceCandidate(sequence=BINDER[:-1] + c, score=-1.0, sample_index=0)
                for c in "ACDEFGHI"
            )

    with pytest.raises(SequenceDesignError, match="repeated a sample index"):
        run(Repeating())


# --- Candidate validation ---------------------------------------------------


def test_a_non_standard_residue_is_refused() -> None:
    with pytest.raises(SequenceDesignError, match="non-standard residues"):
        SequenceCandidate(sequence="MKTAYXIAK", score=-1.0, sample_index=0)


def test_an_empty_candidate_is_refused() -> None:
    with pytest.raises(SequenceDesignError, match="is empty"):
        SequenceCandidate(sequence="", score=-1.0, sample_index=0)


# --- Provenance and ordering ------------------------------------------------


def test_each_design_records_the_model_and_its_weights() -> None:
    (first, *_) = run(FakeDesigner())
    params = dict(first.history[0].params)
    assert first.history[0].stage == "sequence"
    assert params["model"] == "proteinmpnn"
    assert params["weights_sha256"] == "cafebabe"
    assert params["backbone"] == "bb_001"
    assert params["temperature"] == "0.1"


def test_designs_carry_the_arm_and_seed_they_were_made_for() -> None:
    designs = run(FakeDesigner())
    assert all(d.arm is Arm.M3 for d in designs)
    assert all(d.seed == 7 for d in designs)


def test_order_is_the_designers_order_not_a_ranking() -> None:
    """G1 ranks by self-consistency, which this package cannot evaluate."""
    designs = run(FakeDesigner())
    indices = [dict(d.history[0].params)["sample_index"] for d in designs]
    assert indices == [str(i) for i in range(8)]


# --- Duplicate collapse -----------------------------------------------------


def test_converged_sampling_collapses_to_unique_sequences() -> None:
    """Low temperature converges; duplicates would inflate every funnel count."""
    designer = FakeDesigner(sequences=[BINDER, BINDER, BINDER[:-1] + "A"] + [BINDER] * 5)
    designs = run(designer)
    assert len(designs) == 8
    assert len(unique_sequences(designs)) == 2


def test_unique_keeps_the_first_occurrence() -> None:
    designer = FakeDesigner(sequences=[BINDER[:-1] + c for c in "AACDEFGH"])
    kept = unique_sequences(run(designer))
    assert dict(kept[0].history[0].params)["sample_index"] == "0"
