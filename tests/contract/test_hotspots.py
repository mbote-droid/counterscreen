"""Hotspot schemes are derived from the prepared targets, not declared."""

import inspect
from pathlib import Path

import pytest

from counterscreen.core.design import Arm
from counterscreen.generate.hotspots import (
    HotspotError,
    HotspotScheme,
    m1_scheme,
    m2_scheme,
    m3_scheme,
)
from counterscreen.geometry.structure import Structure
from counterscreen.targets.prepare import read_pdb

TARGETS = Path(__file__).resolve().parents[2] / "campaigns" / "kras-g12d-pmhc" / "targets"
MUTANT_POSITION = 6


def load(name: str) -> Structure:
    path = TARGETS / f"{name}.pdb"
    if not path.exists():
        pytest.skip(f"{path} not prepared")
    return read_pdb(path)


def t_plus() -> Structure:
    return load("T_plus")


def d1() -> Structure:
    return load("D1_wild_type")


# --- M1 ---------------------------------------------------------------------


def test_m1_targets_the_aspartate() -> None:
    scheme = m1_scheme(t_plus(), "C", MUTANT_POSITION)
    assert scheme.arm is Arm.M1
    assert "C6" in scheme.labels()


def test_m1_excludes_arg114_because_it_is_not_displaceable() -> None:
    """FINDINGS F-5: bidentate across both oxygens, 2.95 and 3.04 A."""
    assert "A114" not in m1_scheme(t_plus(), "C", MUTANT_POSITION).labels()


def test_m1_reports_which_oxygen_is_reachable() -> None:
    (aspartate,) = [h for h in m1_scheme(t_plus(), "C", MUTANT_POSITION).hotspots if h.chain == "C"]
    assert "OD1" in aspartate.rationale
    assert "OD2" not in aspartate.rationale  # zero SASA, unreachable


# --- M2 ---------------------------------------------------------------------


def test_m2_recovers_the_network_the_specification_names() -> None:
    """PROTOCOL section 4 names the Asp6-Arg114-Gln70 surface; both appear."""
    labels = m2_scheme(t_plus(), "C", MUTANT_POSITION).labels()
    assert "A114" in labels
    assert "A70" in labels


def test_m2_is_a_surface_not_a_contact() -> None:
    labels = m2_scheme(t_plus(), "C", MUTANT_POSITION).labels()
    assert len(labels) > 4
    assert all(label.startswith("A") for label in labels)


# --- M3 ---------------------------------------------------------------------


def test_m3_selects_the_positions_that_move() -> None:
    """FINDINGS F-6: the displacement propagates from 6 to 7-9."""
    labels = m3_scheme(t_plus(), d1(), "C").labels()
    assert {"C7", "C8", "C9"} <= set(labels)


def test_m3_excludes_the_static_half_of_the_peptide() -> None:
    labels = set(m3_scheme(t_plus(), d1(), "C").labels())
    assert not ({"C1", "C2", "C3", "C4", "C5"} & labels)


def test_m3_records_the_fit_quality_in_its_rule() -> None:
    """A displacement is only meaningful relative to how well the frames agree."""
    rule = m3_scheme(t_plus(), d1(), "C").rule
    assert "RMSD" in rule
    assert "179 CA" in rule


def test_m3_needs_both_complexes() -> None:
    """Its signal is a difference, which no other arm's is."""
    parameters = list(inspect.signature(m3_scheme).parameters)
    assert parameters[:2] == ["mutant", "wild_type"]


# --- Scheme invariants ------------------------------------------------------


def test_an_empty_scheme_is_refused() -> None:
    with pytest.raises(HotspotError, match="no hotspots"):
        HotspotScheme(arm=Arm.M1, rule="none", hotspots=())


def test_the_contig_string_is_sorted_and_deduplicated() -> None:
    scheme = m2_scheme(t_plus(), "C", MUTANT_POSITION)
    inner = scheme.as_contig().strip("[]").split(",")
    assert inner == sorted(set(inner))


def test_every_hotspot_carries_its_reason() -> None:
    for scheme in (
        m1_scheme(t_plus(), "C", MUTANT_POSITION),
        m2_scheme(t_plus(), "C", MUTANT_POSITION),
        m3_scheme(t_plus(), d1(), "C"),
    ):
        assert all(h.rationale.strip() for h in scheme.hotspots)


def test_asking_for_a_residue_that_does_not_exist_is_refused() -> None:
    with pytest.raises(HotspotError, match="no residue"):
        m1_scheme(t_plus(), "C", 99)
