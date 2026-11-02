"""Mass-action occupancy, and what a K_D ratio actually buys in a cell.

`CLAUDE.md` section 12.6 makes the argument this module exists for. The
competition ranks on K_D and K_D ratios, and neither answers whether a binder
would be *useful*. Wild-type KRAS is presented across healthy tissue while
G12D is confined to tumour cells, so the ratio a cell experiences is not
``K_D(WT) / K_D(G12D)`` but the ratio of *bound complexes*, which folds in
presentation density:

    theta = [B] / ([B] + K_D)

    selectivity_index = (theta_G12D x copies_G12D) / (theta_WT x copies_WT)

The consequence section 12.6 draws is the point of the whole module: a design
with a hundredfold K_D ratio can have a selectivity index near or below 1 once
presentation density is accounted for. That is a real therapeutic constraint
the competition ranking does not capture, and a test here reproduces it
numerically rather than restating it.

**Copy numbers must arrive as a range, never as a value.** `DESIGN.md`
section 8 registers that as an assertion this package has to satisfy, and
section 12.6 gives the reason: pMHC copy numbers for this epitope are not well
established, so the output is a sensitivity analysis over a stated range and
never a point prediction. :class:`CopyNumberRange` refuses a degenerate range,
so a point estimate cannot be smuggled in by setting both ends equal.

This package takes K_D values from any source and knows nothing about folding
models (`DESIGN.md` section 1). A predicted K_D and a measured one are the
same kind of input here; which it was belongs in the provenance, not in the
arithmetic.
"""

import dataclasses
import math

import numpy as np
from numpy.typing import NDArray

from counterscreen.core.units import Molar


class OccupancyError(ValueError):
    """Raised when an occupancy model is asked for something it cannot mean."""


@dataclasses.dataclass(frozen=True, slots=True)
class CopyNumberRange:
    """A range of presented complexes per cell.

    Refuses a degenerate range on purpose. `CLAUDE.md` section 12.6 requires
    a sensitivity analysis over a stated range and explicitly not a point
    prediction, so collapsing the range is not a valid way to ask this
    question.
    """

    low: int
    high: int

    def __post_init__(self) -> None:
        """Refuse a point estimate dressed as a range."""
        if self.low <= 0:
            msg = f"copy numbers must be positive, got low={self.low}"
            raise OccupancyError(msg)
        if self.high <= self.low:
            msg = (
                f"copy numbers must span a range, got low={self.low} high={self.high}. "
                "CLAUDE.md section 12.6 requires a sensitivity analysis, not a point "
                "prediction: presentation density for this epitope is not well established"
            )
            raise OccupancyError(msg)

    def grid(self, points: int = 25) -> NDArray[np.float64]:
        """Log-spaced copy numbers across the range."""
        if points < 2:  # noqa: PLR2004
            msg = f"a range needs at least 2 points, got {points}"
            raise OccupancyError(msg)
        return np.logspace(math.log10(self.low), math.log10(self.high), points)


def occupancy(binder: Molar, kd: Molar) -> float:
    """Fractional occupancy of a single site under mass action.

    ``theta = [B] / ([B] + K_D)``. At ``[B] == K_D`` this is one half, which is
    what a dissociation constant means.
    """
    if binder.value < 0:
        msg = f"binder concentration cannot be negative, got {binder}"
        raise OccupancyError(msg)
    if kd.value <= 0:
        msg = f"a dissociation constant must be positive, got {kd}"
        raise OccupancyError(msg)
    return binder.value / (binder.value + kd.value)


def competitive_occupancy(
    binder: Molar,
    binder_kd: Molar,
    competitor: Molar,
    competitor_kd: Molar,
) -> float:
    """Occupancy when an endogenous partner competes for the same complex.

    ``theta = ([B]/K_B) / (1 + [B]/K_B + [T]/K_T)``. With no competitor present
    this reduces to :func:`occupancy`, which a test asserts rather than
    assumes.
    """
    for value, name in ((binder_kd, "binder_kd"), (competitor_kd, "competitor_kd")):
        if value.value <= 0:
            msg = f"{name} must be positive, got {value}"
            raise OccupancyError(msg)
    if binder.value < 0 or competitor.value < 0:
        msg = "concentrations cannot be negative"
        raise OccupancyError(msg)
    bound = binder.value / binder_kd.value
    blocked = competitor.value / competitor_kd.value
    return bound / (1.0 + bound + blocked)


def kd_for_occupancy(binder: Molar, target_occupancy: float) -> Molar:
    """Return the K_D needed to reach an occupancy at a given concentration.

    Answers item 2 of `CLAUDE.md` section 12.6: what affinity is actually
    required for meaningful occupancy at plausible neoantigen copy numbers.
    """
    if not 0.0 < target_occupancy < 1.0:
        msg = f"occupancy must lie strictly between 0 and 1, got {target_occupancy}"
        raise OccupancyError(msg)
    return Molar(binder.value * (1.0 - target_occupancy) / target_occupancy)


@dataclasses.dataclass(frozen=True, slots=True)
class SelectivitySurface:
    """Selectivity index over a grid of presentation densities.

    Reported as a surface rather than a value, per `CLAUDE.md` section 12.6.
    ``values[i, j]`` is the index at ``mutant_copies[i]`` and
    ``wild_type_copies[j]``.
    """

    mutant_copies: NDArray[np.float64]
    wild_type_copies: NDArray[np.float64]
    values: NDArray[np.float64]
    kd_ratio: float
    occupancy_ratio: float

    @property
    def minimum(self) -> float:
        """Worst selectivity across the stated range."""
        return float(self.values.min())

    @property
    def maximum(self) -> float:
        """Best selectivity across the stated range."""
        return float(self.values.max())

    def fraction_below(self, threshold: float = 1.0) -> float:
        """Share of the surface at or below a selectivity threshold.

        At 1.0 this is the share of the stated parameter range in which the
        design is not selective at all in bound complexes per cell, whatever
        its K_D ratio says.
        """
        return float(np.mean(self.values <= threshold))

    def dominant_parameter(self) -> str:
        """Which axis drives the result, which section 12.6 requires stating."""
        across_mutant = float(np.ptp(self.values.mean(axis=1)))
        across_wild_type = float(np.ptp(self.values.mean(axis=0)))
        if math.isclose(across_mutant, across_wild_type, rel_tol=1e-9):
            return "neither"
        return "mutant_copies" if across_mutant > across_wild_type else "wild_type_copies"


def selectivity_surface(
    binder: Molar,
    kd_mutant: Molar,
    kd_wild_type: Molar,
    *,
    mutant_copies: CopyNumberRange,
    wild_type_copies: CopyNumberRange,
    points: int = 25,
) -> SelectivitySurface:
    """Compute selectivity in bound complexes per cell, over a density range.

    The K_D ratio and the occupancy ratio are carried alongside so a report can
    show the gap between what the competition ranks on and what a cell would
    experience.
    """
    theta_mutant = occupancy(binder, kd_mutant)
    theta_wild_type = occupancy(binder, kd_wild_type)
    if theta_wild_type == 0.0:
        msg = "wild-type occupancy is zero; selectivity is undefined"
        raise OccupancyError(msg)

    mutant_grid = mutant_copies.grid(points)
    wild_type_grid = wild_type_copies.grid(points)
    numerator = theta_mutant * mutant_grid[:, None]
    denominator = theta_wild_type * wild_type_grid[None, :]

    return SelectivitySurface(
        mutant_copies=mutant_grid,
        wild_type_copies=wild_type_grid,
        values=np.asarray(numerator / denominator, dtype=np.float64),
        kd_ratio=kd_wild_type.ratio_to(kd_mutant),
        occupancy_ratio=theta_mutant / theta_wild_type,
    )
