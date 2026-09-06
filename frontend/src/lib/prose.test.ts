/**
 * The edge cases, carried over from `tests/test_ledger.py` when the page was
 * translated from Python.
 *
 * These are not tests of markup. They are what the deleted suite actually defended:
 * that a window where nothing cleared the floors reads as an outcome rather than a
 * broken build, that an unresolved mark is never confused with an omission, that an
 * unplaced polity is stated rather than blank, and that a band of more than one actor
 * says its order is not a claim.
 *
 * Assertions on tag counts and CSS classes were not carried over. They described markup
 * that no longer exists, and re-creating them would pin this page's structure to the
 * shape of the one it replaced.
 */

import { describe, expect, it } from "vitest";
import {
  bandNote,
  evidenceNote,
  footer,
  foreignLanguage,
  hook,
  neverReached,
  parseStamp,
  percent,
  readingSentence,
  runIso,
  runStamp,
  selectionNote,
  series,
  sincePrevious,
  spellings,
  splitSentence,
  thousands,
} from "./prose";
import type { Report, Run, Story } from "./stories";

const REPORT: Report = {
  window: { slots: 48, articles: 143152 },
  grouping: {
    themes: 1258,
    stories: 1267,
    articles_in_stories: 17928,
    unsplit_themes: 361,
  },
  polities: { domains: 10839, rate: 0.3592 },
  floors: { evaluable: 30, polities: 2 },
  previous_run: "20260904T223145Z",
  published: { stories: 1267, with_a_band: 17 },
  selection: {
    span_hours: 24,
    runs_in_span: 4,
    candidates: 71,
    gone_from_the_window: 54,
    widest_gone: 0.9991,
  },
};

function story(over: Partial<Story> = {}): Story {
  return {
    id: "s-1",
    headline: "A headline",
    headline_language: null,
    band: ["hormuz"],
    sources: 12,
    collapsed: 3,
    polities: ["Spain", "Peru"],
    figures: [
      {
        actor: "hormuz",
        named: 7,
        evaluable: 12,
        unresolved: 0,
        division: 0.918,
        balanced_rate: 0.61,
      },
    ],
    evidence: [],
    ...over,
  };
}

describe("the hero", () => {
  // It used to restate the first row: same publishers, same polities, same split, four
  // hundred pixels apart. Its job is to place that story among the others.
  it("says where the story stands, not what the row below already says", () => {
    const h = hook(story(), REPORT, {});
    if (h.kind !== "figure") throw new Error("unreachable");
    expect(h.say).toContain("17 of 1,267 stories");
    expect(h.say).not.toContain("publishers");
  });

  /**
   * The lede has to follow the ranking or it contradicts the order under it.
   *
   * The page no longer leads with the widest split; it leads with the widest split the
   * country test could speak to, and on most runs those are different stories. Measured
   * across 25 published runs, ranking on division alone put 10 refuted stories on the
   * page and left 39 shown ones off it. Saying "sharpest disagreement" above a story
   * that is not the sharpest would be false in the plainest way a page can be false.
   */
  const structured = {
    sources: 60,
    polities: 8,
    p: 0.002,
    floor: 0.0005,
    powered: true,
    by_polity: [],
  };

  it("claims a country line only when the test showed one", () => {
    const h = hook(story({ structure: structured }), REPORT, {});
    if (h.kind !== "figure") throw new Error("unreachable");
    expect(h.lede).toBe("Widest split that follows a country line");
    expect(h.say).toContain("follows where their sources publish");
  });

  it("says plainly when nothing could be shown", () => {
    const h = hook(story(), REPORT, {});
    if (h.kind !== "figure") throw new Error("unreachable");
    expect(h.lede).toBe("Widest split in this window");
    expect(h.say).toContain("could be shown to split along a country line");
  });

  it("treats a test that ran and found nothing as not shown", () => {
    // p above the threshold is not a country line, however well powered the test was.
    const h = hook(
      story({ structure: { ...structured, p: 0.42 } }),
      REPORT,
      {},
    );
    if (h.kind !== "figure") throw new Error("unreachable");
    expect(h.lede).toBe("Widest split in this window");
  });
});

describe("an empty window", () => {
  it("reads as an outcome, not as a failure, and names the run's own floors", () => {
    const h = hook(null, REPORT, {});
    expect(h.kind).toBe("empty");
    if (h.kind !== "empty") throw new Error("unreachable");
    expect(h.lede).toBe("Nothing cleared the floors in this window");
    // The floors come from the report, so the page states what the run applied
    // rather than a copy of its own.
    expect(h.say).toContain("30 evaluable sources across 2 polities");
    expect(h.say).toContain("a number about the sample, not about the world");
  });

  it("falls back to naming the floors abstractly when the run did not record them", () => {
    const h = hook(null, { ...REPORT, floors: undefined }, {});
    if (h.kind !== "empty") throw new Error("unreachable");
    expect(h.say).toContain("this project's floors");
    // It must not invent numbers it was not given.
    expect(h.say).not.toMatch(/\d+ evaluable sources across/);
  });
});

describe("an unresolved mark", () => {
  it("is never described as an omission", () => {
    const note = evidenceNote(
      story({
        figures: [
          {
            actor: "hormuz",
            named: 7,
            evaluable: 12,
            unresolved: 4,
            division: 0.9,
            balanced_rate: null,
          },
        ],
      }),
    );
    expect(note.unresolved).toContain("4 row(s) are –");
    expect(note.unresolved).toContain("not evaluable");
    expect(note.unresolved.toLowerCase()).toContain("omission is the signal");
  });

  it("says so briefly when there is none", () => {
    // The long warning is printed only where it applies. On a page of five stories a
    // sentence that does not depend on the story appears five times, and the warning
    // that matters gets read as boilerplate alongside it.
    expect(evidenceNote(story()).unresolved).toBe("No unevaluable rows here.");
  });
});

describe("the split sentence", () => {
  const rows = (marks: [string | null, string][]) =>
    marks.map(([polity, mark], i) => ({
      domain: `d${i}.example`,
      polity,
      title: "t",
      marks: { hormuz: mark as never },
    }));

  it("is withheld unless there is both a unanimous for and a unanimous against", () => {
    // Everyone named it: true, but not a split, and saying it would imply one.
    expect(
      splitSentence(
        story({
          evidence: rows([
            ["Spain", "present"],
            ["Peru", "present"],
          ]),
        }),
        {},
      ),
    ).toBeNull();
  });

  it("names both sides when there is one", () => {
    const s = splitSentence(
      story({
        evidence: rows([
          ["Spain", "present"],
          ["Peru", "absent"],
        ]),
      }),
      {},
    );
    expect(s).toBe("Every source in Spain named Hormuz; none of those in Peru did.");
  });

  it("ignores unresolved rows rather than counting them as silence", () => {
    // Peru's only row cannot be evaluated, so Peru is not a polity that stayed
    // silent — it is a polity nothing can be said about.
    expect(
      splitSentence(
        story({
          evidence: rows([
            ["Spain", "present"],
            ["Peru", "unresolved"],
          ]),
        }),
        {},
      ),
    ).toBeNull();
  });

  it("ignores rows with no polity", () => {
    expect(
      splitSentence(
        story({
          evidence: rows([
            ["Spain", "present"],
            [null, "absent"],
          ]),
        }),
        {},
      ),
    ).toBeNull();
  });
});

describe("a band of more than one actor", () => {
  it("says the order inside it is not a claim", () => {
    const note = bandNote(story({ band: ["hormuz", "iran"] }));
    expect(note).toContain("2 actors lead together");
    expect(note).toContain("the band is the claim and the order inside it is not");
  });

  it("says nothing when one actor leads alone", () => {
    expect(bandNote(story())).toBeNull();
  });
});

describe("the reading sentence", () => {
  it("carries the balanced rate as its own clause when the run produced one", () => {
    const r = readingSentence(story(), {});
    expect(r.before).toBe(
      "12 publishers across 2 polities carried this. 7 of 12 named Hormuz",
    );
    expect(r.balanced).toContain("61% once every language counts equally");
  });

  it("omits the clause entirely when the run could not weight languages", () => {
    const r = readingSentence(
      story({
        figures: [
          {
            actor: "hormuz",
            named: 7,
            evaluable: 12,
            unresolved: 0,
            division: 0.9,
            balanced_rate: null,
          },
        ],
      }),
      {},
    );
    // Not "0%", and not "unknown" — the clause is a claim, so its absence is the
    // honest form.
    expect(r.balanced).toBeNull();
  });
});

describe("headline language", () => {
  it("labels anything that is not English, including a language we cannot read", () => {
    expect(foreignLanguage(story({ headline_language: "SPANISH" }))).toBe("Spanish");
    expect(foreignLanguage(story({ headline_language: "TAGALOG" }))).toBe("Tagalog");
  });

  it("leaves English and unlabelled headlines alone", () => {
    expect(foreignLanguage(story({ headline_language: "ENGLISH" }))).toBeNull();
    expect(foreignLanguage(story({ headline_language: null }))).toBeNull();
  });
});

describe("the selection note", () => {
  it("says which span it selected over, and what fell out of the window", () => {
    const note = selectionNote(REPORT, 5);
    expect(note).toContain("the last 24 hours");
    expect(note).toContain("71 candidates across 4 runs");
    expect(note).toContain("54 of them are no longer carried");
    expect(note).toContain("division of 0.9991");
  });

  it("claims only this window when there is no history to select over", () => {
    const note = selectionNote({ ...REPORT, selection: undefined }, 5);
    expect(note).toContain("from this window");
    expect(note).not.toContain("hours");
  });

  it("never calls the five the most divided, because they are not ordered that way", () => {
    // The ranking puts a story shown to split along a country line above a wider one
    // no test could speak to, so "the 5 most divided stories" became false. Both
    // branches of this note are checked, because only one of them had said it.
    const withSpan = REPORT.selection && { ...REPORT.selection, shown: 2 };
    for (const selection of [undefined, withSpan]) {
      const note = selectionNote({ ...REPORT, selection }, 5);
      expect(note).not.toMatch(/most divided/);
      expect(note).toContain("country line");
    }
  });
});

describe("what never reached a story", () => {
  it("is published rather than absorbed", () => {
    const text = neverReached(REPORT);
    expect(text).toContain("125,224 of those articles never reached a story");
    expect(text).toContain("87%");
    expect(text).toContain("361 themes were dropped whole");
  });

  it("says nothing rather than guessing when the run did not record it", () => {
    expect(
      neverReached({
        ...REPORT,
        grouping: { ...REPORT.grouping, articles_in_stories: undefined },
      }),
    ).toBe("");
  });
});

describe("cadence", () => {
  const run = (over: Partial<Run["report"]> = {}): Run => ({
    run: "20260905T044830Z",
    stories: [],
    report: { ...REPORT, ...over },
  });

  it("reports the delivered gap, not a promised schedule", () => {
    expect(sincePrevious(run())).toBe("6 h 17 min");
  });

  it("says so on a first run instead of inventing a gap", () => {
    expect(sincePrevious(run({ previous_run: null }))).toBe("first run");
  });

  it("never says 'hourly'", () => {
    // The schedule asks for a cadence GitHub does not deliver; the page must not
    // repeat the cron line as if it were a fact.
    expect(footer(REPORT)).not.toContain("hourly");
    expect(sincePrevious(run())).not.toContain("hourly");
  });

  it("stamps the run in UTC", () => {
    expect(runStamp(run())).toBe("5 Sep · 04:48 UTC");
    expect(parseStamp("20260905T044830Z").toISOString()).toBe(
      "2026-09-05T04:48:30.000Z",
    );
  });
});

describe("the footer", () => {
  // It used to restate the run: articles, domains, hours, themes, stories, floors,
  // placement rate. Every one of those is now in "What it took to look", so repeating
  // them here was the third telling of the same figures on one page. What is left is
  // the method, which does not change from run to run.
  it("states the method, not the window", () => {
    const text = footer(REPORT);
    expect(text).toContain("collapsed before anything was measured");
    expect(text).toContain("Stories keep their identity between runs");
    expect(text).toContain("Natural Earth 110m");
  });

  it("no longer repeats figures the cards already carry", () => {
    const text = footer(REPORT);
    for (const figure of ["143,152", "10,839", "12 hours", "36%", "17 cleared"]) {
      expect(text).not.toContain(figure);
    }
  });

  it("mentions dropped themes only when the run recorded any", () => {
    expect(footer(REPORT)).toContain("361 themes were dropped whole");
    const quiet = {
      ...REPORT,
      grouping: { ...REPORT.grouping, unsplit_themes: 0 },
    };
    expect(footer(quiet)).not.toContain("dropped whole");
  });
});

describe("formatting", () => {
  it("groups thousands and rounds percentages the way the page reads them", () => {
    expect(thousands(143152)).toBe("143,152");
    expect(percent(0.3592)).toBe("36%");
  });

  it("joins a series without an Oxford comma, matching the published page", () => {
    expect(series(["Spain"])).toBe("Spain");
    expect(series(["Spain", "Peru"])).toBe("Spain and Peru");
    expect(series(["Spain", "Peru", "Chile"])).toBe("Spain, Peru and Chile");
  });
});

describe("runIso", () => {
  it("gives the run's instant as a machine-readable stamp", () => {
    expect(runIso({ run: "20260905T171807Z" } as Run)).toBe(
      "2026-09-05T17:18:07.000Z",
    );
  });

  it("agrees with the stamp the bar prints", () => {
    const run = { run: "20260905T044830Z" } as Run;
    // Same instant, two renderings: one for a reader, one for a machine and for the
    // script that turns it into an age in the reader's own clock.
    expect(runStamp(run)).toBe("5 Sep · 04:48 UTC");
    expect(runIso(run)).toBe("2026-09-05T04:48:30.000Z");
  });
});

describe("spellings", () => {
  const base = { domain: "d.test", polity: "Italy", marks: { kyiv: "present" } };
  const row = (language: string, wrote: string | null, polity = "Italy") => ({
    ...base,
    polity,
    language,
    title: "t",
    wrote: { kyiv: wrote },
  });
  const storyWith = (evidence: ReturnType<typeof row>[]) =>
    ({ ...story(), band: ["kyiv"], evidence }) as unknown as Story;

  it("reports spellings that compete within one language", () => {
    const s = storyWith([
      row("ENGLISH", "Kyiv", "United States"),
      row("ENGLISH", "Kyiv", "United Kingdom"),
      row("ENGLISH", "Kiev", "India"),
      row("ENGLISH", "Kiev", "Pakistan"),
    ]);
    const groups = spellings(s);
    expect(groups?.[0].language).toBe("English");
    expect(groups?.[0].forms.map((f) => f.spelling)).toEqual(["Kyiv", "Kiev"]);
    expect(groups?.[0].forms[0].countries).toBe(2);
  });

  it("does not call a translation a choice", () => {
    // One spelling per language is the language, not a decision. The replication of
    // the framing experiment found exactly this confound eating a result whole.
    const s = storyWith([row("ENGLISH", "Kyiv"), row("SPANISH", "Kiev")]);
    expect(spellings(s)).toBeNull();
  });

  it("does not list a spelling one source used", () => {
    // Usually a headline GDELT filed under the wrong language, not a choice.
    const s = storyWith([row("ENGLISH", "Kyiv"), row("ENGLISH", "Kyiv"), row("ENGLISH", "Ucraïna")]);
    expect(spellings(s)).toBeNull();
  });

  it("is silent where the engine has not kept the spelling", () => {
    const s = { ...story(), band: ["kyiv"] } as Story;
    expect(spellings(s)).toBeNull();
  });
});
