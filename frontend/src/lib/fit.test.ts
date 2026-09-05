/**
 * What the page gives up when it cannot carry everything, and in what order.
 *
 * These are the rules, not the arithmetic. The budget is calibrated against measured
 * builds and will move; what must not move is that figures are never dropped, that the
 * hero keeps its evidence longest, that the narrowest go first, and that a page which
 * dropped something says so.
 */

import { describe, expect, it } from "vitest";
import { capNote, evidenceCost, fitEvidence } from "./fit";
import type { Story } from "./stories";

/** A story whose evidence is `rows` rows of incompressible-ish text. */
function story(id: string, sources: number, rows: number): Story {
  return {
    id,
    headline: `headline ${id}`,
    headline_language: null,
    band: ["actor"],
    sources,
    collapsed: 0,
    polities: ["Spain"],
    figures: [
      {
        actor: "actor",
        named: 1,
        evaluable: sources,
        unresolved: 0,
        division: 0.5,
        balanced_rate: null,
      },
    ],
    evidence: Array.from({ length: rows }, (_, i) => ({
      domain: `d${id}${i}.example`,
      polity: "Spain",
      title: `a headline about ${id} number ${i} with enough words to weigh something`,
      marks: { actor: "present" as const },
    })),
  };
}

describe("fitting the evidence to the budget", () => {
  it("keeps everything when the page fits", () => {
    const rows = [story("hero", 100, 5), story("b", 50, 5), story("c", 10, 5)];
    const fitted = fitEvidence(rows, 1024 * 1024);
    expect(fitted.dropped).toBe(0);
    expect(fitted.kept.size).toBe(3);
  });

  it("gives up the narrowest row first, not the first it encounters", () => {
    const rows = [
      story("hero", 100, 40),
      story("wide", 300, 40),
      story("narrow", 5, 40),
      story("middling", 60, 40),
    ];
    // Room for three of the four.
    const budget = Math.floor(rows.reduce((n, s) => n + evidenceCost(s), 0) * 0.8);
    const fitted = fitEvidence(rows, budget);
    expect(fitted.dropped).toBe(1);
    expect(fitted.kept.has("narrow")).toBe(false);
    expect(fitted.kept.has("wide")).toBe(true);
  });

  it("gives up the hero's evidence last, however narrow the hero is", () => {
    // The hero here is narrower than everything else, so a naive "narrowest first"
    // would drop the page's lead story — leaving it making the boldest claim with the
    // least behind it.
    const rows = [
      story("hero", 3, 40),
      story("b", 200, 40),
      story("c", 150, 40),
    ];
    const fitted = fitEvidence(rows, 1);
    expect(fitted.dropped).toBe(3);
    // Everything goes at a budget of one byte, but check the order it went in by
    // giving it room for exactly one table.
    const one = fitEvidence(rows, evidenceCost(rows[0]));
    expect(one.kept.has("hero")).toBe(true);
    expect(one.kept.size).toBe(1);
  });

  it("never claims completeness it does not have", () => {
    expect(capNote(0)).toBeNull();
    const note = capNote(3);
    expect(note).toContain("3 narrowest");
    expect(note).toContain("data/stories.json");
    // It has to say where the rows are, because "some evidence omitted" is not
    // something a reader can act on.
    expect(note).toContain("the same rows the figures above were computed from");
  });
});
