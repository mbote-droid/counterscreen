"""The campaign's real control panel, read from its own file.

Until this existed the panel lived in a test fixture, so the one number the
Stage -1 go/no-go turns on -- how many controls can actually calibrate -- was
not computed from anything the campaign could edit (`FINDINGS.md` F-23).

These tests are the live status of that question. When a supplementary control
is obtained and added to the catalogue, the shortfall here changes and the
failing assertion is the record of it.
"""

import pathlib

import pytest

from counterscreen.evaluate.panel import (
    MIN_POSITIVE_CONTROLS,
    Control,
    ControlRole,
    PanelError,
    SeedProvenance,
    assess_floor,
    load_catalogue,
    negative_from,
)

CATALOGUE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "campaigns"
    / "kras-g12d-pmhc"
    / "controls"
    / "controls.yaml"
)


def panel() -> tuple[Control, ...]:
    if not CATALOGUE.exists():
        pytest.skip(f"{CATALOGUE} not present")
    return load_catalogue(CATALOGUE)


# --- The live go/no-go ------------------------------------------------------


def test_the_catalogue_loads_and_validates() -> None:
    controls = panel()
    assert len(controls) == 10
    assert {control.name for control in controls} >= {"CTNNB1-S5F", "7OW6_TCR"}
    assert all(control.seed_provenance is SeedProvenance.DESIGNED for control in controls)


def test_the_panel_does_not_yet_reach_the_registered_floor() -> None:
    """The current state, asserted so that changing it is visible.

    One usable control of the five `PREREGISTRATION.md` section 6b requires.
    Stage -1 cannot calibrate an operating point until this reaches five.
    """
    report = assess_floor(panel())
    assert report.positives == 10
    assert report.single_residue == 2
    assert report.foldable == 1
    assert report.usable == 1
    assert not report.met
    assert report.shortfall == MIN_POSITIVE_CONTROLS - 1


def test_the_campaign_template_receptor_is_the_usable_one() -> None:
    """And it is usable because its construct sequence is in the repository."""
    usable = [c for c in panel() if c.is_single_residue and c.is_foldable]
    assert [control.name for control in usable] == ["7OW6_TCR"]

    tcr = usable[0]
    assert len(tcr.chains) == 2
    alpha, beta = tcr.chains
    assert (len(alpha), len(beta)) == (203, 246)
    assert tcr.on_target_peptide == "VVVGADGVGK"
    assert tcr.off_target_peptides[0][0] == "VVVGAGGVGK"


def test_every_control_that_claims_to_be_foldable_carries_a_sequence() -> None:
    for control in panel():
        assert control.is_foldable == bool(control.chains)


# --- What the catalogue refuses --------------------------------------------


def test_a_crystal_seeded_control_in_the_file_is_refused(tmp_path: pathlib.Path) -> None:
    """The registered mutant of PROTOCOL.md section 12.4b, via the loader."""
    leaked = tmp_path / "controls.yaml"
    leaked.write_text(
        "positives:\n"
        "  - name: leaked\n"
        "    allele: 'A*11:01'\n"
        "    target: KRAS G12D\n"
        "    on_target_peptide: VVVGADGVGK\n"
        "    seed_provenance: crystal\n",
        encoding="utf-8",
    )
    with pytest.raises(PanelError, match="crystal"):
        load_catalogue(leaked)


def test_a_control_missing_a_required_field_is_refused(tmp_path: pathlib.Path) -> None:
    incomplete = tmp_path / "controls.yaml"
    incomplete.write_text("positives:\n  - name: nameless\n", encoding="utf-8")
    with pytest.raises(PanelError, match="missing"):
        load_catalogue(incomplete)


def test_a_negative_without_its_registered_gate_is_refused(tmp_path: pathlib.Path) -> None:
    bad = tmp_path / "controls.yaml"
    bad.write_text(
        "negatives:\n"
        "  - name: greasy\n"
        "    role: negative\n"
        "    allele: 'A*11:01'\n"
        "    target: KRAS G12D\n"
        "    on_target_peptide: VVVGADGVGK\n",
        encoding="utf-8",
    )
    with pytest.raises(PanelError, match="failure gate"):
        load_catalogue(bad)


def test_an_empty_catalogue_is_an_empty_panel(tmp_path: pathlib.Path) -> None:
    empty = tmp_path / "controls.yaml"
    empty.write_text("positives: []\n", encoding="utf-8")
    assert load_catalogue(empty) == ()


def test_a_negative_cannot_be_derived_from_a_two_chain_control() -> None:
    """Scrambling one chain of a pair does not fail the gate it is registered to."""
    from counterscreen.core.design import Gate  # noqa: PLC0415

    tcr = next(control for control in panel() if control.name == "7OW6_TCR")
    with pytest.raises(PanelError, match="2 chains"):
        negative_from(tcr, "scrambled", seed=1, expected_gate=Gate.G1)


def test_the_supplementary_section_is_where_new_controls_go() -> None:
    """Published and acquired controls stay distinguishable in every report."""
    import yaml  # noqa: PLC0415

    document = yaml.safe_load(CATALOGUE.read_text(encoding="utf-8"))
    assert "supplementary" in document
    assert document["supplementary"] == []
    assert all(control.role is ControlRole.POSITIVE for control in panel()), (
        "every entry currently in the file is a positive control"
    )
