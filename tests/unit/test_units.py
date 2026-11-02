"""Units carry through the type system, and [R21] is computed rather than recalled."""

import math

import pytest

from counterscreen.core import units
from counterscreen.core.units import (
    KCAL_PER_DECADE,
    REU,
    RT,
    Angstrom,
    KcalPerMol,
    Kelvin,
    Molar,
    delta_g_from_kd,
    kd_from_delta_g,
)

# REFERENCES.md [R21], to the precision the table states.
R21_RT = 0.5925
R21_KCAL_PER_DECADE = 1.3642
R21_TABLE = [(1e-6, -8.19), (1e-7, -9.55), (1e-9, -12.28), (1e-12, -16.37)]


def test_rt_matches_r21() -> None:
    assert RT.value == pytest.approx(R21_RT, abs=5e-5)


def test_one_decade_of_affinity_matches_r21() -> None:
    assert KCAL_PER_DECADE.value == pytest.approx(R21_KCAL_PER_DECADE, abs=5e-5)


@pytest.mark.parametrize(("kd", "expected"), R21_TABLE)
def test_delta_g_reproduces_the_r21_table(kd: float, expected: float) -> None:
    assert delta_g_from_kd(Molar(kd)).value == pytest.approx(expected, abs=5e-3)


def test_delta_g_round_trips_through_kd() -> None:
    kd = Molar(3.7e-8)
    assert kd_from_delta_g(delta_g_from_kd(kd)).value == pytest.approx(kd.value, rel=1e-12)


def test_a_decade_of_affinity_is_one_kcal_per_decade() -> None:
    tighter = delta_g_from_kd(Molar(1e-9))
    looser = delta_g_from_kd(Molar(1e-8))
    assert (looser - tighter).value == pytest.approx(KCAL_PER_DECADE.value, rel=1e-12)


def test_rosetta_energy_units_cannot_be_added_to_kcal_per_mol() -> None:
    """The v0.2 'REU-equivalent' error, made unavailable at runtime as well as to mypy."""
    with pytest.raises(TypeError):
        _ = REU(1.0) + KcalPerMol(1.0)  # type: ignore[operator]


def test_rosetta_energy_units_cannot_be_compared_with_kcal_per_mol() -> None:
    with pytest.raises(TypeError):
        _ = REU(1.0) < KcalPerMol(1.0)  # type: ignore[operator]


def test_no_conversion_between_reu_and_kcal_per_mol_is_exported() -> None:
    """Section 7.2 forbids quoting REU as an affinity, so no such function exists."""
    names = [n.lower() for n in dir(units)]
    assert not [n for n in names if "reu" in n and ("kcal" in n or "convert" in n)]


def test_quantities_of_the_same_unit_combine() -> None:
    assert (Angstrom(3.8) + Angstrom(0.7)).value == pytest.approx(4.5)
    assert Angstrom(4.5) > Angstrom(3.8)


def test_non_finite_values_are_refused_at_construction() -> None:
    for bad in (math.inf, -math.inf, math.nan):
        with pytest.raises(ValueError, match="finite"):
            Kelvin(bad)


def test_a_dissociation_constant_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        delta_g_from_kd(Molar(0.0))


def test_str_carries_the_unit() -> None:
    assert str(KcalPerMol(-9.55)) == "-9.55 kcal/mol"
    assert str(Angstrom(4.5)) == "4.5 Å"
