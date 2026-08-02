# Feed panel audit — what responds, what it publishes, and whether the metadata is right

Fact-gathering for [#15](https://github.com/exdsgift/tensionr/issues/15). **This document decides nothing.** It contains no
recommendation about which sources to keep, drop or add; that belongs to *"The source panel"* ([#5](https://github.com/exdsgift/tensionr/issues/5))
and to a human.

All measurements taken **2026-08-02, between 14:05 and 14:35 UTC**.

## Method and limits

- Every URL in the panel was fetched twice, at least one second apart, with the pipeline's own
  `User-Agent: tensionr_cyber_node/1.0`, redirects followed, timeout 15 s (the pipeline uses 10 s). The five that failed
  were fetched three more times each with a 20 s timeout and 2 s spacing, to separate transient from persistent failure.
- Response times are **single measurements from one residential connection in Italy**. They indicate order of magnitude,
  not a latency budget. Geo-dependent behaviour (CDN blocking, regional feed routing) cannot be ruled out from one vantage point.

### Which code and which data were measured

The ticket names `ALL_FEEDS` and `rss_metadata` in `src/fetch_gdelt.py`. **That file no longer exists.** It was replaced by
a package layout in `4a5c426` ("Refactor code structure…", 2026-07-21) and its remains deleted in `94ba01f`. The audit
therefore reads the current code, and states its references precisely:

| What the ticket calls it | Where it is now, on `origin/master` |
|---|---|
| `ALL_FEEDS` (23 URLs) | `RSS_FEEDS` — `src/tensionr/config.py:31` |
| `rss_metadata` (23 entries) | `RSS_METADATA` — `src/tensionr/config.py:58` |
| random 15-of-23 rotation | `src/tensionr/fetchers/news.py:104` — `random.sample(RSS_FEEDS, min(len(RSS_FEEDS), RSS_SAMPLE_SIZE))` |
| `fetch_rss_news()` / per-feed fetch | `fetch_rss_news()` / `_fetch_single_feed()` — `src/tensionr/fetchers/news.py` |
| `fetch_gdelt_data()` GDELT call | `fetch_gdelt_articles()` / `fetch_gdelt_timeline()` — `src/tensionr/fetchers/news.py` |
| `requirements.txt` | deleted; `pyproject.toml` + `uv.lock`, installed with `uv sync --frozen` |

The old and new literals were compared programmatically (AST parse of both files): the URL list is **identical** — same 23
URLs in the same order — and the metadata table is **identical** — same 23 entries, same values. So the liveness and
metadata findings below hold for both versions, and the rotation is unchanged.

Relevant constants, all in `src/tensionr/config.py`: `RSS_SAMPLE_SIZE = 15` (line 56), `ARTICLE_CAP = 500` (line 20),
`GDELT_QUERY = "war conflict economy military finance"` (line 28), 10 entries taken per feed per run
(`news.py`, `feed.entries[:10]`), cron `0 * * * *` (hourly) in `.github/workflows/update_data.yml`.

**Section 4 measures `data/news.json` at `origin/master` = `b45b57b`, committed 2026-08-02 12:50:57 UTC** — read with
`git show origin/master:data/news.json`. This matters: the local checkout used for this work was **654 commits / 59 days
behind**, and its copy of `news.json` was from 2026-06-04. Every corpus number in section 4 is from the current file; the
June file is cited only where it is explicitly labelled as such, for contrast.

One behavioural difference between the two pipeline versions matters for reading dates. In the deleted
`src/fetch_gdelt.py`, `seendate` for an RSS article was `datetime.now()` — **fetch time**. In
`src/tensionr/fetchers/news.py` it is the entry's `published_parsed`/`updated_parsed` — **publication time**, falling back
to now. The corpus measured in section 4 was produced by the second, so its `seendate` is publication time.

---

## 1. Liveness

Panel order is source order in `RSS_FEEDS` (`src/tensionr/config.py:31`).

| # | Feed host | HTTP | Time (s) | Redirect | `feedparser` | Entries | Newest entry (UTC) | Oldest entry (UTC) | Age of newest |
|---:|---|---:|---:|---|---|---:|---|---|---:|
| 1 | `feeds.bbci.co.uk` | 200 | 0.75 | yes (302) | yes (rss20) | 24 | 2026-08-02 11:49 | 2026-07-31 15:18 | 2.3 h |
| 2 | `www.aljazeera.net` | 200 | 0.59 | yes (302) | yes (rss20) | 25 | 2026-08-02 10:53 | 2026-08-02 08:31 | 3.2 h |
| 3 | `www.theguardian.com` | 200 | 0.86 | no | yes (rss20) | 45 | 2026-08-02 13:58 | 2026-07-28 04:00 | 0.1 h |
| 4 | `feeds.a.dj.com` | 200 | 0.51 | no | yes (rss20) | 20 | 2025-01-27 19:23 | 2025-01-24 22:56 | **552 d** |
| 5 | `www.lemonde.fr` | 200 | 0.51 | no | yes (rss20) | 20 | 2026-08-02 13:21 | 2026-08-02 03:30 | 0.8 h |
| 6 | `www.japantimes.co.jp` | 200 | 2.91 | no | yes (rss20) | 30 | 2026-08-02 12:45 | 2026-08-01 21:59 | 1.4 h |
| 7 | `www.spiegel.de` | 200 | 0.38 | no | yes (rss20) | 20 | 2026-08-02 12:36 | 2026-08-01 11:41 | 1.5 h |
| 8 | `feeds.elpais.com` | 200 | 0.87 | no | yes (rss20) | 145 | 2026-08-02 13:47 | 2026-07-13 08:24 | 0.3 h |
| 9 | `timesofindia.indiatimes.com` | 200 | 0.65 | no | yes (rss20) | 20 | 2026-08-02 13:11 | 2026-08-01 19:48 | 0.9 h |
| 10 | `www.jpost.com` | 200 | 0.33 | no | yes (rss20) | 26 | 2026-08-02 16:41 | 2026-07-01 14:16 | **−2.6 h (future)** |
| 11 | `www.straitstimes.com` | 200 | 0.35 | no | yes (rss20) | 50 | 2026-08-02 13:56 | 2026-08-01 06:51 | 0.2 h |
| 12 | `en.mercopress.com` | 200 | 0.96 | no | yes (rss20) | 10 | 2026-07-31 23:11 | 2026-07-30 18:59 | 38.9 h |
| 13 | `www.chinadaily.com.cn` | 200 | 2.08 | no | yes (rss20) | 100 | 2017-12-12 00:27 | 2017-12-10 00:50 | **3156 d** |
| 14 | `www.rt.com` | 200 | 2.65 | no | yes (rss20) | 100 | 2026-08-02 11:47 | 2026-07-26 07:39 | 2.3 h |
| 15 | `www.scmp.com` | 200 | 1.39 | yes (301→301) | yes (rss20) | 50 | 2026-08-02 14:04 | 2026-08-01 20:59 | 0.1 h |
| 16 | `www.thehindu.com` | 200 | 0.41 | no | yes (rss20) | 60 | 2026-08-02 13:25 | 2026-07-30 23:45 | 0.7 h |
| 17 | `feeds.reuters.com` | **no response** | 0.23 | — | — | — | — | — | — |
| 18 | `www.france24.com` | 200 | 0.35 | no | yes (rss20) | 22 | 2026-08-02 13:04 | 2026-08-01 14:39 | 1.1 h |
| 19 | `www.dw.com` | **404** | 0.28 | no | **no** (HTML) | 0 | — | — | — |
| 20 | `rss.nytimes.com` | 200 | 0.56 | no | yes (rss20) | 57 | 2026-08-02 13:50 | 2026-07-31 05:49 | 0.3 h |
| 21 | `www.washingtonpost.com` | **no response** | 15.30 | — | — | — | — | — | — |
| 22 | `www.cbc.ca` | **404** | 1.08 | yes (301→301) | **no** (HTML) | 0 | — | — | — |
| 23 | `www.abc.net.au` | **404** | 1.15 | no | **no** (HTML) | 0 | — | — | — |

**18 of 23 return a parseable feed. 5 return nothing usable.** Detail on those five, each confirmed over 4 attempts:

| Feed host | Failure mode | Repeated | Evidence |
|---|---|---|---|
| `feeds.reuters.com` | DNS does not resolve | 4/4 | `getaddrinfo` → `EAI_NONAME`; the host has no A record. Reuters retired its public RSS feeds; the domain is gone, not merely 404. |
| `www.dw.com` | HTTP 404 | 4/4 | Resolves (95.100.237.185), TLS fine, returns a 70 KB HTML DW error page. |
| `www.washingtonpost.com` | no HTTP response | 4/4 | Resolves (104.83.106.248), TCP/TLS connect succeeds, then 1× `Connection aborted` and 3× read timeout at 15 s and 20 s. **Cannot distinguish "feed removed" from "our client is blocked"** — no status line ever arrives. |
| `www.cbc.ca` | HTTP 404 after 2 redirects | 4/4 | `301 → http://…/world/ → 301 → https://…/world/`, then a CBC "Sorry — we can't find that page" HTML page. |
| `www.abc.net.au` | HTTP 404 | 4/4 | Body is literally the 4 bytes `gone`. |

Both pipeline versions treat any non-200 as "no articles" and log a warning, so these five contribute **silent zeros**. The
three 404s additionally reach `feedparser`, which sets `bozo` on the HTML; neither version inspects `bozo`, so a feed that
returns a valid HTML error page is indistinguishable in the logs from one that returns an empty valid feed.

**Redirects observed** (all followed successfully, all ending at HTTP 200 except CBC):

| Feed host | Configured URL | Final URL | Note |
|---|---|---|---|
| `feeds.bbci.co.uk` | `http://feeds.bbci.co.uk/news/world/rss.xml` | `https://feeds.bbci.co.uk/news/world/rss.xml` | 302, http→https only |
| `www.aljazeera.net` | `…/aljazeerarss/a7c986be-c2bd-44a7-82f1-104a5e6bb854/73d0e1b4-…` | `…/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-…` | 302 to a **different feed GUID**: the configured identifier no longer exists and is silently swapped for another. The content served is Al Jazeera's Arabic service (`الجزيرة نت`, `<language>ar</language>`). |
| `www.scmp.com` | `https://www.scmp.com/rss/91/feed` | `https://www.scmp.com/rss/91/feed/` | 301→301, https→http→https, trailing slash added |
| `www.cbc.ca` | `https://www.cbc.ca/cctoc/rss/news/world` | `https://www.cbc.ca/cctoc/rss/news/world/` | 301→301, then 404 |

Two further liveness observations that a status code does not catch:

- **`feeds.a.dj.com` (WSJ) and `www.chinadaily.com.cn` return HTTP 200 and parse cleanly, but their content is frozen.**
  WSJ's newest entry is dated 2025-01-27 (552 days old); China Daily's is 2017-12-12 (3156 days old, ~8.6 years). Any check
  based on status code or on "did we get entries" scores both as healthy.
- **`www.jpost.com` emits future-dated entries.** 6 of the 26 entries carried timestamps up to 2 h 20 min ahead of the fetch
  moment, consistent with local Israeli time being labelled as UTC/GMT in the feed. Its oldest entry (2026-07-01) is also
  an outlier 32 days behind the rest, so the feed is not date-ordered.

---

## 2. Volume

"Ingested per run" is what the pipeline actually keeps: `feed.entries[:10]`. "Implied rate at head of feed" is
10 ÷ (time span of the 10 newest entries) — the publication rate the feed is running at right now, which is the figure that
matters given the 10-entry cut. Sorted by that rate.

| Feed host | Entries per fetch | Unique URLs | Ingested per run | Span of the 10 newest | Implied rate at head | Items < 24 h | Items < 7 d |
|---|---:|---:|---:|---:|---:|---:|---:|
| `www.aljazeera.net` | 25 | 25 | 10 | 0.7 h | **369/day** | 25 | 25 |
| `www.theguardian.com` | 45 | 45 | 10 | 2.0 h | 122/day | 23 | 45 |
| `www.jpost.com` | 26 | 26 | 10 | 3.8 h | 64/day | 20 | 21 |
| `www.scmp.com` | 50 | 50 | 10 | 4.1 h | 59/day | 50 | 50 |
| `timesofindia.indiatimes.com` | 20 | 20 | 10 | 4.2 h | 57/day | 20 | 20 |
| `www.france24.com` | 22 | 22 | 10 | 4.4 h | 55/day | 22 | 22 |
| `www.straitstimes.com` | 50 | 49 | 10 | 4.4 h | 55/day | 33 | 50 |
| `www.lemonde.fr` | 20 | 20 | 10 | 5.8 h | 42/day | 20 | 20 |
| `www.thehindu.com` | 60 | 60 | 10 | 6.0 h | 40/day | 27 | 60 |
| `www.chinadaily.com.cn` | 100 | **42** | 10 | 6.3 h | 38/day (in 2017) | 0 | 0 |
| `www.japantimes.co.jp` | 30 | 30 | 10 | 6.3 h | 38/day | 30 | 30 |
| `rss.nytimes.com` | 57 | 57 | 10 | 6.7 h | 36/day | 27 | 57 |
| `feeds.elpais.com` | **145** | 145 | 10 | 6.8 h | 35/day | 83 | 138 |
| `feeds.bbci.co.uk` | 24 | 24 | 10 | 11.9 h | 20/day | 18 | 24 |
| `www.spiegel.de` | 20 | 20 | 10 | 14.9 h | 16/day | 17 | 20 |
| `feeds.a.dj.com` | 20 | 20 | 10 | 15.4 h | 16/day (in 2025) | 0 | 0 |
| `www.rt.com` | 100 | 100 | 10 | 23.2 h | 10/day | 11 | 97 |
| `en.mercopress.com` | 10 | 10 | 10 | 28.2 h | **9/day** | 0 | 10 |
| `feeds.reuters.com` | 0 | 0 | 0 | — | — | — | — |
| `www.dw.com` | 0 | 0 | 0 | — | — | — | — |
| `www.washingtonpost.com` | 0 | 0 | 0 | — | — | — | — |
| `www.cbc.ca` | 0 | 0 | 0 | — | — | — | — |
| `www.abc.net.au` | 0 | 0 | 0 | — | — | — | — |

Derived facts:

- **The spread between the fastest and slowest live feed is 41×** (Al Jazeera 369/day vs MercoPress 9/day). Every feed
  contributes the same 10 items per run regardless.
- **Feed length varies 14.5×** (145 entries at El País vs 10 at MercoPress), and every feed is truncated to 10. Al Jazeera's
  10 newest cover 42 minutes; MercoPress's cover 28 hours. On an hourly cron, Al Jazeera loses items between runs while
  MercoPress mostly re-offers items already ingested.
- **`www.chinadaily.com.cn` serves 100 entries containing only 42 distinct URLs** — 58 are exact duplicates, some appearing
  three times. `www.straitstimes.com` had 1 duplicate URL out of 50. All other feeds were duplicate-free within a fetch.
- Selection probability per run is 15/23 = **65.2%**, so a feed is sampled ~15.7 times per 24 h. Expected number of the 15
  selected feeds that actually respond is 15 × 18/23 = **11.7**, i.e. on average **3.3 of the 15 slots per run are spent on
  dead feeds**, capping realistic yield at ~117 items per run instead of the nominal 150.
- Every entry in every live feed carried a resolvable date and a `link`, so `_entry_seendate()`'s "fetch time" fallback was
  never exercised in this measurement.

---

## 3. Accuracy of the hardcoded country/language table (`RSS_METADATA`)

`RSS_METADATA` (`src/tensionr/config.py:58`, the ticket's `rss_metadata`) maps feed host → `{country, lang}`. `country` is used as `sourcecountry` and `lang` as `language` on every article, verbatim and with no fallback
other than `{"country": "Global", "lang": "English"}` for unknown domains.

Evidence columns: the feed's own `<language>` element, the feed's self-declared `<title>`, and manual inspection of the
first entry titles.

| Feed host | `country` | `lang` | Feed `<language>` | Feed self-title | Verdict |
|---|---|---|---|---|---|
| `feeds.bbci.co.uk` | United Kingdom | English | `en-gb` | BBC News | ok |
| `www.aljazeera.net` | Qatar | Arabic | `ar` | الجزيرة نت | ok (URL redirected, see §1) |
| `www.theguardian.com` | United Kingdom | English | `en-gb` | World news \| The Guardian | ok |
| `feeds.a.dj.com` | United States | English | `en-us` | WSJ.com: World News | ok |
| `www.lemonde.fr` | France | French | `fr` | International — Le Monde.fr | ok |
| `www.japantimes.co.jp` | Japan | Japanese | `en-US` | Latest articles - The Japan Times | **`lang` wrong** |
| `www.spiegel.de` | Germany | English | `de` | DER SPIEGEL - Ausland | **`lang` wrong** |
| `feeds.elpais.com` | Spain | Spanish | `es` | EL PAÍS: el periódico global | ok |
| `timesofindia.indiatimes.com` | India | English | `en-gb` | World News … Times of India | ok (content drift, see below) |
| `www.jpost.com` | Israel | English | *(none)* | JPost.com - The Jerusalem Post | ok |
| `www.straitstimes.com` | Singapore | English | `en` | The Straits Times World News | ok |
| `en.mercopress.com` | Uruguay | Spanish | `en` | MercoPress | **`lang` wrong** |
| `www.chinadaily.com.cn` | China | English | *(none)* | China Daily > China News | ok (`country` see below) |
| `www.rt.com` | Russia | Russian | `en` | RT World News | **`lang` wrong** |
| `www.scmp.com` | China | English | `en` | News - South China Morning Post | ok (`country` see below) |
| `www.thehindu.com` | India | English | `en-US` | World News Today … The Hindu | ok |
| `feeds.reuters.com` | Global | English | — | — | **`country` is not a country**; feed dead |
| `www.france24.com` | France | English | `en` | France 24 - International breaking news | ok (see conflict note) |
| `www.dw.com` | Germany | English | *(none)* | — | **unverifiable** (feed 404) |
| `rss.nytimes.com` | United States | English | `en-us` | NYT > World News | ok |
| `www.washingtonpost.com` | United States | English | *(none)* | — | **unverifiable** (no response) |
| `www.cbc.ca` | Canada | English | *(none)* | — | **unverifiable** (feed 404) |
| `www.abc.net.au` | Australia | English | *(none)* | — | **unverifiable** (feed 404) |

### The four `lang` mismatches, with the evidence

| Feed host | Table says | Feed actually publishes in | Evidence |
|---|---|---|---|
| `www.spiegel.de` | English | **German** | `<language>de</language>`; e.g. *"Indonesien: Tote und Vermisste nach Schiffsbrand vor der Insel Madura"*. The known-bad entry from the ticket, confirmed. |
| `www.japantimes.co.jp` | Japanese | **English** | `<language>en-US</language>`; The Japan Times is an English-language daily published in Tokyo. e.g. *"Japan Lower House to install security cameras in Diet building"*. |
| `www.rt.com` | Russian | **English** | `<language>en</language>`, feed titled "RT World News", URL path `/rss/news/` is the English service. e.g. *"Trump cancels planned attack on Iran"*. |
| `en.mercopress.com` | Spanish | **English** | `<language>en</language>`; the hostname's own subdomain is `en.`. e.g. *"Argentina's central bank reform bill reaches the lower house"*. |

**Net effect: the panel's declared language mix is wrong in both directions.** It claims Japanese and Russian content it
does not have, and does not declare the German content it does have. It over-states English by classifying German as
English and under-states it by classifying English as Japanese/Russian. Quantified against the live corpus in §4.

### Country-of-ownership problems, kept separate from language

| Feed host | Issue |
|---|---|
| `feeds.reuters.com` | `"Global"` is a placeholder, not a country, and it is not in `KNOWN_COUNTRIES` either. Reuters is the news division of Thomson Reuters (headquartered in Toronto, Canada) with its newsroom in London, UK. Moot in practice — the feed is dead. |
| `www.scmp.com` | Labelled `China`. The South China Morning Post is published in Hong Kong and owned by Alibaba Group. Defensible as a jurisdiction, but it collapses into one label alongside `www.chinadaily.com.cn`, which is a Beijing state-owned outlet. The two carry the same `sourcecountry` and are counted as one country in any per-country aggregate. |
| `www.france24.com` | `country: France`, `lang: English` — both correct: France 24 is French state-funded (France Médias Monde) and `/en/rss` is its English service. It is nonetheless a case where **country of ownership and language of publication diverge**, and the panel counts it under "France" together with `www.lemonde.fr`, which is French-language. |

### Where country and language conflict in a way that matters for a "balanced panel" claim

These are not errors in the table; they are facts about the panel that a per-country count hides.

| Country label | Feeds under it | Languages actually published |
|---|---|---|
| France | `www.lemonde.fr`, `www.france24.com` | French, English |
| China | `www.chinadaily.com.cn` (Beijing, state-owned), `www.scmp.com` (Hong Kong, Alibaba-owned) | English, English |
| India | `timesofindia.indiatimes.com`, `www.thehindu.com` | English, English |
| Germany | `www.spiegel.de`, `www.dw.com` (dead) | German, *(unverifiable)* |
| United Kingdom | `feeds.bbci.co.uk`, `www.theguardian.com` | English, English |
| United States | `feeds.a.dj.com` (frozen), `rss.nytimes.com`, `www.washingtonpost.com` (dead) | English |

- **The table declares 16 distinct `country` values across 23 feeds — 15 real countries plus `"Global"` — and 6 distinct
  `lang` values, of which `English` is used for 17 of the 23 feeds. Only 12 country labels appear in the live corpus.**
- Of the 18 live feeds, **14 publish in English**. The only non-English feeds that respond are Al Jazeera (Arabic),
  Le Monde (French), El País (Spanish) and Der Spiegel (German) — **4 feeds, 4 languages**.
- Every feed labelled with a non-European, non-anglophone country (`Japan`, `China`, `Israel`, `Singapore`, `India`,
  `Russia`, `Uruguay`, `Qatar`) publishes in English except Al Jazeera. So the country spread and the language spread are
  close to independent: adding countries has not added languages.
- Two feeds are not the feeds their URL implies. `www.chinadaily.com.cn/rss/world_rss.xml` self-titles
  **"China Daily > China News"**, not a world feed. `timesofindia.indiatimes.com/rssfeeds/296589292.cms` self-titles as a
  world-news feed but its 20 entries were mostly lifestyle and science items (*"You can make yourselves 'luckier': Science-backed
  tips to rewire your brain for luck"*, *"100-million-year-old ichthyosaur's last meal found"*), with 1 of the first 5
  entries being international news. `www.japantimes.co.jp/feed/` self-titles **"Latest articles"** — all sections, not world news.

---

## 4. Actual composition of the corpus on disk

`data/news.json` at `origin/master` `b45b57b` (2026-08-02 12:50 UTC). 500 articles, 500 distinct URLs, no duplicates.
Every article carries all 9 fields (`url`, `title`, `domain`, `seendate`, `source`, `sourcecountry`, `language`,
`narrative_emotion`, `manipulation_score`).

### By `source`

| `source` | Articles | Share |
|---|---:|---:|
| `rss` | 500 | 100.0% |
| `gdelt` | 0 | 0.0% |

**The corpus is entirely RSS. Not one GDELT article is present.** For comparison, the local checkout's 59-day-old copy of
the same file held 498 RSS and **2** GDELT articles (0.4%) out of 500.

### By `domain`

| Domain | Articles | Share |
|---|---:|---:|
| `www.aljazeera.net` | 73 | 14.6% |
| `www.scmp.com` | 52 | 10.4% |
| `timesofindia.indiatimes.com` | 50 | 10.0% |
| `www.straitstimes.com` | 47 | 9.4% |
| `www.jpost.com` | 45 | 9.0% |
| `www.lemonde.fr` | 45 | 9.0% |
| `www.france24.com` | 38 | 7.6% |
| `www.thehindu.com` | 29 | 5.8% |
| `www.japantimes.co.jp` | 27 | 5.4% |
| `www.spiegel.de` | 23 | 4.6% |
| `rss.nytimes.com` | 20 | 4.0% |
| `feeds.bbci.co.uk` | 18 | 3.6% |
| `feeds.elpais.com` | 16 | 3.2% |
| `www.rt.com` | 14 | 2.8% |
| `www.theguardian.com` | 3 | 0.6% |
| `feeds.a.dj.com` | 0 | 0.0% |
| `en.mercopress.com` | 0 | 0.0% |
| `www.chinadaily.com.cn` | 0 | 0.0% |
| `feeds.reuters.com` | 0 | 0.0% |
| `www.dw.com` | 0 | 0.0% |
| `www.washingtonpost.com` | 0 | 0.0% |
| `www.cbc.ca` | 0 | 0.0% |
| `www.abc.net.au` | 0 | 0.0% |

**15 of the 23 panel feeds appear; 8 contribute nothing.** Five of those eight are the dead feeds from §1. The other three —
`feeds.a.dj.com`, `www.chinadaily.com.cn`, `en.mercopress.com` — respond with HTTP 200 and are ingested, but are then
eliminated downstream: articles are sorted by `seendate` (publication time) and cut at 500, and the corpus window is only
31 hours wide, so WSJ's 2025 items, China Daily's 2017 items and MercoPress's 39-hour-old items all fall outside it. **A
feed that responds perfectly can still contribute zero without any error being logged.**

Top domain 14.6% against 0.6% for the Guardian is a **24× spread** among feeds that do appear.

### By `sourcecountry`

| `sourcecountry` | Articles | Share |
|---|---:|---:|
| France | 83 | 16.6% |
| India | 79 | 15.8% |
| Qatar | 73 | 14.6% |
| China | 52 | 10.4% |
| Singapore | 47 | 9.4% |
| Israel | 45 | 9.0% |
| Japan | 27 | 5.4% |
| Germany | 23 | 4.6% |
| United Kingdom | 21 | 4.2% |
| United States | 20 | 4.0% |
| Spain | 16 | 3.2% |
| Russia | 14 | 2.8% |

12 country labels of the 12 claimable ones (`Canada`, `Australia`, `Uruguay` and `Global` are absent because their feeds
contributed nothing). The two most-represented countries, France (16.6%) and India (15.8%), owe their position to having
two live feeds each; the United States has three feeds in the panel and 4.0% of the corpus, because two of the three are
dead or frozen.

### By `language` — as tagged versus as actually published

Left-hand columns are the values in the file. Right-hand columns re-assign each article to the language its feed actually
publishes in, per §3.

| Language | As tagged | Share | Observed | Share | Delta |
|---|---:|---:|---:|---:|---:|
| English | 325 | 65.0% | 343 | 68.6% | +18 |
| Arabic | 73 | 14.6% | 73 | 14.6% | 0 |
| French | 45 | 9.0% | 45 | 9.0% | 0 |
| Japanese | 27 | 5.4% | **0** | **0.0%** | −27 |
| Spanish | 16 | 3.2% | 16 | 3.2% | 0 |
| Russian | 14 | 2.8% | **0** | **0.0%** | −14 |
| German | **0** | **0.0%** | 23 | 4.6% | +23 |

- **64 of 500 articles (12.8%) carry a wrong `language` value.**
- The file reports **6 languages**; the corpus contains **5** (English, Arabic, French, German, Spanish).
- The 27 articles tagged `Japanese` and the 14 tagged `Russian` are all English-language text. The 23 German articles are
  all tagged `English`.
- Corrected, the corpus is **68.6% English**, and its entire non-English content comes from **4 feeds**.

Outlets per language, after correction:

| Language | Outlets | Articles | Which |
|---|---:|---:|---|
| English | 11 | 343 | SCMP 52, Times of India 50, Straits Times 47, JPost 45, France 24 38, The Hindu 29, Japan Times 27, NYT 20, BBC 18, RT 14, Guardian 3 |
| Arabic | **1** | 73 | Al Jazeera 73 |
| French | **1** | 45 | Le Monde 45 |
| German | **1** | 23 | Der Spiegel 23 |
| Spanish | **1** | 16 | El País 16 |

### Cross-check against the earlier report on this corpus

An earlier agent reported the same shape but may have measured the stale June file. Checked against
`origin/master:data/news.json` @ `b45b57b`:

| Earlier claim | Status on current data | Measured value |
|---|---|---|
| 5 languages, not 9 | **confirmed** | 5 (English, Arabic, French, German, Spanish); the file *labels* 6 |
| English ~68% | **confirmed** | 68.6% (343/500) after correction; 65.0% as tagged |
| Arabic ~16% | **corrected** | **14.6%** (73/500), not ~16% |
| then French, Spanish, German | **order corrected** | French 9.0%, **German 4.6%**, Spanish 3.2% — German is ahead of Spanish |
| exactly one outlet per non-English language | **confirmed** | 1 each for Arabic, French, German, Spanish (table above) |
| `lang` wrong for 4 of 18 domains | **confirmed** | Spiegel, Japan Times, RT, MercoPress — 4 of the 18 responding domains; 64/500 articles affected |

### Date range of `seendate`

| Day (UTC) | Articles |
|---|---:|
| 2026-08-01 | 312 |
| 2026-08-02 | 188 |

Range **2026-08-01 07:05:00 → 2026-08-02 14:59:34 UTC**, i.e. a span of **1.33 days**. With `ARTICLE_CAP = 500` and the
measured yield, the rolling window holds roughly **31 hours of news** — that is the entire history available in
`news.json` at any moment.

For contrast, the 59-day-old local copy spanned 2026-06-03 00:22 → 2026-06-04 09:39 (1.39 days), but under the old
fetch-time `seendate`: 498 RSS articles shared only **1–8 distinct `seendate` values per domain** (e.g. all 10
`feeds.a.dj.com` articles bore one identical timestamp), because every article in a batch was stamped with the moment of
the fetch. Any date-based analysis of archived snapshots produced before the refactor is measuring fetch times, not
publication times.

---

## 5. GDELT reachability

The pipeline calls `https://api.gdeltproject.org/api/v2/doc/doc` twice per run: `mode=ArtList` with
`query=war conflict economy military finance`, `maxrecords=50`, `format=json`; and `mode=TimelineVol` with
`query=war conflict economy`.

**Result: not measurable today. 5 of 5 attempts returned HTTP 429.**

| Attempt | Mode | Spacing before | HTTP | Time | Body |
|---:|---|---|---:|---:|---|
| 1 | `ArtList` | — | 429 | 12.6 s | 444-byte throttle notice |
| 2 | `TimelineVol` | 25 s | 429 | 16.2 s | identical 444-byte notice |
| 3 | `ArtList` | ~2 min | 429 | 10.8 s | identical |
| 4 | `ArtList` | 60 s | 429 | 11.3 s | identical |
| 5 | `ArtList` | 60 s | 429 | 9.2 s | identical |

The body is always the same plain-text string, never JSON:

> Please limit requests to one every 5 seconds or contact kalev.leetaru5@gmail.com for larger queries. All high-traffic
> users should switch to our ngrams dataset […]

So, honestly stated:

- **The endpoint is reachable** — DNS, TLS and HTTP all work, and the server answers in ~10 s.
- **The query could not be executed**, at any spacing tried up to 60 s. Probing was deliberately stopped at 5 attempts
  rather than escalated (see below).
- **Record count and field population are therefore unmeasured here.** They are not unknown to the project: the agent
  research recorded in [#2](https://github.com/exdsgift/tensionr/issues/2) reports that `mode=ArtList` returns exactly 8
  keys — `url`, `url_mobile`, `title`, `seendate`, `socialimage`, `domain`, `language`, `sourcecountry` — with a hard cap of
  250 records and no pagination, and that at 20–25 s spacing roughly half of all calls still fail. That finding is
  consistent with what happened here but was **not independently re-confirmed by this audit**, and #2 itself is flagged as
  not yet human-verified. Re-probing was not attempted beyond 5 calls precisely because #2 already characterises the
  throttling and further hammering would add nothing.
- One corroborating on-disk trace of the 8-field shape does exist: the 2 GDELT articles in the 59-day-old local
  `news.json` are the only articles in that file carrying `url_mobile` and `socialimage`.
- Behaviour under throttling differs between pipeline versions. `src/fetch_gdelt.py` does not retry: a single 429 yields
  `[]` and the run continues. `src/tensionr/http_client.py` treats 429 as retryable with 3 attempts, exponential backoff
  and `Retry-After` support. Neither surfaces sustained GDELT failure anywhere in the published data — and §4 shows the
  live corpus contains 0 GDELT articles.

---

## Findings a human should see before deciding the panel

Feeds probed live on 2026-08-02 14:05–14:35 UTC. Corpus measured at `origin/master` `b45b57b` (2026-08-02 12:50 UTC).
Code references are `src/tensionr/config.py` and `src/tensionr/fetchers/news.py`.

1. **5 of 23 feeds return nothing usable**, each confirmed over 4 attempts: `feeds.reuters.com` (DNS gone),
   `www.dw.com` (404), `www.cbc.ca` (404 after 2 redirects), `www.abc.net.au` (404, body = `gone`), and
   `www.washingtonpost.com` (TLS connects, no HTTP response — indistinguishable from a client block at 15 s and 20 s).
2. **3 more return HTTP 200 and contribute zero articles anyway.** `feeds.a.dj.com` is frozen at 2025-01-27 (552 days),
   `www.chinadaily.com.cn` at 2017-12-12 (3156 days), and `en.mercopress.com` publishes ~9 items/day so its newest item is
   older than the 31-hour corpus window. **8 of 23 panel entries are therefore inert; only 15 appear on disk.** Status code
   and entry count both score all three as healthy.
3. **The corpus contains 0 GDELT articles (0.0% of 500).** The DOC 2.0 API returned HTTP 429 on 5 of 5 attempts spaced up to
   60 s, so this audit could not execute the pipeline's query at all. The panel is, in practice, an RSS-only panel.
4. **64 of 500 articles (12.8%) carry a wrong `language`.** Four `RSS_METADATA` entries are wrong:
   `www.spiegel.de` (says English, publishes German), `www.japantimes.co.jp` (says Japanese, publishes English),
   `www.rt.com` (says Russian, publishes English), `en.mercopress.com` (says Spanish, publishes English).
   The file claims 6 languages and 27 Japanese + 14 Russian articles; it contains 5 languages and **zero** Japanese or
   Russian text. This confirms the earlier report's "5 languages, not 9" and "4 of 18 domains mislabelled" on current data,
   with two corrections: Arabic is 14.6% (not ~16%) and German (4.6%) outranks Spanish (3.2%).
5. **Country spread and language spread are close to independent.** 15 countries plus `"Global"` are declared, but `lang`
   is `English` for 17 of the 23 entries, 14 of the 18 live feeds publish in English, and corrected the corpus is 68.6%
   English. All non-English content comes from **4 feeds — exactly one outlet per non-English language** (Al Jazeera →
   Arabic 73, Le Monde → French 45, Der Spiegel → German 23, El País → Spanish 16), against 11 English-language outlets.
   Every non-anglophone country label except Qatar is filled by an English-language outlet. Adding countries has not added
   languages, and no non-English language has a second voice to disagree with.
6. **Volume is not close to balanced, and the panel does nothing to correct it.** Live publication rates span 41×
   (Al Jazeera 369/day, MercoPress 9/day) while every feed is truncated to the same 10 items per run. On disk the spread is
   24× (Al Jazeera 14.6% vs Guardian 0.6%).
7. **`"Global"` is used as a country value** for `feeds.reuters.com`, and is also the default for any unrecognised domain.
   It is not a country and is not in `KNOWN_COUNTRIES`.
8. **Two country labels merge editorially distinct outlets.** `China` covers both Beijing state-owned China Daily and
   Hong-Kong-based, Alibaba-owned SCMP; `France` covers French-language Le Monde and English-language France 24. Any
   per-country aggregate treats each pair as one voice.
9. **Three feeds are not what their URL says.** `chinadaily.com.cn/rss/world_rss.xml` self-titles "China Daily > China
   News"; `japantimes.co.jp/feed/` is "Latest articles", all sections; `timesofindia…/296589292.cms` returned mostly
   lifestyle and science items despite a world-news title.
10. **Two data-quality defects that will contaminate any time-based measure.** `www.jpost.com` emits entries timestamped up
    to 2 h 20 min in the future (local Israeli time labelled as UTC), and `www.chinadaily.com.cn` serves 100 entries
    containing only 42 distinct URLs.
11. **The configured Al Jazeera URL no longer exists.** It 302-redirects to a different feed GUID. The content served is
    still Al Jazeera's Arabic service, but the panel is pinned to an identifier the publisher has retired and the
    substitution is silent.
12. **`news.json` holds ~31 hours of news** (measured span 1.33 days, 500-article cap). That is the whole corpus at any
    instant — relevant to #1's note that anomaly detection needs a historical baseline that does not exist yet.
13. **The pipeline cannot tell any of this apart.** Non-200 becomes an empty list and a log line; `feedparser`'s `bozo` flag
    is never inspected, so an HTML 404 page reads the same as an empty feed; a feed frozen for eight years reads as
    perfectly healthy. Nothing about feed health reaches the published data.
14. **Two spent slots per run, structurally.** With 15 of 23 sampled at random and 5 hosts dead, on average 3.3 of the 15
    slots per run fetch nothing, capping yield at ~117 items instead of 150.
