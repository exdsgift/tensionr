#!/usr/bin/env bash
#
# Build the site from the working tree and serve it, so it can be looked at before it
# is deployed.
#
# There was no way to do this before #81. The homepage only ever existed as CI output,
# which is why the old README's `python -m http.server` served an empty directory. That
# made "check it before deploying" a thing you could intend but not actually do.
#
# This is deliberately NOT `next dev`. The dev server is the right tool while writing a
# component, and `npm run dev` in frontend/ is still there for that. This builds the
# static export and serves it as files, because that is what GitHub Pages does, and the
# gap between the two is where a page breaks after it looks fine locally.
#
# What it does not reproduce: the base path. Production serves from `/tensionr/` and a
# preview from `/tensionr/preview/<branch>/`, while this serves from `/`. That is
# deliberate — a local server at a prefix is friction for no gain, and the base path is
# exercised by assemble-site.sh, which is what actually publishes.
#
# Usage:
#   tools/serve-site.sh [port]        default 8123
#
# Data: uses the working tree's data/. That directory carries the reference tables
# (aliases, polities, coastline) but the pipeline's output — stories.json — is gitignored
# and lives on the `data` branch. Fetch it first if you want a page with stories on it:
#
#   git fetch origin data && git show origin/data:data/stories.json > data/stories.json

set -euo pipefail

PORT="${1:-8123}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/_site"

cd "$ROOT"

if [[ ! -d frontend/node_modules ]]; then
  echo "==> installing frontend dependencies"
  (cd frontend && npm ci --no-audit --no-fund)
fi

echo "==> building the static export"
(cd frontend && PAGES_BASE_PATH="" npm run build)

echo "==> assembling $OUT"
rm -rf "$OUT"
mkdir -p "$OUT"
# Same allow-list as .github/scripts/assemble-site.sh. Kept in step by hand: the two
# are short, and a shared file that both had to source would be a third thing to keep
# in step rather than a second.
for item in data robots.txt sitemap.xml ledger; do
  [[ -e "$item" ]] && rsync -a --exclude=".DS_Store" "$item" "$OUT/"
done
rsync -a frontend/out/ "$OUT/"

if [[ ! -f "$OUT/data/stories.json" ]]; then
  echo
  echo "    note: data/stories.json is not present, so the page has no run to describe."
  echo "    git fetch origin data && git show origin/data:data/stories.json > data/stories.json"
fi

echo
echo "==> serving $OUT at http://localhost:$PORT/  (ctrl-c to stop)"
exec python3 -m http.server "$PORT" --directory "$OUT"
