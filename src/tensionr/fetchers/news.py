"""News fetchers: GDELT ArtList/TimelineVol and parallel RSS."""

import calendar
import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

import feedparser

from tensionr.config import (
    GDELT_BASE_URL,
    GDELT_QUERY,
    GDELT_TIMELINE_QUERY,
    RSS_FEEDS,
    RSS_METADATA,
    RSS_SAMPLE_SIZE,
    USER_AGENT,
)
from tensionr.http_client import request_with_retry
from tensionr.processing.articles import sanitize_data

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": USER_AGENT}
SEENDATE_FORMAT = "%Y%m%dT%H%M%SZ"


def fetch_gdelt_articles() -> list[dict[str, Any]]:
    resp = request_with_retry(
        "GET",
        GDELT_BASE_URL,
        params={
            "query": GDELT_QUERY,
            "mode": "ArtList",
            "maxrecords": 50,
            "format": "json",
        },
        headers=HEADERS,
        timeout=10,
    )
    if resp is None or resp.status_code != 200:
        logger.warning("GDELT article fetch degraded (no data this run)")
        return []
    articles = resp.json().get("articles", [])
    for a in articles:
        a["source"] = "gdelt"
    return [a for a in articles if a.get("url")]


def fetch_gdelt_timeline() -> list[Any]:
    resp = request_with_retry(
        "GET",
        GDELT_BASE_URL,
        params={"query": GDELT_TIMELINE_QUERY, "mode": "TimelineVol", "format": "json"},
        headers=HEADERS,
        timeout=10,
    )
    if resp is None or resp.status_code != 200:
        logger.warning("GDELT timeline fetch degraded")
        return []
    return resp.json().get("timeline", [])


def _entry_seendate(entry: Any) -> str:
    """Real publish time (UTC, GDELT seendate format); fetch time only as last resort."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        dt = datetime.fromtimestamp(calendar.timegm(parsed), tz=UTC)
    else:
        dt = datetime.now(UTC)
    return dt.strftime(SEENDATE_FORMAT)


def _fetch_single_feed(url: str) -> list[dict[str, Any]]:
    domain = url.split("/")[2]
    resp = request_with_retry("GET", url, headers=HEADERS, timeout=10, retries=1)
    if resp is None or resp.status_code != 200:
        logger.warning("RSS feed degraded: %s", domain)
        return []
    feed = feedparser.parse(resp.text)
    meta = RSS_METADATA.get(domain, {"country": "Global", "lang": "English"})
    batch = []
    for entry in feed.entries[:10]:
        link = entry.get("link")
        if not link:
            continue
        batch.append(
            {
                "url": link,
                "title": sanitize_data(entry.get("title", "")),
                "domain": domain,
                "seendate": _entry_seendate(entry),
                "source": "rss",
                "sourcecountry": meta["country"],
                "language": meta["lang"],
            }
        )
    return batch


def fetch_rss_news() -> list[dict[str, Any]]:
    selected = random.sample(RSS_FEEDS, min(len(RSS_FEEDS), RSS_SAMPLE_SIZE))
    logger.info("scanning random rotation of %d rss feeds", len(selected))

    articles: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_single_feed, url): url for url in selected}
        for future in as_completed(futures):
            articles.extend(future.result())
    return articles
