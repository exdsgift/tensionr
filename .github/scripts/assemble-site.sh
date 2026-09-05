#!/usr/bin/env bash
#
# Assemble the full GitHub Pages tree: production at the root, one preview per
# branch under preview/<branch>/.
#
# Why the whole tree, every time: actions/deploy-pages publishes a single
# artifact as the entire site root, so there is no such thing as publishing only
# a subdirectory. Every deployment therefore replaces the whole site, which means
# a preview deployment that carried only the preview would take production down.
# The way out is to make assembly stateless: the site is rebuilt from git refs on
# every run, so any deployment - production or preview - produces the same
# complete, correct tree. Nothing is carried over from a previous deployment and
# there is no state store to drift.
#
# Usage:
#   PREVIEW_BRANCHES=$'feat/a\nfix/b' .github/scripts/assemble-site.sh _site
#
# Environment:
#   PRODUCTION_BRANCH  branch published at the site root (default: master)
#   DATA_BRANCH        branch whose data/ overlays the site (default: data). The
#                      pipeline writes there instead of to the production ref, so
#                      production can be protected (#6, #10). Absent branch is not
#                      an error: the site then serves whatever data/ production
#                      carries, which is how this stays safe to deploy before the
#                      branch exists.
#   STAGING_BRANCH     branch published under staging/ (default: staging). A long-lived
#                      sandbox that can be pushed to and force-pushed directly, so work
#                      can be tried on the real data at a real URL without a pull
#                      request and without touching production. Absent branch is not an
#                      error - the site is then assembled without it.
#   PREVIEW_BRANCHES   newline-separated branch names (default: none)
#   REPO_REMOTE        git remote to clone (default: derived from
#                      GITHUB_SERVER_URL/GITHUB_REPOSITORY, else `origin`)
#   SITE_BASE_URL      only used for the human-readable preview index

set -euo pipefail

OUT_DIR="${1:-_site}"
PRODUCTION_BRANCH="${PRODUCTION_BRANCH:-master}"
DATA_BRANCH="${DATA_BRANCH:-data}"
STAGING_BRANCH="${STAGING_BRANCH:-staging}"
PREVIEW_BRANCHES="${PREVIEW_BRANCHES:-}"
SITE_BASE_URL="${SITE_BASE_URL:-}"

if [[ -z "${REPO_REMOTE:-}" ]]; then
  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    REPO_REMOTE="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}.git"
  else
    REPO_REMOTE="$(git remote get-url origin)"
  fi
fi

# What the published site is made of, as an allow-list.
#
# This used to be a deny-list — copy the whole tree, subtract the things that are not
# site. It failed the way deny-lists fail: when the v1 dashboard was retired to
# `v1.html` it was not added to the list, so eleven source files stayed publicly served
# and crawlable for a year (#80). The tree is now mostly *not* site — an engine, a
# frontend project, its node_modules — so naming the few things that are is both
# shorter and safe by default. Anything new is unpublished until someone says otherwise.
#
# `data/` is here *and* handled below. The reference tables a human edits - the alias
# table, the polity table, the coastline - live on the production ref, while the
# pipeline's output lives on the data branch and is overlaid on top by overlay_data().
# Copying it here is what makes an absent data branch a degradation rather than an
# error: the site then serves whatever data/ production carries.
SITE_FILES=(
  "data"
  "robots.txt"
  "sitemap.xml"
  "ledger"      # a redirect stub for the Ledger's old subpath
)

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

# Clone one branch at depth 1 into $WORK_DIR/<slot> and copy its *static* site files
# into $OUT_DIR/<subpath>. The page itself is not here — it is built from the same
# clone by build_frontend(). Returns non-zero if the branch does not exist.
copy_branch() {
  local branch="$1" slot="$2" subpath="$3"
  local src="$WORK_DIR/$slot"
  local dest="$OUT_DIR/${subpath}"

  if ! git clone --quiet --depth 1 --single-branch --branch "$branch" \
        "$REPO_REMOTE" "$src"; then
    echo "  ! could not clone branch '$branch' - skipped" >&2
    return 1
  fi

  mkdir -p "$dest"
  local item
  for item in "${SITE_FILES[@]}"; do
    [[ -e "$src/$item" ]] || continue
    rsync -a --exclude=".DS_Store" "$src/$item" "$dest/"
  done
  echo "  -> ${subpath:-<root>} (static files)"
}

# Reject anything that could escape the preview directory or confuse a web
# server. Branch names are attacker-influenced input on a public repository.
valid_branch_name() {
  local branch="$1"
  [[ "$branch" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]] || return 1
  [[ "$branch" != *".."* ]] || return 1
  [[ "$branch" != *"//"* ]] || return 1
  return 0
}

case "$OUT_DIR" in
  ""|"/"|"."|"..") echo "refusing to use '$OUT_DIR' as the output directory" >&2; exit 1 ;;
esac
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# The pipeline's output lives on its own ref so the production branch can be
# protected. Reference data - the alias table, the polity table, the coastline -
# stays on production because it is an input a human edits, not output that
# rewrites itself eleven times a day. Cloned once and overlaid onto every tree:
# a preview whose data/ were missing would render an empty page and read as a
# regression in the branch under review.
DATA_SRC=""
if git clone --quiet --depth 1 --single-branch --branch "$DATA_BRANCH" \
      "$REPO_REMOTE" "$WORK_DIR/databranch" 2>/dev/null; then
  if [[ -d "$WORK_DIR/databranch/data" ]]; then
    DATA_SRC="$WORK_DIR/databranch/data"
  else
    echo "! branch '$DATA_BRANCH' has no data/ directory - each tree keeps its own" >&2
  fi
else
  echo "branch '$DATA_BRANCH' not found - each tree serves the data/ it carries"
fi

# state.json is the engine's own cache — the previous window's URLs, 6.5 MB of them —
# and the next run reads it off the branch, not off the site. It is on the data ref
# because that is where regenerable state belongs, but publishing it would put the
# site's largest file in front of readers who have no use for it.
DATA_EXCLUDES=("--exclude=/state.json")

overlay_data() {
  local dest="$1"
  [[ -n "$DATA_SRC" ]] || return 0
  mkdir -p "$dest/data"
  rsync -a "${DATA_EXCLUDES[@]}" "$DATA_SRC/" "$dest/data/"
  echo "  -> data/ from '$DATA_BRANCH' ($(du -sh "$dest/data" | cut -f1))"
}

# The site's pages are built from each tree's *own* frontend, so a branch that changes
# the page previews its own version (#81, #82). This replaced a Python generator that
# needed nothing but an interpreter; a Next.js build needs node_modules, which is why
# this is the expensive part of an assembly and why the workflow caches npm.
#
# `basePath` is the reason the build happens per tree rather than once. It cannot be
# relative and Next inlines it into the client bundle, so the same artifact cannot be
# served from `/tensionr/` and from `/tensionr/preview/<branch>/`. See decision 3 on #79.
#
# The failure contract is inherited from the generator this replaces, and matters just
# as much: for production a failure must stop the deployment rather than publish a site
# with no homepage, so Pages keeps serving the last good build. A preview failing is
# reported and skipped, so one broken branch cannot hold up everyone else's.
build_frontend() {
  local src="$1" dest="$2" base_path="$3" required="$4"

  # A branch with no frontend at all. Two cases, and they are not the same thing.
  #
  # For a preview this is just a branch that predates #81: skip it.
  #
  # For production it is the transition itself. This script always rebuilds production
  # from the production ref, so while #81 is still open, every run - including the run
  # on #81's own pull request - assembles a master that has no frontend and no
  # checked-in index.html either, because the old homepage was generated. Failing there
  # would make #81's own checks unpassable until it merged, which is a check that can
  # only ever be red and tells nobody anything.
  #
  # So production gets a holding page instead, loudly. This is deliberately narrow: it
  # triggers only when frontend/ is absent *entirely*, never when a build fails, so a
  # broken frontend still stops the deployment. Once master carries a frontend this
  # branch is dead code, and it should be deleted when #82 lands.
  if [[ ! -f "$src/frontend/package.json" ]]; then
    if [[ "$required" != required ]]; then
      echo "  ! no frontend on this branch - preview skipped" >&2
      return 0
    fi
    echo "  ! the production branch has no frontend/ - this is the #81 transition." >&2
    echo "    Publishing a holding page so the site keeps answering." >&2
    cat > "$dest/index.html" <<'HOLDING'
<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>tensionr</title>
<style>
  :root { color-scheme: dark }
  body { font: 16px/1.6 ui-monospace, Menlo, monospace; max-width: 34rem;
         margin: 20vh auto; padding: 0 1.25rem; background: #0a0a0a; color: #e8e8e8 }
  a { color: #8ecaff }
</style>
<h1>tensionr</h1>
<p>The interface is being rebuilt. The engine still runs, and every window it
   measures is still published as data.</p>
<p>The measurements are in <a href="data/stories.json">data/stories.json</a>, which
   needs nothing from this page to be useful.</p>
HOLDING
    echo "  -> holding page written"
    return 0
  fi

  # The build reads the data it will be published beside, not the data the branch
  # happens to carry. overlay_data() has already put the data branch's files in $dest;
  # without this the build would see only the reference tables that live on the
  # production ref (aliases, polities, coastline) and no stories.json at all.
  if [[ -d "$dest/data" ]]; then
    mkdir -p "$src/data"
    rsync -a "$dest/data/" "$src/data/"
  fi

  local log="$WORK_DIR/build-$(echo "$base_path" | tr -c 'A-Za-z0-9' '-').log"
  if (
      cd "$src/frontend" &&
      npm ci --no-audit --no-fund &&
      PAGES_BASE_PATH="$base_path" npm run build
     ) > "$log" 2>&1; then
    rsync -a "$src/frontend/out/" "$dest/"
    echo "  -> built at base '${base_path:-/}' ($(du -sh "$dest" | cut -f1) total)"
    return 0
  fi

  echo "  ! the frontend build failed at base '${base_path:-/}':" >&2
  tail -30 "$log" | sed 's/^/     /' >&2
  if [[ "$required" == required ]]; then
    echo "  ! this is production - refusing to publish a site with no homepage." >&2
    echo "    The last good deployment stays live." >&2
    return 1
  fi
  echo "  ! preview skipped" >&2
  return 0
}

# The path component of the Pages URL, with no trailing slash: `/tensionr` for
# https://exdsgift.github.io/tensionr/. Empty when SITE_BASE_URL is unset, which is the
# local case - a local assembly serves from the filesystem root and wants no prefix.
site_base_path() {
  [[ -n "$SITE_BASE_URL" ]] || { printf ''; return; }
  local path="${SITE_BASE_URL#*://}"
  path="/${path#*/}"
  path="${path%/}"
  [[ "$path" == "/" ]] && path=""
  printf '%s' "$path"
}

BASE_PATH="$(site_base_path)"

echo "Assembling production from '$PRODUCTION_BRANCH':"
copy_branch "$PRODUCTION_BRANCH" "production" ""
overlay_data "$OUT_DIR"
build_frontend "$WORK_DIR/production" "$OUT_DIR" "$BASE_PATH" required

# Staging: the same tree as production, from a branch nobody has to protect. It is
# assembled after production and before the previews, and it is optional in the strong
# sense - a broken staging must never be able to hold up a production deployment, which
# is the whole point of having somewhere to break things.
staging_published=0
if [[ -n "$STAGING_BRANCH" && "$STAGING_BRANCH" != "$PRODUCTION_BRANCH" ]]; then
  echo "Assembling staging from '$STAGING_BRANCH':"
  if copy_branch "$STAGING_BRANCH" "staging" "staging"; then
    overlay_data "$OUT_DIR/staging"
    build_frontend "$WORK_DIR/staging" "$OUT_DIR/staging" "$BASE_PATH/staging" optional
    staging_published=1
  fi
fi

published=""
published_count=0
slot=0
while IFS= read -r branch; do
  branch="$(echo "$branch" | tr -d '[:space:]')"
  [[ -n "$branch" ]] || continue
  [[ "$branch" != "$PRODUCTION_BRANCH" ]] || continue

  if ! valid_branch_name "$branch"; then
    echo "  ! refusing unsafe branch name '$branch' - skipped" >&2
    continue
  fi

  slot=$((slot + 1))
  echo "Assembling preview for '$branch':"
  if copy_branch "$branch" "preview-$slot" "preview/$branch"; then
    overlay_data "$OUT_DIR/preview/$branch"
    build_frontend "$WORK_DIR/preview-$slot" "$OUT_DIR/preview/$branch" \
      "$BASE_PATH/preview/$branch" optional
    published="${published}${branch}"$'\n'
    published_count=$((published_count + 1))
  fi
done <<< "$PREVIEW_BRANCHES"

# Staging and previews are public URLs; keep them out of search results. robots.txt
# matching is longest-path-wins, so these beat the site-wide `Allow: /`.
#
# Written unconditionally rather than only when the tree exists: a rule for a path that
# is briefly absent costs nothing, while a missing rule during the window when staging
# is up and robots.txt has not caught up is how a sandbox gets indexed.
if [[ -f "$OUT_DIR/robots.txt" ]]; then
  printf '\n# Neither staging nor branch previews are production; neither may be indexed.\nDisallow: /staging/\nDisallow: /preview/\n' \
    >> "$OUT_DIR/robots.txt"
fi

# A human-readable index, so a preview URL can be found without digging through
# Actions logs - the point of previews is opening them on a phone.
if [[ "$published_count" -gt 0 ]]; then
  {
    echo '<!doctype html>'
    echo '<meta charset="utf-8">'
    echo '<meta name="robots" content="noindex">'
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">'
    echo '<title>tensionr - branch previews</title>'
    echo '<style>body{font:16px/1.6 ui-monospace,Menlo,monospace;max-width:44rem;margin:3rem auto;padding:0 1.25rem;background:#000;color:#e8e8e8}a{color:#8ecaff}li{margin:.4rem 0}</style>'
    echo '<h1>branch previews</h1>'
    echo "<p>Rebuilt from the open pull requests as of $(date -u '+%Y-%m-%d %H:%M UTC'). Not production.</p>"
    echo '<ul>'
    while IFS= read -r branch; do
      [[ -n "$branch" ]] || continue
      printf '<li><a href="%s/preview/%s/">%s</a></li>\n' \
        "${SITE_BASE_URL%/}" "$branch" "$branch"
    done <<< "$published"
    echo '</ul>'
    printf '<p><a href="%s/">production</a></p>\n' "${SITE_BASE_URL%/}"
  } > "$OUT_DIR/preview/index.html"
fi

echo
echo "Site assembled at '$OUT_DIR' ($(du -sh "$OUT_DIR" | cut -f1)), staging: $staging_published, previews: $published_count"

# Consumed by the workflow for the run summary.
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "staging_published=$staging_published" >> "$GITHUB_OUTPUT"
  echo "preview_count=$published_count" >> "$GITHUB_OUTPUT"
  {
    echo "preview_branches<<__EOF__"
    printf '%s' "$published"
    echo "__EOF__"
  } >> "$GITHUB_OUTPUT"
fi
