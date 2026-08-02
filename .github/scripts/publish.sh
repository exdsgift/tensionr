#!/usr/bin/env bash
#
# Publish pipeline output to a data ref, without touching the production ref.
#
#   publish.sh state   <branch> <path>...
#   publish.sh history <branch> <prefix> <path>...
#
# Two modes, because #10 decided current state and accumulated history have opposite
# rules and must not share a store:
#
#   state    The given files are written onto the branch and the whole thing is
#            re-pushed as a single parentless commit. The ref therefore keeps no
#            history — current state is regenerable, so losing it costs one cycle.
#            Files the run did not write are carried over rather than dropped, because
#            more than one job publishes to this ref and they must not erase each
#            other; a file that should disappear has to be removed deliberately.
#
#   history  Each file is added under <prefix> and the branch is extended. Existing
#            paths are never overwritten: the mode refuses rather than rewrite, because
#            this is the one store time cannot rebuild. Set IF_ABSENT=1 to skip a path
#            that is already there instead of failing — for a caller that offers the
#            same file every run and only needs the first offer to stick.
#
# Neither mode can lose a concurrent run's work: history must fast-forward, and state
# pushes with --force-with-lease. Either way a race makes the loser rebuild on the new
# tip and try again, rather than clobber.
#
# Commits are built with plumbing against a temporary index, so the caller's working
# tree and branch are untouched — the job stays checked out on the code it is running.
#
set -euo pipefail

REMOTE="${REMOTE:-origin}"
RETRIES="${RETRIES:-5}"

die() { echo "publish: $*" >&2; exit 1; }

mode="${1:-}"; shift || die "usage: publish.sh state|history <branch> ..."
branch="${1:-}"; shift || die "missing branch"
[[ -n "$branch" ]] || die "missing branch"

prefix=""
case "$mode" in
  state)   [[ $# -gt 0 ]] || die "state: no files given" ;;
  history) prefix="${1:-}"; shift || die "history: missing prefix"
           [[ -n "$prefix" && $# -gt 0 ]] || die "history: need a prefix and files" ;;
  *)       die "unknown mode '$mode' (expected state or history)" ;;
esac

export GIT_INDEX_FILE
GIT_INDEX_FILE="$(mktemp -u "${TMPDIR:-/tmp}/publish-index.XXXXXX")"
trap 'rm -f "$GIT_INDEX_FILE"' EXIT

: "${GIT_AUTHOR_NAME:=github-actions[bot]}"
: "${GIT_AUTHOR_EMAIL:=41898282+github-actions[bot]@users.noreply.github.com}"
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

for path in "$@"; do
  [[ -f "$path" ]] || die "no such file: $path"
done

fetch_base() {
  # The branch may not exist yet: a first run, or someone deleted it.
  if git fetch --quiet --no-tags --depth=1 "$REMOTE" "$branch" 2>/dev/null; then
    base="$(git rev-parse FETCH_HEAD)"
  else
    base=""
  fi
}

build_tree() {
  if [[ -n "$base" ]]; then git read-tree "$base"; else git read-tree --empty; fi
  local path dest blob
  for path in "$@"; do
    if [[ "$mode" == history ]]; then
      dest="$prefix/$(basename "$path")"
      if [[ -n "$base" ]] && git cat-file -e "$base:$dest" 2>/dev/null; then
        if [[ "${IF_ABSENT:-}" == 1 ]]; then
          echo "publish: $dest is already on '$branch' — left as it is"
          continue
        fi
        die "$dest is already on '$branch' — history is append-only, never rewritten"
      fi
    else
      dest="$path"
    fi
    blob="$(git hash-object -w -- "$path")"
    git update-index --add --cacheinfo "100644,$blob,$dest"
  done
  tree="$(git write-tree)"
}

push() {
  local commit lease=()
  if [[ "$mode" == state ]]; then
    # Parentless: the ref is replaced, not extended. The lease turns a lost race into
    # a failure this script can retry, instead of a silent overwrite.
    commit="$(git commit-tree "$tree" -m "$message")" || return 1
    lease=(--force-with-lease="refs/heads/$branch${base:+:$base}")
  elif [[ -n "$base" ]]; then
    commit="$(git commit-tree "$tree" -p "$base" -m "$message")" || return 1
  else
    commit="$(git commit-tree "$tree" -m "$message")" || return 1
  fi
  # An empty source ref is a *deletion*, so a failed commit-tree must never reach push.
  [[ -n "$commit" ]] || die "commit-tree produced nothing — refusing to push an empty ref"
  git push "${lease[@]+"${lease[@]}"}" --quiet "$REMOTE" "$commit:refs/heads/$branch" || return 1
  echo "publish: '$branch' -> $(git rev-parse --short "$commit")"
}

if [[ "$mode" == state ]]; then
  message="Current state at $(date -u +'%Y-%m-%dT%H:%MZ')

Regenerated each run; this ref keeps no history by design (#10)."
else
  message="Record for $prefix

One directory per run, never rewritten (#10)."
fi

fetch_base
build_tree "$@"

if [[ -n "$base" && "$tree" == "$(git rev-parse "$base^{tree}")" ]]; then
  echo "publish: '$branch' already matches this output — nothing to push"
  exit 0
fi

attempt=1
until push; do
  (( attempt++ < RETRIES )) || die "could not push '$branch' after $RETRIES attempts"
  echo "publish: '$branch' moved under us — rebuilding on the new tip (attempt $attempt)"
  fetch_base
  build_tree "$@"
done
