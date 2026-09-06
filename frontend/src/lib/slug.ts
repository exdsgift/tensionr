/**
 * A polity name as a path segment: "United Kingdom" -> "united-kingdom".
 *
 * On its own, with no imports, because it is used inside client components as well as
 * on the server. `stories.ts` reads files with `node:fs`, and an import of anything
 * from it inside a client boundary drags the filesystem into a browser chunk, which
 * Turbopack refuses to build. This module is the seam that keeps that from happening.
 *
 * Reversible only through the table that made it, so pages that take a slug look the
 * name up rather than reconstructing it.
 */
export function slug(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
