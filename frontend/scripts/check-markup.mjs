/**
 * The static export has to carry the page's text as markup, not only as data.
 *
 * This guards the one property that made the whole component choice load-bearing: a
 * collapsed Base UI panel does not render its content into the exported HTML unless it
 * is told to, and without it the five stories exist only after React runs — invisible to
 * crawlers, to reader mode, to link previews and to anyone with scripting off.
 *
 * The check strips `<script>` blocks first, and that is the entire point. Next
 * serialises the whole React tree into the RSC flight payload inside script tags, so
 * grepping the raw file finds the text under *every* configuration, including the
 * broken one. A naive version of this check passes when the page is wrong.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { statSync, readdirSync } from "node:fs";

/**
 * Refuse to grade a stale build.
 *
 * A failed `next build` leaves the previous `out/` in place, so these checks happily
 * measured output from before the change that broke the build and reported a pass. A
 * check that passes on stale output is worse than no check: it says the thing it was
 * written to catch did not happen.
 */
function refuseStaleOutput(outDir) {
  const built = statSync(path.join(outDir, "index.html")).mtimeMs;
  const roots = [
    path.join(outDir, "..", "src"),
    path.join(outDir, "..", "..", "data", "stories.json"),
  ];
  let newest = 0;
  const walk = (p) => {
    const s = statSync(p);
    if (s.isDirectory()) for (const e of readdirSync(p)) walk(path.join(p, e));
    else newest = Math.max(newest, s.mtimeMs);
  };
  for (const r of roots) {
    try { walk(r); } catch { /* absent input is not this check's business */ }
  }
  if (newest > built) {
    console.error(
      "out/index.html is older than the sources it was built from — run `npm run build`.\n" +
      "(A failed build leaves the previous export in place, and grading that reports a\n" +
      " pass for output nobody produced.)",
    );
    process.exit(1);
  }
}

const OUT = path.join(import.meta.dirname, "..", "out", "index.html");
const DATA = path.join(import.meta.dirname, "..", "..", "data", "stories.json");

refuseStaleOutput(path.dirname(OUT));
const raw = readFileSync(OUT, "utf-8");
const markup = raw.replace(/<script[\s\S]*?<\/script>/g, "");
const text = decode(markup.replace(/<[^>]+>/g, " ").replace(/\s+/g, " "));

const run = JSON.parse(readFileSync(DATA, "utf-8"));
const featured = run.stories
  .filter((s) => s.band?.length && s.evidence?.length && s.featured)
  .slice(0, 5);

const failures = [];
const check = (ok, what) => {
  if (!ok) failures.push(what);
};

check(featured.length > 0, "no featured story in the data to check against");

for (const story of featured) {
  check(
    text.includes(decode(story.headline.slice(0, 40))),
    `headline missing from markup: ${story.headline.slice(0, 50)}`,
  );
  const row = story.evidence[0];
  check(
    text.includes(row.domain),
    `evidence row missing from markup: ${row.domain} (story ${story.id})`,
  );
  // The headline lives in the trigger, which is always rendered — so checking it
  // alone would pass even with the panels empty. The reading sentence is inside the
  // accordion panel, which is the thing that actually needs `hiddenUntilFound`.
  check(
    text.includes(`${story.sources} publishers across`),
    `reading sentence missing from markup (story ${story.id})`,
  );
}

// The vocabulary the page publishes. A mark is a glyph, never a colour alone.
for (const glyph of ["●", "○"]) {
  check(text.includes(glyph), `mark glyph missing from markup: ${glyph}`);
}

// The definitions are in the markup too — a native popover, not a portal.
check(
  text.includes("a ten-word headline does not distinguish"),
  "popover definitions missing from markup",
);

// Scripting-off readability depends on this rule surviving in the stylesheet.
check(
  raw.includes('[data-slot="accordion-content"][hidden]'),
  "the noscript rule that reveals collapsed panels is missing",
);

function decode(s) {
  return s
    .replace(/&#x27;|&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ");
}

if (failures.length) {
  console.error("The exported HTML does not carry the page:\n");
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

const words = text.trim().split(/\s+/).length;
console.log(
  `markup check passed: ${featured.length} stories, ${words.toLocaleString("en-US")} words readable with scripts stripped`,
);
