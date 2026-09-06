/**
 * One country, across every actor its outlets could evaluate, run by run.
 *
 * The inverse of the actor page: what did outlets publishing from here name, and how
 * did that move. Pages exist for every polity the series has seen, resolved through the
 * slug table rather than reconstructed from it, so a name with accents or spaces round
 * trips exactly.
 */

import Link from "next/link";
import { notFound } from "next/navigation";

import { RateLine, MIN_EVALUABLE_FOR_A_POINT } from "@/components/rate-line";
import { SiteFooter, TopBar } from "@/components/page-parts";
import { ThemeToggle } from "@/components/theme-toggle";
import { footer, runIso, runStamp } from "@/lib/prose";
import {
  actorName,
  loadCoordinates,
  loadLabels,
  loadRun,
  loadSeries,
} from "@/lib/stories";
import { slug } from "@/lib/slug";

/** Every polity that can be placed on the map, plus any the series has seen. */
function polities(): string[] {
  const seen = new Set(Object.keys(loadCoordinates()));
  for (const byCountry of Object.values(loadSeries()?.actors ?? {}))
    for (const polity of Object.keys(byCountry)) seen.add(polity);
  return [...seen].sort();
}

export function generateStaticParams() {
  return polities().map((p) => ({ country: slug(p) }));
}

export default async function CountryPage({
  params,
}: {
  params: Promise<{ country: string }>;
}) {
  const { country } = await params;
  const polity = polities().find((p) => slug(p) === country);
  if (!polity) notFound();
  const run = loadRun();
  const labels = loadLabels();
  const series = loadSeries();
  const rebuiltBefore = series?.rebuilt_before ?? "";
  const index = series?.index ?? [];

  const actors = Object.entries(series?.actors ?? {})
    .filter(([, byCountry]) => polity in byCountry)
    .map(([actor, byCountry]) => ({
      actor,
      name: actorName(actor, labels),
      points: byCountry[polity].map(([i, named, evaluable]) => ({
        day: index[i],
        named,
        evaluable,
        rebuilt: rebuiltBefore ? index[i] <= rebuiltBefore : false,
      })),
      weight: byCountry[polity].reduce((n, p) => n + p[2], 0),
    }))
    .sort((a, b) => b.weight - a.weight);

  // Same rule as the actor page: a card only where a line can be drawn, the rest summed
  // into one stated line rather than a row of cards that each say "too thin".
  const canDraw = (a: (typeof actors)[number]) =>
    a.points.filter((p) => p.evaluable >= MIN_EVALUABLE_FOR_A_POINT).length >= 2;
  const drawn = actors.filter(canDraw);
  const thin = actors.filter((a) => !canDraw(a));
  const thinEvaluable = thin.reduce((n, a) => n + a.weight, 0);
  const thinNamed = thin.reduce(
    (n, a) => n + a.points.reduce((m, p) => m + p.named, 0),
    0,
  );

  return (
    <>
      <TopBar when={runStamp(run)} iso={runIso(run)}>
        <ThemeToggle />
      </TopBar>
      <main className="wrap">
        <header className="series-head">
          <span className="series-kicker">Country of publication</span>
          <h2 className="series-title">{polity}</h2>
          <p className="series-say">
            How much of the coverage published from {polity} named each actor, over the last {series?.days ?? 90} days. Placement is by where a publisher
            publishes, not who owns it; a source the table could not place is counted on
            the home and appears on no country page.
          </p>
          {actors.length ? (
            <p className="series-note">
              Outlets from {polity} could evaluate {actors.length} actors at least once.
              Days with fewer than {MIN_EVALUABLE_FOR_A_POINT} sources are counted but
              not drawn.
            </p>
          ) : (
            <p className="series-note">
              No run has yet carried enough coverage from {polity} to evaluate an actor.
              This page fills in as runs accumulate.
            </p>
          )}
        </header>

        {drawn.length ? (
          <section className="series-grid" aria-label={`actors as named from ${polity}`}>
            {drawn.map((a) => (
              <article className="series-cell" key={a.actor}>
                <Link href={`/actor/${a.actor}/`}>
                  <h2>{a.name}</h2>
                </Link>
                <p className="series-n">
                  {a.weight.toLocaleString("en-US")} evaluable source-stories across{" "}
                  {a.points.length} days
                </p>
                <RateLine points={a.points} label={`${polity} naming ${a.name}`} />
              </article>
            ))}
          </section>
        ) : null}

        {thin.length ? (
          <p className="series-thin">
            {thin.length} further {thin.length === 1 ? "actor was" : "actors were"}{" "}
            evaluable from {polity} but never on enough sources in one day to draw a
            line. Summed rather than listed: <b>{thinNamed.toLocaleString("en-US")}</b>{" "}
            of <b>{thinEvaluable.toLocaleString("en-US")}</b> named.
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
