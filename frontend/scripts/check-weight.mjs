/**
 * The page weight budget from docs/adr/0002, enforced.
 *
 * Two numbers, because they mean different things. The content half is what this
 * project controls and is the one that says whether the page is getting fatter for a
 * reason anybody chose. The total is what a reader downloads, and most of it is what
 * Next costs — recorded so a regression in one is never mistaken for the other.
 *
 * Counts what a modern browser actually fetches: the `noModule` bundle is excluded
 * because module-capable browsers never request it, and counting it inflates the figure
 * by ~39 KB of code nobody runs.
 */

import { gzipSync } from "node:zlib";
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

const OUT = path.join(import.meta.dirname, "..", "out");
const CONTENT_BUDGET = 160 * 1024;
const TOTAL_BUDGET = 520 * 1024;

refuseStaleOutput(OUT);

/**
 * Every page, not only the home. The budget is per page, and a page nobody grades is a
 * page that grows unnoticed: the actor and country pages are generated from data and
 * there can be a couple of hundred of them.
 */
const pages = [];
const walk = (dir) => {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== "_next") walk(full);
    else if (entry.name === "index.html") pages.push(full);
  }
};
walk(OUT);

let worst = null;
for (const page of pages) {
  const result = grade(page);
  if (!worst || result.content > worst.content) worst = { page, ...result };
}
console.log(`
  ${pages.length} pages graded; the heaviest is ${path.relative(OUT, worst.page) || "index.html"}
`);
report(worst);

function grade(file) {
const html = readFileSync(file, "utf-8");
const gz = (buf) => gzipSync(buf, { level: 9 }).length;
const read = (href) => readFileSync(path.join(OUT, href.replace(/^\//, "")));

/** Assets referenced with an absolute path, which basePath may have prefixed. */
const refs = (re) =>
  [...new Set([...html.matchAll(re)].map((m) => m[1]))].map((href) =>
    href.replace(/^.*?(\/_next\/)/, "$1"),
  );

const scripts = refs(/<script src="([^"]+)"(?![^>]*noModule)/g).concat(
  refs(/rel="preload" as="script"[^>]*href="([^"]+)"/g),
);
const styles = refs(/rel="stylesheet"[^>]*href="([^"]+)"/g);
const fonts = refs(/as="font"[^>]*href="([^"]+)"/g).concat(
  refs(/href="([^"]+\.woff2)"[^>]*as="font"/g),
);

const contentHtml = gz(Buffer.from(html.replace(/<script[\s\S]*?<\/script>/g, "")));
const css = styles.reduce((n, h) => n + gz(read(h)), 0);
const js = [...new Set(scripts)].reduce((n, h) => n + gz(read(h)), 0);
// woff2 is already compressed; gzipping it again would understate what is fetched.
const font = [...new Set(fonts)].reduce((n, h) => n + read(h).length, 0);
const payload = gz(Buffer.from(html)) - contentHtml;

const content = contentHtml + css;
const total = gz(Buffer.from(html)) + js + css + font;
return { contentHtml, css, payload, js, font, content, total };
}

function report({ contentHtml, css, payload, js, font, content, total }) {
const kb = (n) => `${(n / 1024).toFixed(1)} KB`;

console.log(`  page (HTML, scripts stripped)  ${kb(contentHtml).padStart(9)}`);
console.log(`  CSS                            ${kb(css).padStart(9)}`);
console.log(`  ---- content                   ${kb(content).padStart(9)}  budget ${kb(CONTENT_BUDGET)}`);
console.log(`  Next RSC payload               ${kb(payload).padStart(9)}`);
console.log(`  Next + React runtime           ${kb(js).padStart(9)}`);
console.log(`  webfonts                       ${kb(font).padStart(9)}`);
console.log(`  ==== total                     ${kb(total).padStart(9)}  budget ${kb(TOTAL_BUDGET)}`);

const over = [];
if (content > CONTENT_BUDGET)
  over.push(
    `content is ${kb(content)}, over its ${kb(CONTENT_BUDGET)} budget. Drop evidence ` +
      `tables from the narrowest rows first and announce the cap on the page — never ` +
      `truncate silently. See docs/adr/0002.`,
  );
if (total > TOTAL_BUDGET)
  over.push(
    `total is ${kb(total)}, over its ${kb(TOTAL_BUDGET)} budget. If the content half is ` +
      `within budget then the framework grew, which is a decision to revisit rather ` +
      `than a page to trim. See docs/adr/0002.`,
  );

if (over.length) {
  console.error("\nOver budget:\n");
  for (const line of over) console.error(`  - ${line}`);
  process.exit(1);
}
}
