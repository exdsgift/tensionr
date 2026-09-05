"""Does the distance between headlines carry political division, or only language?

Run by hand, never by the pipeline:

    uv run --project backend python tools/embedding_divergence.py --data data/stories.json

The headlines are encoded by a model *hosted* at Hugging Face, over HTTP, exactly the way
the engine already reads GDELT: nothing is downloaded, nothing runs locally, and the
engine's three runtime dependencies are untouched. A local sentence-transformers install
was tried first and is not worth the trouble - it pulls torch, which then has to agree
with numpy about ABI versions, and on this machine it did not.

Needs `HF_TOKEN` in `.env`. That secret has existed in this repository since 2026-05-05
and was wired to nothing; it works.

WHAT THIS TESTS, AND WHY IT IS NOT THE THING THAT WAS ALREADY REFUTED

Issue #8 measured semantic spread over GDELT's own `gsg_docembed` vectors, grouped by
language, and it ranked the wrong way round: multilingual wire-identical wildfire
coverage first at 0.2654, the visibly divergent Trump/Iran story fourteenth at 0.1401,
and a story carried by Russian *and* Ukrainian outlets nineteenth at 0.0700. Two
structural reasons were recorded. Both are addressed here, and neither is dodged.

  1. Those vectors are Universal Sentence Encoder v4 applied to GDELT's *machine
     translation into English*. Framing is the first thing a translation flattens:
     "neutralised" and "killed" collapse into one English word before any vector exists.
     So this script ignores GDELT's vectors and re-encodes the `title` field, which is
     the publisher's own headline in its own language.

  2. Grouping by language made language and polity indistinguishable, so the measure
     could not tell "these outlets disagree" from "these outlets are Croatian and
     Turkish". So the comparison here is *within a language*: same story, same language,
     different polity, against same story, same language, same polity. The language term
     is measured separately rather than removed, because removing it has been tried in
     this project and it destroyed the cross-lingual signal (mean-centering took
     cross-lingual recall from 0.84 to 0.07, and a per-language calibration explained
     1.2% of variance with offsets that did not replicate between windows, r = +0.11).

This is the design `docs/research/language-residual.md` used successfully on the actor
channel, where it found +0.086 for crossing polity with language held constant and only
+0.037 for crossing language on top, indistinguishable from zero.

WHAT WOULD COUNT AS A RESULT

Not a large number. An *order*. The previous attempt failed by ranking noise first, so
the test is whether the ranking matches an expectation written down in advance. The
prediction on record before this was run: most divergent Falklands, Israel/Hezbollah,
Trump/Iran; least divergent Pachuca, Williams, Musk taxi.

A permutation test guards the rest. Polity labels are shuffled *within* (story,
language), so the shuffle destroys the political structure while leaving language,
story and sample sizes exactly as they were. If the real gap is not bigger than the
shuffled gap, there is nothing here.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

# The hosted inference endpoint, same host and same shape the engine already talks to.
EMBED_URL = "https://router.huggingface.co/hf-inference/models/{model}/pipeline/feature-extraction"

# Titles per request. Small enough that one rejected batch costs little and large enough
# that 1,400 headlines take tens of requests rather than hundreds.
BATCH = 32

# The two encoders. Both are run because a finding that appears under one and not the
# other is a property of the model, not of the world, and this project has been wrong
# in that direction before.
#
# LaBSE is deliberately absent: cross-lingual STS 73.5 against 83.7 for XLM-R/SBERT. It
# wins at finding translations and loses at judging similarity, and judging similarity is
# the whole job here. The multilingual-e5 family is absent for a different measured
# reason: it compresses pairwise similarity into 0.76-0.92, leaving too little range to
# separate anything.
MODELS = [
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]

# Enough pairs in both cells for a story's own figure to mean anything. Below this the
# story still contributes to the pooled figure but gets no line of its own.
MIN_PAIRS = 30


def normalise(title: str) -> str:
    """A headline reduced to what syndication detection compares.

    The same normalisation the engine uses to collapse reprints: two outlets carrying
    one agency line word for word are one voice, and counting them twice would make the
    story look more agreed-upon than it is. On the live run this is not a rounding
    error - one story showed 152 sources against 718 collapsed rows.
    """
    text = unicodedata.normalize("NFKC", title).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


def collapse(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per verbatim headline and one per domain, first seen wins."""
    seen_title: set[str] = set()
    seen_domain: set[str] = set()
    kept = []
    for row in rows:
        key = normalise(row["title"])
        if key in seen_title or row["domain"] in seen_domain:
            continue
        seen_title.add(key)
        seen_domain.add(row["domain"])
        kept.append(row)
    return kept


def load(path: Path) -> list[dict[str, Any]]:
    """Banded stories, with their evidence reduced to what this measure can use.

    A row needs a polity and a language or it cannot enter either side of the
    comparison. Dropping it is not a silent filter: the count is reported.
    """
    run = json.loads(path.read_text("utf-8"))
    stories = []
    for story in run["stories"]:
        if not (story.get("band") and story.get("evidence")):
            continue
        rows = collapse(story["evidence"])
        usable = [r for r in rows if r.get("polity") and r.get("language")]
        stories.append(
            {
                "id": story["id"],
                "headline": story["headline"],
                "rows": usable,
                "collapsed_from": len(story["evidence"]),
                "dropped_unplaced": len(rows) - len(usable),
            }
        )
    return stories


def pair_cells(
    rows: list[dict[str, Any]], vectors: np.ndarray
) -> dict[str, np.ndarray]:
    """Cosine distances split into the three cells the design compares.

    Vectors are L2-normalised, so 1 - dot is the cosine distance.
    """
    n = len(rows)
    if n < 2:
        return {
            k: np.empty(0, np.float32) for k in ("same_pol", "diff_pol", "diff_lang")
        }
    sims = vectors @ vectors.T
    iu = np.triu_indices(n, k=1)
    dist = (1.0 - sims[iu]).astype(np.float32)

    lang = np.array([r["language"] for r in rows])
    pol = np.array([r["polity"] for r in rows])
    same_lang = lang[iu[0]] == lang[iu[1]]
    same_pol = pol[iu[0]] == pol[iu[1]]

    return {
        "same_pol": dist[same_lang & same_pol],
        "diff_pol": dist[same_lang & ~same_pol],
        "diff_lang": dist[~same_lang],
    }


def gap(cells: dict[str, np.ndarray]) -> float | None:
    """How much further apart two polities are than two outlets in one polity.

    Positive means the political boundary costs something over and above whatever a
    language and a story already cost. Zero means the boundary is invisible here.
    """
    a, b = cells["diff_pol"], cells["same_pol"]
    if len(a) < 2 or len(b) < 2:
        return None
    return float(a.mean() - b.mean())


def permuted_gaps(
    rows: list[dict[str, Any]],
    vectors: np.ndarray,
    rounds: int,
    rng: np.random.Generator,
) -> list[float]:
    """The same gap with polity shuffled inside each (story, language) block.

    Shuffling within language is what makes this a test of *political* structure. A
    global shuffle would also destroy the language composition and would therefore be
    beaten by any measure that responds to language at all, which is exactly the mistake
    that made the earlier permutation z-scores untrustworthy.
    """
    by_lang: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        by_lang[row["language"]].append(i)

    out = []
    for _ in range(rounds):
        shuffled = [dict(r) for r in rows]
        for idx in by_lang.values():
            labels = [rows[i]["polity"] for i in idx]
            rng.shuffle(labels)
            for i, label in zip(idx, labels, strict=True):
                shuffled[i]["polity"] = label
        g = gap(pair_cells(shuffled, vectors))
        if g is not None:
            out.append(g)
    return out


def bootstrap_ci(
    values: np.ndarray, rounds: int, rng: np.random.Generator
) -> tuple[float, float]:
    if len(values) < 2:
        return (float("nan"), float("nan"))
    draws = rng.integers(0, len(values), size=(rounds, len(values)))
    means = values[draws].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def embed(titles: list[str], model: str, cache_dir: Path) -> np.ndarray:
    """Vectors for these headlines, from the hosted model, cached on disk.

    The cache is keyed by (model, headline) rather than by position, so re-running
    against a different window only pays for the headlines it has not seen. Without it
    every run of this script would re-encode 1,400 titles for no reason, and a rate
    limit halfway through would lose the lot.
    """
    import hashlib

    from tensionr.config import HF_TOKEN
    from tensionr.http_client import request_with_retry

    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = model.replace("/", "_")
    path = cache_dir / f"{slug}.json"
    cache: dict[str, list[float]] = (
        json.loads(path.read_text("utf-8")) if path.exists() else {}
    )

    def key(title: str) -> str:
        return hashlib.sha256(title.encode("utf-8")).hexdigest()[:20]

    missing = [t for t in dict.fromkeys(titles) if key(t) not in cache]
    if missing:
        if not HF_TOKEN:
            raise SystemExit("HF_TOKEN is not set; put it in .env")
        print(
            f"  encoding {len(missing):,} headlines ({len(titles) - len(missing):,} cached)"
        )
        url = EMBED_URL.format(model=model)
        for start in range(0, len(missing), BATCH):
            batch = missing[start : start + BATCH]
            response = request_with_retry(
                "POST",
                url,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": batch},
                timeout=120,
            )
            if response is None or response.status_code != 200:
                code = "no response" if response is None else response.status_code
                raise SystemExit(f"  embedding request failed ({code}) at item {start}")
            for title, vector in zip(batch, response.json(), strict=True):
                cache[key(title)] = vector
            print(
                f"    {min(start + BATCH, len(missing)):>5,}/{len(missing):,}", end="\r"
            )
        print()
        path.write_text(json.dumps(cache), "utf-8")

    return np.asarray([cache[key(t)] for t in titles], dtype=np.float32)


def run_model(name: str, stories: list[dict], args) -> dict[str, Any]:
    print(f"\n{'=' * 78}\n{name}\n{'=' * 78}")
    rng = np.random.default_rng(args.seed)

    titles = [r["title"] for s in stories for r in s["rows"]]
    print(f"{len(titles):,} headlines, each in the language its publisher wrote it in")
    matrix = embed(titles, name, args.cache)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9

    at = 0
    per_story = []
    pooled: dict[str, list[np.ndarray]] = defaultdict(list)
    for story in stories:
        n = len(story["rows"])
        vectors = matrix[at : at + n]
        at += n
        cells = pair_cells(story["rows"], vectors)
        for key, values in cells.items():
            pooled[key].append(values)
        g = gap(cells)
        # The naive figure the earlier attempt reported: every pair, no controls. Kept
        # so the two rankings can be compared directly rather than described.
        every = np.concatenate([cells[k] for k in cells]) if n > 1 else np.empty(0)
        per_story.append(
            {
                "id": story["id"],
                "headline": story["headline"],
                "n": n,
                "same_pol": len(cells["same_pol"]),
                "diff_pol": len(cells["diff_pol"]),
                "gap": g,
                "naive": float(every.mean()) if len(every) else None,
            }
        )

    cells_all = {k: np.concatenate(v) if v else np.empty(0) for k, v in pooled.items()}
    result = {"model": name, "per_story": per_story}

    print("\nPOOLED, over every banded story")
    for key, label in [
        ("same_pol", "same language, same polity      (the null)"),
        ("diff_pol", "same language, different polity (the signal)"),
        ("diff_lang", "different language              (for scale)"),
    ]:
        v = cells_all[key]
        lo, hi = bootstrap_ci(v, args.bootstrap, rng)
        print(f"  {label}  n={len(v):>7,}  mean={v.mean():.4f}  [{lo:.4f}, {hi:.4f}]")
        result[key] = {"n": len(v), "mean": float(v.mean()), "ci": [lo, hi]}

    observed = float(cells_all["diff_pol"].mean() - cells_all["same_pol"].mean())
    lang_gap = float(cells_all["diff_lang"].mean() - cells_all["same_pol"].mean())
    print(f"\n  polity gap   {observed:+.4f}")
    print(f"  language gap {lang_gap:+.4f}   <- how much bigger the language effect is")
    result["polity_gap"] = observed
    result["language_gap"] = lang_gap

    # The observed statistic has to be computed the same way the null is, or the test
    # compares a pooled mean against a mean of per-story means. Those differ whenever
    # story sizes differ, which they do by a factor of twenty here, and comparing them
    # manufactures a result. This is the defect that made the earlier attempt's
    # permutation z-scores untrustworthy, and it was reproduced here before being caught.
    per_story_gaps = [s["gap"] for s in per_story if s["gap"] is not None]
    observed_by_story = float(np.mean(per_story_gaps))
    print(
        f"\n  pooled over pairs      {observed:+.4f}   <- dominated by the largest stories"
    )
    print(
        f"  mean of story gaps     {observed_by_story:+.4f}   <- every story weighted equally"
    )
    result["polity_gap_by_story"] = observed_by_story

    print(
        f"\nPERMUTATION, polity shuffled within (story, language), {args.permutations} rounds"
    )
    print("  (compared against the mean of story gaps, which is what it estimates)")
    at = 0
    per_round: list[list[float]] = [[] for _ in range(args.permutations)]
    for story in stories:
        n = len(story["rows"])
        vectors = matrix[at : at + n]
        at += n
        if n < 3:
            continue
        gaps = permuted_gaps(story["rows"], vectors, args.permutations, rng)
        for i, g in enumerate(gaps):
            per_round[i].append(g)
    null = [float(np.mean(r)) for r in per_round if r]
    if null:
        beat = sum(1 for g in null if g >= observed_by_story)
        print(f"  shuffled gap: mean={np.mean(null):+.4f}  sd={np.std(null):.4f}")
        print(
            f"  rounds at least as extreme as observed: {beat}/{len(null)}  (p = {(beat + 1) / (len(null) + 1):.3f})"
        )
        print(
            f"  the shuffled gap is {np.mean(null):+.4f}, not zero: with polity assigned at"
        )
        print(
            "  random the measure still reports a gap, which is the upward small-sample"
        )
        print(
            "  bias this project has been warned about three times. Read the observed"
        )
        print("  figure against this, never against zero.")
        result["permutation"] = {
            "mean": float(np.mean(null)),
            "sd": float(np.std(null)),
            "p": (beat + 1) / (len(null) + 1),
        }

    print("\nPER STORY, ranked by the language-controlled polity gap")
    print(f"  {'gap':>8}  {'naive':>7}  {'n':>4}  {'pairs':>12}  headline")
    ranked = [
        s
        for s in per_story
        if s["gap"] is not None and min(s["same_pol"], s["diff_pol"]) >= MIN_PAIRS
    ]
    for s in sorted(ranked, key=lambda x: -x["gap"]):
        pairs = f"{s['same_pol']}/{s['diff_pol']}"
        print(
            f"  {s['gap']:>+8.4f}  {s['naive']:>7.4f}  {s['n']:>4}  {pairs:>12}  {s['headline'][:46]}"
        )
    dropped = len(per_story) - len(ranked)
    if dropped:
        print(
            f"  ({dropped} stories omitted: fewer than {MIN_PAIRS} pairs in one of the two cells)"
        )

    if len(ranked) >= 4:
        sizes = np.array([s["n"] for s in ranked], dtype=float)
        gaps = np.array([s["gap"] for s in ranked], dtype=float)

        # Spearman, computed by hand rather than pulling scipy in for one number.
        def rank(v):
            return np.argsort(np.argsort(v)).astype(float)

        rs, rg = rank(sizes), rank(gaps)
        rho = float(np.corrcoef(rs, rg)[0, 1])
        print(
            f"\n  SIZE BIAS: rank correlation between story size and gap = {rho:+.3f}"
        )
        print("  Strongly negative means the measure is mostly reporting that small")
        print("  stories look divergent, which is a property of the estimator and not")
        print("  of the world.")
        result["size_rank_correlation"] = rho

    print("\n  the same stories ranked the naive way, for comparison")
    for s in sorted(ranked, key=lambda x: -x["naive"])[:6]:
        print(
            f"  {s['naive']:>8.4f}            {s['n']:>4}                {s['headline'][:46]}"
        )

    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--data", type=Path, default=Path("data/stories.json"))
    p.add_argument("--out", type=Path, default=None, help="write results as JSON")
    p.add_argument("--permutations", type=int, default=200)
    p.add_argument("--bootstrap", type=int, default=2000)
    p.add_argument("--seed", type=int, default=20260905)
    p.add_argument("--models", nargs="*", default=MODELS)
    p.add_argument("--cache", type=Path, default=Path(".cache/embeddings"))
    args = p.parse_args()

    stories = load(args.data)
    rows = sum(len(s["rows"]) for s in stories)
    raw = sum(s["collapsed_from"] for s in stories)
    unplaced = sum(s["dropped_unplaced"] for s in stories)
    print(f"{len(stories)} banded stories")
    print(
        f"  {raw:,} evidence rows -> {rows + unplaced:,} after collapsing syndication"
    )
    print(f"  {unplaced:,} dropped for having no polity, {rows:,} usable")

    results = [run_model(name, stories, args) for name in args.models]

    if args.out:
        args.out.write_text(json.dumps(results, indent=1, ensure_ascii=False), "utf-8")
        print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
