/**
 * One actor, across every country that could evaluate it, run by run.
 *
 * The home shows five stories from one window. This is the other axis: pick the actor
 * and see how much of each country's coverage used the name over the last ninety days.
 * It is the question a reader of the leaderboard actually has ("and Italy?") and the
 * question the data could not answer until the engine started keeping counts per
 * country.
 *
 * Static, one page per actor in the vocabulary, generated from the same seeds file the
 * alias table is built from, so an actor the engine measures always has a page and an
 * actor it does not never does. Missing series is an honest empty state, not a build
 * failure: the first deploy after the series lands runs before the engine has.
 */

import Link from "next/link";
import { notFound } from "next/navigation";

import { RateLine, MIN_EVALUABLE_FOR_A_POINT } from "@/components/rate-line";
import { SiteFooter, TopBar } from "@/components/page-parts";
import { ThemeToggle } from "@/components/theme-toggle";
import { footer, runIso, runStamp } from "@/lib/prose";
import {
  actorName,
  loadLabels,
  loadRun,
  loadSeries,
} from "@/lib/stories";
import { slug } from "@/lib/slug";

export function generateStaticParams() {
  return Object.keys(loadLabels()).map((actor) => ({ actor }));
}

export default async function ActorPage({
  params,
}: {
  params: Promise<{ actor: string }>;
}) {
  const { actor } = await params;
  const labels = loadLabels();
  if (!(actor in labels)) notFound();
  const run = loadRun();
  const series = loadSeries();
  const name = actorName(actor, labels);

  const byCountry = series?.actors[actor] ?? {};
  const rebuiltBefore = series?.rebuilt_before ?? "";
  const index = series?.index ?? [];
  // Countries with the most evaluable coverage first: that is where a rate means most.
  const countries = Object.entries(byCountry)
    .map(([polity, pts]) => ({
      polity,
      points: pts.map(([i, named, evaluable]) => ({
        day: index[i],
        named,
        evaluable,
        rebuilt: rebuiltBefore ? index[i] <= rebuiltBefore : false,
      })),
      weight: pts.reduce((n, p) => n + p[2], 0),
    }))
    .sort((a, b) => b.weight - a.weight);
  // A country gets a card only if it can carry a line. The rest are real but thin, and
  // they are summed into one stated line rather than 49 cards that each say "too thin":
  // the same rule the country table on the home applies to its rows.
  const canDraw = (c: (typeof countries)[number]) =>
    c.points.filter((p) => p.evaluable >= MIN_EVALUABLE_FOR_A_POINT).length >= 2;
  const drawn = countries.filter(canDraw);
  const thin = countries.filter((c) => !canDraw(c));
  const drawable = drawn.length;
  const thinEvaluable = thin.reduce((n, c) => n + c.weight, 0);
  const thinNamed = thin.reduce(
    (n, c) => n + c.points.reduce((m, p) => m + p.named, 0),
    0,
  );

  return (
    <>
      <TopBar when={runStamp(run)} iso={runIso(run)}>
        <ThemeToggle />
      </TopBar>
      <main className="wrap">
        <header className="series-head">
          <span className="series-kicker">Actor</span>
          <h2 className="series-title">{name}</h2>
          <p className="series-say">
            How much of each country&rsquo;s coverage named {name}, over the last {series?.days ?? 90} days. A source that covered three stories is
            counted three times: the question is how much of the coverage used the
            name, not how many outlets did.
          </p>
          {countries.length ? (
            <p className="series-note">
              {countries.length} countries could evaluate {name} at least once;{" "}
              {drawable} have enough days with {MIN_EVALUABLE_FOR_A_POINT} or more
              sources to draw a line. A rate over two sources is 0%, 50% or 100% and
              nothing else, so thinner days are counted but not drawn.
              {rebuiltBefore ? (
                <>
                  {" "}
                  Points up to {rebuiltBefore} were
                  recomputed from banded stories only, with today&rsquo;s alias table;
                  later points are the engine&rsquo;s own, summed across every story.
                  The dotted mark on a line is that boundary.
                </>
              ) : null}
            </p>
          ) : (
            <p className="series-note">
              Nothing to draw yet. The engine keeps these counts from its next run
              onward, and this page fills in as runs accumulate.
            </p>
          )}
        </header>

        {drawn.length ? (
          <section className="series-grid" aria-label={`${name} by country`}>
            {drawn.map((c) => (
              <article className="series-cell" key={c.polity}>
                <Link href={`/country/${slug(c.polity)}/`}>
                  <h2>{c.polity}</h2>
                </Link>
                <p className="series-n">
                  {c.weight.toLocaleString("en-US")} evaluable source-stories across{" "}
                  {c.points.length} days
                </p>
                <RateLine points={c.points} label={`${c.polity} naming ${name}`} />
              </article>
            ))}
          </section>
        ) : null}

        {thin.length ? (
          <p className="series-thin">
            {thin.length} further {thin.length === 1 ? "country" : "countries"} could
            evaluate {name} but never on enough sources in one day to draw a line.
            Summed rather than listed: <b>{thinNamed.toLocaleString("en-US")}</b> of{" "}
            <b>{thinEvaluable.toLocaleString("en-US")}</b> named {name}.
          </p>
        ) : null}

        <Link className="series-back" href="/">
          &larr; back to the stories
        </Link>
        <SiteFooter text={footer(run.report)} />
      </main>
    </>
  );
}
