"""Render the Ledger page from one run's stories.

The page is generated, not fetched: #14 measured that the design needs zero external
requests and ~33 statements of JavaScript, so the ledger is HTML by the time it reaches
the browser and is readable with scripting off. The only script on the page places the
map markers, which needs the rendered text metrics.

Everything printed here is derived from `stories.json`. Where the prototype carried
hand-written analysis, this prints what the data supports — which publisher said what,
and where the split runs — because a generator that wrote the interpretation would be
inventing it.
"""

import datetime as dt
import gzip
import html
import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any

from tensionr.stories.languages import code_for
from tensionr.stories.marks import PRESENT, UNRESOLVED

# What the page may weigh, compressed, because that is what a reader downloads and what
# #14 was actually arguing about: the v1 page pulled six CDN libraries and showed a
# loading state. The Ledger puts every source of every story inline (#9), so its weight
# grows with how busy the news is rather than with the code — measured at 123 KB gzipped
# for 16 stories and 2,300 source rows, so this leaves room for roughly double before
# any evidence is dropped, and the page says so when it is.
#
# It lives here rather than in `tensionr.config` because config reads a .env file and so
# needs python-dotenv, which the site assembly deliberately does not have. One home.
LEDGER_BUDGET_BYTES = 250 * 1024

# How many stories are written up rather than merely listed (#29, decision 6). Five,
# chosen by the project owner: sixteen thin rows read worse than five substantial ones,
# and the reconstruction and generation each story needs is the binding cost, so the
# number is a budget as much as a reading choice.
#
# The rest are kept as compact rows. Dropping them would turn a measurement into an
# editorial selection, and the page's standing rule is to publish its limits: "13 stories
# cleared the floors, 5 are written up" is a limit, and it is stated.
FEATURED = 5

logger = logging.getLogger(__name__)

COLUMN_HEADS = """    <div class="grid colhead">
      <span>Story<button class="i" popovertarget="p-story" aria-label="How a story is defined">i</button></span>
      <span>Sources<button class="i" popovertarget="p-src" aria-label="How sources are counted">i</button></span>
      <span>Polities<button class="i" popovertarget="p-pol" aria-label="What a polity is">i</button></span>
      <span>Named by<button class="i" popovertarget="p-named" aria-label="What named-by measures">i</button></span>
    </div>

"""

# Marks, in the page's own vocabulary. The third is not a missing value (#22).
GLYPH = {PRESENT: "●", UNRESOLVED: "–"}
CLASS = {PRESENT: "yes", UNRESOLVED: "ne"}


def esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def labels(data: Path) -> dict[str, str]:
    """Display names for actor keys, from the curated seeds.

    The key is a slug the pipeline matches on; the label is what a reader should see,
    and the two are not interchangeable — `hormuz` is the Strait of Hormuz and `trump`
    is Donald Trump. Titlecasing the key would print neither. The seeds are the same
    file the alias table was built from, so the name on the page is the name whose
    Wikidata id was checked by hand (#22).
    """
    seeds = data / "actors" / "seeds.json"
    if not seeds.exists():
        return {}
    return {
        key: value["label"]
        for key, value in json.loads(seeds.read_text("utf-8"))["actors"].items()
        if value.get("label")
    }


def name(actor: str, names: dict[str, str]) -> str:
    return esc(names.get(actor, actor.replace("-", " ").title()))


def cell(lat: float, lon: float, projection: dict[str, Any]) -> tuple[float, float]:
    """Fractional character cell for a coordinate, in the coastline's own projection.

    Read from the coastline file rather than restated here. The prototype encoded the
    crop twice — 82N/58S in the position formula against the 74N/56S the map was
    actually rasterised at — and every marker landed in the wrong place. One source for
    the projection is the fix; a constant in this module would only move the bug.
    """
    top, bottom = projection["lat_top"], projection["lat_bottom"]
    left, right = projection["lon_left"], projection["lon_right"]
    col = (lon - left) / (right - left) * projection["width"]
    row = (top - lat) / (top - bottom) * projection["height"]
    return col, row


def panel(
    story: dict[str, Any], coordinates: dict[str, list[float]], projection: dict
) -> tuple[list[dict[str, Any]], int]:
    """Map markers for the polities that carried the story.

    Two states, both measured: a polity **named** the band's actor in at least one of
    its sources, or it carried the story and named the actor in none of them. That
    second state is the one the project exists to show, so it earns a mark rather than
    a footnote.

    A polity absent from the story is not plotted at all. Marking it silent would claim
    it should have carried the story, and no declared panel exists yet to support that
    (#20) — the prototype's hollow marks were labelled illustrative for this reason.
    """
    actor = story["band"][0]
    named: dict[str, bool] = {}
    for row in story.get("evidence", []):
        if not row["polity"]:
            continue
        hit = row["marks"].get(actor) == PRESENT
        named[row["polity"]] = named.get(row["polity"], False) or hit

    marks = []
    for polity in sorted(named):
        if polity not in coordinates:
            continue
        col, row_ = cell(*coordinates[polity], projection)
        marks.append(
            {
                "n": f"{polity} · {'named' if named[polity] else 'did not name'}",
                "c": round(col, 2),
                "r": round(row_, 2),
                "on": named[polity],
            }
        )
    return marks, len(named)


def _lead(story: dict[str, Any]) -> dict[str, Any]:
    """The band's first figure — the band is unordered, so 'first' is alphabetical."""
    by_actor = {f["actor"]: f for f in story["figures"]}
    return by_actor[story["band"][0]]


def source_link(row: dict[str, Any]) -> str:
    """The publisher, as a link to the article it published.

    The visible text stays the **domain**, because the domain is the evidence — a reader
    is comparing publishers, and a row of URLs would be unreadable. The URL is the proof
    underneath it.

    `rel="nofollow"` because these links are generated in bulk and never reviewed:
    pointing at an article is not a judgement about it. `noopener` because the link opens
    in a new tab, which is what a reader comparing forty sources needs. The URL is left
    exactly as GDELT recorded it, including `http`, since rewriting it would be inventing
    an address nobody observed.

    A row with no URL falls back to plain text rather than a dead anchor. That happens
    for anything captured before #61 and it must read as "no link", not as a broken one.
    """
    domain = esc(row["domain"])
    url = row.get("url")
    if not url:
        return domain
    return (
        f'<a class="src-link" href="{esc(url)}" rel="nofollow noopener" '
        f'target="_blank">{domain}</a>'
    )


def evidence_table(story: dict[str, Any], names: dict[str, str]) -> str:
    """Every source, one row each, in a table that keeps its columns.

    The table is wider than a phone and stays that way. Six columns of which one is a
    headline cannot be folded into 320 pixels without either wrapping the rows into
    cards — which drops the table semantics browsers expose to a screen reader, and
    with them the row/column relationship that is the whole point of showing the
    evidence — or hiding columns, which here means hiding the marks the page exists to
    publish. So it scrolls sideways inside its own box, and the box is made operable:
    `tabindex=0` plus a role and a name, because a region only a mouse or a finger can
    reach fails SC 2.1.1 — Safari still does not make scrollers focusable by itself, and
    neither does Chrome once a scroller has a focusable child (#51).
    """
    actors = story["band"]
    head = "".join(f'<th class="m" scope="col">{name(a, names)}</th>' for a in actors)
    body = []
    for row in story.get("evidence", []):
        marks = "".join(
            f'<td class="m {CLASS.get(row["marks"].get(a), "no")}">'
            f"{GLYPH.get(row['marks'].get(a), '○')}</td>"
            for a in actors
        )
        body.append(
            f'<tr><td class="who">{source_link(row)}</td>'
            f'<td class="pol">{esc(row["polity"] or "—")}</td>'
            f'{marks}<td class="hl" dir="auto">{esc(row["title"][:160])}</td></tr>'
        )
    # The region's name is the table's own caption, referenced rather than restated, so
    # a screen reader announces one name for the scroller and the table it holds. The
    # caption is clipped rather than display:none — an off-screen caption still names
    # the table, and being out of flow it cannot widen it (CAPMIN).
    cap = f"ev-cap-{esc(story['id'])}"
    caption = f"{len(story.get('evidence', []))} sources, and who each one named"
    return (
        f'<div class="ev-scroll" tabindex="0" role="region" aria-labelledby="{cap}">'
        f'<table class="src"><caption class="vh" id="{cap}">{caption}</caption>'
        f'<thead><tr><th scope="col">Source</th><th scope="col">Polity</th>{head}'
        f'<th scope="col">Headline</th>'
        f"</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def _split(story: dict[str, Any], names: dict[str, str]) -> str:
    """Where the disagreement runs, in polities rather than in adjectives.

    This is the sentence the prototype wrote by hand. It is stated only as counts and
    names, because who named an actor is a fact in the table below it and anything more
    would be an interpretation the run cannot support.
    """
    actor = story["band"][0]
    by_polity: dict[str, list[bool]] = {}
    for row in story.get("evidence", []):
        if not row["polity"] or row["marks"].get(actor) == UNRESOLVED:
            continue
        by_polity.setdefault(row["polity"], []).append(
            row["marks"].get(actor) == PRESENT
        )
    every = sorted(p for p, m in by_polity.items() if all(m))
    none = sorted(p for p, m in by_polity.items() if not any(m))
    if not every or not none:
        return ""
    return (
        f"Every source in {_series(every[:4])} named {name(actor, names)}; "
        f"none of those in {_series(none[:4])} did."
    )


def _series(names: list[str]) -> str:
    names = [esc(n) for n in names]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def row_counts(story: dict[str, Any], names: dict[str, str]) -> str:
    out = []
    for actor in story["band"]:
        figure = next(f for f in story["figures"] if f["actor"] == actor)
        rate = figure["named"] / figure["evaluable"] if figure["evaluable"] else 0
        miss = ' class="miss"' if rate < 0.4 else ""
        out.append(
            f"<span{miss}><b>{name(actor, names)}</b> "
            f"{figure['named']}/{figure['evaluable']}</span>"
        )
    return " · ".join(out)


def headline(story: dict[str, Any]) -> str:
    """The story's headline, marked when it is not in the page's own language.

    Not translated. A translation is a claim about what a publisher said, and getting it
    wrong misattributes — the one error this page exists not to make. So a foreign
    headline is shown as the publisher wrote it, labelled, and read as a quotation.
    """
    text = esc(story["headline"][:150])
    language = story.get("headline_language")
    if language and code_for(language) != "en":
        return f'<span dir="auto">{text}</span> <i class="lang">{esc(language.title())}</i>'
    return text


def story_row(
    story: dict[str, Any],
    names: dict[str, str],
    *,
    first: bool,
    with_evidence: bool = True,
) -> str:
    figure = _lead(story)
    unresolved = figure["unresolved"]
    note = (
        f"Every publisher in the story, one row each, after collapsing "
        f"{story['collapsed']} reprint(s) that shared a headline word for word. "
    )
    note += (
        f"{unresolved} row(s) are <b>–</b>, <em>not evaluable</em>: no alias exists in "
        "that script, and that must never be read as an omission — omission is the "
        "signal."
        if unresolved
        else "No row is <b>–</b>: an alias exists in every script present."
    )
    note += (
        " Each publisher links to the article at the address GDELT recorded; the page "
        "does not check that the address still answers."
    )
    sentence = (
        f"{story['sources']} publishers across {len(story['polities'])} polities "
        f"carried this. {figure['named']} of {figure['evaluable']} named "
        f"<b>{name(story['band'][0], names)}</b>"
    )
    if figure["balanced_rate"] is not None:
        sentence += (
            f", which is {figure['balanced_rate']:.0%} once every language counts "
            "equally rather than every source"
        )
    sentence += "."
    if split := _split(story, names):
        sentence += " " + split
    reading = f'<p class="read">{sentence}</p>'
    if with_evidence:
        evidence = f"""<details class="ev"{" open" if first else ""}>
        <summary>{"▾" if first else "▸"} All {story["sources"]} sources, and who each one named</summary>
        {evidence_table(story, names)}
        <p class="ev-note">{note}</p>
      </details>"""
    else:
        # Bounded, and said out loud. The figures above are the run's claim; the rows
        # behind them are in data/stories.json, which is served beside this page.
        evidence = (
            '<p class="ev-note">The sources behind this row are not on this page: it '
            "would have gone past its weight budget. They are in "
            '<a href="data/stories.json">data/stories.json</a>, one row per publisher, '
            "the same rows the figures were computed from.</p>"
        )
    band_note = (
        ""
        if len(story["band"]) == 1
        else f'<p class="read sub">{len(story["band"])} actors lead together, within '
        "0.005 of one another. #23 measured that a single top row is never stable, so "
        "the band is the claim and the order inside it is not.</p>"
    )
    return f"""    <details class="row"{" open" if first else ""}>
      <summary><div class="grid">
        <span class="title"><span class="glyph">▸</span>{headline(story)}
          <small>{story["sources"]} sources · {len(story["polities"])} polities · division {figure["division"]:.3f}</small></span>
        <span class="cell num" data-l="sources">{story["sources"]}</span>
        <span class="cell num" data-l="polities">{len(story["polities"])}</span>
        <span class="actors">{row_counts(story, names)}</span>
      </div></summary>
      {reading}
      {band_note}
      {evidence}
    </details>
"""


def hook(hero: dict[str, Any] | None, report: dict[str, Any], names: dict) -> str:
    """The top-left column: a figure when there is one, a statement when there is not.

    A window where nothing clears both floors is a real outcome, not a broken build, and
    the page has to be able to say so. #6 decided the index declares itself
    non-computable below a floor rather than printing a number it cannot support, and
    this is that rule applied to the page's own headline.
    """
    if hero is None:
        # Named from the report, so the page states the floors the run actually applied
        # rather than a copy of its own. A run written before the report carried them
        # says so instead of inventing numbers.
        floors = report.get("floors")
        threshold = (
            f"{floors['evaluable']} evaluable sources across {floors['polities']} "
            "polities"
            if floors
            else "this project's floors on evaluable sources and polities"
        )
        return f"""      <span class="lede">Nothing cleared the floors in this window</span>
      <div class="fig"><b class="num na">—</b>
        <span class="unit">no figure this run can support</span></div>
      <p class="say">{report["grouping"]["stories"]} stories were grouped from
        {report["window"]["articles"]:,} articles, and none reached {threshold} with a
        measurable division. That is published rather than hidden: a figure below the
        floor would be a number about the sample, not about the world.</p>
      <div class="from"><span>{report["published"]["stories"]} <b>stories</b></span></div>"""

    figure = _lead(hero)
    say = (
        f"{hero['sources']} publishers in {len(hero['polities'])} polities carried this "
        f"story. {figure['named']} named {name(hero['band'][0], names)} and "
        f"{figure['evaluable'] - figure['named']} did not — the widest split this run "
        f"measured."
    )
    return f"""      <span class="lede">Sharpest disagreement in this window</span>
      <div class="fig"><b class="num">{figure["named"]}<i>/{figure["evaluable"]}</i></b>
        <span class="unit">sources named {name(hero["band"][0], names)}</span></div>
      <p class="say">{say}</p>
      <div class="from">{row_counts(hero, names)}<span>{len(hero["polities"])} <b>polities</b></span></div>"""


def legend(hero: dict[str, Any] | None, plotted: int, names: dict) -> str:
    """The map's caption. It names the states actually drawn, and nothing else."""
    if hero is None:
        return (
            '<span class="dim">no polities plotted — no story carries a figure</span>'
        )
    return (
        f'<span><span style="color:var(--cyan)">●</span> named '
        f"{name(hero['band'][0], names)}</span>\n        "
        '<span><span style="color:var(--grey)">○</span> carried it, did not</span>\n'
        '        <span class="dim">pulse = signal received</span>\n        '
        f'<span class="dim">{plotted} of {len(hero["polities"])} plotted</span>'
        '<span class="dim">tap or hover a point</span>'
    )


def selection_note(report: dict[str, Any], featured: int) -> str:
    """What span the page selected over, and what the span could not reach.

    "Of the day" and "of this window" are different claims and the page said neither. It
    now says which, and how many stories that were divided during the day the current
    window no longer carries — that number is what decides whether rebuilding an absent
    story's evidence from the capture is worth building, and publishing it is how the
    decision gets made on data rather than on a guess (#66).
    """
    span = report.get("selection")
    if not span or not span.get("runs_in_span"):
        return (
            f"The {featured} most divided stories in this window, written up. The rest "
            "cleared the floors and are listed below them."
        )
    text = (
        f"The {featured} most divided stories of the last {span['span_hours']} hours, "
        f"ranked by the widest division each reached over that span rather than by this "
        f"window alone — {span['candidates']} candidates across {span['runs_in_span']} "
        "runs."
    )
    gone = span.get("gone_from_the_window")
    if gone:
        widest = span.get("widest_gone")
        text += (
            f" {gone} of them are no longer carried by the current window and were not "
            "eligible"
        )
        text += f", the widest at a division of {widest}." if widest else "."
    return text


def _never_reached(report: dict[str, Any]) -> str:
    """What the grouping threw away, published rather than absorbed.

    #13 decided the page publishes the count of articles that never reached a measurable
    story. Most of a window does not: an article has to join a theme, the theme has to
    yield a story, and the story has to clear two floors. Stating only the survivors
    would make the corpus look like the sample.
    """
    grouped = report.get("grouping", {})
    kept = grouped.get("articles_in_stories")
    total = report.get("window", {}).get("articles")
    if not kept or not total:
        return ""
    dropped = total - kept
    text = (
        f"{dropped:,} of those articles never reached a story at all — "
        f"{100 * dropped / total:.0f}% — because they joined no theme, or joined one "
        "too uniform to separate."
    )
    unsplit = grouped.get("unsplit_themes")
    if unsplit:
        text += (
            f" {unsplit} themes were dropped whole for being near-duplicates at every "
            "resolution."
        )
    return text


def since_previous(stories: dict[str, Any]) -> str:
    """How long since the run before this one, measured rather than promised.

    #10 decided the reader is told the *delivered* rate, not the cron line. The schedule
    asks for one run an hour and GitHub delivers roughly 40% of them, with gaps of
    hours, so "hourly" would be a claim the system does not meet. A run knows exactly
    when the previous one was, so it says that instead.
    """
    previous = stories["report"].get("previous_run")
    if not previous:
        return "first run"
    fmt = "%Y%m%dT%H%M%SZ"
    gap = dt.datetime.strptime(stories["run"], fmt) - dt.datetime.strptime(
        previous, fmt
    )
    minutes = round(gap.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min" if minutes else f"{hours} h"


def transfer_bytes(page: str) -> int:
    """What a reader actually downloads. Pages serves gzip, so that is the number."""
    return len(gzip.compress(page.encode(), 9))


def _fit(
    banded: list[dict[str, Any]], names: dict[str, str], build_page, budget: int
) -> tuple[str, int]:
    """The featured stories written up, the rest listed, inside the weight budget.

    Two separate bounds. The first is editorial: `FEATURED` stories carry their prose and
    their sources, and every other story that cleared the floors keeps a compact row —
    its figures are the run's claim and cost about a kilobyte. The second is the weight
    budget, which can still bite on the featured few when the news is busy, and then
    evidence goes from the *narrowest* division first. Either way the count that lost its
    sources is stated on the page, because a cap nobody is told about reads as "this is
    everything".
    """
    featured = min(FEATURED, len(banded))
    for dropped in range(featured + 1):
        keep = featured - dropped
        rows = COLUMN_HEADS + "".join(
            story_row(s, names, first=i == 0, with_evidence=i < keep)
            for i, s in enumerate(banded[:featured])
        )
        weighed = transfer_bytes(build_page(rows, dropped))
        if weighed <= budget or dropped == featured:
            if dropped:
                logger.info(
                    "evidence dropped from %d of %d featured rows to stay inside %d KB",
                    dropped,
                    featured,
                    budget // 1024,
                )
            return rows, dropped
    return "", 0


def render(
    stories: dict[str, Any],
    coastline: dict[str, Any],
    coordinates: dict[str, list[float]],
    template: str,
    names: dict[str, str] | None = None,
    budget: int = LEDGER_BUDGET_BYTES,
    narrow: dict[str, Any] | None = None,
) -> str:
    """One page from one run, whether or not the run produced a figure.

    Two coastlines, because a 76-character map is not a smaller map at 380 CSS pixels,
    it is the same map at an illegible size: 76 characters of braille need 52 times the
    font size in pixels, so filling a 358-pixel column asks for 6.9px type and leaves
    each dot under a pixel of ink. The narrow map is a different artefact — half the
    resolution on both axes at the same crop — and the page picks between them with a
    media query so the choice survives with scripting off. Both carry their own
    projection fields and each set of markers is derived from the map it belongs to
    (#41): a marker computed against the wrong map is exactly the defect that produced
    that rule. `narrow=None` means one map for every width, which is what a caller with
    a single rasterisation gets.
    """
    names = names or {}
    narrow = narrow or coastline
    banded = [s for s in stories["stories"] if s.get("band") and s.get("evidence")]
    # The engine chooses which stories are written up when it can see a day of history
    # (#66); ranked by the peak division over that day, not by this window's snapshot.
    # Without that history the page falls back to ranking what it has, which is what it
    # did before and is still correct for a single window.
    if any(s.get("featured") for s in banded):
        banded.sort(
            key=lambda s: (not s.get("featured"), -(s.get("span_division") or 0.0))
        )
    else:
        banded.sort(key=lambda s: -_lead(s)["division"])
    hero = banded[0] if banded else None
    marks, plotted = panel(hero, coordinates, coastline) if hero else ([], 0)
    narrow_marks = panel(hero, coordinates, narrow)[0] if hero else []
    report = stories["report"]
    stamp = dt.datetime.strptime(stories["run"], "%Y%m%dT%H%M%SZ").replace(
        tzinfo=dt.UTC
    )
    hours = report["window"]["slots"] * 15 / 60
    foot = (
        f"{report['window']['articles']:,} articles from "
        f"{report['polities']['domains']:,} domains over the last {hours:.0f} hours, "
        f"grouped into {report['grouping']['themes']} themes and "
        f"{report['grouping']['stories']} stories, of which "
        f"{report['published']['with_a_band']} cleared both floors. "
        f"{_never_reached(report)} "
        f"{report['polities']['rate']:.0%} of domains could be placed in a polity, and "
        "the rest are counted rather than dropped. Stories keep their identity between "
        "runs by sharing article URLs, so a story that grows stays the same story. "
        "Coastlines are Natural Earth 110m, rendered in braille at two dots per column "
        "and four per row."
    )

    def build_page(rows: str, dropped: int) -> str:
        note = (
            ""
            if not dropped
            else f" The sources behind the {dropped} narrowest of these rows are not on "
            "this page, which would otherwise go past its weight budget; they are in "
            '<a href="data/stories.json">data/stories.json</a>.'
        )
        return (
            template.replace("@@MAP@@", "\n".join(coastline["rows"]))
            .replace("@@MAP_W@@", str(coastline["width"]))
            .replace("@@MAP_H@@", str(coastline["height"]))
            .replace("@@PANEL@@", json.dumps(marks, ensure_ascii=False))
            .replace("@@MAP_N@@", "\n".join(narrow["rows"]))
            .replace("@@MAP_N_W@@", str(narrow["width"]))
            .replace("@@MAP_N_H@@", str(narrow["height"]))
            .replace("@@PANEL_N@@", json.dumps(narrow_marks, ensure_ascii=False))
            .replace("@@HOOK@@", hook(hero, report, names))
            .replace("@@LEGEND@@", legend(hero, plotted, names))
            .replace("@@BANDED@@", str(report["published"]["with_a_band"]))
            .replace("@@STORIES@@", str(report["published"]["stories"]))
            .replace("@@ARTICLES@@", f"{report['window']['articles']:,}")
            .replace("@@POLITY_RATE@@", f"{report['polities']['rate']:.0%}")
            .replace("@@SLOTS@@", str(report["window"]["slots"]))
            .replace("@@SINCE@@", since_previous(stories))
            .replace(
                "@@SELECTION@@", selection_note(report, min(FEATURED, len(banded)))
            )
            .replace("@@WHEN@@", stamp.strftime("%-d %b · %H:%M UTC"))
            .replace("@@ROWS@@", rows)
            .replace("@@FOOT@@", foot + note)
        )

    if not banded:
        empty = (
            '    <p class="read">No story in this window cleared both floors, so there '
            "is no row to show. The window itself is described below.</p>\n"
        )
        return build_page(empty, 0)

    rows, dropped = _fit(banded, names, build_page, budget)
    return build_page(rows, dropped)


def build(data: Path, out: Path, budget: int = LEDGER_BUDGET_BYTES) -> Path:
    """Render from a data directory laid out as the site serves it."""
    template = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    maps = data / "map"
    page = render(
        json.loads((data / "stories.json").read_text("utf-8")),
        json.loads((maps / "coastline.json").read_text("utf-8")),
        json.loads((data / "polities" / "coordinates.json").read_text("utf-8"))[
            "polities"
        ],
        template,
        labels(data),
        budget,
        narrow=json.loads((maps / "coastline-narrow.json").read_text("utf-8")),
    )
    out.write_text(page, "utf-8")
    logger.info(
        "wrote %s: %d KB, %d KB gzipped against a %d KB budget",
        out,
        len(page.encode()) // 1024,
        transfer_bytes(page) // 1024,
        budget // 1024,
    )
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m tensionr.ledger",
        description="Render the Ledger page from a run's stories.json.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data"),
        help="directory holding stories.json, map/ and polities/",
    )
    parser.add_argument("--out", type=Path, default=Path("index.html"))
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    build(args.data, args.out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
