"""Rasterise Natural Earth 110m land into a braille coastline for the Ledger.

The map on the page is text: a `<pre>` of characters from the Braille Patterns block
(U+2800), each carrying a 2x4 grid of dots, so a W x H block of characters is a
2W x 4H dot bitmap. This writes one of those blocks, with the projection it was drawn
at, into the same JSON shape `tensionr.ledger.cell` reads.

The projection fields travel with the rows on purpose. #41 was one bug: the crop was
stated once in the rasteriser and again in the code that placed the markers, the two
disagreed, and every marker landed in the wrong place. Nothing downstream may restate
what is written here.

Reproducing the shipped file, which is the only reason to trust a new one:

    curl -sLO https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
    uv run python tools/build_map.py --land ne_110m_land.geojson --width 76 --height 22 \
        --out /tmp/coastline.json
    python -c "import json;a='data/map/coastline.json';b='/tmp/coastline.json';\
print(json.load(open(a))['rows']==json.load(open(b))['rows'])"

prints `True`. Verified 2026-08-04 against `ne_110m_land.geojson` at commit-of-the-day
on `nvkelso/natural-earth-vector@master`: all 1,672 cells identical.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

# The crop the shipped map is drawn at: the poles are empty ocean and empty ice, and
# dropping them lets the populated world fill the frame. Every map this tool writes
# carries these numbers in its own file, so a reader never has to know them.
LAT_TOP, LAT_BOTTOM = 74.0, -56.0
LON_LEFT, LON_RIGHT = -180.0, 180.0

# Which bit of a braille character each dot of its 2x4 grid raises. The block was
# encoded for 6-dot braille first and extended to 8, so rows 1-3 are contiguous and
# row 4 is bolted on at 0x40/0x80 rather than following on.
BITS = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}

logger = logging.getLogger(__name__)


def rings(land: Path) -> list[tuple[float, float, float, float, list]]:
    """Every closed ring in the land layer, each with its bounding box.

    The box is not an optimisation detail: the point-in-polygon test below is O(edges)
    and Natural Earth 110m carries about 10,000 of them, so without a box per ring the
    inner loop runs 10,000 edge tests per dot.
    """
    out = []
    for feature in json.loads(land.read_text("utf-8"))["features"]:
        geometry = feature["geometry"]
        polygons = (
            [geometry["coordinates"]]
            if geometry["type"] == "Polygon"
            else geometry["coordinates"]
        )
        for polygon in polygons:
            for ring in polygon:
                xs = [point[0] for point in ring]
                ys = [point[1] for point in ring]
                out.append((min(xs), max(xs), min(ys), max(ys), ring))
    return out


def inside(x: float, y: float, ring: list) -> bool:
    """Crossing-number point-in-polygon, in degrees."""
    hit = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi:
            hit = not hit
        j = i
    return hit


def land_dots(width: int, height: int, land: Path) -> list[list[int]]:
    """A 2W x 4H bitmap of which dots fall on land, sampled at dot centres.

    Rings are tested until one of them contains the sample, rather than accumulating
    crossings across all of them. That treats every ring as solid land, so a lake
    inside a landmass fills in — which is correct here, because the map draws
    coastlines and Natural Earth's land layer has no lakes in it. Counting parity
    across rings instead moves 245 of the 1,672 cells, so this is not a detail.
    """
    dot_w, dot_h = width * 2, height * 4
    polygons = rings(land)
    dots = [[0] * dot_w for _ in range(dot_h)]
    for row in range(dot_h):
        lat = LAT_TOP - (row + 0.5) * (LAT_TOP - LAT_BOTTOM) / dot_h
        candidates = [p for p in polygons if p[2] <= lat <= p[3]]
        if not candidates:
            continue
        for col in range(dot_w):
            lon = LON_LEFT + (col + 0.5) * (LON_RIGHT - LON_LEFT) / dot_w
            for x0, x1, _, _, ring in candidates:
                if x0 <= lon <= x1 and inside(lon, lat, ring):
                    dots[row][col] = 1
                    break
    return dots


def coastline(dots: list[list[int]]) -> list[list[int]]:
    """Keep the land dots that touch water, four-connected — i.e. the coast.

    Filled continents are the wrong drawing at this resolution: at 152x88 dots the
    land is 68% of the frame's ink and reads as a blob. The outline is 415 cells of
    ink against 1,138, and it reads as a map.
    """
    dot_h, dot_w = len(dots), len(dots[0])
    out = [[0] * dot_w for _ in range(dot_h)]
    for row in range(dot_h):
        for col in range(dot_w):
            if not dots[row][col]:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r, c = row + dr, col + dc
                if not (0 <= r < dot_h and 0 <= c < dot_w) or not dots[r][c]:
                    out[row][col] = 1
                    break
    return out


def pack(dots: list[list[int]], width: int, height: int) -> list[str]:
    """Fold the dot bitmap into one braille character per 2x4 dots."""
    rows = []
    for cell_row in range(height):
        line = ""
        for cell_col in range(width):
            bits = 0
            for (dot_col, dot_row), bit in BITS.items():
                if dots[cell_row * 4 + dot_row][cell_col * 2 + dot_col]:
                    bits |= bit
            line += chr(0x2800 + bits)
        rows.append(line)
    return rows


def build(land: Path, width: int, height: int, note: str) -> dict[str, Any]:
    rows = pack(coastline(land_dots(width, height, land)), width, height)
    return {
        "_comment": note,
        "width": width,
        "height": height,
        "lat_top": LAT_TOP,
        "lat_bottom": LAT_BOTTOM,
        "lon_left": LON_LEFT,
        "lon_right": LON_RIGHT,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python tools/build_map.py",
        description="Rasterise Natural Earth 110m land into a braille coastline.",
    )
    parser.add_argument(
        "--land",
        type=Path,
        required=True,
        help="ne_110m_land.geojson from nvkelso/natural-earth-vector",
    )
    parser.add_argument("--width", type=int, required=True, help="characters across")
    parser.add_argument("--height", type=int, required=True, help="characters down")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--comment", default="", help="the file's own _comment")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data = build(args.land, args.width, args.height, args.comment)
    args.out.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    ink = sum(1 for row in data["rows"] for character in row if character != "⠀")
    logger.info(
        "wrote %s: %dx%d characters = %dx%d dots, %d of %d cells carry ink",
        args.out,
        args.width,
        args.height,
        args.width * 2,
        args.height * 4,
        ink,
        args.width * args.height,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
