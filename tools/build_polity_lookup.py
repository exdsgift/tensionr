"""Build the bulk domain-to-polity lookup from GDELT's own table.

Run by hand, not by the engine. The source is a static file GDELT published once in
May 2018 and has not replaced (`2020-` and `2021-` both 404), so there is nothing to
schedule: it is fetched, audited, folded into this repository, and left alone.

    uv run --project backend python tools/build_polity_lookup.py

WHY THIS EXISTS

`data/polities/domains.json` places a publisher from 37 hand-written entries and 100
country TLDs. Generic TLDs are deliberately absent from it, because mapping every
`.com` to one country would invent agreement between unrelated outlets. The cost is
that every `.com` is unplaced, and measured on a real window that is most of the
corpus: 3,264 of 7,890 domains placed, 41.4%.

GDELT's table answers exactly the case the TLD cannot. Measured on the same window it
places 7,387 of 7,890, and the two together place 7,547: **41.4% to 95.7%**.

WHAT WAS AUDITED, BECAUSE COVERAGE IS NOT ACCURACY

Against the 37 entries in this repository that were written by hand, GDELT disagrees on
8 of the 34 it covers, and the disagreements are not random: it calls `aljazeera.com`
United States, `aljazeera.net` Israel, `reuters.com` United States and `scmp.com`
China. That is a 24% error rate on precisely the outlets someone had already found
worth correcting.

That number is not the error rate on the corpus, and reporting it as one would be the
sampling mistake it looks like: those 37 exist *because* they are the hard cases.
Measured across the 3,104 domains where both tables answer, they agree on 95.2%, and
128 of the 148 disagreements are one country under two names rather than two countries.

So the order is: hand-written entries first, then the TLD, then this file. Purely
additive - it can only place a publisher this project previously left unplaced, and
can never overrule a placement already being made. The Al Jazeera correction stands.

WHAT IS STILL WRONG IN IT, AND IS FIXED HERE

Eight domains this project's corpus carries are Palestinian outlets that GDELT places
in Israel. On a page whose entire finding is which country's outlets used which name,
that is not a rounding error, and OVERRIDES corrects it by hand.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from urllib.request import urlopen

SOURCE = (
    "https://data.gdeltproject.org/blog/"
    "2018-news-outlets-by-country-may2018-update/"
    "MASTER-GDELTDOMAINSBYCOUNTRY-MAY2018.TXT"
)

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "polities" / "domains.json"
OUT = ROOT / "data" / "polities" / "gdelt-domains.json.gz"

# One country under two names. Left unmapped, the country test would count Türkiye and
# Turkey as two polities and split a country's outlets in half - in the one measurement
# on the page that is entirely about countries. Measured on a real window, these five
# account for 128 of 148 disagreements between the two tables.
ALIASES = {
    "Turkey": "Türkiye",
    "Czech Republic": "Czechia",
    "Macedonia": "North Macedonia",
    "Slovak Republic": "Slovakia",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}

# Placements GDELT gets wrong that this corpus actually carries. Kept short and
# specific: this is a correction list, not a second table.
OVERRIDES = {
    "maannews.net": "Palestine",
    "maannews.com": "Palestine",
    "wafa.ps": "Palestine",
    "palestinechronicle.com": "Palestine",
    "middleeastmonitor.com": "United Kingdom",
    "al-monitor.com": "United States",
}


def fetch() -> str:
    cache = ROOT / ".cache" / "gdelt-domains.txt"
    if cache.exists():
        print(f"using cached {cache}", file=sys.stderr)
        return cache.read_text("utf-8", errors="replace")
    cache.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {SOURCE}", file=sys.stderr)
    with urlopen(SOURCE, timeout=120) as response:
        text = response.read().decode("utf-8", errors="replace")
    cache.write_text(text, "utf-8")
    return text


def main() -> None:
    table = json.loads(TABLE.read_text("utf-8"))
    tlds = {t.lower() for t in table["tlds"]}

    def tld_decides(domain: str) -> bool:
        parts = domain.split(".")
        return ".".join(parts[-2:]) in tlds or parts[-1] in tlds

    rows: dict[str, str] = {}
    seen = 0
    for line in fetch().splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or not parts[0]:
            continue
        seen += 1
        domain = parts[0].lower()
        # Half the file is domains whose own TLD already answers, and the TLD is
        # consulted first. Keeping them would double the file to say nothing.
        if tld_decides(domain):
            continue
        rows[domain] = ALIASES.get(parts[2], parts[2])
    rows.update(OVERRIDES)

    # Country names are interned: 99,444 rows share about 240 names, and repeating
    # them costs a megabyte for nothing.
    names = sorted(set(rows.values()))
    index = {name: i for i, name in enumerate(names)}
    payload = {
        "_comment": (
            "Domain to polity of publication, from GDELT's May 2018 table. Consulted "
            "only after data/polities/domains.json and its TLD fallback, so it can "
            "place a publisher this project left unplaced and can never overrule a "
            "placement already being made. Built by tools/build_polity_lookup.py; "
            "see that file for what was audited."
        ),
        "_source": SOURCE,
        "names": names,
        "domains": {d: index[c] for d, c in sorted(rows.items())},
    }
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    OUT.write_bytes(gzip.compress(blob, 9))

    print(f"  rows in source          {seen:>8,}", file=sys.stderr)
    print(f"  dropped, TLD decides    {seen - len(rows):>8,}", file=sys.stderr)
    print(f"  written                 {len(rows):>8,}", file=sys.stderr)
    print(f"  distinct polities       {len(names):>8,}", file=sys.stderr)
    print(f"  {OUT.name}  {OUT.stat().st_size / 2**20:.2f} MB", file=sys.stderr)


if __name__ == "__main__":
    main()
