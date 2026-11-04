"""Gate G0: whether a structure is physically possible at all.

`PROTOCOL.md` section 8 puts G0 first and gives the reason: generative backbones
do emit non-physical geometry, and confidence scores miss it entirely. It
costs seconds where co-folding costs minutes to hours, so a structure that
fails here must never reach a GPU. `DESIGN.md` section 8b states the same rule
as an engineering constraint: a geometrically invalid structure is not a cheap
mistake to fold, it is a wasted GPU-hour and a number in the results that
means nothing.

`PREREGISTRATION.md` section 3 registers G0 as a fixed rule: a chain break
beyond 4.5 A between consecutive Ca, Ramachandran outliers at or above 1%, or
any clash, non-L chirality or non-proline cis-peptide.

**One honest limitation, stated here rather than discovered later.** The
Ramachandran criterion below is a coarse region test, not a reference contour.
Real outlier classification uses smoothed density contours derived from a
curated structure set, which this environment cannot reach. The dihedral
arithmetic is exact and tested; the region boundaries are a documented
approximation that will over-report in the tails. `build_rules.pdf` section
2.7 is clear on what is owed here: when a library does something critical,
either use it plainly or re-implement it and test against it, never leave it
an unexamined black box. The differential test against a reference
implementation is owed once real structures are available, and until it is run
this criterion should be treated as provisional.
"""

import dataclasses
import itertools

import numpy as np

from counterscreen.core.config import GateConfig
from counterscreen.geometry.dihedral import bond_angles, dihedral_angles, distances
from counterscreen.geometry.structure import Residue, Structure

# Ideal peptide geometry (Engh & Huber). Used only to measure deviation.
IDEAL_N_CA_ANGSTROM = 1.458
IDEAL_CA_C_ANGSTROM = 1.525
IDEAL_C_N_ANGSTROM = 1.329
IDEAL_N_CA_C_DEGREES = 111.2
IDEAL_CA_C_N_DEGREES = 116.2
IDEAL_C_N_CA_DEGREES = 121.7

#: Coarse allowed (phi, psi) boxes for a general residue, in degrees.
#: Provisional; see the module docstring.
#:
#: Two properties are load-bearing and were both absent in the first version,
#: which flagged three experimentally determined residues as outliers for
#: reasons that were artefacts of how the boxes were drawn
#: (`FINDINGS.md` F-9):
#:
#: 1. **Adjacent basins must touch.** The right-handed alpha and beta boxes
#:    previously ended at psi = 50 and began at psi = 60, leaving a ten-degree
#:    band in which a residue was an outlier only because it sat between two
#:    rectangles. They now meet.
#: 2. **Phi and psi are periodic.** The beta basin runs to phi = -180 and
#:    continues past the wrap, so boxes covering phi near +180 are included.
#:    Without them a residue at phi = 178 was treated as far from a basin whose
#:    edge is two degrees away.
GENERAL_REGIONS: "Regions" = (
    (-180.0, -20.0, 60.0, 180.0),  # beta sheet and polyproline II
    (-180.0, -20.0, -180.0, -150.0),  # beta, psi past the wrap
    (150.0, 180.0, 60.0, 180.0),  # beta, phi past the wrap
    (150.0, 180.0, -180.0, -150.0),  # beta, both past the wrap
    (-160.0, -20.0, -120.0, 60.0),  # right-handed alpha, meeting beta at 60
    (20.0, 100.0, -20.0, 90.0),  # left-handed alpha
)

#: Proline's ring restricts phi; psi is then judged by the general regions.
PROLINE_PHI_RANGE = (-110.0, -40.0)

#: Residues with no side chain beyond CB cannot be chirality-checked.
ACHIRAL_RESIDUES = frozenset({"GLY"})


@dataclasses.dataclass(frozen=True, slots=True)
class ChainBreak:
    """Consecutive Ca atoms too far apart to be bonded."""

    chain: str
    after_residue: int
    distance_angstrom: float


@dataclasses.dataclass(frozen=True, slots=True)
class Clash:
    """Two heavy atoms closer than physically possible."""

    first_atom: int
    second_atom: int
    distance_angstrom: float


@dataclasses.dataclass(frozen=True, slots=True)
class BondOutlier:
    """A bond length or angle outside tolerance of ideal peptide geometry."""

    residue_index: int
    measurement: str
    observed: float
    ideal: float


@dataclasses.dataclass(frozen=True, slots=True)
class CisPeptide:
    """A cis peptide bond, which is an error unless the next residue is proline."""

    residue_index: int
    omega_degrees: float
    next_residue: str


@dataclasses.dataclass(frozen=True, slots=True)
class Disulfide:
    """Two cysteine SG atoms within bonding distance."""

    first_residue: int
    second_residue: int
    distance_angstrom: float


@dataclasses.dataclass(frozen=True, slots=True)
class GeometryReport:
    """Everything G0 measured, and the verdict that follows from it."""

    chain_breaks: tuple[ChainBreak, ...]
    clashes: tuple[Clash, ...]
    ramachandran_outliers: tuple[int, ...]
    ramachandran_evaluated: int
    bond_outliers: tuple[BondOutlier, ...]
    non_l_residues: tuple[int, ...]
    cis_peptides: tuple[CisPeptide, ...]
    disulfides: tuple[Disulfide, ...]
    max_outlier_fraction: float

    @property
    def ramachandran_outlier_fraction(self) -> float:
        """Fraction of evaluable residues classified as outliers."""
        if self.ramachandran_evaluated == 0:
            return 0.0
        return len(self.ramachandran_outliers) / self.ramachandran_evaluated

    @property
    def passed(self) -> bool:
        """The G0 verdict, exactly as PREREGISTRATION section 3 registers it."""
        return not (
            self.chain_breaks
            or self.clashes
            or self.bond_outliers
            or self.non_l_residues
            or self.cis_peptides
            or self.ramachandran_outlier_fraction >= self.max_outlier_fraction
        )

    def reasons(self) -> tuple[str, ...]:
        """Why G0 failed, as short diagnostic strings.

        A design's failing gate is a reportable quantity (`PROTOCOL.md` section
        5.4), so the reason travels with the verdict rather than being
        recomputed later.
        """
        found: list[str] = []
        if self.chain_breaks:
            worst = max(self.chain_breaks, key=lambda b: b.distance_angstrom)
            found.append(
                f"{len(self.chain_breaks)} chain break(s), worst "
                f"{worst.distance_angstrom:.2f} A after residue {worst.after_residue}"
            )
        if self.clashes:
            worst_clash = min(self.clashes, key=lambda c: c.distance_angstrom)
            found.append(
                f"{len(self.clashes)} clash(es), closest {worst_clash.distance_angstrom:.2f} A"
            )
        if self.ramachandran_outlier_fraction >= self.max_outlier_fraction:
            found.append(
                f"Ramachandran outliers {self.ramachandran_outlier_fraction:.1%} "
                f"at or above {self.max_outlier_fraction:.1%}"
            )
        if self.bond_outliers:
            found.append(f"{len(self.bond_outliers)} bond geometry outlier(s)")
        if self.non_l_residues:
            found.append(f"{len(self.non_l_residues)} non-L residue(s)")
        if self.cis_peptides:
            found.append(f"{len(self.cis_peptides)} non-proline cis-peptide(s)")
        return tuple(found)


Regions = tuple[tuple[float, float, float, float], ...]


def _wrap(angle: float) -> float:
    """Fold an angle into [-180, 180), so the two ends of the range meet."""
    return (angle + 180.0) % 360.0 - 180.0


def _in_region(phi: float, psi: float, regions: Regions) -> bool:
    phi, psi = _wrap(phi), _wrap(psi)
    return any(
        lo_phi <= phi <= hi_phi and lo_psi <= psi <= hi_psi
        for lo_phi, hi_phi, lo_psi, hi_psi in regions
    )


def _mirrored(regions: Regions) -> Regions:
    return tuple((-hi_p, -lo_p, -hi_s, -lo_s) for lo_p, hi_p, lo_s, hi_s in regions)


def is_ramachandran_outlier(residue_name: str, phi: float, psi: float) -> bool:
    """Whether a (phi, psi) pair falls outside the allowed regions.

    Provisional; see the module docstring. Glycine has no side chain and so
    additionally occupies the mirror image of the general regions.
    """
    name = residue_name.upper()
    if name == "GLY":
        return not (
            _in_region(phi, psi, GENERAL_REGIONS)
            or _in_region(phi, psi, _mirrored(GENERAL_REGIONS))
        )
    if name == "PRO":
        low, high = PROLINE_PHI_RANGE
        return not (low <= phi <= high and _in_region(phi, psi, GENERAL_REGIONS))
    return not _in_region(phi, psi, GENERAL_REGIONS)


def chirality_improper(structure: Structure, residue: Residue) -> float:
    """Improper dihedral N-CA-C-CB, which separates L from D residues.

    The sign is what matters, not the value: reflecting a structure negates
    every dihedral, so the mirror image of an L residue reports the opposite
    sign. A test asserts exactly that, which pins the convention by
    construction rather than by recollection.
    """
    return float(
        dihedral_angles(
            structure.xyz(residue, "N"),
            structure.xyz(residue, "CA"),
            structure.xyz(residue, "C"),
            structure.xyz(residue, "CB"),
        )[0]
    )


#: Sign of the N-CA-C-CB improper dihedral for an L-amino acid.
#:
#: Negative, matching the value of about -122 degrees that structure
#: validation conventionally reports for L residues. The *relative* claim is
#: proven: a test builds an ideal residue, reflects it, and asserts every
#: improper is negated and that a structure and its mirror cannot both pass.
#: The *absolute* claim -- that negative means L rather than D -- rests on
#: that convention and has not yet been checked against an experimental
#: structure. Confirming it against 7OW6, whose residues are L by
#: construction, is owed as soon as real coordinates are available, and is
#: exactly the differential test `build_rules.pdf` section 2.7 asks for.
L_CHIRALITY_SIGN = -1.0


def find_disulfides(structure: Structure, max_distance: float) -> tuple[Disulfide, ...]:
    """Find cysteine pairs whose SG atoms are within bonding distance.

    `PROTOCOL.md` section 3.1 requires asserting that the HLA alpha-2 and
    beta-2-microglobulin disulfides survive target preparation: if stripping
    the TCR, truncating or re-protonating drops them, every downstream number
    is computed on a subtly wrong target.
    """
    cysteines = [
        (index, residue)
        for index, residue in enumerate(structure.residues)
        if residue.name.upper() == "CYS" and residue.has("SG")
    ]
    found: list[Disulfide] = []
    for (i, left), (j, right) in itertools.combinations(cysteines, 2):
        separation = float(distances(structure.xyz(left, "SG"), structure.xyz(right, "SG"))[0])
        if separation <= max_distance:
            found.append(Disulfide(first_residue=i, second_residue=j, distance_angstrom=separation))
    return tuple(found)


def _chain_breaks(structure: Structure, limit: float) -> tuple[ChainBreak, ...]:
    found: list[ChainBreak] = []
    for chain, residues in structure.chains().items():
        usable = [r for r in residues if r.has("CA")]
        for left, right in itertools.pairwise(usable):
            gap = float(distances(structure.xyz(left, "CA"), structure.xyz(right, "CA"))[0])
            if gap > limit:
                found.append(
                    ChainBreak(chain=chain, after_residue=left.number, distance_angstrom=gap)
                )
    return tuple(found)


def _clashes(structure: Structure, limit: float) -> tuple[Clash, ...]:
    rows = structure.heavy_atom_rows()
    if rows.size == 0:
        return ()
    coords = structure.coords[rows]
    separation = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    residue_of = np.array([structure.residue_numbers[row] for row in rows])
    chain_of = np.array([structure.chain_ids[row] for row in rows])

    close = np.argwhere(separation < limit)
    found: list[Clash] = []
    for first, second in close:
        if first >= second:
            continue
        same_chain = chain_of[first] == chain_of[second]
        adjacent = abs(int(residue_of[first]) - int(residue_of[second])) <= 1
        if same_chain and adjacent:
            continue  # bonded or one-three neighbours, not a clash
        found.append(
            Clash(
                first_atom=int(rows[first]),
                second_atom=int(rows[second]),
                distance_angstrom=float(separation[first, second]),
            )
        )
    return tuple(found)


def _bond_outliers(
    structure: Structure, length_tolerance: float, angle_tolerance: float
) -> tuple[BondOutlier, ...]:
    found: list[BondOutlier] = []

    def check(index: int, label: str, observed: float, ideal: float, tolerance: float) -> None:
        if abs(observed - ideal) > tolerance:
            found.append(
                BondOutlier(residue_index=index, measurement=label, observed=observed, ideal=ideal)
            )

    lookup = {id(residue): index for index, residue in enumerate(structure.residues)}
    for residues in structure.chains().values():
        for residue in residues:
            if not residue.has(*("N", "CA", "C")):
                continue
            index = lookup[id(residue)]
            n, ca, c = (structure.xyz(residue, atom) for atom in ("N", "CA", "C"))
            check(index, "N-CA", float(distances(n, ca)[0]), IDEAL_N_CA_ANGSTROM, length_tolerance)
            check(index, "CA-C", float(distances(ca, c)[0]), IDEAL_CA_C_ANGSTROM, length_tolerance)
            check(
                index,
                "N-CA-C",
                float(bond_angles(n, ca, c)[0]),
                IDEAL_N_CA_C_DEGREES,
                angle_tolerance,
            )
        for left, right in itertools.pairwise(residues):
            if not (left.has("CA", "C") and right.has("N", "CA")):
                continue
            index = lookup[id(left)]
            ca_l, c_l = structure.xyz(left, "CA"), structure.xyz(left, "C")
            n_r, ca_r = structure.xyz(right, "N"), structure.xyz(right, "CA")
            peptide = float(distances(c_l, n_r)[0])
            if peptide > IDEAL_C_N_ANGSTROM + length_tolerance * 4:
                continue  # a chain break, already reported as one
            check(index, "C-N", peptide, IDEAL_C_N_ANGSTROM, length_tolerance)
            check(
                index,
                "CA-C-N",
                float(bond_angles(ca_l, c_l, n_r)[0]),
                IDEAL_CA_C_N_DEGREES,
                angle_tolerance,
            )
            check(
                index,
                "C-N-CA",
                float(bond_angles(c_l, n_r, ca_r)[0]),
                IDEAL_C_N_CA_DEGREES,
                angle_tolerance,
            )
    return tuple(found)


def check_geometry(structure: Structure, gates: GateConfig | None = None) -> GeometryReport:
    """Run every G0 check and return the measurements and the verdict."""
    config = gates or GateConfig()
    lookup = {id(residue): index for index, residue in enumerate(structure.residues)}

    outliers: list[int] = []
    evaluated = 0
    non_l: list[int] = []
    cis: list[CisPeptide] = []

    for residues in structure.chains().values():
        for position, residue in enumerate(residues):
            index = lookup[id(residue)]
            if residue.name.upper() not in ACHIRAL_RESIDUES and residue.has("N", "CA", "C", "CB"):
                improper = chirality_improper(structure, residue)
                if np.sign(improper) != L_CHIRALITY_SIGN:
                    non_l.append(index)

            previous = residues[position - 1] if position > 0 else None
            following = residues[position + 1] if position + 1 < len(residues) else None
            if (
                previous is not None
                and following is not None
                and previous.has("C")
                and residue.has("N", "CA", "C")
                and following.has("N")
            ):
                phi = float(
                    dihedral_angles(
                        structure.xyz(previous, "C"),
                        structure.xyz(residue, "N"),
                        structure.xyz(residue, "CA"),
                        structure.xyz(residue, "C"),
                    )[0]
                )
                psi = float(
                    dihedral_angles(
                        structure.xyz(residue, "N"),
                        structure.xyz(residue, "CA"),
                        structure.xyz(residue, "C"),
                        structure.xyz(following, "N"),
                    )[0]
                )
                evaluated += 1
                if is_ramachandran_outlier(residue.name, phi, psi):
                    outliers.append(index)

            if following is not None and residue.has("CA", "C") and following.has("N", "CA"):
                omega = float(
                    dihedral_angles(
                        structure.xyz(residue, "CA"),
                        structure.xyz(residue, "C"),
                        structure.xyz(following, "N"),
                        structure.xyz(following, "CA"),
                    )[0]
                )
                is_cis = abs(omega) < config.g0_cis_peptide_tolerance_degrees
                if is_cis and following.name.upper() != "PRO":
                    cis.append(
                        CisPeptide(
                            residue_index=index,
                            omega_degrees=omega,
                            next_residue=following.name,
                        )
                    )

    return GeometryReport(
        chain_breaks=_chain_breaks(structure, config.g0_chain_break_angstrom),
        clashes=_clashes(structure, config.g0_clash_distance_angstrom),
        ramachandran_outliers=tuple(outliers),
        ramachandran_evaluated=evaluated,
        bond_outliers=_bond_outliers(
            structure,
            config.g0_bond_length_tolerance_angstrom,
            config.g0_bond_angle_tolerance_degrees,
        ),
        non_l_residues=tuple(non_l),
        cis_peptides=tuple(cis),
        disulfides=find_disulfides(structure, config.g0_disulfide_max_angstrom),
        max_outlier_fraction=config.g0_max_ramachandran_outlier_fraction,
    )
