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
import html
import json
import logging
from importlib import resources
from pathlib import Path
from typing import Any

from tensionr.stories.marks import PRESENT, UNRESOLVED

logger = logging.getLogger(__name__)

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


def evidence_table(story: dict[str, Any], names: dict[str, str]) -> str:
    actors = story["band"]
    head = "".join(f'<th class="m">{name(a, names)}</th>' for a in actors)
    body = []
    for row in story.get("evidence", []):
        marks = "".join(
            f'<td class="m {CLASS.get(row["marks"].get(a), "no")}">'
            f"{GLYPH.get(row['marks'].get(a), '○')}</td>"
            for a in actors
        )
        body.append(
            f'<tr><td class="who">{esc(row["domain"])}</td>'
            f'<td class="pol">{esc(row["polity"] or "—")}</td>'
            f'{marks}<td class="hl" dir="auto">{esc(row["title"][:160])}</td></tr>'
        )
    return (
        '<div class="ev-scroll"><table class="src"><thead><tr>'
        f"<th>Source</th><th>Polity</th>{head}<th>Headline</th>"
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


def story_row(story: dict[str, Any], names: dict[str, str], *, first: bool) -> str:
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
    band_note = (
        ""
        if len(story["band"]) == 1
        else f'<p class="read sub">{len(story["band"])} actors lead together, within '
        "0.005 of one another. #23 measured that a single top row is never stable, so "
        "the band is the claim and the order inside it is not.</p>"
    )
    return f"""    <details class="row"{" open" if first else ""}>
      <summary><div class="grid">
        <span class="title"><span class="glyph">▸</span>{esc(story["headline"][:150])}
          <small>{story["sources"]} sources · {len(story["polities"])} polities · division {figure["division"]:.3f}</small></span>
        <span class="cell num" data-l="sources">{story["sources"]}</span>
        <span class="cell num" data-l="polities">{len(story["polities"])}</span>
        <span class="actors">{row_counts(story, names)}</span>
      </div></summary>
      {reading}
      {band_note}
      <details class="ev"{" open" if first else ""}>
        <summary>{"▾" if first else "▸"} All {story["sources"]} sources, and who each one named</summary>
        {evidence_table(story, names)}
        <p class="ev-note">{note}</p>
      </details>
    </details>
"""


def render(
    stories: dict[str, Any],
    coastline: dict[str, Any],
    coordinates: dict[str, list[float]],
    template: str,
    names: dict[str, str] | None = None,
) -> str:
    """One page from one run. Raises if the run published nothing worth showing."""
    names = names or {}
    banded = [s for s in stories["stories"] if s.get("band") and s.get("evidence")]
    if not banded:
        raise ValueError("no story in this run cleared both floors — nothing to render")
    banded.sort(key=lambda s: -_lead(s)["division"])
    hero = banded[0]
    figure = _lead(hero)
    marks, plotted = panel(hero, coordinates, coastline)
    report = stories["report"]
    stamp = dt.datetime.strptime(stories["run"], "%Y%m%dT%H%M%SZ").replace(
        tzinfo=dt.UTC
    )
    hours = report["window"]["slots"] * 15 / 60

    say = (
        f"{hero['sources']} publishers in {len(hero['polities'])} polities carried this "
        f"story. {figure['named']} named {name(hero['band'][0], names)} and "
        f"{figure['evaluable'] - figure['named']} did not — the widest split this run "
        f"measured."
    )
    foot = (
        f"{report['window']['articles']:,} articles from "
        f"{report['polities']['domains']:,} domains over the last {hours:.0f} hours, "
        f"grouped into {report['grouping']['themes']} themes and "
        f"{report['grouping']['stories']} stories, of which "
        f"{report['published']['with_a_band']} cleared both floors. "
        f"{report['polities']['rate']:.0%} of domains could be placed in a polity, and "
        "the rest are counted rather than dropped. Stories keep their identity between "
        "runs by sharing article URLs, so a story that grows stays the same story. "
        "Coastlines are Natural Earth 110m, rendered in braille at two dots per column "
        "and four per row."
    )

    return (
        template.replace("@@MAP@@", "\n".join(coastline["rows"]))
        .replace("@@MAP_W@@", str(coastline["width"]))
        .replace("@@MAP_H@@", str(coastline["height"]))
        .replace("@@PANEL@@", json.dumps(marks, ensure_ascii=False))
        .replace("@@PLOTTED@@", str(plotted))
        .replace("@@HERO_ACTOR@@", name(hero["band"][0], names))
        .replace("@@HERO_NAMED@@", str(figure["named"]))
        .replace("@@HERO_EVAL@@", str(figure["evaluable"]))
        .replace("@@HERO_POLN@@", str(len(hero["polities"])))
        .replace("@@HERO_SAY@@", say)
        .replace("@@HERO_COUNTS@@", row_counts(hero, names))
        .replace("@@BANDED@@", str(report["published"]["with_a_band"]))
        .replace("@@STORIES@@", str(report["published"]["stories"]))
        .replace("@@ARTICLES@@", f"{report['window']['articles']:,}")
        .replace("@@POLITY_RATE@@", f"{report['polities']['rate']:.0%}")
        .replace("@@SLOTS@@", str(report["window"]["slots"]))
        .replace("@@WHEN@@", stamp.strftime("%-d %b · %H:%M UTC"))
        .replace(
            "@@ROWS@@",
            "".join(story_row(s, names, first=i == 0) for i, s in enumerate(banded)),
        )
        .replace("@@FOOT@@", foot)
    )


def build(data: Path, out: Path) -> Path:
    """Render from a data directory laid out as the site serves it."""
    template = (
        resources.files("tensionr.templates").joinpath("ledger.html").read_text("utf-8")
    )
    page = render(
        json.loads((data / "stories.json").read_text("utf-8")),
        json.loads((data / "map" / "coastline.json").read_text("utf-8")),
        json.loads((data / "polities" / "coordinates.json").read_text("utf-8"))[
            "polities"
        ],
        template,
        labels(data),
    )
    out.write_text(page, "utf-8")
    logger.info("wrote %s (%d bytes)", out, len(page.encode()))
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
