"""Run gate G0 over prepared structures and write the verdicts.

`DESIGN.md` §8b puts this before any GPU spend. Applied to prepared targets
it is a sanity check on preparation: a target that fails G0 means stripping or
truncation damaged it, and every downstream number would be computed on a
broken structure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from counterscreen.geometry.validity import check_geometry
from counterscreen.targets.prepare import read_cif, read_pdb

if TYPE_CHECKING:
    from counterscreen.geometry.structure import Structure

_MIN_ARGC = 3

#: Readers by file extension. Handing a `.cif` to the PDB reader produced an
#: opaque float-parsing error from inside `biotite`, which on Day 1 is time
#: spent on the wrong question (`BUILD_JOURNAL.md` ISSUE-025).
_READERS = {".pdb": read_pdb, ".cif": read_cif, ".mmcif": read_cif}


def read_structure(path: Path) -> Structure:
    """Read a structure by extension, naming what is accepted when it is not."""
    reader = _READERS.get(path.suffix.lower())
    if reader is None:
        msg = f"{path.name}: expected one of {sorted(_READERS)}, got {path.suffix!r}"
        raise SystemExit(msg)
    return reader(path)


def main(argv: list[str]) -> int:
    """Write one G0 report per structure; exit non-zero if any fails."""
    if len(argv) < _MIN_ARGC:
        print(
            "usage: check_geometry.py <out.json> <structure.pdb|.cif>...",
            file=sys.stderr,
        )
        return 2
    out = Path(argv[1])

    report: dict[str, object] = {}
    failed: list[str] = []
    for path in argv[2:]:
        structure = read_structure(Path(path))
        result = check_geometry(structure)
        report[Path(path).name] = {
            "passed": result.passed,
            "reasons": list(result.reasons()),
            "chain_breaks": len(result.chain_breaks),
            "chain_gaps": len(result.chain_gaps),
            "clashes": len(result.clashes),
            "ramachandran_outliers": len(result.ramachandran_outliers),
            "ramachandran_evaluated": result.ramachandran_evaluated,
            "non_l_residues": len(result.non_l_residues),
            "cis_peptides": len(result.cis_peptides),
            "disulfides": len(result.disulfides),
        }
        verdict = "pass" if result.passed else "FAIL"
        print(f"{Path(path).name}: {verdict} {'; '.join(result.reasons())}")
        if not result.passed:
            failed.append(Path(path).name)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if failed:
        print(f"G0 failed for: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
