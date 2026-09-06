/**
 * Keeping the page inside its content budget, by giving up the least.
 *
 * A page's weight is not a property of this code, it is a property of the run. Measured
 * across two consecutive runs: 499 evidence rows in one and 1,227 in the next, with a
 * single story carrying 600 — the content half went from 57.9 KB to 138.6 KB against a
 * 120 KB budget. A fixed budget with no way to meet it is not a budget, it is a build
 * that fails on a Tuesday.
 *
 * So the page sheds evidence tables until it fits, narrowest row first, and says on the
 * page that it did. This is `ledger.py`'s `_fit()`, and the rules it encodes are the
 * part that matters:
 *
 *   - Figures are never dropped. Every story keeps its headline, its counts and its
 *     reading sentence; what goes is the table behind them, and the row still points at
 *     `data/stories.json`, which carries the same rows the figures were computed from.
 *   - The hero keeps its table for as long as anything does. It is the story the page
 *     leads with, and leading with an unevidenced claim is the one thing this page
 *     exists not to do.
 *   - Narrowest first, by source count. A 43-source table is the cheapest thing to give
 *     up and the least missed; a 600-source table is both the most expensive and the
 *     most interesting.
 *   - Nothing is dropped silently. A page that hides rows without saying so is claiming
 *     a completeness it does not have.
 *
 * The cost of a table is measured by gzipping the text it will actually print — the
 * domains, polities, headlines and marks — rather than by rendering it. Rendering it
 * would be exact, but `react-dom/server` is not importable from a server component under
 * Turbopack, and the markup around the text is near-constant per row anyway, so the
 * proxy tracks the real thing closely. `check-weight.mjs` measures the built page and is
 * the actual gate; this only has to be close enough to keep the page under it.
 */

import { gzipSync } from "node:zlib";

import type { Story } from "./stories";

/**
 * How many bytes of gzipped evidence the page may carry.
 *
 * The content budget is 160 KB (ADR 0002), and the page without any tables is the
 * constant below, so what is left is what the tables may spend.
 */
/**
 * Expressed in the proxy's own units. Recalibrated by building the same run at four
 * budgets and reading `check:weight`'s content figure back:
 *
 *   proxy budget     content
 *    0.0 KB          29.3 KB     the page with no tables at all
 *   33.0 KB          91.1 KB
 *   66.0 KB         166.9 KB
 *   99.0 KB         166.9 KB     saturated: every table already fits
 *
 * The line is not quite straight. The slope is 1.87 over the first half and 2.30 over
 * the second, because the later tables are the wide ones. Solving the upper segment for
 * a 160 KB content budget gives about 63 KB of proxy, and the setting is 56.
 *
 * The gap is not caution, it is granularity: a table is admitted whole, so between 56
 * and 58 KB of proxy the content jumps from 149.4 KB to 162.3 KB. 56 is the largest
 * setting that lands under the budget, and it leaves 10.6 KB of the content budget and
 * 25 KB of the total.
 *
 * The previous calibration read `content ~= 26 KB + 2.03 x proxy` and was solved to
 * 66 KB. It went stale the honest way: the constant is the page without evidence, and
 * the page has since grown a latent map, two run cards, a country table per story and a
 * labelled update stamp. It was CI that noticed, on a run carrying 19 banded stories
 * and 2,369 evidence rows.
 *
 * Recalibrate the same way. Do not adjust this by feel: the whole point is that the
 * page sheds evidence for a measured reason.
 */
export const EVIDENCE_BUDGET_BYTES = 56 * 1024;

export interface Fitted {
  /** Story ids whose evidence table survived, in the page's own order. */
  kept: Set<string>;
  /** How many tables were given up. Zero means the page is complete. */
  dropped: number;
  bytes: number;
}

/**
 * Decide which evidence tables the page can afford.
 *
 * `candidates` arrive in the page's display order; the first is the hero and is given up
 * last. Returns the set to render, never an ordering — the page's order is not this
 * function's business.
 */
export function evidenceCost(story: Story): number {
  const text = story.evidence
    .map(
      (row) =>
        `${row.domain}|${row.polity ?? ""}|${row.title.slice(0, 160)}|` +
        story.band.map((a) => row.marks[a] ?? "").join(""),
    )
    .join("\n");
  return gzipSync(Buffer.from(text), { level: 9 }).length;
}

export function fitEvidence(
  candidates: Story[],
  budget: number = EVIDENCE_BUDGET_BYTES,
): Fitted {
  const cost = new Map<string, number>();
  for (const c of candidates) cost.set(c.id, evidenceCost(c));

  const kept = new Set(candidates.map((c) => c.id));
  const total = () => [...kept].reduce((n, id) => n + (cost.get(id) ?? 0), 0);

  // Give up the narrowest first, and never the hero while anything else remains.
  const order = candidates
    .slice(1)
    .sort((a, b) => a.sources - b.sources)
    .concat(candidates.slice(0, 1));

  let dropped = 0;
  for (const c of order) {
    if (total() <= budget) break;
    kept.delete(c.id);
    dropped++;
  }

  return { kept, dropped, bytes: total() };
}

/**
 * What the page says when it could not carry everything.
 *
 * Names the number and where the rows are, because "some evidence omitted" is not a
 * statement a reader can act on.
 */
export function capNote(dropped: number): string | null {
  if (!dropped) return null;
  return (
    `The sources behind the ${dropped} narrowest of these rows are not on this page, ` +
    `which would otherwise go past its weight budget. They are in data/stories.json, ` +
    `one row per publisher, the same rows the figures above were computed from.`
  );
}
