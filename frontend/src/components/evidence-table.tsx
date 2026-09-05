/**
 * Every source, one row each, and who each one named.
 *
 * A server component with no interactivity — it renders to HTML at build time and ships
 * no JavaScript.
 *
 * The table is wider than a phone and stays that way. Six columns of which one is a
 * headline cannot be folded into 320 pixels without either wrapping the rows into cards
 * — which drops the table semantics a screen reader depends on, and with them the
 * row/column relationship that is the whole point of showing the evidence — or hiding
 * columns, which here means hiding the marks the page exists to publish. So it scrolls
 * sideways inside its own box, and the box is made operable: `tabIndex=0` plus a role
 * and a name, because a region only a mouse or a finger can reach fails WCAG SC 2.1.1.
 * Safari does not make scrollers focusable by itself, and neither does Chrome once a
 * scroller has a focusable child.
 */

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  actorName,
  PRESENT,
  UNRESOLVED,
  type Mark,
  type EvidenceRow,
  type Story,
} from "@/lib/stories";

/**
 * A mark is a glyph and a class, never a colour alone. See docs/adr/0001 §2: the
 * character has to be sufficient on its own.
 */
function glyph(mark: Mark | undefined): { char: string; label: string } {
  if (mark === PRESENT) return { char: "●", label: "named" };
  if (mark === UNRESOLVED) return { char: "–", label: "not evaluable" };
  return { char: "○", label: "did not name" };
}

function markClass(mark: Mark | undefined): string {
  if (mark === PRESENT) return "mark-on";
  if (mark === UNRESOLVED) return "mark-ne";
  return "mark-off";
}

/**
 * The publisher, as a link to the article it published.
 *
 * The visible text stays the domain, because the domain is the evidence — a reader is
 * comparing publishers, and a row of URLs would be unreadable. The URL is the proof
 * underneath it.
 *
 * `nofollow` because these links are generated in bulk and never reviewed: pointing at
 * an article is not a judgement about it. `noopener` because it opens in a new tab,
 * which is what comparing forty sources needs. The URL is left exactly as GDELT
 * recorded it, `http` included, since rewriting it would invent an address nobody
 * observed. A row with no URL is plain text rather than a dead anchor.
 */
function SourceLink({ row }: { row: EvidenceRow }) {
  if (!row.url) return <>{row.domain}</>;
  return (
    <a
      className="src-link"
      href={row.url}
      rel="nofollow noopener"
      target="_blank"
    >
      {row.domain}
    </a>
  );
}

export function EvidenceTable({
  story,
  labels,
}: {
  story: Story;
  labels: Record<string, string>;
}) {
  const captionId = `ev-cap-${story.id}`;
  const caption = `${story.evidence.length} sources, and who each one named`;

  return (
    <Table
      className="src"
      containerProps={{
        className: "ev-scroll",
        tabIndex: 0,
        role: "region",
        "aria-labelledby": captionId,
      }}
    >
      {/* Clipped rather than display:none — an off-screen caption still names the
          table, and being out of flow it cannot widen it. */}
      <caption className="vh" id={captionId}>
        {caption}
      </caption>
      <TableHeader>
        <TableRow>
          <TableHead scope="col">Source</TableHead>
          <TableHead scope="col">Polity</TableHead>
          {story.band.map((actor) => (
            <TableHead scope="col" className="m" key={actor}>
              {actorName(actor, labels)}
            </TableHead>
          ))}
          <TableHead scope="col">Headline</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {story.evidence.map((row, i) => (
          <TableRow key={`${row.domain}-${i}`}>
            <TableCell className="who">
              <SourceLink row={row} />
            </TableCell>
            {/* An em dash, not an empty cell: the domain could not be placed in a
                  polity, and that is a stated outcome rather than missing data. */}
            <TableCell className="pol">{row.polity ?? "—"}</TableCell>
            {story.band.map((actor) => {
              const g = glyph(row.marks[actor]);
              return (
                <TableCell
                  className={`m ${markClass(row.marks[actor])}`}
                  key={actor}
                >
                  <span aria-hidden="true">{g.char}</span>
                  <span className="vh">{g.label}</span>
                </TableCell>
              );
            })}
            {/* dir=auto so a right-to-left headline reads in its own direction. */}
            <TableCell className="hl" dir="auto">
              {row.title.slice(0, 160)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
