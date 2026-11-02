"""The design record is immutable, self-identifying, and refuses to lose evidence."""

import dataclasses

import pytest

from counterscreen.core.design import Arm, Design, Gate
from counterscreen.core.hashing import sequence_id

SEQ = "MKTAYIAKQRQISFVKSHFSRQ"


def a_design() -> Design:
    return Design.create(SEQ, arm=Arm.M1, generator="rfdiffusion", seed=0)


def test_record_is_frozen() -> None:
    design = a_design()
    with pytest.raises(dataclasses.FrozenInstanceError):
        design.sequence = "AAAA"  # type: ignore[misc]


def test_design_id_is_derived_from_the_sequence() -> None:
    assert a_design().design_id == sequence_id(SEQ)


def test_create_normalises_the_sequence() -> None:
    assert Design.create("mkt\nayiakqrqisfvkshfsrq", Arm.M1, "rf", 0).sequence == SEQ


def test_constructing_with_an_unnormalised_sequence_is_refused() -> None:
    with pytest.raises(ValueError, match="normalised"):
        Design(sequence="mkt ayi", arm=Arm.M1, generator="rf", seed=0)


def test_negative_seed_is_refused() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Design.create(SEQ, Arm.M1, "rf", -1)


def test_recording_a_stage_returns_a_new_object_and_leaves_the_original_alone() -> None:
    before = a_design()
    after = before.record_stage("fold", model="protenix-v2", seeds="2")
    assert before.history == ()
    assert len(after.history) == 1
    assert after.history[0].stage == "fold"
    assert after is not before


def test_stage_parameters_are_sorted_for_deterministic_output() -> None:
    design = a_design().record_stage("fold", zeta="1", alpha="2", mu="3")
    assert [k for k, _ in design.history[0].params] == ["alpha", "mu", "zeta"]


def test_an_unstamped_gate_is_not_a_pass() -> None:
    """DESIGN section 8b: fold/ refuses a candidate not stamped G0-passed."""
    design = a_design()
    assert design.verdict(Gate.G0) is None
    assert not design.has_passed(Gate.G0)


def test_stamping_records_the_verdict() -> None:
    design = a_design().stamp(Gate.G0, passed=True, detail="no chain breaks")
    assert design.has_passed(Gate.G0)
    verdict = design.verdict(Gate.G0)
    assert verdict is not None
    assert verdict.detail == "no chain breaks"


def test_a_failing_stamp_is_not_a_pass() -> None:
    design = a_design().stamp(Gate.G0, passed=False, detail="Ca-Ca 6.1 A")
    assert not design.has_passed(Gate.G0)


def test_restamping_a_gate_is_refused() -> None:
    """A failure must not be quietly overwritten by a later pass."""
    design = a_design().stamp(Gate.G0, passed=False, detail="chain break")
    with pytest.raises(ValueError, match="already stamped"):
        design.stamp(Gate.G0, passed=True)


def test_first_failure_reports_the_earliest_failing_gate() -> None:
    design = (
        a_design()
        .stamp(Gate.G0, passed=True)
        .stamp(Gate.G1, passed=False, detail="scRMSD 3.1 A")
        .stamp(Gate.G5, passed=False, detail="patch 640 A^2")
    )
    failure = design.first_failure()
    assert failure is not None
    assert failure.gate is Gate.G1


def test_first_failure_is_none_when_everything_passed() -> None:
    design = a_design().stamp(Gate.G0, passed=True).stamp(Gate.G1, passed=True)
    assert design.first_failure() is None


def test_g5_is_the_hydrophobic_patch_gate_and_g10_does_not_exist() -> None:
    """Amendment A1 reused the vacated G5 rather than appending a G10."""
    assert Gate.G5 in set(Gate)
    assert "G10" not in {g.value for g in Gate}
    assert len(set(Gate)) == 10
