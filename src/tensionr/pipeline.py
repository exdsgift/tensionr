"""Pipeline orchestration: fetch -> process -> score -> write, with stage timing."""

import logging
import time
from datetime import datetime
from typing import Any

import pandas as pd

from tensionr import output, scoring
from tensionr.config import DEADLINE_SECONDS, HF_TOKEN, MAX_NEW_ARTICLES
from tensionr.fetchers.flights import fetch_opensky_flights
from tensionr.fetchers.intel import fetch_cyber_intel, fetch_raw_chatter
from tensionr.fetchers.markets import fetch_market_data
from tensionr.fetchers.news import (
    fetch_gdelt_articles,
    fetch_gdelt_timeline,
    fetch_rss_news,
)
from tensionr.processing.analytics import forecast_gti, generate_narrative_graph
from tensionr.processing.articles import (
    deduce_country,
    merge_and_cap,
    sanitize_data,
    select_new_articles,
)
from tensionr.processing.hf import (
    classify_emotions_batch,
    generate_sitrep,
    generate_strategic_insight,
)
from tensionr.processing.keywords import extract_keywords

logger = logging.getLogger(__name__)


class StageTimer:
    def __init__(self) -> None:
        self.start = time.monotonic()
        self.last = self.start

    def lap(self, stage: str) -> None:
        now = time.monotonic()
        logger.info(
            "[timing] %s: %.1fs (total %.1fs)", stage, now - self.last, now - self.start
        )
        self.last = now

    def elapsed(self) -> float:
        return time.monotonic() - self.start


def enrich_new_articles(new_articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize, deduce country and attach batched NLP emotion/bias fields."""
    if len(new_articles) > MAX_NEW_ARTICLES:
        logger.info(
            "capping new articles: %d -> %d", len(new_articles), MAX_NEW_ARTICLES
        )
        new_articles = new_articles[:MAX_NEW_ARTICLES]

    for art in new_articles:
        art["title"] = sanitize_data(art.get("title", ""))
        if "sourcecountry" not in art:
            art["sourcecountry"] = deduce_country(art["title"])

    if not HF_TOKEN:
        logger.warning("HF_TOKEN not set: ML analysis disabled for this run")
    nlp_results = classify_emotions_batch([a["title"] for a in new_articles])
    for art, nlp_intel in zip(new_articles, nlp_results):
        art["narrative_emotion"] = nlp_intel["emotion"]
        art["manipulation_score"] = int(nlp_intel["bias_risk"])
    return new_articles


def run() -> None:
    timer = StageTimer()
    logger.info("initiating synchronization...")

    existing_articles = output.load_existing_articles()

    gdelt_articles = fetch_gdelt_articles()
    rss_articles = fetch_rss_news()
    new_raw = gdelt_articles + rss_articles
    timer.lap("fetch news")

    if not new_raw and not existing_articles:
        logger.error("no signals found and no local cache; aborting run")
        return

    unique_new = select_new_articles(new_raw, existing_articles)
    logger.info("processing %d new signals", len(unique_new))
    processed_new = enrich_new_articles(unique_new)
    timer.lap("nlp enrichment")

    final_articles = merge_and_cap(processed_new, existing_articles)

    cyber_intel = fetch_cyber_intel() or output.fallback_cyber_intel()
    raw_chatter = fetch_raw_chatter()
    market_intel = fetch_market_data() or output.fallback_market_intel()
    flight_intel = fetch_opensky_flights()
    if flight_intel.get("status") == "offline":
        flight_intel = output.fallback_flight_intel()
    timer.lap("fetch intel/markets/flights")

    gti, gti_components = scoring.calculate_gti(
        final_articles, market_intel, flight_intel
    )
    logger.info("GTI %d %s", gti, gti_components)

    # Optional LLM stages: skipped near the CI timeout so the write phase always runs.
    alerts = [
        f"Narrative Spike: {a['title']}"
        for a in final_articles[:15]
        if a.get("manipulation_score", 0) > 85
    ]
    alerts.extend(
        f"Aerial Anomaly: {f['callsign']}"
        for f in flight_intel.get("assets", [])
        if f.get("is_outlier")
    )
    if timer.elapsed() < DEADLINE_SECONDS:
        sitrep = generate_sitrep(alerts[:20])
        strategic_insight = generate_strategic_insight(
            final_articles, market_intel, flight_intel
        )
    else:
        logger.warning("deadline reached (%.0fs): skipping LLM stages", timer.elapsed())
        sitrep = "Intelligence Synthesis Active: Multi-domain nodes reporting normal operational baseline."
        strategic_insight = "Analyzing multi-domain vectors: signal density insufficient for high-confidence correlation."
    logger.info("[SITREP] %s", sitrep)
    logger.info("[INSIGHT] %s", strategic_insight)
    timer.lap("llm synthesis")

    df = pd.DataFrame(final_articles)
    top_keywords = extract_keywords(final_articles)
    narrative_graph = generate_narrative_graph(final_articles)
    timeline = fetch_gdelt_timeline()
    timer.lap("keywords/graph/timeline")

    current_time = datetime.now().isoformat()
    gti_history = output.append_gti_history(gti, current_time)
    forecast_data = forecast_gti(gti_history)

    news_data = {
        "articles": final_articles,
        "timeline_vol": timeline,
        "stats": {
            "top_domains": df["domain"].value_counts().head(8).to_dict()
            if not df.empty
            else {},
            "source_countries": df["sourcecountry"].value_counts().to_dict()
            if not df.empty
            else {},
            "top_keywords": top_keywords,
            "total_nodes": len(final_articles),
        },
        "narrative_graph": narrative_graph,
    }
    status_data = {
        "last_updated": current_time,
        "global_tension_index": gti,
        "gti_components": gti_components,
        "gti_history": gti_history,
        "gti_forecast": forecast_data.get("forecast", []),
        "forecast_confidence": forecast_data.get("confidence", "low"),
    }

    output.write_outputs(
        {
            "news.json": news_data,
            "markets.json": {"market_intel": market_intel},
            "telemetry.json": {"flight_intel": flight_intel},
            "intelligence.json": {
                "cyber_intel": cyber_intel,
                "raw_chatter": raw_chatter,
                "sitrep": sitrep,
                "strategic_insight": strategic_insight,
            },
            "status.json": status_data,
        }
    )
    output.write_archive_snapshot(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "gti": gti,
            "sitrep": sitrep,
            "top_keywords": top_keywords,
            "top_domains": news_data["stats"]["top_domains"],
        }
    )
    timer.lap("write outputs")
    logger.info("sync complete")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    run()


if __name__ == "__main__":
    main()
