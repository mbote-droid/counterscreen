"""`REQUIREMENTS.md` counts its own rows correctly.

The coverage table at the foot of that document is three hand-typed numbers
describing the rows above it, which is the failure mode `DESIGN.md` section 9b
exists to prevent: it had drifted to 43 verified of 49 while the document
carried 57 rows, 53 of them verified. Nothing in the build noticed, because
nothing read the table.

This is not a test of the science. It is a test that a document which claims a
count can be trusted on it.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCUMENT = ROOT / "REQUIREMENTS.md"
ROW = re.compile(r"^\|\s*([A-Z]+-\d+)\s*\|")
COVERAGE = re.compile(r"^\|\s*(?:\*\*)?(Verified|Pending|Total)(?:\*\*)?\s*\|\s*(?:\*\*)?(\d+)")


def rows() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in DOCUMENT.read_text().splitlines():
        match = ROW.match(line)
        if match is None:
            continue
        status = [cell.strip() for cell in line.strip().strip("|").split("|")][-1]
        found.append((match.group(1), status))
    return found


def claimed() -> dict[str, int]:
    return {
        match.group(1).lower(): int(match.group(2))
        for line in DOCUMENT.read_text().splitlines()
        if (match := COVERAGE.match(line))
    }


def test_the_coverage_table_matches_the_rows() -> None:
    counted = rows()
    verified = sum(1 for _, status in counted if "verified" in status)
    pending = sum(1 for _, status in counted if "pending" in status)
    assert claimed() == {"verified": verified, "pending": pending, "total": len(counted)}


def test_every_requirement_is_verified_or_pending_and_nothing_else() -> None:
    for identifier, status in rows():
        assert ("verified" in status) ^ ("pending" in status), f"{identifier}: {status!r}"


def test_every_requirement_states_a_verification_method() -> None:
    """A requirement with no verification method is a wish, says the document."""
    for line in DOCUMENT.read_text().splitlines():
        match = ROW.match(line)
        if match is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        identifier, _, verification, status = cells[0], cells[1], cells[2], cells[3]
        if "pending" in status:
            continue
        assert verification not in {"", "—"}, f"{identifier} is verified by nothing"


def test_requirement_identifiers_are_unique() -> None:
    identifiers = [identifier for identifier, _ in rows()]
    assert len(set(identifiers)) == len(identifiers)
