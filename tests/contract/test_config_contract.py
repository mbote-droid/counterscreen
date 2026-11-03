"""Config schema contract (DESIGN.md section 8).

Defaults must equal the values registered in the specification, and an unknown
key must be an error rather than a silently ignored line.
"""

import dataclasses
from pathlib import Path

import pytest
import yaml

from counterscreen.core.config import (
    SUBMITTED_DESIGNS,
    CampaignConfig,
    ConfigError,
    GateConfig,
    SelectionConfig,
    TruncationConfig,
    load_config,
)

MINIMAL = {
    "campaign": "kras-g12d-pmhc",
    "truncation": {"first_residue": 1, "last_residue": 180},
}


def write(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path


def test_minimal_config_loads(tmp_path: Path) -> None:
    config = load_config(write(tmp_path, MINIMAL))
    assert config.campaign == "kras-g12d-pmhc"
    assert config.truncation.last_residue == 180


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        ("g0_chain_break_angstrom", 4.5),  # CLAUDE section 8, G0
        ("g0_max_ramachandran_outlier_fraction", 0.01),
        ("g1_max_scrmsd_angstrom", 2.0),  # CLAUDE section 8, G1
        ("g1_min_plddt", 80.0),
        ("g1_mpnn_sequences", 8),  # CLAUDE section 9, stage 2
        ("g3_control_percentile", 10.0),  # PREREG section 3, G3
        ("g4_sd_multiple", 2.0),  # CLAUDE section 7.1
        ("g5_control_percentile", 90.0),  # PREREG section 3, amendment A1
        ("g6_max_buried_unsatisfied_charges", 0),
        ("g8_min_length_aa", 10),  # CLAUDE section 3.6
        ("g8_max_length_aa", 250),
        ("g9_max_tm_score", 0.8),  # PREREG section 3, G9
    ],
)
def test_gate_defaults_match_the_registered_values(attribute: str, expected: float) -> None:
    assert getattr(GateConfig(), attribute) == expected


def test_registered_floors_and_counts() -> None:
    config = CampaignConfig(
        campaign="c", truncation=TruncationConfig(first_residue=1, last_residue=180)
    )
    assert config.selection.cluster_tm_score == 0.5  # amendment A2
    assert config.sampling.noise_floor_repeats == 5  # amendment A6
    assert config.evaluation.adversarial_per_class == 10  # amendment A4
    assert config.evaluation.min_positive_controls == 5  # PREREG section 6b
    assert config.evaluation.min_labelled_pairs == 40  # PREREG section 5b
    assert config.evaluation.min_targets == 4
    assert config.selection.total == SUBMITTED_DESIGNS


def test_an_unknown_key_is_an_error_and_names_the_valid_ones(tmp_path: Path) -> None:
    document = {**MINIMAL, "gates": {"g0_chain_break_angstroms": 4.5}}
    with pytest.raises(ConfigError) as excinfo:
        load_config(write(tmp_path, document))
    message = str(excinfo.value)
    assert "g0_chain_break_angstroms" in message
    assert "g0_chain_break_angstrom" in message


def test_an_unknown_top_level_key_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="unknown top-level"):
        load_config(write(tmp_path, {**MINIMAL, "gate": {}}))


def test_importing_the_v02_confidence_threshold_is_structurally_impossible(
    tmp_path: Path,
) -> None:
    """G2's operating point is a derived result, so it has no config field.

    0.61 is the AF3 ipSAE_min cutoff that CLAUDE section 12.3b records as the
    canonical v0.2 error. Trying to set it fails as an unknown key.
    """
    document = {**MINIMAL, "gates": {"g2_confidence": 0.61}}
    with pytest.raises(ConfigError, match="g2_confidence"):
        load_config(write(tmp_path, document))
    names = [f.name for f in dataclasses.fields(GateConfig)]
    assert not [n for n in names if n.startswith("g2")]


def test_truncation_is_required(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="truncation"):
        load_config(write(tmp_path, {"campaign": "kras-g12d-pmhc"}))


def test_truncation_boundaries_must_be_ordered(tmp_path: Path) -> None:
    document = {**MINIMAL, "truncation": {"first_residue": 180, "last_residue": 1}}
    with pytest.raises(ConfigError, match="below last_residue"):
        load_config(write(tmp_path, document))


def test_allocation_must_sum_to_twenty(tmp_path: Path) -> None:
    document = {**MINIMAL, "selection": {"m1": 10}}
    with pytest.raises(ConfigError, match="sums to 26"):
        load_config(write(tmp_path, document))


def test_percentiles_are_bounded(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"\[0, 100\]"):
        load_config(write(tmp_path, {**MINIMAL, "gates": {"g5_control_percentile": 150}}))


def test_tm_scores_are_bounded(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"\[0, 1\]"):
        load_config(write(tmp_path, {**MINIMAL, "gates": {"g9_max_tm_score": 1.5}}))


def test_noise_floor_needs_at_least_two_runs(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="at least 2"):
        load_config(write(tmp_path, {**MINIMAL, "sampling": {"noise_floor_repeats": 1}}))


def test_config_is_frozen() -> None:
    selection = SelectionConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        selection.m1 = 11  # type: ignore[misc]


def test_empty_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError, match="empty"):
        load_config(path)


def test_overrides_are_applied(tmp_path: Path) -> None:
    document = {**MINIMAL, "sampling": {"screening_seeds": 3}}
    config = load_config(write(tmp_path, document))
    assert config.sampling.screening_seeds == 3
    assert config.sampling.finalist_seeds == 5
