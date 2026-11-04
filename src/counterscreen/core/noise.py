"""The campaign noise floor, and the single reading of ``pooled SD``.

`PROTOCOL.md` section 7.1 and `DESIGN.md` section 4 define ``pooled SD`` per
design, across that design's seeds. `PROTOCOL.md` section 10 and
`PREREGISTRATION.md` section 5 define a campaign-level noise floor measured
once from five identical runs. The same symbol sets G4's denominator and the
ranking tie tolerance, and the two readings give different gate verdicts and
different orderings. `DECISIONS.md` D-5 recorded the degeneracy and left it
open rather than resolving it by preference; amendment A9 closes it.

**G4 takes the larger of the two.** Each reading fails in a direction the
other does not. A within-design pooled SD rests on four degrees of freedom per
arm, so the estimate is itself volatile, and it sits in the denominator of a
ratio test: across a few hundred designs, the ones whose seeds happened to
agree get a small denominator and pass on luck. That is the selection effect
that per-gene variance produces in differential-expression testing, and the
reason moderated estimators exist there. The campaign floor is estimated once
and well, but from one input, so it cannot see that a floppy design really is
noisier than a rigid one. ``max`` of the two is weaker than neither, is
parameter-free, and moves errors toward false rejects, which cost a design,
rather than false accepts, which cost a wet-lab slot.

**The tie tolerance takes the campaign floor alone.** The tolerance compares
*two different designs*, and a per-design SD makes that comparison asymmetric:
A would fall within B's tolerance while B fell outside A's, so the grouping
would depend on which design was read first. One campaign number keeps the
tolerance a property of the measurement rather than of whichever designs
happen to be in the input, which is what the registered rank needs to be
reproducible.

The fraction is a module constant and not a configuration field, for the
reason G2 has no configuration field: a tolerance that could be retuned after
the rankings were seen would be a free parameter underneath a registered rule.
"""

import dataclasses
import math

# PREREGISTRATION.md section 4 step 1: ties within half a pooled SD.
TIE_TOLERANCE_SD_FRACTION = 0.5
# PREREGISTRATION.md section 5 (amendment A6), PROTOCOL.md section 10.
REGISTERED_REPEATS = 5


class NoiseFloorError(ValueError):
    """Raised when a noise floor is not the measured quantity it claims to be."""


@dataclasses.dataclass(frozen=True, slots=True)
class NoiseFloor:
    """The spread of one confidence metric over identical repeat runs.

    Every field is required. A default would let a campaign gate on a floor
    nobody measured, which is the failure `DESIGN.md` section 2 guards against
    for truncation boundaries and the same failure here.
    """

    metric: str
    sd: float
    repeats: int
    source: str

    def __post_init__(self) -> None:
        """Refuse a floor that cannot have come from a real measurement."""
        if not self.metric.strip():
            msg = "noise floor names no metric"
            raise NoiseFloorError(msg)
        if not self.source.strip():
            msg = (
                f"noise floor for {self.metric!r} cites no source; it must point at "
                "the recorded repeat runs it was measured from"
            )
            raise NoiseFloorError(msg)
        if not math.isfinite(self.sd):
            msg = f"noise floor for {self.metric!r} is not finite: {self.sd}"
            raise NoiseFloorError(msg)
        if self.sd <= 0.0:
            msg = (
                f"noise floor for {self.metric!r} is {self.sd}; a stochastic "
                "co-folding model cannot have zero spread across repeats, so a "
                "floor at or below zero means the measurement is wrong"
            )
            raise NoiseFloorError(msg)
        if self.repeats < REGISTERED_REPEATS:
            msg = (
                f"noise floor for {self.metric!r} rests on {self.repeats} repeats; "
                f"PREREGISTRATION.md section 5 registers {REGISTERED_REPEATS}"
            )
            raise NoiseFloorError(msg)

    def gate_denominator(self, within_design_sd: float) -> float:
        """Return the G4 denominator: the larger of the two registered readings."""
        if not math.isfinite(within_design_sd) or within_design_sd < 0.0:
            msg = f"within-design pooled SD is not a usable spread: {within_design_sd}"
            raise NoiseFloorError(msg)
        return max(within_design_sd, self.sd)

    def tie_tolerance(self) -> float:
        """Half the campaign floor, per `PREREGISTRATION.md` section 4 step 1.

        Takes no argument, so the fraction cannot be supplied at the call site.
        """
        return TIE_TOLERANCE_SD_FRACTION * self.sd
