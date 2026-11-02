"""Provenance manifest contract (DESIGN.md sections 5 and 8).

The schema must round-trip, and the manifest must be appended to and never
overwritten.
"""

from pathlib import Path

import pytest
import yaml

from counterscreen.core.provenance import (
    ManifestEntry,
    ProvenanceError,
    append_entry,
    git_state,
    new_entry,
    read_entries,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHA_LENGTH = 40


def an_entry(stage: str = "fold_counterscreen") -> ManifestEntry:
    return new_entry(
        stage,
        git_commit="39d7453deadbeef",
        git_dirty=False,
        python_version="3.12.3",
        packages_sha256="abc123",
        seeds=[1, 2],
        inputs_sha256={"target": "aaa", "design": "bbb"},
        outputs_sha256={"scores": "ccc"},
        model="protenix-v2",
        model_weights_sha256={"protenix-v2": "ddd"},
        kaggle_image="gcr.io/kaggle-images/python@sha256:eee",
        gpu="Tesla T4",
        wall_time_s=91.5,
    )


def test_schema_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    append_entry(path, an_entry())
    (restored,) = list(read_entries(path))
    assert restored == an_entry()


def test_every_design_section_5_field_is_present(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    append_entry(path, an_entry())
    document = next(iter(yaml.safe_load_all(path.read_text(encoding="utf-8"))))
    for field in (
        "stage",
        "git_commit",
        "packages_sha256",
        "model",
        "model_weights_sha256",
        "seeds",
        "inputs_sha256",
        "outputs_sha256",
        "wall_time_s",
        "gpu",
        "kaggle_image",
    ):
        assert field in document, field


def test_appending_never_rewrites_what_is_already_there(tmp_path: Path) -> None:
    """The bytes of the first entry must survive the second verbatim."""
    path = tmp_path / "manifest.yaml"
    append_entry(path, an_entry("stage_one"))
    first = path.read_bytes()

    append_entry(path, an_entry("stage_two"))
    second = path.read_bytes()

    assert second.startswith(first)
    assert len(second) > len(first)
    assert [entry.stage for entry in read_entries(path)] == ["stage_one", "stage_two"]


def test_mapping_keys_are_sorted_so_output_does_not_depend_on_dict_order(
    tmp_path: Path,
) -> None:
    forward = new_entry(
        "s",
        git_commit="c",
        git_dirty=False,
        python_version="3.12.3",
        packages_sha256="p",
        inputs_sha256={"alpha": "1", "zeta": "2", "mu": "3"},
    )
    backward = new_entry(
        "s",
        git_commit="c",
        git_dirty=False,
        python_version="3.12.3",
        packages_sha256="p",
        inputs_sha256={"zeta": "2", "mu": "3", "alpha": "1"},
    )
    assert forward == backward

    one, two = tmp_path / "a.yaml", tmp_path / "b.yaml"
    append_entry(one, forward)
    append_entry(two, backward)
    assert one.read_bytes() == two.read_bytes()


def test_the_dirty_flag_is_recorded_rather_than_suppressed(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    append_entry(
        path,
        new_entry(
            "s",
            git_commit="c",
            git_dirty=True,
            python_version="3.12.3",
            packages_sha256="p",
        ),
    )
    (entry,) = list(read_entries(path))
    assert entry.git_dirty is True


def test_an_entry_must_name_its_stage() -> None:
    with pytest.raises(ProvenanceError, match="stage"):
        new_entry("  ", git_commit="c", git_dirty=False, python_version="3", packages_sha256="p")


def test_an_entry_must_carry_a_commit() -> None:
    with pytest.raises(ProvenanceError, match="git commit"):
        new_entry("s", git_commit="", git_dirty=False, python_version="3", packages_sha256="p")


def test_a_malformed_document_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text("---\n- not: a mapping\n", encoding="utf-8")
    with pytest.raises(ProvenanceError, match="non-mapping"):
        list(read_entries(path))


def test_git_state_reads_this_repository() -> None:
    commit, dirty = git_state(REPO_ROOT)
    assert len(commit) == SHA_LENGTH
    assert all(c in "0123456789abcdef" for c in commit)
    assert isinstance(dirty, bool)


def test_git_state_refuses_a_directory_that_is_not_a_repository(tmp_path: Path) -> None:
    with pytest.raises(ProvenanceError, match="git rev-parse"):
        git_state(tmp_path)
