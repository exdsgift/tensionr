"""Fetch a window of GDELT document embeddings and report what was parsed."""

import datetime as dt
import gzip
import io
import json
import logging
from typing import Any
from urllib.parse import urlparse

import numpy as np

from tensionr.config import (
    DOCEMBED_URL,
    EMBEDDING_DIM,
    HEARTBEAT_MINUTES,
    PUBLISH_LAG_MINUTES,
)
from tensionr.http_client import request_with_retry

logger = logging.getLogger(__name__)


def heartbeats(count: int, *, now: dt.datetime | None = None) -> list[str]:
    """The `count` most recent published timestamps, newest first.

    GDELT writes these files only on the quarter hour and publishes them roughly
    twenty minutes late, so a naive "now" asks for a file that does not exist yet.
    """
    now = now or dt.datetime.now(dt.UTC)
    now -= dt.timedelta(minutes=PUBLISH_LAG_MINUTES)
    slot = now.replace(
        minute=(now.minute // HEARTBEAT_MINUTES) * HEARTBEAT_MINUTES,
        second=0,
        microsecond=0,
    )
    return [
        (slot - dt.timedelta(minutes=HEARTBEAT_MINUTES * i)).strftime("%Y%m%d%H%M%S")
        for i in range(count)
    ]


def _parse(payload: bytes) -> tuple[list[dict[str, Any]], int, int]:
    """Return (records, lines seen, lines unparsed) from one gzipped JSONL file."""
    records: list[dict[str, Any]] = []
    seen = unparsed = 0
    with gzip.open(io.BytesIO(payload), "rt", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            seen += 1
            try:
                record = json.loads(line)
                embedding = record["docembed"]
                url = record["url"]
            except (json.JSONDecodeError, KeyError, TypeError):
                unparsed += 1
                continue
            if len(embedding) != EMBEDDING_DIM:
                unparsed += 1
                continue
            records.append(
                {
                    "url": url,
                    "title": record.get("title", ""),
                    "domain": urlparse(url).netloc.lower().removeprefix("www."),
                    "language": record.get("lang", "unknown"),
                    "seen_at": record.get("date", ""),
                    "embedding": embedding,
                }
            )
    return records, seen, unparsed


def fetch(count: int, *, now: dt.datetime | None = None) -> dict[str, Any]:
    """Fetch `count` heartbeat files and return the records plus a parse report.

    Fidelity is reported rather than assumed. A regex that silently matched nothing
    on a perfectly good download once produced a confident zero here, so the ratio
    of parsed to seen lines is part of the output and belongs in the published run
    record.
    """
    records: list[dict[str, Any]] = []
    seen = unparsed = 0
    missing: list[str] = []

    for stamp in heartbeats(count, now=now):
        response = request_with_retry(
            "GET", DOCEMBED_URL.format(stamp=stamp), timeout=60
        )
        if response is None or response.status_code != 200 or not response.content:
            missing.append(stamp)
            logger.warning("docembed slot unavailable: %s", stamp)
            continue
        got, slot_seen, slot_unparsed = _parse(response.content)
        records.extend(got)
        seen += slot_seen
        unparsed += slot_unparsed

    fidelity = (seen - unparsed) / seen if seen else 0.0
    logger.info(
        "window: %d articles from %d/%d slots, parse fidelity %.4f",
        len(records),
        count - len(missing),
        count,
        fidelity,
    )
    return {
        "records": records,
        "slots_requested": count,
        "slots_missing": missing,
        "lines_seen": seen,
        "lines_unparsed": unparsed,
        "parse_fidelity": round(fidelity, 6),
    }


def vectors(records: list[dict[str, Any]]) -> np.ndarray:
    """L2-normalised embedding matrix for the records, in their given order."""
    if not records:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    matrix = np.asarray([r["embedding"] for r in records], dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    return matrix
