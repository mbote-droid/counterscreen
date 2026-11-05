"""SETUP.md section 2.6 assertions, run as tests against the committed targets.

Section 2.6 is explicit that these are written as tests, not as checks run
once. The reason is PROTOCOL.md section 3.1: if stripping the TCR, truncating or
re-protonating drops a disulfide, every downstream number is computed on a
subtly wrong target and nothing later would notice.
"""

from pathlib import Path

import pytest

from counterscreen.geometry.structure import Structure
from counterscreen.geometry.validity import check_geometry, find_disulfides, is_ramachandran_outlier
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


# --- G0 against experimental reality ----------------------------------------


@pytest.mark.parametrize(
    "name",
    ["T_plus", "D1_wild_type", "D2_peptide_free", "T_plus_platform", "D1_wild_type_platform"],
)
def test_deposited_structures_pass_the_geometry_gate(name: str) -> None:
    """The strongest available check on G0's calibration.

    These are experimentally determined coordinates. A gate built to reject
    non-physical generated backbones must not reject them: PROTOCOL.md section
    5.3 is explicit that a positive control failing a gate means the gate is
    wrong, not the control. Three of them did fail before the region
    definitions were corrected (FINDINGS F-9).
    """
    report = check_geometry(load(name))
    assert report.passed, report.reasons()


def test_a_residue_near_the_phi_wrap_is_not_an_outlier() -> None:
    """Phi is periodic: 178 degrees is two degrees from the beta basin edge."""
    assert not is_ramachandran_outlier("HIS", 178.0, 138.0)
    assert not is_ramachandran_outlier("HIS", -178.0, 138.0)


def test_adjacent_basins_leave_no_dead_zone() -> None:
    """A residue must not be an outlier for sitting between two rectangles."""
    for psi in (45.0, 50.0, 55.0, 60.0, 65.0):
        assert not is_ramachandran_outlier("ALA", -100.0, psi), psi


def test_the_gate_still_rejects_a_disallowed_conformation() -> None:
    """The correction must not have loosened the gate into uselessness."""
    assert is_ramachandran_outlier("ALA", 0.0, 0.0)
    assert is_ramachandran_outlier("GLY", 0.0, 0.0)


# --- G0 against a deposited structure with an unmodelled loop ---------------


def test_the_asymmetric_unit_with_an_unmodelled_loop_passes() -> None:
    """7OW4, the sixth deposited structure, and the one F-1 is about.

    All four peptide copies are numbered 4 then 7: positions 5 and 6 were
    never modelled. G0 read each jump as a 7.0-7.7 A chain break and, because
    the omega either side of the gap was computed from non-bonded atoms, as a
    cis-peptide too. Six false defects in a structure with none
    (`FINDINGS.md` F-12).
    """
    source = Path(__file__).resolve().parents[2] / "structures" / "7OW4.cif"
    if not source.exists():
        pytest.skip(f"{source} not available")
    from counterscreen.targets.prepare import read_cif  # noqa: PLC0415

    report = check_geometry(read_cif(source))
    assert report.passed, report.reasons()
    assert len(report.chain_gaps) == 4
    assert {gap.after_residue for gap in report.chain_gaps} == {4}
    assert {gap.next_residue for gap in report.chain_gaps} == {7}
    assert report.chain_breaks == ()
    assert report.cis_peptides == ()


def test_a_numbering_gap_is_not_a_chain_break_but_a_real_jump_is() -> None:
    """The distinction must not become a loophole.

    Consecutive numbering with a long CA-CA distance is still a break, which
    is the only case a generated backbone can produce: designs are numbered
    consecutively by construction.
    """
    coords = [[float(i) * 3.8, 0.0, 0.0] for i in range(4)]
    coords[3] = [40.0, 0.0, 0.0]  # a 29 A jump

    gapped = Structure.from_atoms(coords, ["CA"] * 4, ["ALA"] * 4, [1, 2, 3, 20], ["A"] * 4)
    report = check_geometry(gapped)
    assert report.chain_breaks == ()
    assert len(report.chain_gaps) == 1

    broken = Structure.from_atoms(coords, ["CA"] * 4, ["ALA"] * 4, [1, 2, 3, 4], ["A"] * 4)
    assert len(check_geometry(broken).chain_breaks) == 1


def test_a_disulfide_is_not_reported_as_a_clash() -> None:
    """The margin was 0.02 A (`FINDINGS.md` F-11).

    Every disulfide in the prepared targets measures 2.02-2.08 A against a
    2.0 A clash cutoff, and PROTOCOL.md section 3.1 separately asserts they
    must be present. Tested above the bond length so the exclusion is what is
    being checked, not the cutoff's luck.
    """
    import dataclasses  # noqa: PLC0415

    from counterscreen.core.config import GateConfig  # noqa: PLC0415

    structure = load("T_plus")
    bonds = find_disulfides(structure, DISULFIDE_MAX_ANGSTROM)
    assert len(bonds) >= MIN_PMHC_DISULFIDES
    assert max(bond.distance_angstrom for bond in bonds) < 2.2

    above_the_bond = dataclasses.replace(GateConfig(), g0_clash_distance_angstrom=2.2)
    report = check_geometry(structure, above_the_bond)
    assert report.clashes == (), [
        (structure.atom_names[c.first_atom], structure.atom_names[c.second_atom])
        for c in report.clashes
    ]
    assert report.passed, report.reasons()


def test_the_neighbour_search_finds_the_same_clashes_as_comparing_every_pair() -> None:
    """The KD-tree replaced an (n, n, 3) array; it must not change the answer."""
    import itertools  # noqa: PLC0415

    import numpy as np  # noqa: PLC0415

    from counterscreen.geometry.validity import _clashes  # noqa: PLC0415

    rng = np.random.default_rng(20261105)
    coords = rng.uniform(0.0, 8.0, size=(60, 3))
    structure = Structure.from_atoms(
        coords,
        ["CB"] * 60,
        ["ALA"] * 60,
        list(range(1, 61)),
        ["A"] * 30 + ["B"] * 30,
    )
    limit = 2.0
    found = {(c.first_atom, c.second_atom) for c in _clashes(structure, limit)}

    expected = set()
    for i, j in itertools.combinations(range(60), 2):
        if float(np.linalg.norm(coords[i] - coords[j])) >= limit:
            continue
        if structure.chain_ids[i] == structure.chain_ids[j] and abs(i - j) <= 1:
            continue
        expected.add((i, j))
    assert found == expected
    assert found  # the fixture must actually contain clashes


def test_an_untested_ramachandran_check_does_not_pass() -> None:
    """Zero outliers out of zero evaluated residues is not a clean structure."""
    two = Structure.from_atoms(
        [[0.0, 0.0, 0.0], [3.8, 0.0, 0.0]], ["CA"] * 2, ["ALA"] * 2, [1, 2], ["A"] * 2
    )
    report = check_geometry(two)
    assert report.ramachandran_untested
    assert report.ramachandran_outlier_fraction == 0.0
    assert not report.passed
    assert any("untested" in reason for reason in report.reasons())


def test_each_alignment_bound_applies_on_its_own() -> None:
    """`BUILD_JOURNAL.md` ISSUE-022: `first` alone used to fit the whole chain."""
    from counterscreen.geometry.align import superpose_on  # noqa: PLC0415

    coords = [[float(i) * 3.8, 0.0, 0.0] for i in range(12)]
    chain = Structure.from_atoms(coords, ["CA"] * 12, ["ALA"] * 12, list(range(1, 13)), ["A"] * 12)
    assert superpose_on(chain, chain, "A").paired == 12
    assert superpose_on(chain, chain, "A", first=10).paired == 3
    assert superpose_on(chain, chain, "A", last=3).paired == 3
    assert superpose_on(chain, chain, "A", first=10, last=12).paired == 3


def test_every_deposited_structure_passes_the_geometry_gate() -> None:
    """All ten, including the four source files beyond the prepared targets.

    The strongest calibration available, and the one that found F-9, F-11,
    F-12 and F-21 in turn. `PROTOCOL.md` section 5.3: a positive control
    failing a gate means the gate is wrong.
    """
    from counterscreen.targets.prepare import read_cif  # noqa: PLC0415

    sources = sorted((Path(__file__).resolve().parents[2] / "structures").glob("*.cif"))
    if not sources:
        pytest.skip("source structures not available")
    for source in sources:
        report = check_geometry(read_cif(source))
        assert report.passed, (source.name, report.reasons())


def test_bond_geometry_is_judged_as_a_fraction_not_on_the_first_outlier() -> None:
    """`FINDINGS.md` F-21: one residue 0.41 degrees past tolerance in 1,530.

    And the allowance cannot reach a design: at the registered 1%, a single
    outlier in a 55-75 residue binder is 1.3-1.8% and still fails.
    """
    from counterscreen.geometry.validity import BondOutlier, GeometryReport  # noqa: PLC0415

    def with_one_outlier(residues: int) -> GeometryReport:
        return GeometryReport(
            chain_breaks=(),
            chain_gaps=(),
            clashes=(),
            ramachandran_outliers=(),
            ramachandran_evaluated=residues,
            bond_outliers=(
                BondOutlier(residue_index=3, measurement="N-CA-C", observed=100.8, ideal=111.2),
            ),
            bond_evaluated=residues,
            non_l_residues=(),
            cis_peptides=(),
            disulfides=(),
            max_outlier_fraction=0.01,
        )

    for design_length in (55, 70, 75, 100):
        assert not with_one_outlier(design_length).passed, design_length
    assert with_one_outlier(1530).passed


def test_the_geometry_script_names_the_formats_it_accepts() -> None:
    """Handing it a .cif used to surface a float-parsing error from biotite."""
    import sys  # noqa: PLC0415

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    try:
        from check_geometry import read_structure  # noqa: PLC0415
    finally:
        sys.path.pop(0)

    with pytest.raises(SystemExit, match=r"\.cif"):
        read_structure(Path("structures/7OW4.xyz"))
