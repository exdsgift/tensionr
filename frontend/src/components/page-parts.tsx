/**
 * The blocks around the stories: the bar, the hero's left column, the aggregate strip
 * and the footer. All server components — no interactivity, no JavaScript.
 *
 * They are together in one file because each is a dozen lines of layout over prose that
 * was already composed in `lib/prose.ts`. Splitting them into four files would spread a
 * single reading of the page across four places without making any of them clearer.
 *
 * Server components, and everything they say is in the HTML. The one exception is the
 * age of the run in the bar, which is an enhancement rather than content: the instant
 * itself is rendered and true, and only "how long ago" needs the reader's own clock,
 * because this is a static export and a build-time age is wrong before it is read.
 */

import Script from "next/script";
import type { ReactNode } from "react";

import { SplitBar } from "@/components/split-bar";
import { Separator } from "@/components/ui/separator";
import type { Hook } from "@/lib/prose";

/**
 * When the stories were last rebuilt.
 *
 * The stamp was already here and said only "5 Sep · 04:48 UTC", with nothing to say
 * what the number was about. A reader asking "how old is this page" had no way to know
 * this was the answer.
 *
 * The absolute UTC instant is the part that lives in the HTML, and it is the part that
 * is true. "Four hours ago" cannot be: this is a static export built once and served
 * for as long as the next run takes, so an age rendered at build time is wrong by the
 * time anybody reads it, and wrong in the direction that flatters the page. The age is
 * therefore computed in the reader's own browser, from the same instant, and appended
 * only if scripting is on. With scripting off the reader keeps a timestamp that never
 * goes stale rather than a lie that ages.
 */
export function TopBar({
  when,
  iso,
  children,
}: {
  when: string;
  /** The same instant as `when`, ISO 8601, for `<time>` and for the age script. */
  iso: string;
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
        <p className="when">
          <span className="when-label">Stories updated</span>{" "}
          <time dateTime={iso} id="run-when">
            {when}
          </time>
          {/* Filled in by the script below, in the reader's browser, or left empty. */}
          <span className="when-ago" id="run-ago" suppressHydrationWarning />
        </p>
        {/* The one event this site can vouch for, as a feed any reader can subscribe
            to. A plain link to a static file: no script, no service. */}
        <a className="feed" href="data/feed.xml" title="Atom feed: splits shown to follow a country line">
          feed
        </a>
        {children}
      </div>
      <Script
        id="run-age"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{ __html: AGE }}
      />
    </header>
  );
}

/**
 * How long ago the run was, measured against the reader's clock rather than the
 * builder's. Plain DOM and no framework, like the map's placement pass, and it writes
 * into a node React leaves alone so a late arrival cannot trip hydration.
 *
 * Deliberately coarse. The engine is scheduled every four hours and delivers roughly
 * 70% of what it asks for, so minutes are noise: "3 h ago" is the honest resolution,
 * and anything under an hour is "just now" rather than a spuriously precise count.
 */
const AGE = `(function () {
  var el = document.getElementById('run-when');
  var out = document.getElementById('run-ago');
  if (!el || !out) return;
  var then = new Date(el.getAttribute('datetime'));
  if (isNaN(then)) return;
  function paint() {
    var mins = Math.floor((Date.now() - then.getTime()) / 60000);
    if (mins < 0) { out.textContent = ''; return; }
    var say;
    if (mins < 60) say = 'just now';
    else if (mins < 60 * 48) say = Math.floor(mins / 60) + ' h ago';
    else say = Math.floor(mins / 1440) + ' days ago';
    out.textContent = ' \u00b7 ' + say;
  }
  paint();
  setInterval(paint, 60000);
})();`

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
      {/* The same bar the rows use, so the reading is taught once at the top and
          recognised below rather than explained twice. */}
      <SplitBar
        named={hook.named}
        evaluable={hook.evaluable}
        actor={hook.unit.replace(/^sources named /, "")}
        evenSplit
        restate={false}
        className="split-hero"
      />
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
