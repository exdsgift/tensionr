"""Rebuild the per-country series for the runs whose captures still exist.

Run by hand, once, when series.json is introduced:

    uv run --project backend python tools/backfill_series.py > data/series.json

WHAT IT CAN AND CANNOT RECOVER

The engine now writes each run's per-actor, per-country aggregate into its index and
accumulates it into series.json. Runs before that wrote neither, so their aggregate
has to be recomputed, and only two things survive from a past run: its index, which
lists the article URLs of every banded story, and its capture, which holds title,
domain and language for the articles the run saw for the first time.

Two consequences, both stated rather than hidden:

  1. Only runs whose capture is still on the `history` ref can be rebuilt. Captures
     live on a 20-day rolling window, so the series starts about three weeks back and
     not at the project's first run in early August.

  2. A rebuilt point covers banded stories only, because those are the stories whose
     URLs the index kept. The engine going forward sums across every story. The two
     are therefore not the same quantity, and the file records the stamp before which
     points are rebuilt so the page can draw them differently and say so.

Marks are recomputed with the alias table as it stands today, which is the corrected
one: the rebuilt points do not carry the 32.5% of false positives the shipped table
produced, nor Trump's invisibility in Latin script. That makes the rebuilt past more
accurate than what was published at the time, and the page should not pretend
otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from tensionr.stories.marks import PRESENT, UNRESOLVED
from tensionr.stories.polity import PolityTable
from tensionr.stories.run import _accumulate
from tensionr.stories.wikidata import load as load_aliases


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def main() -> int:
    tip = git("rev-parse", "origin/history").decode().strip()
    paths = git("ls-tree", "-r", "--name-only", tip).decode().split()
    runs = sorted({p.rsplit("/", 1)[0] for p in paths if p.endswith("/capture.json")})
    runs = [r for r in runs if f"{r}/index.json" in paths]

    table = load_aliases(Path("data/actors/aliases.json"))
    places = PolityTable.load(Path("data/polities/domains.json"))
    actors = table.actors()

    # Captures are deltas: an article appears in the capture of the run that first
    # saw it. A story in a later run's index points at URLs captured earlier, so the
    # join has to run over every capture seen so far, not the run's own.
    by_url: dict[str, dict] = {}
    series: dict | None = None
    rebuilt = 0
    for run in runs:
        for article in json.loads(git("show", f"{tip}:{run}/capture.json"))["articles"]:
            by_url.setdefault(article["url"], article)
        index = json.loads(git("show", f"{tip}:{run}/index.json"))
        aggregate: dict[str, dict[str, list[int]]] = {}
        for story in index.get("stories", []):
            rows = [by_url[u] for u in story.get("urls", []) if u in by_url]
            for actor in actors:
                for r in rows:
                    polity = places.of(r["domain"])
                    if not polity:
                        continue
                    mark = table.resolve(r.get("title", ""), actor, r.get("language"))
                    if mark == UNRESOLVED:
                        continue
                    cell = aggregate.setdefault(actor, {}).setdefault(polity, [0, 0])
                    cell[1] += 1
                    if mark == PRESENT:
                        cell[0] += 1
        if aggregate:
            series = _accumulate(series, index["run"], aggregate)
            rebuilt += 1
        print(
            f"  {index['run']}  {len(index.get('stories', []))} banded stories",
            file=sys.stderr,
        )

    if series is None:
        print("nothing to rebuild", file=sys.stderr)
        return 1
    last = series["run"]
    series["rebuilt_before"] = f"{last[0:4]}-{last[4:6]}-{last[6:8]}"
    series["rebuilt_note"] = (
        "Points at or before rebuilt_before were recomputed from banded stories only, "
        "with today's alias table. Later points are the engine's own, summed across "
        "every story."
    )
    json.dump(series, sys.stdout, ensure_ascii=False)
    print(f"\nrebuilt {rebuilt} runs, {len(series['actors'])} actors", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
