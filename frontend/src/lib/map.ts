/**
 * Placing polities on a braille coastline.
 *
 * The projection is read out of the coastline file, never restated here. The prototype
 * encoded the crop twice — 82N/58S in the position formula against the 74N/56S the map
 * was actually rasterised at — and every marker landed in the wrong place. One source
 * for the projection is the fix; a constant in this module would only move the bug.
 *
 * `backend/src/tensionr/map.py` holds the same formula for the same reason, and
 * `backend/tests/test_map_data.py` is what keeps the shipped data honest to it. Two
 * copies of a formula that both read their numbers from the same file agree; two copies
 * that each carry their own numbers drift.
 */

import { PRESENT, type Coastline, type Story } from "./stories";

export interface Marker {
  /** Label, already phrased: "Spain · named" / "Peru · did not name". */
  n: string;
  /** Fractional character cell, column then row. */
  c: number;
  r: number;
  /** Whether at least one of this polity's sources named the actor. */
  on: boolean;
}

/** Fractional character cell for a coordinate, in the coastline's own projection. */
export function cell(
  lat: number,
  lon: number,
  projection: Coastline,
): [number, number] {
  const { lat_top: top, lat_bottom: bottom, lon_left: left, lon_right: right } =
    projection;
  const col = ((lon - left) / (right - left)) * projection.width;
  const row = ((top - lat) / (top - bottom)) * projection.height;
  return [col, row];
}

/**
 * Map markers for the polities that carried the story.
 *
 * Two states, both measured: a polity **named** the band's actor in at least one of its
 * sources, or it carried the story and named the actor in none of them. That second
 * state is the one the project exists to show, so it earns a mark rather than a
 * footnote.
 *
 * A polity absent from the story is not plotted at all. Marking it silent would claim
 * it should have carried the story, and no declared panel exists to support that.
 *
 * `plotted` counts the polities with a mark to give, including any this map has no
 * coordinate for — so the caption can say "9 of 11" rather than quietly showing 9.
 */
export function panel(
  story: Story,
  coordinates: Record<string, [number, number]>,
  projection: Coastline,
): { markers: Marker[]; plotted: number } {
  const actor = story.band[0];
  const named = new Map<string, boolean>();
  for (const row of story.evidence) {
    if (!row.polity) continue;
    const hit = row.marks[actor] === PRESENT;
    named.set(row.polity, (named.get(row.polity) ?? false) || hit);
  }

  const markers: Marker[] = [];
  for (const polity of [...named.keys()].sort()) {
    const at = coordinates[polity];
    if (!at) continue;
    const [col, row] = cell(at[0], at[1], projection);
    markers.push({
      n: `${polity} · ${named.get(polity) ? "named" : "did not name"}`,
      c: Math.round(col * 100) / 100,
      r: Math.round(row * 100) / 100,
      on: named.get(polity) as boolean,
    });
  }
  return { markers, plotted: named.size };
}
