"""The registered selection procedure of `PREREGISTRATION.md` section 4.

Fill the allocation from cluster representatives, place the affinity-only
control at approximately rank 10, and promote the next representative wherever
the prescreen raises a flag.

**The control's rank is explicit, not incidental.** An earlier version of
this module derived it: M1 held nine slots, so filling arms in order put the
control at rank 10 by arithmetic. Amendment A7 then moved M1 to four and M3 to
nine, which would silently have placed the control at rank 5. Since
`CLAUDE.md` section 11 asks for approximately rank 10 *so that it is still
tested if only part of the list is selected*, a rank that drifts with the
allocation defeats the purpose. It now comes from
``SelectionConfig.affinity_control_rank`` and is clamped to the list length.

**Why the control sits there at all.** It is the design that would win if
ranked on confidence against T+ alone, ignoring specificity. Section 11 puts
it mid-list so it is still tested if only part of the list is selected, and
`PREREGISTRATION.md` section 6 makes it the falsification test for H2: if the
affinity-only control performs as well as the specificity-ranked designs in
the returned data, the objective this whole pipeline is built on was wrong.

**Shortfalls are reported, never silently rebalanced.** If an arm has fewer
representatives than its allocation, that slot stays empty and the shortfall
is recorded. Moving it to another arm would change the registered allocation
after seeing how many designs survived, which is the kind of quiet adjustment
the pre-registration exists to prevent.

One tension is resolved here and flagged rather than hidden. Section 11 calls
the reserve "highest composite, any mechanism", but `PREREGISTRATION.md`
section 4 registers that no weighted composite is used. With no composite to
rank on, the reserve is taken as the highest remaining ``M_mut`` across arms,
which is the primary criterion of the registered rule.
"""

import dataclasses
from collections.abc import Mapping, Sequence

from counterscreen.core.config import SUBMITTED_DESIGNS, SelectionConfig
from counterscreen.core.design import Arm
from counterscreen.rank.ranking import RankEntry, RankingError

#: Arms are filled in this order, which is what places the control at rank 10.
ARM_ORDER: tuple[Arm, ...] = (Arm.M1, Arm.M2, Arm.M3)


@dataclasses.dataclass(frozen=True, slots=True)
class Selection:
    """The submission list, and what it could not fill."""

    submitted: tuple[str, ...]
    affinity_control: str
    affinity_control_rank: int
    reserve: str | None
    shortfalls: tuple[tuple[Arm, int], ...]
    excluded: tuple[str, ...]

    @property
    def complete(self) -> bool:
        """Whether every allocated slot was filled."""
        return not self.shortfalls

    def rank_of(self, design_id: str) -> int:
        """One-based rank of a design in the submission list."""
        for index, candidate in enumerate(self.submitted, start=1):
            if candidate == design_id:
                return index
        msg = f"{design_id!r} is not in the submission list"
        raise RankingError(msg)


def _allocation(config: SelectionConfig) -> Mapping[Arm, int]:
    return {Arm.M1: config.m1, Arm.M2: config.m2, Arm.M3: config.m3}


def select(
    representatives: Mapping[Arm, Sequence[RankEntry]],
    affinity_control: str,
    config: SelectionConfig | None = None,
    excluded: frozenset[str] = frozenset(),
) -> Selection:
    """Fill the registered allocation from each arm's ranked representatives.

    ``representatives`` is each arm's cluster representatives, already ranked
    by :func:`counterscreen.rank.ranking.rank_arm`. Anything in ``excluded``
    is passed over, which is how a prescreen flag promotes the next
    representative.
    """
    settings = config or SelectionConfig()
    allocation = _allocation(settings)

    picked: dict[Arm, list[RankEntry]] = {}
    shortfalls: list[tuple[Arm, int]] = []
    for arm in ARM_ORDER:
        available = [
            entry
            for entry in representatives.get(arm, ())
            if entry.design_id not in excluded and entry.design_id != affinity_control
        ]
        wanted = allocation[arm]
        picked[arm] = available[:wanted]
        if len(picked[arm]) < wanted:
            shortfalls.append((arm, wanted - len(picked[arm])))

    chosen_ids = {entry.design_id for entries in picked.values() for entry in entries}
    leftovers = [
        entry
        for arm in ARM_ORDER
        for entry in representatives.get(arm, ())
        if entry.design_id not in chosen_ids
        and entry.design_id not in excluded
        and entry.design_id != affinity_control
    ]
    reserve: str | None = None
    if settings.reserve and leftovers:
        best = min(leftovers, key=lambda e: (-e.m_mut, -e.m_pep, e.design_id))
        reserve = best.design_id

    from_arms: list[str] = [entry.design_id for arm in ARM_ORDER for entry in picked[arm]]
    # Rank 10 of the submitted list, or the end of it if the arms came up
    # short. One-based in the specification, zero-based here.
    control_index = min(max(settings.affinity_control_rank - 1, 0), len(from_arms))
    submitted = [*from_arms[:control_index], affinity_control, *from_arms[control_index:]]
    control_rank = control_index + 1
    if reserve is not None:
        submitted.append(reserve)

    if len(set(submitted)) != len(submitted):
        msg = f"submission list repeats a design: {submitted}"
        raise RankingError(msg)
    if len(submitted) > SUBMITTED_DESIGNS:
        msg = f"submission list holds {len(submitted)} designs, cap is {SUBMITTED_DESIGNS}"
        raise RankingError(msg)

    return Selection(
        submitted=tuple(submitted),
        affinity_control=affinity_control,
        affinity_control_rank=control_rank,
        reserve=reserve,
        shortfalls=tuple(shortfalls),
        excluded=tuple(sorted(excluded)),
    )


def promote(
    representatives: Mapping[Arm, Sequence[RankEntry]],
    affinity_control: str,
    flagged: frozenset[str],
    config: SelectionConfig | None = None,
    already_excluded: frozenset[str] = frozenset(),
) -> Selection:
    """Re-select with prescreen-flagged designs removed.

    Step 6 of the registered procedure: any flag other than ``pass`` removes
    the design and the next cluster representative is promoted. Re-running the
    whole selection rather than patching the list keeps the allocation and the
    control's position exactly as registered.
    """
    return select(
        representatives,
        affinity_control,
        config=config,
        excluded=already_excluded | flagged,
    )
