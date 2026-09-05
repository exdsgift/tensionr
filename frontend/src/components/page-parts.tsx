/**
 * The blocks around the stories: the bar, the hero's left column, the aggregate strip
 * and the footer. All server components — no interactivity, no JavaScript.
 *
 * They are together in one file because each is a dozen lines of layout over prose that
 * was already composed in `lib/prose.ts`. Splitting them into four files would spread a
 * single reading of the page across four places without making any of them clearer.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Hook } from "@/lib/prose";

export function TopBar({ when }: { when: string }) {
  return (
    <header className="bar">
      <div className="in">
        <strong>tensionr</strong>
        <span className="sub">who is telling it differently</span>
        <span className="when">{when}</span>
      </div>
    </header>
  );
}

/**
 * The hero's left column: the figure, and the sentence that qualifies it.
 *
 * The figure is a fraction rather than a percentage on purpose. `7/12` carries its own
 * denominator, so a reader can see the sample it rests on; `58%` hides it, and this page
 * exists to keep the sample in view.
 */
export function Hook({
  hook,
  counts,
  polities,
}: {
  hook: Hook;
  counts: { actor: string; named: number; evaluable: number; miss: boolean }[];
  polities: number;
}) {
  if (hook.kind === "empty") {
    return (
      <div>
        <span className="lede">{hook.lede}</span>
        <div className="fig">
          {/* An em dash, not a zero. There is no figure, which is different from a
              figure of nothing. */}
          <b className="num na">—</b>
          <span className="unit">no figure this run can support</span>
        </div>
        <p className="say">{hook.say}</p>
        <div className="from">
          <span>
            {hook.stories} <b>stories</b>
          </span>
        </div>
      </div>
    );
  }
  return (
    <div>
      <span className="lede">{hook.lede}</span>
      <div className="fig">
        <b className="num">
          {hook.named}
          <i>/{hook.evaluable}</i>
        </b>
        <span className="unit">{hook.unit}</span>
      </div>
      <p className="say">{hook.say}</p>
      <div className="from">
        {counts.map((c) => (
          <span key={c.actor} className={c.miss ? "miss" : undefined}>
            <b>{c.actor}</b> {c.named}/{c.evaluable}
          </span>
        ))}
        <span>
          {polities} <b>polities</b>
        </span>
      </div>
    </div>
  );
}

export interface Tile {
  label: string;
  value: string;
}

/**
 * Five tiles. There were six: an "Aggregate index" hardcoded to "not computable yet",
 * which occupied a tile to say there was no number. The absence is stated in the
 * footer, where the methodology is, and does not need a tile of its own.
 */
export function AggregateStrip({ tiles }: { tiles: Tile[] }) {
  return (
    <div className="agg">
      {tiles.map((t) => (
        <div key={t.label}>
          <span className="lab">{t.label}</span>
          <span className="v">{t.value}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * The methods section, as one paragraph.
 *
 * It states the corpus before the sample, so the five stories above are read as a
 * selection rather than as the world.
 */
export function SiteFooter({ text }: { text: string }) {
  return (
    <>
      <Separator className="foot-rule" />
      <Card className="foot">
        <CardContent>
          <p>{text}</p>
          <p>
            The rows behind every figure are in{" "}
            <a href="data/stories.json">data/stories.json</a>, the same file this page
            was built from. It needs nothing from this site to be useful.
          </p>
        </CardContent>
      </Card>
    </>
  );
}
