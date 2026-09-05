"""Central configuration for the story engine: credentials and tuning constants.

Everything the v1 pipeline needed - the RSS panel and its metadata, the country and
ticker lists, the military callsign prefixes, the GDELT DOC API queries, the archive
paths - went with it in #80. The feed panel is not lost: it is in git history and its
audit is `docs/research/feed-panel-audit.md`, which is the document that matters,
since the panel it describes is measured rather than merely listed.
"""

import os

from dotenv import load_dotenv

load_dotenv()

HF_TOKEN: str | None = os.getenv("HF_TOKEN")
HF_BATCH_SIZE = 32

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
