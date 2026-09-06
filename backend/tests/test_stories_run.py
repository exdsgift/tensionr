"""The capture: what is kept, and what is not kept twice."""

from tensionr.stories.run import (
    _accumulate,
    _by_country,
    _capture,
    _feature,
    _feed,
    _index,
    _publishable,
)

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


class TestSeriesAndSelectionAreDifferentWindows:
    """A featured story's published line may reach further back than the selection does.

    These are two claims with two spans: the selection says "the most divided stories of
    today", the series says "here is this story's life". Loading a week of history to
    draw the second must not let a five-day-old peak decide the first.
    """

    @staticmethod
    def _history():
        # 30 hours apart: outside the 24-hour selection window, inside the 7-day series.
        return [
            {
                "run": "20260901T000000Z",
                "stories": [{"id": "a", "division": 0.99, "sources": 10}],
            },
            {
                "run": "20260902T060000Z",
                "stories": [{"id": "a", "division": 0.10, "sources": 12}],
            },
        ]

    def test_a_peak_outside_the_span_does_not_decide_what_is_featured(self):
        stories = [
            {"id": "a", "band": ["x"], "figures": [{"actor": "x", "division": 0.10}]}
        ]
        _feature(stories, self._history(), count=1)
        # 0.99 is older than SPAN_HOURS, so the story is ranked on what it is now.
        assert stories[0]["span_division"] == 0.1

    def test_the_same_run_still_appears_in_the_series(self):
        stories = [
            {"id": "a", "band": ["x"], "figures": [{"actor": "x", "division": 0.10}]}
        ]
        _feature(stories, self._history(), count=1)
        assert [p["division"] for p in stories[0]["series"]] == [0.99, 0.10]

    def test_a_run_that_did_not_carry_the_story_contributes_no_point(self):
        # Absence and a division of zero are different claims. A line that dropped to
        # the floor whenever a story was not carried would invent a fall that never
        # happened.
        history = self._history()
        history.insert(1, {"run": "20260901T120000Z", "stories": []})
        stories = [
            {"id": "a", "band": ["x"], "figures": [{"actor": "x", "division": 0.10}]}
        ]
        _feature(stories, history, count=1)
        assert len(stories[0]["series"]) == 2

    def test_only_featured_stories_carry_a_series(self):
        history = [
            {
                "run": "20260902T060000Z",
                "stories": [
                    {"id": "a", "division": 0.90, "sources": 10},
                    {"id": "b", "division": 0.10, "sources": 10},
                ],
            }
        ]
        stories = [
            {"id": "a", "band": ["x"], "figures": [{"actor": "x", "division": 0.90}]},
            {"id": "b", "band": ["x"], "figures": [{"actor": "x", "division": 0.10}]},
        ]
        _feature(stories, history, count=1)
        assert "series" in stories[0]
        assert "series" not in stories[1]


def _banded(sid: str, division: float, *, p: float | None = None, powered: bool = True):
    """A story with a country-test verdict attached, or none at all."""
    story = _story(sid, division)
    if p is not None:
        story["structure"] = {
            "sources": 60,
            "polities": 8,
            "p": p,
            "floor": 0.0005,
            "powered": powered,
            "by_polity": [],
        }
    return story


class TestWhatGetsTheTopOfThePage:
    """Ranked by what the country test could show, then by division inside that.

    `division` is the binary entropy of the naming rate and peaks at one half, which is
    exactly what a coin gives, so it cannot tell a story that splits *by country* from
    one that splits at random. Measured by recomputing the test over 25 published runs
    and 467 banded stories: of 125 featured slots, 45 were shown to split by country and
    10 had been tested and shown not to, while 39 stories that were shown to split never
    reached the page at all. Reordered, the same runs carry 76 and none.

    Entropy is not discarded. At a division above 0.9, 42.7% of stories tested
    structured against 2.3% below 0.3, so it is a real signal and it orders within a
    band rather than across bands.
    """

    def test_a_shown_split_outranks_a_wider_one_that_was_only_untestable(self):
        stories = [_banded("wide", 0.99), _banded("shown", 0.61, p=0.001)]
        _feature(stories, [], count=2)
        assert [s["id"] for s in sorted(stories, key=lambda s: s["rank"])] == [
            "shown",
            "wide",
        ]

    def test_and_a_refuted_one_comes_last_however_wide_it_is(self):
        # Tested with power and found not to follow a country line. That is a closed
        # question, and it loses to an open one.
        stories = [
            _banded("refuted", 0.99, p=0.80),
            _banded("untold", 0.40),
            _banded("shown", 0.30, p=0.01),
        ]
        _feature(stories, [], count=3)
        assert [s["id"] for s in sorted(stories, key=lambda s: s["rank"])] == [
            "shown",
            "untold",
            "refuted",
        ]

    def test_an_underpowered_test_is_untold_and_not_refuted(self):
        # A test that could not have detected a split is not evidence there is none.
        stories = [
            _banded("weak", 0.40, p=0.90, powered=False),
            _banded("strong", 0.90, p=0.90, powered=True),
        ]
        _feature(stories, [], count=2)
        assert [s["id"] for s in sorted(stories, key=lambda s: s["rank"])] == [
            "weak",
            "strong",
        ]

    def test_division_still_orders_inside_a_band(self):
        stories = [_banded("narrow", 0.30, p=0.01), _banded("wide", 0.95, p=0.01)]
        _feature(stories, [], count=2)
        assert [s["id"] for s in sorted(stories, key=lambda s: s["rank"])] == [
            "wide",
            "narrow",
        ]

    def test_the_run_publishes_how_many_of_the_five_it_could_speak_to(self):
        # The page says this rather than presenting five findings when it has one.
        stories = [
            _banded("a", 0.90, p=0.01),
            _banded("b", 0.80),
            _banded("c", 0.70, p=0.60),
        ]
        span = _feature(stories, [], count=3)
        assert (span["shown"], span["untold"], span["refuted"]) == (1, 1, 1)


class TestTheRecordKeepsWhatCannotBeRebuilt:
    """The index stores the country test's verdict, and deliberately not its table.

    `_index`'s rule is that anything derivable from the capture is derived rather than
    stored twice. That held while the capture was permanent. It is not any more:
    captures live on a 20-day rolling window, so a verdict that is only derivable
    expires with the articles it came from.

    This was not hypothetical. Deciding whether ranking on `division` was putting coin
    flips on the page needed the test across 25 past runs, and answering it meant
    rejoining every index to its capture and recomputing all 467 verdicts. Three weeks
    later the question would have had no answer: the inputs gone, the outputs never
    written down.
    """

    def rows(self):
        stories = [
            _banded("shown", 0.90, p=0.001),
            _banded("untold", 0.80),
            _banded("refuted", 0.70, p=0.90),
        ]
        _feature(stories, [], count=2)
        return {r["id"]: r for r in _index("20260906T111742Z", stories)["stories"]}

    def test_the_verdict_survives_the_capture_it_came_from(self):
        found = self.rows()["shown"]["structure"]
        assert found == {"p": 0.001, "powered": True, "sources": 60, "polities": 8}

    def test_a_story_the_test_could_not_reach_records_that_as_an_absence(self):
        # None is the answer, not a missing key: the question was asked and could not
        # be put. A later reader must be able to tell that from "never tested".
        assert self.rows()["untold"]["structure"] is None

    def test_a_refuted_story_records_its_refusal_rather_than_dropping_it(self):
        found = self.rows()["refuted"]["structure"]
        assert found["p"] == 0.90 and found["powered"] is True

    def test_the_per_polity_table_is_not_stored(self):
        # It is a presentation of evidence the capture still carries while it lasts,
        # and it is the only part of the verdict that grows with the story.
        assert "by_polity" not in self.rows()["shown"]["structure"]

    def test_where_the_run_put_it_is_recorded_too(self):
        rows = self.rows()
        assert rows["shown"]["rank"] == 0
        assert rows["refuted"]["rank"] is None  # not featured, so it has no position


class TestOnlyFiguresThatAreFigures:
    """A figure with nothing measurable in it is not published.

    One is produced per actor per story, and on a real run 19,469 of 19,880 said only
    "we could not measure this here": 69% of stories.json to carry a `null`. The page
    has never read them, and dropping them was verified to render a byte-identical
    page.
    """

    def figures(self):
        return [
            {"actor": "iran", "named": 20, "evaluable": 40, "measurable": True},
            {"actor": "ceuta", "named": 0, "evaluable": 3, "measurable": False},
            {"actor": "gaza", "named": 0, "evaluable": 0, "measurable": False},
        ]

    def test_an_unmeasurable_figure_is_dropped(self):
        assert [f["actor"] for f in _publishable(self.figures())] == ["iran"]

    def test_a_figure_with_no_verdict_is_kept_rather_than_guessed_at(self):
        # Absent `measurable` is not `measurable: false`. Only an explicit refusal
        # drops a row, so a shape this rule has not seen survives instead of vanishing.
        kept = _publishable([{"actor": "x", "named": 1, "evaluable": 2}])
        assert len(kept) == 1

    def test_nothing_measurable_is_an_empty_list_not_a_missing_key(self):
        assert _publishable([f for f in self.figures() if not f["measurable"]]) == []


class TestTheSeriesAccumulates:
    """Per actor and per polity by day, carried on the data ref like the state.

    The engine only ever sees nine days of indexes, and a series has to reach further
    than that, so it is accumulated run to run rather than rebuilt. By day and not by
    run: the first shape kept a point per run with its stamp on every point, and
    backfilled over 93 runs it was 10.2 MB, 6.1 MB of which was the same stamps written
    355,218 times.
    """

    def test_a_first_run_starts_the_series_on_its_day(self):
        out = _accumulate(None, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        assert out["index"] == ["2026-09-06"]
        assert out["actors"] == {"putin": {"Italy": [[0, 3, 5]]}}
        assert out["runs"] == ["20260906T120000Z"]

    def test_a_second_run_on_the_same_day_adds_into_it(self):
        first = _accumulate(None, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        second = _accumulate(first, "20260906T160000Z", {"putin": {"Italy": [4, 6]}})
        assert second["index"] == ["2026-09-06"]
        assert second["actors"]["putin"]["Italy"] == [[0, 7, 11]]

    def test_a_run_on_the_next_day_opens_a_new_point_in_order(self):
        first = _accumulate(None, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        second = _accumulate(first, "20260907T020000Z", {"putin": {"Italy": [1, 2]}})
        assert second["index"] == ["2026-09-06", "2026-09-07"]
        assert second["actors"]["putin"]["Italy"] == [[0, 3, 5], [1, 1, 2]]

    def test_rerunning_the_same_instant_is_a_no_op_not_a_double_count(self):
        first = _accumulate(None, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        again = _accumulate(first, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        assert again == first

    def test_a_run_that_arrives_out_of_order_lands_in_its_day(self):
        late = _accumulate(None, "20260907T160000Z", {"putin": {"Italy": [4, 6]}})
        fixed = _accumulate(late, "20260906T120000Z", {"putin": {"Italy": [3, 5]}})
        assert fixed["index"] == ["2026-09-06", "2026-09-07"]
        assert fixed["actors"]["putin"]["Italy"] == [[0, 3, 5], [1, 4, 6]]

    def test_the_window_drops_days_older_than_it(self):
        old = _accumulate(None, "20260501T000000Z", {"putin": {"Italy": [1, 1]}})
        now = _accumulate(
            old, "20260906T120000Z", {"putin": {"Italy": [3, 5]}}, days=90
        )
        assert now["index"] == ["2026-09-06"]
        assert now["runs"] == ["20260906T120000Z"]

    def test_a_polity_with_nothing_left_disappears_rather_than_lingering_empty(self):
        old = _accumulate(None, "20260501T000000Z", {"putin": {"Italy": [1, 1]}})
        now = _accumulate(old, "20260906T120000Z", {"iran": {"Spain": [2, 2]}}, days=90)
        assert "putin" not in now["actors"]

    def test_the_run_aggregate_sums_across_stories(self):
        stories = [
            {
                "figures": [
                    {"actor": "putin", "by_polity": {"Italy": [1, 2], "Spain": [0, 1]}}
                ]
            },
            {"figures": [{"actor": "putin", "by_polity": {"Italy": [2, 3]}}]},
        ]
        assert _by_country(stories) == {"putin": {"Italy": [3, 5], "Spain": [0, 1]}}

    def test_the_published_figure_leaves_the_table_behind(self):
        # It goes to the index and is summed there; on stories.json it would repeat
        # thirty rows per story that the page never breaks down.
        kept = _publishable(
            [{"actor": "x", "measurable": True, "by_polity": {"A": [1, 1]}}]
        )
        assert "by_polity" not in kept[0]


class TestTheFeedSaysWhenASplitIsFirstShown:
    """One entry when a story enters the shown band, and nothing else.

    Division moves every run and a feed of that would be noise. The one change this
    project can vouch for is a story whose split was just shown to follow a country
    line, so that is the only event.
    """

    def test_a_story_shown_now_and_not_before_is_an_entry(self):
        now = [_banded("a", 0.9, p=0.001)]
        past = [
            {
                "run": "20260906T080000Z",
                "stories": [{"id": "a", "structure": {"p": 0.6}}],
            }
        ]
        actor = now[0]["band"][0]
        feed = _feed("20260906T120000Z", now, past, {actor: "Actor X"})
        assert feed.count("<entry>") == 1
        assert "Actor X" in feed

    def test_a_story_already_shown_is_not_repeated(self):
        now = [_banded("a", 0.9, p=0.001)]
        past = [
            {
                "run": "20260906T080000Z",
                "stories": [{"id": "a", "structure": {"p": 0.01}}],
            }
        ]
        assert "<entry>" not in _feed("20260906T120000Z", now, past, {})

    def test_an_untold_or_refuted_story_is_never_an_entry(self):
        now = [_banded("a", 0.9), _banded("b", 0.8, p=0.7)]
        assert "<entry>" not in _feed("20260906T120000Z", now, [], {})

    def test_history_without_verdicts_has_no_opinion(self):
        # Indexes from before the verdict field cannot say a story was shown, so the
        # first run after this lands emits a batch: the honest start, not a silent one.
        now = [_banded("a", 0.9, p=0.001)]
        past = [{"run": "20260906T080000Z", "stories": [{"id": "a"}]}]
        assert _feed("20260906T120000Z", now, past, {}).count("<entry>") == 1

    def test_the_feed_is_well_formed_and_escapes_the_headline(self):
        import xml.dom.minidom

        story = _banded("a", 0.9, p=0.001)
        story["headline"] = 'Q&A: "who" <named> it'
        feed = _feed("20260906T120000Z", [story], [], {})
        xml.dom.minidom.parseString(feed)
        assert "&amp;" in feed and "&lt;named&gt;" in feed
