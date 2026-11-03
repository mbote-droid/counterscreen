"""analyze/ contract: raw data is immutable, and no K_D is a bare point value."""

import math
from pathlib import Path

import numpy as np
import pytest

from counterscreen.analyze.refit import (
    SHIFT_THRESHOLD_PERCENT,
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
    return SteadyStateFit(
        kd=kd, kd_stderr=kd * rel, r_max=100.0, r_max_stderr=2.0, residuals=(0.1, -0.1)
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
            SteadyStateFit(kd=1e-8, kd_stderr=bad, r_max=100.0, r_max_stderr=1.0, residuals=())


def test_a_non_positive_kd_is_refused() -> None:
    with pytest.raises(RefitError, match="positive and finite"):
        SteadyStateFit(kd=0.0, kd_stderr=1.0, r_max=1.0, r_max_stderr=1.0, residuals=())


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
    assert fit.one_to_one_adequate  # absence of evidence, not evidence of absence


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
    """CLAUDE section 12.5: this is where the interesting failures live."""
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
