"""Cyber-threat and raw OSINT chatter feeds."""

import logging
from typing import Any

import feedparser

from tensionr.config import CHATTER_FEED_URL, CYBER_FEED_URL
from tensionr.http_client import request_with_retry
from tensionr.processing.articles import sanitize_data

logger = logging.getLogger(__name__)


def fetch_cyber_intel() -> list[dict[str, Any]]:
    logger.info("fetching cyber intelligence...")
    resp = request_with_retry("GET", CYBER_FEED_URL, timeout=15)
    if resp is None or resp.status_code != 200:
        logger.warning("cyber intel feed degraded")
        return []
    feed = feedparser.parse(resp.text)
    return [
        {
            "title": sanitize_data(entry.get("title", "")),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        }
        for entry in feed.entries[:5]
    ]


def fetch_raw_chatter() -> list[dict[str, Any]]:
    logger.info("scanning raw osint chatter...")
    resp = request_with_retry("GET", CHATTER_FEED_URL, timeout=15)
    if resp is None or resp.status_code != 200:
        logger.warning("raw chatter feed degraded")
        return []
    feed = feedparser.parse(resp.text)
    return [
        {
            "title": sanitize_data(entry.get("title", "")),
            "link": entry.get("link", ""),
            "source": "OSINT_MONITOR",
        }
        for entry in feed.entries[:6]
    ]
