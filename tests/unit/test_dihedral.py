"""Dihedral, angle and distance arithmetic, against closed-form answers."""

import numpy as np
import pytest

from counterscreen.geometry.dihedral import bond_angles, dihedral_angles, distances


def quad(turn_degrees: float) -> tuple[np.ndarray, ...]:
    """Four points whose dihedral is +/- ``turn_degrees`` by construction.

    The central bond lies along x. The first and last points are offset
    perpendicular to it, separated by the given rotation about x.
    """
    radians = np.radians(turn_degrees)
    a = np.array([[0.0, 1.0, 0.0]])
    b = np.array([[0.0, 0.0, 0.0]])
    c = np.array([[1.0, 0.0, 0.0]])
    d = c + np.array([[0.0, np.cos(radians), np.sin(radians)]])
    return a, b, c, d


def test_eclipsed_is_zero() -> None:
    assert dihedral_angles(*quad(0.0))[0] == pytest.approx(0.0, abs=1e-9)


def test_anti_is_one_hundred_and_eighty() -> None:
    assert abs(dihedral_angles(*quad(180.0))[0]) == pytest.approx(180.0, abs=1e-9)


@pytest.mark.parametrize("turn", [30.0, 60.0, 90.0, 120.0, 150.0])
def test_magnitude_matches_the_construction(turn: float) -> None:
    assert abs(dihedral_angles(*quad(turn))[0]) == pytest.approx(turn, abs=1e-9)


@pytest.mark.parametrize("turn", [30.0, 90.0, 150.0])
def test_reflection_negates_the_dihedral(turn: float) -> None:
    """The property the L-versus-D check rests on."""
    points = quad(turn)
    mirrored = tuple(p * np.array([[1.0, 1.0, -1.0]]) for p in points)
    assert dihedral_angles(*mirrored)[0] == pytest.approx(-dihedral_angles(*points)[0], abs=1e-9)


def test_rotation_does_not_change_the_dihedral() -> None:
    """Dihedrals are invariant under rigid rotation, unlike reflection."""
    points = quad(75.0)
    angle = np.radians(37.0)
    rotation = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    rotated = tuple(p @ rotation.T for p in points)
    assert dihedral_angles(*rotated)[0] == pytest.approx(dihedral_angles(*points)[0], abs=1e-9)


def test_translation_does_not_change_the_dihedral() -> None:
    points = quad(75.0)
    shifted = tuple(p + np.array([[3.0, -2.0, 7.0]]) for p in points)
    assert dihedral_angles(*shifted)[0] == pytest.approx(dihedral_angles(*points)[0], abs=1e-9)


def test_right_angle() -> None:
    a = np.array([[1.0, 0.0, 0.0]])
    vertex = np.array([[0.0, 0.0, 0.0]])
    c = np.array([[0.0, 1.0, 0.0]])
    assert bond_angles(a, vertex, c)[0] == pytest.approx(90.0, abs=1e-9)


def test_straight_angle() -> None:
    a = np.array([[1.0, 0.0, 0.0]])
    vertex = np.array([[0.0, 0.0, 0.0]])
    c = np.array([[-2.0, 0.0, 0.0]])
    assert bond_angles(a, vertex, c)[0] == pytest.approx(180.0, abs=1e-9)


def test_three_four_five_triangle() -> None:
    assert distances(np.array([[0.0, 0.0, 0.0]]), np.array([[3.0, 4.0, 0.0]]))[0] == pytest.approx(
        5.0
    )


def test_batched_inputs_are_handled_elementwise() -> None:
    a = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    b = np.array([[1.0, 0.0, 0.0], [1.0, 1.0, 2.0]])
    assert distances(a, b) == pytest.approx([1.0, 1.0])


def test_malformed_input_is_refused() -> None:
    with pytest.raises(ValueError, match=r"\(n, 3\)"):
        distances(np.array([[0.0, 0.0]]), np.array([[1.0, 1.0]]))
