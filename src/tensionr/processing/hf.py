"""Hugging Face inference: batched emotion classification, SITREP and strategic insight."""

import logging
from typing import Any

from tensionr.config import HF_BATCH_SIZE, HF_TOKEN
from tensionr.http_client import request_with_retry

logger = logging.getLogger(__name__)

EMOTIONS_URL = (
    "https://router.huggingface.co/hf-inference/models/SamLowe/roberta-base-go_emotions"
)
SITREP_URL = (
    "https://router.huggingface.co/hf-inference/models/sshleifer/distilbart-cnn-12-6"
)
INSIGHT_URL = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"

UNKNOWN = {"emotion": "unknown", "bias_risk": 0}

# GoEmotions label -> (bucket, bias-risk multiplier)
_LABEL_BUCKETS: dict[str, tuple[str, float]] = {
    **dict.fromkeys(["fear", "nervousness", "anxiety", "confusion"], ("fear", 1.2)),
    **dict.fromkeys(
        ["anger", "annoyance", "disapproval", "disgust", "frustration"], ("anger", 1.3)
    ),
    **dict.fromkeys(
        ["sadness", "grief", "remorse", "disappointment", "embarrassment"],
        ("sadness", 1.1),
    ),
    **dict.fromkeys(
        ["surprise", "realization", "curiosity", "excitement", "joy", "pride"],
        ("surprise", 0.8),
    ),
    **dict.fromkeys(
        [
            "optimism",
            "relief",
            "gratitude",
            "approval",
            "love",
            "admiration",
            "desire",
            "caring",
        ],
        ("positive", 0.5),
    ),
}


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {HF_TOKEN.strip()}"}


def _map_prediction(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    top = max(predictions, key=lambda x: x.get("score", 0))
    label = top.get("label", "").lower()
    score = top.get("score", 0)
    emotion, multiplier = _LABEL_BUCKETS.get(label, ("neutral", 1.0))
    return {"emotion": emotion, "bias_risk": min(int(score * 100 * multiplier), 100)}


def classify_emotions_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Classify many titles with batched requests (one POST per HF_BATCH_SIZE inputs)."""
    if not HF_TOKEN or not texts:
        return [dict(UNKNOWN) for _ in texts]

    results: list[dict[str, Any]] = []
    for start in range(0, len(texts), HF_BATCH_SIZE):
        batch = [t[:500] if t else "" for t in texts[start : start + HF_BATCH_SIZE]]
        resp = request_with_retry(
            "POST",
            EMOTIONS_URL,
            headers=_headers(),
            json={"inputs": batch, "options": {"wait_for_model": True}},
            timeout=60,
        )
        if resp is None or resp.status_code != 200:
            if resp is not None:
                logger.warning(
                    "HF emotions API error %d: %s", resp.status_code, resp.text[:200]
                )
            results.extend(dict(UNKNOWN) for _ in batch)
            continue
        payload = resp.json()
        # One list of {label, score} per input
        for item in payload if isinstance(payload, list) else []:
            if isinstance(item, list) and item:
                results.append(_map_prediction(item))
            else:
                results.append(dict(UNKNOWN))
        # Defensive: keep alignment if the API returned fewer items than inputs
        while len(results) < start + len(batch):
            results.append(dict(UNKNOWN))
    return results


def generate_sitrep(alerts: list[str]) -> str:
    if not HF_TOKEN or not alerts:
        return "Tactical bulletin pending: awaiting signal density..."

    text = "Tactical Alerts: " + ". ".join(alerts[:10])
    resp = request_with_retry(
        "POST",
        SITREP_URL,
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "inputs": text,
            "parameters": {"max_length": 80, "min_length": 30, "do_sample": False},
            "options": {"wait_for_model": True},
        },
        timeout=30,
    )
    if resp is not None and resp.status_code == 200:
        result = resp.json()
        if isinstance(result, list) and result:
            summary = result[0].get("summary_text", "").strip()
            if summary:
                return summary[:250]
    logger.warning("SITREP generation degraded to fallback text")
    return "Intelligence Synthesis Active: Multi-domain nodes reporting normal operational baseline."


def generate_strategic_insight(
    articles: list[dict[str, Any]],
    markets: list[dict[str, Any]],
    flights: dict[str, Any],
) -> str:
    """Cross-domain LLM correlation (Mistral-7B-Instruct)."""
    if not HF_TOKEN:
        return "Strategic analyst offline: awaiting secure handshake."

    top_news = [a["title"] for a in articles[:8]]
    market_alerts = [
        f"{m['symbol']} moved {m['change']}%"
        for m in (markets or [])
        if abs(m["change"]) > 1.5
    ]
    anomalies = [a for a in flights.get("assets", []) if a.get("is_outlier")]
    flight_context = f"{len(anomalies)} anomalies detected in {flights.get('theater', 'unknown')} theater"

    prompt = (
        "<s>[INST] You are a Senior Geopolitical Intelligence Analyst. Analyze the following "
        "SIGINT/OSINT data nodes for HIDDEN CORRELATIONS and ESCALATION RISKS.\n\n"
        "NEWS FEED:\n- " + "\n- ".join(top_news) + "\n\n"
        "MARKET ANOMALIES: "
        + (", ".join(market_alerts) if market_alerts else "Stable")
        + "\n"
        f"AERIAL TELEMETRY: {flight_context}\n\n"
        "Identify ONE non-obvious strategic link between these domains. If news mentions a region "
        "and telemetry shows anomalies there, highlight the tactical significance. "
        "Be specific, clinical, and predictive. Max 25 words.\n"
        "FORMAT: CORRELATION: [Your insight] [/INST]"
    )
    resp = request_with_retry(
        "POST",
        INSIGHT_URL,
        headers=_headers(),
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 80,
                "temperature": 0.4,
                "repetition_penalty": 1.2,
            },
            "options": {"wait_for_model": True},
        },
        timeout=30,
    )
    if resp is not None and resp.status_code == 200:
        result = resp.json()
        text = ""
        if isinstance(result, list) and result:
            text = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            text = result.get("generated_text", "")
        if "CORRELATION:" in text:
            insight = text.split("CORRELATION:")[1].strip().split("\n")[0]
            if len(insight) > 10:
                return insight
    logger.warning("strategic insight degraded to fallback text")
    return "Analyzing multi-domain vectors: signal density insufficient for high-confidence correlation."
