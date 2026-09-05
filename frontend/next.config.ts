import type { NextConfig } from "next";

/**
 * The site is a static export served by GitHub Pages from a path that is not the
 * domain root, and not even a *fixed* path: production sits at `/tensionr/` while
 * every open pull request gets a preview at `/tensionr/preview/<branch>/`.
 *
 * `basePath` cannot absorb that at deploy time. It rejects relative values outright
 * (`Specified basePath has to start with a /`) and is inlined into the client bundle,
 * and `next/link` emits absolute hrefs regardless of `assetPrefix`. So the base path is
 * a build input, and `.github/scripts/assemble-site.sh` runs one build per tree it
 * publishes. See decision 3 on #79.
 *
 * The default is empty rather than `/tensionr`, so a local `next dev` and a local
 * `npm run build` both serve from `/` without anyone having to remember a flag. CI is
 * the only place that sets it, and it always sets it explicitly.
 */
const basePath = process.env.PAGES_BASE_PATH ?? "";

if (basePath && (!basePath.startsWith("/") || basePath.endsWith("/"))) {
  throw new Error(
    `PAGES_BASE_PATH must start with "/" and must not end with one; got "${basePath}"`,
  );
}

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  // Directory-style URLs (`foo/index.html`) rather than `foo.html`. Both work on
  // Pages, but only this form survives being moved under a deeper prefix, which is
  // exactly what a preview deployment does.
  trailingSlash: true,
  // The optimiser needs a server. There is none, and the page ships no raster images
  // anyway - the map is text.
  images: { unoptimized: true },
};

export default nextConfig;
