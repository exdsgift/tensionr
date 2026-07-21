"""GTI forecasting and narrative-graph generation."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from tensionr.config import ARCHIVE_DIR

logger = logging.getLogger(__name__)


def forecast_gti(
    history: list[dict[str, Any]], archive_dir: Path = ARCHIVE_DIR
) -> dict[str, Any]:
    """Predict GTI for the next 48h (6h steps) with Ridge regression."""
    data: list[dict[str, float]] = []

    if archive_dir.exists():
        for path in sorted(archive_dir.glob("*.json")):
            try:
                archive_data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("skipping unreadable archive %s: %s", path.name, e)
                continue
            date_str = archive_data.get("date")
            gti = archive_data.get("gti")
            if date_str and gti is not None:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                data.append({"ts": dt.timestamp(), "gti": gti})

    for h in history:
        ts = datetime.fromisoformat(h["timestamp"]).timestamp()
        data.append({"ts": ts, "gti": h["score"]})

    if len(data) < 5:
        return {"forecast": [], "confidence": "low", "reason": "insufficient_data"}

    df = pd.DataFrame(data).sort_values("ts").drop_duplicates("ts")

    X = df["ts"].values.reshape(-1, 1)
    y = df["gti"].values
    model = Ridge(alpha=1.0)
    model.fit(X, y)

    last_ts = df["ts"].max()
    future_ts = [last_ts + (i * 3600 * 6) for i in range(1, 9)]
    predictions = np.clip(model.predict(np.array(future_ts).reshape(-1, 1)), 1, 100)

    forecast_points = [
        {"timestamp": datetime.fromtimestamp(ts).isoformat(), "score": int(val)}
        for ts, val in zip(future_ts, predictions)
    ]
    return {
        "forecast": forecast_points,
        "confidence": "medium" if len(data) > 20 else "low",
        "last_training": datetime.now().isoformat(),
    }


def generate_narrative_graph(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Graph of narrative relationships via title keyword overlap (entity proxy)."""
    nodes = []
    edges = []
    stop_words = {"the", "a", "in", "on", "at", "for", "with", "is", "of", "and", "to"}

    subset = articles[: min(len(articles), 100)]
    for i, art in enumerate(subset):
        nodes.append(
            {
                "id": art["url"],
                "title": art["title"],
                "emotion": art.get("narrative_emotion", "unknown"),
                "domain": art.get("domain", "unknown"),
            }
        )
        title_i = set(art["title"].lower().split())
        for j in range(i + 1, len(subset)):
            art_j = subset[j]
            overlap = (
                title_i.intersection(set(art_j["title"].lower().split())) - stop_words
            )
            if len(overlap) >= 2:
                edges.append(
                    {
                        "source": art["url"],
                        "target": art_j["url"],
                        "weight": len(overlap),
                    }
                )

    return {"nodes": nodes, "edges": edges}
