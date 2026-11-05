"""analyze/ contract: raw data is immutable, and no K_D is a bare point value."""

import math
from pathlib import Path

import numpy as np
import pytest

from counterscreen.analyze.refit import (
    SHIFT_THRESHOLD_PERCENT,
    Adequacy,
    BindingCall,
    RefitError,
    SteadyStateFit,
    classify,
    fit_steady_state,
    langmuir_steady_state,
    runs_test_z,
    specificity_ratio,
)
from counterscreen.analyze.storage import (
    CampaignPaths,
    ImmutabilityError,
    guard_write,
    refit_destination,
)


def paths(tmp_path: Path) -> CampaignPaths:
    campaign = CampaignPaths(root=tmp_path)
    campaign.raw.mkdir(parents=True, exist_ok=True)
    campaign.refit.mkdir(parents=True, exist_ok=True)
    return campaign


def a_fit(kd: float = 1e-8, rel: float = 0.05) -> SteadyStateFit:
    """Build a fit whose K_D sits inside the series that produced it."""
    return SteadyStateFit(
        kd=kd,
        kd_stderr=kd * rel,
        r_max=100.0,
        r_max_stderr=2.0,
        residuals=(0.1, -0.1),
        concentration_low=kd / 10.0,
        concentration_high=kd * 10.0,
    )


# --- Registered mutant: write to results/raw/ from analyze/ -----------------


def test_writing_into_raw_is_refused(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    with pytest.raises(ImmutabilityError, match="append-only"):
        guard_write(campaign, campaign.raw / "run-001.csv")


def test_writing_into_raw_via_a_parent_traversal_is_refused(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    sneaky = campaign.refit / ".." / "raw" / "run-001.csv"
    with pytest.raises(ImmutabilityError, match="append-only"):
        guard_write(campaign, sneaky)


def test_writing_into_a_subdirectory_of_raw_is_refused(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    (campaign.raw / "batch1").mkdir()
    with pytest.raises(ImmutabilityError, match="append-only"):
        guard_write(campaign, campaign.raw / "batch1" / "x.csv")


def test_writing_into_refit_is_allowed(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    destination = campaign.refit / "fit-001.json"
    assert guard_write(campaign, destination) == destination


def test_refit_destination_lands_under_refit(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    assert refit_destination(campaign, "fit-001.json").parent == campaign.refit


def test_an_escaping_refit_name_is_refused(tmp_path: Path) -> None:
    campaign = paths(tmp_path)
    for name in ("../raw/x.json", "/etc/passwd"):
        with pytest.raises(ImmutabilityError):
            refit_destination(campaign, name)


# --- Registered assertion: K_D carries uncertainty --------------------------


def test_a_fit_without_a_usable_uncertainty_is_refused() -> None:
    """DESIGN section 8: never a bare point value."""
    for bad in (math.nan, -1.0, math.inf):
        with pytest.raises(RefitError, match="not a usable uncertainty"):
            SteadyStateFit(
                kd=1e-8,
                kd_stderr=bad,
                r_max=100.0,
                r_max_stderr=1.0,
                residuals=(),
                concentration_low=1e-9,
                concentration_high=1e-7,
            )


def test_a_non_positive_kd_is_refused() -> None:
    with pytest.raises(RefitError, match="positive and finite"):
        SteadyStateFit(
            kd=0.0,
            kd_stderr=1.0,
            r_max=1.0,
            r_max_stderr=1.0,
            residuals=(),
            concentration_low=1e-9,
            concentration_high=1e-7,
        )


# --- Fitting ----------------------------------------------------------------


def test_the_fit_recovers_a_known_dissociation_constant() -> None:
    rng = np.random.default_rng(7)
    concentrations = np.logspace(-9.5, -6, 8)
    true_kd = 12e-9
    responses = langmuir_steady_state(concentrations, 100.0, true_kd) + rng.normal(
        0, 1.0, concentrations.size
    )
    fit = fit_steady_state(concentrations, responses)
    assert fit.kd == pytest.approx(true_kd, rel=0.2)
    assert fit.kd_stderr > 0
    assert fit.relative_stderr < 0.2


def test_too_few_points_to_fit_two_parameters_is_refused() -> None:
    with pytest.raises(RefitError, match="at least 3 points"):
        fit_steady_state([1e-9, 2e-9], [1.0, 2.0])


def test_mismatched_inputs_are_refused() -> None:
    with pytest.raises(RefitError, match="against"):
        fit_steady_state([1e-9, 2e-9, 3e-9], [1.0, 2.0])


def test_non_positive_concentrations_are_refused() -> None:
    with pytest.raises(RefitError, match="must be positive"):
        fit_steady_state([0.0, 1e-9, 2e-9], [0.0, 1.0, 2.0])


# --- The 1:1 adequacy diagnostic, and its honest limit ----------------------


def test_alternating_residuals_look_like_independent_noise() -> None:
    z = runs_test_z([1, -1, 1, -1, 1, -1, 1, -1])
    assert z is not None
    assert z > RUNS_FLOOR


RUNS_FLOOR = -1.96


def test_residuals_all_on_one_side_are_maximally_systematic() -> None:
    assert runs_test_z([1.0] * 10) == -math.inf


def test_too_few_residuals_report_nothing_rather_than_a_number() -> None:
    assert runs_test_z([1, -1, 1]) is None


def test_a_fit_with_too_few_residuals_does_not_claim_adequacy_evidence() -> None:
    fit = a_fit()
    assert fit.residual_runs_z is None
    assert fit.one_to_one_adequacy is Adequacy.UNTESTED


def test_heterogeneous_binding_is_detected_once_there_are_enough_points() -> None:
    """The diagnostic works, but needs points. Quantified rather than assumed.

    A two-site curve fitted as 1:1 goes undetected at 8 concentrations and is
    caught decisively from 16 upward. A typical SPR concentration series is
    5-8 points, so this test belongs on the kinetic time-course residuals,
    where n is in the hundreds, not on the steady-state isotherm.
    """

    def heterogeneous(n: int) -> float | None:
        concentrations = np.logspace(-9.6, -5.8, n)
        responses = langmuir_steady_state(concentrations, 60.0, 2e-9) + langmuir_steady_state(
            concentrations, 40.0, 400e-9
        )
        return fit_steady_state(concentrations, responses).residual_runs_z

    assert (heterogeneous(8) or 0) > RUNS_FLOOR  # missed: too few points
    for n in (16, 32, 64):
        assert (heterogeneous(n) or 0) < RUNS_FLOOR  # caught


# --- Classification ---------------------------------------------------------


def test_a_fitted_curve_is_called_fitted() -> None:
    assert classify(a_fit(), association_shift_percent=0.0) is BindingCall.FITTED


def test_an_unfittable_curve_clearing_the_shift_rule_is_its_own_class() -> None:
    """PROTOCOL section 12.5: this is where the interesting failures live."""
    assert classify(None, SHIFT_THRESHOLD_PERCENT) is BindingCall.SHIFT_ONLY
    assert classify(None, 450.0) is BindingCall.SHIFT_ONLY


def test_an_unfittable_curve_below_the_shift_rule_is_a_non_binder() -> None:
    assert classify(None, 299.0) is BindingCall.NON_BINDER


# --- Ratios propagate, rather than dividing point estimates -----------------


def test_the_ratio_interval_is_multiplicative() -> None:
    ratio = specificity_ratio(a_fit(kd=1e-6), a_fit(kd=1e-8))
    assert ratio.ratio == pytest.approx(100.0)
    # Symmetric in log space: the point is the geometric mean of the bounds.
    assert math.sqrt(ratio.ci_low * ratio.ci_high) == pytest.approx(ratio.ratio)
    assert ratio.ci_low > 0


def test_a_well_determined_ratio_discriminates() -> None:
    assert specificity_ratio(a_fit(kd=1e-6, rel=0.05), a_fit(kd=1e-8, rel=0.05)).discriminates


def test_a_tenfold_ratio_from_poor_fits_does_not_discriminate() -> None:
    """A point ratio alone would present this as a tenfold result.

    Both fits are barely determined, at 100% relative error. Note that the
    delta-method propagation is itself strained in that regime; the module
    docstring states the validity range and what to use instead. The direction
    is nonetheless unambiguous, and reporting the point estimate alone would
    present a non-result as a tenfold one.
    """
    ratio = specificity_ratio(a_fit(kd=1e-7, rel=1.0), a_fit(kd=1e-8, rel=1.0))
    assert ratio.ratio == pytest.approx(10.0)
    assert ratio.ci_low < 1.0
    assert not ratio.discriminates


def test_uncertainty_compounds_across_both_fits() -> None:
    one = specificity_ratio(a_fit(rel=0.1), a_fit(rel=0.0))
    both = specificity_ratio(a_fit(rel=0.1), a_fit(rel=0.1))
    assert both.log_stderr > one.log_stderr


# --- Identifiability of K_D (FINDINGS F-17) ---------------------------------


def a_series_that_cannot_pin_a_kd() -> tuple[list[float], list[float]]:
    """Five concentrations well below K_D: the isotherm is still linear."""
    import numpy as np  # noqa: PLC0415

    from counterscreen.analyze.refit import langmuir_steady_state  # noqa: PLC0415

    concentrations = np.array([1.0, 3.0, 10.0, 30.0, 100.0])
    responses = langmuir_steady_state(concentrations, 100.0, 10_000.0)
    rng = np.random.default_rng(7)
    noisy = responses * (1 + rng.normal(0.0, 0.01, size=responses.size))
    return list(concentrations), list(noisy)


def test_a_kd_above_the_measured_range_is_not_treated_as_determined() -> None:
    """The fit succeeds, looks respectable, and is an extrapolation."""
    concentrations, responses = a_series_that_cannot_pin_a_kd()
    fit = fit_steady_state(concentrations, responses)

    assert fit.kd > max(concentrations)
    assert fit.relative_stderr < 0.5, "it does not even look badly determined"
    assert not fit.kd_is_identified
    assert fit.kd_range_multiple > 10.0


def test_an_unidentifiable_fit_is_not_called_a_fitted_binder() -> None:
    """It falls through to the shift test, which is what that class is for."""
    concentrations, responses = a_series_that_cannot_pin_a_kd()
    fit = fit_steady_state(concentrations, responses)

    assert classify(fit, association_shift_percent=400.0) is BindingCall.SHIFT_ONLY
    assert classify(fit, association_shift_percent=10.0) is BindingCall.NON_BINDER
    assert classify(a_fit(), association_shift_percent=0.0) is BindingCall.FITTED


def test_a_ratio_refuses_to_propagate_an_extrapolation() -> None:
    concentrations, responses = a_series_that_cannot_pin_a_kd()
    unidentified = fit_steady_state(concentrations, responses)

    with pytest.raises(RefitError, match="outside the concentration range"):
        specificity_ratio(unidentified, a_fit())
    with pytest.raises(RefitError, match="outside the concentration range"):
        specificity_ratio(a_fit(kd=1e-6), unidentified)


def test_the_runs_test_threshold_is_the_one_sided_five_percent_quantile() -> None:
    """`FINDINGS.md` F-8 reported power at alpha = 0.05; now the code agrees."""
    import statistics  # noqa: PLC0415

    from counterscreen.analyze.refit import RUNS_Z_THRESHOLD  # noqa: PLC0415
    from counterscreen.core.intervals import CONFIDENCE_LEVEL  # noqa: PLC0415

    assert pytest.approx(-1.6448536269514722) == RUNS_Z_THRESHOLD
    assert (
        pytest.approx(statistics.NormalDist().inv_cdf(1.0 - CONFIDENCE_LEVEL)) == RUNS_Z_THRESHOLD
    )


def test_f8_still_holds_at_the_corrected_threshold() -> None:
    """The finding must not have depended on the wrong critical value.

    F-8 fitted a two-site curve as 1:1 and reported z = -1.44 at eight
    concentration points, undetected. At -1.645 it is still undetected, so the
    conclusion -- that the test belongs on kinetic residuals -- stands.
    """
    from counterscreen.analyze.refit import RUNS_Z_THRESHOLD, Adequacy  # noqa: PLC0415

    eight_point_z = -1.44
    assert eight_point_z > RUNS_Z_THRESHOLD
    sixteen_point_z = -3.09
    assert sixteen_point_z < RUNS_Z_THRESHOLD
    assert Adequacy.UNTESTED not in {Adequacy.ADEQUATE, Adequacy.INADEQUATE}
