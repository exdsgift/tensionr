import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from typing import List, Dict, Any, Optional

def forecast_gti(history: List[Dict[str, Any]], archive_dir: str = "data/archive") -> Dict[str, Any]:
    """
    Predicts GTI score for the next 24-48 hours using a Ridge regression model
    based on historical GTI trends and archives.
    """
    # 1. Prepare Dataset
    data = []
    
    # Load from archives
    if os.path.exists(archive_dir):
        for filename in sorted(os.listdir(archive_dir)):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(archive_dir, filename), "r") as f:
                        archive_data = json.load(f)
                        date_str = archive_data.get("date")
                        gti = archive_data.get("gti")
                        if date_str and gti:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                            data.append({"ts": dt.timestamp(), "gti": gti})
                except:
                    continue
    
    # Add current history points if available
    for h in history:
        ts = datetime.fromisoformat(h["timestamp"]).timestamp()
        data.append({"ts": ts, "gti": h["score"]})
        
    if len(data) < 5:
        return {"forecast": [], "confidence": "low", "reason": "insufficient_data"}
    
    df = pd.DataFrame(data).sort_values("ts").drop_duplicates("ts")
    
    # 2. Train Model (Ridge Regression for stability with small data)
    X = df["ts"].values.reshape(-1, 1)
    y = df["gti"].values
    
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    
    # 3. Predict next 48 hours (in 6h intervals)
    last_ts = df["ts"].max()
    future_ts = [last_ts + (i * 3600 * 6) for i in range(1, 9)]
    predictions = model.predict(np.array(future_ts).reshape(-1, 1))
    
    # Constrain predictions to [1, 100]
    predictions = np.clip(predictions, 1, 100)
    
    forecast_points = []
    for ts, val in zip(future_ts, predictions):
        forecast_points.append({
            "timestamp": datetime.fromtimestamp(ts).isoformat(),
            "score": int(val)
        })
        
    return {
        "forecast": forecast_points,
        "confidence": "medium" if len(data) > 20 else "low",
        "last_training": datetime.now().isoformat()
    }

def generate_narrative_graph(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates a graph of narrative relationships based on entity overlap.
    """
    nodes = []
    edges = []
    
    # Sample articles for performance
    sample_size = min(len(articles), 100)
    subset = articles[:sample_size]
    
    for i, art in enumerate(subset):
        nodes.append({
            "id": art["url"],
            "title": art["title"],
            "emotion": art.get("narrative_emotion", "unknown"),
            "domain": art.get("domain", "unknown")
        })
        
        # Simple overlap detection (hypothetical, real logic would use extracted entities)
        # For now we use title keyword overlap as proxy
        title_i = set(art["title"].lower().split())
        for j in range(i + 1, len(subset)):
            art_j = subset[j]
            title_j = set(art_j["title"].lower().split())
            overlap = title_i.intersection(title_j)
            
            # Filter common words
            stop_words = {"the", "a", "in", "on", "at", "for", "with", "is", "of", "and", "to"}
            meaningful_overlap = overlap - stop_words
            
            if len(meaningful_overlap) >= 2:
                edges.append({
                    "source": art["url"],
                    "target": art_j["url"],
                    "weight": len(meaningful_overlap)
                })
                
    return {"nodes": nodes, "edges": edges}
