"""Drawing 512 dimensions on a plane, and refusing to when it would mislead.

The whole module exists on one condition: that adjacency on the plane means adjacency
in the space. These check that it is measured rather than hoped for, and that a
projection which fails the condition is not drawn.
"""

import numpy as np

from tensionr.stories.latent import GRID, MIN_AGREEMENT, POINTS_PER_STORY, project


def blobs(sizes: list[int], spread: float, seed: int = 0) -> tuple[list, np.ndarray]:
    """One cluster per entry in `sizes`. `spread` sets how much they overlap."""
    rng = np.random.default_rng(seed)
    centres = rng.normal(size=(len(sizes), 512))
    rows, groups, at = [], [], 0
    for i, n in enumerate(sizes):
        v = centres[i] + spread * rng.normal(size=(n, 512))
        rows.append(v / np.linalg.norm(v, axis=1, keepdims=True))
        groups.append(list(range(at, at + n)))
        at += n
    return groups, np.concatenate(rows).astype(np.float32)


class TestWhenItRefusesToDraw:
    def test_one_story_has_no_adjacency_to_be_about(self):
        groups, vectors = blobs([40], 0.3)
        assert project(groups, vectors) is None

    def test_a_story_of_one_article_cannot_be_a_shape(self):
        groups, vectors = blobs([1, 1], 0.3)
        assert project(groups, vectors) is None

    def test_a_projection_that_scrambles_the_neighbourhoods_is_not_drawn(self):
        # Stories sitting on top of each other in the space. There is no plane that
        # separates them, so any picture would invent a separation.
        groups, vectors = blobs([80] * 6, 8.0, seed=5)
        assert project(groups, vectors) is None

    def test_and_the_floor_is_the_one_it_publishes(self):
        groups, vectors = blobs([80, 80, 80], 0.2)
        drawn = project(groups, vectors)
        assert drawn is not None
        assert drawn["agreement"] >= MIN_AGREEMENT


class TestWhatItDraws:
    def test_separated_stories_survive_the_flattening(self):
        groups, vectors = blobs([120, 90, 60, 200, 45], 0.35)
        drawn = project(groups, vectors)
        assert drawn is not None
        assert drawn["agreement"] > 0.9
        assert 0.0 < drawn["retained"] <= 1.0

    def test_every_story_keeps_its_own_series_in_the_order_given(self):
        groups, vectors = blobs([30, 40, 50], 0.35)
        drawn = project(groups, vectors)
        assert [s["articles"] for s in drawn["stories"]] == [30, 40, 50]

    def test_a_long_story_is_sampled_and_says_so(self):
        groups, vectors = blobs([400, 40], 0.35)
        drawn = project(groups, vectors)
        big = drawn["stories"][0]
        assert big["articles"] == 400
        assert big["shown"] == POINTS_PER_STORY
        assert len(big["points"]) == POINTS_PER_STORY
        assert drawn["plotted"] == POINTS_PER_STORY + 40
        assert drawn["articles"] == 440

    def test_a_short_story_is_not_padded(self):
        groups, vectors = blobs([12, 40], 0.35)
        assert drawn_shown(project(groups, vectors), 0) == 12

    def test_coordinates_are_integers_inside_the_published_grid(self):
        groups, vectors = blobs([60, 60, 60], 0.35)
        drawn = project(groups, vectors)
        every = [p for s in drawn["stories"] for p in s["points"]]
        assert drawn["grid"] == GRID
        assert all(isinstance(v, int) for p in every for v in p)
        assert all(0 <= v <= GRID for p in every for v in p)

    def test_the_same_run_drawn_twice_is_the_same_picture(self):
        groups, vectors = blobs([300, 80, 55], 0.35)
        assert project(groups, vectors) == project(groups, vectors)


def drawn_shown(drawn: dict, index: int) -> int:
    return drawn["stories"][index]["shown"]
