"""The registered confidence level, and the quantile derived from it.

Two separate reasons this is a module constant rather than a configuration
field, and they point the same way.

**It is not a free parameter.** `PREREGISTRATION.md` §7b registers the
false-accept rate as a point estimate with an interval, and the width of that
interval is the headline result. A confidence level that could be set per run
could be narrowed to 90% once the interval turned out wider than hoped, which
is the same researcher freedom G2's missing configuration field exists to
remove.

**It must not drift from the quantile.** The level and the normal quantile are
two numbers that have to agree, so only one of them is written down:
:data:`Z_TWO_SIDED` is computed from :data:`CONFIDENCE_LEVEL` at import. A
level changed in one place and a quantile left behind in another is not a
possible state.

:func:`level_label` renders the level for prose, so that documents cite it
through a key like any other number rather than carrying "95%" by hand --
`DESIGN.md` §9b, and the decision recorded against `BUILD_JOURNAL.md`
ISSUE-011.
"""

import statistics

#: Two-sided interval coverage. `METHODS.md` section 8.5.
CONFIDENCE_LEVEL = 0.95

#: The two-sided normal quantile for :data:`CONFIDENCE_LEVEL`, derived rather
#: than typed: 1.959963984540054 at 95%.
Z_TWO_SIDED = statistics.NormalDist().inv_cdf(0.5 + CONFIDENCE_LEVEL / 2.0)


def level_label() -> str:
    """Render the level as prose would write it, e.g. ``95%``."""
    return f"{CONFIDENCE_LEVEL * 100:g}%"
