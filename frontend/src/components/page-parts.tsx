/**
 * The blocks around the stories: the bar, the hero's left column, the aggregate strip
 * and the footer. All server components — no interactivity, no JavaScript.
 *
 * They are together in one file because each is a dozen lines of layout over prose that
 * was already composed in `lib/prose.ts`. Splitting them into four files would spread a
 * single reading of the page across four places without making any of them clearer.
 */

import type { ReactNode } from "react";

import { Separator } from "@/components/ui/separator";
import type { Hook } from "@/lib/prose";

export function TopBar({
  when,
  children,
}: {
  when: string;
  children?: ReactNode;
}) {
  return (
    <header className="bar">
      <div className="in">
        {/* The page's only h1. It was a <strong>, which left the document outline
            starting at <h2>Stories</h2> and gave a screen reader no title at all. The
            tagline is inside it because together they are the page's name, and it is
            styled to look exactly as it did. */}
        <h1>
          tensionr <span className="sub">who is telling it differently</span>
        </h1>
        <span className="when">{when}</span>
        {children}
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
  polities,
}: {
  hook: Hook;
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
        <span>
          {polities} <b>polities</b>
        </span>
        <a href="#stories">read the story below</a>
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
      {/* A landmark, not a Card. It was the only boxed element on the page, which made
          the methods statement read as an aside rather than as the thing that qualifies
          every figure above it. */}
      <footer className="foot">
        <p>{text}</p>
        <p>
          The rows behind every figure are in{" "}
          <a href="data/stories.json">data/stories.json</a>, the same file this page was
          built from. It needs nothing from this site to be useful.
        </p>
      </footer>
    </>
  );
}
