"""Gate contract (CLAUDE.md section 12.4b): a gate must never be silently skipped."""

import pytest

from counterscreen.core.design import Arm, Design, Gate
from counterscreen.rank.gates import (
    GATE_COST,
    PIPELINE_ORDER,
    Funnel,
    GateCost,
    GateError,
    GateEvaluator,
    GateResult,
    run_gates,
)

SEQ = "MKTAYIAKQRQISFVKSHFSRQ"


def design(sequence: str = SEQ) -> Design:
    return Design.create(sequence, arm=Arm.M1, generator="rfdiffusion", seed=0)


def always(verdict: bool, detail: str = "") -> GateEvaluator:
    def evaluate(_: Design) -> tuple[bool, str]:
        return verdict, detail

    return evaluate


def all_passing() -> dict[Gate, GateEvaluator]:
    return {gate: always(True, "ok") for gate in PIPELINE_ORDER}


# --- Registered mutant: skip gate G3 entirely -------------------------------


def test_a_missing_evaluator_refuses_to_run() -> None:
    evaluators = all_passing()
    del evaluators[Gate.G3]
    with pytest.raises(GateError, match="G3"):
        run_gates(design(), evaluators)


@pytest.mark.parametrize("skipped", list(PIPELINE_ORDER))
def test_no_registered_gate_can_be_omitted(skipped: Gate) -> None:
    evaluators = all_passing()
    del evaluators[skipped]
    with pytest.raises(GateError, match=str(skipped)):
        run_gates(design(), evaluators)


def test_every_gate_is_evaluated_when_all_pass() -> None:
    result = run_gates(design(), all_passing())
    assert [gate for gate, _, _ in result.outcomes] == list(PIPELINE_ORDER)
    assert result.passed
    assert result.failed_at is None


# --- Ordering ---------------------------------------------------------------


def test_geometry_runs_before_anything_that_folds() -> None:
    """DESIGN section 8b: never spend a fold on a structure that is not valid."""
    folding = {GateCost.CHEAP_FOLD, GateCost.COFOLD}
    first_fold = min(i for i, g in enumerate(PIPELINE_ORDER) if GATE_COST[g] in folding)
    assert PIPELINE_ORDER.index(Gate.G0) < first_fold


def test_the_cheap_structure_gates_run_before_co_folding() -> None:
    first_cofold = min(i for i, g in enumerate(PIPELINE_ORDER) if GATE_COST[g] is GateCost.COFOLD)
    for gate in (Gate.G0, Gate.G1, Gate.G5):
        assert PIPELINE_ORDER.index(gate) < first_cofold


def test_the_order_covers_every_gate_exactly_once() -> None:
    assert sorted(PIPELINE_ORDER, key=str) == sorted(Gate, key=str)
    assert len(set(PIPELINE_ORDER)) == len(PIPELINE_ORDER)


def test_g8_is_sequence_only_and_currently_sits_after_co_folding() -> None:
    """Documents the ordering departure named in the module docstring.

    Not an assertion that this is right. G8 needs no structure at all, so
    every design it rejects consumed co-folding time it never needed. Changing
    a specified order is an amendment, so the test records the state of play
    rather than enforcing a fix.
    """
    assert GATE_COST[Gate.G8] is GateCost.SEQUENCE
    last_cofold = max(i for i, g in enumerate(PIPELINE_ORDER) if GATE_COST[g] is GateCost.COFOLD)
    assert PIPELINE_ORDER.index(Gate.G8) > last_cofold


# --- Short-circuiting and diagnostics ---------------------------------------


def test_evaluation_stops_at_the_first_failure() -> None:
    evaluators = all_passing()
    evaluators[Gate.G1] = always(False, "scRMSD 3.1 A")
    result = run_gates(design(), evaluators)
    assert result.failed_at is Gate.G1
    assert result.reason == "scRMSD 3.1 A"
    assert [gate for gate, _, _ in result.outcomes] == [Gate.G0, Gate.G1]
    assert not result.passed


def test_the_diagnostic_reason_travels_with_the_verdict() -> None:
    evaluators = all_passing()
    evaluators[Gate.G5] = always(False, "largest apolar patch 640 A^2")
    result = run_gates(design(), evaluators)
    assert "apolar patch" in result.reason


# --- Funnel -----------------------------------------------------------------


def make_results(failures: dict[Gate, int], survivors: int) -> list[GateResult]:
    results: list[GateResult] = []
    for gate, count in failures.items():
        for _ in range(count):
            evaluators = all_passing()
            evaluators[gate] = always(False, "no")
            results.append(run_gates(design(), evaluators))
    results.extend(run_gates(design(), all_passing()) for _ in range(survivors))
    return results


def test_the_funnel_balances() -> None:
    results = make_results({Gate.G0: 5, Gate.G4: 3}, survivors=2)
    funnel = Funnel.from_results(results, clustered=2, submitted=2)
    assert funnel.generated == 10
    assert funnel.survived_gates == 2
    assert dict(funnel.rejected_by)[Gate.G0] == 5
    assert dict(funnel.rejected_by)[Gate.G4] == 3


def test_a_funnel_that_does_not_balance_is_refused() -> None:
    with pytest.raises(GateError, match="does not balance"):
        Funnel(
            generated=10,
            rejected_by=((Gate.G0, 5),),
            survived_gates=2,
            clustered=2,
            submitted=2,
        )


def test_funnel_counts_cannot_increase_down_the_cascade() -> None:
    with pytest.raises(GateError, match="must not increase"):
        Funnel(
            generated=10,
            rejected_by=((Gate.G0, 8),),
            survived_gates=2,
            clustered=5,
            submitted=2,
        )


def test_remaining_after_each_gate_is_non_increasing() -> None:
    results = make_results({Gate.G0: 4, Gate.G1: 3, Gate.G9: 1}, survivors=2)
    funnel = Funnel.from_results(results, clustered=2, submitted=2)
    counts = [funnel.remaining_after(gate) for gate in PIPELINE_ORDER]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] == 6
    assert counts[-1] == funnel.survived_gates


def test_remaining_after_an_unknown_gate_is_refused() -> None:
    funnel = Funnel.from_results([], clustered=0, submitted=0)
    with pytest.raises(GateError, match="not in the pipeline order"):
        funnel.remaining_after(Gate.G0, order=[Gate.G1])
