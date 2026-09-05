"""Reconstructing article bodies from n-grams: minute selection, filtering, assembly."""

import gzip
import json

from tensionr.stories.bodies import assemble, fragments, minutes_for


def ngram(url, pre, gram, post, pos=50):
    return json.dumps(
        {"url": url, "pre": pre, "ngram": gram, "post": post, "pos": pos, "lang": "en"}
    )


def payload(*lines):
    return gzip.compress("\n".join(lines).encode("utf-8"))


def test_a_wanted_minute_is_fetched_with_its_neighbours():
    """Only 76% of articles are in the file their heartbeat names; the rest are +/-1."""
    assert minutes_for(["2026-08-04T06:31"]) == [
        "20260804063000",
        "20260804063100",
        "20260804063200",
    ]


def test_the_minutes_of_many_sources_collapse_to_a_set():
    """A story's sources cluster on the quarter-hour, so the union is small."""
    stamps = ["2026-08-04T06:31", "2026-08-04T06:31", "2026-08-04T06:32"]
    assert minutes_for(stamps) == [
        "20260804063000",
        "20260804063100",
        "20260804063200",
        "20260804063300",
    ]


def test_the_first_and_last_minute_of_an_hour_do_not_wrap():
    assert minutes_for(["2026-08-04T06:00"]) == ["20260804060000", "20260804060100"]
    assert minutes_for(["2026-08-04T06:59"]) == ["20260804065800", "20260804065900"]


def test_an_unparseable_stamp_is_skipped_rather_than_guessed():
    assert minutes_for(["", None, "not a date", "2026"]) == []


def test_only_wanted_urls_are_kept():
    """Membership in a set, not a substring scan — the whole reason this exists.

    The package's own entry point tests every wanted URL as a substring of every record
    and did not finish in ten minutes on one real file with 263 of them.
    """
    raw = payload(
        ngram("https://a.example/1", "the", "quick", "brown"),
        ngram("https://b.example/2", "not", "wanted", "here"),
    )
    found = fragments(raw, {"https://a.example/1"})
    assert list(found) == ["https://a.example/1"]
    assert found["https://a.example/1"] == [(50, "the quick brown")]


def test_a_url_that_merely_contains_a_wanted_one_is_not_kept():
    """Substring matching would take this; exact membership does not."""
    raw = payload(ngram("https://a.example/1/amp", "x", "y", "z"))
    assert fragments(raw, {"https://a.example/1"}) == {}


def test_a_malformed_line_does_not_lose_the_file():
    raw = payload("{not json", ngram("https://a.example/1", "a", "b", "c"), "")
    assert len(fragments(raw, {"https://a.example/1"})["https://a.example/1"]) == 1


def test_the_end_glued_to_the_beginning_is_cut_at_the_slash():
    """The artifact the paper documents, which makes the overlap walk follow a false
    transition. Only applied near the start, where it does damage."""
    raw = payload(
        ngram("https://a.example/1", "tail of article /  the", "real", "start", pos=5)
    )
    text = fragments(raw, {"https://a.example/1"})["https://a.example/1"][0][1]
    assert text == "the real start"


def test_a_slash_late_in_an_article_is_left_alone():
    raw = payload(ngram("https://a.example/1", "half / half", "x", "y", pos=80))
    text = fragments(raw, {"https://a.example/1"})["https://a.example/1"][0][1]
    assert text == "half / half x y"


def test_fragments_merge_on_their_longest_overlap():
    pieces = [
        (10, "the quick brown fox jumps"),
        (20, "brown fox jumps over the lazy"),
        (30, "over the lazy dog and runs"),
    ]
    assert assemble(pieces) == "the quick brown fox jumps over the lazy dog and runs"


def test_assembly_is_deterministic_on_reordered_input():
    pieces = [
        (10, "alpha beta gamma delta"),
        (20, "gamma delta epsilon zeta"),
        (30, "epsilon zeta eta theta"),
    ]
    assert assemble(pieces) == assemble(list(reversed(pieces)))


def test_a_fragment_that_cannot_be_placed_stops_the_walk_rather_than_guessing():
    """The paper's rule: if nothing satisfies the position constraint with a positive
    overlap, reconstruction stops. Inventing an order would be worse than a short text."""
    pieces = [(10, "alpha beta gamma"), (90, "unrelated words entirely")]
    assert assemble(pieces) == "alpha beta gamma"


def test_a_later_fragment_cannot_be_prepended():
    """`pos` is too coarse to order fragments but sharp enough to refuse an
    end-of-article fragment landing before a beginning."""
    pieces = [(50, "middle of the piece"), (90, "the piece ends here")]
    joined = assemble(pieces)
    assert joined.startswith("middle of the piece")


def test_no_fragments_is_an_empty_string_not_an_error():
    assert assemble([]) == ""


def test_one_fragment_is_itself():
    assert assemble([(0, "a lone fragment")]) == "a lone fragment"
