"""Data-contract test: the exact key-paths the frontend reads must exist with the right types.

Derived from api.js / app.js / charts.js / map.js / tactical_map.js consumption.
Points at the repo's data/ by default; set TENSIONR_SHAPE_DIR to validate the
output of a fresh pipeline run instead.
"""

import json
import os
from pathlib import Path

import pytest

SHAPE_DIR = Path(os.getenv("TENSIONR_SHAPE_DIR", "data"))

NUMBER = (int, float)

ARTICLE_REQUIRED = {
    "url": str,
    "title": str,
    "domain": str,
    "seendate": str,
    "source": str,
    "sourcecountry": str,
    "narrative_emotion": str,
    "manipulation_score": NUMBER,
}

REMOVED_KEYS = {
    "status.json": ["security_check"],
    "articles": [
        "reddit_shares",
        "mastodon_shares",
        "bot_probability",
        "target_platforms",
    ],
}


def _load(name: str) -> dict:
    path = SHAPE_DIR / name
    if not path.exists():
        pytest.skip(f"{path} not present")
    return json.loads(path.read_text(encoding="utf-8"))


def test_news_contract():
    news = _load("news.json")
    articles = news["articles"]
    assert isinstance(articles, list) and articles
    for i, article in enumerate(articles):
        for key, expected in ARTICLE_REQUIRED.items():
            assert key in article, f"articles[{i}] missing {key}"
            assert isinstance(article[key], expected), f"articles[{i}].{key} wrong type"

    stats = news["stats"]
    assert isinstance(stats["total_nodes"], int)
    assert isinstance(stats["top_domains"], dict)
    assert isinstance(stats["source_countries"], dict)
    keywords = stats["top_keywords"]
    assert isinstance(keywords, dict) and keywords
    sample = next(iter(keywords.values()))
    assert isinstance(sample["count"], int) and isinstance(sample["type"], str)

    graph = news["narrative_graph"]
    assert isinstance(graph["nodes"], list) and isinstance(graph["edges"], list)
    assert isinstance(news["timeline_vol"], list)


def test_status_contract():
    status = _load("status.json")
    assert isinstance(status["last_updated"], str)
    assert isinstance(status["global_tension_index"], int)
    assert 1 <= status["global_tension_index"] <= 100
    history = status["gti_history"]
    assert isinstance(history, list) and history
    assert isinstance(history[0]["timestamp"], str) and isinstance(
        history[0]["score"], NUMBER
    )
    for point in status["gti_forecast"]:
        assert isinstance(point["timestamp"], str) and isinstance(
            point["score"], NUMBER
        )
    assert status["forecast_confidence"] in ("low", "medium", "high")


def test_markets_contract():
    markets = _load("markets.json")
    intel = markets["market_intel"]
    assert isinstance(intel, list)
    for m in intel:
        assert isinstance(m["symbol"], str)
        assert isinstance(m["price"], NUMBER)
        assert isinstance(m["change"], NUMBER)


def test_telemetry_contract():
    telemetry = _load("telemetry.json")
    intel = telemetry["flight_intel"]
    assert isinstance(intel["status"], str)
    assert isinstance(intel["assets"], list)
    for asset in intel["assets"]:
        for key in (
            "icao24",
            "callsign",
            "lat",
            "lon",
            "alt",
            "vel",
            "is_mil",
            "is_outlier",
        ):
            assert key in asset, f"asset missing {key}"


def test_intelligence_contract():
    intel = _load("intelligence.json")
    assert isinstance(intel["sitrep"], str)
    assert isinstance(intel["strategic_insight"], str)
    for item in intel["cyber_intel"]:
        assert isinstance(item["title"], str) and isinstance(item["link"], str)
    for item in intel["raw_chatter"]:
        assert isinstance(item["title"], str) and isinstance(item["link"], str)


def test_archive_contract():
    archive_dir = SHAPE_DIR / "archive"
    if not archive_dir.exists():
        pytest.skip("no archive dir")
    latest = sorted(archive_dir.glob("*.json"))[-1]
    snapshot = json.loads(latest.read_text(encoding="utf-8"))
    assert isinstance(snapshot["date"], str)
    assert isinstance(snapshot["gti"], NUMBER)
    assert isinstance(snapshot["sitrep"], str)
    assert isinstance(snapshot["top_keywords"], dict)
    assert isinstance(snapshot["top_domains"], dict)


def test_removed_fields_stay_removed():
    """Dead fields must not creep back (only enforced on fresh pipeline output).

    Note: articles inherited from an old news.json may carry the removed
    reddit/mastodon fields until they age out of the 500-item window, so only
    the status.json contract is enforced here.
    """
    if not os.getenv("TENSIONR_SHAPE_DIR"):
        pytest.skip("only enforced on fresh pipeline output")
    status = _load("status.json")
    for key in REMOVED_KEYS["status.json"]:
        assert key not in status
    assert "gti_components" in status
