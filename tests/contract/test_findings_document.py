"""`FINDINGS.md` keeps its evidence-class table in step with its entries.

That table is not decoration. The file's own preamble says a finding's
evidence class governs what may be written from it and that a reader of a
preprint cannot infer the class from the finding alone, so a finding with no
row is a finding with no stated licence -- and the table had silently stopped
at F-7 while F-8 and F-9 existed (`FINDINGS.md` F-10, `BUILD_JOURNAL.md`
ISSUE-020).

This is the third document in the project whose claims about itself are
asserted rather than typed, after the funnel tables and the requirements
coverage.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCUMENT = ROOT / "FINDINGS.md"
ENTRY = re.compile(r"^##\s+(F-\d+)\s+·")
TABLE_ROW = re.compile(r"^\|\s*\*\*(F-\d+)\*\*\s*\|")


def entries() -> list[str]:
    return [
        match.group(1) for line in DOCUMENT.read_text().splitlines() if (match := ENTRY.match(line))
    ]


def classified() -> list[str]:
    return [
        match.group(1)
        for line in DOCUMENT.read_text().splitlines()
        if (match := TABLE_ROW.match(line))
    ]


def test_every_finding_has_an_evidence_class() -> None:
    missing = [entry for entry in entries() if entry not in classified()]
    assert missing == [], f"no evidence-class row for {missing}"


def test_the_evidence_table_names_no_finding_that_does_not_exist() -> None:
    assert [row for row in classified() if row not in entries()] == []


def test_findings_are_numbered_once_and_in_order() -> None:
    found = entries()
    assert len(set(found)) == len(found)
    assert found == sorted(found, key=lambda name: int(name.split("-")[1]))


def test_every_evidence_class_states_what_it_does_not_license() -> None:
    """An empty limit column licenses everything.

    Which is the claim the table exists to prevent.
    """
    for line in DOCUMENT.read_text().splitlines():
        match = TABLE_ROW.match(line)
        if match is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 4, f"{match.group(1)}: expected four columns, got {len(cells)}"
        assert cells[3] not in {"", "—", "-"}, f"{match.group(1)} states no limit"
