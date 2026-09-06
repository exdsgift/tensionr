"""One pass of the story pipeline: fetch, group, reconcile, measure, write."""

import datetime as dt
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

from tensionr.config import MIN_EVALUABLE, MIN_POLITIES
from tensionr.stories import cluster, identity, languages, latent, measure, window
from tensionr.stories.polity import PolityTable
from tensionr.stories.structure import structure
from tensionr.stories.wikidata import load as load_aliases

logger = logging.getLogger(__name__)

# Everything before reconciliation is recomputable and everything after it is
# append-only (#10). The three outputs below sit on either side of that line:
# `state` is a cache the next run overwrites, `stories` is what the site reads, and
# `record` is written once and never rewritten.
SERIES = "series.json"
FEED = "feed.xml"
STATE, STORIES, RECORD, CAPTURE, INDEX = (
    "state.json",
    "stories.json",
    "record.json",
    "capture.json",
    "index.json",
)

# How wide "of the day" is (#29 decision 6). Twenty-four hours, so the page means today
# rather than whichever twelve hours the last run happened to cover.
SPAN_HOURS = 24

# How far back a featured story's published series may reach. Longer than SPAN_HOURS on
# purpose: the selection is a claim about today and must not change, while the series is
# a picture of the story's life and is thin at six points. A run outside the selection
# window contributes to the line and never to the ranking.
SERIES_HOURS = 168

# Points per series. At one run every four hours a week is about 42, and the cap is a
# guard against a burst of runs rather than a display choice.
SERIES_CAP = 60


def _capture(records: list[dict[str, Any]], already: set[str]) -> list[dict[str, Any]]:
    """The irrecoverable minimum: what GDELT will not give back if it drops it.

    Embeddings and actor marks are functions of these fields and can be recomputed at
    any time, so they are not kept (#12). Articles already captured by the previous
    run are skipped: windows overlap, and writing an immutable file per run means an
    article seen twice would otherwise be stored twice for ever.
    """
    return [
        {
            "url": r["url"],
            "title": r["title"],
            "domain": r["domain"],
            "language": r["language"],
            "seen_at": r["seen_at"],
        }
        for r in records
        if r["url"] not in already
    ]


def _representative(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The title that most of the others agree with, not the longest one.

    Longest is a bad proxy for most descriptive, because boilerplate is long by nature:
    it put "Radio Station WHMI 93.5 FM - Livingston County Michigan News, Weather,
    Traffic" on the page as one of five featured headlines. A station's own masthead is
    long and shares almost no words with what the story is about.

    So each title is scored by how much of its vocabulary the *other* titles also use.
    The phrasing several publishers converge on wins; a masthead loses because nobody
    else repeats it. Length breaks ties, since among titles that agree the fuller one
    carries more. Stop-word-free and language-agnostic on purpose — it is a vote, not a
    parse, and it has to work on the fallback path where the rows are not English.
    """
    if not rows:
        return None
    bags = [set(re.findall(r"\w+", r.get("title", "").lower())) for r in rows]
    uses: dict[str, int] = {}
    for bag in bags:
        for word in bag:
            uses[word] = uses.get(word, 0) + 1

    def agreement(pair: tuple[dict[str, Any], set[str]]) -> tuple[float, int]:
        row, bag = pair
        if not bag:
            return (-1.0, 0)
        # The fraction of this title's words that at least one other title also used —
        # a word cannot count its own use. Deliberately a fraction rather than a total:
        # a total lets a long title win by accumulating common words, which is how
        # "Australia news LIVE: Trump says..." beat "Trump says talks resume Monday".
        # And deliberately not a mean over all titles, which rewards the lowest common
        # denominator and strips every specific detail.
        shared = sum(1 for w in bag if uses[w] > 1) / len(bag)
        return (shared, len(row.get("title", "")))

    return max(zip(rows, bags, strict=True), key=agreement)[0]


def _index(stamp: str, stories: list[dict[str, Any]]) -> dict[str, Any]:
    """The slim per-run record a day-wide selection is made from.

    Published to the append-only ref instead of the whole of `stories.json`. Measured per
    run: `stories.json` is 2.68 MB against `capture.json`'s 13.7 MB, so publishing it
    would add 20% to the project's largest cost, while this adds about 3%. The evidence
    is not here because a mark is a pure function of title, actor and language, and the
    capture already holds all three, so it can be rebuilt rather than stored twice (#66).

    THE VERDICT IS AN EXCEPTION TO THAT RULE, AND HAS TO BE

    "Rebuild it from the capture" held while the capture was permanent. It is not any
    more: captures now live on a 20-day rolling window, so a verdict that is only
    derivable expires with the articles it was derived from.

    That was not hypothetical. Asking whether ranking on `division` was putting coin
    flips on the page needed the country test across 25 past runs, and the only way to
    answer it was to rejoin every index to its capture and recompute all 467 of them.
    Three weeks later that question would have had no answer at all, because the inputs
    would be gone and the outputs were never written down.

    So the verdict is stored and the table it rests on is not. The scalars are what a
    later question is asked of, and they cost four numbers per banded story; `by_polity`
    is a presentation of the same evidence the capture still carries while it lasts.
    """
    rows = []
    for story in stories:
        if not story.get("band"):
            continue
        figure = next(
            (f for f in story["figures"] if f["actor"] == story["band"][0]), None
        )
        found = story.get("structure")
        rows.append(
            {
                "id": story["id"],
                "headline": story["headline"],
                "headline_language": story.get("headline_language"),
                "band": story["band"],
                "division": (figure or {}).get("division"),
                "sources": story["sources"],
                "polities": len(story["polities"]),
                # What the country test could say, and what it was able to say it
                # about. `division` alone cannot be re-asked later: it peaks where a
                # coin does, and the ranking is decided on this.
                "structure": found
                and {
                    "p": found["p"],
                    "powered": found["powered"],
                    "sources": found["sources"],
                    "polities": found["polities"],
                },
                # Where the run put it. Recomputing this later would need the band rule
                # of the day, which is exactly the thing a record is for.
                "rank": story.get("rank"),
                # already in the evidence since #61, so derived rather than stored twice
                "urls": [r["url"] for r in story.get("evidence", []) if r.get("url")],
            }
        )
    return {"run": stamp, "stories": rows, "actors": _by_country(stories)}


def _by_country(stories: list[dict[str, Any]]) -> dict[str, dict[str, list[int]]]:
    """Named over evaluable, per actor and per polity, summed across every story.

    The run's answer to "how did outlets in each country name each actor", which no
    output carried until now. It is what a series over time is drawn from, and at 36
    actors and about 70 polities it is a few thousand integers per run. A source that
    covered three stories is counted three times, deliberately: the question is how
    much of the coverage used the name, not how many outlets did, and `actorBoard` on
    the page already sums the same way.
    """
    out: dict[str, dict[str, list[int]]] = {}
    for story in stories:
        for figure in story.get("figures", []):
            actor = figure["actor"]
            for polity, (named, evaluable) in figure.get("by_polity", {}).items():
                cell = out.setdefault(actor, {}).setdefault(polity, [0, 0])
                cell[0] += named
                cell[1] += evaluable
    return {a: dict(sorted(p.items())) for a, p in sorted(out.items())}


# How far back the accumulated series reaches. A day is a few thousand integers, so
# ninety days is a few megabytes on the ref the site reads. Beyond it the per-run
# indexes on `history` still carry every run's aggregate for anyone who wants more.
SERIES_DAYS = 90


def _accumulate(
    previous: dict[str, Any] | None,
    stamp: str,
    aggregate: dict[str, dict[str, list[int]]],
    *,
    days: int = SERIES_DAYS,
) -> dict[str, Any]:
    """The rolling series: previous runs plus this one, by day, windowed.

    Kept on the `data` ref and carried run to run, the way `state.json` is, because
    the engine only ever sees nine days of indexes and a series has to reach further
    than that.

    BY DAY, NOT BY RUN, AND WITH THE DATES IN ONE TABLE

    The first shape of this file kept one point per run with its stamp repeated on
    every point. Backfilled over 93 runs it came to 10.2 MB, and 6.1 MB of that was
    the same sixteen-character stamps written 355,218 times. A day is also the more
    honest unit for a line: GitHub delivers three to six runs a day, so per-run points
    over-weight busy days for no reason a reader would want.

    So `index` is the sorted list of days, each point is `[day_index, named,
    evaluable]`, and a run's counts are added into its day. `runs` lists every stamp
    already folded in, which is what makes a rerun of the same instant a no-op rather
    than a double count.
    """
    prev = previous or {}
    if stamp in set(prev.get("runs", [])):
        return prev

    day = f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}"
    old_index: list[str] = list(prev.get("index", []))
    # Rebuild as {actor: {polity: {day: [named, evaluable]}}}, which is easy to add to,
    # then re-index at the end.
    table: dict[str, dict[str, dict[str, list[int]]]] = {}
    for actor, polities in prev.get("actors", {}).items():
        for polity, points in polities.items():
            cell = table.setdefault(actor, {}).setdefault(polity, {})
            for i, named, evaluable in points:
                cell[old_index[i]] = [named, evaluable]
    for actor, polities in aggregate.items():
        for polity, (named, evaluable) in polities.items():
            cell = table.setdefault(actor, {}).setdefault(polity, {})
            got = cell.setdefault(day, [0, 0])
            got[0] += named
            got[1] += evaluable

    cutoff = _shift(stamp, -days * 24)[:8]
    cutoff = f"{cutoff[0:4]}-{cutoff[4:6]}-{cutoff[6:8]}"
    all_days = sorted(
        {d for a in table.values() for c in a.values() for d in c if d >= cutoff}
    )
    at = {d: i for i, d in enumerate(all_days)}
    actors: dict[str, dict[str, list[list[int]]]] = {}
    for actor, polities in table.items():
        for polity, cell in polities.items():
            pts = [[at[d], n, e] for d, (n, e) in sorted(cell.items()) if d in at]
            if pts:
                actors.setdefault(actor, {})[polity] = pts

    runs = sorted(
        r for r in {*prev.get("runs", []), stamp} if r[:8] >= cutoff.replace("-", "")
    )
    out: dict[str, Any] = {
        "run": stamp,
        "days": days,
        "runs": runs,
        "index": all_days,
        "actors": actors,
    }
    for key in ("rebuilt_before", "rebuilt_note"):
        if key in prev:
            out[key] = prev[key]
    return out


def _shift(stamp: str, hours: int) -> str:
    """A run stamp moved by `hours`, as a comparable stamp."""
    t = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%SZ") + dt.timedelta(hours=hours)
    return t.strftime("%Y%m%dT%H%M%SZ")


def _feed(
    stamp: str,
    stories: list[dict[str, Any]],
    history: list[dict[str, Any]],
    labels: dict[str, str],
    *,
    site: str = "https://exdsgift.github.io/tensionr/",
) -> str:
    """An Atom feed of the stories that entered the shown band this run.

    Monitoring means being told when something changes, and the one change this
    project can vouch for is a story whose split was just shown to follow a country
    line. Nothing else here is an event: division moves every run, and a feed of that
    would be noise a reader would unsubscribe from in a day.

    An entry is written when a story is shown now and was not shown in the most recent
    previous run that recorded a verdict. Indexes older than the verdict field have no
    opinion, and a story they carried is treated as not previously shown rather than as
    unknown; on the first run after this lands that means one batch of entries for
    everything shown, which is the honest starting point rather than a silent one.

    A static file, because the whole site is. It lives beside stories.json on the data
    ref and is served at /data/feed.xml with no script and no service behind it.

    Atom (RFC 4287) requires an author on the feed or on every entry, and the first
    version shipped without one: well-formed, parsed by lenient readers, refused by
    validators and by strict ones. The requirement is now pinned by a test rather than
    remembered.
    """
    previous = None
    for past in sorted(history, key=lambda h: h.get("run", ""), reverse=True):
        if any("structure" in row for row in past.get("stories", [])):
            previous = past
            break
    shown_before = {
        row["id"]
        for row in (previous or {}).get("stories", [])
        if (row.get("structure") or {}).get("p", 1.0) <= 0.05
    }
    entered = [
        s
        for s in stories
        if s.get("band")
        and (s.get("structure") or {}).get("p", 1.0) <= 0.05
        and s["id"] not in shown_before
    ]
    when = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.UTC)
    iso = when.isoformat().replace("+00:00", "Z")

    def esc(text: str) -> str:
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    entries = []
    for s in sorted(entered, key=lambda x: -(x.get("span_division") or 0)):
        actor = s["band"][0]
        name = labels.get(actor, actor)
        found = s["structure"]
        figure = next((f for f in s["figures"] if f["actor"] == actor), {})
        named, evaluable = figure.get("named", 0), figure.get("evaluable", 0)
        summary = (
            f"{named} of {evaluable} sources named {name}, and which ones did follows "
            f"where they publish: p = {found['p']} across {found['sources']} sources "
            f"in {found['polities']} countries."
        )
        entries.append(
            f"""  <entry>
    <title>{esc(s.get("headline") or name)}</title>
    <id>tag:tensionr,{when:%Y-%m-%d}:{esc(s["id"])}</id>
    <updated>{iso}</updated>
    <link rel="alternate" type="text/html" href="{esc(site)}actor/{esc(actor)}/"/>
    <category term="{esc(actor)}" label="{esc(name)}"/>
    <summary>{esc(summary)}</summary>
  </entry>"""
        )
    body = "\n".join(entries)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>tensionr: splits shown to follow a country line</title>
  <subtitle>One entry when a story's naming split is first shown to align with the country of publication. Nothing else is an event.</subtitle>
  <link rel="alternate" type="text/html" href="{esc(site)}"/>
  <link rel="self" type="application/atom+xml" href="{esc(site)}data/feed.xml"/>
  <id>tag:tensionr,2026:shown</id>
  <updated>{iso}</updated>
  <author><name>tensionr</name><uri>{esc(site)}</uri></author>
{body}
</feed>
"""


def _stamp_before(history: list[dict[str, Any]], hours: int) -> str | None:
    """The run stamp `hours` before the newest run in `history`, as a comparable string.

    Compared as text rather than parsed: the stamps are fixed-width UTC, so string order
    is time order, and this runs once per feature pass.
    """
    stamps = sorted(h["run"] for h in history if h.get("run"))
    if not stamps:
        return None
    newest = dt.datetime.strptime(stamps[-1], "%Y%m%dT%H%M%SZ")
    return (newest - dt.timedelta(hours=hours)).strftime("%Y%m%dT%H%M%SZ")


def _series(
    history: list[dict[str, Any]], ids: set[str]
) -> dict[str, list[dict[str, Any]]]:
    """Each featured story's division over the runs that carried it.

    This is the third pillar of the v2 map - deviations over time in the same measure -
    and it needs no new data: the engine has kept story identity between runs since #10,
    and every run has published its own index since #66. The line was there all along
    and nothing read it.

    A run where the story was absent contributes no point rather than a zero. Absence
    and a division of zero are different claims, and a line that dips to the floor when
    a story simply was not carried would invent a story about the world.
    """
    cutoff = _stamp_before(history, SERIES_HOURS)
    out: dict[str, list[dict[str, Any]]] = {}
    for past in sorted(history, key=lambda h: h.get("run", "")):
        stamp = past.get("run")
        if not stamp or (cutoff and stamp < cutoff):
            continue
        for row in past.get("stories", []):
            if row["id"] not in ids or row.get("division") is None:
                continue
            out.setdefault(row["id"], []).append(
                {
                    "run": stamp,
                    "division": row["division"],
                    "sources": row.get("sources"),
                }
            )
    return {k: v[-SERIES_CAP:] for k, v in out.items()}


# What the country test was able to say about a story, as an order. This is the primary
# ranking key; `division` breaks ties inside each band.
#
# `division` is the binary entropy of the naming rate. It peaks at one half, which is
# exactly what a fair coin gives, so it cannot tell a story whose sources split *by
# country* from one whose sources split at random. Ranking on it alone put coin flips on
# the page and left real findings off it. Measured by recomputing the test across 25
# published runs and 467 banded stories:
#
#     of 125 featured slots, 45 were shown to split by country     36%
#     of those same slots, 10 were tested and shown NOT to          8%
#     structured stories that never reached the page               39
#
# Entropy is not useless, and this does not throw it away: at a division above 0.9,
# 42.7% of stories tested structured, against 2.3% below 0.3. It is a real signal, just
# a weak one, so it orders within a band rather than across bands.
#
# Reordered on the same 25 runs, the page carries 76 structured stories instead of 45
# and no refuted one at all.
#
# Three bands because there are three states, not two. A story the test could not reach
# is an open question; a story it reached and refuted is a closed one. Preferring the
# open question is the whole point: only 7 of 25 runs had five structured stories to
# show, median three, so most days the page has to fill the rest with something, and
# "we could not tell" is worth more of a reader's attention than "we checked, and no".
SHOWN, UNTOLD, REFUTED = 0, 1, 2


def _band(story: dict[str, Any]) -> int:
    found = story.get("structure")
    if found and found["p"] <= 0.05:
        return SHOWN
    if not found or not found["powered"]:
        return UNTOLD
    return REFUTED


def _labels(aliases: Path) -> dict[str, str]:
    """Actor key to display label, from the seeds beside the alias table.

    The feed prints names, not keys, and the label whose Wikidata id was checked by
    hand is the only name this project should print. A missing seeds file is a feed
    with cruder names, not a failed run.
    """
    try:
        seeds = json.loads((Path(aliases).parent / "seeds.json").read_text("utf-8"))
        return {k: v.get("label", k) for k, v in seeds.get("actors", {}).items()}
    except (OSError, json.JSONDecodeError):
        return {}


def _publishable(figures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The figures worth writing down, which is the ones that are figures.

    One is produced for every actor in the vocabulary and 97.9% of them say nothing:
    `measurable: false`, `division: null`, and a count of evaluable sources below the
    floor. Measured on a real run that was 19,469 of 19,880 rows and 69% of
    stories.json, 2.42 MB of 3.49. The page has never read them - `actorBoard` drops
    `measurable === false` on sight - and dropping them here was verified to render a
    byte-identical page.

    Publishing them was also what made a larger vocabulary impossible. At 196 actors
    the old rule would write about 34 MB of figures per run to the ref the site reads;
    this writes 0.7 MB. How many actors the run considered is in the report, so a short
    list stays a stated fact rather than a silent truncation.
    """
    # `by_polity` travels to the index, where it is summed across stories into the
    # run's per-country aggregate. On the published figure it would be the same 30-odd
    # rows repeated for every story the page never breaks down, so it stays behind.
    return [
        {k: v for k, v in f.items() if k != "by_polity"}
        for f in figures
        if f.get("measurable") is not False
    ]


def _feature(
    stories: list[dict[str, Any]],
    history: list[dict[str, Any]],
    *,
    count: int,
) -> dict[str, Any]:
    """Mark the stories to write up: the widest divisions of the last day, still live.

    Ranked by each story's **peak** division over the span rather than by this window's
    snapshot, which is what makes the selection mean "today" instead of "the last twelve
    hours". A story that was the most divided thing in the corpus this morning keeps that
    standing all day, even if the current window has caught it in a quieter moment.

    Restricted to stories the current window still carries, and the count of candidates
    that are **not** carried is returned rather than hidden. That number decides whether
    rebuilding an absent story's evidence from the capture is worth building at all — a
    story nobody is covering any more is arguably not one of today's five, and until the
    number exists this is a guess either way (#66).
    """
    # The selection window and the series window are different spans, so they are
    # separated here rather than in the caller. Whoever loads history may hand over a
    # week of it; only the last SPAN_HOURS may decide what is featured.
    cutoff = _stamp_before(history, SPAN_HOURS)
    peak: dict[str, float] = {}
    for past in history:
        if cutoff and past.get("run", "") < cutoff:
            continue
        for row in past.get("stories", []):
            division = row.get("division")
            if division is None:
                continue
            peak[row["id"]] = max(peak.get(row["id"], 0.0), float(division))

    live = {s["id"]: s for s in stories if s.get("band")}
    for story in live.values():
        figure = next(
            (f for f in story["figures"] if f["actor"] == story["band"][0]), None
        )
        now = (figure or {}).get("division") or 0.0
        story["span_division"] = round(max(now, peak.get(story["id"], 0.0)), 4)

    ranked = sorted(live.values(), key=lambda s: (_band(s), -s["span_division"]))
    series = _series(history, {s["id"] for s in ranked[:count]})
    for position, story in enumerate(ranked[:count]):
        story["featured"] = True
        # The page must not re-derive this. It cannot: `structure` is on the story but
        # the band rule lives here, and two sorts that have to agree are one sort that
        # will eventually not.
        story["rank"] = position
        # Only for the stories written up. Every banded story would multiply the
        # payload for lines nobody is shown.
        if story["id"] in series:
            story["series"] = series[story["id"]]

    bands = Counter(_band(s) for s in ranked[:count])
    absent = sorted(peak.items(), key=lambda kv: -kv[1])
    absent = [(i, d) for i, d in absent if i not in live]
    return {
        "span_hours": SPAN_HOURS,
        "runs_in_span": len(history),
        "candidates": len(set(peak) | set(live)),
        "gone_from_the_window": len(absent),
        # what a rebuild would have to recover, if the number ever justifies it
        "widest_gone": round(absent[0][1], 4) if absent else None,
        # How many of the featured stories the country test could actually speak to.
        # The page says this rather than presenting five findings when it has two.
        "shown": bands[SHOWN],
        "untold": bands[UNTOLD],
        "refuted": bands[REFUTED],
    }


def run(
    out: Path,
    *,
    slots: int,
    aliases: Path,
    polities: Path,
    state: Path | None = None,
    history: Path | None = None,
    series: Path | None = None,
    featured: int = 5,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Produce one run's outputs from a live window.

    Returns the run report, which is also written beside the outputs: a run publishes
    what it decided, not only what it produced, so the thresholds it chose and the
    coverage it achieved travel with the figures.
    """
    stamp = (now or dt.datetime.now(dt.UTC)).strftime("%Y%m%dT%H%M%SZ")
    table = load_aliases(aliases)
    places = PolityTable.load(polities)

    fetched = window.fetch(slots, now=now)
    records = fetched["records"]
    by_url = {r["url"]: r for r in records}
    # Bound to a name rather than passed anonymously: the featured stories are drawn
    # in the embedding space they were grouped in, and that cannot be reconstructed
    # once the matrix is gone. It is 262 MB at a 128,189-article window and the run's
    # peak falls during clustering, when the edge list is alive alongside it, so
    # holding it through measurement does not raise the high-water mark.
    vectors = window.vectors(records)
    grouped = cluster.two_stage(vectors)

    known: dict[str, list[str]] = {}
    captured: set[str] = set()
    previous: str | None = None
    if state and Path(state).exists():
        prior = json.loads(Path(state).read_text("utf-8"))
        known = prior.get("open", {})
        captured = set(prior.get("window", []))
        previous = prior.get("run")

    clusters = [[records[i]["url"] for i in s] for s in grouped["stories"]]
    reconciled = identity.reconcile(clusters, known)

    actors = table.actors()
    stories = []
    for assignment in reconciled["assignments"]:
        rows = [
            {**by_url[u], "polity": places.of(by_url[u]["domain"])}
            for u in assignment["urls"]
            if u in by_url
        ]
        measured = measure.measure_story(rows, actors, table.resolve)
        band = [f["actor"] for f in measure.top_band(measured["figures"])]
        # The page is written in English, so the headline it shows has to be one where any
        # source supplies one: taking the longest title over all languages made the
        # production homepage lead in Greek, Malayalam and Slovak. Where no English source
        # carried the story the original stands, and its language travels with it so the
        # page can say which it is rather than pass it off as its own prose.
        english = [r for r in rows if languages.code_for(r.get("language")) == "en"]
        chosen = _representative(english or rows)
        story = {
            "id": assignment["id"],
            "headline": chosen["title"] if chosen else "",
            "headline_language": chosen.get("language") if chosen else None,
            "band": band,
            **measured,
            "figures": _publishable(measured["figures"]),
        }
        # Only a story that publishes a band carries its sources: the page shows the
        # evidence behind the figures it prints, and nothing else needs it.
        if band:
            story["evidence"] = measure.evidence(
                rows, band, table.resolve, spelling=table.spelling
            )
            # Whether the split runs along the polity of publication, or is a coin.
            # `division` cannot tell those apart - it peaks at one half, which is
            # exactly what a fair coin gives - and on a published run it was ranking
            # coin flips first: the top row scored a perfect 1.00 at p = 0.62.
            #
            # Banded stories only. Two thousand permutations across thirteen hundred
            # stories would cost more than the rest of the engine, and a story with no
            # band has no figure for the question to be about.
            found = structure(story["evidence"], band[0])
            if found is not None:
                story["structure"] = found
        stories.append(story)

    measurable = [s for s in stories if s["band"]]

    # Which five get written up, over a day rather than over this window (#29 d6). The
    # indexes are handed in as files because the engine does not speak git; the job
    # fetches them from the append-only ref, exactly as it already fetches the state.
    past = []
    if history and Path(history).is_dir():
        for path in sorted(Path(history).glob("*.json")):
            try:
                past.append(json.loads(path.read_text("utf-8")))
            except (OSError, json.JSONDecodeError):
                logger.warning("unreadable index, skipped: %s", path)
    span = _feature(stories, past, count=featured)

    # Where the five sit relative to one another in the space that grouped them. Only
    # the five, and only once they are known: see `latent` for why the same picture
    # drawn over twenty stories would be showing a reader adjacencies that are not
    # there.
    at = {story["id"]: i for i, story in enumerate(stories)}
    shown = sorted(
        (s for s in stories if s.get("featured")), key=lambda s: -s["span_division"]
    )
    drawn = latent.project([grouped["stories"][at[s["id"]]] for s in shown], vectors)
    if drawn is not None:
        # Not `series`: that is the path of the rolling series file, a parameter of
        # this function, and a loop variable of the same name here left it bound to a
        # dict when the write block reached `Path(series)`. The run died on the first
        # production dispatch after the series landed, with everything else finished.
        for story, plotted in zip(shown, drawn.pop("stories"), strict=True):
            story["latent"] = plotted
    del vectors

    report = {
        "run": stamp,
        "window": {
            "slots": fetched["slots_requested"],
            "missing": len(fetched["slots_missing"]),
            "articles": len(records),
            "parse_fidelity": fetched["parse_fidelity"],
        },
        "grouping": {
            "theme_threshold": grouped["theme_threshold"],
            "themes": grouped["themes"],
            "unsplit_themes": grouped["unsplit_themes"],
            "indivisible_themes": grouped.get("indivisible_themes", 0),
            "stories": len(clusters),
            # #13 decided the page publishes the count of articles that never reached a
            # measurable story. Until this landed it did not, and the loss had to be
            # found by instrumenting the clustering by hand.
            "articles_in_stories": grouped.get("articles_in_stories", 0),
        },
        "identity": {
            e: sum(1 for x in reconciled["events"] if x["type"] == e)
            for e in ("created", "merged", "split", "dormant")
        },
        "polities": places.coverage(sorted({r["domain"] for r in records})),
        # A run publishes what it decided, not only what it produced: the page states
        # these when nothing clears them, and must not keep its own copy of them.
        "floors": {"evaluable": MIN_EVALUABLE, "polities": MIN_POLITIES},
        # How many actors the run asked about, against how many it could answer for.
        # Only measurable figures are published, so without this the page could not
        # tell a thin vocabulary from a thin day.
        "actors": {
            "considered": len(actors),
            "measurable": len({f["actor"] for s in stories for f in s["figures"]}),
        },
        # The cadence the reader is told is the *delivered* one, not the cron line
        # (#10). GitHub delivers about 70% of what this schedule asks for, with
        # observed gaps of hours, so the interval since the previous run is the only
        # honest statement of how fresh the page is - and it is measured, per run.
        "previous_run": previous,
        "published": {"stories": len(stories), "with_a_band": len(measurable)},
        "selection": span,
        # None when the projection would not have been honest about adjacency, which
        # the page states rather than quietly omitting the figure.
        "latent": drawn,
    }

    out.mkdir(parents=True, exist_ok=True)
    (out / STORIES).write_text(
        json.dumps(
            {"run": stamp, "stories": stories, "report": report},
            ensure_ascii=False,
            indent=1,
        ),
        "utf-8",
    )
    (out / STATE).write_text(
        json.dumps(
            {
                "run": stamp,
                "open": {a["id"]: a["urls"] for a in reconciled["assignments"]},
                # only the last window, so the set that dedupes the capture is bounded
                "window": [r["url"] for r in records],
            }
        ),
        "utf-8",
    )
    (out / RECORD).write_text(
        json.dumps(
            {"run": stamp, "report": report, "events": reconciled["events"]}, indent=1
        ),
        "utf-8",
    )
    index = _index(stamp, stories)
    (out / INDEX).write_text(json.dumps(index, ensure_ascii=False), "utf-8")
    previous_series = None
    if series and Path(series).exists():
        try:
            previous_series = json.loads(Path(series).read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("unreadable series, starting one afresh: %s", series)
    (out / FEED).write_text(
        _feed(stamp, stories, past, _labels(aliases)),
        "utf-8",
    )
    (out / SERIES).write_text(
        json.dumps(
            _accumulate(previous_series, stamp, index["actors"]), ensure_ascii=False
        ),
        "utf-8",
    )
    (out / CAPTURE).write_text(
        json.dumps(
            {"run": stamp, "articles": _capture(records, captured)}, ensure_ascii=False
        ),
        "utf-8",
    )

    logger.info(
        "run %s: %d articles, %d stories, %d with a band, polity coverage %.0f%%",
        stamp,
        len(records),
        len(stories),
        len(measurable),
        100 * report["polities"]["rate"],
    )
    logger.info(
        "selection: %d candidates over %d h from %d runs, %d featured, "
        "%d no longer in the window (widest %s)",
        span["candidates"],
        span["span_hours"],
        span["runs_in_span"],
        min(featured, len(measurable)),
        span["gone_from_the_window"],
        span["widest_gone"],
    )
    return report
