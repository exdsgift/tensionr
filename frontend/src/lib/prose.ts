/**
 * Every sentence on the page that contains a number the run measured.
 *
 * This was `ledger.py` — the same logic, translated. It lives in the frontend rather
 * than in the engine because it *is* presentation: the engine's job is to measure, and
 * `stories.json` carries facts. Nothing here computes a figure; everything here decides
 * how one is said.
 *
 * The rule that governs the wording, from the project's own terms: no number without a
 * unit, a stated procedure, and a declared uncertainty. Most of the awkwardness in these
 * strings is the third one. When a sentence looks like it could be tightened by dropping
 * a clause, check first whether that clause is the uncertainty.
 *
 * The edge cases are the part that took the work, and they are what `prose.test.ts`
 * pins: an empty window, a single actor, an unresolved actor, an unplaced polity, more
 * than one actor leading.
 */

import {
  actorName,
  lead,
  PRESENT,
  UNRESOLVED,
  type Report,
  type Run,
  type Story,
} from "./stories";

type Labels = Record<string, string>;

/** "a, b and c". Oxford comma deliberately absent, matching the published page. */
export function series(names: string[]): string {
  if (names.length === 1) return names[0];
  return names.slice(0, -1).join(", ") + " and " + names[names.length - 1];
}

/** 1234567 -> "1,234,567". Fixed locale: the page is English wherever it is read. */
export function thousands(n: number): string {
  return n.toLocaleString("en-US");
}

/** 0.3592 -> "36%". */
export function percent(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

/**
 * Whether a headline needs its language named.
 *
 * The engine's rule is `code_for(language) !== "en"`, where an unmapped language yields
 * null and is therefore labelled. That reduces to: label anything that is not English,
 * including a language this project cannot read — which is the honest outcome, since
 * nothing can be concluded about a headline in a language with no aliases fetched.
 */
export function foreignLanguage(story: Story): string | null {
  const language = story.headline_language;
  if (!language || language.trim().toUpperCase() === "ENGLISH") return null;
  // Title case, so "SPANISH" is printed as "Spanish".
  return language.charAt(0).toUpperCase() + language.slice(1).toLowerCase();
}

/**
 * Where the disagreement runs, in polities rather than in adjectives.
 *
 * Stated only as counts and names, because who named an actor is a fact in the table
 * below it and anything more would be an interpretation the run cannot support.
 *
 * Returns null when there is no clean split — either no polity was unanimous for, or
 * none was unanimous against. Saying "every source in A named it" is only worth saying
 * when there is a B where none did.
 */
export function splitSentence(story: Story, labels: Labels): string | null {
  const actor = story.band[0];
  const byPolity = new Map<string, boolean[]>();
  for (const row of story.evidence) {
    if (!row.polity || row.marks[actor] === UNRESOLVED) continue;
    const marks = byPolity.get(row.polity) ?? [];
    marks.push(row.marks[actor] === PRESENT);
    byPolity.set(row.polity, marks);
  }
  const every = [...byPolity]
    .filter(([, m]) => m.every(Boolean))
    .map(([p]) => p)
    .sort();
  const none = [...byPolity]
    .filter(([, m]) => !m.some(Boolean))
    .map(([p]) => p)
    .sort();
  if (!every.length || !none.length) return null;
  return (
    `Every source in ${series(every.slice(0, 4))} named ` +
    `${actorName(actor, labels)}; none of those in ${series(none.slice(0, 4))} did.`
  );
}

/** The per-actor counts shown on a row. `miss` marks a rate a reader should notice. */
export function rowCounts(
  story: Story,
  labels: Labels,
): { actor: string; named: number; evaluable: number; miss: boolean }[] {
  return story.band.map((actor) => {
    const figure = story.figures.find((f) => f.actor === actor);
    if (!figure) throw new Error(`story ${story.id}: no figure for ${actor}`);
    const rate = figure.evaluable ? figure.named / figure.evaluable : 0;
    return {
      actor: actorName(actor, labels),
      named: figure.named,
      evaluable: figure.evaluable,
      miss: rate < 0.4,
    };
  });
}

/**
 * The reading sentence under a story: what carried it, and how divided it was.
 *
 * Returned in parts rather than as one string because the balanced-rate clause is
 * emphasised on the page, and a component should not have to parse prose back apart to
 * find it.
 */
export function readingSentence(
  story: Story,
  labels: Labels,
): { before: string; balanced: string | null; split: string | null } {
  const figure = lead(story);
  const before =
    `${story.sources} publishers across ${story.polities.length} polities carried ` +
    `this. ${figure.named} of ${figure.evaluable} named ` +
    `${actorName(story.band[0], labels)}`;
  const balanced =
    figure.balanced_rate === null
      ? null
      : `which is ${percent(figure.balanced_rate)} once every language counts equally ` +
        `rather than every source`;
  return { before, balanced, split: splitSentence(story, labels) };
}

/**
 * The note under an evidence table: what the rows are, and what a dash means.
 *
 * The dash clause is the load-bearing one. An unresolved row means no alias exists in
 * that script, and reading it as an omission would invert the page's whole finding —
 * omission is the signal.
 */
export function evidenceNote(story: Story): {
  collapsed: string;
  unresolved: string;
  links: string;
} {
  const figure = lead(story);
  return {
    collapsed:
      `Every publisher in the story, one row each, after collapsing ` +
      `${story.collapsed} reprint(s) that shared a headline word for word.`,
    unresolved: figure.unresolved
      ? `${figure.unresolved} row(s) are –, not evaluable: no alias exists in that ` +
        `script, and that must never be read as an omission — omission is the signal.`
      : `No row is –: an alias exists in every script present.`,
    links:
      `Each publisher links to the article at the address GDELT recorded; the page ` +
      `does not check that the address still answers.`,
  };
}

/**
 * Shown when more than one actor leads. The band is the claim; its order is not.
 */
export function bandNote(story: Story): string | null {
  if (story.band.length === 1) return null;
  return (
    `${story.band.length} actors lead together, within 0.005 of one another. A single ` +
    `top row was measured never to be stable, so the band is the claim and the order ` +
    `inside it is not.`
  );
}

/**
 * The hero. A figure when there is one, a statement when there is not.
 *
 * A window where nothing clears both floors is a real outcome, not a broken build, and
 * the page has to be able to say so. The index declares itself non-computable below a
 * floor rather than printing a number it cannot support; this is that rule applied to
 * the page's own headline.
 */
export type Hook =
  | {
      kind: "figure";
      lede: string;
      named: number;
      evaluable: number;
      unit: string;
      say: string;
    }
  | { kind: "empty"; lede: string; say: string; stories: number };

export function hook(
  hero: Story | null,
  report: Report,
  labels: Labels,
): Hook {
  if (!hero) {
    // Named from the report, so the page states the floors the run actually applied
    // rather than a copy of its own. A run written before the report carried them says
    // so instead of inventing numbers.
    const floors = report.floors;
    const threshold = floors
      ? `${floors.evaluable} evaluable sources across ${floors.polities} polities`
      : `this project's floors on evaluable sources and polities`;
    return {
      kind: "empty",
      lede: "Nothing cleared the floors in this window",
      say:
        `${report.grouping.stories} stories were grouped from ` +
        `${thousands(report.window.articles)} articles, and none reached ${threshold} ` +
        `with a measurable division. That is published rather than hidden: a figure ` +
        `below the floor would be a number about the sample, not about the world.`,
      stories: report.published.stories,
    };
  }
  const figure = lead(hero);
  const actor = actorName(hero.band[0], labels);
  return {
    kind: "figure",
    lede: "Sharpest disagreement in this window",
    named: figure.named,
    evaluable: figure.evaluable,
    unit: `sources named ${actor}`,
    say:
      `${hero.sources} publishers in ${hero.polities.length} polities carried this ` +
      `story. ${figure.named} named ${actor} and ${figure.evaluable - figure.named} ` +
      `did not — the widest split this run measured.`,
  };
}

/** The map's caption. It names the states actually drawn, and nothing else. */
export function legend(
  hero: Story | null,
  plotted: number,
  labels: Labels,
): { named: string; silent: string; plotted: string } | null {
  if (!hero) return null;
  return {
    named: `named ${actorName(hero.band[0], labels)}`,
    silent: "carried it, did not",
    plotted: `${plotted} of ${hero.polities.length} plotted`,
  };
}

/**
 * What span the page selected over, and what the span could not reach.
 *
 * "Of the day" and "of this window" are different claims, and the page has to say
 * which. The count of stories that were divided during the day but are no longer in the
 * window is published rather than absorbed: it is the number that decides whether
 * rebuilding an absent story's evidence is worth building.
 */
export function selectionNote(report: Report, featured: number): string {
  const span = report.selection;
  if (!span?.runs_in_span) {
    return (
      `The ${featured} most divided stories in this window, written up. The rest ` +
      `cleared the floors and are listed below them.`
    );
  }
  let text =
    `The ${featured} most divided stories of the last ${span.span_hours} hours, ` +
    `ranked by the widest division each reached over that span rather than by this ` +
    `window alone — ${span.candidates} candidates across ${span.runs_in_span} runs.`;
  if (span.gone_from_the_window) {
    text +=
      ` ${span.gone_from_the_window} of them are no longer carried by the current ` +
      `window and were not eligible`;
    text += span.widest_gone
      ? `, the widest at a division of ${span.widest_gone}.`
      : `.`;
  }
  return text;
}

/**
 * What the grouping threw away, published rather than absorbed.
 *
 * Most of a window never reaches a measurable story: an article has to join a theme,
 * the theme has to yield a story, and the story has to clear two floors. Stating only
 * the survivors would make the corpus look like the sample.
 */
export function neverReached(report: Report): string {
  const kept = report.grouping.articles_in_stories;
  const total = report.window.articles;
  if (!kept || !total) return "";
  const dropped = total - kept;
  let text =
    `${thousands(dropped)} of those articles never reached a story at all — ` +
    `${Math.round((100 * dropped) / total)}% — because they joined no theme, or ` +
    `joined one too uniform to separate.`;
  if (report.grouping.unsplit_themes) {
    text +=
      ` ${report.grouping.unsplit_themes} themes were dropped whole for being ` +
      `near-duplicates at every resolution.`;
  }
  return text;
}

/**
 * How long since the run before this one, measured rather than promised.
 *
 * The reader is told the *delivered* rate, not the cron line. The schedule asks for a
 * run every few hours and GitHub delivers a fraction of them, with gaps, so a fixed
 * cadence would be a claim the system does not meet. A run knows exactly when the
 * previous one was, so it says that instead.
 */
export function sincePrevious(run: Run): string {
  const previous = run.report.previous_run;
  if (!previous) return "first run";
  const minutes = Math.round(
    (parseStamp(run.run).getTime() - parseStamp(previous).getTime()) / 60000,
  );
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${String(rest).padStart(2, "0")} min` : `${hours} h`;
}

/** "20260905T044830Z" -> Date. The engine's own stamp format, not ISO. */
export function parseStamp(stamp: string): Date {
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(stamp);
  if (!m) throw new Error(`not a run stamp: ${stamp}`);
  const [, y, mo, d, h, mi, s] = m;
  return new Date(
    Date.UTC(+y, +mo - 1, +d, +h, +mi, +s),
  );
}

/** "5 Sep · 04:48 UTC" — the run this page describes. */
export function runStamp(run: Run): string {
  const t = parseStamp(run.run);
  const month = t.toLocaleString("en-US", { month: "short", timeZone: "UTC" });
  const hh = String(t.getUTCHours()).padStart(2, "0");
  const mm = String(t.getUTCMinutes()).padStart(2, "0");
  return `${t.getUTCDate()} ${month} · ${hh}:${mm} UTC`;
}

/**
 * The footer: the window, the grouping, and what could not be placed.
 *
 * One paragraph, and it is the page's methods section. It states the corpus before the
 * sample, so the five stories above are read as a selection rather than as the world.
 */
export function footer(report: Report): string {
  const hours = Math.round((report.window.slots * 15) / 60);
  return (
    `${thousands(report.window.articles)} articles from ` +
    `${thousands(report.polities.domains)} domains over the last ${hours} hours, ` +
    `grouped into ${report.grouping.themes} themes and ${report.grouping.stories} ` +
    `stories, of which ${report.published.with_a_band} cleared both floors. ` +
    `${neverReached(report)} ${percent(report.polities.rate)} of domains could be ` +
    `placed in a polity, and the rest are counted rather than dropped. Stories keep ` +
    `their identity between runs by sharing article URLs, so a story that grows stays ` +
    `the same story. Coastlines are Natural Earth 110m, rendered in braille at two ` +
    `dots per column and four per row.`
  );
}
