"""Say what a Wikidata id resolves to, and whether the vocabulary's rules admit it.

Run by the propose-an-actor workflow and by hand:

    uv run --project backend python tools/check_actor.py Q13628723

It decides nothing. It prints the label, the description, the types, and for a person
the occupation and position tests and the death test, in the words a maintainer needs
to accept or refuse the proposal. The rules are the ones recorded in
tools/actor_candidates.py; this reads them from there rather than copying them, so the
two cannot drift apart.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from actor_candidates import (
    GOVERNMENT_POSITION_TYPES,
    KEEP_TYPES,
    POLITICAL_OCCUPATIONS,
)
from tensionr.stories import wikidata as W


def _ids(entity: dict, prop: str) -> list[str]:
    return [
        c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
        for c in entity.get("claims", {}).get(prop, [])
        if c.get("mainsnak", {}).get("datavalue")
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not re.fullmatch(r"Q\d+", argv[1]):
        print("usage: check_actor.py Q<number>", file=sys.stderr)
        return 2
    qid = argv[1]
    entity = W.entities([qid]).get(qid)
    if not entity or "missing" in entity:
        print(f"**{qid}** does not resolve to a Wikidata entity.")
        return 1

    label = entity.get("labels", {}).get("en", {}).get("value") or entity.get(
        "labels", {}
    ).get("mul", {}).get("value", "(no label)")
    description = entity.get("descriptions", {}).get("en", {}).get("value", "")
    type_ids = [t for t in _ids(entity, "P31") if t]
    occ_ids = [t for t in _ids(entity, "P106") if t]
    pos_ids = [t for t in _ids(entity, "P39") if t]
    names = W.entities(sorted(set(type_ids + occ_ids + pos_ids)))
    lab = lambda x: names.get(x, {}).get("labels", {}).get("en", {}).get("value", x)
    types = [lab(t) for t in type_ids]
    occupations = [lab(t) for t in occ_ids]
    positions = [lab(t) for t in pos_ids]
    died = bool(entity.get("claims", {}).get("P570"))

    print(f"**{qid}** resolves to **{label}**: {description or 'no description'}.")
    print()
    print(f"- instance of: {', '.join(types) or 'nothing recorded'}")
    in_scope = any(t in KEEP_TYPES for t in types)
    if "human" in types:
        political = sorted(POLITICAL_OCCUPATIONS & set(occupations))
        pos_types: set[str] = set()
        for pid in pos_ids:
            pos_types |= {lab(t) for t in _ids(names.get(pid, {}), "P31")}
        govt = sorted(GOVERNMENT_POSITION_TYPES & pos_types)
        print(f"- occupations: {', '.join(occupations) or 'none recorded'}")
        print(f"- positions held: {', '.join(positions[:6]) or 'none recorded'}")
        print(
            f"- political occupation: {'yes, ' + ', '.join(political) if political else 'no'}"
        )
        print(f"- government position: {'yes, ' + ', '.join(govt) if govt else 'no'}")
        print(
            f"- date of death: {'recorded, so not a living actor' if died else 'none'}"
        )
        admit = (bool(political) or bool(govt)) and not died
    else:
        admit = in_scope
    print()
    if admit:
        print(
            "**Passes the vocabulary's rules.** A maintainer still verifies the label and "
            "description above are the intended entity before it lands: 34 of 65 ids "
            "once looked right and pointed at the wrong thing."
        )
    else:
        print(
            "**Does not pass the vocabulary's rules as they stand.** A maintainer can "
            "still admit it with a stated reason, or the rules can change; neither "
            "happens silently."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
