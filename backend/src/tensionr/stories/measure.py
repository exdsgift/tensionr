"""Per-(story, actor) figures: three-state presence, floors, division and its twin."""

import logging
import math
import re
from collections.abc import Callable
from typing import Any

from tensionr.config import BAND_TOLERANCE, MIN_EVALUABLE, MIN_POLITIES
from tensionr.stories.marks import ABSENT, PRESENT, UNRESOLVED

logger = logging.getLogger(__name__)

# Re-exported: the three states live in `marks` so that rendering a page needs no
# dependency, and every module that already reads them from here keeps working.
__all__ = ["ABSENT", "PRESENT", "UNRESOLVED"]

# (title, actor, language) -> one of the three states. The language is not optional:
# a row whose language nobody mapped is unmeasurable, not absent (#49).
Resolver = Callable[[str, str, str | None], str]


def _normalise(title: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", title.lower(), flags=re.UNICODE).split())


def collapse_syndication(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """One row per publisher, dropping reprints that share a headline word for word.

    Between a fifth and a third of clustered articles are wire copy. Six local papers
    carrying one agency line are one voice, and counting six would make disagreement
    look smaller than it is. Returns the kept rows and how many were collapsed, since
    the difference is published rather than absorbed.
    """
    kept: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    seen_domains: set[str] = set()
    for row in rows:
        title = _normalise(row.get("title", ""))
        if title in seen_titles or row["domain"] in seen_domains:
            continue
        seen_titles.add(title)
        seen_domains.add(row["domain"])
        kept.append(row)
    return kept, len(rows) - len(kept)


def division(named: int, evaluable: int) -> float:
    """Binary entropy of the naming rate: highest when the sources are split evenly.

    Ordering by division is what is computable at launch. Ordering by *notable*
    omission needs a per-actor baseline and arrives with one (#12).
    """
    if evaluable <= 0:
        return 0.0
    p = named / evaluable
    if p in (0.0, 1.0):
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def _balanced_rate(marks: list[tuple[str, str]]) -> float | None:
    """Naming rate with every language weighted equally, not every source.

    The published figure is a pooled rate, so a story carried by forty English
    outlets and two Arabic ones reports mostly what English did. The balanced twin
    is published beside it so a reader can see how much of the figure is language
    composition rather than disagreement (#23).
    """
    by_language: dict[str, list[str]] = {}
    for language, state in marks:
        if state == UNRESOLVED:
            continue
        by_language.setdefault(language, []).append(state)
    rates = [
        sum(1 for s in group if s == PRESENT) / len(group)
        for group in by_language.values()
        if group
    ]
    return sum(rates) / len(rates) if rates else None


def measure_story(
    rows: list[dict[str, Any]],
    actors: list[str],
    resolve: Resolver,
    *,
    min_evaluable: int = MIN_EVALUABLE,
    min_polities: int = MIN_POLITIES,
) -> dict[str, Any]:
    """Figures for one story: one row per actor, with the floors applied.

    `rows` carry `domain`, `language`, `polity` and `title`. `resolve` answers, for
    one title and one actor, whether the actor is present, absent, or undecidable in
    that script — three states, never two.
    """
    kept, collapsed = collapse_syndication(rows)
    polities = {r["polity"] for r in kept if r.get("polity")}
    below_quorum = len(polities) < min_polities

    figures = []
    for actor in actors:
        marks = [
            (
                r.get("language", "unknown"),
                resolve(r.get("title", ""), actor, r.get("language")),
            )
            for r in kept
        ]
        evaluable = [m for _, m in marks if m != UNRESOLVED]
        named = sum(1 for m in evaluable if m == PRESENT)
        unresolved = len(marks) - len(evaluable)

        # M varies by actor within one story: alias coverage differs by script, and
        # excluding the undecidable is the only option that neither manufactures an
        # omission nor asserts a presence.
        measurable = len(evaluable) >= min_evaluable and not below_quorum
        figures.append(
            {
                "actor": actor,
                "named": named,
                "evaluable": len(evaluable),
                "unresolved": unresolved,
                "division": round(division(named, len(evaluable)), 4)
                if measurable
                else None,
                "balanced_rate": (
                    round(b, 4)
                    if measurable and (b := _balanced_rate(marks)) is not None
                    else None
                ),
                "measurable": measurable,
            }
        )

    return {
        "sources": len(kept),
        "collapsed": collapsed,
        "polities": sorted(polities),
        "below_quorum": below_quorum,
        "figures": figures,
    }


def evidence(
    rows: list[dict[str, Any]], actors: list[str], resolve: Resolver
) -> list[dict[str, Any]]:
    """One row per surviving publisher, with its mark for each actor asked about.

    The figures say a story is divided; this says who said what, which is the only
    form in which a reader can check the claim rather than take it. Emitted only for
    the stories that publish a band, because the whole point is evidence for a figure
    that is on the page — and 286 stories' worth of rows would be a corpus dump.

    Ordered by polity, then language, then publisher, with the polities the table
    could not place last: the axis the project measures on is polity of publication,
    so grouping by it makes agreement and disagreement legible in the order rows
    appear. Unplaced sources are not hidden — they are counted, and #21 established
    that most of what is unplaceable is not journalism.
    """
    kept, _ = collapse_syndication(rows)
    marked = [
        {
            # The URL is what lets a reader check the row rather than take it. It was
            # already here — it is the key story identity is joined on between runs
            # (#10) — and it was being dropped at exactly the point where the evidence
            # is published, which left the sources unlinkable (#61).
            "url": r.get("url"),
            "domain": r["domain"],
            "polity": r.get("polity"),
            "language": r.get("language", "unknown"),
            "title": r.get("title", ""),
            "marks": {
                a: resolve(r.get("title", ""), a, r.get("language")) for a in actors
            },
        }
        for r in kept
    ]
    return sorted(
        marked,
        key=lambda r: (
            r["polity"] is None,
            r["polity"] or "",
            r["language"],
            r["domain"],
        ),
    )


def top_band(
    figures: list[dict[str, Any]], *, tolerance: float = BAND_TOLERANCE
) -> list[dict[str, Any]]:
    """The rows that lead, without asserting an order among them.

    #23 measured that the single top row is never stable: several sit within 0.005 of
    each other while the language artefact moves a figure by as much again. A band is
    the claim the data supports; a ranking is not.
    """
    scored = [
        f for f in figures if f.get("measurable") and f.get("division") is not None
    ]
    # Zero division means every source agreed - all named the actor or none did.
    # That is not a lead, and a band of zeros would report "nothing happened" as the
    # headline. The tolerance doubles as the resolution: a row within it of zero is
    # not measurably divided.
    scored = [f for f in scored if f["division"] > tolerance]
    if not scored:
        return []
    best = max(f["division"] for f in scored)
    band = [f for f in scored if best - f["division"] <= tolerance]
    return sorted(band, key=lambda f: f["actor"])
