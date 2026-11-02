# mypy: disallow_any_decorated=false
# hypothesis types @given as Callable[..., None], which disallow_any_decorated
# rejects. Relaxing that one flag here keeps strict mode everywhere else.
"""Invariants of the design record that must hold for any sequence and history."""

from hypothesis import given
from hypothesis import strategies as st

from counterscreen.core.design import Arm, Design, Gate
from counterscreen.core.hashing import sequence_id

RESIDUES = "ACDEFGHIKLMNPQRSTVWY"
sequences = st.text(alphabet=RESIDUES, min_size=1, max_size=60)
lowercase = st.characters(min_codepoint=97, max_codepoint=122)
stage_names = st.text(alphabet=lowercase, min_size=1, max_size=8)


@given(sequence=sequences)
def test_identity_depends_only_on_the_sequence(sequence: str) -> None:
    left = Design.create(sequence, Arm.M1, "rfdiffusion", 0)
    right = Design.create(sequence, Arm.M3, "other-generator", 99)
    assert left.design_id == right.design_id == sequence_id(sequence)


@given(sequence=sequences, stages=st.lists(stage_names, max_size=6))
def test_history_grows_by_exactly_one_per_stage(sequence: str, stages: list[str]) -> None:
    design = Design.create(sequence, Arm.M2, "rfdiffusion", 1)
    for name in stages:
        design = design.record_stage(name)
    assert len(design.history) == len(stages)
    assert [entry.stage for entry in design.history] == stages


@given(sequence=sequences, verdicts=st.lists(st.booleans(), min_size=1, max_size=10, unique=False))
def test_stamping_never_mutates_the_original(sequence: str, verdicts: list[bool]) -> None:
    original = Design.create(sequence, Arm.M1, "rfdiffusion", 0)
    current = original
    for gate, passed in zip(list(Gate), verdicts, strict=False):
        current = current.stamp(gate, passed=passed)
    assert original.gates == ()
    assert len(current.gates) == min(len(verdicts), len(list(Gate)))


@given(sequence=sequences, verdicts=st.lists(st.booleans(), min_size=1, max_size=10))
def test_first_failure_agrees_with_has_passed(sequence: str, verdicts: list[bool]) -> None:
    design = Design.create(sequence, Arm.M1, "rfdiffusion", 0)
    for gate, passed in zip(list(Gate), verdicts, strict=False):
        design = design.stamp(gate, passed=passed)
    failure = design.first_failure()
    if failure is None:
        assert all(design.has_passed(stamp.gate) for stamp in design.gates)
    else:
        assert not design.has_passed(failure.gate)
