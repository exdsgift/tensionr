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
#   PREVIEW_BRANCHES   newline-separated branch names (default: none)
#   REPO_REMOTE        git remote to clone (default: derived from
#                      GITHUB_SERVER_URL/GITHUB_REPOSITORY, else `origin`)
#   SITE_BASE_URL      only used for the human-readable preview index

set -euo pipefail

OUT_DIR="${1:-_site}"
PRODUCTION_BRANCH="${PRODUCTION_BRANCH:-master}"
DATA_BRANCH="${DATA_BRANCH:-data}"
PREVIEW_BRANCHES="${PREVIEW_BRANCHES:-}"
SITE_BASE_URL="${SITE_BASE_URL:-}"

if [[ -z "${REPO_REMOTE:-}" ]]; then
  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    REPO_REMOTE="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}.git"
  else
    REPO_REMOTE="$(git remote get-url origin)"
  fi
fi

# Paths that are in the repository but are not part of the published site.
# The legacy Jekyll build served the repository root verbatim, so the Python
# package, the lockfile and a stray server.log are all publicly served today;
# a workflow build is the moment to stop shipping them.
EXCLUDES=(
  "--exclude=/.git/"
  "--exclude=/.github/"
  "--exclude=/.gitignore"
  "--exclude=/src/"
  "--exclude=/tests/"
  "--exclude=/docs/"
  "--exclude=/pyproject.toml"
  "--exclude=/uv.lock"
  "--exclude=/CLAUDE.md"
  "--exclude=/server.log"
  "--exclude=__pycache__/"
  "--exclude=.venv/"
  "--exclude=.DS_Store"
)

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

# Clone one branch at depth 1 into $WORK_DIR/<slot> and copy its site files into
# $OUT_DIR/<subpath>. Returns non-zero if the branch does not exist.
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
  rsync -a "${EXCLUDES[@]}" "$src/" "$dest/"
  local size
  size="$(du -sh "$dest" | cut -f1)"
  echo "  -> ${subpath:-<root>} ($size)"
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

overlay_data() {
  local dest="$1"
  [[ -n "$DATA_SRC" ]] || return 0
  mkdir -p "$dest/data"
  rsync -a "$DATA_SRC/" "$dest/data/"
  echo "  -> data/ from '$DATA_BRANCH' ($(du -sh "$dest/data" | cut -f1))"
}

echo "Assembling production from '$PRODUCTION_BRANCH':"
copy_branch "$PRODUCTION_BRANCH" "production" ""
overlay_data "$OUT_DIR"

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
    published="${published}${branch}"$'\n'
    published_count=$((published_count + 1))
  fi
done <<< "$PREVIEW_BRANCHES"

# Previews are public URLs; keep them out of search results. robots.txt matching
# is longest-path-wins, so this beats the site-wide `Allow: /`.
if [[ -f "$OUT_DIR/robots.txt" ]]; then
  printf '\n# Branch previews are not production and must not be indexed.\nDisallow: /preview/\n' \
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
echo "Site assembled at '$OUT_DIR' ($(du -sh "$OUT_DIR" | cut -f1)), previews: $published_count"

# Consumed by the workflow for the run summary.
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "preview_count=$published_count" >> "$GITHUB_OUTPUT"
  {
    echo "preview_branches<<__EOF__"
    printf '%s' "$published"
    echo "__EOF__"
  } >> "$GITHUB_OUTPUT"
fi
