"""FoldResult schema and the G0 refusal (DESIGN.md sections 3, 8 and 8b)."""

import numpy as np
import pytest

from counterscreen.core.design import Arm, Design, Gate
from counterscreen.fold.adapter import (
    AdapterRegistry,
    ConfidenceMetric,
    FoldError,
    FoldResult,
    confidence_from,
    fold,
    objective_has_an_input,
    require_g0,
)

SEQ = "MKTAYIAKQRQISFVKSHFSRQ"


def design(*, g0: bool | None = True) -> Design:
    base = Design.create(SEQ, arm=Arm.M1, generator="rfdiffusion", seed=0)
    if g0 is None:
        return base
    return base.stamp(Gate.G0, passed=g0, detail="" if g0 else "chain break 6.1 A")


class FakeAdapter:
    """A stand-in model, so the interface can be tested without a GPU."""

    def __init__(self, emits: frozenset[ConfidenceMetric], name: str = "fake") -> None:
        """Record what this stand-in claims to emit."""
        self._name = name
        self._emits = emits
        self.calls: list[tuple[str, int]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def emits(self) -> frozenset[ConfidenceMetric]:
        return self._emits

    def predict(self, design: Design, target: str, seed: int, /) -> FoldResult:
        self.calls.append((target, seed))
        return FoldResult(
            design_id=design.design_id,
            target=target,
            model=self._name,
            model_weights_sha256="deadbeef",
            seed=seed,
            coordinates=np.zeros((10, 3)),
            confidence=confidence_from({"iptm": 0.7, "ipsae": 0.6}),
            chain_ids=("A", "B"),
            wall_time_s=1.0,
        )


# --- Registered: never fold a structure G0 has not passed -------------------


def test_an_unstamped_design_is_refused() -> None:
    with pytest.raises(FoldError, match="has not been through G0"):
        require_g0(design(g0=None))


def test_a_design_that_failed_g0_is_refused_with_its_reason() -> None:
    with pytest.raises(FoldError, match="chain break"):
        require_g0(design(g0=False))


def test_a_g0_passed_design_proceeds() -> None:
    require_g0(design(g0=True))


def test_fold_enforces_the_gate_before_spending_anything() -> None:
    adapter = FakeAdapter(frozenset({ConfidenceMetric.IPSAE}))
    with pytest.raises(FoldError, match="G0"):
        fold(design(g0=None), ["T+"], [1], adapter)
    assert adapter.calls == []


# --- The counter-screen shape -----------------------------------------------


def test_every_target_is_folded_at_every_seed() -> None:
    adapter = FakeAdapter(frozenset({ConfidenceMetric.IPSAE}))
    results = fold(design(), ["T+", "D1", "D2"], [1, 2], adapter)
    assert len(results) == 6
    assert adapter.calls == [("T+", 1), ("T+", 2), ("D1", 1), ("D1", 2), ("D2", 1), ("D2", 2)]


def test_the_same_seeds_run_against_every_target() -> None:
    """Margins pair by seed, so the seed sets must match across targets."""
    adapter = FakeAdapter(frozenset({ConfidenceMetric.IPSAE}))
    results = fold(design(), ["T+", "D1"], [7, 8], adapter)
    by_target: dict[str, set[int]] = {}
    for r in results:
        by_target.setdefault(r.target, set()).add(r.seed)
    assert by_target["T+"] == by_target["D1"] == {7, 8}


def test_repeated_seeds_are_refused() -> None:
    with pytest.raises(FoldError, match="distinct"):
        fold(design(), ["T+"], [1, 1], FakeAdapter(frozenset()))


def test_folding_with_no_target_or_no_seed_is_refused() -> None:
    adapter = FakeAdapter(frozenset())
    with pytest.raises(FoldError, match="at least one target"):
        fold(design(), [], [1], adapter)
    with pytest.raises(FoldError, match="at least one seed"):
        fold(design(), ["T+"], [], adapter)


# --- FoldResult schema ------------------------------------------------------


def test_a_result_must_name_its_model_and_weights() -> None:
    for field in ("model", "model_weights_sha256", "design_id"):
        kwargs = {
            "design_id": "d",
            "target": "T+",
            "model": "m",
            "model_weights_sha256": "abc",
            "seed": 1,
            "coordinates": np.zeros((2, 3)),
            "confidence": (),
            "chain_ids": ("A",),
            "wall_time_s": 0.0,
        }
        kwargs[field] = ""
        with pytest.raises(FoldError, match=field):
            FoldResult(**kwargs)  # type: ignore[arg-type]


def test_confidence_metrics_must_be_sorted_for_reproducibility() -> None:
    with pytest.raises(FoldError, match="must be sorted"):
        FoldResult(
            design_id="d",
            target="T+",
            model="m",
            model_weights_sha256="abc",
            seed=1,
            coordinates=np.zeros((2, 3)),
            confidence=(("iptm", 0.7), ("ipsae", 0.6)),
            chain_ids=("A",),
            wall_time_s=0.0,
        )


def test_confidence_from_sorts_whatever_order_it_is_given() -> None:
    assert confidence_from({"iptm": 0.7, "ipsae": 0.6}) == (("ipsae", 0.6), ("iptm", 0.7))


def test_a_missing_metric_names_what_is_available() -> None:
    result = FakeAdapter(frozenset()).predict(design(), "T+", 1)
    assert result.value("ipsae") == pytest.approx(0.6)
    with pytest.raises(FoldError, match="plddt"):
        result.value("plddt")


# --- SETUP section 5: does the objective have an input at all? --------------


def test_ipsae_emitted_directly_is_enough() -> None:
    assert objective_has_an_input(frozenset({ConfidenceMetric.IPSAE}))


def test_a_pae_matrix_plus_chain_assignments_is_enough() -> None:
    """Section 5's second pass condition: ipSAE is derivable from those two."""
    assert objective_has_an_input(
        frozenset({ConfidenceMetric.PAE_MATRIX, ConfidenceMetric.CHAIN_ASSIGNMENTS})
    )


def test_summary_scores_alone_are_not_enough() -> None:
    """If this is the whole stack, section 7.1 has no input and the plan changes."""
    assert not objective_has_an_input(
        frozenset({ConfidenceMetric.IPTM, ConfidenceMetric.PTM, ConfidenceMetric.PLDDT})
    )


def test_a_pae_matrix_without_chain_assignments_is_not_enough() -> None:
    assert not objective_has_an_input(frozenset({ConfidenceMetric.PAE_MATRIX}))


# --- Registry ---------------------------------------------------------------


def test_a_duplicate_adapter_name_fails_loudly() -> None:
    registry = AdapterRegistry()
    registry.register(FakeAdapter(frozenset(), "protenix"))
    with pytest.raises(FoldError, match="already registered"):
        registry.register(FakeAdapter(frozenset(), "protenix"))


def test_an_unknown_model_names_the_valid_ones() -> None:
    registry = AdapterRegistry()
    registry.register(FakeAdapter(frozenset(), "boltz"))
    with pytest.raises(FoldError, match="boltz"):
        registry.get("protenix")


def test_the_registry_reports_which_models_can_feed_the_objective() -> None:
    registry = AdapterRegistry()
    registry.register(FakeAdapter(frozenset({ConfidenceMetric.IPSAE}), "has_ipsae"))
    registry.register(
        FakeAdapter(
            frozenset({ConfidenceMetric.PAE_MATRIX, ConfidenceMetric.CHAIN_ASSIGNMENTS}),
            "has_pae",
        )
    )
    registry.register(FakeAdapter(frozenset({ConfidenceMetric.IPTM}), "summary_only"))
    assert registry.names() == ("has_ipsae", "has_pae", "summary_only")
    assert registry.usable() == ("has_ipsae", "has_pae")
