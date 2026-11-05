"""Target preparation: T+, the decoys, and the truncated screening construct.

`SETUP.md` section 2 fixes what is built and `PROTOCOL.md` section 3.1 fixes why
each assertion exists. The one that matters most is the disulfide check: the
HLA alpha-2 domain and beta-2-microglobulin each carry a structural disulfide,
and if stripping the TCR, truncating or re-protonating drops one, every
downstream number is computed on a subtly wrong target and nothing later
notices.

**D1 comes from real 7OW5 coordinates, never from mutating T+.** `SETUP.md`
section 2.2 is explicit, and the reason is that an in-silico mutation would
bias the comparison toward our own repacking rather than toward
crystallographic reality.

A related trap is worth naming, because 7OW3 makes it available. 7OW3 is the
wild-type 10-mer *without* a TCR, which looks like a tidier D1 than
TCR-stripped 7OW5. It is not. T+ comes from a receptor-bound structure, so a
D1 drawn from an apo structure would differ from it in conformational state as
well as in sequence, and the margin would partly measure that rather than the
G12D substitution. Both arms must be prepared identically; 7OW3 is a
cross-reference, not a decoy.
"""

import dataclasses
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from biotite.structure.info import one_letter_code
from biotite.structure.io.pdbx import CIFFile

from counterscreen.core.hashing import file_sha256
from counterscreen.geometry.structure import Structure
from counterscreen.geometry.validity import Disulfide, find_disulfides

#: Distance below which two cysteine SG atoms are treated as bonded.
DISULFIDE_MAX_ANGSTROM = 2.5

#: Minimum disulfides expected in a prepared three-chain pMHC: one in the
#: HLA alpha-2 domain, one in beta-2-microglobulin (`PROTOCOL.md` section 3.1).
MIN_PMHC_DISULFIDES = 2


class PreparationError(ValueError):
    """Raised when a prepared target fails an assertion it must satisfy."""


#: mmCIF values meaning "no alternate conformer at this atom".
NO_ALTERNATE = frozenset({".", "?", ""})

#: The alternate conformer kept when a residue has several: the first label.
#: Deposited files order them A, B, ... and the convention is that A is the
#: one to take when occupancies are equal, which for the files here they are.
PRIMARY_ALTERNATE = "A"


def alternate_conformers(path: Path) -> dict[tuple[str, int, str], tuple[str, ...]]:
    """Alternate conformers in a file, keyed by (chain, residue, residue name).

    Reported rather than assumed away. `FINDINGS.md` F-13 is about what the
    silent handling chose: 7OW5 carries one, 7OW4 five, and one of 7OW4's is
    Gln70 -- a residue amendment A8 names as an M1 target -- modelled in two
    conformations 6.1 A apart at NE2, each at half occupancy.
    """
    atoms = CIFFile.read(path).block["atom_site"]
    keep = atoms["group_PDB"].as_array() == "ATOM"
    alt = atoms["label_alt_id"].as_array()[keep]
    chains = atoms["auth_asym_id"].as_array()[keep]
    numbers = atoms["auth_seq_id"].as_array(int)[keep]
    names = atoms["label_comp_id"].as_array()[keep]
    found: dict[tuple[str, int, str], set[str]] = {}
    for row in range(len(alt)):
        label = str(alt[row])
        if label in NO_ALTERNATE:
            continue
        found.setdefault((str(chains[row]), int(numbers[row]), str(names[row])), set()).add(label)
    return {key: tuple(sorted(labels)) for key, labels in sorted(found.items())}


def read_cif(path: Path) -> Structure:
    """Read an mmCIF file into the atom table the geometry checks consume.

    Three things are decided here rather than left to whichever row came last
    in the file (`FINDINGS.md` F-13):

    * **HETATM is dropped**, so waters, ligands and selenomethionine do not
      enter the geometry checks.
    * **One conformer is kept** where a residue has alternates: the
      :data:`PRIMARY_ALTERNATE` label, which for every file here is the equal
      occupancy half of a 0.5/0.5 pair. Choosing it is a choice, so
      :func:`alternate_conformers` reports what was there.
    * **Insertion codes are refused**, not ignored. Two residues sharing a
      number would have collided into one, and silently keeping some atoms
      from each is worse than not reading the file.
    """
    block = CIFFile.read(path).block
    atoms = block["atom_site"]
    groups = atoms["group_PDB"].as_array()
    alt = atoms["label_alt_id"].as_array()
    keep = (groups == "ATOM") & np.array(
        [str(label) in NO_ALTERNATE or str(label) == PRIMARY_ALTERNATE for label in alt]
    )
    if "pdbx_PDB_ins_code" in atoms:
        codes = atoms["pdbx_PDB_ins_code"].as_array()[keep]
        present = sorted({str(code) for code in codes} - NO_ALTERNATE)
        if present:
            msg = (
                f"{path.name} uses insertion codes {present}, which this reader does "
                "not handle: two residues would share one number and collapse into one"
            )
            raise PreparationError(msg)
    coords = np.stack(
        [atoms[f"Cartn_{axis}"].as_array(float)[keep] for axis in ("x", "y", "z")],
        axis=1,
    )
    return Structure.from_atoms(
        coords,
        atoms["label_atom_id"].as_array()[keep],
        atoms["label_comp_id"].as_array()[keep],
        atoms["auth_seq_id"].as_array(int)[keep],
        atoms["auth_asym_id"].as_array()[keep],
    )


def read_pdb(path: Path) -> Structure:
    """Read a prepared target back from PDB, for the assertions in CI."""
    from biotite.structure.io.pdb import PDBFile  # noqa: PLC0415

    array = PDBFile.read(path).get_structure(model=1)
    return Structure.from_atoms(
        np.asarray(array.coord, dtype=np.float64),
        [str(x) for x in array.atom_name],
        [str(x) for x in array.res_name],
        [int(x) for x in array.res_id],
        [str(x) for x in array.chain_id],
    )


def select_chains(structure: Structure, chains: Sequence[str]) -> Structure:
    """Keep only the named chains, in their original order."""
    wanted = set(chains)
    rows = [i for i, chain in enumerate(structure.chain_ids) if chain in wanted]
    if not rows:
        msg = f"no atoms in chains {sorted(wanted)}; have {sorted(set(structure.chain_ids))}"
        raise PreparationError(msg)
    index = np.array(rows, dtype=int)
    return Structure.from_atoms(
        structure.coords[index],
        [structure.atom_names[i] for i in rows],
        [structure.residue_names[i] for i in rows],
        [structure.residue_numbers[i] for i in rows],
        [structure.chain_ids[i] for i in rows],
    )


def chain_sequence(structure: Structure, chain: str) -> str:
    """One-letter sequence of a chain, in residue-number order."""
    seen: dict[int, str] = {}
    for residue in structure.residues:
        if residue.chain == chain:
            letter = one_letter_code(residue.name)
            seen[residue.number] = letter.upper() if letter else "X"
    return "".join(seen[number] for number in sorted(seen))


@dataclasses.dataclass(frozen=True, slots=True)
class PreparedTarget:
    """One prepared target, with the provenance needed to reproduce it."""

    name: str
    structure: Structure
    source_file: str
    source_sha256: str
    kept_chains: tuple[str, ...]
    peptide_chain: str | None
    peptide_sequence: str
    disulfides: tuple[Disulfide, ...]

    @property
    def chains(self) -> tuple[str, ...]:
        """Chains actually present after preparation."""
        return tuple(sorted(str(c) for c in set(self.structure.chain_ids)))


def prepare(
    path: Path,
    name: str,
    *,
    keep_chains: Sequence[str],
    peptide_chain: str | None,
    expected_peptide: str | None = None,
    excluded_chains: Sequence[str] = (),
) -> PreparedTarget:
    """Build one target from a structure file, asserting everything required.

    ``excluded_chains`` names the TCR chains that must not survive; it is
    checked after selection rather than assumed, because a silent failure here
    leaves TCR atoms in the target and nothing downstream would catch it.
    """
    full = read_cif(path)
    selected = select_chains(full, keep_chains)

    present = set(selected.chain_ids)
    leaked = present & set(excluded_chains)
    if leaked:
        msg = f"{name}: excluded chains survived preparation: {sorted(leaked)}"
        raise PreparationError(msg)
    missing = set(keep_chains) - present
    if missing:
        msg = f"{name}: expected chains absent after preparation: {sorted(missing)}"
        raise PreparationError(msg)

    peptide = chain_sequence(selected, peptide_chain) if peptide_chain else ""
    if expected_peptide is not None and peptide != expected_peptide:
        msg = f"{name}: peptide is {peptide!r}, expected {expected_peptide!r}"
        raise PreparationError(msg)

    disulfides = find_disulfides(selected, DISULFIDE_MAX_ANGSTROM)
    if len(disulfides) < MIN_PMHC_DISULFIDES:
        msg = (
            f"{name}: found {len(disulfides)} disulfide(s), expected at least "
            f"{MIN_PMHC_DISULFIDES}. PROTOCOL.md section 3.1: if preparation drops them, "
            "every downstream number is computed on a subtly wrong target"
        )
        raise PreparationError(msg)

    return PreparedTarget(
        name=name,
        structure=selected,
        source_file=path.name,
        source_sha256=file_sha256(path),
        kept_chains=tuple(keep_chains),
        peptide_chain=peptide_chain,
        peptide_sequence=peptide,
        disulfides=disulfides,
    )


def truncate(structure: Structure, chain: str, first: int, last: int) -> Structure:
    """Keep a residue range of one chain, and every other chain whole.

    Used for the alpha-1/alpha-2 platform construct of `SETUP.md` section 2.5.
    """
    if first >= last:
        msg = f"truncation range must ascend, got {first}-{last}"
        raise PreparationError(msg)
    rows = [
        i
        for i, (c, number) in enumerate(
            zip(structure.chain_ids, structure.residue_numbers, strict=True)
        )
        if c != chain or first <= number <= last
    ]
    index = np.array(rows, dtype=int)
    return Structure.from_atoms(
        structure.coords[index],
        [structure.atom_names[i] for i in rows],
        [structure.residue_names[i] for i in rows],
        [structure.residue_numbers[i] for i in rows],
        [structure.chain_ids[i] for i in rows],
    )


def backbone_rmsd(left: Structure, right: Structure, chain: str) -> float:
    """CA RMSD over residues a pair of structures share in one chain.

    `SETUP.md` section 2.5 requires verifying that truncation leaves the
    peptide and groove geometry unchanged. No superposition is applied: both
    come from the same coordinate frame, so a non-zero value means atoms
    moved, not that the structures are differently oriented.
    """

    def alpha_carbons(structure: Structure) -> dict[int, np.ndarray]:
        return {
            residue.number: structure.xyz(residue, "CA")
            for residue in structure.residues
            if residue.chain == chain and residue.has("CA")
        }

    a, b = alpha_carbons(left), alpha_carbons(right)
    shared = sorted(set(a) & set(b))
    if not shared:
        msg = f"no shared CA atoms in chain {chain!r}"
        raise PreparationError(msg)
    deltas = np.array([a[n] - b[n] for n in shared])
    return float(np.sqrt((deltas**2).sum(axis=1).mean()))


def write_pdb(structure: Structure, path: Path) -> None:
    """Write a prepared target to PDB.

    PDB rather than mmCIF because these files are committed: they are the
    prepared targets `.gitignore` deliberately tracks, and a compact,
    diffable text format keeps that honest.
    """
    from biotite.structure import AtomArray  # noqa: PLC0415
    from biotite.structure.io.pdb import PDBFile  # noqa: PLC0415

    # biotite ships no stubs, so AtomArray is Any here; the annotation keeps
    # mypy strict quiet without widening anything that leaves this function.
    array: Any = AtomArray(len(structure.atom_names))
    array.coord = structure.coords
    array.atom_name = list(structure.atom_names)
    array.res_name = list(structure.residue_names)
    array.res_id = list(structure.residue_numbers)
    array.chain_id = list(structure.chain_ids)
    array.element = [name[0] for name in structure.atom_names]
    array.hetero = [False] * len(structure.atom_names)

    output = PDBFile()
    output.set_structure(array)
    path.parent.mkdir(parents=True, exist_ok=True)
    output.write(path)
