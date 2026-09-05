/**
 * The dark palette is written twice — once on `.dark`, once under
 * `prefers-color-scheme: dark` — because CSS cannot apply one declaration block from
 * both a class selector and a media query, and the page has to follow the operating
 * system with scripting off, which rules out a class-toggling script.
 *
 * Duplication that nothing checks is duplication that drifts. This fails the moment the
 * two blocks stop agreeing, which is the only reason the duplication is acceptable.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const CSS = readFileSync(
  path.join(import.meta.dirname, "globals.css"),
  "utf-8",
);

/** Every `--token: value` declaration in a block, normalised for comparison. */
function declarations(block: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [, name, value] of block.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    out[name] = value.trim();
  }
  return out;
}

function blockAfter(marker: string): string {
  const start = CSS.indexOf(marker);
  if (start === -1) throw new Error(`not found in globals.css: ${marker}`);
  const open = CSS.indexOf("{", start);
  let depth = 0;
  for (let i = open; i < CSS.length; i++) {
    if (CSS[i] === "{") depth++;
    else if (CSS[i] === "}" && --depth === 0) return CSS.slice(open + 1, i);
  }
  throw new Error(`unbalanced braces after ${marker}`);
}

describe("the dark palette", () => {
  it("is identical whether it comes from the class or from the OS preference", () => {
    const byClass = declarations(blockAfter("\n.dark {"));
    const byPreference = declarations(
      blockAfter("@media (prefers-color-scheme: dark) {\n  :root:not(.light)"),
    );
    expect(Object.keys(byClass).length).toBeGreaterThan(20);
    expect(byPreference).toEqual(byClass);
  });

  it("covers every colour the light palette defines", () => {
    // Colours only. `--radius` is geometry and is deliberately shared by both
    // palettes; requiring a dark value for it would be requiring noise.
    const colours = (block: Record<string, string>) =>
      Object.keys(block)
        .filter((k) => block[k].startsWith("oklch"))
        .sort();
    // A colour defined only in light silently keeps its light value in dark, which is
    // how a single unreadable element survives a review.
    expect(colours(declarations(blockAfter("\n.dark {")))).toEqual(
      colours(declarations(blockAfter("\n:root {"))),
    );
  });
});

describe("the dark variant", () => {
  it("fires for the class and for the OS preference", () => {
    // The shadcn components carry `dark:` utilities. Without the media-query arm they
    // would stay light on a dark page, and nothing would look obviously broken —
    // just a handful of elements at the wrong contrast.
    const variant = blockAfter("@custom-variant dark");
    expect(variant).toContain(".dark *");
    expect(variant).toContain("prefers-color-scheme: dark");
  });
});

describe("the reader's own settings", () => {
  it("never has a font-size imposed on the body", () => {
    // ADR 0001 §3. A `font-size` here overrides the browser's text-size setting.
    const body = /\bbody\s*\{[^}]*\}/.exec(CSS)?.[0] ?? "";
    expect(body).not.toContain("font-size");
  });

  it("disables the map's pulse under prefers-reduced-motion", () => {
    // ADR 0001 §6.
    expect(CSS).toContain("@media (prefers-reduced-motion: reduce)");
  });
});
