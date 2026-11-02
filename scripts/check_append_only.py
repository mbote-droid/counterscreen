"""Fail if a change rewrites committed evidence.

``campaigns/*/results/`` holds returned measurements. Those are evidence, so
they are committed and append-only: new measurements may be added, but an
existing record may not be modified, deleted or renamed away.

The reason this is mechanical rather than a convention is that the damage is
silent. A quietly edited sensorgram fit still produces a plausible results
table, and nothing downstream can tell that the number changed after the
claim was registered. Catching it needs a diff against the base, which is
exactly what CI has and a reviewer's eye does not.
"""

from __future__ import annotations

import re
import subprocess
import sys

# campaigns/<campaign>/results/...
RESULTS_PATH = re.compile(r"^campaigns/[^/]+/results/")

# Placeholders are structure, not evidence.
EXEMPT_SUFFIXES = (".gitkeep",)

# Modified, Deleted, or Renamed away from its recorded path.
REWRITING_STATUSES = frozenset({"M", "D", "R"})

# A name-status line is at minimum "<status>\t<path>".
_MIN_NAME_STATUS_FIELDS = 2

_EXPECTED_ARGC = 2
_EXIT_OK = 0
_EXIT_VIOLATION = 1
_EXIT_USAGE = 2


def _is_evidence(path: str) -> bool:
    return bool(RESULTS_PATH.match(path)) and not path.endswith(EXEMPT_SUFFIXES)


def violations(name_status_output: str) -> list[tuple[str, str]]:
    """Find evidence rewrites in ``git diff --name-status`` output.

    Returns a list of ``(status, path)`` pairs. For a rename, the reported
    path is the original one, since that is the record that disappeared.
    """
    found: list[tuple[str, str]] = []
    for line in name_status_output.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < _MIN_NAME_STATUS_FIELDS:
            continue
        status = fields[0]
        path = fields[1]
        if status[:1] in REWRITING_STATUSES and _is_evidence(path):
            found.append((status, path))
    return found


def main(argv: list[str]) -> int:
    """Compare against a base ref and report any evidence rewrite."""
    if len(argv) != _EXPECTED_ARGC:
        print("usage: check_append_only.py <base-ref>", file=sys.stderr)
        return _EXIT_USAGE
    base = argv[1]

    result = subprocess.run(  # noqa: S603
        ["git", "diff", "--name-status", f"{base}...HEAD", "--", "campaigns"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"git diff failed against {base}:\n{result.stderr}", file=sys.stderr)
        return _EXIT_USAGE

    found = violations(result.stdout)
    if not found:
        print(f"append-only: no committed evidence was rewritten against {base}")
        return _EXIT_OK

    print("append-only violation: committed evidence must not be rewritten.", file=sys.stderr)
    for status, path in found:
        print(f"  {status}\t{path}", file=sys.stderr)
    print(
        "\nAdd a new record instead. If a measurement was genuinely wrong, "
        "append a correction and log it; do not edit the original.",
        file=sys.stderr,
    )
    return _EXIT_VIOLATION


if __name__ == "__main__":
    sys.exit(main(sys.argv))
