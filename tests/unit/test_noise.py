"""The amendment A9 noise floor (`DECISIONS.md` D-5, `PREREGISTRATION.md` A9)."""

import inspect
import math

import pytest

from counterscreen.core.noise import (
    REGISTERED_REPEATS,
    TIE_TOLERANCE_SD_FRACTION,
    NoiseFloor,
    NoiseFloorError,
)
from counterscreen.score.margins import ArmScores, CounterScreen, MarginError, TargetRole


def floor(
    sd: float = 0.02,
    metric: str = "ipsae",
    repeats: int = REGISTERED_REPEATS,
    source: str = "benchmarks/day1_gpu_benchmark.md",
) -> NoiseFloor:
    return NoiseFloor(metric=metric, sd=sd, repeats=repeats, source=source)


def screen(
    design_id: str,
    target: dict[int, float],
    decoy: dict[int, float],
    metric: str = "ipsae",
) -> CounterScreen:
    return CounterScreen(
        design_id=design_id,
        metric=metric,
        arms=(
            ArmScores.create("T+", TargetRole.TARGET, target),
            ArmScores.create("D1", TargetRole.MUTATION_DECOY, decoy),
        ),
    )


# --- A floor must be a measurement, not a number ----------------------------


def test_a_floor_must_cite_where_it_was_measured() -> None:
    with pytest.raises(NoiseFloorError, match="cites no source"):
        floor(source="   ")


def test_a_floor_must_name_its_metric() -> None:
    with pytest.raises(NoiseFloorError, match="names no metric"):
        floor(metric="")


def test_a_floor_below_the_registered_repeat_count_is_refused() -> None:
    with pytest.raises(NoiseFloorError, match="registers 5"):
        floor(repeats=REGISTERED_REPEATS - 1)


def test_more_repeats_than_registered_are_accepted() -> None:
    assert floor(repeats=REGISTERED_REPEATS + 3).sd == pytest.approx(0.02)


def test_a_zero_floor_is_refused_as_a_failed_measurement() -> None:
    with pytest.raises(NoiseFloorError, match="measurement is wrong"):
        floor(sd=0.0)


def test_a_negative_or_infinite_floor_is_refused() -> None:
    with pytest.raises(NoiseFloorError):
        floor(sd=-0.1)
    with pytest.raises(NoiseFloorError, match="not finite"):
        floor(sd=math.inf)


def test_a_floor_has_no_defaults_to_fall_back_on() -> None:
    """Every field is required, so a campaign cannot gate on an unmeasured floor."""
    with pytest.raises(TypeError):
        NoiseFloor()  # type: ignore[call-arg]


# --- The G4 denominator: the larger of the two readings ---------------------


def test_the_denominator_is_the_larger_of_the_two_readings() -> None:
    assert floor(sd=0.05).gate_denominator(0.01) == pytest.approx(0.05)
    assert floor(sd=0.05).gate_denominator(0.09) == pytest.approx(0.09)


def test_a_design_whose_seeds_happened_to_agree_cannot_pass_on_that_alone() -> None:
    """The selection effect amendment A9 exists to block.

    Two designs with the same margin. One has a volatile seed spread, the
    other's five seeds happened to land on top of each other. Under the
    per-design reading alone the lucky one passes on a denominator near zero.
    """
    lucky = screen("lucky", {1: 0.500, 2: 0.500001}, {1: 0.450, 2: 0.450001}).m_mut()
    assert lucky.pooled_sd < 1e-5
    assert lucky.mean == pytest.approx(0.05, abs=1e-4)

    # Per-design reading alone: 0.05 > 2 x ~0, so it passes.
    assert lucky.mean > 2.0 * lucky.pooled_sd
    # Amendment A9, with a campaign floor of 0.04: 0.05 < 2 x 0.04, so it does not.
    assert not lucky.exceeds_noise(2.0, floor(sd=0.04))


def test_a_genuinely_noisy_design_raises_its_own_bar_above_the_floor() -> None:
    """The campaign floor alone cannot see design-specific noise."""
    noisy = screen("noisy", {1: 0.30, 2: 0.90}, {1: 0.25, 2: 0.85}).m_mut()
    assert noisy.pooled_sd > 0.2
    assert noisy.mean == pytest.approx(0.05)
    # Campaign floor alone would be 0.01, and 0.05 > 2 x 0.01 would pass.
    assert not noisy.exceeds_noise(2.0, floor(sd=0.01))


def test_a_margin_is_not_judged_against_another_metric_s_floor() -> None:
    margin = screen("d", {1: 0.8, 2: 0.82}, {1: 0.5, 2: 0.52}).m_mut()
    with pytest.raises(MarginError, match="scored on 'ipsae'"):
        margin.exceeds_noise(2.0, floor(metric="plddt"))


def test_an_unusable_within_design_spread_is_refused_not_coerced() -> None:
    with pytest.raises(NoiseFloorError, match="not a usable spread"):
        floor().gate_denominator(math.nan)
    with pytest.raises(NoiseFloorError, match="not a usable spread"):
        floor().gate_denominator(-1.0)


# --- The tie tolerance ------------------------------------------------------


def test_the_tie_tolerance_is_half_the_campaign_floor() -> None:
    assert floor(sd=0.2).tie_tolerance() == pytest.approx(0.1)
    assert TIE_TOLERANCE_SD_FRACTION == 0.5


def test_the_tie_tolerance_takes_no_argument() -> None:
    """A fraction that could be supplied here would be a free parameter."""
    assert set(inspect.signature(NoiseFloor.tie_tolerance).parameters) == {"self"}


def test_the_tie_tolerance_does_not_depend_on_any_design() -> None:
    """One number per campaign, so the grouping is symmetric between designs."""
    tight = screen("tight", {1: 0.80, 2: 0.80}, {1: 0.50, 2: 0.50}).m_mut()
    loose = screen("loose", {1: 0.30, 2: 0.90}, {1: 0.20, 2: 0.60}).m_mut()
    assert tight.pooled_sd != loose.pooled_sd
    assert floor(sd=0.2).tie_tolerance() == pytest.approx(0.1)
