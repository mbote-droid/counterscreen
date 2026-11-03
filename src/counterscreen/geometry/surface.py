"""Solvent accessibility, as pure structural arithmetic.

Two callers need it and neither should own it. Gate G5 thresholds on the
largest contiguous solvent-exposed apolar patch (`CLAUDE.md` §8, amendment
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
    array.element = [name[0] for name in structure.atom_names]
    return array


def atom_sasa(structure: Structure, probe_radius: float = 1.4) -> NDArray[np.float64]:
    """Per-atom solvent-accessible surface area, in square angstrom."""
    from biotite.structure import sasa  # noqa: PLC0415

    values = sasa(_to_atom_array(structure), probe_radius=probe_radius, vdw_radii="Single")
    return np.nan_to_num(np.asarray(values, dtype=np.float64))


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

    A sum rather than a contiguous patch. `CLAUDE.md` §8 registers G5 against
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
