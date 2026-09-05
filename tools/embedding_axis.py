"""Is there a political direction inside a story, or only a dominant one?

    uv run --project backend python tools/embedding_axis.py

Run by hand. Shares the hosted-embedding cache with `embedding_divergence.py`, so a
headline already encoded costs nothing here.

THE QUESTION THIS ANSWERS, AND THE ONE IT DOES NOT

A principal component always exists. Take any set of vectors and the first one comes
back, explaining whatever it explains, with headlines at each end. It will look like
something. The question is never whether a direction appears; it is whether the
direction is the one you were looking for, and the only way to know is to look for a
direction you already know is there.

So this runs two things in a fixed order.

**The positive control: the Falklands.** Argentine and Spanish outlets, in one language,
covering islands whose *name* is the disagreement. If the first component separates the
Argentine outlets, the method can find a division that is genuinely present. If it
cannot find that one, nothing it says about a division we cannot check is worth
anything. The separation is scored against a permutation of the polity labels, and the
end-to-end check is blunter still: does one end say Malvinas and the other Falklands.

**The hypothesis: Saxony-Anhalt.** German outlets only, one country and one language, on
a domestic election. Whatever separates them cannot be nationality and cannot be
language, so if a left/right axis is anywhere in this corpus it is here. There is no
label to score against, which is the point: the extremes are printed and judged by eye.

Prediction on record before the run: on the Falklands, Argentine outlets at one end and
Spanish and Mexican at the other, with Malvinas and Falkland splitting cleanly. If the
ends instead separate long headlines from short ones, or news from explainers, the
component is measuring editorial format and the answer is no.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embedding_divergence import collapse, embed  # noqa: E402

# The two cells, chosen from the run for their outlet counts and named here so the
# selection is on record rather than picked after seeing the answer.
CASES = [
    {
        "name": "FALKLANDS  (positive control: a division we already know is there)",
        "match": "Falkland",
        # Scored: does the component separate these from the rest?
        "label": ["Argentina"],
        "restrict_language": None,
        "tokens": ("malvinas", "falkland"),
    },
    {
        "name": "SAXONY-ANHALT  (the hypothesis: one country, one language, a domestic vote)",
        "match": "Saxony-Anhalt",
        "label": None,
        "restrict_language": "GERMAN",
        "tokens": None,
    },
]

MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def principal_axis(vectors: np.ndarray) -> tuple[np.ndarray, float]:
    """The first principal component, and the share of variance it carries.

    Centred but not scaled: these are unit vectors already, and scaling dimensions of a
    sentence embedding independently would be inventing a geometry the model does not
    have.
    """
    centred = vectors - vectors.mean(axis=0, keepdims=True)
    _, singular, right = np.linalg.svd(centred, full_matrices=False)
    variance = singular**2
    return right[0], float(variance[0] / variance.sum())


def auc(scores: np.ndarray, flag: np.ndarray) -> float:
    """Probability that a flagged row sits further along the axis than an unflagged one.

    0.5 is no separation. Distance from 0.5 in either direction is separation, because
    the sign of a principal component is arbitrary.
    """
    pos, neg = scores[flag], scores[~flag]
    if not len(pos) or not len(neg):
        return float("nan")
    wins = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(wins / (len(pos) * len(neg)))


def run_case(case: dict, stories: list[dict], args) -> None:
    story = next(
        (s for s in stories if case["match"].lower() in s["headline"].lower()), None
    )
    if story is None:
        print(f"\n{case['name']}\n  no story matching {case['match']!r} in this run")
        return

    rows = [r for r in collapse(story["evidence"]) if r.get("polity")]
    if case["restrict_language"]:
        rows = [r for r in rows if r.get("language") == case["restrict_language"]]

    print(f"\n{'=' * 78}\n{case['name']}\n{'=' * 78}")
    print(f"  {story['headline'][:70]}")
    print(f"  {len(rows)} outlets after collapsing syndication")
    if len(rows) < 12:
        print("  too few to look for a direction in; skipped")
        return

    by_polity: dict[str, int] = {}
    for r in rows:
        by_polity[r["polity"]] = by_polity.get(r["polity"], 0) + 1
    top = sorted(by_polity.items(), key=lambda kv: -kv[1])[:6]
    print("  " + ", ".join(f"{p} {n}" for p, n in top))

    vectors = embed([r["title"] for r in rows], MODEL, args.cache)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9
    axis, share = principal_axis(vectors)
    scores = (vectors - vectors.mean(axis=0, keepdims=True)) @ axis
    print(f"\n  first component carries {share:.1%} of the variance")

    if case["label"]:
        flag = np.array([r["polity"] in case["label"] for r in rows])
        observed = auc(scores, flag)
        rng = np.random.default_rng(args.seed)
        null = []
        for _ in range(args.permutations):
            shuffled = rng.permutation(flag)
            null.append(abs(auc(scores, shuffled) - 0.5))
        beat = sum(1 for v in null if v >= abs(observed - 0.5))
        label = "/".join(case["label"])
        print(f"\n  does the axis separate {label} from the rest?")
        print(f"    AUC {observed:.3f}   (0.5 is no separation, either direction counts)")
        print(f"    shuffled |AUC-0.5|: mean {np.mean(null):.3f}, sd {np.std(null):.3f}")
        print(f"    p = {(beat + 1) / (len(null) + 1):.3f}")

    order = np.argsort(scores)
    print("\n  five at one end")
    for i in order[:5]:
        print(f"    [{rows[i]['polity'][:12]:<12}] {rows[i]['title'][:64]}")
    print("  five at the other")
    for i in order[-5:][::-1]:
        print(f"    [{rows[i]['polity'][:12]:<12}] {rows[i]['title'][:64]}")

    if case["tokens"]:
        a, b = case["tokens"]
        half = len(order) // 2
        low = {i: rows[i]["title"].lower() for i in order[:half]}
        high = {i: rows[i]["title"].lower() for i in order[half:]}
        print(f"\n  the words themselves, split at the median of the axis:")
        for token in (a, b):
            lo = sum(1 for t in low.values() if token in t)
            hi = sum(1 for t in high.values() if token in t)
            print(f"    {token:<12} {lo:>3} on one side, {hi:>3} on the other")
        print("    A component that found the disagreement should put these on")
        print("    opposite sides. Split evenly means it found something else.")

    # What a sceptic would check next: is the axis just headline length?
    lengths = np.array([len(r["title"]) for r in rows], dtype=float)
    rank = lambda v: np.argsort(np.argsort(v)).astype(float)  # noqa: E731
    rho = float(np.corrcoef(rank(lengths), rank(scores))[0, 1])
    print(f"\n  rank correlation with headline length: {rho:+.3f}")
    print("  Near zero is what you want. Strong either way means the component is")
    print("  mostly measuring how long a headline is.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--data", type=Path, default=Path("data/stories.json"))
    p.add_argument("--cache", type=Path, default=Path(".cache/embeddings"))
    p.add_argument("--permutations", type=int, default=2000)
    p.add_argument("--seed", type=int, default=20260905)
    args = p.parse_args()

    run = json.loads(args.data.read_text("utf-8"))
    stories = [s for s in run["stories"] if s.get("band") and s.get("evidence")]
    print(f"run {run['run']}, {len(stories)} banded stories")

    for case in CASES:
        run_case(case, stories, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
