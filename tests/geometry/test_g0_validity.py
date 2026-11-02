"""Gate G0 on fixtures with known defects (DESIGN.md section 8)."""

import numpy as np
import pytest
from structures import ALPHA_HELIX, BETA_SHEET, build_chain, mirrored

from counterscreen.core.config import GateConfig
from counterscreen.geometry.structure import Structure
from counterscreen.geometry.validity import (
    check_geometry,
    chirality_improper,
    find_disulfides,
    is_ramachandran_outlier,
)

OUTLIER_TORSION = (0.0, 0.0)


def test_an_ideal_helix_passes_every_check() -> None:
    report = check_geometry(build_chain([ALPHA_HELIX] * 8))
    assert report.passed, report.reasons()
    assert report.chain_breaks == ()
    assert report.clashes == ()
    assert report.bond_outliers == ()
    assert report.ramachandran_outliers == ()


def test_an_ideal_sheet_passes_every_check() -> None:
    report = check_geometry(build_chain([BETA_SHEET] * 8))
    assert report.passed, report.reasons()


def test_a_known_chain_break_is_found_with_its_magnitude() -> None:
    structure = build_chain([ALPHA_HELIX] * 8)
    shifted = structure.coords.copy()
    moved = np.array([n >= 5 for n in structure.residue_numbers])
    shifted[moved] += np.array([12.0, 0.0, 0.0])
    broken = Structure.from_atoms(
        shifted,
        structure.atom_names,
        structure.residue_names,
        structure.residue_numbers,
        structure.chain_ids,
    )
    report = check_geometry(broken)
    assert not report.passed
    assert len(report.chain_breaks) == 1
    (gap,) = report.chain_breaks
    assert gap.after_residue == 4
    assert gap.distance_angstrom > GateConfig().g0_chain_break_angstrom
    assert "chain break" in " ".join(report.reasons())


def test_the_chain_break_threshold_comes_from_the_config() -> None:
    """A gate must read its registered threshold, not a hard-coded one."""
    structure = build_chain([ALPHA_HELIX] * 6)
    assert check_geometry(structure).chain_breaks == ()
    strict = GateConfig(g0_chain_break_angstrom=1.0)
    assert check_geometry(structure, strict).chain_breaks != ()


def test_a_known_clash_is_found() -> None:
    first = build_chain([ALPHA_HELIX] * 6, chain="A")
    overlapped = first.coords + np.array([0.4, 0.0, 0.0])
    structure = Structure.from_atoms(
        np.vstack([first.coords, overlapped]),
        [*first.atom_names, *first.atom_names],
        [*first.residue_names, *first.residue_names],
        [*first.residue_numbers, *first.residue_numbers],
        [*first.chain_ids, *["B"] * len(first.atom_names)],
    )
    report = check_geometry(structure)
    assert not report.passed
    assert report.clashes != ()
    assert min(c.distance_angstrom for c in report.clashes) < 2.0
    assert "clash" in " ".join(report.reasons())


def test_a_known_ramachandran_outlier_is_found() -> None:
    torsions = [ALPHA_HELIX, ALPHA_HELIX, OUTLIER_TORSION, ALPHA_HELIX, ALPHA_HELIX]
    report = check_geometry(build_chain(torsions))
    assert report.ramachandran_outliers != ()
    assert not report.passed
    assert "Ramachandran" in " ".join(report.reasons())


def test_the_outlier_fraction_is_measured_against_evaluable_residues() -> None:
    report = check_geometry(build_chain([ALPHA_HELIX] * 8))
    assert report.ramachandran_evaluated == 6
    assert report.ramachandran_outlier_fraction == 0.0


def test_glycine_is_allowed_the_mirror_regions_and_alanine_is_not() -> None:
    mirror_of_beta = (139.0, -135.0)
    assert not is_ramachandran_outlier("GLY", *mirror_of_beta)
    assert is_ramachandran_outlier("ALA", *mirror_of_beta)


def test_proline_phi_is_restricted() -> None:
    assert is_ramachandran_outlier("PRO", -150.0, 140.0)
    assert not is_ramachandran_outlier("PRO", -60.0, -45.0)


def test_a_non_proline_cis_peptide_fails() -> None:
    report = check_geometry(build_chain([ALPHA_HELIX] * 4, omega_degrees=0.0))
    assert report.cis_peptides != ()
    assert not report.passed
    assert "cis-peptide" in " ".join(report.reasons())


def test_a_cis_peptide_before_proline_is_allowed() -> None:
    structure = build_chain(
        [ALPHA_HELIX] * 4, residue_names=["ALA", "PRO", "PRO", "PRO"], omega_degrees=0.0
    )
    assert check_geometry(structure).cis_peptides == ()


def test_a_mirrored_structure_fails_on_chirality() -> None:
    """Reflection inverts every centre, so L and D cannot both pass."""
    structure = build_chain([ALPHA_HELIX] * 6)
    assert check_geometry(structure).non_l_residues == ()

    reflected = mirrored(structure)
    report = check_geometry(reflected)
    assert len(report.non_l_residues) == 6
    assert not report.passed
    assert "non-L" in " ".join(report.reasons())


def test_reflection_negates_every_chirality_improper() -> None:
    structure = build_chain([ALPHA_HELIX] * 5)
    reflected = mirrored(structure)
    for left, right in zip(structure.residues, reflected.residues, strict=True):
        assert chirality_improper(structure, left) == pytest.approx(
            -chirality_improper(reflected, right), abs=1e-9
        )


def test_glycine_is_not_chirality_checked() -> None:
    structure = build_chain([ALPHA_HELIX] * 4, residue_names=["GLY"] * 4)
    assert mirrored(structure) is not None
    assert check_geometry(mirrored(structure)).non_l_residues == ()


def test_a_disulfide_is_found_at_bonding_distance() -> None:
    structure = Structure.from_atoms(
        np.array([[0.0, 0.0, 0.0], [2.05, 0.0, 0.0]]),
        ["SG", "SG"],
        ["CYS", "CYS"],
        [10, 50],
        ["A", "A"],
    )
    (bond,) = find_disulfides(structure, max_distance=2.5)
    assert bond.distance_angstrom == pytest.approx(2.05)


def test_distant_cysteines_are_not_a_disulfide() -> None:
    structure = Structure.from_atoms(
        np.array([[0.0, 0.0, 0.0], [6.0, 0.0, 0.0]]),
        ["SG", "SG"],
        ["CYS", "CYS"],
        [10, 50],
        ["A", "A"],
    )
    assert find_disulfides(structure, max_distance=2.5) == ()


def test_bond_geometry_outliers_are_found() -> None:
    structure = build_chain([ALPHA_HELIX] * 5)
    stretched = structure.coords.copy()
    stretched[1] += np.array([0.9, 0.0, 0.0])  # drag one CA off its N
    distorted = Structure.from_atoms(
        stretched,
        structure.atom_names,
        structure.residue_names,
        structure.residue_numbers,
        structure.chain_ids,
    )
    report = check_geometry(distorted)
    assert report.bond_outliers != ()
    assert not report.passed
