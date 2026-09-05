"""The shipped map and coordinate tables have to agree with each other.

These run against the real files in `data/`, not fixtures. They are the guard that
caught the defect they encode: the coastline is rasterised at one crop and the marker
positions were computed at another, so every point on the map was displaced. Nothing in
the type system or the schema notices that — only a check that the two files describe
the same planet does.
"""

import json
from pathlib import Path

from tensionr.map import cell

# `data/` is the contract between the engine and the frontend, so it stays at the
# repository root rather than inside `backend/` (#81). Two parents up from this file,
# not one.
DATA = Path(__file__).resolve().parents[2] / "data"

COASTLINE = json.loads((DATA / "map" / "coastline.json").read_text("utf-8"))
NARROW = json.loads((DATA / "map" / "coastline-narrow.json").read_text("utf-8"))
COORDINATES = json.loads((DATA / "polities" / "coordinates.json").read_text("utf-8"))
DOMAINS = json.loads((DATA / "polities" / "domains.json").read_text("utf-8"))

PROJECTION_FIELDS = (
    "width",
    "height",
    "lat_top",
    "lat_bottom",
    "lon_left",
    "lon_right",
)

MAPS = {"coastline.json": COASTLINE, "coastline-narrow.json": NARROW}

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


def test_every_coordinate_is_on_the_planet_and_inside_every_map_crop():
    for polity, (lat, lon) in COORDINATES["polities"].items():
        assert -90 <= lat <= 90 and -180 <= lon <= 180, polity
        for which, projection in MAPS.items():
            assert projection["lat_bottom"] <= lat <= projection["lat_top"], (
                f"{polity} is outside {which}"
            )


def test_every_map_carries_its_own_complete_projection():
    """#41: a map without its projection invites the code to restate one, and guess."""
    for which, projection in MAPS.items():
        for field in PROJECTION_FIELDS:
            assert field in projection, f"{which} has no {field}"
        assert len(projection["rows"]) == projection["height"], which
        assert {len(row) for row in projection["rows"]} == {projection["width"]}, which
        assert all(
            "⠀" <= character <= "⣿" for row in projection["rows"] for character in row
        ), f"{which} holds something that is not a braille character"


def test_the_narrow_map_is_a_narrower_map_and_not_a_copy():
    """A second file that held the same grid would be a squeezed map, not another one."""
    assert NARROW["width"] < COASTLINE["width"]
    assert NARROW["height"] < COASTLINE["height"]
    assert NARROW["rows"] != COASTLINE["rows"]
    # Same planet, same crop: the two are the same projection at two resolutions, so a
    # reader moving between them sees one map rather than two different worlds.
    for field in PROJECTION_FIELDS[2:]:
        assert NARROW[field] == COASTLINE[field], field


def _on_a_traced_coast(lat: float, lon: float, projection: dict) -> bool:
    col, row = cell(lat, lon, projection)
    if not (
        0 <= int(row) < projection["height"] and 0 <= int(col) < projection["width"]
    ):
        return False
    return projection["rows"][int(row)][int(col)] != BLANK


def test_coastal_capitals_land_on_the_coastline_every_map_actually_draws():
    """Both maps, because a marker is placed against whichever one the reader is shown.

    32 of 34 on each at the time of writing — the narrow map loses nothing here, which
    is the measurement that decided its size (#51): halving the resolution halves the
    cells but each cell covers four times the area, so a coastal capital is no less
    likely to land on drawn coast. A projection mismatch moves most of them, which is
    the failure this catches.
    """
    for which, projection in MAPS.items():
        hits = sum(
            _on_a_traced_coast(*COORDINATES["polities"][p], projection) for p in COASTAL
        )
        assert hits >= 30, (
            f"only {hits} of {len(COASTAL)} coastal capitals hit a coast cell on {which}"
        )


def test_the_crop_the_prototype_used_would_fail_this_check():
    """Without this, the check above could pass on any projection and prove nothing."""
    wrong = {**COASTLINE, "lat_top": 82.0, "lat_bottom": -58.0}
    hits = sum(_on_a_traced_coast(*COORDINATES["polities"][p], wrong) for p in COASTAL)
    assert hits < 30, f"{hits} hits on a crop that does not match the map"


def test_the_narrow_map_cannot_police_the_projection_by_itself():
    """Measured, and the reason the check above stays on the full-resolution map.

    The prototype's 82N/58S crop scores 25 of 34 against the 76x22 grid and **30** of 34
    against the 38x11 one, because a cell four times the area swallows the displacement.
    So the narrow map is worth checking but is not the guard: if the wide check above is
    ever dropped, a projection mismatch walks straight through.
    """
    wrong = {**NARROW, "lat_top": 82.0, "lat_bottom": -58.0}
    hits = sum(_on_a_traced_coast(*COORDINATES["polities"][p], wrong) for p in COASTAL)
    assert hits >= 30, (
        f"{hits} hits: the narrow grid has become discriminating enough to police the "
        "projection on its own, and the note above is now wrong"
    )
