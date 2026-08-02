"""Join GDELT's knowledge-graph rows to our articles by URL, for resolved entities."""

import csv
import datetime as dt
import io
import logging
import zipfile
from typing import Any

from tensionr.config import (
    FIELD_SIZE_LIMIT,
    GKG_COLUMNS,
    GKG_LAG_MINUTES,
    GKG_TRANSLATION_URL,
    GKG_URL,
    HEARTBEAT_MINUTES,
)
from tensionr.http_client import request_with_retry

logger = logging.getLogger(__name__)

# GKG rows carry V2GCAM and V2EXTRASXML fields that run to hundreds of kilobytes,
# well past Python's 128 KB default. Without this the reader raises part-way through
# a slot and the run loses every row after it — found by widening the window.
csv.field_size_limit(FIELD_SIZE_LIMIT)

# Column positions in GKG 2.1. Hardcoded indices fail silently if the schema moves,
# so every row is checked for the expected width and mismatches are counted rather
# than skipped quietly.
URL, LOCATIONS, PERSONS, ORGANISATIONS, ALLNAMES = 4, 9, 11, 13, 23


def heartbeats(count: int, *, now: dt.datetime | None = None) -> list[str]:
    """The `count` most recent GKG timestamps, newest first."""
    now = (now or dt.datetime.now(dt.UTC)) - dt.timedelta(minutes=GKG_LAG_MINUTES)
    slot = now.replace(
        minute=(now.minute // HEARTBEAT_MINUTES) * HEARTBEAT_MINUTES,
        second=0,
        microsecond=0,
    )
    return [
        (slot - dt.timedelta(minutes=HEARTBEAT_MINUTES * i)).strftime("%Y%m%d%H%M%S")
        for i in range(count)
    ]


def _locations(field: str) -> list[str]:
    """Place names from V1LOCATIONS: `type#name#cc#adm1#lat#lon#featureid;`."""
    out = []
    for entry in field.split(";"):
        parts = entry.split("#")
        if len(parts) >= 2 and parts[1]:
            out.append(parts[1])
    return out


def _names(field: str) -> list[str]:
    """Names from V2.1ALLNAMES: `Name,charoffset;`, offsets discarded."""
    out = []
    for entry in field.split(";"):
        name = entry.rsplit(",", 1)[0].strip()
        if name:
            out.append(name)
    return out


def _simple(field: str) -> list[str]:
    return [p.strip() for p in field.split(";") if p.strip()]


def parse(payload: bytes) -> tuple[dict[str, dict[str, list[str]]], dict[str, int]]:
    """Rows indexed by article URL, plus a report of what did not parse."""
    rows: dict[str, dict[str, list[str]]] = {}
    report = {"rows": 0, "wrong_width": 0, "no_url": 0}

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        name = archive.namelist()[0]
        with archive.open(name) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace")
            for record in csv.reader(text, delimiter="\t", quoting=csv.QUOTE_NONE):
                report["rows"] += 1
                if len(record) != GKG_COLUMNS:
                    report["wrong_width"] += 1
                    continue
                url = record[URL].strip()
                if not url:
                    report["no_url"] += 1
                    continue
                rows[url] = {
                    "locations": _locations(record[LOCATIONS]),
                    "names": _names(record[ALLNAMES]),
                    "persons": _simple(record[PERSONS]),
                    "organisations": _simple(record[ORGANISATIONS]),
                }
    return rows, report


def fetch(count: int, *, now: dt.datetime | None = None) -> dict[str, Any]:
    """Both GKG feeds over `count` slots, indexed by URL.

    The translation feed carries the non-English coverage and its names arrive
    already in Latin script, because GDELT machine-translates and then runs the
    English extractor. Accumulating a window matters: a single timestamp joined only
    23% of our articles, while a wider window reaches 95% (#22).
    """
    rows: dict[str, dict[str, list[str]]] = {}
    totals = {"rows": 0, "wrong_width": 0, "no_url": 0}
    missing: list[str] = []

    for stamp in heartbeats(count, now=now):
        for template in (GKG_URL, GKG_TRANSLATION_URL):
            response = request_with_retry(
                "GET", template.format(stamp=stamp), timeout=90
            )
            if response is None or response.status_code != 200 or not response.content:
                missing.append(template.format(stamp=stamp).rsplit("/", 1)[-1])
                continue
            try:
                got, report = parse(response.content)
            except zipfile.BadZipFile:
                logger.warning("gkg slot is not a zip: %s", stamp)
                missing.append(stamp)
                continue
            rows.update(got)
            for key in totals:
                totals[key] += report[key]

    if totals["wrong_width"]:
        # Not fatal, but it is how a schema change would first appear, so it is
        # surfaced rather than absorbed into a silent zero.
        logger.warning(
            "gkg: %d of %d rows were not %d columns wide",
            totals["wrong_width"],
            totals["rows"],
            GKG_COLUMNS,
        )
    logger.info(
        "gkg: %d urls over %d slots, %d files missing", len(rows), count, len(missing)
    )
    # The report is nested rather than merged in: it carries its own "rows" count,
    # and spreading it over the payload silently replaced the data with an integer.
    return {"rows": rows, "slots_missing": missing, "report": totals}


def join(
    article_urls: list[str], gkg_rows: dict[str, dict[str, list[str]]]
) -> dict[str, Any]:
    """Match articles to GKG rows and report the rate, because it is the whole risk.

    Identifiers are byte-identical between the two feeds, so no normalisation is
    applied: any normalisation here would hide a mismatch rather than fix one.
    """
    matched = {u: gkg_rows[u] for u in article_urls if u in gkg_rows}
    rate = len(matched) / len(article_urls) if article_urls else 0.0
    return {
        "matched": matched,
        "rate": round(rate, 4),
        "misses": len(article_urls) - len(matched),
    }
