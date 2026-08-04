"""Two-stage story clustering with per-window thresholds chosen by percolation."""

import logging
from collections import defaultdict

import numpy as np

from tensionr.config import (
    EDGE_FLOOR,
    MIN_STORY_SIZE,
    MIN_THEME_SIZE,
    STORY_MAX_SHARE,
    THEME_MAX_SHARE,
    THRESHOLD_HI,
    THRESHOLD_STEP,
)

logger = logging.getLogger(__name__)

Edge = tuple[int, int, float]


class UnionFind:
    """Disjoint sets over 0..n-1, with the largest set size tracked as it grows."""

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))
        self._size = [1] * n
        self.largest = 1 if n else 0

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        self.largest = max(self.largest, self._size[ra])
        return True

    def groups(self) -> list[list[int]]:
        by_root: dict[int, list[int]] = defaultdict(list)
        for i in range(len(self._parent)):
            by_root[self.find(i)].append(i)
        return list(by_root.values())


def similarity_edges(vectors: np.ndarray, *, floor: float = EDGE_FLOOR) -> list[Edge]:
    """Cosine edges above `floor`, computed in row blocks.

    The full similarity matrix is never materialised: at 22k articles it would be
    1.9 GB, while the edge list above a useful floor is a few hundred thousand
    tuples. Vectors are assumed L2-normalised.
    """
    n = len(vectors)
    edges: list[Edge] = []
    block = 2000
    for start in range(0, n, block):
        sims = vectors[start : start + block] @ vectors.T
        for offset, row in enumerate(sims):
            i = start + offset
            row[: i + 1] = -1.0  # upper triangle only
            for j in np.nonzero(row >= floor)[0]:
                edges.append((i, int(j), float(row[j])))
        del sims
    return edges


def select_threshold(
    edges: list[Edge],
    n: int,
    *,
    max_share: float,
    floor: float = EDGE_FLOOR,
    hi: float = THRESHOLD_HI,
    step: float = THRESHOLD_STEP,
) -> float | None:
    """Return the most inclusive threshold whose largest component stays small.

    Three separate measurements found the percolation point moves between windows
    (0.70, 0.75, 0.76), so it cannot be a constant. Walking thresholds downwards
    only ever adds edges, so one descending pass over the sorted edge list finds
    the step just before the largest component exceeds `max_share` of the window.

    Returns None when no threshold in [floor, hi] satisfies the constraint — the
    window is dominated by near-duplicates at every resolution, and the caller has
    to say so rather than fall back to a threshold that over-merges.
    """
    if n <= 1 or not edges:
        return hi

    ordered = sorted(edges, key=lambda e: e[2], reverse=True)
    limit = max_share * n
    uf = UnionFind(n)
    cursor = 0
    chosen: float | None = None
    steps = int(round((hi - floor) / step))

    for k in range(steps + 1):
        candidate = hi - k * step
        while cursor < len(ordered) and ordered[cursor][2] >= candidate:
            a, b, _ = ordered[cursor]
            uf.union(a, b)
            cursor += 1
        if uf.largest > limit:
            break
        chosen = candidate

    return None if chosen is None else round(chosen, 4)


def components(edges: list[Edge], n: int, threshold: float) -> list[list[int]]:
    """Connected components using only edges at or above `threshold`."""
    uf = UnionFind(n)
    for a, b, score in edges:
        if score >= threshold:
            uf.union(a, b)
    return uf.groups()


def two_stage(
    vectors: np.ndarray,
    *,
    theme_max_share: float = THEME_MAX_SHARE,
    story_max_share: float = STORY_MAX_SHARE,
    min_theme: int = MIN_THEME_SIZE,
    min_story: int = MIN_STORY_SIZE,
) -> dict:
    """Group a window into stories: themes first, then stories inside each theme.

    A single threshold yields themes rather than stories — one pass merged Greek
    wildfires, a German heatwave and a Korean temperature record into one group.
    A second pass inside each theme separates them while keeping the multi-language
    spread the polity comparison needs.

    The shares are arguments because they are the criterion, and the floor under
    them still has to be calibrated against how many stories a day survive it.

    Returns the stories, the thresholds actually chosen, and the themes that could
    not be split, so a run publishes what it decided rather than only what it
    produced.
    """
    empty = {
        "stories": [],
        "theme_threshold": None,
        "story_thresholds": [],
        "themes": 0,
        "unsplit_themes": 0,
    }
    n = len(vectors)
    if n == 0:
        return empty

    edges = similarity_edges(vectors)
    theme_threshold = select_threshold(edges, n, max_share=theme_max_share)
    if theme_threshold is None:
        logger.warning(
            "no threshold keeps the largest theme under %.0f%% of %d articles",
            theme_max_share * 100,
            n,
        )
        return empty

    themes = [g for g in components(edges, n, theme_threshold) if len(g) >= min_theme]
    logger.info(
        "themes: %d at threshold %.3f (%d edges over %d articles)",
        len(themes),
        theme_threshold,
        len(edges),
        n,
    )

    # One pass over the edge list, bucketed by theme, rather than one pass per theme.
    # The obvious loop rescans every edge for every theme, which is O(themes x edges):
    # at 210,538 articles that was 2,113 themes against 71.7 million edges — 1.5e11
    # tuple inspections in Python, and a run killed by its own timeout after 32 minutes
    # in this step alone. An edge is only ever needed by the theme containing both its
    # ends, so it is filed once.
    theme_of: dict[int, int] = {}
    local_of: dict[int, int] = {}
    for index, theme in enumerate(themes):
        for position, node in enumerate(theme):
            theme_of[node] = index
            local_of[node] = position
    buckets: list[list[Edge]] = [[] for _ in themes]
    for a, b, score in edges:
        if score < theme_threshold:
            continue
        index = theme_of.get(a)
        if index is not None and index == theme_of.get(b):
            buckets[index].append((local_of[a], local_of[b], score))

    # A theme this small could never have been split, whatever its contents: a valid
    # split needs some component at or above `min_story` while the largest stays under
    # `story_max_share` of the theme, so it needs at least `min_story / story_max_share`
    # articles — 14.3 at the shipped constants, against a `min_theme` of 8. Every theme
    # between those two numbers was admitted and then discarded, and on one measured
    # window that was 287 of 497 themes and 2,928 articles. Such a theme is emitted
    # whole, because for a group this small "whole" is not the over-merge the second pass
    # exists to prevent — that concern is about large themes, and they are still dropped.
    indivisible = min_story / story_max_share if story_max_share > 0 else 0

    stories: list[list[int]] = []
    chosen: list[float] = []
    unsplit = 0
    indivisible_kept = 0
    for theme, inner in zip(themes, buckets, strict=True):
        threshold = select_threshold(
            inner, len(theme), max_share=story_max_share, floor=theme_threshold
        )
        groups: list[list[int]] = []
        if threshold is not None:
            chosen.append(threshold)
            groups = [
                g
                for g in components(inner, len(theme), threshold)
                if len(g) >= min_story
            ]

        if groups:
            stories.extend([theme[i] for i in g] for g in groups)
        elif len(theme) < indivisible and len(theme) >= min_story:
            stories.append(list(theme))
            indivisible_kept += 1
        else:
            # Large and dominated by near-duplicates at every resolution. Dropped, and
            # counted, because emitting it whole really would over-merge.
            unsplit += 1

    logger.info(
        "stories: %d from %d themes (%d indivisible kept whole, %d dropped as "
        "over-merged, %d articles never reached a story)",
        len(stories),
        len(themes),
        indivisible_kept,
        unsplit,
        n - sum(len(g) for g in stories),
    )
    return {
        "stories": stories,
        "theme_threshold": theme_threshold,
        "story_thresholds": chosen,
        "themes": len(themes),
        "unsplit_themes": unsplit,
        "indivisible_themes": indivisible_kept,
        # #13 decided the page publishes the count of articles that never reached a
        # measurable story. It never did, which is why the loss had to be found by
        # instrumenting the clustering by hand: 7,227 discarded against 5,549 kept on
        # the window that exposed it.
        "articles": n,
        "articles_in_stories": sum(len(g) for g in stories),
    }
