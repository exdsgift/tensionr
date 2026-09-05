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

const OUT = path.join(import.meta.dirname, "..", "out");
const CONTENT_BUDGET = 120 * 1024;
const TOTAL_BUDGET = 340 * 1024;

const html = readFileSync(path.join(OUT, "index.html"), "utf-8");
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
