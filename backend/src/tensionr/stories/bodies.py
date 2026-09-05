"""Reconstruct article bodies from GDELT's Web News NGrams, for chosen URLs only.

The algorithm is the one Collodon & Vestrelli describe and release as `gdeltnews`
(https://doi.org/10.3390/bdcc10020045): each n-gram record carries a keyword-in-context
window, and an article is rebuilt by merging those windows on their longest token overlap,
constrained by the decile position each records. Validated by its authors at 0.75
similarity to the original unfiltered and 0.96 at high token overlap.

**Why this is reimplemented rather than imported.** The package's only public entry point
filters by URL *substring*: `url_filters` is checked with a containment test against every
record. Measured, on one real minute-file (22.7 MB, ~1M records, 1,680 distinct URLs) with
the 263 URLs the sampling rule selects, it did not finish in **ten minutes** — 263
substring tests per record is a quarter of a billion string operations per file, and a
12-hour selection needs tens of files inside a 2400 s budget that clustering already
spends eight minutes of.

We know the exact URLs we want, so membership in a set answers in constant time and the
expensive assembly runs on 263 articles instead of 1,680. Nothing here is stored: #70
decided the reconstruction is transient, so callers read it and let it go.
"""

import gzip
import json
import logging
import re
import urllib.error
import urllib.request
from collections.abc import Iterable

logger = logging.getLogger(__name__)

NGRAM_URL = "http://data.gdeltproject.org/gdeltv3/webngrams/{stamp}.webngrams.json.gz"

# An article's n-grams sit in the file for the minute GDELT processed it, but only for
# about three quarters of them: measured, 2,171 of 2,861 articles in a docembed heartbeat
# at 06:31 appear in the 06:31 n-gram file, 76%. The rest are a minute either side, so
# each wanted minute is fetched with its neighbours.
NEIGHBOURS = (0, -1, 1)

# The artifact the paper documents: the end of an article is sometimes glued to the
# beginning inside `pre`, separated by a slash, which makes the overlap walk follow a
# false transition. Only applied near the start of an article, where it does damage.
_ARTIFACT_POS = 20


def minutes_for(stamps: Iterable[str]) -> list[str]:
    """The n-gram file stamps to fetch for a set of `seen_at` values, with neighbours.

    Sorted and deduplicated, because a story's sources cluster on GDELT's quarter-hour
    heartbeat: measured, the sources of one story span 9 to 16 distinct minutes, and the
    same minutes serve every story in a selection — so the union for five stories is tens
    of files rather than the 720 a 12-hour window contains.
    """
    wanted: set[str] = set()
    for stamp in stamps:
        digits = re.sub(r"\D", "", str(stamp))[:12]
        if len(digits) != 12:
            continue
        minute = int(digits[10:12])
        for offset in NEIGHBOURS:
            shifted = minute + offset
            if 0 <= shifted <= 59:
                wanted.add(f"{digits[:10]}{shifted:02d}00")
    return sorted(wanted)


def fragments(payload: bytes, urls: set[str]) -> dict[str, list[tuple[int, str]]]:
    """Keyword-in-context fragments per wanted URL, from one n-gram file.

    Membership in a set rather than a substring scan — that is the whole reason this
    exists. Each fragment is `pre + ngram + post` with whitespace collapsed, carrying the
    decile position so the assembly can refuse implausible orderings.
    """
    found: dict[str, list[tuple[int, str]]] = {}
    for line in gzip.decompress(payload).decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = record.get("url")
        if url not in urls:
            continue
        text = " ".join(
            f"{record.get('pre', '')} {record.get('ngram', '')} {record.get('post', '')}".split()
        )
        if not text:
            continue
        try:
            position = int(record.get("pos", 0))
        except (TypeError, ValueError):
            position = 0
        if position < _ARTIFACT_POS and "/" in text:
            text = text.split("/", 1)[1].strip() or text
        found.setdefault(url, []).append((position, text))
    return found


def _overlap(left: list[str], right: list[str]) -> int:
    """Longest suffix of `left` that is a prefix of `right`."""
    for size in range(min(len(left), len(right)), 0, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def assemble(pieces: list[tuple[int, str]]) -> str:
    """Merge overlapping fragments into one token sequence.

    Maximum-overlap assembly with a position constraint: a fragment may be appended only
    if its decile is not earlier than the furthest already included, and prepended only if
    it is not later than the earliest — `pos` is too coarse to order fragments but sharp
    enough to refuse an end-of-article fragment landing before a beginning. Ties break on
    position then length so the same input always gives the same output.
    """
    if not pieces:
        return ""
    ordered = sorted(pieces, key=lambda p: (p[0], -len(p[1])))
    text = ordered[0][1].split()
    low = high = ordered[0][0]
    remaining = ordered[1:]

    while remaining:
        best = None
        for index, (position, fragment) in enumerate(remaining):
            tokens = fragment.split()
            if position >= high:
                score = _overlap(text, tokens)
                if score and (best is None or score > best[0]):
                    best = (score, index, tokens, "append")
            if position <= low:
                score = _overlap(tokens, text)
                if score and (best is None or score > best[0]):
                    best = (score, index, tokens, "prepend")
        if best is None:
            break
        score, index, tokens, where = best
        position, _ = remaining.pop(index)
        if where == "append":
            text = text + tokens[score:]
            high = max(high, position)
        else:
            text = tokens[:-score] + text
            low = min(low, position)
    return " ".join(text)


def fetch(stamp: str, *, timeout: int = 90) -> bytes | None:
    """One n-gram file, or None. A missing minute is ordinary, not an error."""
    try:
        with urllib.request.urlopen(
            NGRAM_URL.format(stamp=stamp), timeout=timeout
        ) as r:
            return r.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        logger.info("no n-grams for %s: %s", stamp, error)
        return None


def bodies(
    urls: Iterable[str], stamps: Iterable[str], *, limit: int | None = None
) -> dict[str, str]:
    """Reconstructed text for the wanted URLs, keyed by URL.

    Streams each file and drops it: nothing is written to disk and nothing is kept beyond
    the call, because #70 decided the reconstruction is transient and a public repository
    archiving it would be republishing the articles.
    """
    wanted = {u for u in urls if u}
    collected: dict[str, list[tuple[int, str]]] = {}
    files = minutes_for(stamps)
    if limit is not None:
        files = files[:limit]
    for stamp in files:
        payload = fetch(stamp)
        if payload is None:
            continue
        for url, pieces in fragments(payload, wanted).items():
            collected.setdefault(url, []).extend(pieces)
        del payload

    text = {url: assemble(pieces) for url, pieces in collected.items()}
    logger.info(
        "bodies: %d of %d urls reconstructed from %d minute files, median %d characters",
        len(text),
        len(wanted),
        len(files),
        sorted(len(v) for v in text.values())[len(text) // 2] if text else 0,
    )
    return text
