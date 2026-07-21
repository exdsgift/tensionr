"""Global Tension Index: pure scoring logic, no I/O."""

from typing import Any

BASE = 5


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def _narrative_component(articles: list[dict[str, Any]]) -> float:
    """0-40: negative-emotion ratio (0-30) + mean manipulation intensity (0-10)."""
    known = [a for a in articles if a.get("narrative_emotion") not in (None, "unknown")]
    if not known:
        return 0.0
    neg = sum(1 for a in known if a["narrative_emotion"] in ("fear", "anger"))
    sentiment = (neg / len(known)) * 30
    intensity = (
        (sum(a.get("manipulation_score", 0) for a in known) / len(known)) / 100 * 10
    )
    return sentiment + intensity


def _market_component(market_intel: list[dict[str, Any]]) -> float:
    """0-30: absolute VIX level (0-15) + signed daily shock (-5..15).

    Unlike the old formula there is no fixed baseline and falling VIX
    subtracts, so calm markets actually read as calm.
    """
    if not market_intel:
        return 0.0
    by_symbol = {m["symbol"]: m for m in market_intel}

    vix = by_symbol.get("VIX (VOLATILITY)")
    vix_level = _clamp((vix["price"] - 12) * 1.0, 0, 15) if vix else 0.0

    shock = 0.0
    if vix:
        shock += _clamp(vix["change"] * 1.5, -5, 8)
    gold = by_symbol.get("GOLD (XAU)")
    if gold and gold["change"] > 1:
        shock += min((gold["change"] - 1) * 3, 7)
    for symbol in ("S&P 500", "NASDAQ 100"):
        equity = by_symbol.get(symbol)
        if equity and equity["change"] < 0:
            shock += min(abs(equity["change"]) * 2.5, 10)
    shock = _clamp(shock, -5, 15)

    return _clamp(vix_level + shock, 0, 30)


def _telemetry_component(flight_intel: dict[str, Any]) -> float:
    """0-30: military volume (0-12) + multi-signal anomalies (0-18).

    Only anomaly_score >= 0.8 counts as severe: every tracked asset is an
    "outlier" by construction, so raw outlier counts carry no signal.
    """
    if not flight_intel or flight_intel.get("status") != "active":
        return 0.0
    assets = flight_intel.get("assets", [])
    mil_count = sum(1 for a in assets if a.get("is_mil"))
    high_severity = sum(1 for a in assets if a.get("anomaly_score", 0) >= 0.8)
    mil = min(mil_count / 25, 1.0) * 12
    severity = min(high_severity / 8, 1.0) * 18
    return mil + severity


def calculate_gti(
    articles: list[dict[str, Any]],
    market_intel: list[dict[str, Any]],
    flight_intel: dict[str, Any],
) -> tuple[int, dict[str, float]]:
    """Composite Global Tension Index in [1, 100] plus its components.

    Expected regimes: calm ~25-35, elevated ~50-65, crisis 80+.
    """
    narrative = _narrative_component(articles or [])
    market = _market_component(market_intel or [])
    telemetry = _telemetry_component(flight_intel or {})

    gti = int(round(_clamp(BASE + narrative + market + telemetry, 1, 100)))
    components = {
        "base": float(BASE),
        "narrative": round(narrative, 1),
        "market": round(market, 1),
        "telemetry": round(telemetry, 1),
    }
    return gti, components
