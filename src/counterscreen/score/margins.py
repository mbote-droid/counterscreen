"""Specificity margins: the quantity this project ranks on.

`PROTOCOL.md` section 3.5 states the strategic fact the whole pipeline turns on.
The competition resolves mutation specificity and peptide-dependence before
affinity, so a micromolar binder that discriminates beats a nanomolar binder
that does not, yet nearly every default pipeline ranks on confidence against
the target alone. The margins here are the alternative objective:

    M_mut = C(T+) - C(D1)     mutation specificity, against the wild type
    M_pep = C(T+) - C(D2)     peptide dependence, against the empty groove
    M_var = C(T+) - max C(D3..D5)   variant discrimination, optional

Three implementation decisions are load-bearing, and each has a registered
mutant in `PROTOCOL.md` section 12.4b that a test must kill.

**Pooled SD is measured across seeds within one design, never across
designs.** `DESIGN.md` section 4 is explicit that getting this backwards would
invert the gate: variation between designs is the signal being ranked, so
folding it into the noise estimate would make good designs look
indistinguishable from noise and bad ones look clean. A :class:`CounterScreen`
holds one design, so the wrong quantity is not expressible here, and a test
pins it anyway.

**Margins are paired by seed, not by position.** The counter-screen runs the
same seed against every target, so subtracting matched seeds removes the
seed-to-seed component the gate is trying to measure against. Arms are matched
on seed identity and a mismatch is refused rather than silently zipped.

**Roles are named, never positional.** D1 is the wild-type complex and D2 the
peptide-free one; swapping them is a registered mutant. Nothing here takes
decoys as an ordered list.
"""

import dataclasses
import enum
import math
import statistics
from collections.abc import Mapping, Sequence

#: Two seeds is the minimum that admits a standard deviation at all, and is
#: what `PROTOCOL.md` section 9 runs at the screening tier.
MIN_SEEDS = 2


class TargetRole(enum.StrEnum):
    """What a target is for, per `PROTOCOL.md` section 3.1."""

    TARGET = "target"
    MUTATION_DECOY = "mutation_decoy"
    PEPTIDE_FREE_DECOY = "peptide_free_decoy"
    VARIANT_DECOY = "variant_decoy"


class MarginError(ValueError):
    """Raised when a counter-screen cannot yield a well-defined margin."""


@dataclasses.dataclass(frozen=True, slots=True)
class ArmScores:
    """One design's confidence values against one target, over seeds."""

    label: str
    role: TargetRole
    scores: tuple[tuple[int, float], ...]

    def __post_init__(self) -> None:
        """Refuse an arm that cannot support a spread."""
        if len(self.scores) < MIN_SEEDS:
            msg = f"arm {self.label!r} has {len(self.scores)} seed(s); at least {MIN_SEEDS} needed"
            raise MarginError(msg)
        seeds = [seed for seed, _ in self.scores]
        if len(set(seeds)) != len(seeds):
            msg = f"arm {self.label!r} repeats a seed: {seeds}"
            raise MarginError(msg)
        if any(not math.isfinite(value) for _, value in self.scores):
            msg = f"arm {self.label!r} carries a non-finite confidence value"
            raise MarginError(msg)

    @classmethod
    def create(cls, label: str, role: TargetRole, scores: Mapping[int, float]) -> "ArmScores":
        """Build an arm, ordering by seed so output never depends on dict order."""
        return cls(label=label, role=role, scores=tuple(sorted(scores.items())))

    @property
    def seeds(self) -> tuple[int, ...]:
        """Seeds this arm was scored at, ascending."""
        return tuple(seed for seed, _ in self.scores)

    @property
    def values(self) -> tuple[float, ...]:
        """Confidence values, ordered by seed."""
        return tuple(value for _, value in self.scores)

    @property
    def mean(self) -> float:
        """Mean confidence across seeds."""
        return statistics.fmean(self.values)

    @property
    def sd(self) -> float:
        """Sample standard deviation across seeds, within this design."""
        return statistics.stdev(self.values)

    def at(self, seed: int) -> float:
        """Confidence at one seed."""
        for candidate, value in self.scores:
            if candidate == seed:
                return value
        msg = f"arm {self.label!r} was not scored at seed {seed}"
        raise MarginError(msg)


@dataclasses.dataclass(frozen=True, slots=True)
class Margin:
    """A specificity margin, with the noise it must be judged against."""

    name: str
    minuend: str
    subtrahend: str
    per_seed: tuple[tuple[int, float], ...]
    pooled_sd: float

    @property
    def values(self) -> tuple[float, ...]:
        """Per-seed margin values, ordered by seed."""
        return tuple(value for _, value in self.per_seed)

    @property
    def mean(self) -> float:
        """Mean margin across seeds."""
        return statistics.fmean(self.values)

    @property
    def sd(self) -> float:
        """Standard deviation of the margin itself across seeds."""
        return statistics.stdev(self.values)

    def exceeds_noise(self, sd_multiple: float) -> bool:
        """Whether the margin clears the G4 noise floor.

        One-sided on purpose. `PROTOCOL.md` section 8 registers G4 as
        ``M > 2 x pooled SD``, so a design that scores *better* against a
        decoy produces a negative margin and fails, rather than passing on
        magnitude.
        """
        return self.mean > sd_multiple * self.pooled_sd


def pooled_sd(arms: Sequence[ArmScores]) -> float:
    """Pool the within-design seed standard deviations of several arms.

    The usual pooled estimator, weighting each arm's variance by its degrees
    of freedom. Every value comes from one design's seeds, which is the whole
    point: `DESIGN.md` section 4 warns that pooling across designs would fold
    the signal into the noise and invert the gate.
    """
    if not arms:
        msg = "pooled SD needs at least one arm"
        raise MarginError(msg)
    numerator = 0.0
    degrees = 0
    for arm in arms:
        freedom = len(arm.scores) - 1
        numerator += freedom * arm.sd**2
        degrees += freedom
    if degrees == 0:
        msg = "pooled SD needs at least one arm with two or more seeds"
        raise MarginError(msg)
    return math.sqrt(numerator / degrees)


@dataclasses.dataclass(frozen=True, slots=True)
class CounterScreen:
    """One design scored against the target and its decoys.

    Holds a single design, so a pooled SD computed from it cannot accidentally
    reach across designs.
    """

    design_id: str
    metric: str
    arms: tuple[ArmScores, ...]

    def __post_init__(self) -> None:
        """Refuse a screen whose arms cannot be compared seed for seed."""
        labels = [arm.label for arm in self.arms]
        if len(set(labels)) != len(labels):
            msg = f"counter-screen repeats an arm label: {labels}"
            raise MarginError(msg)
        if not any(arm.role is TargetRole.TARGET for arm in self.arms):
            msg = "counter-screen has no target arm"
            raise MarginError(msg)
        seed_sets = {arm.seeds for arm in self.arms}
        if len(seed_sets) != 1:
            msg = f"arms were scored at different seeds: {sorted(seed_sets)}"
            raise MarginError(msg)

    @property
    def seeds(self) -> tuple[int, ...]:
        """Seeds every arm was scored at."""
        return self.arms[0].seeds

    def arm(self, label: str) -> ArmScores:
        """Return the arm with this label."""
        for arm in self.arms:
            if arm.label == label:
                return arm
        msg = f"no arm labelled {label!r}; have {[a.label for a in self.arms]}"
        raise MarginError(msg)

    def by_role(self, role: TargetRole) -> tuple[ArmScores, ...]:
        """Every arm serving a given role."""
        return tuple(arm for arm in self.arms if arm.role is role)

    def _single(self, role: TargetRole) -> ArmScores:
        found = self.by_role(role)
        if len(found) != 1:
            msg = f"expected exactly one {role} arm, found {len(found)}"
            raise MarginError(msg)
        return found[0]

    def margin(self, name: str, minuend: ArmScores, subtrahend: Sequence[ArmScores]) -> Margin:
        """Margin of one arm over the best of several, paired by seed."""
        if not subtrahend:
            msg = f"margin {name!r} needs something to subtract"
            raise MarginError(msg)
        per_seed = tuple(
            (seed, minuend.at(seed) - max(arm.at(seed) for arm in subtrahend))
            for seed in self.seeds
        )
        return Margin(
            name=name,
            minuend=minuend.label,
            subtrahend="|".join(arm.label for arm in subtrahend),
            per_seed=per_seed,
            pooled_sd=pooled_sd([minuend, *subtrahend]),
        )

    def m_mut(self) -> Margin:
        """Mutation-specificity margin: the target over the wild-type decoy."""
        return self.margin(
            "M_mut",
            self._single(TargetRole.TARGET),
            [self._single(TargetRole.MUTATION_DECOY)],
        )

    def m_pep(self) -> Margin:
        """Peptide-dependence margin: the target over the peptide-free decoy."""
        return self.margin(
            "M_pep",
            self._single(TargetRole.TARGET),
            [self._single(TargetRole.PEPTIDE_FREE_DECOY)],
        )

    def m_var(self) -> Margin:
        """Variant-discrimination margin: the target over the best variant decoy.

        Optional, per `PROTOCOL.md` section 7.1. Uses the maximum over D3..D5,
        so the margin reflects the decoy the design was worst at rejecting.
        """
        variants = self.by_role(TargetRole.VARIANT_DECOY)
        if not variants:
            msg = "counter-screen carries no variant decoys"
            raise MarginError(msg)
        return self.margin("M_var", self._single(TargetRole.TARGET), variants)


@dataclasses.dataclass(frozen=True, slots=True)
class Distribution:
    """A distribution summary, which is how every quality metric is reported.

    `PROTOCOL.md` section 12.3a: report distributions, never point values. The
    median, the interquartile range and the count passing say something; a
    single mean invites the reader to assume it is typical.
    """

    count: int
    passing: int
    median: float
    q1: float
    q3: float
    minimum: float
    maximum: float

    @property
    def iqr(self) -> float:
        """Interquartile range."""
        return self.q3 - self.q1


def summarise(values: Sequence[float], passing: Sequence[bool] | None = None) -> Distribution:
    """Summarise values as a distribution, with how many passed."""
    if not values:
        msg = "cannot summarise an empty sample"
        raise MarginError(msg)
    ordered = sorted(values)
    if len(ordered) >= MIN_SEEDS:
        quartiles = statistics.quantiles(ordered, n=4, method="inclusive")
        q1, _, q3 = quartiles
    else:
        q1 = q3 = ordered[0]
    return Distribution(
        count=len(ordered),
        passing=sum(passing) if passing is not None else 0,
        median=statistics.median(ordered),
        q1=q1,
        q3=q3,
        minimum=ordered[0],
        maximum=ordered[-1],
    )
