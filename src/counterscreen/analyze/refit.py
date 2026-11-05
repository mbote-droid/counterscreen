"""Independent re-fitting of returned sensorgrams.

`PROTOCOL.md` §12.5 is clear that the returned binary call is not the terminal
output. Adaptyv has noted that its standard fit assumes a **1:1 interaction**
and that further fitting models were being added [R26], and the challenge
counts binding either as a fittable curve with a K_D **or**, where the curve
cannot be fitted, as an association shift clearing 300% over negative control
[R18]. That second class is where the interesting failures live, and consuming
the binary label discards it.

Four things happen here, each from a numbered item of §12.5.

**Every K_D carries its uncertainty.** `DESIGN.md` §8 registers an assertion
that re-fitted values are never bare point estimates, so
:class:`SteadyStateFit` refuses to exist without a finite standard error. A
K_D of 12 nM from a well-determined curve and one from a curve that barely
leaves the baseline are different claims, and a point value cannot tell them
apart.

**The 1:1 assumption is tested, not assumed.** Residual *structure* is what
reveals an inadequate model — a systematically curved residual trace can
accompany a perfectly respectable R². The Wald-Wolfowitz runs test on residual
signs detects exactly that, and needs no alternative model fitted to raise the
alarm.

**Ratios propagate in log space, within a stated validity range.** A
specificity ratio divides two positive, independently fitted quantities
spanning orders of magnitude. Its
sampling distribution is far closer to log-normal than normal, so the interval
is computed on ``ln K_D`` and reported multiplicatively. A symmetric
± interval on the ratio itself can extend below zero, which is not a possible
K_D ratio.

The propagation uses the delta-method identity ``sigma_ln(x) ~= sigma_x / x``,
which is a first-order approximation and degrades as the relative error grows.
Below roughly 30% relative error on each fit it is accurate enough; by 100% it
is unreliable, and a poorly determined fit should have its interval from a
bootstrap over the residuals or from refitting with ``ln K_D`` as the
parameter. :attr:`SteadyStateFit.relative_stderr` is reported alongside every
ratio so a reader can see which regime a given result is in.

**Unfittable curves are classified rather than dropped.** The 300%-shift class
is reported separately, because a design that shifts without fitting is an
ambiguous result and averaging it into either bucket hides that.
"""

import dataclasses
import itertools
import math
import statistics
from collections.abc import Sequence
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from counterscreen.core.intervals import CONFIDENCE_LEVEL, Z_TWO_SIDED

#: The challenge's alternative binding criterion when no K_D can be fitted.
SHIFT_THRESHOLD_PERCENT = 300.0


#: Below this the runs test has no power and is not reported.
MIN_RESIDUALS_FOR_RUNS_TEST = 8

#: A runs-test z below this is systematic residual structure: too few runs
#: for independent noise, which is what an inadequate 1:1 fit looks like.
#:
#: Derived, and **one-sided**. The alternative is directional -- an inadequate
#: model gives *fewer* sign changes, never more -- so the critical value is the
#: 5% quantile, -1.645. This previously held -1.96, which is the *two-sided*
#: 5% quantile and therefore a one-sided test at 2.5%, while `FINDINGS.md`
#: F-8 reported its power "at alpha = 0.05". Halving the stated alpha costs
#: power in a test whose purpose is to *detect* inadequacy, which is the wrong
#: direction to be conservative in: a missed inadequate fit is reported as a
#: K_D, and a spurious one only sends a curve for another look.
RUNS_Z_THRESHOLD = statistics.NormalDist().inv_cdf(1.0 - CONFIDENCE_LEVEL)


#: Accepted input for a measured series: a plain sequence or a numpy array.
Series = Sequence[float] | NDArray[np.float64]


class RefitError(ValueError):
    """Raised when a sensorgram cannot be re-fitted or interpreted."""


class Adequacy(StrEnum):
    """Whether the 1:1 model was tested, and what the test said.

    Three states, not two. ``UNTESTED`` existed before as
    ``one_to_one_adequate`` returning ``True`` with a docstring warning that
    the caller must not read it as adequacy -- a guard made of prose over an
    API that invited the error (`FINDINGS.md` F-8, F-10). A caller now has to
    handle the third case to get an answer at all.
    """

    ADEQUATE = "adequate"
    INADEQUATE = "inadequate"
    UNTESTED = "untested"


class BindingCall(StrEnum):
    """How a curve was classified, per `PROTOCOL.md` §3.5."""

    FITTED = "fitted"
    SHIFT_ONLY = "shift_only"
    NON_BINDER = "non_binder"


def langmuir_steady_state(
    concentration: NDArray[np.float64], r_max: float, kd: float
) -> NDArray[np.float64]:
    """Single-site steady-state binding isotherm, ``R = R_max C / (C + K_D)``."""
    return r_max * concentration / (concentration + kd)


@dataclasses.dataclass(frozen=True, slots=True)
class SteadyStateFit:
    """A fitted isotherm, which cannot exist without its uncertainty.

    It also cannot exist without the concentration range it was fitted over.
    Outside that range ``R_max`` and ``K_D`` are not separately identifiable --
    below it the isotherm is still linear and only the ratio ``R_max / K_D``
    is determined -- so a K_D above the top concentration is an extrapolation
    wearing the clothes of a measurement (`FINDINGS.md` F-17).
    """

    kd: float
    kd_stderr: float
    r_max: float
    r_max_stderr: float
    residuals: tuple[float, ...]
    concentration_low: float
    concentration_high: float

    def __post_init__(self) -> None:
        """Refuse a fit that reports a value without saying how well determined it is."""
        if self.kd <= 0 or not math.isfinite(self.kd):
            msg = f"K_D must be positive and finite, got {self.kd}"
            raise RefitError(msg)
        if not 0.0 < self.concentration_low <= self.concentration_high:
            msg = (
                f"concentration range {self.concentration_low} to "
                f"{self.concentration_high} is not a usable series"
            )
            raise RefitError(msg)
        if not math.isfinite(self.kd_stderr) or self.kd_stderr < 0:
            msg = (
                f"K_D standard error is {self.kd_stderr}, which is not a usable "
                "uncertainty. DESIGN.md section 8: a re-fitted K_D is never a bare "
                "point value, because a well-determined one and a barely-determined "
                "one are different claims"
            )
            raise RefitError(msg)

    @property
    def relative_stderr(self) -> float:
        """Fractional uncertainty on K_D."""
        return self.kd_stderr / self.kd

    @property
    def kd_is_identified(self) -> bool:
        """Whether K_D lies inside the concentration range that was measured.

        The standard SPR requirement, and not a conservative one: a series
        ideally brackets K_D. Outside the range the data constrain only the
        initial slope, so the reported K_D and R_max can trade off against
        each other almost freely while the residuals stay small and the
        standard error stays respectable (`FINDINGS.md` F-17).
        """
        return self.concentration_low <= self.kd <= self.concentration_high

    @property
    def kd_range_multiple(self) -> float:
        """How far outside the measured range K_D sits, as a factor.

        ``1.0`` when inside. Reportable, because "154x above the highest
        concentration tested" says what "K_D = 15 uM" conceals.
        """
        if self.kd > self.concentration_high:
            return self.kd / self.concentration_high
        if self.kd < self.concentration_low:
            return self.concentration_low / self.kd
        return 1.0

    @property
    def residual_runs_z(self) -> float | None:
        """Runs-test z on residual signs, or ``None`` when too few points."""
        return runs_test_z(self.residuals)

    @property
    def one_to_one_adequacy(self) -> Adequacy:
        """Whether the residuals look like independent noise, or were untested.

        An eight-point isotherm -- what a real SPR experiment supplies -- gives
        the runs test no power, so most campaign curves land on
        :attr:`Adequacy.UNTESTED` rather than on a verdict. That is the whole
        content of `FINDINGS.md` F-8 and it is now in the return type.
        """
        z = self.residual_runs_z
        if z is None:
            return Adequacy.UNTESTED
        return Adequacy.ADEQUATE if z > RUNS_Z_THRESHOLD else Adequacy.INADEQUATE


def runs_test_z(residuals: Series) -> float | None:
    """Wald-Wolfowitz runs-test z statistic on residual signs.

    Negative z means fewer sign changes than independent noise would give,
    which is the signature of a systematically curved residual trace and so of
    a model that does not fit the data's shape. Returns ``None`` when there are
    too few residuals for the test to carry information.
    """
    signs = [1 if r > 0 else -1 for r in residuals if r != 0]
    n = len(signs)
    if n < MIN_RESIDUALS_FOR_RUNS_TEST:
        return None
    positives = sum(1 for s in signs if s > 0)
    negatives = n - positives
    if positives == 0 or negatives == 0:
        # Every residual on one side: maximally systematic.
        return -math.inf
    runs = 1 + sum(1 for a, b in itertools.pairwise(signs) if a != b)
    expected = 2.0 * positives * negatives / n + 1.0
    variance = (expected - 1.0) * (expected - 2.0) / (n - 1.0)
    if variance <= 0:
        return None
    return (runs - expected) / math.sqrt(variance)


def fit_steady_state(concentrations: Series, responses: Series) -> SteadyStateFit:
    """Fit a 1:1 steady-state isotherm and return it with its uncertainty."""
    from scipy.optimize import curve_fit  # noqa: PLC0415

    x = np.asarray(concentrations, dtype=np.float64)
    y = np.asarray(responses, dtype=np.float64)
    min_points = 3
    if x.size != y.size:
        msg = f"{x.size} concentrations against {y.size} responses"
        raise RefitError(msg)
    if x.size < min_points:
        msg = f"need at least {min_points} points to fit two parameters, got {x.size}"
        raise RefitError(msg)
    if np.any(x <= 0):
        msg = "concentrations must be positive"
        raise RefitError(msg)

    guess = [float(max(y.max(), 1e-9)), float(np.median(x))]
    try:
        popt, pcov = curve_fit(
            langmuir_steady_state, x, y, p0=guess, maxfev=20000, bounds=(0, np.inf)
        )
    except (RuntimeError, ValueError) as exc:
        msg = f"the 1:1 isotherm did not converge: {exc}"
        raise RefitError(msg) from exc

    errors = np.sqrt(np.diag(np.asarray(pcov, dtype=np.float64)))
    fitted = langmuir_steady_state(x, float(popt[0]), float(popt[1]))
    return SteadyStateFit(
        kd=float(popt[1]),
        kd_stderr=float(errors[1]),
        r_max=float(popt[0]),
        r_max_stderr=float(errors[0]),
        residuals=tuple(float(v) for v in (y - fitted)),
        concentration_low=float(x.min()),
        concentration_high=float(x.max()),
    )


def classify(
    fit: SteadyStateFit | None,
    association_shift_percent: float,
    threshold: float = SHIFT_THRESHOLD_PERCENT,
) -> BindingCall:
    """Classify a curve as fitted, shift-only, or non-binding.

    A fit whose K_D falls outside the concentration range is treated as *not
    fitted*, which is what `PROTOCOL.md` section 3.5's second class is for: a
    curve the series cannot pin a K_D on is exactly the "cannot be fitted"
    case, and it still counts as binding if the association shift clears the
    threshold. The registered three classes are unchanged; what changed is
    that an unidentifiable K_D no longer enters the first one
    (`FINDINGS.md` F-17).
    """
    if fit is not None and fit.kd_is_identified:
        return BindingCall.FITTED
    if association_shift_percent >= threshold:
        return BindingCall.SHIFT_ONLY
    return BindingCall.NON_BINDER


@dataclasses.dataclass(frozen=True, slots=True)
class SpecificityRatio:
    """A K_D ratio with a multiplicative interval, not a ratio of points."""

    ratio: float
    ci_low: float
    ci_high: float
    log_stderr: float

    @property
    def discriminates(self) -> bool:
        """Whether the interval excludes unity.

        A hundredfold point ratio whose interval spans 1 is not evidence of
        discrimination, and reporting the point alone would present it as if
        it were.
        """
        return self.ci_low > 1.0


def specificity_ratio(decoy: SteadyStateFit, target: SteadyStateFit) -> SpecificityRatio:
    """Ratio ``K_D(decoy) / K_D(target)`` with uncertainty propagated in log space.

    Higher is better: the design binds the target more tightly than the decoy.
    Both fits are assumed independent, which holds when they come from
    separate sensorgrams.
    """
    unidentified = [
        name for name, fit in (("decoy", decoy), ("target", target)) if not fit.kd_is_identified
    ]
    if unidentified:
        msg = (
            f"the {' and '.join(unidentified)} K_D lies outside the concentration range "
            "measured, so the ratio would propagate an extrapolation. Report the shift "
            "class or widen the series; PROTOCOL.md section 12.5 and FINDINGS.md F-17"
        )
        raise RefitError(msg)
    ratio = decoy.kd / target.kd
    # Delta method: sigma_ln(x) ~= sigma_x / x. First order, so it degrades as
    # relative error grows; see the module docstring for the validity range.
    log_stderr = math.sqrt(decoy.relative_stderr**2 + target.relative_stderr**2)
    spread = Z_TWO_SIDED * log_stderr
    return SpecificityRatio(
        ratio=ratio,
        ci_low=ratio * math.exp(-spread),
        ci_high=ratio * math.exp(spread),
        log_stderr=log_stderr,
    )
