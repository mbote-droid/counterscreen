"""Builders for synthetic structures with known defects.

DESIGN.md section 8 requires the geometry tests to run on a fixture with a
known chain break, a known clash and a known Ramachandran outlier. Rather than
ship a PDB file whose contents must be taken on trust, chains are built here
from ideal internal coordinates, so the defect under test is the only thing
wrong with the structure and its magnitude is exactly known.
"""

import numpy as np
from numpy.typing import NDArray

from counterscreen.geometry.structure import Structure
from counterscreen.geometry.validity import (
    IDEAL_C_N_ANGSTROM,
    IDEAL_C_N_CA_DEGREES,
    IDEAL_CA_C_ANGSTROM,
    IDEAL_CA_C_N_DEGREES,
    IDEAL_N_CA_ANGSTROM,
    IDEAL_N_CA_C_DEGREES,
)

CB_BOND_ANGSTROM = 1.53
N_CA_CB_DEGREES = 110.5
#: Dihedral C-N-CA-CB used to place the side chain of an L residue.
L_CB_DIHEDRAL_DEGREES = -122.6

ALPHA_HELIX = (-57.0, -47.0)
BETA_SHEET = (-139.0, 135.0)


def place_atom(
    a: NDArray[np.float64],
    b: NDArray[np.float64],
    c: NDArray[np.float64],
    *,
    bond: float,
    angle_degrees: float,
    dihedral_degrees: float,
) -> NDArray[np.float64]:
    """Place a fourth atom from internal coordinates (the NeRF construction)."""
    angle = np.radians(angle_degrees)
    torsion = np.radians(dihedral_degrees)
    bc = c - b
    bc = bc / np.linalg.norm(bc)
    normal = np.cross(b - a, bc)
    normal = normal / np.linalg.norm(normal)
    frame = np.array([bc, np.cross(normal, bc), normal]).T
    offset = np.array(
        [
            -bond * np.cos(angle),
            bond * np.sin(angle) * np.cos(torsion),
            bond * np.sin(angle) * np.sin(torsion),
        ]
    )
    return np.asarray(c + frame @ offset, dtype=np.float64)


def build_chain(
    torsions: list[tuple[float, float]],
    *,
    residue_names: list[str] | None = None,
    omega_degrees: float = 180.0,
    with_cb: bool = True,
    cb_dihedral_degrees: float = L_CB_DIHEDRAL_DEGREES,
    chain: str = "A",
) -> Structure:
    """Build an ideal backbone with the given (phi, psi) per residue."""
    names = residue_names or ["ALA"] * len(torsions)
    coords: list[NDArray[np.float64]] = []
    atoms: list[str] = []
    residues: list[str] = []
    numbers: list[int] = []

    n = np.array([0.0, 0.0, 0.0])
    ca = np.array([IDEAL_N_CA_ANGSTROM, 0.0, 0.0])
    swing = np.radians(180.0 - IDEAL_N_CA_C_DEGREES)
    c = ca + IDEAL_CA_C_ANGSTROM * np.array([np.cos(swing), np.sin(swing), 0.0])

    for index, (phi, psi) in enumerate(torsions):
        if index > 0:
            previous_n, previous_ca, previous_c = coords[-3], coords[-2], coords[-1]
            if with_cb:
                previous_n, previous_ca, previous_c = coords[-4], coords[-3], coords[-2]
            n = place_atom(
                previous_n,
                previous_ca,
                previous_c,
                bond=IDEAL_C_N_ANGSTROM,
                angle_degrees=IDEAL_CA_C_N_DEGREES,
                dihedral_degrees=torsions[index - 1][1],
            )
            ca = place_atom(
                previous_ca,
                previous_c,
                n,
                bond=IDEAL_N_CA_ANGSTROM,
                angle_degrees=IDEAL_C_N_CA_DEGREES,
                dihedral_degrees=omega_degrees,
            )
            c = place_atom(
                previous_c,
                n,
                ca,
                bond=IDEAL_CA_C_ANGSTROM,
                angle_degrees=IDEAL_N_CA_C_DEGREES,
                dihedral_degrees=phi,
            )
        for atom, position in (("N", n), ("CA", ca), ("C", c)):
            coords.append(position)
            atoms.append(atom)
            residues.append(names[index])
            numbers.append(index + 1)
        if with_cb:
            cb = place_atom(
                c,
                n,
                ca,
                bond=CB_BOND_ANGSTROM,
                angle_degrees=N_CA_CB_DEGREES,
                dihedral_degrees=cb_dihedral_degrees,
            )
            coords.append(cb)
            atoms.append("CB")
            residues.append(names[index])
            numbers.append(index + 1)
        _ = psi

    return Structure.from_atoms(np.array(coords), atoms, residues, numbers, [chain] * len(atoms))


def mirrored(structure: Structure) -> Structure:
    """Reflect a structure through the xy-plane, inverting every chirality."""
    flipped = structure.coords * np.array([1.0, 1.0, -1.0])
    return Structure.from_atoms(
        flipped,
        structure.atom_names,
        structure.residue_names,
        structure.residue_numbers,
        structure.chain_ids,
    )
