"""Where re-fits may be written, and where they may not.

`DESIGN.md` §1 states the rule: ``analyze/`` reads sensorgrams from
``results/raw/``, **never mutates them**, and writes independent fits to
``results/refit/``. Raw data is append-only because a returned measurement is
evidence.

`PROTOCOL.md` §12.4b registers "write to ``results/raw/`` from ``analyze/``" as
a mutant an immutability assertion must kill. The guard is a function every
write goes through rather than a convention, because the failure is silent and
irreversible: a re-fitted K_D written over a returned one leaves no trace that
the number changed after the claim was registered, and the CI append-only gate
would then be checking a file that had already been overwritten locally.

The two directories are not symmetric. ``raw/`` is what the provider sent;
``refit/`` is what we concluded from it. Keeping our conclusions out of their
evidence is what lets both be published side by side and compared.
"""

import dataclasses
from pathlib import Path

#: Returned measurements, exactly as the provider sent them.
RAW_SUBDIR = Path("results") / "raw"

#: Our independent fits. Everything this package writes lands here.
REFIT_SUBDIR = Path("results") / "refit"


class ImmutabilityError(RuntimeError):
    """Raised on any attempt to write into the raw results directory."""


@dataclasses.dataclass(frozen=True, slots=True)
class CampaignPaths:
    """The two result directories of one campaign."""

    root: Path

    @property
    def raw(self) -> Path:
        """Returned measurements. Read-only to this package."""
        return self.root / RAW_SUBDIR

    @property
    def refit(self) -> Path:
        """Independent fits. The only directory this package writes to."""
        return self.root / REFIT_SUBDIR


def guard_write(paths: CampaignPaths, destination: Path) -> Path:
    """Refuse a write that would land in the raw results directory.

    Resolves both sides before comparing, so a path reaching ``raw/`` through
    ``..`` or a symlink is caught as readily as a direct one.
    """
    raw = paths.raw.resolve()
    target = destination.resolve()
    if target == raw or raw in target.parents:
        msg = (
            f"refusing to write {destination} into {paths.raw}. "
            "DESIGN.md section 1: returned measurements are evidence and are "
            "append-only; analyze/ writes independent fits to results/refit/ "
            "and never mutates what the provider sent"
        )
        raise ImmutabilityError(msg)
    return destination


def refit_destination(paths: CampaignPaths, name: str) -> Path:
    """Build a path under ``results/refit/``, checked before it is returned."""
    if Path(name).is_absolute() or ".." in Path(name).parts:
        msg = f"refit name {name!r} must be a plain relative filename"
        raise ImmutabilityError(msg)
    return guard_write(paths, paths.refit / name)
