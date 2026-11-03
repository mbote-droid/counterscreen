"""SETUP.md section 2.6 assertions, run as tests against the committed targets.

Section 2.6 is explicit that these are written as tests, not as checks run
once. The reason is PROTOCOL.md section 3.1: if stripping the TCR, truncating or
re-protonating drops a disulfide, every downstream number is computed on a
subtly wrong target and nothing later would notice.
"""

from pathlib import Path

import pytest

from counterscreen.geometry.structure import Structure
from counterscreen.geometry.validity import find_disulfides
from counterscreen.targets.prepare import (
    DISULFIDE_MAX_ANGSTROM,
    MIN_PMHC_DISULFIDES,
    chain_sequence,
    read_pdb,
)

TARGETS = Path(__file__).resolve().parents[2] / "campaigns" / "kras-g12d-pmhc" / "targets"

G12D = "VVVGADGVGK"
WILD_TYPE = "VVVGAGGVGK"
TCR_CHAINS = {"D", "E"}
PLATFORM_MAX_RESIDUES = 200


def load(name: str) -> Structure:
    path = TARGETS / f"{name}.pdb"
    if not path.exists():
        pytest.skip(f"{path} not prepared")
    return read_pdb(path)


@pytest.mark.parametrize(
    ("name", "chains"),
    [
        ("T_plus", {"A", "B", "C"}),
        ("D1_wild_type", {"A", "B", "C"}),
        ("D2_peptide_free", {"A", "B"}),
    ],
)
def test_chain_composition_is_correct(name: str, chains: set[str]) -> None:
    assert set(load(name).chain_ids) == chains


@pytest.mark.parametrize(("name", "peptide"), [("T_plus", G12D), ("D1_wild_type", WILD_TYPE)])
def test_the_peptide_sequence_matches_exactly(name: str, peptide: str) -> None:
    assert chain_sequence(load(name), "C") == peptide


def test_the_two_peptides_differ_at_position_six_alone() -> None:
    """The entire discrimination signal, confirmed on the prepared targets."""
    mutant = chain_sequence(load("T_plus"), "C")
    wild = chain_sequence(load("D1_wild_type"), "C")
    differing = [i + 1 for i, (a, b) in enumerate(zip(mutant, wild, strict=True)) if a != b]
    assert differing == [6]
    assert (mutant[5], wild[5]) == ("D", "G")


@pytest.mark.parametrize("name", ["T_plus", "D1_wild_type", "D2_peptide_free"])
def test_no_tcr_atoms_remain(name: str) -> None:
    assert not (set(load(name).chain_ids) & TCR_CHAINS)


@pytest.mark.parametrize("name", ["T_plus", "D1_wild_type", "D2_peptide_free"])
def test_disulfides_survive_preparation(name: str) -> None:
    """PROTOCOL.md section 3.1: the HLA alpha-2 and beta-2m disulfides must survive."""
    found = find_disulfides(load(name), DISULFIDE_MAX_ANGSTROM)
    assert len(found) >= MIN_PMHC_DISULFIDES


def test_d2_has_no_peptide() -> None:
    assert "C" not in set(load("D2_peptide_free").chain_ids)


def test_d1_is_real_coordinates_not_a_mutated_target() -> None:
    """SETUP.md section 2.2: mutating T+ would bias toward our own repacking.

    Two independently solved crystal structures differ everywhere at the
    sub-angstrom level. A D1 built by mutating T+ in silico would be identical
    to it outside the repacked shell, so a non-trivial backbone difference
    across the whole groove is the signature of real coordinates.
    """
    plus, decoy = load("T_plus"), load("D1_wild_type")
    shared = 0
    moved = 0
    for left, right in zip(plus.residues, decoy.residues, strict=False):
        if left.chain == right.chain == "A" and left.has("CA") and right.has("CA"):
            shared += 1
            delta = plus.xyz(left, "CA") - decoy.xyz(right, "CA")
            if float((delta**2).sum()) ** 0.5 > 0.05:
                moved += 1
    assert shared > 100
    assert moved / shared > 0.5


@pytest.mark.parametrize("name", ["T_plus_platform", "D1_wild_type_platform"])
def test_the_platform_construct_drops_b2m_and_the_alpha3_domain(name: str) -> None:
    """SETUP.md section 2.5: roughly 180 residues, no beta-2m."""
    platform = load(name)
    assert set(platform.chain_ids) == {"A", "C"}
    assert len(platform.residues) <= PLATFORM_MAX_RESIDUES


def test_truncation_leaves_the_peptide_untouched() -> None:
    """Section 2.5 requires verifying the groove geometry is unchanged."""
    from counterscreen.targets.prepare import backbone_rmsd  # noqa: PLC0415

    assert backbone_rmsd(load("T_plus_platform"), load("T_plus"), "C") == pytest.approx(0.0)
