"""The append-only gate must catch evidence rewrites and allow additions.

``scripts`` is on the path via the pytest ``pythonpath`` setting.
"""

from check_append_only import violations

RESULTS = "campaigns/kras-g12d-pmhc/results/raw/run-001.csv"


def test_addition_is_allowed() -> None:
    assert violations(f"A\t{RESULTS}") == []


def test_modification_is_caught() -> None:
    assert violations(f"M\t{RESULTS}") == [("M", RESULTS)]


def test_deletion_is_caught() -> None:
    assert violations(f"D\t{RESULTS}") == [("D", RESULTS)]


def test_rename_is_caught_and_reports_the_original_path() -> None:
    new = "campaigns/kras-g12d-pmhc/results/raw/renamed.csv"
    assert violations(f"R100\t{RESULTS}\t{new}") == [("R100", RESULTS)]


def test_gitkeep_is_exempt() -> None:
    assert violations("D\tcampaigns/kras-g12d-pmhc/results/raw/.gitkeep") == []


def test_non_results_paths_are_ignored() -> None:
    assert violations("M\tcampaigns/kras-g12d-pmhc/controls/panel.yaml") == []
    assert violations("M\tsrc/counterscreen/core/__init__.py") == []


def test_refit_directory_is_also_evidence() -> None:
    path = "campaigns/kras-g12d-pmhc/results/refit/fit-001.json"
    assert violations(f"M\t{path}") == [("M", path)]


def test_multiple_violations_are_all_reported() -> None:
    other = "campaigns/kras-g12d-pmhc/results/refit/fit-001.json"
    out = violations(f"M\t{RESULTS}\nA\tcampaigns/x/results/raw/new.csv\nD\t{other}")
    assert out == [("M", RESULTS), ("D", other)]


def test_blank_and_malformed_lines_are_tolerated() -> None:
    assert violations("\n\nM\n  \n") == []
