"""Hotspot schemes for the three mechanism arms, derived not declared.

`PROTOCOL.md` §9 stage 1 runs RFdiffusion with "three hotspot schemes for
M1/M2/M3". A hotspot conditions generation on a target residue, so the scheme
*is* the mechanism: it is where the arm's hypothesis becomes a backbone.

Each scheme here is a **derivation rule computed from the prepared targets**,
not a list of residue numbers typed from a figure. That follows the same
discipline `PREREGISTRATION.md` §3 applies to G2 and G3, and it matters more
than usual here: amendments A7 and A8 exist because the original M1 definition
named residues that turned out not to be reachable, and a hard-coded list
would have hidden that rather than surfaced it.

The rules, and the measurements behind them:

**M1** — the aspartate itself. Restricted to carboxylate oxygens with non-zero
SASA, plus the HLA residues hydrogen-bonding the aspartate *other than*
Arg114, which is bidentate and not displaceable (`FINDINGS.md` F-5).

**M2** — the composite surface. The HLA residues forming the Asp6 environment,
selected by proximity to its side chain, which is the Asp6-Arg114-Gln70
network §4 names plus whatever else is actually in range.

**M3** — the conformational readout. Peptide positions whose CA moves between
the mutant and wild-type complexes by more than a stated threshold *and* that
are solvent-accessible enough for a binder to read. This needs **both**
structures, which no other arm does, and that is the point: M3's signal is a
difference, not a feature.
"""

import dataclasses

from counterscreen.core.design import Arm
from counterscreen.geometry.align import displacement, superpose_on
from counterscreen.geometry.structure import Structure
from counterscreen.geometry.surface import atom_sasa_for, residue_sasa

#: An atom counts as reachable when a probe can touch it at all.
MIN_REACHABLE_SASA = 1.0

#: HLA residues within this distance of the aspartate side chain form the
#: composite surface of M2.
COMPOSITE_RADIUS_ANGSTROM = 5.0

#: Hydrogen-bond distance for identifying the aspartate's coordinating partners.
HBOND_ANGSTROM = 3.6

#: M3 reads positions that move. F-6 measured 0.96 A at position 6 and 0.78,
#: 0.51 and 0.64 at 7-9, against 0.26 or less for positions 1-5, so a
#: threshold here separates the responding half of the peptide from the static
#: half with room on either side.
MIN_DISPLACEMENT_ANGSTROM = 0.4

#: And that a binder could actually reach.
MIN_HOTSPOT_SASA = 10.0


class HotspotError(ValueError):
    """Raised when a hotspot scheme cannot be derived from the targets."""


@dataclasses.dataclass(frozen=True, slots=True)
class Hotspot:
    """One target residue to condition generation on, and why."""

    chain: str
    residue: int
    name: str
    rationale: str

    def label(self) -> str:
        """RFdiffusion-style residue label, e.g. ``A114``."""
        return f"{self.chain}{self.residue}"


@dataclasses.dataclass(frozen=True, slots=True)
class HotspotScheme:
    """One arm's hotspots, with the rule that produced them."""

    arm: Arm
    rule: str
    hotspots: tuple[Hotspot, ...]

    def __post_init__(self) -> None:
        """Refuse an empty scheme rather than generate against nothing."""
        if not self.hotspots:
            msg = (
                f"{self.arm} produced no hotspots. Generating unconditioned backbones "
                "would silently abandon the mechanism this arm exists to test"
            )
            raise HotspotError(msg)

    def labels(self) -> tuple[str, ...]:
        """Residue labels, sorted, as RFdiffusion expects them."""
        return tuple(sorted({h.label() for h in self.hotspots}))

    def as_contig(self) -> str:
        """Hotspot specification string, e.g. ``[A70,C6]``."""
        return "[" + ",".join(self.labels()) + "]"


def _peptide_residue(structure: Structure, chain: str, number: int) -> object:
    for residue in structure.residues:
        if residue.chain == chain and residue.number == number:
            return residue
    msg = f"no residue {chain}{number} in the target"
    raise HotspotError(msg)


def m1_scheme(
    target: Structure, peptide_chain: str, mutant_position: int, hla_chain: str = "A"
) -> HotspotScheme:
    """Derive M1: the reachable face of the aspartate, and its weaker partner."""
    import numpy as np  # noqa: PLC0415

    aspartate = _peptide_residue(target, peptide_chain, mutant_position)
    exposure = atom_sasa_for(target, aspartate)  # type: ignore[arg-type]
    reachable = {
        atom: area
        for atom, area in exposure.items()
        if atom.startswith("OD") and area >= MIN_REACHABLE_SASA
    }
    if not reachable:
        msg = (
            f"no carboxylate oxygen of {peptide_chain}{mutant_position} is reachable; "
            "M1 has no handle at all and the arm should be retired, not generated against"
        )
        raise HotspotError(msg)

    hotspots = [
        Hotspot(
            chain=peptide_chain,
            residue=mutant_position,
            name=str(aspartate.name),  # type: ignore[attr-defined]
            rationale=(
                "reachable carboxylate oxygens: "
                + ", ".join(f"{a} {v:.1f} A^2" for a, v in sorted(reachable.items()))
            ),
        )
    ]

    oxygens = [target.xyz(aspartate, a) for a in reachable]  # type: ignore[arg-type]
    for residue in target.residues:
        if residue.chain != hla_chain:
            continue
        for atom in residue.atoms:
            if atom[:1] not in {"N", "O"}:
                continue
            gap = min(float(np.linalg.norm(target.xyz(residue, atom) - o)) for o in oxygens)
            if gap <= HBOND_ANGSTROM and residue.name.upper() != "ARG":
                hotspots.append(
                    Hotspot(
                        chain=hla_chain,
                        residue=residue.number,
                        name=residue.name,
                        rationale=f"coordinates the aspartate at {gap:.2f} A and is displaceable",
                    )
                )
                break

    return HotspotScheme(
        arm=Arm.M1,
        rule=(
            "carboxylate oxygens with SASA >= "
            f"{MIN_REACHABLE_SASA} A^2, plus non-arginine HLA partners within "
            f"{HBOND_ANGSTROM} A. Arg114 excluded: bidentate and not displaceable (F-5)"
        ),
        hotspots=tuple(hotspots),
    )


def m2_scheme(
    target: Structure, peptide_chain: str, mutant_position: int, hla_chain: str = "A"
) -> HotspotScheme:
    """Derive M2: the HLA surface surrounding the aspartate."""
    import numpy as np  # noqa: PLC0415

    aspartate = _peptide_residue(target, peptide_chain, mutant_position)
    side_chain = [
        target.xyz(aspartate, a)  # type: ignore[arg-type]
        for a in aspartate.atoms  # type: ignore[attr-defined]
        if a not in {"N", "CA", "C", "O"}
    ]
    hotspots = []
    for residue in target.residues:
        if residue.chain != hla_chain:
            continue
        gap = min(
            float(np.linalg.norm(target.xyz(residue, atom) - point))
            for atom in residue.atoms
            for point in side_chain
        )
        if gap <= COMPOSITE_RADIUS_ANGSTROM:
            hotspots.append(
                Hotspot(
                    chain=hla_chain,
                    residue=residue.number,
                    name=residue.name,
                    rationale=f"{gap:.2f} A from the aspartate side chain",
                )
            )
    return HotspotScheme(
        arm=Arm.M2,
        rule=(
            f"HLA residues within {COMPOSITE_RADIUS_ANGSTROM} A of the aspartate side "
            "chain: the composite surface the substitution alters"
        ),
        hotspots=tuple(hotspots),
    )


def m3_scheme(
    mutant: Structure,
    wild_type: Structure,
    peptide_chain: str,
    hla_chain: str = "A",
    platform_last: int = 180,
) -> HotspotScheme:
    """Derive M3: the peptide positions that move, and that can be reached.

    The only scheme needing both complexes, because M3's signal is the
    difference between them rather than a feature of either.
    """
    alignment = superpose_on(wild_type, mutant, hla_chain, 1, platform_last)
    shifts = displacement(wild_type, mutant, peptide_chain, alignment)
    exposure = residue_sasa(mutant)

    hotspots = [
        Hotspot(
            chain=peptide_chain,
            residue=number,
            name=next(
                r.name for r in mutant.residues if r.chain == peptide_chain and r.number == number
            ),
            rationale=(
                f"CA moves {shift:.2f} A between mutant and wild type, "
                f"SASA {exposure.get((peptide_chain, number), 0.0):.1f} A^2"
            ),
        )
        for number, shift in sorted(shifts.items())
        if shift >= MIN_DISPLACEMENT_ANGSTROM
        and exposure.get((peptide_chain, number), 0.0) >= MIN_HOTSPOT_SASA
    ]
    return HotspotScheme(
        arm=Arm.M3,
        rule=(
            f"peptide positions whose CA displaces >= {MIN_DISPLACEMENT_ANGSTROM} A "
            f"between the two complexes and whose SASA >= {MIN_HOTSPOT_SASA} A^2, "
            f"after superposing on {hla_chain} 1-{platform_last} "
            f"(fit RMSD {alignment.rmsd:.3f} A over {alignment.paired} CA)"
        ),
        hotspots=tuple(hotspots),
    )
