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

import { ABSENT, PRESENT, type Coastline, type Story } from "./stories";

export interface Marker {
  /** Label, already phrased: "Germany · 28 of 34 named Ukraine". */
  n: string;
  /** Fractional character cell, column then row. */
  c: number;
  r: number;
  /**
   * How the country is drawn:
   *   "most"  most of its sources named the actor
   *   "few"   most did not
   *   "thin"  one or two sources, which cannot carry a rate at all
   *
   * Three states rather than two because the old boolean lied. A polity counted as
   * "named" if *any* one of its sources named the actor, so a country where 1 of 20
   * named looked identical to one where 20 of 20 did, and 46 of 62 marks on the live
   * map were solid on that basis.
   */
  state: "most" | "few" | "thin";
  named: number;
  evaluable: number;
}

/** Below this a rate is not a rate. Matches the engine's `thin` flag and the country table. */
const MIN_SOURCES = 3;

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
 * Map marks for the countries that carried the story, drawn by how they split.
 *
 * This is the country table rendered geographically. A country is solid when most of
 * its sources named the actor, hollow when most did not, and a hairline when it has
 * one or two sources and therefore no rate worth drawing.
 *
 * A country absent from the story is not plotted at all. Marking it silent would claim
 * it should have carried the story, and no declared panel exists to support that.
 *
 * `carried` counts the countries with something to say, including any this map has no
 * coordinate for, so the caption can be honest about what is missing rather than
 * dividing a number by itself.
 */
export function panel(
  story: Story,
  coordinates: Record<string, [number, number]>,
  projection: Coastline,
  actorLabel: string,
): { markers: Marker[]; plotted: number; carried: number } {
  const actor = story.band[0];
  const counts = new Map<string, { named: number; evaluable: number }>();
  for (const row of story.evidence) {
    if (!row.polity) continue;
    const mark = row.marks[actor];
    // An unresolved mark carries no evidence either way, so it enters neither side.
    if (mark !== PRESENT && mark !== ABSENT) continue;
    const seen = counts.get(row.polity) ?? { named: 0, evaluable: 0 };
    seen.evaluable += 1;
    if (mark === PRESENT) seen.named += 1;
    counts.set(row.polity, seen);
  }

  const markers: Marker[] = [];
  for (const polity of [...counts.keys()].sort()) {
    const at = coordinates[polity];
    if (!at) continue;
    const { named, evaluable } = counts.get(polity) as {
      named: number;
      evaluable: number;
    };
    const state: Marker["state"] =
      evaluable < MIN_SOURCES ? "thin" : named / evaluable > 0.5 ? "most" : "few";
    const [col, row] = cell(at[0], at[1], projection);
    markers.push({
      n: `${polity} · ${named} of ${evaluable} named ${actorLabel}`,
      c: Math.round(col * 100) / 100,
      r: Math.round(row * 100) / 100,
      state,
      named,
      evaluable,
    });
  }
  return { markers, plotted: markers.length, carried: counts.size };
}
