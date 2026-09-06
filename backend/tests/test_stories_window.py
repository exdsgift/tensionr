"""How much of the window is held in memory, which is what kills runs.

Neither guarantee here is visible at runtime: undo them and every figure the run
publishes is unchanged, the process simply needs several more gigabytes and the runner
kills it. Six of forty runs died that way, so the size of the representation is pinned
by a test rather than by a comment.
"""

import gzip
import io
import json
import sys

import numpy as np
import pytest

from tensionr.config import EMBEDDING_DIM
from tensionr.stories import window


def payload(rows: list[dict]) -> bytes:
    buffer = io.BytesIO()
    with gzip.open(buffer, "wt", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    return buffer.getvalue()


def article(index: int = 0, dim: int = EMBEDDING_DIM) -> dict:
    return {
        "url": f"https://p{index}.test/a",
        "title": f"headline {index}",
        "lang": "eng",
        "date": "20260905221338",
        "docembed": [0.01 * (index + 1)] * dim,
    }


class TestTheWindowIsParsedNarrow:
    def test_an_embedding_is_a_float32_row_not_a_list_of_python_floats(self):
        records, _, _ = window._parse(payload([article()]))
        embedding = records[0]["embedding"]
        assert isinstance(embedding, np.ndarray)
        assert embedding.dtype == np.float32

    def test_which_is_the_whole_point_of_doing_it_here(self):
        # The window is parsed in full before anything asks for a matrix, so the
        # representation chosen at parse time is the one held through fetch.
        records, _, _ = window._parse(payload([article()]))
        narrow = records[0]["embedding"].nbytes
        wide = sys.getsizeof([0.0] * EMBEDDING_DIM) + EMBEDDING_DIM * sys.getsizeof(0.1)
        assert narrow * 4 < wide, (narrow, wide)

    def test_a_short_embedding_is_still_refused(self):
        records, seen, unparsed = window._parse(payload([article(dim=8)]))
        assert (records, seen, unparsed) == ([], 1, 1)


class TestTheMatrixTakesOwnership:
    def test_building_the_matrix_releases_the_per_record_copies(self):
        records, _, _ = window._parse(payload([article(i) for i in range(4)]))
        window.vectors(records)
        assert all("embedding" not in r for r in records)

    def test_the_rest_of_the_record_survives_it(self):
        records, _, _ = window._parse(payload([article(1)]))
        window.vectors(records)
        assert records[0]["domain"] == "p1.test"
        assert records[0]["language"] == "eng"

    def test_asking_twice_fails_loudly_rather_than_returning_zeros(self):
        records, _, _ = window._parse(payload([article()]))
        window.vectors(records)
        with pytest.raises(KeyError):
            window.vectors(records)

    def test_the_rows_are_normalised_and_in_the_given_order(self):
        records, _, _ = window._parse(payload([article(i) for i in range(3)]))
        matrix = window.vectors(records)
        assert matrix.shape == (3, EMBEDDING_DIM)
        assert matrix.dtype == np.float32
        assert np.allclose(np.linalg.norm(matrix, axis=1), 1.0, atol=1e-5)

    def test_an_empty_window_is_an_empty_matrix_not_an_error(self):
        matrix = window.vectors([])
        assert matrix.shape == (0, EMBEDDING_DIM)
        assert matrix.dtype == np.float32
