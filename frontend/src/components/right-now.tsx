/**
 * What the window is about, and what it cost to look.
 *
 * Two cards. The first is the leaderboard: which actors the world's headlines named,
 * ranked by how much of the coverage used the name. The second is the run itself -
 * corpus, grouping, and what never reached a story - which was previously buried in one
 * long paragraph in the footer where nobody counted it.
 *
 * The leaderboard is of *actors*, not of words, and the reason is measured rather than
 * stylistic: see the note on `actorBoard`. Briefly, the fifteen commonest words in a
 * real capture are articles and prepositions in five languages, and every attempt to
 * rank words by how unusual they are surfaces content-farm noise instead of news.
 *
 * The peak division column is what ties this to the rest of the page: an actor can be
 * named a great deal and be uncontroversial, or named rarely and split the room. Both
 * are worth seeing next to each other, and neither is the other's summary.
 */

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface ActorRow {
  key: string;
  actor: string;
  named: number;
  evaluable: number;
  stories: number;
  peak: number;
}

export interface RunFacts {
  articles: string;
  domains: string;
  hours: number;
  themes: number;
  stories: number;
  withBand: number;
  neverReached: string;
  neverReachedPct: number;
  polityRate: string;
  since: string;
}

export function RightNow({
  actors,
  facts,
  measurable,
}: {
  actors: ActorRow[];
  facts: RunFacts;
  /** How many actors were measurable at all, so a short list reads as a fact. */
  measurable: number;
}) {
  return (
    <section className="rightnow" id="right-now">
      <Card className="rn-card">
        <CardHeader>
          <CardTitle>Who the window is about</CardTitle>
          <p className="rn-sub">
            Actors the headlines named, over every story in this{" "}
            {facts.hours}-hour window. Resolved across languages rather than matched as
            text, so <i>Иран</i>, <i>إيران</i> and <i>Iran</i> are one row.
          </p>
        </CardHeader>
        <CardContent>
          <Table
            className="rn-table"
            containerProps={{ className: "rn-scroll" }}
          >
            <caption className="vh">
              Actors ranked by how much of the window&rsquo;s coverage named them
            </caption>
            <TableHeader>
              <TableRow>
                <TableHead scope="col">Actor</TableHead>
                <TableHead scope="col">Named in</TableHead>
                <TableHead scope="col" className="rn-barhead">
                  <span className="vh">share of coverage</span>
                </TableHead>
                <TableHead scope="col">Stories</TableHead>
                <TableHead scope="col">Widest split</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {actors.map((a) => {
                const rate = a.evaluable ? a.named / a.evaluable : 0;
                return (
                  <TableRow key={a.actor}>
                    <TableCell className="rn-actor">
                      {/* Every row now leads to the actor across countries and runs. */}
                      <Link href={`/actor/${a.key}/`}>{a.actor}</Link>
                    </TableCell>
                    <TableCell className="rn-n">
                      <b>{a.named.toLocaleString("en-US")}</b> of{" "}
                      {a.evaluable.toLocaleString("en-US")}
                    </TableCell>
                    <TableCell>
                      <span className="rn-bar" aria-hidden="true">
                        <i style={{ width: `${Math.max(rate * 100, 0.6)}%` }} />
                      </span>
                      <span className="rn-pct">
                        {rate >= 0.01 ? `${Math.round(rate * 100)}%` : "<1%"}
                      </span>
                    </TableCell>
                    <TableCell className="rn-n">{a.stories}</TableCell>
                    <TableCell className="rn-n">
                      {a.peak > 0 ? a.peak.toFixed(3) : "—"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          <p className="rn-note">
            {measurable <= actors.length ? (
              <>
                All <b>{measurable}</b> actors the run could measure are listed. The
                vocabulary is a curated table, not everything a headline mentions, so a
                short list is a property of the table rather than of the news.
              </>
            ) : (
              <>
                The {actors.length} most-named of <b>{measurable}</b> measurable actors.
              </>
            )}{" "}
            A source that covered three stories is counted three times, because the
            question is how much of the coverage named an actor rather than how many
            outlets did.
          </p>
        </CardContent>
      </Card>

      <Card className="rn-card">
        <CardHeader>
          <CardTitle>What it took to look</CardTitle>
          <p className="rn-sub">
            The corpus behind the five stories above, so they read as a selection rather
            than as the world.
          </p>
        </CardHeader>
        <CardContent>
          <dl className="rn-facts">
            <div>
              <dt>Articles read</dt>
              <dd>{facts.articles}</dd>
              <p>from {facts.domains} domains, over {facts.hours} hours</p>
            </div>
            <div>
              <dt>Never reached a story</dt>
              <dd>
                {facts.neverReached} <Badge variant="outline">{facts.neverReachedPct}%</Badge>
              </dd>
              <p>joined no theme, or one too uniform to separate</p>
            </div>
            <div>
              <dt>Grouped into</dt>
              <dd>
                {facts.stories.toLocaleString("en-US")} stories
              </dd>
              <p>from {facts.themes.toLocaleString("en-US")} themes</p>
            </div>
            <div>
              <dt>Cleared both floors</dt>
              <dd>{facts.withBand}</dd>
              <p>enough evaluable sources, in enough countries</p>
            </div>
            <div>
              <dt>Sources placed in a country</dt>
              <dd>{facts.polityRate}</dd>
              <p>the rest are counted, never dropped</p>
            </div>
            <div>
              <dt>Since the previous run</dt>
              <dd>{facts.since}</dd>
              <p>the delivered gap, not the schedule</p>
            </div>
          </dl>
        </CardContent>
      </Card>
    </section>
  );
}
