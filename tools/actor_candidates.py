"""Propose actors from the corpus itself, for a human to verify.

Run by hand against captures from the `history` ref:

    uv run --project backend python tools/actor_candidates.py /tmp/cap_*.json

WHY THE VOCABULARY NEEDS A SOURCE OTHER THAN MEMORY

The shipped table is fourteen actors, and they arrived by accumulation: whatever the
story of the week happened to need. That is a keyhole, and worse, it is a keyhole
nobody chose the position of. Measured on one real run, the corpus was naming Putin
across 239 domains and 12 languages, Kushner across 127 and Witkoff across 97, and the
engine could not see any of them.

WHAT COUNTS AS A CANDIDATE, AND WHY EACH TEST IS THERE

  capitalised, not sentence-initial   Marks a name in Latin, Cyrillic and Greek script,
                                      which is 76% of this corpus. Arabic and Chinese
                                      carry no case, so nothing here can propose an
                                      actor that appears only in them. That is a real
                                      hole and it is stated rather than papered over.

  across several languages            A name the world is using crosses languages; a
                                      local one does not. This is the test that
                                      separates an actor from a domestic story.

  across several domains              Otherwise one prolific publisher writes the
                                      vocabulary.

  capitalised most of the time        Measured per token across the whole corpus.
                                      Without it the list fills with words that are
                                      also names: `la` came out at 0.11, `un` at 0.05,
                                      `el niño` at 0.16, `open` at 0.64.

WHAT THIS DELIBERATELY DOES NOT DO

It does not write seeds.json. Wikidata search is unreliable at exactly the job it looks
suited for: probing twelve real candidates, `kremlin` resolved to Harvard University and
`ferrari`, `gasly` and `witkoff` resolved to the surname rather than the person. That is
the same failure #22 recorded, where 34 of 65 hand-written ids were wrong and every one
failed silently. So this proposes, with the label, the description and the Wikidata type
beside each row, and a person decides.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from tensionr.stories import wikidata as W

# Languages where a capital marks a name rather than every noun. German is absent on
# purpose: it capitalises all nouns, so it would contribute noise to every row.
CASED = {
    "ENGLISH",
    "SPANISH",
    "ITALIAN",
    "TURKISH",
    "GREEK",
    "RUSSIAN",
    "FRENCH",
    "PORTUGUESE",
    "VIETNAMESE",
    "DUTCH",
    "POLISH",
    "ROMANIAN",
    "INDONESIAN",
    "SWEDISH",
    "CZECH",
    "CATALAN",
    "SERBIAN",
    "UKRAINIAN",
    "BULGARIAN",
    "CROATIAN",
}

MIN_LANGUAGES = 4
MIN_DOMAINS = 10
MIN_CAPITALISED = 0.80

TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)

# Wikidata types this project measures. Stated here so the scope is a decision on the
# record rather than a taste applied row by row. A type cannot tell Monza the circuit
# from Kyiv the capital, which is why the output is a proposal and not a table.
KEEP_TYPES = {
    "sovereign state",
    "country",
    "landlocked country",
    "island country",
    "city",
    "largest city",
    "city or town",
    "capital",
    "capital city",
    "human",
    "political party",
    "political organization",
    "international organization",
    "intergovernmental organization",
    "armed organization",
    "militant group",
    "terrorist organization",
    "state",
    "autonomous community",
    "territory",
    "disputed territory",
    "strait",
    "region",
    "geographic region",
}


def candidates(captures: list[Path]) -> list[dict]:
    langs: dict[str, set[str]] = defaultdict(set)
    doms: dict[str, set[str]] = defaultdict(set)
    upper: dict[str, int] = defaultdict(int)
    lower: dict[str, int] = defaultdict(int)
    seen = 0

    for path in captures:
        for article in json.loads(path.read_text("utf-8")).get("articles", []):
            if article.get("language") not in CASED:
                continue
            words = TOKEN.findall(article.get("title", ""))
            if len(words) < 3:
                continue
            seen += 1
            for position, word in enumerate(words):
                key = word.lower()
                if position and word[:1].isupper() and not word.isupper():
                    upper[key] += 1
                elif word.islower():
                    lower[key] += 1
            run: list[str] = []
            for position, word in enumerate(words):
                if position and word[:1].isupper() and not word.isupper():
                    run.append(word)
                    continue
                if run:
                    _file(" ".join(run).lower(), article, langs, doms)
                run = []
            if run:
                _file(" ".join(run).lower(), article, langs, doms)

    rows = []
    for term, seen_langs in langs.items():
        if len(seen_langs) < MIN_LANGUAGES or len(doms[term]) < MIN_DOMAINS:
            continue
        parts = term.split()
        up = sum(upper[p] for p in parts)
        down = sum(lower[p] for p in parts)
        share = up / max(up + down, 1)
        if share < MIN_CAPITALISED:
            continue
        rows.append(
            {
                "term": term,
                "languages": len(seen_langs),
                "domains": len(doms[term]),
                "capitalised": round(share, 3),
            }
        )
    rows.sort(key=lambda r: (-r["domains"], -r["languages"]))
    print(f"read {seen:,} titles from {len(captures)} captures", file=sys.stderr)
    return rows


def _file(term: str, article: dict, langs: dict, doms: dict) -> None:
    langs[term].add(article["language"])
    doms[term].add(article["domain"])


# How many candidates are looked up. Each is one search plus a share of two batched
# entity fetches, and the list is already sorted by how much of the corpus carries the
# term, so the tail is where the noise lives rather than the actors.
ANNOTATE = 150


def annotate(rows: list[dict]) -> list[dict]:
    """Attach Wikidata's best guess, its description and its type, for verification."""
    rows = rows[:ANNOTATE]
    for row in rows:
        hits = W.search(row["term"], limit=1)
        if not hits:
            row.update(qid=None, label=None, description=None, types=[])
            continue
        hit = hits[0]
        row.update(qid=hit["qid"], label=hit["label"], description=hit["description"])
    qids = [r["qid"] for r in rows if r.get("qid")]
    entities = W.entities(qids)
    type_ids = {
        claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
        for qid in qids
        for claim in entities.get(qid, {}).get("claims", {}).get("P31", [])
    }
    names = W.entities(sorted(t for t in type_ids if t))
    for row in rows:
        if not row.get("qid"):
            continue
        row["types"] = [
            names.get(
                claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
                .get("id"),
                {},
            )
            .get("labels", {})
            .get("en", {})
            .get("value")
            for claim in entities.get(row["qid"], {}).get("claims", {}).get("P31", [])
        ]
        row["types"] = [t for t in row["types"] if t]
        row["in_scope"] = any(t in KEEP_TYPES for t in row["types"])
    return rows


def main() -> int:
    captures = [Path(a) for a in sys.argv[1:]]
    if not captures:
        print(__doc__, file=sys.stderr)
        return 2
    rows = annotate(candidates(captures))
    known = set(json.loads(Path("data/actors/seeds.json").read_text("utf-8"))["actors"])
    for row in rows:
        row["already"] = row["term"] in known
    Path("/tmp/actor-candidates.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), "utf-8"
    )
    scope = [r for r in rows if r.get("in_scope") and not r["already"]]
    print(f"{len(rows)} candidates, {len(scope)} in scope and not already known\n")
    print(f"  {'dom':>5}{'lang':>5}{'cap':>6}  {'qid':<10}{'label':<26}type")
    for r in scope:
        print(
            f"  {r['domains']:>5}{r['languages']:>5}{r['capitalised']:>6.2f}  "
            f"{r['qid'] or '-':<10}{(r['label'] or '')[:24]:<26}{(r['types'] or ['?'])[0]}"
        )
    print("\nwritten to /tmp/actor-candidates.json, with the rows this filtered out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
