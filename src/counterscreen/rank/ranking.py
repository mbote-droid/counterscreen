"""The registered ranking rule of `PREREGISTRATION.md` section 4.

Within each mechanism arm: ``M_mut`` descending; ties within half a pooled SD
broken by ``M_pep`` descending; remaining ties broken by confidence against
T+; and for the M1 arm only, a fourth tiebreak on delta-delta-G_spec.

**No weighted composite exists here, and that is the point.** Section 4 is
explicit that a weighted sum would require choosing weights, and any weight
chosen after seeing the score distributions is a post-hoc decision disguised
as a formula. There is no weights argument to pass, so the composite cannot
be reintroduced by configuration.

**delta-delta-G_spec is confined to M1 by construction.** `PROTOCOL.md` section
7.2 gives the reason: in-place mutation with local repack measures loss of
direct side-chain contact, which M3 does not operate through at all and M2
operates through only unreliably. Used more widely it would systematically
delete the two differentiated arms. Here it is read only when the arm is M1,
and a test asserts that changing it cannot move an M2 or M3 design.

Two interpretations were necessary; both are recorded rather than assumed.

*What "within 0.5 x pooled SD of each other" groups.* A tolerance comparison
is not transitive -- A may be close to B and B to C while A and C are far
apart -- so it does not by itself define an order. The reading implemented is
the literal one: sort on ``M_mut``, then group runs of designs where each is
within the tolerance of the one above it. This is deterministic and depends on
nothing but the input. It does chain: a long, gradual spread of designs each
just inside the tolerance becomes a single tie group, which a test
demonstrates rather than hides.

*Which pooled SD sets the tolerance.* The specification is not single-voiced.
`PROTOCOL.md` section 7.1 and `DESIGN.md` section 4 define pooled SD per design,
across that design's seeds; `PROTOCOL.md` section 10 and `PREREGISTRATION.md`
section 5 describe a campaign-level noise floor measured once from five
identical Day-1 runs. Amendment A9 settles it on the campaign floor, because a
per-design SD makes the comparison asymmetric -- A inside B's tolerance while B
sits outside A's -- and a grouping that depends on which design is read first
is not a reproducible rank. These functions therefore take a
:class:`counterscreen.core.noise.NoiseFloor` and derive the tolerance from it;
there is no float to pass, so a design's own SD cannot be supplied in its
place.
"""

import dataclasses
import itertools
from collections.abc import Sequence

from counterscreen.core.design import Arm
from counterscreen.core.noise import NoiseFloor


class RankingError(ValueError):
    """Raised when designs cannot be ranked as registered."""


@dataclasses.dataclass(frozen=True, slots=True)
class RankEntry:
    """One design's ranking inputs.

    ``ddg_spec`` is a ranking statistic, never an affinity. Rosetta reports
    Rosetta Energy Units and the open fallback reports kcal/mol; whichever
    path was taken is recorded with the run, per `PROTOCOL.md` section 7.3.
    Higher is more specific for the mutant, since it is
    ``delta-G(binder.WT) - delta-G(binder.G12D)``.
    """

    design_id: str
    arm: Arm
    m_mut: float
    m_pep: float
    target_confidence: float
    ddg_spec: float | None = None


def _tiebreak_key(entry: RankEntry, *, use_ddg: bool) -> tuple[float, float, float, str]:
    """Sort key inside a tie group: M_pep, then confidence, then M1-only ddG.

    ``design_id`` closes the key so that designs equal on every registered
    criterion still have one definite order. Without it the result would
    depend on input order, and a pre-registered ranking that is not
    reproducible is not registered.
    """
    ddg = -(entry.ddg_spec or 0.0) if use_ddg else 0.0
    return (-entry.m_pep, -entry.target_confidence, ddg, entry.design_id)


def rank_arm(entries: Sequence[RankEntry], floor: NoiseFloor) -> tuple[RankEntry, ...]:
    """Rank one mechanism arm by the registered rule.

    The tolerance comes from ``floor`` rather than from an argument, so no
    number chosen after the scores were seen can widen or narrow a tie group.
    """
    tie_tolerance = floor.tie_tolerance()
    arms = {entry.arm for entry in entries}
    if len(arms) > 1:
        msg = f"rank_arm ranks one arm at a time, got {sorted(str(a) for a in arms)}"
        raise RankingError(msg)
    if not entries:
        return ()

    use_ddg = arms == {Arm.M1}
    ordered = sorted(entries, key=lambda e: (-e.m_mut, e.design_id))

    groups: list[list[RankEntry]] = [[ordered[0]]]
    for above, entry in itertools.pairwise(ordered):
        if above.m_mut - entry.m_mut <= tie_tolerance:
            groups[-1].append(entry)
        else:
            groups.append([entry])

    ranked: list[RankEntry] = []
    for group in groups:
        ranked.extend(sorted(group, key=lambda e: _tiebreak_key(e, use_ddg=use_ddg)))
    return tuple(ranked)


def tie_groups(entries: Sequence[RankEntry], floor: NoiseFloor) -> tuple[tuple[str, ...], ...]:
    """Expose the tie grouping, so chaining is visible rather than implicit."""
    if not entries:
        return ()
    tie_tolerance = floor.tie_tolerance()
    ordered = sorted(entries, key=lambda e: (-e.m_mut, e.design_id))
    groups: list[list[str]] = [[ordered[0].design_id]]
    for above, entry in itertools.pairwise(ordered):
        if above.m_mut - entry.m_mut <= tie_tolerance:
            groups[-1].append(entry.design_id)
        else:
            groups.append([entry.design_id])
    return tuple(tuple(group) for group in groups)
