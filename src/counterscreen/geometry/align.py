"""Superposition, so two structures can be compared in one frame.

Needed because T+ and D1 come from different crystals (`SETUP.md` §2.2
requires real 7OW5 coordinates rather than a mutated T+), so any comparison
between them must first put them in a common frame or it measures
crystallographic placement instead of conformation.
"""

import dataclasses

import numpy as np
from numpy.typing import NDArray

from counterscreen.geometry.structure import Structure


class AlignmentError(ValueError):
    """Raised when two structures cannot be put in a common frame."""


@dataclasses.dataclass(frozen=True, slots=True)
class Alignment:
    """The result of superposing one structure onto another."""

    rmsd: float
    paired: int
    rotation: NDArray[np.float64]
    translation: NDArray[np.float64]

    def apply(self, coords: NDArray[np.float64]) -> NDArray[np.float64]:
        """Move coordinates into the reference frame."""
        return np.asarray(coords @ self.rotation.T + self.translation, dtype=np.float64)


def _alpha_carbons(
    structure: Structure, chain: str, first: int | None, last: int | None
) -> dict[int, NDArray[np.float64]]:
    """CA atoms of one chain, optionally restricted to a residue range.

    Each bound is applied independently. The earlier form read
    ``not (first <= n <= last if last else True)``, which evaluates the
    conditional first, so ``first`` alone was discarded and the whole chain was
    fitted -- an RMSD over an atom set nobody asked for
    (`BUILD_JOURNAL.md` ISSUE-022).
    """
    found: dict[int, NDArray[np.float64]] = {}
    for residue in structure.residues:
        if residue.chain != chain or not residue.has("CA"):
            continue
        if first is not None and residue.number < first:
            continue
        if last is not None and residue.number > last:
            continue
        found[residue.number] = structure.xyz(residue, "CA")
    return found


def superpose_on(
    mobile: Structure,
    reference: Structure,
    chain: str,
    first: int | None = None,
    last: int | None = None,
) -> Alignment:
    """Kabsch-superpose ``mobile`` onto ``reference`` using one chain's CA atoms.

    Only the named chain drives the fit. For a pMHC pair that is the HLA
    platform, so the peptide is free to differ and the difference is what gets
    measured rather than what gets fitted away.
    """
    a = _alpha_carbons(reference, chain, first, last)
    b = _alpha_carbons(mobile, chain, first, last)
    shared = sorted(set(a) & set(b))
    if len(shared) < 3:  # noqa: PLR2004
        msg = f"only {len(shared)} shared CA atoms in chain {chain!r}; cannot superpose"
        raise AlignmentError(msg)

    target = np.array([a[n] for n in shared])
    moving = np.array([b[n] for n in shared])
    target_centre, moving_centre = target.mean(axis=0), moving.mean(axis=0)
    correlation = (moving - moving_centre).T @ (target - target_centre)
    u, _, vt = np.linalg.svd(correlation)
    sign = np.sign(np.linalg.det(vt.T @ u.T))
    correction = np.diag([1.0, 1.0, sign])
    rotation = vt.T @ correction @ u.T
    translation = target_centre - rotation @ moving_centre

    fitted = moving @ rotation.T + translation
    rmsd = float(np.sqrt(((target - fitted) ** 2).sum(axis=1).mean()))
    return Alignment(rmsd=rmsd, paired=len(shared), rotation=rotation, translation=translation)


def displacement(
    mobile: Structure,
    reference: Structure,
    chain: str,
    alignment: Alignment,
) -> dict[int, float]:
    """Per-residue CA displacement between two aligned structures."""
    a = _alpha_carbons(reference, chain, None, None)
    b = _alpha_carbons(mobile, chain, None, None)
    return {
        n: float(np.linalg.norm(a[n] - alignment.apply(b[n][None, :])[0]))
        for n in sorted(set(a) & set(b))
    }
