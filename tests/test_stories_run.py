"""The capture: what is kept, and what is not kept twice."""

from tensionr.stories.run import _capture

RECORDS = [
    {
        "url": "https://a.test/1",
        "title": "One",
        "domain": "a.test",
        "language": "ENGLISH",
        "seen_at": "2026-08-02T10:00:00Z",
        "embedding": [0.0] * 512,
    },
    {
        "url": "https://b.test/2",
        "title": "Two",
        "domain": "b.test",
        "language": "ARABIC",
        "seen_at": "2026-08-02T10:05:00Z",
        "embedding": [0.0] * 512,
    },
]


def test_only_the_irrecoverable_fields_are_kept():
    # Embeddings are a function of the title and can be recomputed; keeping them
    # would cost 660 MB/day against roughly 19.
    kept = _capture(RECORDS, set())
    assert set(kept[0]) == {"url", "title", "domain", "language", "seen_at"}


def test_an_article_the_previous_window_already_captured_is_not_captured_again():
    # Windows overlap and each run writes an immutable file, so without this an
    # article seen twice is stored twice for ever.
    kept = _capture(RECORDS, {"https://a.test/1"})
    assert [r["url"] for r in kept] == ["https://b.test/2"]


def test_a_fully_overlapping_window_captures_nothing():
    assert _capture(RECORDS, {r["url"] for r in RECORDS}) == []
