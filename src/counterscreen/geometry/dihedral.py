"""Dihedral, angle and distance arithmetic on Cartesian coordinates.

Separated from the validity checks because this is exact mathematics with no
biological judgement in it: every function here has a closed-form answer that a
test can state independently, which is what makes the checks built on top
worth trusting. The biology -- what counts as an outlier, a clash or a break --
lives in :mod:`counterscreen.geometry.validity`.

Angles are returned in degrees and dihedrals follow the IUPAC sign convention,
so a mirrored structure returns negated dihedrals. The chirality check depends
on that property and a test asserts it directly.
"""

import numpy as np
from numpy.typing import NDArray

Coordinates = NDArray[np.float64]

_POINT_DIMENSIONS = 3
_POINT_NDIM = 2


def _as_points(array: Coordinates) -> Coordinates:
    """Validate and normalise an (n, 3) stack of points."""
    points = np.atleast_2d(np.asarray(array, dtype=np.float64))
    if points.ndim != _POINT_NDIM or points.shape[1] != _POINT_DIMENSIONS:
        msg = f"expected an (n, 3) array of points, got shape {points.shape}"
        raise ValueError(msg)
    return points


def distances(first: Coordinates, second: Coordinates) -> NDArray[np.float64]:
    """Euclidean distance between paired points."""
    difference = _as_points(first) - _as_points(second)
    return np.asarray(np.linalg.norm(difference, axis=1), dtype=np.float64)


def bond_angles(first: Coordinates, vertex: Coordinates, last: Coordinates) -> NDArray[np.float64]:
    """Angle at ``vertex``, in degrees, for paired triples of points."""
    left = _as_points(first) - _as_points(vertex)
    right = _as_points(last) - _as_points(vertex)
    left_norm = np.linalg.norm(left, axis=1)
    right_norm = np.linalg.norm(right, axis=1)
    cosine = np.einsum("ij,ij->i", left, right) / (left_norm * right_norm)
    return np.asarray(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))), dtype=np.float64)


def dihedral_angles(
    first: Coordinates,
    second: Coordinates,
    third: Coordinates,
    fourth: Coordinates,
) -> NDArray[np.float64]:
    """Signed dihedral angles, in degrees, for paired quadruples of points.

    Uses the IUPAC sign convention: looking along the second-to-third bond, a
    clockwise rotation of the fourth atom relative to the first is positive.
    Reflecting every coordinate negates the result, which is what makes a
    dihedral able to tell an L residue from a D one.
    """
    a, b, c, d = (_as_points(x) for x in (first, second, third, fourth))
    b0 = a - b
    b1 = c - b
    b2 = d - c

    b1_unit = b1 / np.linalg.norm(b1, axis=1)[:, None]
    # Components of b0 and b2 perpendicular to the central bond.
    v = b0 - np.einsum("ij,ij->i", b0, b1_unit)[:, None] * b1_unit
    w = b2 - np.einsum("ij,ij->i", b2, b1_unit)[:, None] * b1_unit

    x = np.einsum("ij,ij->i", v, w)
    y = np.einsum("ij,ij->i", np.cross(b1_unit, v), w)
    return np.asarray(np.degrees(np.arctan2(y, x)), dtype=np.float64)
