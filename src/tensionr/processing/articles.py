"""Article text sanitation, country deduction and merge/dedup logic."""

import re
from typing import Any

from tensionr.config import ARTICLE_CAP, KNOWN_COUNTRIES


def sanitize_data(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"[<>{}[\]\\]", "", text)


def deduce_country(title: str) -> str:
    title_lower = title.lower()
    for country in KNOWN_COUNTRIES:
        if country.lower() in title_lower:
            return country
    return "Unknown"


def select_new_articles(
    raw_articles: list[dict[str, Any]], existing_articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return raw articles not already known, dropping entries without a URL."""
    existing_urls = {a["url"] for a in existing_articles if a.get("url")}
    return [a for a in raw_articles if a.get("url") and a["url"] not in existing_urls]


def merge_and_cap(
    new_articles: list[dict[str, Any]],
    existing_articles: list[dict[str, Any]],
    cap: int = ARTICLE_CAP,
) -> list[dict[str, Any]]:
    """Merge, sort newest-first by seendate, dedup by URL and cap the window."""
    merged = new_articles + existing_articles
    merged.sort(key=lambda x: x.get("seendate", ""), reverse=True)

    final: list[dict[str, Any]] = []
    seen: set[str] = set()
    for article in merged:
        url = article.get("url")
        if url and url not in seen:
            final.append(article)
            seen.add(url)
    return final[:cap]
