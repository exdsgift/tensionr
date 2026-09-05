/**
 * The shape of `data/stories.json`, and how the page gets hold of it.
 *
 * This is the contract between the engine and this site, and it goes one way: the
 * engine emits facts and numbers, and everything that reads like a sentence is
 * composed here. Nothing in this directory may ask the engine for a phrase.
 *
 * Only the fields the page actually reads are typed. The payload carries more — the
 * engine's own bookkeeping — and typing fields nobody uses would turn every change to
 * the engine's internals into a change here.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

/** How a source treated one actor. The engine's vocabulary, not the page's. */
export const PRESENT = "present";
export const ABSENT = "absent";
export const UNRESOLVED = "unresolved";

export type Mark = typeof PRESENT | typeof ABSENT | typeof UNRESOLVED;

export interface EvidenceRow {
  /** Absent for anything captured before the URL was recorded. Not an error. */
  url?: string;
  domain: string;
  /** null when the domain could not be placed in a polity. */
  polity: string | null;
  language?: string;
  title: string;
  marks: Record<string, Mark>;
}

export interface Figure {
  actor: string;
  named: number;
  evaluable: number;
  unresolved: number;
  division: number;
  /** null when the run could not weight languages equally. */
  balanced_rate: number | null;
  measurable?: boolean;
}

export interface Story {
  id: string;
  headline: string;
  /** GDELT's own language name, e.g. "SPANISH". Absent means English. */
  headline_language: string | null;
  /** The leading actors, within 0.005 of one another. Unordered; band[0] is alphabetical. */
  band: string[];
  sources: number;
  /** Reprints that shared a headline word for word, collapsed before counting. */
  collapsed: number;
  polities: string[];
  figures: Figure[];
  evidence: EvidenceRow[];
  /** Set by the engine when it can see a day of history. */
  featured?: boolean;
  span_division?: number;
  /**
   * This story's division over the runs that carried it, oldest first, on featured
   * stories only. A run that did not carry the story contributes no point rather than
   * a zero, so the axis is runs-that-carried-it and not time.
   */
  series?: { run: string; division: number; sources: number | null }[];
  /**
   * Whether the naming split aligns with the country of publication. Absent when the
   * question cannot be asked: one country, or unanimity among the rows that carry a
   * country. Both are outcomes rather than failures.
   */
  structure?: {
    sources: number;
    polities: number;
    p: number;
    floor: number;
    powered: boolean;
    by_polity: { polity: string; named: number; evaluable: number; thin: boolean }[];
  };
}

export interface Report {
  window: { slots: number; articles: number; missing?: number };
  grouping: {
    themes: number;
    stories: number;
    articles_in_stories?: number;
    unsplit_themes?: number;
  };
  polities: { domains: number; rate: number };
  floors?: { evaluable: number; polities: number };
  previous_run: string | null;
  published: { stories: number; with_a_band: number };
  selection?: {
    span_hours: number;
    runs_in_span: number;
    candidates: number;
    gone_from_the_window: number;
    widest_gone: number;
  };
}

export interface Run {
  /** Compact UTC stamp, e.g. "20260905T044830Z". */
  run: string;
  stories: Story[];
  report: Report;
}

export interface Coastline {
  width: number;
  height: number;
  lat_top: number;
  lat_bottom: number;
  lon_left: number;
  lon_right: number;
  /** One string per row, packed into braille (U+28xx). */
  rows: string[];
}

/** How many stories are written up. The rest are counted, not shown. */
export const FEATURED = 5;

/**
 * `data/` sits at the repository root, beside `frontend/` rather than inside it,
 * because it is the contract between the engine and this site and is published as-is.
 * Resolved from the working directory because that is where `next build` runs.
 */
const DATA = path.join(process.cwd(), "..", "data");

function readJson<T>(...parts: string[]): T {
  return JSON.parse(readFileSync(path.join(DATA, ...parts), "utf-8")) as T;
}

export function loadRun(): Run {
  try {
    return readJson<Run>("stories.json");
  } catch (cause) {
    // The engine's output lives on the `data` branch, not in this one, so this is the
    // first thing that breaks when the overlay did not happen. Left as an ENOENT it
    // surfaces as a Next export stack trace with a temp path in it, which says nothing
    // about what to do.
    throw new Error(
      `data/stories.json is missing, so there is no run to render.\n` +
        `It is produced by the engine and published to the \`data\` branch; ` +
        `assemble-site.sh overlays it onto each tree before building.\n` +
        `Locally: git fetch origin data && git show origin/data:data/stories.json > data/stories.json`,
      { cause },
    );
  }
}

export function loadCoastlines(): { wide: Coastline; narrow: Coastline } {
  return {
    wide: readJson<Coastline>("map", "coastline.json"),
    narrow: readJson<Coastline>("map", "coastline-narrow.json"),
  };
}

export function loadCoordinates(): Record<string, [number, number]> {
  return readJson<{ polities: Record<string, [number, number]> }>(
    "polities",
    "coordinates.json",
  ).polities;
}

/**
 * Display names for actor keys.
 *
 * The key is a slug the pipeline matches on; the label is what a reader should see, and
 * the two are not interchangeable — `hormuz` is the Strait of Hormuz and `trump` is
 * Donald Trump. Title-casing the key would print neither. The seeds are the same file
 * the alias table was built from, so the name on the page is the name whose Wikidata id
 * was checked by hand.
 */
export function loadLabels(): Record<string, string> {
  try {
    const seeds = readJson<{
      actors: Record<string, { label?: string }>;
    }>("actors", "seeds.json");
    return Object.fromEntries(
      Object.entries(seeds.actors)
        .filter(([, v]) => v.label)
        .map(([k, v]) => [k, v.label as string]),
    );
  } catch {
    // A missing seed file is a page with cruder names, not a broken build.
    return {};
  }
}

export function actorName(
  actor: string,
  labels: Record<string, string>,
): string {
  return (
    labels[actor] ??
    actor
      .split("-")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ")
  );
}

/** The band's first figure. The band is unordered, so "first" is alphabetical. */
export function lead(story: Story): Figure {
  const found = story.figures.find((f) => f.actor === story.band[0]);
  if (!found) {
    throw new Error(`story ${story.id}: band names ${story.band[0]}, figures do not`);
  }
  return found;
}

/**
 * The stories that can be written up, in the order the page shows them.
 *
 * A story needs both a band and evidence: a band with no rows behind it is a figure
 * with nothing to check it against.
 *
 * The engine chooses which stories are featured when it can see a day of history,
 * ranking by the widest division each reached over that span rather than by this
 * window's snapshot. Without that history the page ranks what it has, which is what it
 * did before and is still correct for a single window.
 */
export function banded(run: Run): Story[] {
  const rows = run.stories.filter((s) => s.band?.length && s.evidence?.length);
  if (rows.some((s) => s.featured)) {
    return rows.sort(
      (a, b) =>
        Number(!a.featured) - Number(!b.featured) ||
        (b.span_division ?? 0) - (a.span_division ?? 0),
    );
  }
  return rows.sort((a, b) => lead(b).division - lead(a).division);
}
