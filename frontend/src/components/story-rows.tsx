"use client";

/**
 * The five stories, each expandable, each with its evidence table expandable inside it.
 *
 * This is the only place on the page where the choice of primitive is load-bearing
 * rather than cosmetic. A collapsed Base UI panel does **not** render its content into
 * the exported HTML by default, which for this site is disqualifying: the story text has
 * to be there for crawlers, reader mode, link previews and anyone with scripting off.
 * `hiddenUntilFound` fixes that and does one better than `keepMounted` — the closed
 * panel is findable with Ctrl+F.
 *
 * Do not remove those props to tidy the markup. There is a test that fails if the text
 * leaves the HTML, and it strips `<script>` blocks first, because Next serialises the
 * whole React tree into the RSC payload and a naive grep passes on every configuration
 * including the broken one.
 *
 * The evidence tables arrive as `children` from the server rather than being rendered
 * here. They are the biggest thing on the page — up to 233 rows — and a client
 * component would put every row in the RSC payload as well as in the HTML, paying for
 * them twice.
 */

import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { ByCountry, type Structure } from "@/components/by-country";
import { DivisionLine, type Point } from "@/components/division-line";
import { SplitBar } from "@/components/split-bar";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export interface StoryRowView {
  id: string;
  headline: string;
  language: string | null;
  sources: number;
  polities: number;
  division: number;
  counts: { actor: string; named: number; evaluable: number; miss: boolean }[];
  /** The band's leading actor, drawn as a split. */
  lead: { actor: string; named: number; evaluable: number };
  languages: { shown: { name: string; sources: number }[]; more: number };
  series: Point[];
  structure: Structure | null;
  leadActor: string;
  reading: { before: string; balanced: string | null; split: string | null };
  bandNote: string | null;
  note: { collapsed: string; unresolved: string; links: string };
}

export function StoryRows({
  rows,
  evidence,
  capNote,
}: {
  rows: StoryRowView[];
  /** One rendered evidence table per row, keyed by story id. Absent means the page
      could not afford that table; the row says so rather than showing nothing. */
  evidence: Record<string, ReactNode>;
  /** Stated once, above the rows, when the page had to give tables up. */
  capNote: string | null;
}) {
  return (
    <>
      {capNote ? <p className="read sub cap-note">{capNote}</p> : null}
      <Accordion
        // The first row open, so the page shows what an expanded row looks like without
        // asking the reader to guess that the rows expand at all.
        defaultValue={rows.length ? [rows[0].id] : []}
        hiddenUntilFound
        className="rows-list"
      >
        {rows.map((row) => (
          <AccordionItem value={row.id} key={row.id} className="row">
            <AccordionTrigger className="row-trigger">
              <span className="row-grid">
                <span className="title">
                  {row.headline}
                  {row.language ? <i className="lang">{row.language}</i> : null}
                  {/* Which languages the story is told in. The tag above labels only
                      the one headline shown, and only when it is not English, so a
                      story carried by 72 Russian and 53 Ukrainian outlets showed
                      nothing at all. This is the fact that was missing. */}
                  <small>
                    {/* Repeated from the columns on purpose, and hidden by CSS at the
                        width where the columns collapse. One of the two is always
                        redundant; which one depends on the viewport. */}
                    <span className="title-counts">
                      {row.sources} sources · {row.polities} polities ·{" "}
                    </span>
                    told in{" "}
                    {row.languages.shown.map((l, i) => (
                      <span key={l.name}>
                        {i > 0 ? ", " : ""}
                        {l.name} <span className="lang-n">{l.sources}</span>
                      </span>
                    ))}
                    {row.languages.more ? ` and ${row.languages.more} more` : ""}
                  </small>
                </span>
                <span className="cell num" data-l="sources">
                  {row.sources}
                </span>
                <span className="cell num" data-l="polities">
                  {row.polities}
                </span>
                <span className="actors" data-l="named by">
                  <SplitBar
                    named={row.lead.named}
                    evaluable={row.lead.evaluable}
                    actor={row.lead.actor}
                    division={row.division}
                  />
                  <DivisionLine points={row.series} label={row.headline} />
                  {row.counts.length > 1 ? (
                    <span className="actors-rest">
                      {row.counts
                        .filter((c) => c.actor !== row.lead.actor)
                        .map((c) => (
                          <Badge
                            key={c.actor}
                            variant="outline"
                            className={c.miss ? "miss" : undefined}
                          >
                            {c.actor} {c.named}/{c.evaluable}
                          </Badge>
                        ))}
                    </span>
                  ) : null}
                </span>
              </span>
            </AccordionTrigger>

            <AccordionContent>
              <p className="read">
                {row.reading.before}
                {row.reading.balanced ? (
                  <>
                    , which is{" "}
                    <em>{row.reading.balanced.replace(/^which is /, "")}</em>
                  </>
                ) : null}
                .{row.reading.split ? ` ${row.reading.split}` : ""}
              </p>

              {row.bandNote ? <p className="read sub">{row.bandNote}</p> : null}

            {row.structure ? (
              <ByCountry structure={row.structure} actor={row.leadActor} />
            ) : null}

              {evidence[row.id] ? (
                <Collapsible>
                  <CollapsibleTrigger className="ev-toggle">
                    All {row.sources} sources, and who each one named
                  </CollapsibleTrigger>
                  <CollapsibleContent hiddenUntilFound>
                    {evidence[row.id]}
                    <p className="ev-note">
                      {row.note.collapsed} {row.note.unresolved}{" "}
                      {row.note.links}
                    </p>
                  </CollapsibleContent>
                </Collapsible>
              ) : (
                // Bounded, and said out loud. The figures above are the run's claim; the
                // rows behind them are served beside this page.
                <p className="ev-note">
                  The {row.sources} sources behind this row are not on this
                  page: it would have gone past its weight budget. They are in{" "}
                  <a href="data/stories.json">data/stories.json</a>, one row per
                  publisher, the same rows the figures were computed from.
                </p>
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </>
  );
}
