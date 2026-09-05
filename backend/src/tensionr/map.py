"""Projecting a coordinate onto a rasterised coastline.

One function, kept in the engine rather than in whatever renders the map, because it is
the rule the *data* has to satisfy and `tests/test_map_data.py` is what enforces it.

The frontend needs the same projection to place its markers, so it is expressed twice —
once here, once in TypeScript. That duplication is deliberate and is exactly why the
projection must be read out of the coastline file rather than restated as constants:
two copies of a formula that both read their numbers from the same file agree; two
copies that each carry their own numbers drift, silently, into markers in the wrong
place.

Dependency-free on purpose, so validating the map data needs nothing installed.
"""

from typing import Any


def cell(lat: float, lon: float, projection: dict[str, Any]) -> tuple[float, float]:
    """Fractional character cell for a coordinate, in the coastline's own projection.

    Read from the coastline file rather than restated here. The prototype encoded the
    crop twice — 82N/58S in the position formula against the 74N/56S the map was
    actually rasterised at — and every marker landed in the wrong place. One source for
    the projection is the fix; a constant in this module would only move the bug.
    """
    top, bottom = projection["lat_top"], projection["lat_bottom"]
    left, right = projection["lon_left"], projection["lon_right"]
    col = (lon - left) / (right - left) * projection["width"]
    row = (top - lat) / (top - bottom) * projection["height"]
    return col, row
