"""Is the split along a line, or is it a coin?

`division` is the binary entropy of the naming rate. It is maximal at one half, which is
also what a fair coin produces, so it cannot tell a story whose sources divide *by
country* from one whose sources divide at random. Measured on this project's own
published run, that is not a theoretical worry: the story at the top of the ledger, at a
perfect division of 1.00, was indistinguishable from random assignment (p = 0.53), while
a story ranked below it at 0.76 was structured at p = 0.0005. The ranking was putting
noise first, systematically, because noise is exactly where entropy peaks.

This module answers the other question: **does knowing where a publisher is tell you
whether it used the name?**

WHAT IS REPORTED, AND WHAT IS DELIBERATELY NOT

Reported: whether the alignment with polity is distinguishable from chance, as a
permutation p-value, plus the per-polity table it rests on.

Not reported: how *much* of the split polity explains. Every association measure -
mutual information, Cramér's V, an intraclass correlation - is severely biased upward at
these sample sizes, and the bias depends on both N and the number of groups, which vary
per story. Measured here: the mean plug-in mutual information across published rows was
0.223 bits against 0.182 bits for the permutation null on the same table shapes, so
roughly four fifths of any headline figure would be an artefact of the table's shape.
The permutation test is exact at every N; a published effect size would not be.

THE NULL

The mark is shuffled across sources. That holds the polity sizes fixed and holds the
number of sources that named the actor fixed, and destroys only the correspondence
between them - which is the hypothesis. Shuffling anything else would test a different
question.

POWER, WHICH IS THE REAL LIMIT

Simulated on this corpus's own table shapes, at alpha 0.05:

    N=20, 6 polities, an 80/20 split   power 0.44
    N=50, 6 polities                   power 0.97
    N=50, 20 polities                  power 0.70
    N=100, 20 polities                 power 0.98

At a 65/35 split none of those reach 0.35. So a story that fails this test has not been
shown to be unstructured; it has failed to show that it is. `powered` records whether
the test could have detected a strong split at all, and the page has to say so rather
than print a bare "not significant".
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tensionr.stories.marks import PRESENT, UNRESOLVED

# Permutation rounds. The smallest p this can report is 1/(ROUNDS+1), and the reported
# value is floored at that rather than at zero: a permutation test never proves absence
# of chance, it only fails to find it within the rounds it ran.
ROUNDS = 2000

# Below this the test is reported but marked unpowered. Taken from the simulation above:
# fifty sources is where an 80/20 split becomes reliably detectable with a handful of
# polities.
POWERED_SOURCES = 50
POWERED_POLITIES = 4


def _mutual_information(polity: np.ndarray, mark: np.ndarray) -> float:
    """Mutual information between polity and the naming mark, in bits.

    Used only as the statistic the permutation ranks; it is never published, because at
    these sample sizes its value is mostly a property of the table's shape.
    """
    n = len(mark)
    if n == 0:
        return 0.0
    total = 0.0
    named = mark.sum()
    for share in (named / n, 1 - named / n):
        if share <= 0:
            return 0.0
    for group in np.unique(polity):
        rows = polity == group
        size = rows.sum()
        hits = mark[rows].sum()
        for count, marginal in ((hits, named), (size - hits, n - named)):
            if count == 0 or marginal == 0:
                continue
            total += (count / n) * math.log2(
                (count / n) / ((size / n) * (marginal / n))
            )
    return max(0.0, total)


def structure(
    rows: list[dict[str, Any]], actor: str, *, rounds: int = ROUNDS, seed: int = 0
) -> dict[str, Any] | None:
    """Whether this actor's naming split aligns with the polity of publication.

    `rows` are the story's evidence rows. A row joins the test only if it has a polity
    and a mark that is not `unresolved`: a row nobody can evaluate carries no evidence
    either way, and a row with no polity cannot speak to a question about polities.

    Returns None when the question cannot be asked - fewer than two polities, or no
    variation in the mark. Both are real outcomes rather than failures, and the caller
    publishes the absence rather than a number.
    """
    usable = [
        r
        for r in rows
        if r.get("polity") and r.get("marks", {}).get(actor, UNRESOLVED) != UNRESOLVED
    ]
    if len(usable) < 4:
        return None

    polity = np.array([r["polity"] for r in usable])
    mark = np.array(
        [1 if r["marks"][actor] == PRESENT else 0 for r in usable], dtype=np.int64
    )
    groups = len(np.unique(polity))
    named = int(mark.sum())

    # One polity cannot disagree with anything, and a unanimous story has no split to
    # be structured. Neither is a failure of the test.
    if groups < 2 or named == 0 or named == len(mark):
        return None

    observed = _mutual_information(polity, mark)
    rng = np.random.default_rng(seed)
    beaten = sum(
        1
        for _ in range(rounds)
        if _mutual_information(polity, rng.permutation(mark)) >= observed
    )
    # Yeh's bound: a permutation test cannot report zero, and reporting zero would claim
    # a certainty the rounds do not support.
    p = (beaten + 1) / (rounds + 1)

    return {
        "sources": len(usable),
        "polities": groups,
        "p": round(p, 4),
        "floor": round(1 / (rounds + 1), 4),
        "powered": len(usable) >= POWERED_SOURCES and groups >= POWERED_POLITIES,
        "by_polity": _table(usable, actor),
    }


def _table(rows: list[dict[str, Any]], actor: str) -> list[dict[str, Any]]:
    """Named over evaluable, per polity, most-naming first.

    This is the artefact a reader checks, and the reason the whole thing is worth doing:
    "outlets in East Asia named China, outlets in Europe did not" is a finding, while a
    p-value is a statistic. Every row here is countable against the evidence table.

    Polities with a single source are kept rather than pooled, and marked, because
    2/2 = 100% is noise wearing a percentage and the page has to be able to say which
    rows it is asking the reader not to lean on.
    """
    counts: dict[str, list[int]] = {}
    for row in rows:
        named, total = counts.setdefault(row["polity"], [0, 0])
        counts[row["polity"]] = [
            named + (1 if row["marks"][actor] == PRESENT else 0),
            total + 1,
        ]
    return sorted(
        (
            {
                "polity": polity,
                "named": named,
                "evaluable": total,
                # Below three sources a rate is not a rate. Published anyway, flagged,
                # because dropping the row would hide part of the sample.
                "thin": total < 3,
            }
            for polity, (named, total) in counts.items()
        ),
        key=lambda r: (-(r["named"] / r["evaluable"]), -r["evaluable"], r["polity"]),
    )
