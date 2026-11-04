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

from counterscreen.geometry.validity import check_geometry
from counterscreen.targets.prepare import read_pdb

_MIN_ARGC = 3


def main(argv: list[str]) -> int:
    """Write one G0 report per structure; exit non-zero if any fails."""
    if len(argv) < _MIN_ARGC:
        print("usage: check_geometry.py <out.json> <structure.pdb>...", file=sys.stderr)
        return 2
    out = Path(argv[1])

    report: dict[str, object] = {}
    failed: list[str] = []
    for path in argv[2:]:
        structure = read_pdb(Path(path))
        result = check_geometry(structure)
        report[Path(path).name] = {
            "passed": result.passed,
            "reasons": list(result.reasons()),
            "chain_breaks": len(result.chain_breaks),
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
