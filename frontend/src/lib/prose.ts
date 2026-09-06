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

/**
 * Which languages a story is being told in, most-carried first.
 *
 * This is not what the language tag beside a headline says. That one labels the single
 * headline the page chose to print, and only when it is not English, so a story carried
 * by 72 Russian and 53 Ukrainian outlets showed no tag at all because the representative
 * headline happened to be English. Which languages a story is told in is a different
 * fact, it was not on the page anywhere, and on a site about who tells things
 * differently it is worth more than the tag.
 *
 * Counted over distinct publishers rather than raw rows: the engine has already
 * collapsed syndication in `evidence`, so each row is one voice.
 */
export function storyLanguages(
  story: Story,
  limit = 4,
): { shown: { name: string; sources: number }[]; more: number } {
  const counts = new Map<string, number>();
  for (const row of story.evidence) {
    if (!row.language) continue;
    counts.set(row.language, (counts.get(row.language) ?? 0) + 1);
  }
  const ordered = [...counts]
    .map(([name, sources]) => ({ name: titleCase(name), sources }))
    .sort((a, b) => b.sources - a.sources || a.name.localeCompare(b.name));
  return { shown: ordered.slice(0, limit), more: Math.max(0, ordered.length - limit) };
}

/** GDELT names languages in capitals, and sometimes not. "SPANISH" -> "Spanish". */
function titleCase(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
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
} {
  const figure = lead(story);
  return {
    collapsed:
      `Every publisher in the story, one row each, after collapsing ` +
      `${story.collapsed} reprint(s) that shared a headline word for word.`,
    // The long form only where it applies. With five stories on a page, a sentence
    // that does not depend on the story is printed five times, and the warning that
    // matters gets read as boilerplate along with it.
    unresolved: figure.unresolved
      ? `${figure.unresolved} row(s) are –, not evaluable: no alias exists in that ` +
        `script, and that must never be read as an omission. Omission is the signal.`
      : `No unevaluable rows here.`,
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
  // The lede has to follow the ranking, or it states something the order contradicts.
  // The page no longer leads with the widest split; it leads with the widest split the
  // country test could speak to, and on most runs that is not the same story. Saying
  // "sharpest disagreement" above a story ranked below a wider one would be false in
  // the plainest way a page can be false.
  const split = hero.structure && hero.structure.p <= 0.05;
  return {
    kind: "figure",
    lede: split
      ? "Widest split that follows a country line"
      : "Widest split in this window",
    named: figure.named,
    evaluable: figure.evaluable,
    unit: `sources named ${actor}`,
    // About the window, not about the story. This used to read "N publishers in M
    // polities carried this story, X named the actor and Y did not" - which is, word
    // for word, what the first row below says about the same story, four hundred
    // pixels further down. The hero's job is to place that story among the others.
    say:
      `${report.published.with_a_band} of ` +
      `${thousands(report.published.stories)} stories in this window had enough ` +
      `evaluable sources, in enough countries, to carry a figure at all. ` +
      (split
        ? `This is the most divided of those whose split follows where their sources ` +
          `publish.`
        : `None of them could be shown to split along a country line, so this is ` +
          `simply the most divided.`),
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
  const shown = span?.shown ?? 0;
  // The same claim in both branches, because both branches describe the same order.
  // This one used to say "the N most divided stories", which the ranking stopped being
  // true of: a story shown to split along a country line now outranks a wider one that
  // no test could speak to.
  const rule = shown
    ? `The ${shown} whose split was shown to follow a country line come first, then ` +
      `those the test could not speak to; each group is ordered by how divided it is.`
    : `None could be shown to split along a country line, so they are ordered by how ` +
      `divided they are.`;
  if (!span?.runs_in_span) {
    return (
      `${featured} stories from this window, written up. ${rule} The rest cleared ` +
      `the floors and are listed below them.`
    );
  }
  // What the ordering actually is, said once, because it is not the obvious one and a
  // reader who assumes "most divided first" will find the third row wider than the
  // second and conclude the page is broken.
  let text =
    `${featured} stories of the last ${span.span_hours} hours, over ` +
    `${span.candidates} candidates across ${span.runs_in_span} runs. ${rule} ` +
    `An even split is the widest a story can be, so a story can be very divided and ` +
    `divided by nothing in particular.`;
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
    `${thousands(dropped)} of those articles never reached a story at all, ` +
    `${Math.round((100 * dropped) / total)}%, because they joined no theme, or ` +
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

/** The run's instant as an ISO 8601 string, for `<time datetime>` and for scripting. */
export function runIso(run: Run): string {
  return parseStamp(run.run).toISOString();
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
 * The method, and only the method.
 *
 * This paragraph used to restate the run: articles, domains, hours, themes, stories,
 * how many cleared the floors, the placement rate. Every one of those numbers is now in
 * "What it took to look", labelled, where a reader can actually find them - so saying
 * them again here was the third telling of the same figures on one page.
 *
 * What survives is what no card says: how a story keeps its identity, what was done to
 * syndication before anything was counted, what was thrown away at the grouping stage,
 * and how the map is drawn. Those are claims about the procedure rather than about this
 * window, which is why they belong at the bottom and why they do not change run to run.
 */
export function footer(report: Report): string {
  const dropped = report.grouping.unsplit_themes;
  return (
    `Sources are counted once each: reprints that shared a headline word for word were ` +
    `collapsed before anything was measured, so a wire story carried by six outlets is ` +
    `one voice rather than six. ` +
    (dropped
      ? `${dropped} themes were dropped whole for being near-duplicates at every ` +
        `resolution. `
      : "") +
    `Stories keep their identity between runs by sharing article URLs, so a story that ` +
    `grows stays the same story. Every publisher links to the article at the address ` +
    `GDELT recorded, and this page does not check that the address still answers. ` +
    `Coastlines are Natural Earth 110m, rendered in braille at two dots per column and ` +
    `four per row.`
  );
}

/**
 * Who the window is about: the actors, ranked by how many sources named them.
 *
 * A leaderboard of the most-used *words* was tried first and does not work on this
 * corpus, which is why this counts actors instead. Measured on a real capture, the
 * fifteen commonest words are `de, in, to, la, en, the, of, for, el, and, un, on, 2026,
 * after, di` - articles and prepositions in five languages. Ranking instead by how
 * unusual a word is now against a baseline surfaces `mendl, hodu, erni, backblocks,
 * q2fy27, izdajice`: proper nouns from one source and content-farm noise. Counting
 * distinct outlets rather than articles improves it - `tankers` at 237 outlets,
 * `warships` at 133 - but still admits `clad`, `marred` and `sitters`, which are
 * journalistic register rather than news.
 *
 * Actors avoid all of that because they are *resolved*, not matched on the surface: the
 * engine reads them through an alias table whose Wikidata ids were checked by hand, so
 * `Иран`, `إيران` and `Iran` are one row. The list is short - fourteen actors were
 * measurable in the run this was built against - and that is a real property of the
 * vocabulary rather than a display choice, so the section says how many there were.
 *
 * `evaluable` is summed across stories, so a source that covered three stories is
 * counted three times. That is the right denominator for "how much of the window's
 * coverage named this actor" and the wrong one for "how many outlets named it"; the
 * label says the first.
 */
export function actorBoard(
  run: Run,
  labels: Record<string, string>,
  /**
   * Ten, not fifteen. The card is a leaderboard rather than a census: past the tenth
   * row the shares are small and near-identical, so the extra five added length
   * without adding a reading. The count of actors the run could measure at all is
   * still printed under the table, so a shorter list is still a stated fact rather
   * than a silent truncation.
   */
  limit = 10,
): {
  actor: string;
  named: number;
  evaluable: number;
  stories: number;
  peak: number;
}[] {
  const totals = new Map<
    string,
    { named: number; evaluable: number; stories: number; peak: number }
  >();
  for (const story of run.stories) {
    for (const figure of story.figures) {
      // An unmeasurable figure has no denominator worth adding: below the floors the
      // engine publishes the counts but not the rate, and summing them here would
      // rebuild the aggregate it declined to compute.
      if (figure.measurable === false) continue;
      const row = totals.get(figure.actor) ?? {
        named: 0,
        evaluable: 0,
        stories: 0,
        peak: 0,
      };
      row.named += figure.named;
      row.evaluable += figure.evaluable;
      row.stories += 1;
      row.peak = Math.max(row.peak, figure.division ?? 0);
      totals.set(figure.actor, row);
    }
  }
  return [...totals]
    .map(([actor, row]) => ({ actor: actorName(actor, labels), ...row }))
    .sort((a, b) => b.named - a.named || a.actor.localeCompare(b.actor))
    .slice(0, limit);
}
