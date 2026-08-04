"""One pass of the story pipeline: fetch, group, reconcile, measure, write."""

import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any

from tensionr.config import MIN_EVALUABLE, MIN_POLITIES
from tensionr.stories import cluster, identity, languages, measure, window
from tensionr.stories.polity import PolityTable
from tensionr.stories.wikidata import load as load_aliases

logger = logging.getLogger(__name__)

# Everything before reconciliation is recomputable and everything after it is
# append-only (#10). The three outputs below sit on either side of that line:
# `state` is a cache the next run overwrites, `stories` is what the site reads, and
# `record` is written once and never rewritten.
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
    capture already holds all three — so it can be rebuilt rather than stored twice (#66).
    """
    rows = []
    for story in stories:
        if not story.get("band"):
            continue
        figure = next(
            (f for f in story["figures"] if f["actor"] == story["band"][0]), None
        )
        rows.append(
            {
                "id": story["id"],
                "headline": story["headline"],
                "headline_language": story.get("headline_language"),
                "band": story["band"],
                "division": (figure or {}).get("division"),
                "sources": story["sources"],
                "polities": len(story["polities"]),
                # already in the evidence since #61, so derived rather than stored twice
                "urls": [r["url"] for r in story.get("evidence", []) if r.get("url")],
            }
        )
    return {"run": stamp, "stories": rows}


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
    peak: dict[str, float] = {}
    for past in history:
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

    ranked = sorted(live.values(), key=lambda s: -s["span_division"])
    for story in ranked[:count]:
        story["featured"] = True

    absent = sorted(peak.items(), key=lambda kv: -kv[1])
    absent = [(i, d) for i, d in absent if i not in live]
    return {
        "span_hours": SPAN_HOURS,
        "runs_in_span": len(history),
        "candidates": len(set(peak) | set(live)),
        "gone_from_the_window": len(absent),
        # what a rebuild would have to recover, if the number ever justifies it
        "widest_gone": round(absent[0][1], 4) if absent else None,
    }


def run(
    out: Path,
    *,
    slots: int,
    aliases: Path,
    polities: Path,
    state: Path | None = None,
    history: Path | None = None,
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
    grouped = cluster.two_stage(window.vectors(records))

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
        }
        # Only a story that publishes a band carries its sources: the page shows the
        # evidence behind the figures it prints, and nothing else needs it.
        if band:
            story["evidence"] = measure.evidence(rows, band, table.resolve)
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
        # The cadence the reader is told is the *delivered* one, not the cron line
        # (#10). GitHub delivers roughly 40% of what this schedule asks for, with
        # observed gaps of hours, so the interval since the previous run is the only
        # honest statement of how fresh the page is - and it is measured, per run.
        "previous_run": previous,
        "published": {"stories": len(stories), "with_a_band": len(measurable)},
        "selection": span,
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
    (out / INDEX).write_text(
        json.dumps(_index(stamp, stories), ensure_ascii=False), "utf-8"
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
