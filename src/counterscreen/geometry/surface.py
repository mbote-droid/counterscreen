"""Solvent accessibility, as pure structural arithmetic.

Two callers need it and neither should own it. Gate G5 thresholds on the
largest contiguous solvent-exposed apolar patch (`PROTOCOL.md` §8, amendment
A1), and hotspot selection needs to know which atoms a binder could actually
reach (`FINDINGS.md` F-5 measured the Asp6 carboxylate at 6.4 Å² on OD1 and
zero on OD2 using exactly this).

Shrake-Rupley with a 1.4 Å probe. Absolute values depend on the radius set, so
comparisons between residues in one structure are the robust output and a
single number in isolation is not.
"""

import dataclasses
from typing import Any

import numpy as np
from numpy.typing import NDArray

from counterscreen.geometry.structure import Residue, Structure

#: Atoms treated as apolar for patch detection: carbon and sulfur.
APOLAR_ELEMENTS = frozenset({"C", "S"})

#: Elements a protein heavy-atom table may contain. Anything else means the
#: name was not parsed as intended, and an unrecognised element silently
#: becomes zero area under `biotite`'s single-radius set, which reads exactly
#: like "buried" (`FINDINGS.md` F-14). Refused rather than coerced.
KNOWN_ELEMENTS = frozenset({"C", "N", "O", "S", "H", "P"})


class SurfaceError(ValueError):
    """Raised when a structure's atoms cannot be assigned surface area."""


def element_of(atom_name: str) -> str:
    """Element symbol for a PDB atom name.

    Leading digits belong to hydrogen names such as ``1HB``, so they are
    stripped before the first character is read.
    """
    stripped = atom_name.strip().lstrip("0123456789")
    if not stripped:
        msg = f"atom name {atom_name!r} carries no element"
        raise SurfaceError(msg)
    return stripped[0].upper()


def _to_atom_array(structure: Structure) -> Any:  # noqa: ANN401
    # biotite ships no stubs, so AtomArray is Any; the annotation keeps mypy
    # strict quiet without widening anything that leaves this module.
    from biotite.structure import AtomArray  # noqa: PLC0415

    array: Any = AtomArray(len(structure.atom_names))
    array.coord = structure.coords
    array.atom_name = list(structure.atom_names)
    array.res_name = list(structure.residue_names)
    array.res_id = list(structure.residue_numbers)
    array.chain_id = list(structure.chain_ids)
    elements = [element_of(name) for name in structure.atom_names]
    unknown = sorted(set(elements) - KNOWN_ELEMENTS)
    if unknown:
        msg = (
            f"atom names gave unrecognised elements {unknown}; a radius lookup would "
            "return no value and the area would read as zero, which is indistinguishable "
            "from buried"
        )
        raise SurfaceError(msg)
    array.element = elements
    return array


def atom_sasa(structure: Structure, probe_radius: float = 1.4) -> NDArray[np.float64]:
    """Per-atom solvent-accessible surface area, in square angstrom."""
    from biotite.structure import sasa  # noqa: PLC0415

    values = np.asarray(
        sasa(_to_atom_array(structure), probe_radius=probe_radius, vdw_radii="Single"),
        dtype=np.float64,
    )
    # biotite returns NaN for an atom it has no radius for. Replacing it with
    # zero -- which this did -- turns "not measured" into "fully buried", and
    # the measurement that mattered most here was an exposure of exactly zero
    # (`FINDINGS.md` F-5, F-14). Hydrogens legitimately have no area under the
    # single-radius set and are excluded instead of patched.
    heavy = np.array([element_of(name) != "H" for name in structure.atom_names])
    missing = np.flatnonzero(~np.isfinite(values) & heavy)
    if missing.size:
        names = sorted({structure.atom_names[int(row)] for row in missing})
        msg = f"no solvent-accessible area returned for heavy atoms {names}"
        raise SurfaceError(msg)
    return np.where(np.isfinite(values), values, 0.0)


def residue_sasa(structure: Structure, probe_radius: float = 1.4) -> dict[tuple[str, int], float]:
    """Per-residue SASA, keyed by (chain, residue number)."""
    values = atom_sasa(structure, probe_radius)
    totals: dict[tuple[str, int], float] = {}
    for residue in structure.residues:
        key = (residue.chain, residue.number)
        totals[key] = float(sum(values[row] for row in residue.atoms.values()))
    return totals


def atom_sasa_for(
    structure: Structure, residue: Residue, probe_radius: float = 1.4
) -> dict[str, float]:
    """SASA of each named atom of one residue."""
    values = atom_sasa(structure, probe_radius)
    return {atom: float(values[row]) for atom, row in residue.atoms.items()}


def exposed_apolar_area(structure: Structure, probe_radius: float = 1.4) -> float:
    """Total solvent-exposed apolar area, summed over every apolar atom.

    Not the quantity G5 thresholds on -- see :func:`largest_apolar_patch` for
    that -- but reported alongside it, because the ratio of the two says
    whether a surface carries one large patch or many scattered ones, and a
    gate on the largest alone cannot distinguish them.
    """
    values = atom_sasa(structure, probe_radius)
    return float(
        sum(
            values[row]
            for row, name in enumerate(structure.atom_names)
            if element_of(name) in APOLAR_ELEMENTS
        )
    )


#: Dots per atom sphere. Shrake-Rupley's own sampling parameter: more dots
#: give a finer surface and a slower pass. 256 puts the dots about 0.7 A apart
#: on a carbon's expanded sphere, which is fine enough that patch boundaries
#: are set by the surface rather than by the sampling.
DOTS_PER_ATOM = 256

#: Two accessible dots are adjacent when they lie within this multiple of the
#: mean dot separation. Registered by amendment A13. The scale comes from the
#: sampling rather than from taste, which is the point: an adjacency in
#: angstrom would be a free parameter underneath a registered gate, while
#: "neighbouring dots on the same surface" is a property of the surface.
DOT_ADJACENCY_SPACINGS = 1.8

#: Fewest dots a region must span to count as a patch. Four dots is about
#: 1.9 square angstrom on a carbon at the default sampling: smaller than any
#: patch with a physical meaning, and larger than the one- and two-dot
#: fragments that the sampling throws into crevices. The floor is on the
#: *resolution* of the measurement, not on significance -- G5's threshold is a
#: percentile of the control panel, so what counts as a large patch is
#: answered by the panel and not here.
MIN_PATCH_DOTS = 4


@dataclasses.dataclass(frozen=True, slots=True)
class ApolarPatch:
    """One contiguous run of solvent-exposed apolar surface.

    Patches partition the accessible *dots*, not the atoms, so one atom can
    appear in two patches: a side chain exposed on both sides of a polar ridge
    contributes surface to each. ``first_dot`` is unique per patch and orders
    them, because ``atoms`` is not unique for that reason.
    """

    area: float
    atoms: tuple[int, ...]
    dots: int
    first_dot: int

    @property
    def size(self) -> int:
        """How many exposed apolar atoms the patch spans."""
        return len(self.atoms)


def sphere_points(count: int = DOTS_PER_ATOM) -> NDArray[np.float64]:
    """Near-uniform unit vectors by the golden-spiral construction.

    Deterministic, so a patch area is reproducible to the bit. A random or
    seeded sampling would make the gate's own threshold depend on the seed.
    """
    if count < 1:
        msg = f"a sphere needs at least one point, got {count}"
        raise SurfaceError(msg)
    index = np.arange(count, dtype=np.float64) + 0.5
    z = 1.0 - 2.0 * index / count
    radius = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    golden = np.pi * (1.0 + 5.0**0.5) * index
    return np.stack([radius * np.cos(golden), radius * np.sin(golden), z], axis=1)


def _radii(structure: Structure) -> NDArray[np.float64]:
    """Single-value van der Waals radii, the same set the areas are built on.

    `biotite` ships no stubs, so the radius comes back as ``Any``; a missing
    element would come back as ``None``, which :func:`_to_atom_array` has
    already refused by the time this runs.
    """
    from biotite.structure.info import vdw_radius_single  # noqa: PLC0415

    radii: list[float] = []
    for name in structure.atom_names:
        radius: Any = vdw_radius_single(element_of(name))
        if radius is None:
            msg = f"no van der Waals radius for atom {name!r}"
            raise SurfaceError(msg)
        radii.append(float(radius))
    return np.array(radii, dtype=np.float64)


def accessible_dots(
    structure: Structure, probe_radius: float = 1.4, count: int = DOTS_PER_ATOM
) -> tuple[NDArray[np.float64], NDArray[np.int_]]:
    """Solvent-accessible surface dots, and the atom row each belongs to.

    A dot on atom *i*'s expanded sphere is accessible when it lies outside
    every other atom's expanded sphere -- the Shrake-Rupley test itself. The
    dots are what make contiguity measurable: adjacency between *atoms*
    percolates across a protein surface, because exposed carbons are
    everywhere, so a distance rule on atom centres merges the whole surface
    into one patch and measures nothing (`FINDINGS.md` F-22).
    """
    from scipy.spatial import cKDTree  # noqa: PLC0415

    heavy = structure.heavy_atom_rows()
    if heavy.size == 0:
        return np.zeros((0, 3)), np.zeros(0, dtype=np.int_)
    radii = _radii(structure)[heavy] + probe_radius
    coords = structure.coords[heavy]
    unit = sphere_points(count)
    tree = cKDTree(coords)
    reach = float(radii.max() * 2.0)

    kept: list[NDArray[np.float64]] = []
    owners: list[NDArray[np.int_]] = []
    for position in range(len(heavy)):
        dots = coords[position] + radii[position] * unit
        neighbours = [n for n in tree.query_ball_point(coords[position], reach) if n != position]
        if neighbours:
            separation = np.linalg.norm(dots[:, None, :] - coords[neighbours][None, :, :], axis=-1)
            free = np.all(separation > radii[neighbours][None, :], axis=1)
        else:
            free = np.ones(len(dots), dtype=bool)
        if not free.any():
            continue
        kept.append(dots[free])
        owners.append(np.full(int(free.sum()), int(heavy[position]), dtype=np.int_))
    if not kept:
        return np.zeros((0, 3)), np.zeros(0, dtype=np.int_)
    return np.concatenate(kept), np.concatenate(owners)


def dot_sasa(
    structure: Structure, probe_radius: float = 1.4, count: int = DOTS_PER_ATOM
) -> dict[int, float]:
    """Per-atom SASA from the dot count, as a check on the library's own value.

    `build_rules.pdf` section 2.7 asks for a differential test wherever a
    library does something critical. This is that test for SASA: the same
    quantity by an independent route, agreeing with `biotite` to the sampling
    error rather than taken on trust.
    """
    _, owners = accessible_dots(structure, probe_radius, count)
    radii = _radii(structure) + probe_radius
    totals: dict[int, float] = {}
    for row in np.unique(owners):
        sphere = 4.0 * np.pi * radii[row] ** 2
        totals[int(row)] = float(sphere * np.count_nonzero(owners == row) / count)
    return totals


def apolar_patches(
    structure: Structure,
    probe_radius: float = 1.4,
    count: int = DOTS_PER_ATOM,
) -> tuple[ApolarPatch, ...]:
    """Contiguous solvent-exposed apolar patches, largest area first.

    Connected components of the accessible apolar *dots*, joined when they lie
    within :data:`DOT_ADJACENCY_SPACINGS` of the mean dot separation. Each
    patch's area is the dot-derived area of its own dots, so the areas sum to
    the total exposed apolar surface by construction.
    """
    from scipy.sparse import coo_matrix  # noqa: PLC0415
    from scipy.sparse.csgraph import connected_components  # noqa: PLC0415
    from scipy.spatial import cKDTree  # noqa: PLC0415

    dots, owners = accessible_dots(structure, probe_radius, count)
    if dots.size == 0:
        return ()
    apolar = np.array(
        [element_of(structure.atom_names[int(row)]) in APOLAR_ELEMENTS for row in owners]
    )
    dots, owners = dots[apolar], owners[apolar]
    if dots.size == 0:
        return ()

    radii = _radii(structure) + probe_radius
    # Mean spacing between dots on a sphere: each covers 4 pi R^2 / count, so
    # the equivalent disc radius is 2R / sqrt(count).
    spacing = float(2.0 * radii[np.unique(owners)].mean() / np.sqrt(count))
    cutoff = DOT_ADJACENCY_SPACINGS * spacing

    pairs = cKDTree(dots).query_pairs(cutoff, output_type="ndarray")
    graph = coo_matrix(
        (np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])),
        shape=(len(dots), len(dots)),
    )
    _, labels = connected_components(graph, directed=False)

    areas = 4.0 * np.pi * radii[owners] ** 2 / count
    patches: list[ApolarPatch] = []
    for label in np.unique(labels):
        members = np.flatnonzero(labels == label)
        if members.size < MIN_PATCH_DOTS:
            continue
        patches.append(
            ApolarPatch(
                area=float(areas[members].sum()),
                atoms=tuple(sorted({int(row) for row in owners[members]})),
                dots=int(members.size),
                first_dot=int(members[0]),
            )
        )
    return tuple(sorted(patches, key=lambda patch: (-patch.area, patch.first_dot)))


def largest_apolar_patch(structure: Structure, probe_radius: float = 1.4) -> float:
    """Area of the largest contiguous solvent-exposed apolar patch.

    The quantity gate G5 thresholds on (`PROTOCOL.md` §8, amendment A1): at or
    below the 90th percentile of the positive control panel. A *derivation
    rule*, which is what makes the contiguity convention above tolerable --
    the threshold is computed from the panel with the same rule, so a looser
    or tighter adjacency moves the designs and the reference together rather
    than shifting one against the other.
    """
    patches = apolar_patches(structure, probe_radius)
    return patches[0].area if patches else 0.0
