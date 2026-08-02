"""Threshold selection and two-stage grouping."""

import numpy as np

from tensionr.stories.cluster import (
    UnionFind,
    components,
    select_threshold,
    similarity_edges,
    two_stage,
)


def test_union_find_tracks_largest_set():
    uf = UnionFind(5)
    assert uf.largest == 1
    uf.union(0, 1)
    uf.union(1, 2)
    assert uf.largest == 3
    uf.union(3, 4)
    assert uf.largest == 3
    assert sorted(len(g) for g in uf.groups()) == [2, 3]


def test_union_find_reports_whether_it_merged():
    uf = UnionFind(3)
    assert uf.union(0, 1) is True
    assert uf.union(1, 0) is False


def test_threshold_excludes_the_bridge_between_two_cliques():
    # Two tight groups joined by one weak edge. A threshold that admits the bridge
    # produces one component of every node, which is the over-merge to avoid.
    edges = [
        (0, 1, 0.90),
        (1, 2, 0.90),
        (0, 2, 0.90),
        (3, 4, 0.90),
        (4, 5, 0.90),
        (3, 5, 0.90),
        (2, 3, 0.62),
    ]
    threshold = select_threshold(edges, 6, max_share=0.55)
    assert threshold > 0.62
    assert sorted(len(g) for g in components(edges, 6, threshold)) == [3, 3]


def test_threshold_returns_the_floor_when_nothing_explodes():
    edges = [(0, 1, 0.80)]
    assert select_threshold(edges, 100, max_share=0.5, floor=0.60) == 0.60


def test_threshold_is_the_ceiling_without_edges():
    assert select_threshold([], 10, max_share=0.1) == 0.95


def test_lowering_the_threshold_never_shrinks_components():
    rng = np.random.default_rng(7)
    edges = [
        (int(a), int(b), float(s))
        for a, b, s in zip(
            rng.integers(0, 30, 80), rng.integers(0, 30, 80), rng.uniform(0.5, 1.0, 80)
        )
        if a != b
    ]
    sizes = [
        max(len(g) for g in components(edges, 30, t))
        for t in (0.95, 0.85, 0.75, 0.65, 0.55)
    ]
    assert sizes == sorted(sizes)


def test_similarity_edges_only_reports_the_upper_triangle_above_the_floor():
    vectors = np.eye(4, dtype=np.float32)
    vectors[1] = vectors[0]  # a duplicate pair, cosine 1.0
    edges = similarity_edges(vectors, floor=0.9)
    assert edges == [(0, 1, 1.0)]


def test_two_stage_splits_a_theme_into_stories():
    # Three tight stories sharing a common direction, so they group into one theme
    # and separate inside it. The shares are passed explicitly because the defaults
    # are calibrated for a twenty-thousand-article window, not for twenty-four.
    rng = np.random.default_rng(3)
    base = np.zeros(64, dtype=np.float32)
    base[0] = 1.0
    rows = []
    for k in range(3):
        distinct = np.zeros(64, dtype=np.float32)
        distinct[k + 1] = 0.55
        centre = base + distinct
        centre /= np.linalg.norm(centre)
        for _ in range(8):
            rows.append(centre + rng.normal(0, 0.02, 64).astype(np.float32))
    vectors = np.asarray(rows, dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    result = two_stage(
        vectors, theme_max_share=1.0, story_max_share=0.5, min_theme=8, min_story=5
    )
    assert result["themes"] == 1
    assert len(result["stories"]) == 3
    assert sorted(len(s) for s in result["stories"]) == [8, 8, 8]
    # no article is claimed by two stories
    assigned = [i for story in result["stories"] for i in story]
    assert len(assigned) == len(set(assigned))


def test_two_stage_records_a_theme_it_cannot_split():
    # Twelve identical vectors: no resolution separates them, so the theme is
    # reported as unsplit rather than emitted whole.
    vectors = np.tile(np.eye(1, 8, dtype=np.float32), (12, 1))
    result = two_stage(vectors, theme_max_share=1.0, story_max_share=0.3)
    assert result["stories"] == []
    assert result["unsplit_themes"] == 1


def test_two_stage_on_an_empty_window():
    result = two_stage(np.zeros((0, 512), dtype=np.float32))
    assert result["stories"] == []
    assert result["theme_threshold"] is None
    assert result["themes"] == 0


def test_threshold_is_none_when_duplicates_dominate_at_every_resolution():
    edges = [(i, j, 1.0) for i in range(6) for j in range(i + 1, 6)]
    assert select_threshold(edges, 6, max_share=0.3) is None
