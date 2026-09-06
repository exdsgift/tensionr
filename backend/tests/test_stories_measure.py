"""Three-state presence, denominators, floors, division and the balanced twin."""

import pytest

from tensionr.stories.measure import (
    ABSENT,
    PRESENT,
    UNRESOLVED,
    collapse_syndication,
    division,
    evidence,
    measure_story,
    top_band,
)


def row(domain, title, language="en", polity="A"):
    return {"domain": domain, "title": title, "language": language, "polity": polity}


def resolver(named_by: dict[str, str]):
    """Answer from a table keyed by domain, so tests state marks directly."""

    def resolve(title, actor, language=None):
        return named_by.get(f"{title}|{actor}", ABSENT)

    return resolve


def test_verbatim_reprints_collapse_to_one_voice():
    rows = [
        row("a.test", "Same wire headline"),
        row("b.test", "Same wire headline"),
        row("c.test", "Same Wire  Headline!"),
        row("d.test", "A different headline"),
    ]
    kept, collapsed = collapse_syndication(rows)
    assert [r["domain"] for r in kept] == ["a.test", "d.test"]
    assert collapsed == 2


def test_one_publisher_counts_once_even_with_two_headlines():
    rows = [row("a.test", "first"), row("a.test", "second")]
    kept, collapsed = collapse_syndication(rows)
    assert len(kept) == 1
    assert collapsed == 1


@pytest.mark.parametrize(
    "named,evaluable,expected",
    [(0, 10, 0.0), (10, 10, 0.0), (5, 10, 1.0), (0, 0, 0.0)],
)
def test_division_peaks_when_sources_are_split_evenly(named, evaluable, expected):
    assert division(named, evaluable) == pytest.approx(expected)


def test_division_ranks_an_even_split_above_a_near_universal_actor():
    assert division(50, 100) > division(95, 100)


def test_unresolved_leaves_the_denominator_rather_than_counting_as_absent():
    rows = [row(f"{i}.test", f"t{i}") for i in range(4)]
    marks = {
        "t0|iran": PRESENT,
        "t1|iran": PRESENT,
        "t2|iran": UNRESOLVED,
        "t3|iran": ABSENT,
    }
    out = measure_story(
        rows, ["iran"], resolver(marks), min_evaluable=1, min_polities=1
    )
    figure = out["figures"][0]

    assert figure["evaluable"] == 3, (
        "the undecidable row must not sit in the denominator"
    )
    assert figure["named"] == 2
    assert figure["unresolved"] == 1


def test_the_denominator_differs_between_actors_in_one_story():
    rows = [row("a.test", "t0"), row("b.test", "t1")]
    marks = {
        "t0|iran": PRESENT,
        "t1|iran": ABSENT,
        "t0|hormuz": PRESENT,
        "t1|hormuz": UNRESOLVED,
    }
    out = measure_story(
        rows, ["iran", "hormuz"], resolver(marks), min_evaluable=1, min_polities=1
    )
    assert [f["evaluable"] for f in out["figures"]] == [2, 1]


def test_a_story_below_the_polity_quorum_produces_no_figure():
    rows = [row(f"{i}.test", f"t{i}", polity="A") for i in range(40)]
    out = measure_story(rows, ["iran"], resolver({}), min_evaluable=1, min_polities=2)
    assert out["below_quorum"] is True
    assert out["figures"][0]["measurable"] is False
    assert out["figures"][0]["division"] is None
    assert out["figures"][0]["named"] == 0, (
        "raw counts survive; only the figure is withheld"
    )


def test_a_story_below_the_evaluable_floor_produces_no_figure():
    rows = [row(f"{i}.test", f"t{i}", polity="A" if i else "B") for i in range(10)]
    out = measure_story(rows, ["iran"], resolver({}), min_evaluable=30, min_polities=2)
    assert out["figures"][0]["measurable"] is False
    assert out["figures"][0]["division"] is None


def test_the_balanced_twin_weights_languages_not_sources():
    # eight English sources all naming the actor, two Arabic sources naming neither.
    # Pooled says 0.8; weighting the two languages equally says 0.5.
    rows = [row(f"e{i}.test", f"e{i}", language="en", polity="A") for i in range(8)]
    rows += [row(f"a{i}.test", f"a{i}", language="ar", polity="B") for i in range(2)]
    marks = {f"e{i}|iran": PRESENT for i in range(8)}
    out = measure_story(
        rows, ["iran"], resolver(marks), min_evaluable=1, min_polities=2
    )
    figure = out["figures"][0]

    assert figure["named"] / figure["evaluable"] == pytest.approx(0.8)
    assert figure["balanced_rate"] == pytest.approx(0.5)


def test_the_band_holds_every_row_that_leads_and_orders_none_of_them():
    figures = [
        {"actor": "b", "division": 0.900, "measurable": True},
        {"actor": "a", "division": 0.898, "measurable": True},
        {"actor": "c", "division": 0.700, "measurable": True},
        {"actor": "d", "division": None, "measurable": False},
    ]
    band = top_band(figures, tolerance=0.005)
    assert [f["actor"] for f in band] == ["a", "b"], (
        "alphabetical, so no rank is implied"
    )


def test_the_band_is_empty_when_nothing_is_measurable():
    assert top_band([{"actor": "a", "division": None, "measurable": False}]) == []


def test_a_band_of_zeros_is_no_band_at_all():
    # Found on live data: a story where nobody named any tracked actor put three
    # rows at division 0.000 into the band, headlining "nothing happened".
    figures = [
        {"actor": "iran", "division": 0.0, "measurable": True},
        {"actor": "trump", "division": 0.0, "measurable": True},
        {"actor": "israel", "division": 0.0, "measurable": True},
    ]
    assert top_band(figures) == []


def test_a_row_indistinguishable_from_undivided_does_not_lead():
    figures = [{"actor": "a", "division": 0.004, "measurable": True}]
    assert top_band(figures, tolerance=0.005) == []


def test_evidence_carries_one_row_per_voice_with_a_mark_per_actor():
    rows = [
        row("a.example", "Iran and Hormuz", polity="Iran"),
        row("b.example", "Iran and Hormuz", polity="Egypt"),  # verbatim reprint
        row("c.example", "Hormuz only", polity="Egypt"),
    ]
    resolve = resolver(
        {
            "Iran and Hormuz|iran": PRESENT,
            "Iran and Hormuz|hormuz": PRESENT,
            "Hormuz only|hormuz": PRESENT,
        }
    )
    ev = evidence(rows, ["hormuz", "iran"], resolve)

    # the reprint is collapsed, exactly as the figures collapse it
    assert [r["domain"] for r in ev] == ["c.example", "a.example"]
    assert ev[1]["marks"] == {"hormuz": PRESENT, "iran": PRESENT}
    assert ev[0]["marks"] == {"hormuz": PRESENT, "iran": ABSENT}


def test_evidence_groups_by_polity_and_puts_the_unplaced_last():
    rows = [
        row("z.example", "one", polity=None),
        row("m.example", "two", polity="Turkey"),
        row("a.example", "three", polity="Egypt"),
    ]
    ev = evidence(rows, ["iran"], resolver({}))
    assert [r["polity"] for r in ev] == ["Egypt", "Turkey", None]


def test_evidence_never_reports_two_states_where_the_resolver_gave_three():
    rows = [row("a.example", "\u0637\u0647\u0631\u0627\u0646", language="ar")]
    resolve = resolver({"\u0637\u0647\u0631\u0627\u0646|iran": UNRESOLVED})
    assert evidence(rows, ["iran"], resolve)[0]["marks"]["iran"] == UNRESOLVED


def test_every_figure_carries_its_counts_per_polity():
    """What a series over time is drawn from, and what nothing kept until now.

    The country test had this table for the band actor of a banded story and threw
    it away; no other figure had it at all. Only polities that could evaluate the
    actor appear, so a row unresolved everywhere leaves nothing rather than zeros.
    """
    rows = [
        row("a1.test", "a1", language="en", polity="A"),
        row("a2.test", "a2", language="en", polity="A"),
        row("b1.test", "b1", language="en", polity="B"),
        row("u1.test", "u1", language="xx", polity="C"),
    ]
    # The helper answers ABSENT to anything it was not told, so the unresolved row
    # has to be stated: it is the case the table must leave nothing behind for.
    marks = {
        "a1|iran": PRESENT,
        "a2|iran": ABSENT,
        "b1|iran": PRESENT,
        "u1|iran": UNRESOLVED,
    }
    out = measure_story(
        rows, ["iran"], resolver(marks), min_evaluable=1, min_polities=1
    )
    assert out["figures"][0]["by_polity"] == {"A": [1, 2], "B": [1, 1]}
