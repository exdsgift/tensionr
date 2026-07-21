"""OpenSky ADS-B telemetry with statistical anomaly detection."""

import logging
from typing import Any

from tensionr.config import MIL_CALLSIGN_PREFIXES, OPENSKY_URL
from tensionr.http_client import request_with_retry

logger = logging.getLogger(__name__)

HIGH_ALTITUDE_M = 13500
VELOCITY_Z_THRESHOLD = 2.5


def fetch_opensky_flights() -> dict[str, Any]:
    logger.info("scanning strategic aerial assets (opensky)...")
    resp = request_with_retry("GET", OPENSKY_URL, timeout=15, retries=1)
    if resp is None:
        logger.warning("OpenSky unreachable")
        return {"status": "offline", "assets": []}
    if resp.status_code != 200:
        logger.warning("OpenSky returned HTTP %d", resp.status_code)
        return {"status": "api_limit", "assets": []}

    try:
        states = resp.json().get("states", []) or []
    except ValueError as e:
        logger.warning("OpenSky payload unparsable: %s", e)
        return {"status": "offline", "assets": []}

    velocities = [s[9] for s in states if s[9] is not None]
    avg_vel = sum(velocities) / len(velocities) if velocities else 200
    std_vel = (
        (sum((x - avg_vel) ** 2 for x in velocities) / len(velocities)) ** 0.5
        if velocities
        else 50
    )

    assets: list[dict[str, Any]] = []
    for s in states:
        callsign = (s[1] or "").strip()
        is_mil = any(callsign.startswith(pre) for pre in MIL_CALLSIGN_PREFIXES)
        altitude = s[7]
        velocity = s[9]

        is_outlier = False
        anomaly_score = 0.0
        if is_mil:
            is_outlier = True
            anomaly_score += 0.5
        if altitude and altitude > HIGH_ALTITUDE_M:
            is_outlier = True
            anomaly_score += 0.3
        if velocity:
            z_score = (velocity - avg_vel) / (std_vel + 1e-6)
            if abs(z_score) > VELOCITY_Z_THRESHOLD:
                is_outlier = True
                anomaly_score += min(abs(z_score) * 0.1, 0.5)

        if is_outlier:
            assets.append(
                {
                    "icao24": s[0],
                    "callsign": callsign if callsign else "U_ID",
                    "origin": s[2],
                    "lat": s[6],
                    "lon": s[5],
                    "alt": int(altitude) if altitude else 0,
                    "vel": int(velocity * 3.6) if velocity else 0,
                    "is_mil": is_mil,
                    "is_outlier": is_outlier,
                    "anomaly_score": round(anomaly_score, 2),
                }
            )

    assets.sort(key=lambda x: x.get("anomaly_score", 0), reverse=True)

    theaters = {"EUROPE": 0, "MIDDLE_EAST": 0, "ASIA_PACIFIC": 0, "AMERICAS": 0}
    for a in assets:
        lat, lon = a["lat"], a["lon"]
        if lat and lon:
            if 35 < lat < 70 and -10 < lon < 40:
                theaters["EUROPE"] += 1
            elif 10 < lat < 45 and 30 < lon < 75:
                theaters["MIDDLE_EAST"] += 1
            elif -10 < lat < 50 and 70 < lon < 150:
                theaters["ASIA_PACIFIC"] += 1
            else:
                theaters["AMERICAS"] += 1

    return {
        "status": "active",
        "assets": assets[:80],
        "count": len(assets),
        "theater": max(theaters, key=theaters.get) if assets else "NONE",
        "global_avg_velocity": int(avg_vel * 3.6),
    }
