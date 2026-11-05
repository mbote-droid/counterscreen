"""Mass-action occupancy and the selectivity a cell would actually experience."""

import numpy as np
import pytest

from counterscreen.biophys.occupancy import (
    CopyNumberRange,
    OccupancyError,
    competitive_occupancy,
    discrimination_at_occupancy,
    kd_for_occupancy,
    occupancy,
    occupancy_for_discrimination,
    selectivity_surface,
)
from counterscreen.core.units import Molar

NANOMOLAR = 1e-9


def nm(value: float) -> Molar:
    return Molar(value * NANOMOLAR)


# --- The physics ------------------------------------------------------------


def test_occupancy_is_one_half_at_the_dissociation_constant() -> None:
    """What a K_D means, and the simplest check that the formula is right."""
    assert occupancy(nm(5.0), nm(5.0)) == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("binder", "expected"),
    [(0.0, 0.0), (1.0, 1 / 11), (10.0, 0.5), (100.0, 100 / 110), (1e6, 1e6 / (1e6 + 10))],
)
def test_occupancy_saturates(binder: float, expected: float) -> None:
    assert occupancy(nm(binder), nm(10.0)) == pytest.approx(expected, rel=1e-6)


def test_occupancy_rises_with_concentration() -> None:
    values = [occupancy(nm(c), nm(10.0)) for c in (0.1, 1.0, 10.0, 100.0)]
    assert values == sorted(values)


def test_competitive_binding_reduces_to_single_site_when_nothing_competes() -> None:
    """A property, not a coincidence: the competitive form must contain the simple one."""
    for concentration in (0.1, 1.0, 10.0, 100.0):
        assert competitive_occupancy(
            nm(concentration), nm(10.0), Molar(0.0), nm(10.0)
        ) == pytest.approx(occupancy(nm(concentration), nm(10.0)))


def test_a_competitor_lowers_occupancy() -> None:
    alone = competitive_occupancy(nm(10.0), nm(10.0), Molar(0.0), nm(10.0))
    crowded = competitive_occupancy(nm(10.0), nm(10.0), nm(100.0), nm(10.0))
    assert crowded < alone


def test_kd_for_occupancy_inverts_occupancy() -> None:
    required = kd_for_occupancy(nm(10.0), 0.9)
    assert occupancy(nm(10.0), required) == pytest.approx(0.9)


def test_occupancy_refuses_a_non_positive_dissociation_constant() -> None:
    with pytest.raises(OccupancyError, match="must be positive"):
        occupancy(nm(1.0), Molar(0.0))


def test_impossible_occupancy_targets_are_refused() -> None:
    for target in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(OccupancyError, match="strictly between"):
            kd_for_occupancy(nm(10.0), target)


# --- Registered: copy numbers must be a range -------------------------------


def test_a_single_copy_number_is_refused() -> None:
    """DESIGN section 8 registers this assertion against biophys/."""
    with pytest.raises(OccupancyError, match="must span a range"):
        CopyNumberRange(low=100, high=100)


def test_an_inverted_range_is_refused() -> None:
    with pytest.raises(OccupancyError, match="must span a range"):
        CopyNumberRange(low=500, high=100)


def test_a_non_positive_copy_number_is_refused() -> None:
    with pytest.raises(OccupancyError, match="must be positive"):
        CopyNumberRange(low=0, high=100)


def test_a_range_grids_across_its_span() -> None:
    grid = CopyNumberRange(low=10, high=1000).grid(points=5)
    assert len(grid) == 5
    assert grid[0] == pytest.approx(10.0)
    assert grid[-1] == pytest.approx(1000.0)
    assert np.all(np.diff(grid) > 0)


# --- The claim PROTOCOL section 12.6 makes ------------------------------------


def test_a_hundredfold_kd_ratio_can_still_be_unselective_in_a_cell() -> None:
    """Reproduces section 12.6's central warning numerically.

    A design with a hundredfold K_D ratio can have a selectivity index near or
    below 1 once presentation density is accounted for, because neoantigen
    pMHC presentation is low while wild-type presentation on healthy tissue
    may be far higher.
    """
    surface = selectivity_surface(
        binder=nm(1.0),
        kd_mutant=nm(1.0),
        kd_wild_type=nm(100.0),
        mutant_copies=CopyNumberRange(low=10, high=200),
        wild_type_copies=CopyNumberRange(low=1_000, high=20_000),
    )
    assert surface.kd_ratio == pytest.approx(100.0)
    assert surface.occupancy_ratio == pytest.approx(50.5, rel=1e-3)

    # Despite the hundredfold K_D ratio, part of the plausible density range
    # gives no selectivity at all in bound complexes per cell.
    assert surface.minimum < 1.0
    assert surface.fraction_below(1.0) > 0.0


def test_the_occupancy_ratio_is_not_the_kd_ratio() -> None:
    """Saturation makes them differ, which is why the index is computed at all."""
    surface = selectivity_surface(
        binder=nm(1.0),
        kd_mutant=nm(1.0),
        kd_wild_type=nm(100.0),
        mutant_copies=CopyNumberRange(low=10, high=200),
        wild_type_copies=CopyNumberRange(low=1_000, high=20_000),
    )
    assert surface.occupancy_ratio != pytest.approx(surface.kd_ratio)


def test_equal_densities_make_selectivity_the_occupancy_ratio() -> None:
    surface = selectivity_surface(
        binder=nm(1.0),
        kd_mutant=nm(1.0),
        kd_wild_type=nm(100.0),
        mutant_copies=CopyNumberRange(low=100, high=101),
        wild_type_copies=CopyNumberRange(low=100, high=101),
        points=2,
    )
    assert surface.values[0, 0] == pytest.approx(surface.occupancy_ratio)


def test_the_surface_reports_which_parameter_dominates() -> None:
    """Section 12.6 requires saying which parameter drives the result."""
    surface = selectivity_surface(
        binder=nm(1.0),
        kd_mutant=nm(1.0),
        kd_wild_type=nm(100.0),
        mutant_copies=CopyNumberRange(low=10, high=20),
        wild_type_copies=CopyNumberRange(low=1_000, high=100_000),
    )
    assert surface.dominant_parameter() == "wild_type_copies"


def test_the_surface_spans_the_whole_grid() -> None:
    surface = selectivity_surface(
        binder=nm(1.0),
        kd_mutant=nm(1.0),
        kd_wild_type=nm(100.0),
        mutant_copies=CopyNumberRange(low=10, high=200),
        wild_type_copies=CopyNumberRange(low=1_000, high=20_000),
        points=7,
    )
    assert surface.values.shape == (7, 7)
    assert surface.minimum <= surface.maximum


# --- The occupancy-discrimination trade-off (FINDINGS F-18) -----------------


def test_discrimination_interpolates_between_the_kd_ratio_and_one() -> None:
    assert discrimination_at_occupancy(100.0, 0.0) == pytest.approx(100.0)
    assert discrimination_at_occupancy(100.0, 0.5) == pytest.approx(50.5)
    assert discrimination_at_occupancy(100.0, 0.9) == pytest.approx(10.9)
    assert discrimination_at_occupancy(100.0, 1.0) == pytest.approx(1.0)


def test_the_identity_matches_the_mass_action_calculation_exactly() -> None:
    """D = r(1-x) + x is algebra, not a fit, so it must agree to machine precision."""
    kd_mutant, kd_wild_type = 1.0, 100.0
    for concentration in (0.01, 0.1, 1.0, 9.0, 10.0, 100.0, 1000.0):
        mutant = occupancy(nm(concentration), nm(kd_mutant))
        wild_type = occupancy(nm(concentration), nm(kd_wild_type))
        assert mutant / wild_type == pytest.approx(
            discrimination_at_occupancy(kd_wild_type / kd_mutant, mutant), rel=1e-12
        )


def test_half_the_discrimination_is_gone_at_half_occupancy() -> None:
    """Which is the concentration a dose would aim for."""
    for ratio in (10.0, 100.0, 1000.0):
        assert discrimination_at_occupancy(ratio, 0.5) == pytest.approx((ratio + 1.0) / 2.0)


def test_the_trade_off_inverts() -> None:
    assert occupancy_for_discrimination(100.0, 50.5) == pytest.approx(0.5)
    assert occupancy_for_discrimination(100.0, 10.9) == pytest.approx(0.9)
    for occupancy_target in (0.1, 0.5, 0.9, 0.99):
        achieved = discrimination_at_occupancy(100.0, occupancy_target)
        assert occupancy_for_discrimination(100.0, achieved) == pytest.approx(occupancy_target)


def test_a_ratio_that_cannot_be_traded_is_refused() -> None:
    with pytest.raises(OccupancyError, match="must exceed 1"):
        occupancy_for_discrimination(1.0, 1.0)
    with pytest.raises(OccupancyError, match="between 1 and"):
        occupancy_for_discrimination(100.0, 200.0)
