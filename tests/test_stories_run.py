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


def test_boilerplate_loses_to_the_phrasing_the_others_share():
    """Longest is a bad proxy for descriptive: a masthead is long and says nothing.

    This put "Radio Station WHMI 93.5 FM - Livingston County Michigan News, Weather,
    Traffic" on the page as one of five featured headlines.
    """
    from tensionr.stories.run import _representative

    rows = [
        {
            "title": "Radio Station WHMI 93.5 FM - Livingston County Michigan News, "
            "Weather, Traffic and Community Information"
        },
        {"title": "Russia says seven killed as Ukrainian drone hits beach"},
        {"title": "Seven killed as Ukrainian drone hits Russian beach, Russia says"},
        {"title": "Russia: seven killed in Ukrainian drone strike on a beach"},
    ]
    assert "Radio Station" not in _representative(rows)["title"]


def test_a_title_cannot_vote_for_itself():
    """Otherwise the longest title wins by having more words to count."""
    from tensionr.stories.run import _representative

    rows = [
        {"title": "alpha beta gamma delta epsilon zeta eta theta iota kappa"},
        {"title": "shared words here"},
        {"title": "shared words here too"},
    ]
    assert _representative(rows)["title"].startswith("shared words here")


def test_the_fuller_title_wins_among_those_whose_words_the_others_used():
    """Fullest of the agreeing titles, not fullest overall.

    "in Geneva" is a detail one publisher had and the others did not, so it is discounted
    rather than rewarded: the headline should say what the coverage says, and a fact only
    one source carries belongs in that source's row, not in the page's own voice.
    """
    from tensionr.stories.run import _representative

    rows = [
        {"title": "Trump says talks resume"},
        {"title": "Trump says talks resume Monday in Geneva"},
        {"title": "Trump says talks resume Monday"},
    ]
    assert _representative(rows)["title"] == "Trump says talks resume Monday"


def test_a_detail_only_one_source_carries_does_not_decide_the_headline():
    from tensionr.stories.run import _representative

    rows = [
        {"title": "Seven killed in a drone strike on a beach"},
        {"title": "Seven killed in a drone strike on a beach in Zatoka, says governor"},
        {"title": "Seven killed in a drone strike on a beach"},
    ]
    assert "Zatoka" not in _representative(rows)["title"]


def test_no_rows_is_not_an_error():
    from tensionr.stories.run import _representative

    assert _representative([]) is None


def test_a_title_with_no_words_does_not_win():
    from tensionr.stories.run import _representative

    rows = [{"title": "..."}, {"title": "Trump says talks resume"}]
    assert _representative(rows)["title"] == "Trump says talks resume"


def _story(sid, division, band="hormuz", evidence=True):
    return {
        "id": sid,
        "headline": f"Story {sid}",
        "band": [band],
        "sources": 40,
        "polities": ["A", "B"],
        "figures": [{"actor": band, "division": division, "measurable": True}],
        "evidence": [{"url": f"https://{sid}.example/a"}] if evidence else [],
    }


def test_the_selection_ranks_by_the_widest_division_of_the_day():
    """#66: a story that led this morning keeps its standing in a quieter window."""
    from tensionr.stories.run import _feature

    stories = [_story("a", 0.20), _story("b", 0.90)]
    history = [{"stories": [{"id": "a", "division": 0.99}]}]
    _feature(stories, history, count=1)
    by_id = {s["id"]: s for s in stories}
    assert by_id["a"]["span_division"] == 0.99
    assert by_id["a"].get("featured") is True
    assert by_id["b"].get("featured") is None


def test_this_window_wins_when_it_is_the_widest_the_story_has_been():
    from tensionr.stories.run import _feature

    stories = [_story("a", 0.95)]
    _feature(stories, [{"stories": [{"id": "a", "division": 0.30}]}], count=1)
    assert stories[0]["span_division"] == 0.95


def test_a_candidate_the_window_no_longer_carries_is_counted_not_hidden():
    """That count is what decides whether rebuilding its evidence is worth building."""
    from tensionr.stories.run import _feature

    stories = [_story("live", 0.50)]
    history = [{"stories": [{"id": "gone", "division": 0.97}]}]
    span = _feature(stories, history, count=5)
    assert span["gone_from_the_window"] == 1
    assert span["widest_gone"] == 0.97
    assert span["candidates"] == 2


def test_no_history_selects_over_this_window_alone():
    from tensionr.stories.run import _feature

    stories = [_story("a", 0.40), _story("b", 0.80)]
    span = _feature(stories, [], count=1)
    assert span["runs_in_span"] == 0
    assert span["gone_from_the_window"] == 0
    assert [s["id"] for s in stories if s.get("featured")] == ["b"]


def test_the_index_carries_only_banded_stories_and_derives_their_urls():
    from tensionr.stories.run import _index

    payload = _index("20260804T000000Z", [_story("a", 0.9), _story("b", None)])
    ids = [r["id"] for r in payload["stories"]]
    assert ids == ["a", "b"]  # both have a band; division may be null
    assert payload["stories"][0]["urls"] == ["https://a.example/a"]


def test_a_story_with_no_band_is_not_in_the_index():
    from tensionr.stories.run import _index

    plain = _story("c", 0.5)
    plain["band"] = []
    assert _index("20260804T000000Z", [plain])["stories"] == []
