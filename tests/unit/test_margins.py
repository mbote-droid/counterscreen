"""Specificity margins, including the three registered mutants of CLAUDE section 12.4b."""

import statistics
from collections.abc import Mapping

import pytest

from counterscreen.score.margins import (
    ArmScores,
    CounterScreen,
    MarginError,
    TargetRole,
    pooled_sd,
    summarise,
)


def screen(
    design_id: str = "d0",
    target: Mapping[int, float] | None = None,
    mutation: Mapping[int, float] | None = None,
    peptide_free: Mapping[int, float] | None = None,
    variants: Mapping[str, Mapping[int, float]] | None = None,
) -> CounterScreen:
    arms = [
        ArmScores.create("T+", TargetRole.TARGET, target or {1: 0.80, 2: 0.82}),
        ArmScores.create("D1", TargetRole.MUTATION_DECOY, mutation or {1: 0.50, 2: 0.52}),
        ArmScores.create("D2", TargetRole.PEPTIDE_FREE_DECOY, peptide_free or {1: 0.20, 2: 0.22}),
    ]
    for label, scores in (variants or {}).items():
        arms.append(ArmScores.create(label, TargetRole.VARIANT_DECOY, scores))
    return CounterScreen(design_id=design_id, metric="ipsae", arms=tuple(arms))


# --- Registered mutant 1: invert the sign of M_mut --------------------------


def test_m_mut_is_target_minus_decoy_not_the_reverse() -> None:
    margin = screen().m_mut()
    assert [seed for seed, _ in margin.per_seed] == [1, 2]
    assert [value for _, value in margin.per_seed] == pytest.approx([0.30, 0.30])
    assert margin.mean == pytest.approx(0.30)
    assert margin.mean > 0


def test_a_design_that_prefers_the_decoy_yields_a_negative_margin() -> None:
    margin = screen(target={1: 0.40, 2: 0.42}, mutation={1: 0.80, 2: 0.82}).m_mut()
    assert margin.mean == pytest.approx(-0.40)
    assert not margin.exceeds_noise(2.0)


def test_the_noise_gate_is_one_sided() -> None:
    """A large negative margin must fail, not pass on magnitude."""
    margin = screen(target={1: 0.10, 2: 0.12}, mutation={1: 0.90, 2: 0.92}).m_mut()
    assert abs(margin.mean) > 0.5
    assert not margin.exceeds_noise(2.0)


# --- Registered mutant 2: pooled SD across designs instead of within --------


def test_pooled_sd_is_measured_within_a_design_not_across_designs() -> None:
    first = screen("A", target={1: 0.80, 2: 0.82}, mutation={1: 0.50, 2: 0.52})
    second = screen("B", target={1: 0.20, 2: 0.22}, mutation={1: 0.10, 2: 0.12})

    within = first.m_mut().pooled_sd
    assert within == pytest.approx(0.0141421, abs=1e-6)

    across = statistics.stdev([*first.arm("T+").values, *second.arm("T+").values])
    assert across > 20 * within

    # DESIGN section 4: getting this backwards inverts the gate. The same
    # design passes on its own seed noise and fails on the between-design
    # spread, which is the signal being ranked.
    assert first.m_mut().exceeds_noise(2.0)
    assert first.m_mut().mean < 2.0 * across


def test_a_counter_screen_cannot_see_another_design() -> None:
    """Structural guard: the wrong quantity is not expressible."""
    fields = set(CounterScreen.__dataclass_fields__)
    assert "design_id" in fields
    # One design id, and arms rather than designs: there is no field through
    # which another design's seed values could reach the pooled SD.
    assert not any("designs" in name for name in fields)
    assert all(isinstance(arm, ArmScores) for arm in screen().arms)


def test_pooled_sd_weights_by_degrees_of_freedom() -> None:
    tight = ArmScores.create("a", TargetRole.TARGET, {1: 1.0, 2: 1.0, 3: 1.0})
    loose = ArmScores.create("b", TargetRole.MUTATION_DECOY, {1: 0.0, 2: 2.0})
    expected = ((3 - 1) * tight.sd**2 + (2 - 1) * loose.sd**2) / ((3 - 1) + (2 - 1))
    assert pooled_sd([tight, loose]) == pytest.approx(expected**0.5)


# --- Registered mutant 3: swap D1 and D2 ------------------------------------


def test_m_mut_reads_the_wild_type_decoy_and_m_pep_the_peptide_free_one() -> None:
    model = screen(
        target={1: 0.90, 2: 0.90},
        mutation={1: 0.60, 2: 0.60},
        peptide_free={1: 0.10, 2: 0.10},
    )
    assert model.m_mut().mean == pytest.approx(0.30)
    assert model.m_pep().mean == pytest.approx(0.80)
    assert model.m_mut().subtrahend == "D1"
    assert model.m_pep().subtrahend == "D2"


def test_roles_are_named_so_decoys_cannot_be_positionally_swapped() -> None:
    model = screen()
    assert model.by_role(TargetRole.MUTATION_DECOY)[0].label == "D1"
    assert model.by_role(TargetRole.PEPTIDE_FREE_DECOY)[0].label == "D2"


def test_a_missing_role_is_refused_rather_than_defaulted() -> None:
    arms = (
        ArmScores.create("T+", TargetRole.TARGET, {1: 0.9, 2: 0.9}),
        ArmScores.create("D1", TargetRole.MUTATION_DECOY, {1: 0.5, 2: 0.5}),
    )
    model = CounterScreen(design_id="d", metric="ipsae", arms=arms)
    with pytest.raises(MarginError, match="exactly one"):
        model.m_pep()


# --- Seed pairing -----------------------------------------------------------


def test_margins_pair_by_seed_identity() -> None:
    model = screen(target={1: 1.0, 2: 0.0}, mutation={1: 0.0, 2: 1.0})
    per_seed = model.m_mut().per_seed
    assert [seed for seed, _ in per_seed] == [1, 2]
    assert [value for _, value in per_seed] == pytest.approx([1.0, -1.0])
    assert model.m_mut().mean == pytest.approx(0.0)


def test_arms_scored_at_different_seeds_are_refused() -> None:
    arms = (
        ArmScores.create("T+", TargetRole.TARGET, {1: 0.9, 2: 0.9}),
        ArmScores.create("D1", TargetRole.MUTATION_DECOY, {3: 0.5, 4: 0.5}),
    )
    with pytest.raises(MarginError, match="different seeds"):
        CounterScreen(design_id="d", metric="ipsae", arms=arms)


def test_a_single_seed_cannot_support_a_spread() -> None:
    with pytest.raises(MarginError, match="at least 2"):
        ArmScores.create("T+", TargetRole.TARGET, {1: 0.9})


def test_a_repeated_arm_label_is_refused() -> None:
    arms = (
        ArmScores.create("T+", TargetRole.TARGET, {1: 0.9, 2: 0.9}),
        ArmScores.create("T+", TargetRole.MUTATION_DECOY, {1: 0.5, 2: 0.5}),
    )
    with pytest.raises(MarginError, match="repeats an arm label"):
        CounterScreen(design_id="d", metric="ipsae", arms=arms)


def test_a_screen_without_a_target_is_refused() -> None:
    arms = (
        ArmScores.create("D1", TargetRole.MUTATION_DECOY, {1: 0.5, 2: 0.5}),
        ArmScores.create("D2", TargetRole.PEPTIDE_FREE_DECOY, {1: 0.4, 2: 0.4}),
    )
    with pytest.raises(MarginError, match="no target arm"):
        CounterScreen(design_id="d", metric="ipsae", arms=arms)


def test_a_non_finite_confidence_is_refused() -> None:
    with pytest.raises(MarginError, match="non-finite"):
        ArmScores.create("T+", TargetRole.TARGET, {1: 0.9, 2: float("nan")})


# --- M_var ------------------------------------------------------------------


def test_m_var_uses_the_worst_variant_decoy() -> None:
    model = screen(
        target={1: 0.90, 2: 0.90},
        variants={"D3": {1: 0.30, 2: 0.30}, "D4": {1: 0.70, 2: 0.70}},
    )
    # max over D3..D5 is D4, so the margin reflects the hardest decoy.
    assert model.m_var().mean == pytest.approx(0.20)


def test_m_var_without_variant_decoys_is_refused() -> None:
    with pytest.raises(MarginError, match="no variant decoys"):
        screen().m_var()


# --- Distribution reporting -------------------------------------------------


def test_summarise_reports_a_distribution_not_a_point_value() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    distribution = summarise(values, passing=[False, False, True, True, True])
    assert distribution.count == 5
    assert distribution.passing == 3
    assert distribution.median == pytest.approx(3.0)
    assert distribution.minimum == pytest.approx(1.0)
    assert distribution.maximum == pytest.approx(5.0)
    assert distribution.iqr == pytest.approx(distribution.q3 - distribution.q1)


def test_summarising_nothing_is_refused() -> None:
    with pytest.raises(MarginError, match="empty sample"):
        summarise([])
