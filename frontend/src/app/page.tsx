/**
 * The Ledger: one run, its five most divided stories, and what the run did not reach.
 *
 * A server component. Everything below happens once, at build time, on CI — reading the
 * run, composing the prose, projecting the map. What reaches a reader is HTML.
 *
 * The only client component on the page is the story list, because expanding a row is
 * genuinely interactive. Its content is still in the exported HTML; see the note in
 * `story-rows.tsx` for why that is not automatic and must not be undone.
 */

import { BrailleMap } from "@/components/braille-map";
import { EvidenceTable } from "@/components/evidence-table";
import { InfoPopover } from "@/components/info-popover";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Hook,
  SiteFooter,
  TopBar,
} from "@/components/page-parts";
import { LatentMap, type LatentStory } from "@/components/latent-map";
import { RightNow } from "@/components/right-now";
import { StoryRows, type StoryRowView } from "@/components/story-rows";
import { ThemeToggle } from "@/components/theme-toggle";
import { capNote, fitEvidence } from "@/lib/fit";
import { panel } from "@/lib/map";
import {
  actorBoard,
  bandNote,
  evidenceNote,
  footer,
  foreignLanguage,
  hook,
  percent,
  readingSentence,
  rowCounts,
  runIso,
  runStamp,
  selectionNote,
  sincePrevious,
  storyLanguages,
  thousands,
} from "@/lib/prose";
import {
  actorName,
  banded,
  FEATURED,
  lead,
  loadCoastlines,
  loadCoordinates,
  loadLabels,
  loadRun,
} from "@/lib/stories";

export default function Ledger() {
  const run = loadRun();
  const labels = loadLabels();
  const { wide, narrow } = loadCoastlines();
  const coordinates = loadCoordinates();

  const rows = banded(run);
  const hero = rows[0] ?? null;
  const featured = rows.slice(0, FEATURED);
  const report = run.report;

  const heroActor = hero ? actorName(hero.band[0], labels) : "";
  const empty = { markers: [], plotted: 0, carried: 0 };
  const widePanel = hero ? panel(hero, coordinates, wide, heroActor) : empty;
  const narrowPanel = hero ? panel(hero, coordinates, narrow, heroActor) : empty;

  // Where the five sit relative to one another in the embedding space that grouped
  // them. Each story carries its own series, so this does not depend on the page and
  // the engine agreeing about order. Absent when the engine judged the projection
  // would not have been honest about adjacency, which is a refusal rather than a gap.
  const latent = report.latent ?? null;
  const latentStories: LatentStory[] = featured
    .map((story, index) => ({ story, rank: index + 1 }))
    .filter(({ story }) => story.latent)
    .map(({ story, rank }) => ({
      rank,
      headline: story.headline.slice(0, 110),
      actor: actorName(story.band[0], labels),
      points: story.latent!.points,
      shown: story.latent!.shown,
      articles: story.latent!.articles,
    }));

  const views: StoryRowView[] = featured.map((story) => ({
    id: story.id,
    headline: story.headline.slice(0, 150),
    language: foreignLanguage(story),
    sources: story.sources,
    polities: story.polities.length,
    division: lead(story).division,
    counts: rowCounts(story, labels),
    lead: (() => {
      const f = lead(story);
      return {
        actor: actorName(story.band[0], labels),
        named: f.named,
        evaluable: f.evaluable,
      };
    })(),
    languages: storyLanguages(story),
    series: story.series ?? [],
    structure: story.structure ?? null,
    leadActor: actorName(story.band[0], labels),
    reading: readingSentence(story, labels),
    bandNote: bandNote(story),
    note: evidenceNote(story),
  }));

  // How heavy the page is depends on the run, not on this code: consecutive runs
  // carried 499 and 1,227 evidence rows. Rather than let that decide whether the build
  // passes, the page gives up its narrowest tables until it fits, and says so.
  const fitted = fitEvidence(featured);
  const evidence = Object.fromEntries(
    featured
      .filter((story) => fitted.kept.has(story.id))
      .map((story) => [
        story.id,
        <EvidenceTable story={story} labels={labels} key={story.id} />,
      ]),
  );

  const board = actorBoard(run, labels);
  // How many the run could measure at all, so a short board reads as a fact about the
  // actor table rather than as a truncation.
  const measurableActors = new Set(
    run.stories.flatMap((s) =>
      s.figures.filter((f) => f.measurable !== false).map((f) => f.actor),
    ),
  ).size;


  return (
    <>
      <a className="skip" href="#stories">
        Skip to the stories
      </a>
      <TopBar when={runStamp(run)} iso={runIso(run)}>
        <ThemeToggle />
      </TopBar>

      <main className="wrap">
        <section className="hook">
          <Hook
            hook={hook(hero, report, labels)}
            polities={hero ? hero.polities.length : 0}
          />
          <BrailleMap
            wide={wide}
            narrow={narrow}
            wideMarkers={widePanel.markers}
            narrowMarkers={narrowPanel.markers}
            legend={
              hero
                ? {
                    actor: heroActor,
                    plotted: widePanel.plotted,
                    carried: widePanel.carried,
                    // Placed sources, which is what the map could ever draw: the
                    // rest of the story has no country and never reaches it.
                    sources: hero.evidence.filter((r) => r.polity).length,
                  }
                : null
            }
          />
        </section>

        <section className="rows" id="stories">
          <h2>Stories</h2>
          {/* The mechanism, in the reader's words, before the first row. Without it
              the page shows a story about a rescue in Nepal beside a figure about the
              People's Republic of China and never says what joins them. The word
              "actor" appeared nowhere on this page until now. */}
          <p className="how">
            Every story here is measured on one <b>actor</b>: a person, a place or an
            organisation that some sources name and others leave out.{" "}
            <b>The bar shows how many named it</b>, and the mark on it is the even
            split, which the figure above spells out in sources.
          </p>
          <p className="span">
            {selectionNote(report, Math.min(FEATURED, rows.length))}
          </p>

          <div className="row-grid colhead">
            <span>
              Story
              <InfoPopover
                id="p-story"
                label="How a story is defined"
                title="What a story is"
              >
                <p>
                  Articles about the same happening, grouped across sources and
                  languages. Not an <em>event</em>: a ten-word headline does not
                  distinguish &ldquo;will resign&rdquo; from &ldquo;has
                  resigned&rdquo;, and neither do human annotators. Measured on
                  a hand-built gold set, precision is 0.86 at story granularity
                  and 0.23 at event granularity.
                </p>
              </InfoPopover>
            </span>
            <span>
              Sources
              <InfoPopover
                id="p-src"
                label="What a source is"
                title="What a source is"
              >
                <p>
                  One publisher, counted once, after reprints that shared a
                  headline word for word have been collapsed. A wire story
                  reprinted by six outlets is one voice agreeing with itself,
                  not six sources agreeing.
                </p>
              </InfoPopover>
            </span>
            <span>
              Polities
              <InfoPopover
                id="p-pol"
                label="What a polity is"
                title="What a polity is"
              >
                <p>
                  The state a publisher&rsquo;s domain could be placed in.
                  Placement is incomplete and the rate is published above; a
                  domain that could not be placed is counted, never dropped, and
                  shows as <em>&mdash;</em> in the evidence table.
                </p>
              </InfoPopover>
            </span>
            <span>
              How divided
              <InfoPopover
                id="p-named"
                label="How the division is measured"
                title="How the division is measured"
              >
                <p>
                  How many evaluable sources used a name for this actor, over
                  how many could have. <em>Evaluable</em> excludes rows shown as{" "}
                  <em>&ndash;</em>, where no alias exists in that script, because
                  silence there is the tool&rsquo;s and not the publisher&rsquo;s.
                  Omission is the signal, so it must never be confused with an absent
                  alias.
                </p>
              </InfoPopover>
            </span>
          </div>

          {featured.length ? (
            <StoryRows
              rows={views}
              evidence={evidence}
              capNote={capNote(fitted.dropped)}
            />
          ) : (
            <Alert>
              <AlertTitle>No row to show, and that is a result</AlertTitle>
              <AlertDescription>
                No story in this window cleared both floors. The window itself is
                described below: a figure under the floor would be a number about the
                sample rather than about the world.
              </AlertDescription>
            </Alert>
          )}
        </section>

        {/* Immediately after the five, because it is about the five and nothing else:
            the space it draws is the one they were grouped in. */}
        {latent && latentStories.length >= 2 ? (
          <LatentMap stories={latentStories} facts={latent} />
        ) : null}

        {/* After the stories, not before: the five are what the reader came for, and
            the corpus behind them is what qualifies them. */}
        <RightNow
          actors={board}
          measurable={measurableActors}
          facts={{
            articles: thousands(report.window.articles),
            domains: thousands(report.polities.domains),
            hours: Math.round((report.window.slots * 15) / 60),
            themes: report.grouping.themes,
            stories: report.grouping.stories,
            withBand: report.published.with_a_band,
            neverReached: thousands(
              report.window.articles - (report.grouping.articles_in_stories ?? 0),
            ),
            neverReachedPct: Math.round(
              (100 *
                (report.window.articles -
                  (report.grouping.articles_in_stories ?? 0))) /
                report.window.articles,
            ),
            polityRate: percent(report.polities.rate),
            since: sincePrevious(run),
          }}
        />

        <SiteFooter text={footer(report)} />
      </main>
    </>
  );
}
