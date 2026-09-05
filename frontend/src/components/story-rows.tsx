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
  reading: { before: string; balanced: string | null; split: string | null };
  bandNote: string | null;
  note: { collapsed: string; unresolved: string; links: string };
}

export function StoryRows({
  rows,
  evidence,
}: {
  rows: StoryRowView[];
  /** One rendered evidence table per row, keyed by story id. */
  evidence: Record<string, ReactNode>;
}) {
  return (
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
            <span className="grid">
              <span className="title">
                {row.headline}
                {row.language ? <i className="lang">{row.language}</i> : null}
                <small>
                  {row.sources} sources · {row.polities} polities · division{" "}
                  {row.division.toFixed(3)}
                </small>
              </span>
              <span className="cell num" data-l="sources">
                {row.sources}
              </span>
              <span className="cell num" data-l="polities">
                {row.polities}
              </span>
              <span className="actors">
                {row.counts.map((c, i) => (
                  <span key={c.actor} className={c.miss ? "miss" : undefined}>
                    {i > 0 ? " · " : ""}
                    <b>{c.actor}</b> {c.named}/{c.evaluable}
                  </span>
                ))}
              </span>
            </span>
          </AccordionTrigger>

          <AccordionContent>
            <p className="read">
              {row.reading.before}
              {row.reading.balanced ? (
                <>
                  , which is <em>{row.reading.balanced.replace(/^which is /, "")}</em>
                </>
              ) : null}
              .{row.reading.split ? ` ${row.reading.split}` : ""}
            </p>

            {row.bandNote ? <p className="read sub">{row.bandNote}</p> : null}

            <Collapsible>
              <CollapsibleTrigger className="ev-toggle">
                All {row.sources} sources, and who each one named
              </CollapsibleTrigger>
              <CollapsibleContent hiddenUntilFound>
                {evidence[row.id]}
                <p className="ev-note">
                  {row.note.collapsed} {row.note.unresolved} {row.note.links}
                </p>
              </CollapsibleContent>
            </Collapsible>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
