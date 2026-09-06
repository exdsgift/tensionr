"""A two-dimensional view of where the featured stories sit in the embedding space.

This is a picture of 512 dimensions drawn on a plane, which is a lossy thing to do, so
the question is not whether it loses something but whether what survives is true. Both
answers are measured on the run's own vectors and published beside the picture rather
than assumed.

WHY ONLY THE FEATURED STORIES

Fitting the projection to the whole window and plotting everything would be the obvious
thing and it would be a lie. Measured on a real 26,015-article window, the first two
principal components of the whole window carry **7.4%** of its variance, and 42
components are needed for half of it. That picture is a cloud with no structure in it,
and a reader would take the absence of structure for a finding.

Restricted to the articles of the five featured stories, the same procedure carries
**28.3%**, and more to the point the neighbourhoods survive: 90.3% of those points have
their nearest neighbour on the plane inside the same story they belong to, against 100%
in the full space. So nine adjacencies in ten are real.

That degrades quickly as more stories are added, which is why the cut is five and not
a preference:

    5 stories, 1,515 articles    28.3% of variance    90.3% of neighbours
    10 stories, 2,085            23.3%                80.3%
    20 stories, 2,634            19.7%                74.8%

At twenty, a quarter of the adjacencies a reader would see are artefacts of the
flattening. The agreement is recomputed per run on the points actually plotted, so a
window where the projection happens to be poor says so instead of being drawn anyway.

WHY THE POINTS ARE CAPPED

The page has a measured weight budget (ADR 0002), and the framework serialises the tree
into the document a second time, so a coordinate costs about twice what it reads. The
cap is per story and the sampling is deterministic and evenly spaced through the story's
own order, and the true count travels with it so the page states what it is showing.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# At most this many points per story. Evenly spaced rather than random, so the same run
# drawn twice is the same picture.
POINTS_PER_STORY = 120

# Coordinates are published on this grid. Anything finer is invisible at the size the
# figure is drawn and costs bytes in a budget that has about 13 KB spare.
GRID = 1000

# Below this share of nearest neighbours landing in the right story, the projection is
# not telling the truth about adjacency and the page is told not to draw it.
MIN_AGREEMENT = 0.75


def _sample(indices: list[int], cap: int) -> list[int]:
    """`cap` of `indices`, evenly spaced, keeping the order they arrived in."""
    if len(indices) <= cap:
        return list(indices)
    step = np.linspace(0, len(indices) - 1, cap)
    return [indices[int(round(p))] for p in step]


def _agreement(points: np.ndarray, label: np.ndarray) -> float:
    """Share of points whose nearest neighbour on the plane is in the same story."""
    if len(points) < 2:
        return 0.0
    gap = ((points[:, None, :] - points[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(gap, np.inf)
    return float((label[gap.argmin(1)] == label).mean())


def project(
    groups: list[list[int]],
    vectors: np.ndarray,
    *,
    cap: int = POINTS_PER_STORY,
) -> dict[str, Any] | None:
    """Project the articles of `groups` onto their own first two components.

    `groups` are article row indices into `vectors`, one list per featured story, in
    the order the page shows them. Returns None when there is nothing worth drawing:
    fewer than two stories, or a projection whose neighbourhoods do not survive it.
    """
    usable = [g for g in groups if len(g) >= 2]
    if len(usable) < 2:
        return None

    taken = [_sample(g, cap) for g in usable]
    flat = np.concatenate([np.asarray(t, dtype=np.int64) for t in taken])
    label = np.concatenate(
        [np.full(len(t), i, dtype=np.int64) for i, t in enumerate(taken)]
    )

    block = vectors[flat]
    centred = block - block.mean(0)
    # Full SVD of an (n x 512) block, where n is at most cap x stories. The economy
    # form is what numpy gives by default for a tall matrix.
    _, singular, components = np.linalg.svd(centred, full_matrices=False)
    plane = centred @ components[:2].T

    spread = float((singular**2).sum())
    retained = float((singular[:2] ** 2).sum() / spread) if spread > 0 else 0.0
    agreement = _agreement(plane, label)

    if agreement < MIN_AGREEMENT:
        logger.info(
            "latent projection not drawn: %.1f%% of neighbours survive it, below %.0f%%",
            100 * agreement,
            100 * MIN_AGREEMENT,
        )
        return None

    # To the grid, with each axis scaled independently: the figure has no units and a
    # shared scale would waste most of the frame on whichever axis happens to be short.
    lo, hi = plane.min(0), plane.max(0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    grid = np.rint((plane - lo) / span * GRID).astype(int)

    at = 0
    series = []
    for group, sampled in zip(usable, taken, strict=True):
        chunk = grid[at : at + len(sampled)]
        at += len(sampled)
        series.append(
            {
                "points": [[int(x), int(y)] for x, y in chunk],
                "shown": len(sampled),
                "articles": len(group),
            }
        )

    return {
        "stories": series,
        "grid": GRID,
        "retained": round(retained, 4),
        "agreement": round(agreement, 4),
        "plotted": int(len(flat)),
        "articles": int(sum(len(g) for g in usable)),
    }
