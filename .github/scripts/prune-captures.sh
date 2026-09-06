#!/usr/bin/env bash
#
# Keep the capture archive to a rolling window, and actually reclaim the space.
#
#   prune-captures.sh                 # report what would go, change nothing
#   prune-captures.sh --apply         # rewrite the ref
#
# Environment:
#   HISTORY_BRANCH   ref to prune (default: history)
#   WINDOW_DAYS      days of captures to keep (default: 20)
#   REMOTE           git remote (default: origin)
#
# WHY THIS IS A SEPARATE SCRIPT AND NOT PART OF publish.sh
#
# publish.sh's `history` mode refuses to overwrite an existing path, on the stated
# grounds that this is the one store time cannot rebuild. That guarantee is worth
# keeping for `index.json` and `record.json`, which are small and which the site's
# time series reads. So the engine goes on appending and never deletes anything, and
# the one operation that destroys data lives here, runs once a day, does nothing else,
# and can be asked what it would do before it does it.
#
# WHY A PARENTLESS COMMIT
#
# Removing a file from a branch does not reclaim anything: the blob stays reachable
# from every earlier commit, so the tree shrinks and the repository does not. The only
# way to reclaim is for the ref to stop pointing at those commits, which means
# replacing the ref rather than extending it. The dropped objects then become
# unreachable and GitHub collects them on its own schedule, which is not something this
# script can force.
#
# So this is destructive and irreversible by design, which is why --apply is opt-in and
# why the default is a report.
#
# WHAT IS KEPT AND WHAT IS NOT
#
#   capture.json   windowed. ~8 MB per run, read by nothing automatic, and the reason
#                  the ref reached 2.9 GB in a month.
#   index.json     kept for ever. 280 KB per run, and it is what a story's published
#                  line over time is drawn from - windowing it would cap the project's
#                  own baseline to save 1.6% of the space.
#   record.json    kept for ever. 95 KB per run.
#   anything else  kept. This script only ever removes paths ending in capture.json.

set -euo pipefail

REMOTE="${REMOTE:-origin}"
HISTORY_BRANCH="${HISTORY_BRANCH:-history}"
WINDOW_DAYS="${WINDOW_DAYS:-20}"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

die() { echo "prune: $*" >&2; exit 1; }
[[ "$WINDOW_DAYS" =~ ^[0-9]+$ && "$WINDOW_DAYS" -ge 1 ]] || die "WINDOW_DAYS must be a positive integer, got '$WINDOW_DAYS'"

git fetch --quiet --no-tags "$REMOTE" "$HISTORY_BRANCH" \
  || die "cannot fetch '$HISTORY_BRANCH' from '$REMOTE'"
tip="$(git rev-parse FETCH_HEAD)"

# The window is measured from the newest capture on the ref, not from today. A ref that
# has not been written for a week must not lose a week the moment this runs; if the
# engine has stopped, that is a different problem and this script is not the place to
# discover it.
newest="$(git ls-tree -r --name-only "$tip" \
  | grep '/capture\.json$' \
  | sed -E 's#history/([0-9]{4})/([0-9]{2})/([0-9]{2})/.*#\1-\2-\3#' \
  | sort -u | tail -1)"
if [[ -z "$newest" ]]; then
  echo "prune: no captures on '$HISTORY_BRANCH' - nothing to do"
  exit 0
fi

# Date arithmetic through python3 rather than `date -d`, which is GNU-only: the CI
# runner has it and macOS does not, and the dry run is meant to be looked at locally
# before anyone passes --apply.
cutoff="$(python3 -c "
import datetime as dt, sys
d = dt.date.fromisoformat(sys.argv[1])
print(d - dt.timedelta(days=int(sys.argv[2]) - 1))
" "$newest" "$WINDOW_DAYS")"
echo "prune: newest capture $newest, window $WINDOW_DAYS days, keeping from $cutoff"

# A read loop rather than `mapfile`, which needs bash 4: the runner has bash 5 and
# macOS still ships 3.2, and this script is meant to be dry-run on a laptop first.
doomed=()
while IFS= read -r path; do
  [ -n "$path" ] && doomed+=("$path")
done < <(
  git ls-tree -r --name-only "$tip" \
    | grep '/capture\.json$' \
    | awk -F/ -v cut="$cutoff" '{ if ($2"-"$3"-"$4 < cut) print }' \
    | sort
)

if [[ ${#doomed[@]} -eq 0 ]]; then
  echo "prune: every capture is inside the window - nothing to remove"
  exit 0
fi

bytes=0
for path in "${doomed[@]}"; do
  size="$(git cat-file -s "$(git rev-parse "$tip:$path")")"
  bytes=$((bytes + size))
done
printf 'prune: %d captures to remove, %.0f MB\n' "${#doomed[@]}" "$(echo "$bytes / 1048576" | bc -l)"
printf '  oldest %s\n  newest %s\n' "${doomed[0]}" "${doomed[$((${#doomed[@]} - 1))]}"

kept="$(git ls-tree -r --name-only "$tip" | grep -c '/capture\.json$' || true)"
printf '  %d captures would remain\n' "$((kept - ${#doomed[@]}))"

if [[ "$APPLY" -ne 1 ]]; then
  echo "prune: dry run, nothing changed. Pass --apply to rewrite the ref."
  exit 0
fi

: "${GIT_AUTHOR_NAME:=github-actions[bot]}"
: "${GIT_AUTHOR_EMAIL:=41898282+github-actions[bot]@users.noreply.github.com}"
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

export GIT_INDEX_FILE
GIT_INDEX_FILE="$(mktemp -u "${TMPDIR:-/tmp}/prune-index.XXXXXX")"
trap 'rm -f "$GIT_INDEX_FILE"' EXIT

git read-tree "$tip"
for path in "${doomed[@]}"; do
  git update-index --force-remove "$path"
done
tree="$(git write-tree)"
[[ -n "$tree" ]] || die "write-tree produced nothing - refusing to push"

# A tree identical to the tip means the removals did nothing, which would mean the path
# list and the ref disagree. Pushing then would replace a healthy ref with a copy of
# itself and throw away its history for no reason at all.
[[ "$tree" != "$(git rev-parse "$tip^{tree}")" ]] || die "tree unchanged after removals - refusing to push"

message="prune captures older than $cutoff (${WINDOW_DAYS}-day window)

Removed ${#doomed[@]} capture files. index.json and record.json are untouched.
Parentless on purpose: removing a path from a child commit shrinks the tree and
reclaims nothing, because the blobs stay reachable from the parents."
commit="$(git commit-tree "$tree" -m "$message")" || die "commit-tree failed"

# The lease is what makes a race safe: if a run published between the fetch above and
# this push, the push fails and the next scheduled prune picks up the new tip. Losing a
# prune costs a day of space; losing a run's index costs data.
git push --force-with-lease="refs/heads/$HISTORY_BRANCH:$tip" \
  --quiet "$REMOTE" "$commit:refs/heads/$HISTORY_BRANCH" \
  || die "push rejected - the ref moved since the fetch. Re-run; nothing was changed."

echo "prune: '$HISTORY_BRANCH' -> $(git rev-parse --short "$commit")"
echo "prune: the dropped objects are now unreachable. GitHub collects them on its own"
echo "       schedule, so the repository's size falls later rather than immediately."
