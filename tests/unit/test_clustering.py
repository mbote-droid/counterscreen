"""Diversity clustering: single-linkage at the registered TM-score threshold."""

import numpy as np
import pytest

from counterscreen.rank.clustering import (
    ClusteringError,
    representatives,
    single_linkage,
    summarise_clusters,
)

REGISTERED_THRESHOLD = 0.5  # PREREGISTRATION section 4 step 2, amendment A2


def matrix(rows: list[list[float]]) -> np.ndarray:
    return np.array(rows, dtype=np.float64)


def test_everything_similar_collapses_to_one_cluster() -> None:
    similarity = matrix([[1.0, 0.9, 0.8], [0.9, 1.0, 0.85], [0.8, 0.85, 1.0]])
    assert single_linkage(["a", "b", "c"], similarity, REGISTERED_THRESHOLD) == (("a", "b", "c"),)


def test_nothing_similar_leaves_singletons() -> None:
    similarity = matrix([[1.0, 0.1, 0.2], [0.1, 1.0, 0.15], [0.2, 0.15, 1.0]])
    clusters = single_linkage(["a", "b", "c"], similarity, REGISTERED_THRESHOLD)
    assert clusters == (("a",), ("b",), ("c",))


def test_single_linkage_chains_through_an_intermediate() -> None:
    """The defining property, and the reason single linkage was registered.

    A resembles B and B resembles C, while A and C do not resemble each other.
    Single linkage makes them one fold family; complete linkage would split
    them and let two ends of one chain be submitted as independent designs.
    """
    similarity = matrix([[1.0, 0.6, 0.1], [0.6, 1.0, 0.6], [0.1, 0.6, 1.0]])
    assert single_linkage(["a", "b", "c"], similarity, REGISTERED_THRESHOLD) == (("a", "b", "c"),)


def test_the_threshold_is_inclusive() -> None:
    """TM-score >= 0.5 merges, per the registered rule."""
    similarity = matrix([[1.0, 0.5], [0.5, 1.0]])
    assert single_linkage(["a", "b"], similarity, 0.5) == (("a", "b"),)
    assert single_linkage(["a", "b"], similarity, 0.51) == (("a",), ("b",))


def test_clusters_partition_the_input() -> None:
    labels = ["a", "b", "c", "d", "e"]
    similarity = matrix(
        [
            [1.0, 0.7, 0.1, 0.0, 0.0],
            [0.7, 1.0, 0.1, 0.0, 0.0],
            [0.1, 0.1, 1.0, 0.9, 0.2],
            [0.0, 0.0, 0.9, 1.0, 0.2],
            [0.0, 0.0, 0.2, 0.2, 1.0],
        ]
    )
    clusters = single_linkage(labels, similarity, REGISTERED_THRESHOLD)
    flattened = [label for cluster in clusters for label in cluster]
    assert sorted(flattened) == sorted(labels)
    assert len(flattened) == len(set(flattened))
    assert clusters == (("a", "b"), ("c", "d"), ("e",))


def test_representatives_take_the_best_ranked_member() -> None:
    clusters = (("a", "b"), ("c", "d"), ("e",))
    ranking = ["d", "b", "e", "a", "c"]
    assert representatives(clusters, ranking) == ("d", "b", "e")


def test_representatives_come_back_in_ranking_order() -> None:
    clusters = (("e",), ("a", "b"), ("c", "d"))
    ranking = ["d", "b", "e", "a", "c"]
    assert representatives(clusters, ranking) == ("d", "b", "e")


def test_a_representative_absent_from_the_ranking_is_refused() -> None:
    with pytest.raises(ClusteringError, match="absent from the ranking"):
        representatives((("a", "zz"),), ["a", "b"])


def test_clustering_reports_what_it_collapsed() -> None:
    summary = summarise_clusters((("a", "b", "c"), ("d",)))
    assert summary.designs == 4
    assert summary.clusters == 2
    assert summary.collapsed == 2


def test_an_asymmetric_similarity_matrix_is_refused() -> None:
    """TM-score is not symmetric, so the caller must symmetrise deliberately."""
    similarity = matrix([[1.0, 0.9], [0.2, 1.0]])
    with pytest.raises(ClusteringError, match="symmetric"):
        single_linkage(["a", "b"], similarity, REGISTERED_THRESHOLD)


def test_a_non_square_matrix_is_refused() -> None:
    with pytest.raises(ClusteringError, match="square"):
        single_linkage(["a", "b"], matrix([[1.0, 0.5, 0.2], [0.5, 1.0, 0.3]]), 0.5)


def test_a_matrix_of_the_wrong_size_is_refused() -> None:
    similarity = matrix([[1.0, 0.5], [0.5, 1.0]])
    with pytest.raises(ClusteringError, match="for 3 labels"):
        single_linkage(["a", "b", "c"], similarity, 0.5)


def test_duplicate_labels_are_refused() -> None:
    similarity = matrix([[1.0, 0.5], [0.5, 1.0]])
    with pytest.raises(ClusteringError, match="unique"):
        single_linkage(["a", "a"], similarity, 0.5)


def test_non_finite_similarity_is_refused() -> None:
    similarity = matrix([[1.0, np.nan], [np.nan, 1.0]])
    with pytest.raises(ClusteringError, match="non-finite"):
        single_linkage(["a", "b"], similarity, 0.5)


def test_a_single_design_is_its_own_cluster() -> None:
    assert single_linkage(["a"], matrix([[1.0]]), REGISTERED_THRESHOLD) == (("a",),)
