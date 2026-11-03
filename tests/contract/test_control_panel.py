"""Control panel contract: the crystal-seed refusal, and the registered floor.

The crystal-seed assertion is the one DESIGN.md section 3 asks to be encoded
rather than written down, and PROTOCOL.md section 12.4b registers "return the
crystal pose as a control seed" as a mutant it must kill.
"""

import pytest

from counterscreen.core.design import Gate
from counterscreen.evaluate.panel import (
    MIN_POSITIVE_CONTROLS,
    Control,
    ControlRole,
    PanelError,
    SeedProvenance,
    assess_floor,
    negative_from,
    residue_differences,
    reverse,
    scramble,
    validate_panel,
)

# Supplementary Table 1 of the Liu et al. preprint, read from the page images.
LIU_PANEL = [
    ("MAGE-A3", "A*01:01", "EVDPIGHLY", [("ESDPIVAQY", "TTN")], 4),
    (
        "HIV-Env",
        "A*02:01",
        "KLTPLCVTL",
        [("KLQELCCTL", "YES1"), ("KLNPVCCEL", "ATG2B"), ("KLIPLCHQL", "CTNNAL1")],
        3,
    ),
    (
        "WT1",
        "A*02:01",
        "RMFPNAPYL",
        [("RLFPNLPEL", "ARHGEF11"), ("HLYPNTPYA", "APEX1"), ("RMFPTPPSL", "MED13L")],
        3,
    ),
    (
        "SARS-CoV-M",
        "A*02:01",
        "GLMWLSYFV",
        [("GLAWLSLFV", "KCNK5"), ("GLIFSSYFV", "KCNQ1"), ("SLMYLSYLV", "ELOVL6")],
        2,
    ),
    ("MART-1", "A*02:01", "ELAGIGILTV", [("GLMGAGIAQV", "HADHA"), ("SLAGLGLWLL", "LY6G6C")], 5),
    ("gp100", "A*02:01", "YLEPGPVTA", [("FQDPVPLTV", "TRIM24"), ("YLQPWPVDV", "ASB6")], 4),
    ("PAP", "A*02:01", "TLMSAMTNL", [("TLMSMVANL", "PSMB3"), ("TLFSALTGL", "ZMPSTE24")], 3),
    (
        "PRAME",
        "A*02:01",
        "ALYVDSLFFL",
        [
            ("ILYVDPLPMI", "ATP2A1"),
            ("MLTLNSIFYV", "ABCA5"),
            ("LMYLGSLAFL", "ADM"),
            ("YLSIDSALFV", "PQLC1"),
        ],
        5,
    ),
    ("CTNNB1-S5F", "A*03:01", "TTAPFLSGK", [("TTAPSLSGK", "CNTTB1")], 1),
]


def liu_controls() -> list[Control]:
    return [
        Control(
            name=name,
            role=ControlRole.POSITIVE,
            allele=allele,
            target=name,
            on_target_peptide=on,
            off_target_peptides=tuple(offs),
            source="Liu et al. 2024, Supplementary Table 1",
        )
        for name, allele, on, offs, _ in LIU_PANEL
    ]


def a_positive(name: str = "ctrl", sequence: str | None = "MKTAYIAKQR") -> Control:
    return Control(
        name=name,
        role=ControlRole.POSITIVE,
        allele="A*11:01",
        target="KRAS G12D",
        on_target_peptide="VVVGADGVGK",
        off_target_peptides=(("VVVGAGGVGK", "KRAS"),),
        binder_sequence=sequence,
    )


# --- Registered mutant: the crystal pose as a control seed ------------------


def test_a_control_seeded_from_a_crystal_pose_is_refused() -> None:
    leaked = Control(
        name="7OW6_TCR",
        role=ControlRole.POSITIVE,
        allele="A*11:01",
        target="KRAS G12D",
        on_target_peptide="VVVGADGVGK",
        seed_provenance=SeedProvenance.CRYSTAL,
    )
    with pytest.raises(PanelError, match="crystal"):
        validate_panel([leaked])


def test_the_refusal_names_the_offending_controls() -> None:
    bad = Control(
        name="leaky",
        role=ControlRole.POSITIVE,
        allele="A*11:01",
        target="x",
        on_target_peptide="VVVGADGVGK",
        seed_provenance=SeedProvenance.CRYSTAL,
    )
    with pytest.raises(PanelError, match="leaky"):
        validate_panel([a_positive(), bad])


def test_designed_seeding_is_accepted() -> None:
    validate_panel([a_positive()])


def test_assessing_the_floor_runs_the_crystal_check_first() -> None:
    """A leaked panel must not quietly return a floor report."""
    bad = Control(
        name="leaky",
        role=ControlRole.POSITIVE,
        allele="A*11:01",
        target="x",
        on_target_peptide="VVVGADGVGK",
        seed_provenance=SeedProvenance.CRYSTAL,
    )
    with pytest.raises(PanelError, match="crystal"):
        assess_floor([bad])


# --- Difficulty, measured from the real panel -------------------------------


@pytest.mark.parametrize(("name", "expected"), [(row[0], row[4]) for row in LIU_PANEL])
def test_difficulty_matches_the_published_panel(name: str, expected: int) -> None:
    control = next(c for c in liu_controls() if c.name == name)
    assert control.difficulty == expected


def test_only_one_published_control_is_a_single_residue_discrimination() -> None:
    """FINDINGS F-3, computed rather than asserted."""
    singles = [c.name for c in liu_controls() if c.is_single_residue]
    assert singles == ["CTNNB1-S5F"]


def test_our_own_task_is_the_same_difficulty_as_the_one_that_qualifies() -> None:
    assert residue_differences("VVVGADGVGK", "VVVGAGGVGK") == 1


def test_length_mismatched_peptides_have_no_stated_difficulty() -> None:
    assert residue_differences("VVVGADGVGK", "VVGADGVGK") is None


def test_a_control_with_no_off_targets_has_no_difficulty() -> None:
    bare = Control(
        name="x",
        role=ControlRole.POSITIVE,
        allele="A*11:01",
        target="x",
        on_target_peptide="VVVGADGVGK",
    )
    assert bare.difficulty is None
    assert not bare.is_single_residue


# --- The registered floor ---------------------------------------------------


def test_the_published_panel_does_not_reach_the_floor() -> None:
    """PREREGISTRATION section 6b needs five; the panel supplies one."""
    report = assess_floor(liu_controls())
    assert report.positives == 9
    assert report.single_residue == 1
    assert not report.met
    assert report.shortfall == MIN_POSITIVE_CONTROLS - 1


def test_the_panel_reports_how_many_controls_can_actually_be_folded() -> None:
    """No binder sequences were published, so none are foldable yet."""
    assert assess_floor(liu_controls()).foldable == 0
    assert assess_floor([*liu_controls(), a_positive()]).foldable == 1


def test_enough_single_residue_controls_clears_the_floor() -> None:
    panel = [a_positive(f"ctrl{i}") for i in range(MIN_POSITIVE_CONTROLS)]
    report = assess_floor(panel)
    assert report.met
    assert report.shortfall == 0


# --- Negative panel ---------------------------------------------------------


def test_a_negative_control_must_carry_its_registered_gate() -> None:
    with pytest.raises(PanelError, match="registered failure gate"):
        Control(
            name="scrambled",
            role=ControlRole.NEGATIVE,
            allele="A*11:01",
            target="x",
            on_target_peptide="VVVGADGVGK",
        )


def test_a_scrambled_negative_keeps_composition_and_changes_order() -> None:
    negative = negative_from(a_positive(), "scrambled", seed=7, expected_gate=Gate.G1)
    assert negative.binder_sequence is not None
    assert sorted(negative.binder_sequence) == sorted("MKTAYIAKQR")
    assert negative.binder_sequence != "MKTAYIAKQR"
    assert negative.expected_gate is Gate.G1
    assert negative.role is ControlRole.NEGATIVE


def test_scrambling_is_deterministic_under_a_seed() -> None:
    """A negative control that differs between runs is not a control."""
    assert scramble("MKTAYIAKQR", 7) == scramble("MKTAYIAKQR", 7)
    assert scramble("MKTAYIAKQR", 7) != scramble("MKTAYIAKQR", 8)


def test_a_reversed_negative_is_the_sequence_backwards() -> None:
    negative = negative_from(a_positive(), "reversed", seed=0, expected_gate=Gate.G1)
    assert negative.binder_sequence == reverse("MKTAYIAKQR")


def test_the_derivation_records_what_it_came_from() -> None:
    negative = negative_from(a_positive("parent"), "scrambled", seed=3, expected_gate=Gate.G1)
    assert "parent" in negative.source
    assert "seed=3" in negative.source


def test_a_negative_cannot_be_derived_without_a_sequence() -> None:
    with pytest.raises(PanelError, match="no binder sequence"):
        negative_from(a_positive(sequence=None), "scrambled", seed=1, expected_gate=Gate.G1)


def test_an_unknown_negative_kind_is_refused() -> None:
    with pytest.raises(PanelError, match="unknown negative kind"):
        negative_from(a_positive(), "mutated", seed=1, expected_gate=Gate.G1)


def test_duplicate_control_names_are_refused() -> None:
    with pytest.raises(PanelError, match="repeats a control name"):
        validate_panel([a_positive("same"), a_positive("same")])
