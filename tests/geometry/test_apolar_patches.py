"""The quantity gate G5 thresholds on (PROTOCOL.md section 8, amendments A1 and A13).

G5 is registered against the largest *contiguous* solvent-exposed apolar
patch. Until now the code reported the *total* apolar area and said so, which
is a different quantity: a surface carrying one 300 square angstrom patch and
one carrying thirty 10 square angstrom spots have the same total and very
different expression liabilities.

`FINDINGS.md` F-22 is why it is computed over surface dots rather than atoms.
"""

import pathlib

import numpy as np
import pytest

from counterscreen.geometry.structure import Structure
from counterscreen.geometry.surface import (
    DOTS_PER_ATOM,
    apolar_patches,
    atom_sasa,
    dot_sasa,
    exposed_apolar_area,
    largest_apolar_patch,
    sphere_points,
)
from counterscreen.targets.prepare import read_pdb

TARGETS = pathlib.Path(__file__).resolve().parents[2] / "campaigns" / "kras-g12d-pmhc" / "targets"


def platform() -> Structure:
    path = TARGETS / "T_plus_platform.pdb"
    if not path.exists():
        pytest.skip(f"{path} not prepared")
    return read_pdb(path)


# --- The sampling -----------------------------------------------------------


def test_sphere_points_are_unit_vectors_and_near_uniform() -> None:
    points = sphere_points(512)
    assert points.shape == (512, 3)
    assert np.allclose(np.linalg.norm(points, axis=1), 1.0)
    # A uniform sampling has its centroid at the origin.
    assert np.linalg.norm(points.mean(axis=0)) < 0.02


def test_the_sampling_is_deterministic() -> None:
    """A seeded sampling would make the gate's own threshold seed-dependent."""
    assert np.array_equal(sphere_points(64), sphere_points(64))


def test_an_empty_sphere_is_refused() -> None:
    from counterscreen.geometry.surface import SurfaceError  # noqa: PLC0415

    with pytest.raises(SurfaceError, match="at least one point"):
        sphere_points(0)


# --- Differential test against the library (build_rules.pdf 2.7) ------------


def test_dot_derived_sasa_agrees_with_the_library() -> None:
    """The check `build_rules.pdf` section 2.7 asks for, on a critical call.

    An independent Shrake-Rupley pass over the same radii. Agreement to a
    fraction of a percent on the total is what licenses using the library's
    value; the per-atom spread is the sampling error at 256 dots.
    """
    structure = platform()
    mine = dot_sasa(structure)
    theirs = atom_sasa(structure)
    rows = sorted(mine)
    ours = np.array([mine[row] for row in rows])
    library = np.array([theirs[row] for row in rows])

    assert ours.sum() == pytest.approx(library.sum(), rel=0.01)
    assert np.abs(ours - library).mean() < 1.0
    assert np.corrcoef(ours, library)[0, 1] > 0.99


# --- The patch measure is not the total ------------------------------------


def test_the_largest_patch_is_a_fraction_of_the_total_apolar_area() -> None:
    """The percolation regression (`FINDINGS.md` F-22).

    An adjacency rule over atom *centres* merged the entire protein surface
    into one component, making the patch area equal to the total and the gate
    a restatement of a quantity it already had.
    """
    structure = platform()
    patches = apolar_patches(structure)
    total = exposed_apolar_area(structure)

    assert len(patches) > 50, "a protein surface is not one apolar patch"
    assert patches[0].area < 0.5 * total
    assert largest_apolar_patch(structure) == pytest.approx(patches[0].area)


def test_the_patches_account_for_the_exposed_apolar_area() -> None:
    """Every accessible apolar dot is in one patch, or below the dot floor.

    The patches therefore sum to slightly *less* than the total, and the gap
    is how much surface the sampling threw into fragments. Asserted as a
    bound, so the gap cannot grow quietly.
    """
    structure = platform()
    patched = sum(patch.area for patch in apolar_patches(structure))
    total = exposed_apolar_area(structure)
    assert patched <= total
    # 7.2% on the platform construct at the registered four-dot floor.
    assert patched > 0.90 * total, f"{1 - patched / total:.1%} of the surface in fragments"


def test_the_gated_quantity_does_not_depend_on_the_fragment_floor() -> None:
    """The property that makes the convention safe (`FINDINGS.md` F-22).

    The floor changes how many regions are *called* patches -- 618 at one dot,
    101 at sixteen -- and leaves the largest patch at 295.4 square angstrom
    throughout. G5 thresholds on the largest, so its verdict is invariant to
    the one convention amendment A13 had to register by choice.
    """
    structure = platform()
    import counterscreen.geometry.surface as module  # noqa: PLC0415

    original = module.MIN_PATCH_DOTS
    try:
        areas = []
        for floor in (1, 2, 4, 8, 16):
            module.MIN_PATCH_DOTS = floor
            areas.append(apolar_patches(structure)[0].area)
    finally:
        module.MIN_PATCH_DOTS = original
    assert areas == [pytest.approx(areas[0])] * len(areas)


def test_patches_are_ordered_by_area_and_the_order_is_total() -> None:
    patches = apolar_patches(platform())
    areas = [patch.area for patch in patches]
    assert areas == sorted(areas, reverse=True)
    # Unique per patch; `atoms` is not, because patches partition dots.
    assert len({patch.first_dot for patch in patches}) == len(patches)


def test_one_atom_can_belong_to_more_than_one_patch() -> None:
    """Patches partition the surface, not the atoms.

    A side chain exposed on both sides of a polar ridge contributes to two
    patches, which is why the patch order is keyed on a dot and not an atom.
    """
    patches = apolar_patches(platform())
    appearances: dict[int, int] = {}
    for patch in patches:
        for atom in patch.atoms:
            appearances[atom] = appearances.get(atom, 0) + 1
    assert max(appearances.values()) > 1


def test_patch_detection_is_reproducible() -> None:
    structure = platform()
    first = [(patch.area, patch.atoms) for patch in apolar_patches(structure)]
    second = [(patch.area, patch.atoms) for patch in apolar_patches(structure)]
    assert first == second


# --- Contiguity behaves as contiguity --------------------------------------


def two_carbon_clusters(separation: float) -> Structure:
    """Two triangles of carbons, `separation` angstrom apart.

    One residue per atom, because the F-13 guard refuses two atoms sharing a
    name within a residue -- it caught this fixture on its first run.
    """
    offsets = np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0], [0.75, 1.3, 0.0]])
    coords = np.vstack([offsets, offsets + np.array([separation, 0.0, 0.0])])
    return Structure.from_atoms(
        coords,
        ["CB"] * 6,
        ["ALA"] * 6,
        [1, 2, 3, 4, 5, 6],
        ["A"] * 6,
    )


def test_separated_apolar_clusters_are_separate_patches() -> None:
    patches = apolar_patches(two_carbon_clusters(separation=20.0))
    assert len(patches) == 2
    assert patches[0].area == pytest.approx(patches[1].area, rel=0.05)


def test_touching_apolar_clusters_join_into_one_patch() -> None:
    """The property under test is contiguity, not the patch count.

    Six overlapping spheres also leave a small accessible pocket between
    them, which is a real separate region in this artificial geometry. What
    matters is that the largest patch spans atoms from both clusters.
    """
    patches = apolar_patches(two_carbon_clusters(separation=1.5))
    assert set(patches[0].atoms) >= {0, 1, 2, 3, 4, 5}


def test_fragments_below_the_sampling_resolution_are_not_patches() -> None:
    """One- and two-dot regions in crevices are sampling noise, not surface."""
    from counterscreen.geometry.surface import MIN_PATCH_DOTS  # noqa: PLC0415

    patches = apolar_patches(platform())
    assert patches, "the fixture must produce patches"
    assert min(patch.dots for patch in patches) >= MIN_PATCH_DOTS


def test_a_structure_with_no_apolar_atoms_has_no_patches() -> None:
    polar = Structure.from_atoms(
        [[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]], ["N", "O"], ["SER"] * 2, [1, 2], ["A"] * 2
    )
    assert apolar_patches(polar) == ()
    assert largest_apolar_patch(polar) == 0.0


def test_the_dot_count_is_the_sampling_parameter_not_a_threshold() -> None:
    """Halving the sampling must not move the patch area much."""
    structure = platform()
    coarse = apolar_patches(structure, count=DOTS_PER_ATOM // 2)[0].area
    fine = apolar_patches(structure, count=DOTS_PER_ATOM)[0].area
    assert coarse == pytest.approx(fine, rel=0.25)
