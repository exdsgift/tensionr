"""One pass of the story pipeline: fetch, group, reconcile, measure, write."""

import datetime as dt
import json
import logging
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
STATE, STORIES, RECORD, CAPTURE = (
    "state.json",
    "stories.json",
    "record.json",
    "capture.json",
)


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


def run(
    out: Path,
    *,
    slots: int,
    aliases: Path,
    polities: Path,
    state: Path | None = None,
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
        # The page is written in English, so the headline it shows has to be one, when
        # any source supplies one. Taking the longest title over all languages made the
        # production homepage lead in Greek, Malayalam and Slovak. Where no English
        # source carried the story the original stands, and the language travels with it
        # so the page can say which it is rather than pass it off as its own prose.
        english = [r for r in rows if languages.code_for(r.get("language")) == "en"]
        chosen = max(english or rows, key=lambda r: len(r["title"]), default=None)
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
            "stories": len(clusters),
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
    return report
