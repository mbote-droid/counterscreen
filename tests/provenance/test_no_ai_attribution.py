"""Commit messages must carry no AI attribution (CLAUDE.md section 15)."""

import subprocess
from pathlib import Path

from check_no_ai_attribution import offending_patterns

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_a_co_author_trailer_is_caught() -> None:
    assert offending_patterns("Fix thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>")


def test_a_session_trailer_is_caught() -> None:
    assert offending_patterns("Fix thing\n\nClaude-Session: https://claude.ai/code/session_x")


def test_a_generated_with_line_is_caught() -> None:
    assert offending_patterns("Fix thing\n\nGenerated with Claude Code")


def test_the_robot_emoji_footer_is_caught() -> None:
    assert offending_patterns("Fix thing\n\n\U0001f916 Generated with something")


def test_an_ordinary_message_is_clean() -> None:
    assert not offending_patterns(
        "targets: build T+ and the decoys\n\nVerified the disulfides survive preparation."
    )


def test_the_word_claude_alone_is_not_a_trailer() -> None:
    """Prose may legitimately discuss the assistant; only attribution is banned."""
    assert not offending_patterns(
        "AGENT_ERRORS: record where the assistant got the lockfile pin wrong"
    )


def test_the_whole_history_is_clean() -> None:
    """The guard applied to this repository, which is the point of it."""
    shas = subprocess.run(
        ["git", "log", "--format=%H"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert shas
    dirty = []
    for sha in shas:
        body = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--format=%B", sha],  # noqa: S607
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if offending_patterns(body):
            dirty.append(sha[:12])
    assert not dirty, f"commits carrying AI attribution: {dirty}"
