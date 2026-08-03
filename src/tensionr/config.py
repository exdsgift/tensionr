"""Central configuration: paths, credentials, feed lists and tuning constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths (overridable for tests / local runs)
DATA_DIR = Path(os.getenv("TENSIONR_DATA_DIR", "data"))
ARCHIVE_DIR = DATA_DIR / "archive"

HF_TOKEN: str | None = os.getenv("HF_TOKEN")

USER_AGENT = "tensionr_cyber_node/1.0"

# Pipeline tuning
MAX_NEW_ARTICLES = 200  # cap on per-run NLP work
ARTICLE_CAP = 500  # rolling window size of news.json
GTI_HISTORY_CAP = 50
DEADLINE_SECONDS = int(
    os.getenv("TENSIONR_DEADLINE", "480")
)  # skip optional LLM stages past this
HF_BATCH_SIZE = 32

GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = "war conflict economy military finance"
GDELT_TIMELINE_QUERY = "war conflict economy"

RSS_FEEDS: list[str] = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.net/aljazeerarss/a7c986be-c2bd-44a7-82f1-104a5e6bb854/73d0e1b4-532f-45ef-b135-bfdff8b8cab9",
    "https://www.theguardian.com/world/rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.japantimes.co.jp/feed/",
    "https://www.spiegel.de/ausland/index.rss",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
    "https://www.straitstimes.com/news/world/rss.xml",
    "https://en.mercopress.com/rss/",
    "https://www.chinadaily.com.cn/rss/world_rss.xml",
    "https://www.rt.com/rss/news/",
    "https://www.scmp.com/rss/91/feed",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://www.france24.com/en/rss",
    "https://www.dw.com/en/top-stories/s-9097/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.washingtonpost.com/arcfeed/rss/category/world/?itid=lk_inline_manual_41",
    "https://www.cbc.ca/cctoc/rss/news/world",
    "https://www.abc.net.au/news/feed/52278/rss.xml",
]
RSS_SAMPLE_SIZE = 15

RSS_METADATA: dict[str, dict[str, str]] = {
    "feeds.bbci.co.uk": {"country": "United Kingdom", "lang": "English"},
    "www.aljazeera.net": {"country": "Qatar", "lang": "Arabic"},
    "www.theguardian.com": {"country": "United Kingdom", "lang": "English"},
    "feeds.a.dj.com": {"country": "United States", "lang": "English"},
    "www.lemonde.fr": {"country": "France", "lang": "French"},
    "www.japantimes.co.jp": {"country": "Japan", "lang": "Japanese"},
    "www.spiegel.de": {"country": "Germany", "lang": "English"},
    "feeds.elpais.com": {"country": "Spain", "lang": "Spanish"},
    "timesofindia.indiatimes.com": {"country": "India", "lang": "English"},
    "www.jpost.com": {"country": "Israel", "lang": "English"},
    "www.straitstimes.com": {"country": "Singapore", "lang": "English"},
    "en.mercopress.com": {"country": "Uruguay", "lang": "Spanish"},
    "www.chinadaily.com.cn": {"country": "China", "lang": "English"},
    "www.rt.com": {"country": "Russia", "lang": "Russian"},
    "www.scmp.com": {"country": "China", "lang": "English"},
    "www.thehindu.com": {"country": "India", "lang": "English"},
    "feeds.reuters.com": {"country": "Global", "lang": "English"},
    "www.france24.com": {"country": "France", "lang": "English"},
    "www.dw.com": {"country": "Germany", "lang": "English"},
    "rss.nytimes.com": {"country": "United States", "lang": "English"},
    "www.washingtonpost.com": {"country": "United States", "lang": "English"},
    "www.cbc.ca": {"country": "Canada", "lang": "English"},
    "www.abc.net.au": {"country": "Australia", "lang": "English"},
}

KNOWN_COUNTRIES: list[str] = [
    "United States",
    "United Kingdom",
    "Qatar",
    "France",
    "Russia",
    "Japan",
    "Australia",
    "India",
    "Israel",
    "Ukraine",
    "Singapore",
    "Canada",
    "Saudi Arabia",
    "Uruguay",
    "Iran",
    "China",
    "Germany",
    "Turkey",
    "Egypt",
    "United Arab Emirates",
    "South Korea",
    "North Korea",
    "Taiwan",
    "Pakistan",
    "Syria",
    "Lebanon",
    "Yemen",
    "Iraq",
    "Afghanistan",
    "Mexico",
    "Brazil",
    "Venezuela",
    "Colombia",
    "South Africa",
    "Nigeria",
    "Kenya",
    "Somalia",
    "Sudan",
    "Ethiopia",
    "Poland",
    "Italy",
    "Spain",
    "Palestine",
]

TICKERS: dict[str, str] = {
    "VIX (VOLATILITY)": "^VIX",
    "GOLD (XAU)": "GC=F",
    "CRUDE OIL": "CL=F",
    "RAYTHEON (RTX)": "RTX",
    "LOCKHEED (LMT)": "LMT",
    "NORTHROP (NOC)": "NOC",
    "GEN DYNAMICS (GD)": "GD",
    "BTC/USD": "BTC-USD",
    "EUR/USD": "EURUSD=X",
    "S&P 500": "^GSPC",
    "NASDAQ 100": "^IXIC",
}

MIL_CALLSIGN_PREFIXES: list[str] = [
    "RCH",
    "SPAR",
    "SAM",
    "USAF",
    "AF",
    "RRR",
    "FAF",
    "GAF",
    "IAM",
    "BAF",
    "PLF",
    "CFC",
    "ASY",
    "RSF",
    "SUI",
    "AME",
]

CYBER_FEED_URL = "https://feeds.feedburner.com/TheHackersNews"
CHATTER_FEED_URL = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"
OPENSKY_URL = "https://opensky-network.org/api/states/all"

# --- v2 story pipeline -------------------------------------------------------
# GDELT publishes document embeddings on the quarter hour, roughly twenty
# minutes late. See docs/research/event-clustering-multilingual-headlines.md.
DOCEMBED_URL = (
    "http://data.gdeltproject.org/gdeltv3/gsg_docembed/{stamp}.gsg.docembed.json.gz"
)
HEARTBEAT_MINUTES = 15
PUBLISH_LAG_MINUTES = 25
EMBEDDING_DIM = 512

# Twelve hours. Not a tuning parameter, and not a freshness setting: it is sized so
# consecutive windows still overlap when GitHub skips a run. Story identity is a URL
# join between runs (#10), and the capture is the one store time cannot rebuild (#12),
# so a gap wider than the window loses articles permanently.
#
# Measured on this repository: the schedule is asked for every 4 hours and GitHub
# delivers 37-44% of what is asked, with observed gaps to 3h55 at hourly. At a
# 4-hourly cadence a single missed run is an 8-hour gap, which a 6-hour window would
# not cover. Twelve hours covers two consecutive misses.
WINDOW_SLOTS = 48

# Clustering. Thresholds are chosen per window rather than fixed: the percolation
# point was measured at 0.70, 0.75 and 0.76 in three separate windows, so a
# constant would over-merge a quarter of the corpus on some days. What is fixed
# is the criterion — the largest component may not exceed this share.
EDGE_FLOOR = 0.55
THRESHOLD_HI = 0.95
THRESHOLD_STEP = 0.01
THEME_MAX_SHARE = 0.05
STORY_MAX_SHARE = 0.35
MIN_THEME_SIZE = 8
MIN_STORY_SIZE = 5

# Identity across runs. Windows overlap in time, so a story seen twice shares
# concrete articles: the join is exact rather than a similarity. Containment
# rather than Jaccard, because a story that doubles still shares every earlier
# article and must not read as a new one.
IDENTITY_CONTAINMENT = 0.5

# Floors on a published figure. Both measured rather than chosen: below M = 20 the
# language artefact moves a figure 4.9pp at the median and 16.7pp at p90, against
# 0.7 / 3.7 at M >= 50, and top-ten ranking stability rises from 3/10 at a floor of
# 10 to 8/10 at 30 (#23). Two polities because one voice cannot disagree (#20).
MIN_EVALUABLE = 30
MIN_POLITIES = 2


# Several rows sit within 0.005 of the top division score while the artefact moves a
# figure by as much again, so the lead is a band and its internal order is not a
# claim (#23).
BAND_TOLERANCE = 0.005

# GDELT's knowledge graph, the second channel for actor resolution. Its name fields
# arrive in Latin script for every language because GDELT machine-translates and then
# runs the English extractor, and V2DOCUMENTIDENTIFIER is the article URL in exactly
# the form the embeddings feed uses. A single timestamp joins only ~23% of a window;
# accumulating slots reaches ~95% (#22).
GKG_URL = "http://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip"
GKG_TRANSLATION_URL = (
    "http://data.gdeltproject.org/gdeltv2/{stamp}.translation.gkg.csv.zip"
)
GKG_LAG_MINUTES = 30
GKG_COLUMNS = 27
FIELD_SIZE_LIMIT = 4 * 1024 * 1024

# The alias table. Languages are the thirteen with a resilient two-polity panel
# (#21) plus the scripts our corpus actually carries, so an actor is answerable
# wherever a story might be told. QIDs live in data, never in source: 34 of 65
# hand-written ids pointed at the wrong entity and failed silently (#22).
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/w/api.php"
# The languages to fetch labels for live in `tensionr.stories.languages`, beside the
# GDELT-name-to-code mapping that decides which of them a row can be measured in.
# Two lists would drift, and the drift is exactly the defect #49 records.
