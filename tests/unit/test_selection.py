"""The registered selection procedure (PREREGISTRATION.md section 4, steps 4-6)."""

import pytest

from counterscreen.core.config import SUBMITTED_DESIGNS, SelectionConfig
from counterscreen.core.design import Arm
from counterscreen.rank.ranking import RankEntry, RankingError
from counterscreen.rank.selection import promote, select

CONTROL = "affinity-only"


def arm_entries(arm: Arm, count: int, prefix: str) -> list[RankEntry]:
    """Build representatives for one arm, already ranked best first."""
    return [
        RankEntry(
            design_id=f"{prefix}{i}",
            arm=arm,
            m_mut=1.0 - i / 100,
            m_pep=0.5,
            target_confidence=0.8,
        )
        for i in range(count)
    ]


def full_pool(extra: int = 3) -> dict[Arm, list[RankEntry]]:
    return {
        Arm.M1: arm_entries(Arm.M1, 9 + extra, "m1_"),
        Arm.M2: arm_entries(Arm.M2, 5 + extra, "m2_"),
        Arm.M3: arm_entries(Arm.M3, 4 + extra, "m3_"),
    }


# --- Step 4: fill the allocation --------------------------------------------


def test_the_registered_allocation_is_filled() -> None:
    selection = select(full_pool(), CONTROL)
    # The reserve is drawn from any mechanism, so it is excluded before
    # counting what each arm's own allocation contributed.
    allocated = [d for d in selection.submitted if d not in {CONTROL, selection.reserve}]
    assert sum(1 for d in allocated if d.startswith("m1_")) == 9
    assert sum(1 for d in allocated if d.startswith("m2_")) == 5
    assert sum(1 for d in allocated if d.startswith("m3_")) == 4
    assert selection.complete


def test_the_submission_holds_exactly_twenty_designs() -> None:
    selection = select(full_pool(), CONTROL)
    assert len(selection.submitted) == SUBMITTED_DESIGNS


def test_each_arm_takes_its_best_representatives() -> None:
    selection = select(full_pool(), CONTROL)
    chosen = [d for d in selection.submitted if d.startswith("m1_")]
    assert chosen == [f"m1_{i}" for i in range(9)]


def test_no_design_appears_twice() -> None:
    selection = select(full_pool(), CONTROL)
    assert len(set(selection.submitted)) == len(selection.submitted)


# --- Step 5: the affinity-only control at rank 10 ---------------------------


def test_the_affinity_control_lands_at_rank_ten() -> None:
    """M1 takes ranks 1-9, so the control falls at 10 without any interleaving."""
    selection = select(full_pool(), CONTROL)
    assert selection.affinity_control_rank == 10
    assert selection.submitted[9] == CONTROL
    assert selection.rank_of(CONTROL) == 10


def test_the_control_is_not_also_drawn_from_an_arm() -> None:
    pool = full_pool()
    pool[Arm.M1].insert(0, RankEntry(CONTROL, Arm.M1, 9.9, 9.9, 9.9))
    selection = select(pool, CONTROL)
    assert selection.submitted.count(CONTROL) == 1
    assert selection.affinity_control_rank == 10


# --- Reserve ----------------------------------------------------------------


def test_the_reserve_is_the_best_remaining_representative_across_arms() -> None:
    pool = full_pool(extra=0)
    strong = RankEntry("spare", Arm.M2, m_mut=5.0, m_pep=5.0, target_confidence=0.9)
    pool[Arm.M2].append(strong)
    selection = select(pool, CONTROL)
    assert selection.reserve == "spare"
    assert selection.submitted[-1] == "spare"


def test_with_nothing_left_over_there_is_no_reserve() -> None:
    selection = select(full_pool(extra=0), CONTROL)
    assert selection.reserve is None
    assert len(selection.submitted) == SUBMITTED_DESIGNS - 1


# --- Shortfalls are reported, not rebalanced --------------------------------


def test_a_short_arm_is_recorded_rather_than_topped_up_from_elsewhere() -> None:
    """Short arms stay short.

    Moving a slot between arms after seeing how many survived would change
    the registered allocation, which is what the pre-registration prevents.
    """
    pool = full_pool()
    pool[Arm.M3] = arm_entries(Arm.M3, 1, "m3_")
    selection = select(pool, CONTROL)
    assert selection.shortfalls == ((Arm.M3, 3),)
    assert not selection.complete
    allocated = [d for d in selection.submitted if d not in {CONTROL, selection.reserve}]
    assert sum(1 for d in allocated if d.startswith("m1_")) == 9
    assert sum(1 for d in allocated if d.startswith("m3_")) == 1


def test_an_empty_arm_reports_its_whole_allocation_as_short() -> None:
    pool = full_pool()
    pool[Arm.M2] = []
    selection = select(pool, CONTROL)
    assert (Arm.M2, 5) in selection.shortfalls


# --- Step 6: promotion on a prescreen flag ----------------------------------


def test_a_flagged_design_is_replaced_by_the_next_representative() -> None:
    pool = full_pool()
    before = select(pool, CONTROL)
    assert "m1_0" in before.submitted

    after = promote(pool, CONTROL, flagged=frozenset({"m1_0"}))
    assert "m1_0" not in after.submitted
    assert "m1_9" in after.submitted
    allocated = [d for d in after.submitted if d not in {CONTROL, after.reserve}]
    assert sum(1 for d in allocated if d.startswith("m1_")) == 9
    assert after.complete


def test_promotion_keeps_the_control_at_rank_ten() -> None:
    pool = full_pool()
    after = promote(pool, CONTROL, flagged=frozenset({"m1_0", "m1_1"}))
    assert after.affinity_control_rank == 10
    assert after.submitted[9] == CONTROL


def test_promotion_records_what_was_excluded() -> None:
    after = promote(full_pool(), CONTROL, flagged=frozenset({"m2_0"}))
    assert after.excluded == ("m2_0",)


def test_flagging_more_than_an_arm_can_replace_reports_a_shortfall() -> None:
    pool = full_pool(extra=0)
    flagged = frozenset({f"m3_{i}" for i in range(3)})
    after = promote(pool, CONTROL, flagged=flagged)
    assert (Arm.M3, 3) in after.shortfalls


# --- Configuration ----------------------------------------------------------


def test_the_allocation_comes_from_the_registered_config() -> None:
    config = SelectionConfig()
    assert (config.m1, config.m2, config.m3) == (9, 5, 4)
    assert config.total == SUBMITTED_DESIGNS


def test_asking_for_a_rank_of_an_unselected_design_is_refused() -> None:
    selection = select(full_pool(), CONTROL)
    with pytest.raises(RankingError, match="not in the submission list"):
        selection.rank_of("nonexistent")
