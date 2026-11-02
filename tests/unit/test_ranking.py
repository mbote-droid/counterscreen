"""The registered ranking rule (PREREGISTRATION.md section 4)."""

import inspect
import random

import pytest

from counterscreen.core.design import Arm
from counterscreen.rank.ranking import RankEntry, RankingError, rank_arm, tie_groups

TOLERANCE = 0.1  # stands in for 0.5 x pooled SD


def entry(
    design_id: str,
    m_mut: float,
    *,
    m_pep: float = 0.0,
    confidence: float = 0.0,
    ddg: float | None = None,
    arm: Arm = Arm.M1,
) -> RankEntry:
    return RankEntry(
        design_id=design_id,
        arm=arm,
        m_mut=m_mut,
        m_pep=m_pep,
        target_confidence=confidence,
        ddg_spec=ddg,
    )


def ids(ranked: tuple[RankEntry, ...]) -> list[str]:
    return [e.design_id for e in ranked]


# --- Criterion 1: M_mut descending ------------------------------------------


def test_m_mut_is_the_primary_criterion() -> None:
    ranked = rank_arm([entry("a", 0.1), entry("b", 0.9), entry("c", 0.5)], TOLERANCE)
    assert ids(ranked) == ["b", "c", "a"]


def test_a_clear_m_mut_lead_is_not_overturned_by_m_pep() -> None:
    """Separation beyond the tolerance means no tie, whatever M_pep says."""
    ranked = rank_arm([entry("lead", 0.90, m_pep=0.0), entry("trail", 0.50, m_pep=9.9)], TOLERANCE)
    assert ids(ranked) == ["lead", "trail"]


# --- Criterion 2: ties broken by M_pep --------------------------------------


def test_designs_within_the_tolerance_are_broken_by_m_pep() -> None:
    ranked = rank_arm([entry("a", 0.50, m_pep=0.1), entry("b", 0.55, m_pep=0.9)], TOLERANCE)
    assert ids(ranked) == ["b", "a"]

    flipped = rank_arm([entry("a", 0.55, m_pep=0.1), entry("b", 0.50, m_pep=0.9)], TOLERANCE)
    assert ids(flipped) == ["b", "a"]  # lower M_mut wins on M_pep inside a tie


# --- Criterion 3: remaining ties broken by confidence ------------------------


def test_remaining_ties_are_broken_by_confidence_against_the_target() -> None:
    ranked = rank_arm(
        [
            entry("a", 0.50, m_pep=0.5, confidence=0.70),
            entry("b", 0.52, m_pep=0.5, confidence=0.90),
        ],
        TOLERANCE,
    )
    assert ids(ranked) == ["b", "a"]


# --- Position 4: ddG_spec, M1 only ------------------------------------------


def test_ddg_spec_breaks_a_remaining_tie_in_m1() -> None:
    ranked = rank_arm(
        [
            entry("a", 0.5, m_pep=0.5, confidence=0.5, ddg=1.0, arm=Arm.M1),
            entry("b", 0.5, m_pep=0.5, confidence=0.5, ddg=4.0, arm=Arm.M1),
        ],
        TOLERANCE,
    )
    assert ids(ranked) == ["b", "a"]


@pytest.mark.parametrize("arm", [Arm.M2, Arm.M3])
def test_ddg_spec_cannot_move_a_design_outside_m1(arm: Arm) -> None:
    """CLAUDE section 7.2: weighting it for M2 or M3 would delete those arms."""
    base = [
        entry("a", 0.5, m_pep=0.5, confidence=0.5, ddg=1.0, arm=arm),
        entry("b", 0.5, m_pep=0.5, confidence=0.5, ddg=9.0, arm=arm),
    ]
    swapped = [
        entry("a", 0.5, m_pep=0.5, confidence=0.5, ddg=9.0, arm=arm),
        entry("b", 0.5, m_pep=0.5, confidence=0.5, ddg=1.0, arm=arm),
    ]
    assert ids(rank_arm(base, TOLERANCE)) == ids(rank_arm(swapped, TOLERANCE))


def test_a_missing_ddg_does_not_crash_m1_ranking() -> None:
    ranked = rank_arm(
        [
            entry("a", 0.5, m_pep=0.5, confidence=0.5, ddg=None),
            entry("b", 0.5, m_pep=0.5, confidence=0.5, ddg=2.0),
        ],
        TOLERANCE,
    )
    assert ids(ranked) == ["b", "a"]


# --- No weighted composite --------------------------------------------------


def test_no_weighting_can_be_supplied() -> None:
    """Section 4 forbids a weighted composite, so there is nothing to weight."""
    parameters = set(inspect.signature(rank_arm).parameters)
    assert parameters == {"entries", "tie_tolerance"}
    assert not any("weight" in name for name in parameters)


# --- Determinism ------------------------------------------------------------


def test_ranking_does_not_depend_on_input_order() -> None:
    entries = [entry(f"d{i}", m_mut=i / 10, m_pep=(i % 3) / 10) for i in range(12)]
    expected = ids(rank_arm(entries, TOLERANCE))
    # Seeded shuffle to probe order-independence; not cryptographic.
    shuffler = random.Random(20261102)  # noqa: S311
    for _ in range(8):
        shuffled = entries[:]
        shuffler.shuffle(shuffled)
        assert ids(rank_arm(shuffled, TOLERANCE)) == expected


def test_designs_equal_on_every_criterion_still_have_one_definite_order() -> None:
    entries = [
        entry("zz", 0.5, m_pep=0.5, confidence=0.5),
        entry("aa", 0.5, m_pep=0.5, confidence=0.5),
    ]
    assert ids(rank_arm(entries, TOLERANCE)) == ["aa", "zz"]


# --- Tie grouping chains, and the test says so ------------------------------


def test_the_tie_rule_chains_across_a_gradual_spread() -> None:
    """Documented behaviour, not a hidden one.

    Each design is within the tolerance of the one above it, so all five form
    one tie group even though the first and last are half a unit apart.
    """
    entries = [entry(f"d{i}", m_mut=1.0 - 0.09 * i) for i in range(5)]
    assert tie_groups(entries, TOLERANCE) == (("d0", "d1", "d2", "d3", "d4"),)


def test_a_gap_wider_than_the_tolerance_splits_the_group() -> None:
    entries = [entry("a", 1.0), entry("b", 0.95), entry("c", 0.5)]
    assert tie_groups(entries, TOLERANCE) == (("a", "b"), ("c",))


def test_a_zero_tolerance_ties_only_exact_equals() -> None:
    entries = [entry("a", 1.0), entry("b", 1.0), entry("c", 0.99)]
    assert tie_groups(entries, 0.0) == (("a", "b"), ("c",))


# --- Refusals ---------------------------------------------------------------


def test_mixing_arms_is_refused() -> None:
    with pytest.raises(RankingError, match="one arm at a time"):
        rank_arm([entry("a", 0.5, arm=Arm.M1), entry("b", 0.5, arm=Arm.M2)], TOLERANCE)


def test_a_negative_tolerance_is_refused() -> None:
    with pytest.raises(RankingError, match="not be negative"):
        rank_arm([entry("a", 0.5)], -0.1)


def test_an_empty_arm_ranks_to_nothing() -> None:
    assert rank_arm([], TOLERANCE) == ()
    assert tie_groups([], TOLERANCE) == ()
