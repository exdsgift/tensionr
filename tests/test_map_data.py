"""The shipped map and coordinate tables have to agree with each other.

These run against the real files in `data/`, not fixtures. They are the guard that
caught the defect they encode: the coastline is rasterised at one crop and the marker
positions were computed at another, so every point on the map was displaced. Nothing in
the type system or the schema notices that — only a check that the two files describe
the same planet does.
"""

import json
from pathlib import Path

from tensionr.ledger import cell

DATA = Path(__file__).resolve().parent.parent / "data"

COASTLINE = json.loads((DATA / "map" / "coastline.json").read_text("utf-8"))
COORDINATES = json.loads((DATA / "polities" / "coordinates.json").read_text("utf-8"))
DOMAINS = json.loads((DATA / "polities" / "domains.json").read_text("utf-8"))

BLANK = "⠀"  # braille with no dots raised

# Capitals on or within a few kilometres of a coast. Chosen because a coastline is the
# only feature this map draws, so a coastal capital is the one case where "did the point
# land in the right place" has an answer the data itself can check.
COASTAL = [
    "Cuba",
    "Denmark",
    "Dominican Republic",
    "Ecuador",
    "Estonia",
    "Finland",
    "Ghana",
    "Greece",
    "Iceland",
    "Israel",
    "Japan",
    "Kenya",
    "Kuwait",
    "Latvia",
    "Lebanon",
    "Morocco",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Oman",
    "Panama",
    "Peru",
    "Philippines",
    "Portugal",
    "Qatar",
    "Singapore",
    "South Korea",
    "Sri Lanka",
    "Sweden",
    "Tunisia",
    "United Arab Emirates",
    "United Kingdom",
    "Uruguay",
    "Venezuela",
]


def polities_in_the_domain_table() -> set[str]:
    return {
        value for key in ("domains", "tlds") for value in DOMAINS[key].values() if value
    }


def test_every_polity_the_table_can_name_can_be_placed_on_the_map():
    """A polity with no coordinate is counted but never drawn, so the gap is silent."""
    assert polities_in_the_domain_table() <= set(COORDINATES["polities"])


def test_no_coordinate_names_a_polity_the_table_cannot_produce():
    assert set(COORDINATES["polities"]) <= polities_in_the_domain_table()


def test_every_coordinate_is_on_the_planet_and_inside_the_map_crop():
    for polity, (lat, lon) in COORDINATES["polities"].items():
        assert -90 <= lat <= 90 and -180 <= lon <= 180, polity
        assert COASTLINE["lat_bottom"] <= lat <= COASTLINE["lat_top"], polity


def _on_a_traced_coast(lat: float, lon: float, projection: dict) -> bool:
    col, row = cell(lat, lon, projection)
    if not (
        0 <= int(row) < projection["height"] and 0 <= int(col) < projection["width"]
    ):
        return False
    return projection["rows"][int(row)][int(col)] != BLANK


def test_coastal_capitals_land_on_the_coastline_the_map_actually_draws():
    hits = sum(
        _on_a_traced_coast(*COORDINATES["polities"][p], COASTLINE) for p in COASTAL
    )
    # 33 of 34 at the time of writing. A regenerated map may move a cell or two, but a
    # projection mismatch moves most of them, which is the failure this catches.
    assert hits >= 30, (
        f"only {hits} of {len(COASTAL)} coastal capitals hit a coast cell"
    )


def test_the_crop_the_prototype_used_would_fail_this_check():
    """Without this, the check above could pass on any projection and prove nothing."""
    wrong = {**COASTLINE, "lat_top": 82.0, "lat_bottom": -58.0}
    hits = sum(_on_a_traced_coast(*COORDINATES["polities"][p], wrong) for p in COASTAL)
    assert hits < 30, f"{hits} hits on a crop that does not match the map"
