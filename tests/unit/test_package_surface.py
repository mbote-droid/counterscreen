"""The installed package exposes a coherent version and a working CLI."""

import re

from typer.testing import CliRunner

import counterscreen
from counterscreen.__main__ import app

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+.][0-9A-Za-z.-]+)?$")


def test_version_is_semver() -> None:
    assert SEMVER.match(counterscreen.__version__), counterscreen.__version__


def test_version_command_reports_the_package_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == counterscreen.__version__


def test_bare_invocation_shows_help_rather_than_failing_silently() -> None:
    result = CliRunner().invoke(app, [])
    assert "Usage" in result.output
