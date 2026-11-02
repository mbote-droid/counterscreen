"""A minimal atom table, and the per-residue view the G0 checks need.

Deliberately not a general structure library. It holds exactly what geometric
validation reads -- coordinates, atom names, residue identity and chain -- so
that a test can build a structure with a known chain break or a known clash in
a few lines, which is what `DESIGN.md` section 8 requires of the geometry
tests. Parsing real PDB and mmCIF files belongs in ``targets/``; this type is
what that package will hand over.

If ``targets/`` or ``score/`` turn out to need the same representation, it
moves to ``core/``. It stays here until a second caller actually exists, per
the over-engineering test in `build_rules.pdf` section 2.11.
"""

import dataclasses
from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

#: Backbone atoms every amino acid carries.
BACKBONE_ATOMS = ("N", "CA", "C")

_COORD_NDIM = 2
_COORD_COLUMNS = 3


#: Atoms that are not hydrogens, by the convention that hydrogen names begin
#: with H or a digit followed by H.
def is_heavy_atom(name: str) -> bool:
    """Whether an atom name denotes a heavy (non-hydrogen) atom."""
    stripped = name.strip()
    if not stripped:
        return False
    if stripped[0] == "H":
        return False
    return not (stripped[0].isdigit() and len(stripped) > 1 and stripped[1] == "H")


@dataclasses.dataclass(frozen=True, slots=True)
class Residue:
    """One residue, and where its atoms sit in the parent coordinate array."""

    name: str
    chain: str
    number: int
    atoms: Mapping[str, int]

    def has(self, *names: str) -> bool:
        """Whether every named atom is present."""
        return all(name in self.atoms for name in names)


@dataclasses.dataclass(frozen=True, slots=True)
class Structure:
    """An atom table with a residue index built over it."""

    coords: NDArray[np.float64]
    atom_names: tuple[str, ...]
    residue_names: tuple[str, ...]
    residue_numbers: tuple[int, ...]
    chain_ids: tuple[str, ...]
    residues: tuple[Residue, ...]

    def __post_init__(self) -> None:
        """Refuse an atom table whose columns disagree."""
        if self.coords.ndim != _COORD_NDIM or self.coords.shape[1] != _COORD_COLUMNS:
            msg = f"coords must be (n_atoms, 3), got {self.coords.shape}"
            raise ValueError(msg)
        lengths = {
            len(self.atom_names),
            len(self.residue_names),
            len(self.residue_numbers),
            len(self.chain_ids),
            int(self.coords.shape[0]),
        }
        if len(lengths) != 1:
            msg = f"atom table columns disagree in length: {sorted(lengths)}"
            raise ValueError(msg)
        if not np.isfinite(self.coords).all():
            msg = "coords contain non-finite values"
            raise ValueError(msg)

    @classmethod
    def from_atoms(
        cls,
        coords: NDArray[np.float64] | Sequence[Sequence[float]],
        atom_names: Sequence[str],
        residue_names: Sequence[str],
        residue_numbers: Sequence[int],
        chain_ids: Sequence[str],
    ) -> "Structure":
        """Build a structure and index its residues in input order."""
        array = np.asarray(coords, dtype=np.float64)
        index: dict[tuple[str, int], dict[str, int]] = {}
        order: list[tuple[str, int, str]] = []
        for row, (atom, residue, number, chain) in enumerate(
            zip(atom_names, residue_names, residue_numbers, chain_ids, strict=True)
        ):
            key = (chain, number)
            if key not in index:
                index[key] = {}
                order.append((chain, number, residue))
            index[key][atom] = row
        residues = tuple(
            Residue(name=residue, chain=chain, number=number, atoms=index[(chain, number)])
            for chain, number, residue in order
        )
        return cls(
            coords=array,
            atom_names=tuple(atom_names),
            residue_names=tuple(residue_names),
            residue_numbers=tuple(residue_numbers),
            chain_ids=tuple(chain_ids),
            residues=residues,
        )

    def xyz(self, residue: Residue, atom: str) -> NDArray[np.float64]:
        """Coordinates of one named atom of one residue."""
        return np.asarray(self.coords[residue.atoms[atom]], dtype=np.float64)

    def chains(self) -> dict[str, tuple[Residue, ...]]:
        """Residues grouped by chain, each in input order."""
        grouped: dict[str, list[Residue]] = {}
        for residue in self.residues:
            grouped.setdefault(residue.chain, []).append(residue)
        return {chain: tuple(members) for chain, members in grouped.items()}

    def heavy_atom_rows(self) -> NDArray[np.int_]:
        """Row indices of every heavy atom."""
        return np.array(
            [row for row, name in enumerate(self.atom_names) if is_heavy_atom(name)],
            dtype=np.int_,
        )
