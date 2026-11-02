# mypy: disallow_any_decorated=false
# hypothesis types @given as Callable[..., None], which disallow_any_decorated
# rejects. Relaxing that one flag here keeps strict mode everywhere else.
"""Clustering invariants that must hold for any similarity matrix."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from counterscreen.rank.clustering import single_linkage

similarity_value = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
sizes = st.integers(min_value=1, max_value=7)


@st.composite
def symmetric_matrix(draw: st.DrawFn) -> tuple[list[str], np.ndarray]:
    """Draw a symmetric similarity matrix with a unit diagonal, and its labels."""
    size = draw(sizes)
    upper = draw(st.lists(similarity_value, min_size=size * size, max_size=size * size))
    grid = np.array(upper, dtype=np.float64).reshape(size, size)
    grid = np.triu(grid, 1)
    grid = grid + grid.T
    np.fill_diagonal(grid, 1.0)
    return [f"d{i}" for i in range(size)], grid


@given(case=symmetric_matrix(), threshold=similarity_value)
def test_clusters_always_partition_the_input(
    case: tuple[list[str], np.ndarray], threshold: float
) -> None:
    labels, grid = case
    clusters = single_linkage(labels, grid, threshold)
    flattened = [label for cluster in clusters for label in cluster]
    assert sorted(flattened) == sorted(labels)
    assert len(flattened) == len(set(flattened))


@given(case=symmetric_matrix(), high=similarity_value, drop=similarity_value)
def test_lowering_the_threshold_can_only_merge(
    case: tuple[list[str], np.ndarray], high: float, drop: float
) -> None:
    """Clustering is monotone in the threshold: looser never splits."""
    labels, grid = case
    low = max(0.0, high - drop)
    assert len(single_linkage(labels, grid, low)) <= len(single_linkage(labels, grid, high))


@given(case=symmetric_matrix())
def test_a_threshold_above_every_similarity_leaves_singletons(
    case: tuple[list[str], np.ndarray],
) -> None:
    labels, grid = case
    off_diagonal = grid[~np.eye(len(labels), dtype=bool)]
    ceiling = float(off_diagonal.max()) if off_diagonal.size else 0.0
    clusters = single_linkage(labels, grid, ceiling + 0.01)
    assert len(clusters) == len(labels)


@given(case=symmetric_matrix())
def test_a_threshold_of_zero_collapses_everything(
    case: tuple[list[str], np.ndarray],
) -> None:
    labels, grid = case
    assert len(single_linkage(labels, grid, 0.0)) == 1
