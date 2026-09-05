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
import {
  AggregateStrip,
  Hook,
  SiteFooter,
  TopBar,
} from "@/components/page-parts";
import { StoryRows, type StoryRowView } from "@/components/story-rows";
import { capNote, fitEvidence } from "@/lib/fit";
import { panel } from "@/lib/map";
import {
  bandNote,
  evidenceNote,
  footer,
  foreignLanguage,
  hook,
  legend,
  percent,
  readingSentence,
  rowCounts,
  runStamp,
  selectionNote,
  sincePrevious,
  thousands,
} from "@/lib/prose";
import {
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

  const widePanel = hero
    ? panel(hero, coordinates, wide)
    : { markers: [], plotted: 0 };
  const narrowPanel = hero
    ? panel(hero, coordinates, narrow)
    : { markers: [], plotted: 0 };

  const views: StoryRowView[] = featured.map((story) => ({
    id: story.id,
    headline: story.headline.slice(0, 150),
    language: foreignLanguage(story),
    sources: story.sources,
    polities: story.polities.length,
    division: lead(story).division,
    counts: rowCounts(story, labels),
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

  const tiles = [
    {
      label: "Stories with a band",
      value: `${report.published.with_a_band} of ${report.published.stories}`,
    },
    { label: "Articles in window", value: thousands(report.window.articles) },
    { label: "Sources placed", value: percent(report.polities.rate) },
    { label: "Window", value: `${report.window.slots} × 15 min` },
    { label: "Since previous run", value: sincePrevious(run) },
  ];

  return (
    <>
      <TopBar when={runStamp(run)} />

      <div className="wrap">
        <section className="hook">
          <Hook
            hook={hook(hero, report, labels)}
            counts={hero ? rowCounts(hero, labels) : []}
            polities={hero ? hero.polities.length : 0}
          />
          <BrailleMap
            wide={wide}
            narrow={narrow}
            wideMarkers={widePanel.markers}
            narrowMarkers={narrowPanel.markers}
            legend={legend(hero, widePanel.plotted, labels)}
          />
        </section>

        <AggregateStrip tiles={tiles} />

        <section className="rows">
          <h2>Stories</h2>
          <p className="span">
            {selectionNote(report, Math.min(FEATURED, rows.length))}
          </p>

          <div className="grid colhead">
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
                  shows as <em>&mdash;</em> in the evidence.
                </p>
              </InfoPopover>
            </span>
            <span>
              Named by
              <InfoPopover
                id="p-named"
                label="What named by means"
                title="What &ldquo;named by&rdquo; means"
              >
                <p>
                  How many evaluable sources used a name for this actor, over
                  how many could have. <em>Evaluable</em> excludes rows where no
                  alias exists in that script &mdash; shown as <em>&ndash;</em>{" "}
                  &mdash; because silence there is the tool&rsquo;s, not the
                  publisher&rsquo;s. Omission is the signal, so it must never be
                  confused with an absent alias.
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
            <p className="read">
              No story in this window cleared both floors, so there is no row to
              show. The window itself is described below.
            </p>
          )}
        </section>

        <SiteFooter text={footer(report)} />
      </div>
    </>
  );
}
