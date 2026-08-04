"""Rendering the Ledger: projection, marker states, and what the page may claim."""

import json

from tensionr.ledger import (
    FEATURED,
    LEDGER_BUDGET_BYTES,
    cell,
    evidence_table,
    headline,
    labels,
    panel,
    render,
    row_counts,
    since_previous,
    source_link,
    transfer_bytes,
)
from tensionr.stories.marks import ABSENT, PRESENT, UNRESOLVED

# The real file's shape, small enough to reason about: 4 cells wide, 2 tall.
PROJECTION = {
    "width": 4,
    "height": 2,
    "lat_top": 80.0,
    "lat_bottom": -80.0,
    "lon_left": -180.0,
    "lon_right": 180.0,
    "rows": ["⠿⠿⠿⠿", "⠿⠿⠿⠿"],
}

COORDS = {"Iran": [35.7, 51.4], "Spain": [40.4, -3.7], "Chile": [-33.5, -70.7]}
NAMES = {"hormuz": "Strait of Hormuz"}


def source(domain, polity, marks, title="a headline", language="en", url=None):
    return {
        "url": url if url is not None else f"https://{domain}/a-story",
        "domain": domain,
        "polity": polity,
        "language": language,
        "title": title,
        "marks": marks,
    }


def story(**over):
    base = {
        "id": "s-1",
        "headline": "A headline about the strait",
        "band": ["hormuz"],
        "sources": 3,
        "collapsed": 1,
        "polities": ["Iran", "Spain"],
        "below_quorum": False,
        "figures": [
            {
                "actor": "hormuz",
                "named": 2,
                "evaluable": 3,
                "unresolved": 0,
                "division": 0.9183,
                "balanced_rate": 0.5,
                "measurable": True,
            }
        ],
        "evidence": [
            source("a.ir", "Iran", {"hormuz": PRESENT}),
            source("b.es", "Spain", {"hormuz": ABSENT}),
            source("c.es", "Spain", {"hormuz": ABSENT}),
        ],
    }
    return {**base, **over}


def run(stories):
    return {
        "run": "20260802T223324Z",
        "stories": stories,
        "report": {
            "window": {"slots": 24, "articles": 54516, "parse_fidelity": 1.0},
            "grouping": {"themes": 427, "stories": 286},
            "polities": {"domains": 6706, "placed": 2799, "rate": 0.4174},
            "floors": {"evaluable": 30, "polities": 2},
            "previous_run": "20260802T213324Z",
            "published": {"stories": 286, "with_a_band": 1},
        },
    }


def test_the_projection_comes_from_the_map_not_from_a_constant():
    # The centre of the lon range sits at the middle column, the top edge at row 0.
    assert cell(80.0, 0.0, PROJECTION) == (2.0, 0.0)
    assert cell(-80.0, 180.0, PROJECTION) == (4.0, 2.0)


def test_a_different_crop_moves_every_point():
    """The prototype's bug: the crop was stated twice and the two disagreed."""
    wider = {**PROJECTION, "lat_top": 90.0, "lat_bottom": -90.0}
    assert cell(45.0, 0.0, PROJECTION) != cell(45.0, 0.0, wider)


def test_a_polity_that_named_the_actor_is_filled_and_one_that_did_not_is_hollow():
    marks, plotted = panel(story(), COORDS, PROJECTION)
    assert plotted == 2
    by_polity = {m["n"].split(" · ")[0]: m for m in marks}
    assert by_polity["Iran"]["on"] is True
    assert by_polity["Spain"]["on"] is False
    assert "did not name" in by_polity["Spain"]["n"]


def test_a_polity_absent_from_the_story_is_not_plotted_at_all():
    """Marking it silent would claim it should have carried the story (#20)."""
    marks, _ = panel(story(), COORDS, PROJECTION)
    assert "Chile" not in {m["n"].split(" · ")[0] for m in marks}


def test_a_polity_with_no_coordinate_is_counted_but_not_plotted():
    s = story(evidence=[source("a.xx", "Narnia", {"hormuz": PRESENT})])
    marks, plotted = panel(s, COORDS, PROJECTION)
    assert marks == []
    assert plotted == 1


def test_unplaced_sources_appear_in_the_table_rather_than_vanishing():
    s = story(evidence=[source("a.xx", None, {"hormuz": PRESENT})])
    table = evidence_table(s, NAMES)
    assert "a.xx" in table
    assert "—" in table


def test_the_third_state_is_rendered_as_itself_and_not_as_an_absence():
    s = story(evidence=[source("a.ir", "Iran", {"hormuz": UNRESOLVED})])
    table = evidence_table(s, NAMES)
    assert "–" in table and "ne" in table
    assert "●" not in table


def test_the_page_leads_with_the_widest_split():
    thin = story(
        id="s-2",
        headline="A narrower one",
        figures=[
            {
                "actor": "hormuz",
                "named": 1,
                "evaluable": 10,
                "unresolved": 0,
                "division": 0.1,
                "balanced_rate": 0.1,
                "measurable": True,
            }
        ],
    )
    page = render(run([thin, story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert page.index("A headline about the strait") < page.index("A narrower one")


def test_a_run_with_nothing_measurable_still_renders_and_says_so():
    """A window below the floors is an outcome, not a broken build (#6)."""
    page = render(
        run([story(band=[], evidence=[])]), PROJECTION, COORDS, TEMPLATE, NAMES
    )
    assert "@@" not in page
    assert "Nothing cleared the floors in this window" in page
    assert "no row to show" in page
    # the floors named are the ones the run applied, not a copy kept by the page
    assert "30 evaluable sources across 2 polities" in page


def test_a_run_that_never_published_its_floors_does_not_invent_them():
    r = run([story(band=[], evidence=[])])
    del r["report"]["floors"]
    page = render(r, PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "this project's floors" in page
    assert "None" not in page
    # and no figure is printed, because there is none to print
    assert "sources named" not in page


def test_a_run_with_nothing_measurable_plots_no_polities():
    page = render(
        run([story(band=[], evidence=[])]), PROJECTION, COORDS, TEMPLATE, NAMES
    )
    assert "const PANEL=[]," in page
    assert "no polities plotted" in page


def test_the_column_heads_appear_only_when_there_are_rows():
    empty = render(
        run([story(band=[], evidence=[])]), PROJECTION, COORDS, TEMPLATE, NAMES
    )
    full = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "colhead" in full
    assert "colhead" not in empty


def test_the_split_sentence_is_only_written_when_the_split_is_clean():
    """Named by some in every polity is not "every ... none of ..." and must not say so."""
    mixed = story(
        evidence=[
            source("a.ir", "Iran", {"hormuz": PRESENT}),
            source("b.ir", "Iran", {"hormuz": ABSENT}),
            source("c.es", "Spain", {"hormuz": PRESENT}),
            source("d.es", "Spain", {"hormuz": ABSENT}),
        ]
    )
    page = render(run([mixed]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "Every source in" not in page


def test_every_placeholder_is_filled():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "@@" not in page


def test_the_map_size_the_script_uses_is_the_map_that_was_drawn():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "W=4, H=2" in page


def test_row_counts_flags_a_low_naming_rate():
    quiet = story(
        figures=[
            {
                "actor": "hormuz",
                "named": 2,
                "evaluable": 10,
                "unresolved": 0,
                "division": 0.72,
                "balanced_rate": 0.2,
                "measurable": True,
            }
        ]
    )
    assert "miss" in row_counts(quiet, NAMES)
    loud = story(
        figures=[
            {
                "actor": "hormuz",
                "named": 9,
                "evaluable": 10,
                "unresolved": 0,
                "division": 0.4,
                "balanced_rate": 0.9,
                "measurable": True,
            }
        ]
    )
    assert "miss" not in row_counts(loud, NAMES)


def test_the_balanced_twin_is_published_beside_the_figure():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "every language counts" in page


TEMPLATE = """<!doctype html><title>t</title>
<span class="when">@@WHEN@@</span>
<div class="hook"><div>
@@HOOK@@
</div></div>
<pre id="globe">@@MAP@@</pre>
<pre id="globe-n">@@MAP_N@@</pre>
<div class="cap">@@LEGEND@@</div>
<div class="agg">@@BANDED@@ of @@STORIES@@ · @@ARTICLES@@ · @@POLITY_RATE@@ · @@SLOTS@@ · @@SINCE@@</div>
@@ROWS@@
<div class="foot">@@FOOT@@</div>
<script>const PANEL=@@PANEL@@, W=@@MAP_W@@, H=@@MAP_H@@;
const PANEL_N=@@PANEL_N@@, W_N=@@MAP_N_W@@, H_N=@@MAP_N_H@@;</script>
"""


def test_the_marks_are_valid_json_for_the_script():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    payload = page.split("const PANEL=")[1].split(", W=")[0]
    assert isinstance(json.loads(payload), list)


def test_the_page_prints_the_curated_label_not_a_titlecased_slug():
    """`hormuz` is the Strait of Hormuz and `trump` is Donald Trump (#22)."""
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "Strait of Hormuz" in page
    # the bare titlecased slug must not appear as a label of its own
    assert ">Hormuz<" not in page


def test_an_actor_with_no_curated_label_still_reads_as_a_name():
    page = render(
        run(
            [
                story(
                    band=["white-house"],
                    figures=[
                        {
                            "actor": "white-house",
                            "named": 2,
                            "evaluable": 3,
                            "unresolved": 0,
                            "division": 0.9183,
                            "balanced_rate": 0.5,
                            "measurable": True,
                        }
                    ],
                    evidence=[source("a.ir", "Iran", {"white-house": PRESENT})],
                )
            ]
        ),
        PROJECTION,
        COORDS,
        TEMPLATE,
        {},
    )
    assert "White House" in page


def test_labels_are_optional_and_absent_seeds_are_not_an_error(tmp_path):
    assert labels(tmp_path) == {}


NARROW = {
    "width": 2,
    "height": 1,
    "lat_top": 80.0,
    "lat_bottom": -80.0,
    "lon_left": -180.0,
    "lon_right": 180.0,
    "rows": ["⠿⠿"],
}


def test_the_narrow_map_gets_its_own_markers_from_its_own_projection():
    """A marker computed against the wrong map is the #41 defect, twice over."""
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES, narrow=NARROW)
    wide = json.loads(page.split("const PANEL=")[1].split(", W=")[0])
    thin = json.loads(page.split("const PANEL_N=")[1].split(", W_N=")[0])
    assert [m["n"] for m in wide] == [m["n"] for m in thin]
    # half the columns and half the rows, so every column and row halves with them
    # (to the rounding both sets are published at)
    by_name = {m["n"]: m for m in wide}
    for mark in thin:
        assert abs(mark["c"] - by_name[mark["n"]]["c"] / 2) <= 0.01, mark["n"]
        assert abs(mark["r"] - by_name[mark["n"]]["r"] / 2) <= 0.01, mark["n"]


def test_one_map_is_used_for_every_width_when_only_one_was_given():
    """A caller with a single rasterisation gets it everywhere, not an empty map."""
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "W=4, H=2" in page and "W_N=4, H_N=2" in page
    assert (
        page.split("const PANEL=")[1].split(", W=")[0]
        == page.split("const PANEL_N=")[1].split(", W_N=")[0]
    )


def test_the_narrow_map_carries_its_own_size_into_the_script():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES, narrow=NARROW)
    assert "W=4, H=2" in page
    assert "W_N=2, H_N=1" in page


def test_the_evidence_scroller_can_be_reached_without_a_pointer():
    """A region only a finger can scroll fails SC 2.1.1, and Safari does not help."""
    table = evidence_table(story(), NAMES)
    assert 'tabindex="0"' in table
    assert 'role="region"' in table
    # named by pointing at the table's own caption rather than repeating the string
    caption_id = table.split('aria-labelledby="')[1].split('"')[0]
    assert f'id="{caption_id}"' in table
    assert "<caption " in table and caption_id.startswith("ev-cap-")


def test_the_marks_columns_are_headers_of_their_columns():
    table = evidence_table(story(), NAMES)
    assert table.count('scope="col"') == 3 + len(story()["band"])


def test_two_tables_on_one_page_do_not_share_a_caption_id():
    page = render(run(many(3)), PROJECTION, COORDS, TEMPLATE, NAMES)
    ids = [chunk.split('"')[0] for chunk in page.split('<caption class="vh" id="')[1:]]
    assert len(ids) == 3
    assert len(set(ids)) == 3


def test_the_real_template_leaves_no_placeholder_behind():
    """The fixture template only carries the placeholders the fixtures know about.

    So it cannot catch a placeholder added to the shipped template and never filled —
    which is exactly what a second map introduced four of.
    """
    from importlib import resources

    tpl = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    page = render(run([story()]), PROJECTION, COORDS, tpl, NAMES, narrow=NARROW)
    assert "@@" not in page


def test_the_grid_tracks_have_one_definition_for_the_heads_and_the_rows():
    """The heads aligning with their cells is a property of there being one --cols.

    A second `grid-template-columns` on `.colhead` or `.grid` is how they drift apart at
    a width nobody tested, which is the complaint that produced `--cols` in review.
    """
    from importlib import resources

    tpl = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    assert tpl.count("grid-template-columns:var(--cols)") == 1
    assert ".colhead{display:grid" not in tpl
    # and no track list may be spelled `1fr` on its own: that is minmax(auto,1fr), whose
    # content-based minimum is what let the map drag the page wider than the viewport
    for line in tpl.splitlines():
        if "grid-template-columns:" in line:
            assert "grid-template-columns:1fr" not in line.replace(" ", ""), line


def test_the_real_template_is_a_complete_document():
    """It is the homepage now. The prototype relied on an artifact wrapper for this."""
    from importlib import resources

    tpl = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    assert tpl.lstrip().startswith("<!doctype html>")
    for required in (
        '<html lang="en">',
        '<meta charset="utf-8">',
        '<meta name="viewport"',
        "<title>",
        "</body>",
        "</html>",
    ):
        assert required in tpl, required


def test_the_rendered_page_declares_its_encoding_before_any_braille():
    """Without a charset the map and non-Latin headlines are at the browser's mercy."""
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "@@" not in page


# Small enough to bite on the synthetic fixture, whose near-identical headlines compress
# far better than real ones: 40 stories with 5 featured come to 10.23 KB gzipped here
# once each source carries its URL, against 4.49 KB before #61. Measured each time it
# moves, not guessed — an earlier value of 10 KB was above the page's own weight, so the
# drop path was never exercised and the tests passed while proving nothing.
BITES = 8 * 1024


def many(n):
    """n banded stories, each with enough sources to make the page heavy."""
    out = []
    for i in range(n):
        ev = [
            source(
                f"d{j}.example",
                "Iran" if j % 2 else "Spain",
                {"hormuz": PRESENT},
                title=f"A headline number {j} about the strait and its traffic {i}",
            )
            for j in range(120)
        ]
        out.append(
            story(
                id=f"s-{i}",
                headline=f"Story {i}",
                evidence=ev,
                figures=[
                    {
                        "actor": "hormuz",
                        "named": 60,
                        "evaluable": 120,
                        "unresolved": 0,
                        "division": 1.0 - i / 1000,
                        "balanced_rate": 0.5,
                        "measurable": True,
                    }
                ],
            )
        )
    return out


def test_the_page_stays_inside_its_budget_by_dropping_the_narrowest_evidence():
    page = render(run(many(40)), PROJECTION, COORDS, TEMPLATE, NAMES, budget=BITES)
    assert transfer_bytes(page) <= BITES
    # every story still has a row: the figures are the run's claim, not the evidence
    assert (
        page.count('<details class="row"') + page.count('<div class="row quiet">') == 40
    )
    assert "are not on this page" in page


def test_the_widest_split_keeps_its_evidence_when_the_budget_bites():
    page = render(run(many(40)), PROJECTION, COORDS, TEMPLATE, NAMES, budget=BITES)
    first = page.index("Story 0")
    last = page.index(f"Story {FEATURED}")
    assert 'class="ev-scroll"' in page[first:last]  # the hero kept its table
    assert 'class="ev-scroll"' not in page[last:]  # past the featured few, none does


def test_nothing_is_dropped_when_the_page_already_fits():
    page = render(run(many(2)), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "are not on this page" not in page
    assert page.count('class="ev-scroll"') == 2


def test_a_cap_is_never_silent():
    """A bounded page that does not say so reads as "this is everything"."""
    tight = render(run(many(40)), PROJECTION, COORDS, TEMPLATE, NAMES, budget=BITES)
    assert "data/stories.json" in tight


def test_the_budget_has_one_home():
    assert LEDGER_BUDGET_BYTES == 250 * 1024


def test_the_page_states_the_delivered_gap_not_the_schedule():
    """#10: the reader is told the delivered rate, never the cron line."""
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "1 h" in page  # 21:33 -> 22:33 in the fixture
    assert "hourly" not in page


def test_the_gap_is_read_from_the_two_stamps():
    r = run([story()])
    assert since_previous(r) == "1 h"
    r["report"]["previous_run"] = "20260802T221333Z"
    assert since_previous(r) == "20 min"
    r["report"]["previous_run"] = "20260802T043324Z"
    assert since_previous(r) == "18 h"
    r["report"]["previous_run"] = "20260802T040324Z"
    assert since_previous(r) == "18 h 30 min"


def test_a_first_run_says_so_rather_than_showing_a_zero():
    r = run([story()])
    r["report"]["previous_run"] = None
    assert since_previous(r) == "first run"


def test_a_foreign_headline_is_labelled_rather_than_translated():
    """A wrong translation misattributes, which is the one error this page must not make."""
    marked = headline({"headline": "Έφυγε από τη Ρωσία", "headline_language": "GREEK"})
    assert "Greek" in marked
    assert 'dir="auto"' in marked
    assert "Έφυγε" in marked


def test_an_english_headline_carries_no_label():
    plain = headline({"headline": "He left Russia", "headline_language": "ENGLISH"})
    assert "lang" not in plain
    assert plain == "He left Russia"


def test_a_headline_with_no_language_recorded_is_not_labelled():
    assert headline({"headline": "He left Russia"}) == "He left Russia"


def test_only_the_featured_stories_are_written_up():
    """Decision 6: five are explained, the rest are listed but never dropped."""
    page = render(run(many(12)), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert page.count('<details class="row"') == FEATURED
    assert page.count('<div class="row quiet">') == 12 - FEATURED


def test_every_story_that_cleared_the_floors_keeps_a_row():
    """Dropping them would turn a measurement into an editorial selection."""
    page = render(run(many(12)), PROJECTION, COORDS, TEMPLATE, NAMES)
    for i in range(12):
        assert f"Story {i}" in page


def test_a_compact_row_carries_the_figures_and_no_evidence():
    page = render(run(many(12)), PROJECTION, COORDS, TEMPLATE, NAMES)
    tail = page[page.index("Story 11") - 400 :]
    assert "division" in tail
    assert "ev-scroll" not in tail


def test_fewer_stories_than_featured_is_not_an_error():
    page = render(run(many(2)), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert page.count('<details class="row"') == 2
    assert '<div class="row quiet">' not in page


def test_the_budget_still_bites_on_the_featured_few():
    page = render(run(many(12)), PROJECTION, COORDS, TEMPLATE, NAMES, budget=BITES)
    assert transfer_bytes(page) <= BITES
    assert page.count('<div class="row quiet">') == 12 - FEATURED
    assert "are not on this page" in page


def test_the_page_does_not_override_the_readers_text_size():
    """#55: an absolute font-size on body is the one thing that defeats it.

    `-webkit-text-size-adjust` gates nothing since Chromium deleted its text autosizer,
    so this declaration was the whole of the problem. The page falls through to the
    browser's monospace default and every rem moves with the reader.
    """
    import re
    from importlib import resources

    tpl = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    body = re.search(r"\n  body\{[^}]*\}", tpl)
    assert body, "the body rule moved; this test has to follow it"
    assert "font-size" not in body.group(0)


def test_a_source_links_to_the_article_and_shows_the_domain():
    """#61: the domain is the evidence, the URL is the proof under it."""
    link = source_link({"domain": "abc.net.au", "url": "https://abc.net.au/x"})
    assert 'href="https://abc.net.au/x"' in link
    assert ">abc.net.au<" in link
    assert 'rel="nofollow noopener"' in link


def test_a_row_with_no_url_is_plain_text_not_a_dead_anchor():
    """Anything captured before #61 has no URL, and must read as no link."""
    assert source_link({"domain": "abc.net.au"}) == "abc.net.au"
    assert source_link({"domain": "abc.net.au", "url": None}) == "abc.net.au"


def test_the_url_is_not_rewritten():
    """Upgrading it would invent an address nobody observed."""
    link = source_link({"domain": "x.example", "url": "http://x.example/a?b=1&c=2"})
    assert "http://x.example/a?b=1&amp;c=2" in link


def test_the_evidence_table_links_every_source():
    table = evidence_table(story(), NAMES)
    assert table.count('<a class="src-link"') == len(story()["evidence"])


def test_the_page_does_not_claim_it_checked_the_links():
    page = render(run([story()]), PROJECTION, COORDS, TEMPLATE, NAMES)
    assert "does not check that the address still answers" in page
