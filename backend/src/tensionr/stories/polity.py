"""Map a publisher's domain to the polity it publishes from."""

import gzip
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

    def __init__(
        self,
        explicit: dict[str, str],
        tlds: dict[str, str],
        bulk: dict[str, str] | None = None,
    ) -> None:
        self._explicit = {d.lower(): p for d, p in explicit.items()}
        self._tlds = {t.lower(): p for t, p in tlds.items()}
        self._bulk = bulk or {}

    @classmethod
    def load(cls, path: Path) -> "PolityTable":
        """Load the hand table, and the bulk lookup beside it if it is there.

        The bulk file is optional on purpose: it is a build artefact of
        `tools/build_polity_lookup.py`, and a checkout without it must still place
        every publisher the hand table and the TLDs can, rather than fail.
        """
        path = Path(path)
        payload = json.loads(path.read_text("utf-8"))
        return cls(
            payload.get("domains", {}),
            payload.get("tlds", {}),
            _load_bulk(path.with_name("gdelt-domains.json.gz")),
        )

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

        # Last, and only where the two above are silent. That order is what makes this
        # purely additive: the bulk table can place a publisher this project used to
        # leave unplaced, and can never overrule a placement already being made - which
        # matters, because it calls `aljazeera.com` United States and this repository
        # does not. Measured on a real window, adding it moves placement from 41.4% to
        # 95.7% without changing one existing answer.
        if domain in self._bulk:
            return self._bulk[domain]
        # A parent-domain walk, which took GDELT's own coverage from 94.1% to 98.7%:
        # `news.example.com` is placed by `example.com` when the host itself is absent.
        for cut in range(1, len(parts) - 1):
            parent = ".".join(parts[cut:])
            if parent in self._bulk:
                return self._bulk[parent]
        return None

    def coverage(self, domains: list[str]) -> dict[str, float | int]:
        """How much of a set of publishers can be placed at all."""
        placed = sum(1 for d in domains if self.of(d))
        return {
            "domains": len(domains),
            "placed": placed,
            "rate": round(placed / len(domains), 4) if domains else 0.0,
        }


def _load_bulk(path: Path) -> dict[str, str]:
    """The gzipped domain-to-polity lookup, with its country names interned.

    99,445 rows share 242 names, so the file stores each name once and each domain as
    an index into that list: 3.08 MB of plain JSON becomes 0.61 MB on disk. It is read
    once per run, in the engine only; the page never sees it.
    """
    if not path.exists():
        logger.info("no bulk polity lookup at %s; hand table and TLDs only", path)
        return {}
    payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    names = payload.get("names", [])
    return {d: names[i] for d, i in payload.get("domains", {}).items()}
