"""Carry story identity across runs by URL overlap, recording merges and splits."""

import hashlib
import logging
from typing import Any

from tensionr.config import IDENTITY_CONTAINMENT

logger = logging.getLogger(__name__)


def _seeded(seed: str) -> str:
    return "s-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def story_id(urls: list[str], taken: set[str] | None = None) -> str:
    """A stable id seeded from one of the story's article URLs.

    Assigned once at creation and carried in state afterwards, so it survives the
    seeding article leaving the window. Deterministic, and traceable back to a real
    article rather than to a counter nobody can check.

    `taken` matters when a story splits: the half holding the earliest article would
    otherwise re-derive the id the whole story already had, and two stories would
    share one identity. Seeding walks forward until it finds an id nobody holds.
    """
    taken = taken or set()
    for url in sorted(urls):
        candidate = _seeded(url)
        if candidate not in taken:
            return candidate
    return _seeded("|".join(sorted(urls)))


def _containment(a: set[str], b: set[str]) -> float:
    """Overlap as a fraction of the smaller set.

    Jaccard is wrong here: a story that doubles between runs shares every earlier
    article and would still score low, so it would look like a different story every
    time it grew. Containment asks the question that matters — is one of these two
    substantially inside the other.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def reconcile(
    clusters: list[list[str]],
    known: dict[str, list[str]],
    *,
    containment: float = IDENTITY_CONTAINMENT,
) -> dict[str, Any]:
    """Match this run's clusters to the stories already open.

    `clusters` are article-URL lists from the current window; `known` maps story id
    to the URLs last seen under it. Windows overlap in time, so a story seen twice
    shares concrete articles and the join is exact rather than a similarity.

    Merges and splits are recorded as events. Without them the accumulated history
    becomes unjoinable exactly when the anomalies first need it: a story that absorbs
    another, or divides in two, would otherwise appear to have jumped.
    """
    current = [set(c) for c in clusters]
    prior = {sid: set(urls) for sid, urls in known.items()}

    # every (cluster, known story) pair that overlaps enough to be the same story
    matches: dict[int, list[str]] = {i: [] for i in range(len(current))}
    for i, cluster in enumerate(current):
        for sid, urls in prior.items():
            if _containment(cluster, urls) >= containment:
                matches[i].append(sid)

    assignments: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    used: set[str] = set()

    for i, cluster in enumerate(current):
        candidates = [s for s in matches[i] if s not in used]
        if not candidates:
            sid = story_id(sorted(cluster), used | set(prior))
            assignments.append({"id": sid, "urls": sorted(cluster)})
            # a cluster whose only candidates were taken is a split, not a birth
            if matches[i]:
                events.append({"type": "split", "from": sorted(matches[i]), "to": sid})
            else:
                events.append({"type": "created", "id": sid})
            used.add(sid)
            continue

        # keep the largest prior story's id, so the longest-running series survives
        sid = max(candidates, key=lambda s: len(prior[s]))
        assignments.append({"id": sid, "urls": sorted(cluster)})
        used.add(sid)
        absorbed = [s for s in candidates if s != sid]
        if absorbed:
            events.append({"type": "merged", "into": sid, "absorbed": sorted(absorbed)})
            used.update(absorbed)

    seen_ids = {a["id"] for a in assignments} | {
        s for e in events if e["type"] == "merged" for s in e["absorbed"]
    }
    for sid in prior:
        if sid not in seen_ids:
            events.append({"type": "dormant", "id": sid})

    logger.info(
        "identity: %d clusters -> %d stories (%s)",
        len(current),
        len(assignments),
        ", ".join(
            f"{t}={sum(1 for e in events if e['type'] == t)}"
            for t in ("created", "merged", "split", "dormant")
        ),
    )
    return {"assignments": assignments, "events": events}
