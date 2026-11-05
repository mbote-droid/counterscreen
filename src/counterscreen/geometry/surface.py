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
    """Total solvent-exposed apolar area, the quantity G5 thresholds on.

    A sum rather than a contiguous patch. `PROTOCOL.md` §8 registers G5 against
    the largest *contiguous* patch; contiguity needs a surface-adjacency pass
    that is not written yet, and reporting a total as though it were a patch
    would overstate what is measured. This is the honest intermediate.
    """
    values = atom_sasa(structure, probe_radius)
    return float(
        sum(
            values[row]
            for row, name in enumerate(structure.atom_names)
            if name[:1] in APOLAR_ELEMENTS
        )
    )
