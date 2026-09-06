"""Two-stage story clustering with per-window thresholds chosen by percolation."""

import logging
from collections import defaultdict

import numpy as np

from tensionr.config import (
    EDGE_FLOOR,
    EDGE_FLOOR_TRIAL,
    MIN_STORY_SIZE,
    MIN_THEME_SIZE,
    STORY_MAX_SHARE,
    THEME_MAX_SHARE,
    THRESHOLD_HI,
    THRESHOLD_STEP,
)

logger = logging.getLogger(__name__)

Edge = tuple[int, int, float]

# How much of the similarity matrix to hold at once, in bytes. A row block is
# `block x n` float32, so a fixed row count is a moving byte cost: the block of 2,000
# this replaces was 176 MB when the window was 22k articles and 0.96 GiB once the
# window reached 128,189, a transient nobody had accounted for. A byte budget holds
# still as the window grows.
SIMS_BLOCK_BYTES = 128 * 1024 * 1024


class Edges:
    """An edge list held as three columns rather than as a list of tuples.

    Measured on this project's own corpus: an `(int, int, float)` tuple costs 144 bytes
    once its two integers and its float are counted, against 12 for the same three
    numbers as int32, int32 and float32 columns. The published 128,189-article window
    produced 30,577,733 edges, so that list is 4.1 GiB as tuples and 350 MB as columns,
    on a runner with 16 GiB that has killed six runs in forty.

    The union-find still has to be handed Python integers, so a column is converted
    back a slice at a time and never all at once, and only for the edges a caller
    actually reaches. That is the smaller half by far: `select_threshold` stops at
    percolation and `components` masks first, and on the same window 92% of the edges
    were below the threshold finally chosen.
    """

    __slots__ = ("a", "b", "score")

    def __init__(self, a: np.ndarray, b: np.ndarray, score: np.ndarray) -> None:
        self.a = a
        self.b = b
        self.score = score

    def __len__(self) -> int:
        return int(self.score.size)

    @classmethod
    def empty(cls) -> "Edges":
        return cls(
            np.empty(0, np.int32), np.empty(0, np.int32), np.empty(0, np.float32)
        )

    @classmethod
    def of(cls, rows: list[Edge]) -> "Edges":
        """Build from `(a, b, score)` triples, for per-theme buckets and for tests."""
        if not rows:
            return cls.empty()
        a, b, score = zip(*rows, strict=True)
        return cls(
            np.fromiter(a, np.int32, len(rows)),
            np.fromiter(b, np.int32, len(rows)),
            np.fromiter(score, np.float32, len(rows)),
        )

    def above(self, threshold: float) -> "Edges":
        keep = self.score >= threshold
        return Edges(self.a[keep], self.b[keep], self.score[keep])

    def descending(self) -> "Edges":
        order = np.argsort(self.score)[::-1]
        return Edges(self.a[order], self.b[order], self.score[order])


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


def similarity_edges(vectors: np.ndarray, *, floor: float = EDGE_FLOOR) -> Edges:
    """Cosine edges above `floor`, computed in row blocks.

    The full similarity matrix is never materialised: at 128k articles it would be
    65 GB, while the edge list above a useful floor is a few hundred megabytes. The
    block is sized by `SIMS_BLOCK_BYTES` rather than by a row count, because a row
    count is a byte cost that grows with the window.

    Vectors are assumed L2-normalised.
    """
    n = len(vectors)
    if n == 0:
        return Edges.empty()

    block = max(1, min(n, SIMS_BLOCK_BYTES // (n * vectors.itemsize)))
    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    scores: list[np.ndarray] = []

    for start in range(0, n, block):
        sims = vectors[start : start + block] @ vectors.T
        for offset in range(len(sims)):
            sims[offset, : start + offset + 1] = -1.0  # upper triangle only
        hit_row, hit_col = np.nonzero(sims >= floor)
        rows.append((hit_row + start).astype(np.int32))
        cols.append(hit_col.astype(np.int32))
        scores.append(sims[hit_row, hit_col])
        del sims, hit_row, hit_col

    return Edges(
        np.concatenate(rows), np.concatenate(cols), np.concatenate(scores)
    )


def select_threshold(
    edges: Edges,
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

    Returns None when no threshold in [floor, hi] satisfies the constraint: the
    window is dominated by near-duplicates at every resolution, and the caller has
    to say so rather than fall back to a threshold that over-merges.

    The descent stops at the first candidate that percolates, so the edges below it
    are never converted out of their columns and never touched at all.
    """
    if n <= 1 or not len(edges):
        return hi

    ordered = edges.descending()
    # `searchsorted` needs an ascending array, and the scores are descending, so the
    # search runs on their negation. `stop` is then the number of edges at or above
    # the candidate, found in log time instead of by walking the list.
    falling = -ordered.score
    limit = max_share * n
    uf = UnionFind(n)
    cursor = 0
    chosen: float | None = None
    steps = int(round((hi - floor) / step))

    for k in range(steps + 1):
        candidate = hi - k * step
        stop = int(np.searchsorted(falling, -candidate, side="right"))
        if stop > cursor:
            for a, b in zip(
                ordered.a[cursor:stop].tolist(),
                ordered.b[cursor:stop].tolist(),
                strict=True,
            ):
                uf.union(a, b)
            cursor = stop
        if uf.largest > limit:
            break
        chosen = candidate

    return None if chosen is None else round(chosen, 4)


def components(edges: Edges, n: int, threshold: float) -> list[list[int]]:
    """Connected components using only edges at or above `threshold`.

    Masked in numpy before anything is converted to Python, so the discarded edges
    cost one pass over a float32 column rather than one Python comparison each.
    """
    kept = edges.above(threshold)
    uf = UnionFind(n)
    for a, b in zip(kept.a.tolist(), kept.b.tolist(), strict=True):
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

    # Built at the trial floor first. If the descent stops there the search hit the
    # wall rather than percolation, so it might have wanted to go lower and the window
    # is rebuilt at the real floor. Anything above the wall is unaffected: the edges
    # the two passes share are identical, and the ones only the second pass has are
    # below the threshold either pass would choose, where all three consumers drop
    # them. Verified against the previous implementation on a 57,579-article window:
    # same threshold, same themes, same story membership by hash.
    edges = similarity_edges(vectors, floor=EDGE_FLOOR_TRIAL)
    theme_threshold = select_threshold(
        edges, n, max_share=theme_max_share, floor=EDGE_FLOOR_TRIAL
    )
    # Two ways to hit the wall rather than percolation, and the second is easy to miss:
    # with no edges at all above the trial floor `select_threshold` returns the ceiling
    # by its own early exit, which looks like a confident answer and would leave every
    # article a singleton even though the window's edges were merely all below 0.65.
    reached_the_wall = theme_threshold is not None and (
        not len(edges) or theme_threshold <= EDGE_FLOOR_TRIAL + 1e-9
    )
    if reached_the_wall:
        logger.info(
            "threshold reached the trial floor %.2f, rebuilding from %.2f",
            EDGE_FLOOR_TRIAL,
            EDGE_FLOOR,
        )
        del edges
        edges = similarity_edges(vectors, floor=EDGE_FLOOR)
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
    # Masked in numpy first. On the published window that drops 30.6 million edges to
    # 2.4 million before a single Python object is created, where the previous loop
    # created and discarded one tuple comparison per edge.
    inner = edges.above(theme_threshold)
    buckets: list[list[Edge]] = [[] for _ in themes]
    for a, b, score in zip(
        inner.a.tolist(), inner.b.tolist(), inner.score.tolist(), strict=True
    ):
        index = theme_of.get(a)
        if index is not None and index == theme_of.get(b):
            buckets[index].append((local_of[a], local_of[b], score))
    packed = [Edges.of(bucket) for bucket in buckets]
    del inner, buckets

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
    for theme, edges_in_theme in zip(themes, packed, strict=True):
        threshold = select_threshold(
            edges_in_theme,
            len(theme),
            max_share=story_max_share,
            floor=theme_threshold,
        )
        groups: list[list[int]] = []
        if threshold is not None:
            chosen.append(threshold)
            groups = [
                g
                for g in components(edges_in_theme, len(theme), threshold)
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
