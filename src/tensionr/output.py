"""Load previous state, build the 5 JSON payloads and the daily archive snapshot."""

import json
import logging
from pathlib import Path
from typing import Any

from tensionr.config import ARCHIVE_DIR, DATA_DIR, GTI_HISTORY_CAP

logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("could not read %s: %s", path, e)
        return None


def load_existing_articles() -> list[dict[str, Any]]:
    payload = load_json(DATA_DIR / "news.json")
    return payload.get("articles", []) if payload else []


def fallback_cyber_intel() -> list[dict[str, Any]]:
    payload = load_json(DATA_DIR / "intelligence.json")
    return payload.get("cyber_intel", []) if payload else []


def fallback_market_intel() -> list[dict[str, Any]]:
    payload = load_json(DATA_DIR / "markets.json")
    return payload.get("market_intel", []) if payload else []


def fallback_flight_intel() -> dict[str, Any]:
    payload = load_json(DATA_DIR / "telemetry.json")
    intel = payload.get("flight_intel") if payload else None
    if intel:
        intel["status"] = "stale"
        return intel
    return {"status": "stale", "assets": []}


def append_gti_history(gti: int, timestamp: str) -> list[dict[str, Any]]:
    payload = load_json(DATA_DIR / "status.json")
    history = payload.get("gti_history", []) if payload else []
    history.append({"timestamp": timestamp, "score": gti})
    return history[-GTI_HISTORY_CAP:]


def write_outputs(modules: dict[str, dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, content in modules.items():
        path = DATA_DIR / filename
        path.write_text(json.dumps(content, indent=4), encoding="utf-8")
        logger.info("wrote %s", path)


def write_archive_snapshot(snapshot: dict[str, Any]) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / f"{snapshot['date']}.json"
    path.write_text(json.dumps(snapshot, indent=4), encoding="utf-8")
    logger.info("wrote archive %s", path)
    return path
