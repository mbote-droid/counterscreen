"""Mass-action occupancy, and what a K_D ratio actually buys in a cell.

`PROTOCOL.md` section 12.6 makes the argument this module exists for. The
competition ranks on K_D and K_D ratios, and neither answers whether a binder
would be *useful*. Wild-type KRAS is presented across healthy tissue while
G12D is confined to tumour cells, so the ratio a cell experiences is not
``K_D(WT) / K_D(G12D)`` but the ratio of *bound complexes*, which folds in
presentation density:

    theta = [B] / ([B] + K_D)

    selectivity_index = (theta_G12D x copies_G12D) / (theta_WT x copies_WT)

The consequence section 12.6 draws is the point of the whole module: a design
with a hundredfold K_D ratio can have a selectivity index near or below 1 once
presentation density is accounted for. That is a real therapeutic constraint that no ranking
on affinity ratios can capture, and a test here reproduces it numerically
rather than restating it (`PROTOCOL.md` §12.6).

**Discrimination is also a function of dose, which the ranked objective is
not.** :func:`discrimination_at_occupancy` gives the exact identity
``D = r(1 - x) + x``: the discrimination a K_D ratio ``r`` actually delivers
at target occupancy ``x`` interpolates linearly between ``r``, approached only
as the dose goes to zero, and 1 at saturation. So the affinity ratio the
pipeline ranks on is its own best case, realised at a concentration that
binds nothing, and a hundredfold ratio is tenfold at 90% occupancy. See
`FINDINGS.md` F-18.

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

    Refuses a degenerate range on purpose. `PROTOCOL.md` section 12.6 requires
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
                "PROTOCOL.md section 12.6 requires a sensitivity analysis, not a point "
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


def discrimination_at_occupancy(kd_ratio: float, target_occupancy: float) -> float:
    """Discrimination actually achieved at a given target occupancy.

    ``D = r(1 - x) + x`` for a K_D ratio ``r`` and target occupancy ``x``.
    Exact, not an approximation: substituting the concentration that gives
    occupancy ``x`` into the ratio of occupancies
    ``(K_wt + [B]) / (K_mut + [B])`` cancels the concentration entirely.

    The consequence is the one `FINDINGS.md` F-18 is about. Discrimination is
    a linear interpolation between the full K_D ratio, approached only as
    occupancy goes to zero, and 1 at saturation -- so the affinity ratio this
    pipeline ranks on is the value at a dose that binds nothing. A hundredfold
    ratio yields 50.5-fold at half occupancy and 10.9-fold at 90%.
    """
    if kd_ratio <= 0.0:
        msg = f"a K_D ratio must be positive, got {kd_ratio}"
        raise OccupancyError(msg)
    if not 0.0 <= target_occupancy <= 1.0:
        msg = f"occupancy must lie in [0, 1], got {target_occupancy}"
        raise OccupancyError(msg)
    return kd_ratio * (1.0 - target_occupancy) + target_occupancy


def occupancy_for_discrimination(kd_ratio: float, discrimination: float) -> float:
    """Return the most target occupancy that still leaves a given discrimination.

    Inverts :func:`discrimination_at_occupancy`: ``x = (r - D) / (r - 1)``.
    Answers the question `PROTOCOL.md` section 12.6 item 2 asks in the other
    direction -- not what affinity is needed for occupancy, but what occupancy
    costs in specificity.
    """
    if kd_ratio <= 1.0:
        msg = f"a K_D ratio must exceed 1 to trade against, got {kd_ratio}"
        raise OccupancyError(msg)
    if not 1.0 <= discrimination <= kd_ratio:
        msg = (
            f"discrimination must lie between 1 and the K_D ratio {kd_ratio}, got {discrimination}"
        )
        raise OccupancyError(msg)
    return (kd_ratio - discrimination) / (kd_ratio - 1.0)


def kd_for_occupancy(binder: Molar, target_occupancy: float) -> Molar:
    """Return the K_D needed to reach an occupancy at a given concentration.

    Answers item 2 of `PROTOCOL.md` section 12.6: what affinity is actually
    required for meaningful occupancy at plausible neoantigen copy numbers.
    """
    if not 0.0 < target_occupancy < 1.0:
        msg = f"occupancy must lie strictly between 0 and 1, got {target_occupancy}"
        raise OccupancyError(msg)
    return Molar(binder.value * (1.0 - target_occupancy) / target_occupancy)


@dataclasses.dataclass(frozen=True, slots=True)
class SelectivitySurface:
    """Selectivity index over a grid of presentation densities.

    Reported as a surface rather than a value, per `PROTOCOL.md` section 12.6.
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
        """Share of the grid at or below a selectivity threshold.

        At 1.0 this is the share of the stated parameter range in which the
        design is not selective at all in bound complexes per cell, whatever
        its K_D ratio says.

        **It is a share of grid points, and the grid is log-spaced**, so this
        is an average under an implicit log-uniform prior over copy numbers --
        a choice, not a neutral summary, and the only defensible default when
        the density is known to within orders of magnitude. It is not a
        probability: the copy-number range is a stated interval, not a
        distribution anyone measured. Report :attr:`minimum` alongside it,
        which carries no prior at all.
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
    show the gap between the affinity ratio and the selectivity a cell would
    actually experience.
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
