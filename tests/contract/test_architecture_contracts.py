"""The DESIGN.md section 1 dependency table must stay complete and enforced.

These tests guard the guard: ``import-linter`` checks that the declared
boundaries hold, but nothing stops a new subpackage from being added with no
contract naming it. That package would then be silently unconstrained. The
tests below fail in that case.
"""

import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "src" / "counterscreen"

# The packages named in the DESIGN.md section 1 dependency table.
DESIGNED_PACKAGES = frozenset(
    {
        "analyze",
        "biophys",
        "core",
        "evaluate",
        "fold",
        "generate",
        "geometry",
        "rank",
        "report",
        "score",
        "sequence",
        "targets",
    }
)

# report is the top of the graph: it reads everything and nothing reads it, so
# it is the one package with no outbound restriction of its own.
SINK_PACKAGE = "report"


def _subpackages() -> frozenset[str]:
    return frozenset(
        path.name
        for path in PACKAGE_ROOT.iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    )


def _contracts() -> list[dict[str, Any]]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    contracts: list[dict[str, Any]] = config["tool"]["importlinter"]["contracts"]
    return contracts


def _qualified(package: str) -> str:
    return f"counterscreen.{package}"


def test_no_designed_package_is_missing() -> None:
    missing = DESIGNED_PACKAGES - _subpackages()
    assert not missing, f"packages in DESIGN.md section 1 but absent from src: {sorted(missing)}"


def test_no_undeclared_package_exists() -> None:
    extra = _subpackages() - DESIGNED_PACKAGES
    assert not extra, (
        f"packages present in src but not in the DESIGN.md section 1 table: {sorted(extra)}. "
        "Add the package to the table and give it an architecture contract."
    )


def test_every_package_states_its_boundary() -> None:
    for package in sorted(DESIGNED_PACKAGES):
        text = (PACKAGE_ROOT / package / "__init__.py").read_text(encoding="utf-8")
        assert "Boundary:" in text, f"{package}/__init__.py does not state its boundary"


def test_every_package_is_constrained_by_a_contract() -> None:
    """Every package bar the sink must appear as the source of some contract."""
    constrained: set[str] = set()
    for contract in _contracts():
        for module in contract["source_modules"]:
            constrained.add(module)

    unconstrained = {
        package
        for package in DESIGNED_PACKAGES - {SINK_PACKAGE}
        if _qualified(package) not in constrained
    }
    assert not unconstrained, (
        f"packages with no architecture contract naming them as a source: {sorted(unconstrained)}"
    )


def test_the_sink_package_is_protected() -> None:
    """Nothing may import report, and every other package must be held to that."""
    forbidding = {
        frozenset(contract["source_modules"])
        for contract in _contracts()
        if _qualified(SINK_PACKAGE) in contract["forbidden_modules"]
    }
    assert forbidding, f"no contract forbids importing {SINK_PACKAGE}"

    held = set[str]().union(*forbidding)
    unheld = {
        package for package in DESIGNED_PACKAGES - {SINK_PACKAGE} if _qualified(package) not in held
    }
    assert not unheld, f"packages allowed to import {SINK_PACKAGE}: {sorted(unheld)}"
