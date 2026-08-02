"""Decide whether an actor is named in a headline, in three states, across scripts."""

import logging
import re
import unicodedata
from typing import Any

from tensionr.stories.measure import ABSENT, PRESENT, UNRESOLVED

logger = logging.getLogger(__name__)

# A two-letter Latin alias is noise — "US" matches half the corpus. Two CJK
# characters are a whole word. The floor is therefore per script, not global; a
# single global value silently deleted every CJK alias during the research (#22).
MIN_ALIAS_CHARS = {
    "latin": 4,
    "cyrillic": 4,
    "greek": 4,
    "arabic": 3,
    "cjk": 2,
    "other": 3,
}

# Aliases that look like identifiers rather than names. This may only be applied to
# ASCII strings: run against Arabic or CJK it rejects ordinary words (#22).
CODE_SHAPE = re.compile(r"^[A-Z0-9][A-Z0-9._/-]*$")

_RANGES = (
    ("cyrillic", 0x0400, 0x04FF),
    ("greek", 0x0370, 0x03FF),
    ("arabic", 0x0600, 0x06FF),
    ("cjk", 0x3040, 0x9FFF),
    ("cjk", 0xAC00, 0xD7AF),
)


def script_of(text: str) -> str:
    """The dominant script of a string, by counting letters."""
    counts: dict[str, int] = {}
    for char in text:
        if not char.isalpha():
            continue
        code = ord(char)
        name = "latin" if code < 0x0250 else "other"
        for candidate, lo, hi in _RANGES:
            if lo <= code <= hi:
                name = candidate
                break
        counts[name] = counts.get(name, 0) + 1
    return max(counts, key=counts.get) if counts else "other"


def usable_alias(alias: str) -> bool:
    """Whether an alias is specific enough to match on.

    Two traps from #22 are encoded here. The length floor is per script, and the
    code-shape filter is ASCII-only — applied to other scripts it rejects real
    words, which is how an earlier build zeroed out every CJK actor without failing.
    """
    alias = alias.strip()
    if not alias:
        return False
    script = script_of(alias)
    if len(alias) < MIN_ALIAS_CHARS.get(script, 3):
        return False
    if alias.isascii() and CODE_SHAPE.match(alias):
        return False
    return True


def _fold(text: str) -> str:
    """Lowercase, strip accents on Latin text, and reduce punctuation to spaces."""
    lowered = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in lowered if not unicodedata.combining(c))
    return (
        " "
        + " ".join(re.sub(r"[^\w\s]", " ", stripped, flags=re.UNICODE).split())
        + " "
    )


class AliasTable:
    """Actor keys to aliases, indexed by the script each alias is written in.

    Built from data rather than literals. #22 found that 34 of 65 hand-written
    Wikidata QIDs were wrong and failed silently, so nothing here is hardcoded: the
    table is loaded, and an actor absent from it is undecidable rather than absent.
    """

    def __init__(self, actors: dict[str, list[str]]) -> None:
        self._by_script: dict[str, dict[str, list[str]]] = {}
        self._dropped: list[tuple[str, str]] = []
        for actor, aliases in actors.items():
            for alias in aliases:
                if not usable_alias(alias):
                    self._dropped.append((actor, alias))
                    continue
                script = script_of(alias)
                self._by_script.setdefault(actor, {}).setdefault(script, []).append(
                    alias
                )

    @property
    def dropped(self) -> list[tuple[str, str]]:
        """Aliases rejected as unusable, so a thin actor can be seen rather than guessed at."""
        return list(self._dropped)

    def actors(self) -> list[str]:
        return sorted(self._by_script)

    def scripts_for(self, actor: str) -> set[str]:
        return set(self._by_script.get(actor, {}))

    def resolve(self, title: str, actor: str) -> str:
        """Present, absent, or undecidable — never two states.

        Undecidable means the table holds no alias in the title's own script, so the
        question cannot be answered rather than answered "no". An undecidable row
        leaves the denominator; counting it absent would manufacture an omission, and
        omission is the signal.
        """
        script = script_of(title)
        aliases = self._by_script.get(actor, {}).get(script)
        if not aliases:
            return UNRESOLVED

        if script in ("arabic", "cjk"):
            # No spaces between words in CJK, and Arabic attaches clitics, so a
            # boundary match would miss most real mentions.
            lowered = title.lower()
            return PRESENT if any(a.lower() in lowered for a in aliases) else ABSENT

        folded = _fold(title)
        return PRESENT if any(_fold(a).strip() in folded for a in aliases) else ABSENT


def coverage(
    table: AliasTable, rows: list[dict[str, Any]], actor: str
) -> dict[str, Any]:
    """How much of a story the table can actually answer for, by script.

    Reported rather than assumed: the hazard #22 measured is not missing entities but
    morphology — Ukrainian had 94.6% alias availability against 24.1% title recall.
    A script that is answerable but never matches is the signature, though it is a
    signal to investigate rather than a diagnosis: the actor may simply be absent
    from those stories. Separating the two needs a story known to involve the actor.
    """
    seen: dict[str, dict[str, int]] = {}
    for row in rows:
        script = script_of(row.get("title", ""))
        bucket = seen.setdefault(script, {"rows": 0, "answerable": 0, "named": 0})
        bucket["rows"] += 1
        state = table.resolve(row.get("title", ""), actor)
        if state != UNRESOLVED:
            bucket["answerable"] += 1
        if state == PRESENT:
            bucket["named"] += 1
    return seen
