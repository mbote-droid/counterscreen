"""The Python version pin must agree in every place that states it.

Four files independently name the interpreter: .python-version, the
``requires-python`` constraint in pyproject.toml, the resolved constraint
baked into uv.lock, and the Dockerfile base image. If they drift, the failure
surfaces late and confusingly — a Docker build dying on "No interpreter found
for Python ==3.12.*" rather than a lint error naming the real problem. This
test turns that into an immediate, named failure.

Moving Python is a deliberate decision about the lockfile, so it should fail
here and be updated in all four places at once.
"""

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

MINOR = re.compile(r"3\.\d+")


def _python_version_file() -> str:
    return (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()


def _requires_python() -> str:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["requires-python"])


def _lock_requires_python() -> str:
    text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    match = re.search(r'^requires-python = "(?P<spec>[^"]+)"', text, re.MULTILINE)
    assert match, "uv.lock does not state requires-python"
    return match.group("spec")


def _dockerfile_bases() -> list[str]:
    text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    return re.findall(r"^FROM python:(?P<tag>\S+)", text, re.MULTILINE)


def test_the_pin_is_a_single_minor_version() -> None:
    pinned = _python_version_file()
    assert MINOR.fullmatch(pinned), f".python-version should name one minor, got {pinned!r}"


def test_requires_python_admits_only_the_pinned_minor() -> None:
    pinned = _python_version_file()
    spec = _requires_python()
    assert f">={pinned}" in spec, f"requires-python {spec!r} does not floor at {pinned}"
    minors = set(MINOR.findall(spec))
    unexpected = {m for m in minors if m != pinned and not spec.endswith(f"<{m}")}
    assert not unexpected, f"requires-python {spec!r} mentions unexpected minors: {unexpected}"


def test_lockfile_is_resolved_for_the_pinned_minor() -> None:
    pinned = _python_version_file()
    spec = _lock_requires_python()
    assert pinned in spec, (
        f"uv.lock is resolved for {spec!r}, not {pinned}. Re-run `uv lock` after moving the pin."
    )


def test_every_dockerfile_stage_uses_the_pinned_minor() -> None:
    pinned = _python_version_file()
    bases = _dockerfile_bases()
    assert bases, "Dockerfile has no FROM python: stage"
    wrong = [tag for tag in bases if not tag.startswith(f"{pinned}-")]
    assert not wrong, (
        f"Dockerfile base images {wrong} do not match the pinned Python {pinned}. "
        "uv sync --locked will fail inside the image."
    )


def test_all_dockerfile_stages_agree_with_each_other() -> None:
    bases = set(_dockerfile_bases())
    assert len(bases) == 1, f"Dockerfile stages disagree on the base image: {sorted(bases)}"
