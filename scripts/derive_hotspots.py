"""Derive the three mechanism hotspot schemes from the prepared targets.

Operator entry point for `PROTOCOL.md` §9 stage 1. The schemes are computed
from the structures rather than written down; see
:mod:`counterscreen.generate.hotspots` for the rules and the measurements
behind them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from counterscreen.generate.hotspots import m1_scheme, m2_scheme, m3_scheme
from counterscreen.targets.prepare import read_pdb

PEPTIDE_CHAIN = "C"
MUTANT_POSITION = 6
_EXPECTED_ARGC = 4


def main(argv: list[str]) -> int:
    """Write the three schemes, with their rules and rationales, as JSON."""
    if len(argv) != _EXPECTED_ARGC:
        print("usage: derive_hotspots.py <target.pdb> <decoy.pdb> <out.json>", file=sys.stderr)
        return 2
    target = read_pdb(Path(argv[1]))
    decoy = read_pdb(Path(argv[2]))

    schemes = [
        m1_scheme(target, PEPTIDE_CHAIN, MUTANT_POSITION),
        m2_scheme(target, PEPTIDE_CHAIN, MUTANT_POSITION),
        m3_scheme(target, decoy, PEPTIDE_CHAIN),
    ]
    document = {
        str(scheme.arm): {
            "contig": scheme.as_contig(),
            "rule": scheme.rule,
            "hotspots": [
                {
                    "label": h.label(),
                    "residue": h.name,
                    "rationale": h.rationale,
                }
                for h in scheme.hotspots
            ],
        }
        for scheme in schemes
    }

    out = Path(argv[3])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for scheme in schemes:
        print(f"{scheme.arm}: {scheme.as_contig()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
