"""Rendering the Ledger: projection, marker states, and what the page may claim."""

import json

from tensionr.ledger import cell, evidence_table, labels, panel, render, row_counts
from tensionr.stories.measure import ABSENT, PRESENT, UNRESOLVED

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


def source(domain, polity, marks, title="a headline", language="en"):
    return {
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
<div class="cap">@@LEGEND@@</div>
<div class="agg">@@BANDED@@ of @@STORIES@@ · @@ARTICLES@@ · @@POLITY_RATE@@ · @@SLOTS@@</div>
@@ROWS@@
<div class="foot">@@FOOT@@</div>
<script>const PANEL=@@PANEL@@, W=@@MAP_W@@, H=@@MAP_H@@;</script>
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
