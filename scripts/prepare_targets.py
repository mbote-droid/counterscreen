"""Build T+, D1, D2 and the truncated construct from the deposited structures.

Operator script for `SETUP.md` section 2. Run once per source refresh; the
outputs are committed, so the assertions in
:mod:`counterscreen.targets.prepare` run again in CI against what was written.
"""

from __future__ import annotations

import sys
from pathlib import Path

from counterscreen.targets.prepare import (
    backbone_rmsd,
    prepare,
    select_chains,
    truncate,
    write_pdb,
)

TCR_CHAINS = ("D", "E")
PMHC_CHAINS = ("A", "B", "C")

# SETUP.md section 2.5: alpha-1/alpha-2 platform, roughly 180 residues.
PLATFORM_FIRST, PLATFORM_LAST = 1, 180

_EXPECTED_ARGC = 3


def main(argv: list[str]) -> int:
    """Prepare every target from a directory of source mmCIF files."""
    if len(argv) != _EXPECTED_ARGC:
        print("usage: prepare_targets.py <source-dir> <out-dir>", file=sys.stderr)
        return 2
    source, out = Path(argv[1]), Path(argv[2])

    plan = [
        ("T_plus", "7OW6", PMHC_CHAINS, "C", "VVVGADGVGK"),
        ("D1_wild_type", "7OW5", PMHC_CHAINS, "C", "VVVGAGGVGK"),
        ("D2_peptide_free", "7OW6", ("A", "B"), None, None),
    ]

    for name, code, chains, peptide_chain, peptide in plan:
        matches = sorted(source.glob(f"*{code}*.cif"))
        if not matches:
            print(f"missing source for {code} in {source}", file=sys.stderr)
            return 1
        target = prepare(
            matches[0],
            name,
            keep_chains=chains,
            peptide_chain=peptide_chain,
            expected_peptide=peptide,
            excluded_chains=TCR_CHAINS,
        )
        write_pdb(target.structure, out / f"{name}.pdb")
        print(
            f"{name}: {code} chains={target.chains} peptide={target.peptide_sequence or '-'} "
            f"disulfides={len(target.disulfides)} sha256={target.source_sha256[:12]}"
        )

        if peptide_chain is not None:
            # SETUP.md section 2.5: alpha-1/alpha-2 platform plus peptide.
            # beta-2m and the alpha-3 domain are both dropped -- they are
            # structurally remote from the epitope and identical across every
            # target, so they contribute nothing to discrimination while
            # costing most of the compute.
            groove = select_chains(target.structure, ["A", peptide_chain])
            platform = truncate(groove, "A", PLATFORM_FIRST, PLATFORM_LAST)
            write_pdb(platform, out / f"{name}_platform.pdb")
            shifted = backbone_rmsd(platform, target.structure, peptide_chain)
            print(
                f"  platform: {len(platform.residues)} residues, "
                f"peptide CA RMSD vs full complex {shifted:.3f} A"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
