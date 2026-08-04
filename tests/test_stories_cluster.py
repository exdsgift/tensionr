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


def test_a_theme_too_small_to_split_is_one_story():
    """It could never have been split, so discarding it discarded a real story.

    A valid split needs a component at or above `min_story` while the largest stays
    under `story_max_share` of the theme — so at least `min_story / story_max_share`
    articles. Below that the two constants contradict each other, and every such theme
    was admitted and then thrown away: 287 of 497 themes and 2,928 articles on one
    measured window.
    """
    vectors = np.tile(np.eye(1, 8, dtype=np.float32), (12, 1))
    result = two_stage(vectors, theme_max_share=1.0, story_max_share=0.3, min_story=5)
    assert [len(s) for s in result["stories"]] == [12]
    assert result["indivisible_themes"] == 1
    assert result["unsplit_themes"] == 0


def test_a_large_theme_that_cannot_split_is_still_dropped():
    """For a big group, emitting it whole is the over-merge the second pass prevents."""
    vectors = np.tile(np.eye(1, 8, dtype=np.float32), (40, 1))
    result = two_stage(vectors, theme_max_share=1.0, story_max_share=0.3, min_story=5)
    assert result["stories"] == []
    assert result["unsplit_themes"] == 1
    assert result["indivisible_themes"] == 0


def test_a_theme_below_the_story_floor_is_not_rescued():
    """Small enough to be indivisible is not the same as big enough to be a story."""
    vectors = np.tile(np.eye(1, 8, dtype=np.float32), (4, 1))
    result = two_stage(
        vectors, theme_max_share=1.0, story_max_share=0.3, min_theme=3, min_story=5
    )
    assert result["stories"] == []
    assert result["indivisible_themes"] == 0


def test_the_run_reports_how_many_articles_never_reached_a_story():
    """#13 decided this is published. It was not, so the loss had to be instrumented."""
    vectors = np.tile(np.eye(1, 8, dtype=np.float32), (40, 1))
    result = two_stage(vectors, theme_max_share=1.0, story_max_share=0.3, min_story=5)
    assert result["articles"] == 40
    assert result["articles_in_stories"] == 0


def test_two_stage_on_an_empty_window():
    result = two_stage(np.zeros((0, 512), dtype=np.float32))
    assert result["stories"] == []
    assert result["theme_threshold"] is None
    assert result["themes"] == 0


def test_threshold_is_none_when_duplicates_dominate_at_every_resolution():
    edges = [(i, j, 1.0) for i in range(6) for j in range(i + 1, 6)]
    assert select_threshold(edges, 6, max_share=0.3) is None


def test_edges_are_filed_to_the_theme_that_owns_both_their_ends():
    """The sub-pass must see each theme's internal edges and no others.

    This is the invariant behind the fix for the O(themes x edges) rescan: the loop
    that filed one edge list per theme by re-reading every edge produced the right
    answer and took 97 projected minutes at 2,113 themes against 71.7 million edges,
    which killed a run on its own timeout. Bucketing in a single pass has to give
    exactly the same grouping, and two well-separated themes is where a leak between
    buckets would show up as a merge.
    """
    rng = np.random.default_rng(11)
    rows = []
    # two themes on orthogonal axes, two stories inside each
    for axis in (0, 32):
        for k in range(2):
            centre = np.zeros(64, dtype=np.float32)
            centre[axis] = 1.0
            centre[axis + k + 1] = 0.55
            centre /= np.linalg.norm(centre)
            for _ in range(8):
                rows.append(centre + rng.normal(0, 0.02, 64).astype(np.float32))
    vectors = np.asarray(rows, dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)

    result = two_stage(
        vectors, theme_max_share=0.6, story_max_share=0.6, min_theme=8, min_story=5
    )
    assert result["themes"] == 2
    assert len(result["stories"]) == 4
    assert sorted(len(s) for s in result["stories"]) == [8, 8, 8, 8]
    # every story sits wholly inside one theme: an edge filed to the wrong bucket
    # would join articles across the orthogonal axes
    for story in result["stories"]:
        assert len({i // 16 for i in story}) == 1
    assigned = [i for story in result["stories"] for i in story]
    assert len(assigned) == len(set(assigned))
