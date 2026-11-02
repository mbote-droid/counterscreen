"""Diversity clustering, so twenty submissions are twenty experiments.

`CLAUDE.md` section 11 gives the reason in one line: twenty variants of one
fold is one experiment, not twenty. Designs are therefore clustered by
structural similarity within each mechanism arm and cluster representatives
are submitted, never the top N by score.

`PREREGISTRATION.md` section 4 step 2, as amended by A2, registers the rule:
single-linkage at TM-score >= 0.5, the conventional same-fold boundary,
computed with the same machinery that serves G9. Single linkage is the choice
that matters here. It merges A with C whenever both resemble B, even if A and
C do not resemble each other, which is the conservative behaviour for this
purpose: a chain of near-neighbours is one fold family, and submitting two of
its ends as though they were independent is the cherry-picking that clustering
exists to prevent.
"""

import dataclasses
from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

_SIMILARITY_NDIM = 2


class ClusteringError(ValueError):
    """Raised when a similarity matrix cannot support clustering."""


def _validate(labels: Sequence[str], similarity: NDArray[np.float64]) -> None:
    if len(set(labels)) != len(labels):
        msg = f"labels must be unique, got {list(labels)}"
        raise ClusteringError(msg)
    if similarity.ndim != _SIMILARITY_NDIM or similarity.shape[0] != similarity.shape[1]:
        msg = f"similarity must be square, got shape {similarity.shape}"
        raise ClusteringError(msg)
    if similarity.shape[0] != len(labels):
        msg = f"similarity is {similarity.shape[0]}x{similarity.shape[0]} for {len(labels)} labels"
        raise ClusteringError(msg)
    # Finiteness first: np.allclose is False wherever a NaN sits, so checking
    # symmetry first would report a misleading reason for a NaN matrix.
    if not np.isfinite(similarity).all():
        msg = "similarity contains non-finite values"
        raise ClusteringError(msg)
    if not np.allclose(similarity, similarity.T, atol=1e-9):
        msg = "similarity must be symmetric; TM-score is not, so symmetrise before clustering"
        raise ClusteringError(msg)


def single_linkage(
    labels: Sequence[str],
    similarity: NDArray[np.float64],
    threshold: float,
) -> tuple[tuple[str, ...], ...]:
    """Group labels into single-linkage clusters at a similarity threshold.

    Two designs join the same cluster when their similarity reaches the
    threshold, and transitively: if A joins B and B joins C, all three are one
    cluster even where A and C are dissimilar.

    Clusters are returned in order of their first member's position in
    ``labels``, and members in that same order, so the result does not depend
    on iteration order anywhere.
    """
    _validate(labels, similarity)
    parent = list(range(len(labels)))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if similarity[i, j] >= threshold:
                union(i, j)

    grouped: dict[int, list[str]] = {}
    for index, label in enumerate(labels):
        grouped.setdefault(find(index), []).append(label)
    return tuple(tuple(members) for _, members in sorted(grouped.items()))


def representatives(
    clusters: Sequence[Sequence[str]],
    ranking: Sequence[str],
) -> tuple[str, ...]:
    """Take the best-ranked member of each cluster.

    ``ranking`` is the whole arm's designs, best first. The representative is
    whichever cluster member appears earliest in it, and the representatives
    come back in that same order, so selection reads straight off the
    registered ranking rule without a second sort.
    """
    position: Mapping[str, int] = {label: index for index, label in enumerate(ranking)}
    chosen: list[tuple[int, str]] = []
    for cluster in clusters:
        missing = [label for label in cluster if label not in position]
        if missing:
            msg = f"cluster members absent from the ranking: {sorted(missing)}"
            raise ClusteringError(msg)
        best = min(cluster, key=lambda label: position[label])
        chosen.append((position[best], best))
    return tuple(label for _, label in sorted(chosen))


@dataclasses.dataclass(frozen=True, slots=True)
class ClusterSummary:
    """What clustering removed, which is a reportable number in the funnel."""

    designs: int
    clusters: int

    @property
    def collapsed(self) -> int:
        """How many designs were absorbed into a representative."""
        return self.designs - self.clusters


def summarise_clusters(clusters: Sequence[Sequence[str]]) -> ClusterSummary:
    """Count designs and clusters for the funnel."""
    return ClusterSummary(
        designs=sum(len(cluster) for cluster in clusters),
        clusters=len(clusters),
    )
