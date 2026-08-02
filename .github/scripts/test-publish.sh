#!/usr/bin/env bash
#
# Tests for publish.sh, against a throwaway bare repo. It decides where irrecoverable
# data lands, so its guarantees are checked rather than assumed: the single-commit
# invariant, that two publishers on one ref do not erase each other, and that history
# refuses to rewrite.
#
set -uo pipefail

PUB="${PUB:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/publish.sh}"
LAB="$(mktemp -d "${TMPDIR:-/tmp}/publish-lab.XXXXXX")"
trap 'rm -rf "$LAB"' EXIT

git init -q --bare "$LAB/remote.git"
git init -q "$LAB/work"
cd "$LAB/work"
git config user.email test@example.com
git config user.name test
export REMOTE="$LAB/remote.git"

pass=0; fail=0
check() {  # check <label> <expected> <actual>
  if [[ "$2" == "$3" ]]; then
    echo "  ok   $1"; pass=$((pass + 1))
  else
    echo "  FAIL $1: expected '$2', got '$3'"; fail=$((fail + 1))
  fi
}
at() { git --git-dir="$LAB/remote.git" "$@"; }

mkdir -p data
echo '{"a":1}' > data/news.json
echo '{"b":2}' > data/status.json

echo "== state, first run =="
bash "$PUB" state data data/news.json data/status.json > /dev/null || echo "  FAIL exit $?"
check "files on branch" "data/news.json data/status.json" \
  "$(at ls-tree -r --name-only data | tr '\n' ' ' | sed 's/ $//')"
check "single commit" "1" "$(at rev-list --count data)"

echo "== a second run replaces content and keeps the ref at one commit =="
echo '{"a":99}' > data/news.json
bash "$PUB" state data data/news.json data/status.json > /dev/null || echo "  FAIL exit $?"
check "content replaced" '{"a":99}' "$(at show data:data/news.json)"
check "still a single commit" "1" "$(at rev-list --count data)"

echo "== a second publisher does not erase the first =="
# Two jobs write to this ref (#10). If state replaced the tree wholesale, whichever
# ran last would delete the other's output.
echo '{"s":1}' > data/stories.json
bash "$PUB" state data data/stories.json > /dev/null || echo "  FAIL exit $?"
check "both publishers present" "data/news.json data/status.json data/stories.json" \
  "$(at ls-tree -r --name-only data | tr '\n' ' ' | sed 's/ $//')"
check "one commit after both" "1" "$(at rev-list --count data)"

echo "== state is a no-op when nothing changed =="
out="$(bash "$PUB" state data data/stories.json)"
check "reports no-op" "1" "$(echo "$out" | grep -c 'nothing to push')"

echo "== a lost race is retried, not clobbered =="
# The real hazard: another publisher lands between this script's fetch and its push.
# A pre-receive hook reproduces it exactly — it moves the ref out from under the first
# attempt and rejects it, which is what the server does when the lease no longer holds.
# The retry must then rebuild on the new tip and keep the interloper's file.
echo '{"x":1}' > data/other.json
GIT_INDEX_FILE="$LAB/idx" git read-tree "$(at rev-parse data)"
blob="$(git hash-object -w data/other.json)"
GIT_INDEX_FILE="$LAB/idx" git update-index --add --cacheinfo "100644,$blob,data/other.json"
t="$(GIT_INDEX_FILE="$LAB/idx" git write-tree)"
interloper="$(git commit-tree "$t" -p "$(at rev-parse data)" -m interloper)"
git push -q "$REMOTE" "$interloper:refs/heads/interloper"   # so the object exists server-side

cat > "$LAB/remote.git/hooks/pre-receive" <<HOOK
#!/bin/sh
if [ ! -f "$LAB/raced" ]; then
  touch "$LAB/raced"
  # receive-pack quarantines object writes and forbids ref updates in the
  # hook; the interloper commit is already in the object db, so step out of it
  env -u GIT_QUARANTINE_PATH git update-ref refs/heads/data $interloper
  echo "another publisher got there first" >&2
  exit 1
fi
exit 0
HOOK
chmod +x "$LAB/remote.git/hooks/pre-receive"

echo '{"a":100}' > data/news.json
bash "$PUB" state data data/news.json > /dev/null 2>&1 || echo "  FAIL exit $?"
rm -f "$LAB/remote.git/hooks/pre-receive"
check "the race actually happened" "1" "$([[ -f "$LAB/raced" ]] && echo 1 || echo 0)"
check "interloper's file survived" '{"x":1}' "$(at show data:data/other.json)"
check "our write landed" '{"a":100}' "$(at show data:data/news.json)"
check "still a single commit" "1" "$(at rev-list --count data)"

echo "== history appends =="
echo '{"run":1}' > record.json
bash "$PUB" history history history/2026/08/02/1400 record.json > /dev/null || echo "  FAIL exit $?"
echo '{"run":2}' > record.json
bash "$PUB" history history history/2026/08/02/1415 record.json > /dev/null || echo "  FAIL exit $?"
check "both runs kept" \
  "history/2026/08/02/1400/record.json history/2026/08/02/1415/record.json" \
  "$(at ls-tree -r --name-only history | tr '\n' ' ' | sed 's/ $//')"
check "two commits" "2" "$(at rev-list --count history)"
check "earlier run intact" '{"run":1}' "$(at show history:history/2026/08/02/1400/record.json)"

echo "== history refuses to rewrite =="
echo '{"run":"tampered"}' > record.json
out="$(bash "$PUB" history history history/2026/08/02/1400 record.json 2>&1)"
check "refused" "1" "$(echo "$out" | grep -c 'append-only')"
check "original untouched" '{"run":1}' "$(at show history:history/2026/08/02/1400/record.json)"

echo "== IF_ABSENT turns a repeat offer into a no-op =="
# The v1 job offers yesterday's snapshot every run and only the first offer should
# stick; without this it would fail eleven times a day.
out="$(IF_ABSENT=1 bash "$PUB" history history history/2026/08/02/1400 record.json 2>&1)"
check "skipped, not failed" "1" "$(echo "$out" | grep -c 'left as it is')"
check "no new commit" "2" "$(at rev-list --count history)"
check "original untouched" '{"run":1}' "$(at show history:history/2026/08/02/1400/record.json)"
echo '{"run":3}' > record.json
IF_ABSENT=1 bash "$PUB" history history history/2026/08/02/1430 record.json > /dev/null \
  || echo "  FAIL exit $?"
check "a genuinely new path still lands" '{"run":3}' \
  "$(at show history:history/2026/08/02/1430/record.json)"

echo "== a missing file is an error, not a silent empty commit =="
out="$(bash "$PUB" state data data/news.json data/absent.json 2>&1)"
check "refused" "1" "$(echo "$out" | grep -c 'no such file')"

echo
echo "$pass passed, $fail failed"
[[ $fail -eq 0 ]]
