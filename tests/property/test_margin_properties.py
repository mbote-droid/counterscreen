# mypy: disallow_any_decorated=false
# hypothesis types @given as Callable[..., None], which disallow_any_decorated
# rejects. Relaxing that one flag here keeps strict mode everywhere else.
"""Margin invariants DESIGN.md section 8 names: antisymmetry, and monotone gates."""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from counterscreen.score.margins import ArmScores, CounterScreen, TargetRole, pooled_sd

confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
paired = st.lists(st.tuples(confidence, confidence), min_size=2, max_size=6)

TOLERANCE = 1e-9


def build(pairs: list[tuple[float, float]]) -> CounterScreen:
    target = {seed: value for seed, (value, _) in enumerate(pairs)}
    decoy = {seed: value for seed, (_, value) in enumerate(pairs)}
    return CounterScreen(
        design_id="d",
        metric="ipsae",
        arms=(
            ArmScores.create("T+", TargetRole.TARGET, target),
            ArmScores.create("D1", TargetRole.MUTATION_DECOY, decoy),
        ),
    )


@given(pairs=paired)
def test_margin_is_antisymmetric(pairs: list[tuple[float, float]]) -> None:
    """M(A, B) == -M(B, A), stated in DESIGN.md section 8."""
    screen = build(pairs)
    forward = screen.margin("fwd", screen.arm("T+"), [screen.arm("D1")])
    backward = screen.margin("bwd", screen.arm("D1"), [screen.arm("T+")])
    assert forward.mean == pytest.approx(-backward.mean, abs=TOLERANCE)
    for (_, left), (_, right) in zip(forward.per_seed, backward.per_seed, strict=True):
        assert left == pytest.approx(-right, abs=TOLERANCE)


@given(pairs=paired)
def test_a_margin_against_itself_is_zero(pairs: list[tuple[float, float]]) -> None:
    screen = build(pairs)
    assert screen.margin("self", screen.arm("T+"), [screen.arm("T+")]).mean == pytest.approx(
        0.0, abs=TOLERANCE
    )


@given(pairs=paired, bump=st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
def test_raising_target_confidence_cannot_lower_the_margin(
    pairs: list[tuple[float, float]], bump: float
) -> None:
    """Gates are monotone in their inputs (DESIGN.md section 8)."""
    base = build(pairs).m_mut()
    raised = build([(t + bump, d) for t, d in pairs]).m_mut()
    assert raised.mean >= base.mean - TOLERANCE


@given(pairs=paired, bump=st.floats(min_value=0.0, max_value=5.0, allow_nan=False))
def test_raising_decoy_confidence_cannot_raise_the_margin(
    pairs: list[tuple[float, float]], bump: float
) -> None:
    base = build(pairs).m_mut()
    raised = build([(t, d + bump) for t, d in pairs]).m_mut()
    assert raised.mean <= base.mean + TOLERANCE


@given(
    pairs=paired,
    bump=st.floats(min_value=0.0, max_value=5.0, allow_nan=False),
    multiple=st.floats(min_value=0.0, max_value=4.0, allow_nan=False),
)
def test_the_noise_gate_is_monotone(
    pairs: list[tuple[float, float]], bump: float, multiple: float
) -> None:
    """A design that passes cannot be made to fail by scoring better."""
    base = build(pairs).m_mut()
    assume(base.exceeds_noise(multiple))
    raised = build([(t + bump, d) for t, d in pairs]).m_mut()
    assert raised.exceeds_noise(multiple)


@given(pairs=paired, shift=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False))
def test_pooled_sd_measures_spread_not_level(
    pairs: list[tuple[float, float]], shift: float
) -> None:
    """Shifting a design's overall level must not change its noise estimate.

    This is the property that separates a within-design pooled SD from an
    across-design one. Pooling across designs would make the estimate depend
    on where each design sits, which is exactly the signal being ranked.
    """
    original = build(pairs)
    shifted = build([(t + shift, d + shift) for t, d in pairs])
    assert pooled_sd(list(shifted.arms)) == pytest.approx(pooled_sd(list(original.arms)), abs=1e-7)


@given(pairs=paired, shift=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False))
def test_shifting_both_arms_together_leaves_the_margin_unchanged(
    pairs: list[tuple[float, float]], shift: float
) -> None:
    base = build(pairs).m_mut()
    shifted = build([(t + shift, d + shift) for t, d in pairs]).m_mut()
    assert shifted.mean == pytest.approx(base.mean, abs=1e-7)
