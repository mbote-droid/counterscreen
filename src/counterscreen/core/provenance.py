"""The provenance manifest: what ran, on what, with which seeds.

`DESIGN.md` section 5 fixes the schema and one rule about it -- "written by
every stage, appended, never overwritten". Both are implemented here.
`build_rules.pdf` section 4.2 adds the ``dirty`` flag, which admits
uncommitted changes rather than hiding them, and that is kept: a manifest that
quietly claims a clean tree is worse than one that says the tree was dirty.

**This file is the one output expected to differ between runs.**
`build_rules.pdf` section 4.1 requires byte-identical results across runs and
forbids timestamps and unsorted sets in output, but wall time and the GPU name
are in the section 5 schema precisely because they are facts about an
execution rather than about a result. Keeping them here, and out of the
metrics, is what lets the results stay byte-comparable while the provenance
stays honest about the machine. Mapping keys are still sorted, so the only
things that vary between two runs of the same work are the measured ones.
"""

import dataclasses
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

import yaml


class ProvenanceError(RuntimeError):
    """Raised when a manifest cannot be written or read safely."""


def _pairs(mapping: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    """Freeze a mapping into sorted pairs, so output never depends on dict order."""
    return tuple(sorted(mapping.items()))


@dataclasses.dataclass(frozen=True, slots=True)
class ManifestEntry:
    """One stage's provenance record, in the `DESIGN.md` section 5 schema."""

    stage: str
    git_commit: str
    git_dirty: bool
    python_version: str
    packages_sha256: str
    seeds: tuple[int, ...] = ()
    inputs_sha256: tuple[tuple[str, str], ...] = ()
    outputs_sha256: tuple[tuple[str, str], ...] = ()
    model: str | None = None
    model_weights_sha256: tuple[tuple[str, str], ...] = ()
    kaggle_image: str | None = None
    gpu: str | None = None
    wall_time_s: float | None = None

    def __post_init__(self) -> None:
        """Refuse a record that cannot identify what it describes."""
        if not self.stage.strip():
            msg = "a manifest entry must name its stage"
            raise ProvenanceError(msg)
        if not self.git_commit.strip():
            msg = "a manifest entry must carry a git commit"
            raise ProvenanceError(msg)

    def to_document(self) -> dict[str, object]:
        """Render as a plain mapping for YAML, with every mapping key sorted."""
        document: dict[str, object] = {
            "stage": self.stage,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "python_version": self.python_version,
            "packages_sha256": self.packages_sha256,
            "seeds": list(self.seeds),
            "inputs_sha256": dict(self.inputs_sha256),
            "outputs_sha256": dict(self.outputs_sha256),
            "model_weights_sha256": dict(self.model_weights_sha256),
        }
        optional: dict[str, object] = {
            "model": self.model,
            "kaggle_image": self.kaggle_image,
            "gpu": self.gpu,
            "wall_time_s": self.wall_time_s,
        }
        document.update({k: v for k, v in optional.items() if v is not None})
        return document

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> "ManifestEntry":
        """Rebuild an entry from a parsed YAML document."""

        def text(key: str) -> str:
            value = document.get(key)
            if not isinstance(value, str):
                msg = f"manifest entry field {key!r} must be a string, got {value!r}"
                raise ProvenanceError(msg)
            return value

        def mapping(key: str) -> tuple[tuple[str, str], ...]:
            value = document.get(key) or {}
            if not isinstance(value, dict):
                msg = f"manifest entry field {key!r} must be a mapping"
                raise ProvenanceError(msg)
            return _pairs({str(k): str(v) for k, v in value.items()})

        def optional_text(key: str) -> str | None:
            value = document.get(key)
            return value if isinstance(value, str) else None

        raw_seeds = document.get("seeds") or []
        if not isinstance(raw_seeds, Sequence) or isinstance(raw_seeds, str | bytes):
            msg = "manifest entry field 'seeds' must be a list"
            raise ProvenanceError(msg)
        wall = document.get("wall_time_s")
        return cls(
            stage=text("stage"),
            git_commit=text("git_commit"),
            git_dirty=bool(document.get("git_dirty", False)),
            python_version=text("python_version"),
            packages_sha256=text("packages_sha256"),
            seeds=tuple(int(seed) for seed in raw_seeds),
            inputs_sha256=mapping("inputs_sha256"),
            outputs_sha256=mapping("outputs_sha256"),
            model=optional_text("model"),
            model_weights_sha256=mapping("model_weights_sha256"),
            kaggle_image=optional_text("kaggle_image"),
            gpu=optional_text("gpu"),
            wall_time_s=float(wall) if isinstance(wall, int | float) else None,
        )


def new_entry(
    stage: str,
    *,
    git_commit: str,
    git_dirty: bool,
    python_version: str,
    packages_sha256: str,
    seeds: Sequence[int] = (),
    inputs_sha256: Mapping[str, str] | None = None,
    outputs_sha256: Mapping[str, str] | None = None,
    model: str | None = None,
    model_weights_sha256: Mapping[str, str] | None = None,
    kaggle_image: str | None = None,
    gpu: str | None = None,
    wall_time_s: float | None = None,
) -> ManifestEntry:
    """Build a :class:`ManifestEntry`, sorting every mapping on the way in."""
    return ManifestEntry(
        stage=stage,
        git_commit=git_commit,
        git_dirty=git_dirty,
        python_version=python_version,
        packages_sha256=packages_sha256,
        seeds=tuple(seeds),
        inputs_sha256=_pairs(inputs_sha256 or {}),
        outputs_sha256=_pairs(outputs_sha256 or {}),
        model=model,
        model_weights_sha256=_pairs(model_weights_sha256 or {}),
        kaggle_image=kaggle_image,
        gpu=gpu,
        wall_time_s=wall_time_s,
    )


def append_entry(path: Path, entry: ManifestEntry) -> None:
    """Append one entry to a manifest, as a new YAML document.

    Opened in append mode, never in write mode. A manifest records what has
    already happened, so truncating it would destroy evidence of a run that did
    occur, which is the same rule `DESIGN.md` section 1 applies to returned
    measurements.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(
        entry.to_document(),
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("---\n")
        handle.write(rendered)


def read_entries(path: Path) -> Iterator[ManifestEntry]:
    """Yield every entry in a manifest, oldest first."""
    with path.open("r", encoding="utf-8") as handle:
        for document in yaml.safe_load_all(handle):
            if document is None:
                continue
            if not isinstance(document, dict):
                msg = f"{path} contains a non-mapping document"
                raise ProvenanceError(msg)
            yield ManifestEntry.from_document(document)


def git_state(repo: Path) -> tuple[str, bool]:
    """Return the current commit and whether the working tree is dirty.

    The dirty flag is reported, never suppressed: `build_rules.pdf` section 4.2
    keeps it precisely so a result produced from uncommitted code says so.
    """

    def run(*args: str) -> str:
        completed = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            msg = f"git {' '.join(args)} failed in {repo}: {completed.stderr.strip()}"
            raise ProvenanceError(msg)
        return completed.stdout.strip()

    commit = run("rev-parse", "HEAD")
    dirty = bool(run("status", "--porcelain"))
    return commit, dirty
