"""Fail if any commit message carries AI attribution.

`CLAUDE.md` section 15 is unambiguous: commits show only `mbote-droid`, with
no AI co-author trailers, no "Generated with" lines, and no AI attribution of
any kind in commit messages or pull request descriptions. `build_rules.pdf`
Part XIV repeats it.

Enforced here rather than left to care: a trailer added by habit is easy to
miss in review and permanent in history once pushed.

`CLAUDE.md` section 16 says repository history is part of the artifact, and
`build_rules.pdf` Part XII.5 records that what an outside reader actually
responded to was the commit messages and code structure. A trailer in that
history is not cosmetic.
"""

from __future__ import annotations

import re
import subprocess
import sys

#: Patterns that must never appear in a commit message.
FORBIDDEN = (
    re.compile(r"co-authored-by:\s*claude", re.IGNORECASE),
    re.compile(r"co-authored-by:.*anthropic", re.IGNORECASE),
    re.compile(r"generated with.*claude", re.IGNORECASE),
    re.compile(r"^claude-session:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\U0001f916"),  # robot emoji, used by some attribution footers
)

_EXPECTED_ARGC = 2
_EXIT_OK = 0
_EXIT_VIOLATION = 1
_EXIT_USAGE = 2


def offending_patterns(message: str) -> list[str]:
    """Return the forbidden patterns a commit message matches."""
    return [pattern.pattern for pattern in FORBIDDEN if pattern.search(message)]


def main(argv: list[str]) -> int:
    """Scan every commit in a range for AI attribution."""
    if len(argv) != _EXPECTED_ARGC:
        print("usage: check_no_ai_attribution.py <rev-range>", file=sys.stderr)
        return _EXIT_USAGE
    rev_range = argv[1]

    listing = subprocess.run(  # noqa: S603
        ["git", "log", "--format=%H", rev_range],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if listing.returncode != 0:
        print(f"git log failed for {rev_range}: {listing.stderr.strip()}", file=sys.stderr)
        return _EXIT_USAGE

    found: list[tuple[str, list[str]]] = []
    for sha in listing.stdout.split():
        body = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--format=%B", sha],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        hits = offending_patterns(body)
        if hits:
            found.append((sha, hits))

    if not found:
        print(f"no AI attribution in commit messages across {rev_range}")
        return _EXIT_OK

    print("AI attribution found in commit messages (CLAUDE.md section 15):", file=sys.stderr)
    for sha, hits in found:
        print(f"  {sha[:12]}  matched {hits}", file=sys.stderr)
    return _EXIT_VIOLATION


if __name__ == "__main__":
    sys.exit(main(sys.argv))
