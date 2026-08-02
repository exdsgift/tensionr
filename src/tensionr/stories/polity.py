"""Map a publisher's domain to the polity it publishes from."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PolityTable:
    """Domain to polity, from explicit entries first and a TLD fallback second.

    Polity of publication is a fact rather than a judgement about editorial stance,
    which is why it is the axis (#20). The distinction it does *not* yet make is
    ownership: a Qatari-owned outlet publishing from London is a real case, and the
    sourced table #21 calls for records both. This one records publication only, and
    is provisional until that table exists.
    """

    def __init__(self, explicit: dict[str, str], tlds: dict[str, str]) -> None:
        self._explicit = {d.lower(): p for d, p in explicit.items()}
        self._tlds = {t.lower(): p for t, p in tlds.items()}

    @classmethod
    def load(cls, path: Path) -> "PolityTable":
        payload = json.loads(Path(path).read_text("utf-8"))
        return cls(payload.get("domains", {}), payload.get("tlds", {}))

    def of(self, domain: str) -> str | None:
        """The polity, or None when it cannot be decided from the domain alone.

        None is not "unknown country" — it means this publisher cannot be placed, so
        it contributes to the source count but not to the polity quorum. Guessing a
        polity from a generic TLD would put every `.com` in one bucket and quietly
        invent agreement between unrelated outlets.
        """
        domain = domain.lower().removeprefix("www.")
        if domain in self._explicit:
            return self._explicit[domain]
        parts = domain.split(".")
        for candidate in (".".join(parts[-2:]), parts[-1]):
            if candidate in self._tlds:
                return self._tlds[candidate]
        return None

    def coverage(self, domains: list[str]) -> dict[str, float | int]:
        """How much of a set of publishers can be placed at all."""
        placed = sum(1 for d in domains if self.of(d))
        return {
            "domains": len(domains),
            "placed": placed,
            "rate": round(placed / len(domains), 4) if domains else 0.0,
        }
