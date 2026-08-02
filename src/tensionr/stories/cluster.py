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

    stories: list[list[int]] = []
    chosen: list[float] = []
    unsplit = 0
    for theme in themes:
        local = {global_i: local_i for local_i, global_i in enumerate(theme)}
        inner = [
            (local[a], local[b], score)
            for a, b, score in edges
            if a in local and b in local and score >= theme_threshold
        ]
        threshold = select_threshold(
            inner, len(theme), max_share=story_max_share, floor=theme_threshold
        )
        if threshold is None:
            # Near-duplicates at every resolution inside this theme. Recorded and
            # skipped: emitting it whole would be the over-merge the second pass exists
            # to prevent.
            unsplit += 1
            continue
        chosen.append(threshold)
        for group in components(inner, len(theme), threshold):
            if len(group) >= min_story:
                stories.append([theme[i] for i in group])

    logger.info(
        "stories: %d from %d themes (%d unsplit)", len(stories), len(themes), unsplit
    )
    return {
        "stories": stories,
        "theme_threshold": theme_threshold,
        "story_thresholds": chosen,
        "themes": len(themes),
        "unsplit_themes": unsplit,
    }
