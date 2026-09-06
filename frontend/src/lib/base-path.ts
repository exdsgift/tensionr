/**
 * A site-root path with the deployment's base path in front of it.
 *
 * `next/link` prefixes `basePath` on its own, but a plain `<a href>` does not, and the
 * bar and footer point at files under `data/` that are not routes. Written relative,
 * those links resolved against the page they sat on, so from `/actor/putin/` the feed
 * became `/actor/putin/data/feed.xml`: a 404 on every one of the 212 generated pages,
 * and correct only on the home, which is where it was tested.
 *
 * Same environment variable `next.config.ts` reads, read at build time, empty locally.
 */
const base = process.env.PAGES_BASE_PATH ?? "";

export function withBase(path: string): string {
  return `${base}/${path.replace(/^\/+/, "")}`;
}
