"""Build the actor alias table from Wikidata, with every entity verified."""

import json
import logging
from pathlib import Path
from typing import Any

from tensionr.config import WIKIDATA_ENTITY_URL, WIKIDATA_SEARCH_URL
from tensionr.http_client import request_with_retry
from tensionr.stories.actors import AliasTable, script_of, usable_alias
from tensionr.stories.languages import codes

logger = logging.getLogger(__name__)


def language_scripts(entities: dict[str, dict[str, Any]]) -> dict[str, str]:
    """The script each language writes in, counted from the labels themselves.

    Needed by the `mul` fallback below, and derived rather than declared: a table of
    language codes to scripts is one more thing to keep true, while the labels already
    say it several dozen times over.
    """
    tally: dict[str, dict[str, int]] = {}
    for entity in entities.values():
        for language, label in entity.get("labels", {}).items():
            value = label.get("value")
            if not value or language == "mul":
                continue
            counts = tally.setdefault(language, {})
            script = script_of(value)
            counts[script] = counts.get(script, 0) + 1
    return {
        language: max(counts, key=lambda s: counts[s])
        for language, counts in tally.items()
        if counts
    }


def select_aliases(
    entity: dict[str, Any],
    languages: list[str] | None = None,
    scripts: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """Labels and aliases per language, filtered and deduplicated within each.

    Keyed by language, not flattened, because the language is what decides whether a
    headline can be measured at all: a row in a language we never fetched is
    unmeasurable rather than an omission (#49). Flattening threw that away, and a
    Bulgarian headline was then judged against Russian spellings.

    Deduplication is within a language, not across. The same string in two languages is
    kept in both — "Iran" is the label in English, Spanish and Italian, and each of those
    is a separate claim about what can be read.

    Only strings surviving `usable_alias` are kept, so the script-aware length floor and
    the ASCII-only code filter apply here rather than at match time.

    THE `mul` LABEL, WHICH IS WHY TRUMP WAS INVISIBLE IN ENGLISH

    Wikidata has begun storing a name that is written identically across languages once,
    under the language code `mul`, instead of repeating it for each. Q22686 is fully
    migrated: it carries `mul: "Donald Trump"` and Cyrillic, Chinese, Tamil and Hebrew
    labels, and **no English, Spanish, Italian or French label at all**.

    Reading only the per-language labels, this produced a table where Trump had no
    Latin-script alias, so every English headline came back `unresolved` rather than
    measured. Measured on the corpus: of 248 Latin-script headlines containing the word
    Trump, the engine named him in **none**. Putin, Kushner and Witkoff were at 4%,
    matching only where the full name appeared.

    So `mul` fills in for a language that has no label of its own. Not unconditionally:
    #49's lesson is that claiming a row is answerable when it is not manufactures false
    omissions, and a Latin name would do exactly that to a language written in another
    script. It is applied only where the script of the `mul` label matches the script
    that language is written in, and that script is counted from the labels rather than
    declared in a table.
    """
    table: dict[str, dict[str, list[str]]] = {}
    labels = entity.get("labels", {})
    shared = labels.get("mul", {}).get("value")
    shared_script = script_of(shared) if shared else None
    for language in languages if languages is not None else codes():
        found: list[str] = []
        label = labels.get(language, {}).get("value")
        if label:
            found.append(label)
        elif shared and (scripts or {}).get(language) == shared_script:
            found.append(shared)
        for alias in entity.get("aliases", {}).get(language, []):
            value = alias.get("value")
            if value:
                found.append(value)

        seen: set[str] = set()
        kept: list[str] = []
        for value in found:
            key = value.casefold()
            if key in seen or not usable_alias(value):
                continue
            seen.add(key)
            kept.append(value)
        if kept:
            table[language] = kept
    return table


def describe(entity: dict[str, Any]) -> dict[str, Any]:
    """The fields a human needs to check that the right entity was picked."""
    return {
        "qid": entity.get("id"),
        "label": entity.get("labels", {}).get("en", {}).get("value"),
        "description": entity.get("descriptions", {}).get("en", {}).get("value"),
        "instance_of": [
            claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
            for claim in entity.get("claims", {}).get("P31", [])
        ],
    }


def search(term: str, *, limit: int = 5) -> list[dict[str, str]]:
    """Candidate entities for a search term, with their descriptions."""
    response = request_with_retry(
        "GET",
        WIKIDATA_SEARCH_URL,
        params={
            "action": "wbsearchentities",
            "search": term,
            "language": "en",
            "format": "json",
            "limit": limit,
        },
        headers={"User-Agent": "tensionr/2.0 (alias table builder)"},
    )
    if response is None or response.status_code != 200:
        return []
    return [
        {
            "qid": hit["id"],
            "label": hit.get("label", ""),
            "description": hit.get("description", ""),
        }
        for hit in response.json().get("search", [])
    ]


def entities(qids: list[str]) -> dict[str, dict[str, Any]]:
    """Full records for up to fifty ids at a time, the API's batch limit."""
    out: dict[str, dict[str, Any]] = {}
    for start in range(0, len(qids), 50):
        batch = qids[start : start + 50]
        response = request_with_retry(
            "GET",
            WIKIDATA_ENTITY_URL,
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels|aliases|descriptions|claims",
                "format": "json",
            },
            headers={"User-Agent": "tensionr/2.0 (alias table builder)"},
        )
        if response is None or response.status_code != 200:
            logger.warning("wikidata batch failed: %s", batch[0])
            continue
        out.update(response.json().get("entities", {}))
    return out


def build(seeds: dict[str, str]) -> dict[str, Any]:
    """An alias table from `{actor key: QID}`, with an audit row for every entity.

    QIDs are never written in source. #22 found 34 of 65 hand-written ids pointed at
    the wrong entity and failed without complaint, so the seeds come from a data file
    that `search` helps assemble and a human checks, and this records what each id
    actually resolved to so the check can be repeated later.
    """
    records = entities(sorted(set(seeds.values())))

    # A person's family name, which is what a headline actually writes.
    #
    # Wikidata gives a person's label as their full name, and headlines give the
    # surname alone. Measured on the corpus: of 248 Latin-script headlines containing
    # the word Trump, the full-name alias matched 10. Restoring evaluability without
    # this would be worse than leaving it broken, because 213 rows that honestly said
    # "cannot be answered" would start saying "did not name Trump" about headlines
    # whose first word is Trump. That is #49's failure exactly.
    #
    # P734 is the property, and the family name is an entity with its own labels per
    # language, so `Trump` and `Трамп` and `トランプ` all arrive in the right script
    # rather than being split off the label as a string.
    surnames = {
        qid: [
            claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
            for claim in entity.get("claims", {}).get("P734", [])
        ]
        for qid, entity in records.items()
    }
    family = entities(sorted({q for ids in surnames.values() for q in ids if q}))

    # Counted once across every entity, because the `mul` fallback needs to know which
    # script a language is written in and no single entity can say.
    scripts = language_scripts({**records, **family})
    table: dict[str, dict[str, list[str]]] = {}
    audit: list[dict[str, Any]] = []
    missing: list[str] = []

    for actor, qid in seeds.items():
        entity = records.get(qid)
        if not entity or "missing" in entity:
            missing.append(actor)
            continue
        aliases = select_aliases(entity, scripts=scripts)
        for surname_qid in surnames.get(qid, []):
            if not surname_qid:
                continue
            for language, names in select_aliases(
                family.get(surname_qid, {}), scripts=scripts
            ).items():
                merged = aliases.setdefault(language, [])
                seen = {n.casefold() for n in merged}
                merged.extend(n for n in names if n.casefold() not in seen)
        if not aliases:
            missing.append(actor)
            continue
        table[actor] = aliases
        audit.append(
            {
                "actor": actor,
                **describe(entity),
                "aliases": sum(len(v) for v in aliases.values()),
                "languages": len(aliases),
            }
        )

    if missing:
        logger.warning(
            "no usable aliases for %d actors: %s", len(missing), ", ".join(missing[:8])
        )
    return {"table": table, "audit": audit, "missing": missing}


def write(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True), "utf-8"
    )


def read_seeds(path: Path) -> dict[str, str]:
    """Actor key to QID from the curated file, dropping the comment key."""
    payload = json.loads(Path(path).read_text("utf-8"))
    return {actor: row["qid"] for actor, row in payload["actors"].items()}


def load(path: Path) -> AliasTable:
    """The resolver's table, loaded from data rather than constructed in code."""
    payload = json.loads(Path(path).read_text("utf-8"))
    return AliasTable(payload["table"])


def main(argv: list[str] | None = None) -> int:
    """Rebuild the alias table from the curated seeds.

    Deliberately a command rather than a scheduled job. The table is reference data a
    human checks: every entity carries an audit row with its label and description so a
    wrong QID can be seen, and #22 found 34 of 65 hand-written ids pointed at the wrong
    entity while failing silently. Rebuilding is cheap; rebuilding unattended is how a
    silent regression ships.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m tensionr.stories.wikidata",
        description="Rebuild data/actors/aliases.json from data/actors/seeds.json.",
    )
    parser.add_argument("--seeds", type=Path, default=Path("data/actors/seeds.json"))
    parser.add_argument("--out", type=Path, default=Path("data/actors/aliases.json"))
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    result = build(read_seeds(args.seeds))
    write(result, args.out)
    logger.info(
        "%d actors, %d aliases across %d languages, %d actors with nothing usable",
        len(result["table"]),
        sum(
            len(v)
            for by_language in result["table"].values()
            for v in by_language.values()
        ),
        len({lang for by_language in result["table"].values() for lang in by_language}),
        len(result["missing"]),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
