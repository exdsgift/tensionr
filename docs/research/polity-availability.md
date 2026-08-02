# Polity availability per language: which polities publish in GDELT, and where a two-polity quorum is possible

Evidence for [#21](https://github.com/exdsgift/tensionr/issues/21), applying the **polity of
publication** axis (Decision 1 on [#20](https://github.com/exdsgift/tensionr/issues/20)) and the
**pool with a two-polity quorum** (Decision 2 on the same ticket).

**This document does not choose the pool.** It measures, per language, which polities publish into
GDELT with measurable volume, which outlets carry that volume for each polity, and whether any polity
is represented by more than one outlet. Where a two-polity quorum is impossible that is stated as a
finding. No outlet is recommended for adoption and no pool is proposed.

Measured against `origin/master` = `ff9a706`. No project file was modified; this document is the only
addition.

---

## 0. Correction to the ticket's premise, and what that cost

The ticket describes this as cheap re-analysis of the census delivered on
[#17](https://github.com/exdsgift/tensionr/issues/17). Two things made that impossible:

1. **The #17 raw census does not exist.** Only the markdown document was committed on
   `research/panel-candidates`; the 215,936-record dataset was not preserved. There is nothing to
   re-read.
2. **The #17 document's domain selection is biased for this purpose, by construction.** It was
   assembled to answer the *state-aligned vs independent* question, so it tabulates volume for the
   outlets that axis nominated. The polity axis needs the **highest-volume domains per language
   regardless of alignment**, which that document records only incidentally.

So this is a fresh measurement pass over `gsg_docembed` — but a much cheaper one in memory than #17's,
because it keeps only an aggregate histogram (see §1). The consequence to keep in mind while reading:
**the numbers here are not comparable to #17's numbers**. They are a different day, and §2.4 shows the
day matters by about 70%.

---

## 1. Method

### 1.1 A streaming histogram, not a stored census

Source: `http://data.gdeltproject.org/gdeltv3/gsg_docembed/YYYYMMDDHHMMSS.gsg.docembed.json.gz`,
15-minute buckets. Each record is one article with `date`, `url`, `lang`, `title`, `model` (`USEv4`)
and a 512-float `docembed`.

Each slot was downloaded to memory, decompressed, parsed, folded into aggregates, and **discarded
before the next slot was fetched**. Nothing but the aggregates survived a slot. The aggregates are:

- `(host, lang) → record count`
- `host → number of slots in which the host appeared at all` (the intermittency measure, §2.5)
- `lang → number of slots in which the language appeared at all`

1,351 MB of gzipped payload passed through memory across the two windows; peak retained state was a
few megabytes of counters. **The embeddings were never decoded** — see §1.2.

The **DOC 2.0 API was not used**, per the ticket and per #2 / #15: it returned HTTP 429 on five of
five attempts from this project.

### 1.2 Parse fidelity, measured and reported as a number

#17 records a reproduction trap worth repeating: `gsg_docembed` separates fields with `", "` — a
**space after the colon** — so a regex written without the space matches nothing and yields a silent
zero on a perfectly successful 8–13 MB download. That is the same failure class as the Frontpage
Graph returning 200 OK with an empty payload, and it is why fidelity is reported here as a number
rather than assumed.

This run used JSON parsing, not a regex, with a deliberate optimisation and a validation of it:

- **Fast path.** Each line is truncated at the first occurrence of `"title":` and the prefix is closed
  with `}`, yielding `{"date":…, "url":…, "lang":…}`. This is parsed with `json.loads`. It never
  touches the `title` field (whose escaping caused #17's 0.04% loss) and never decodes the 512-float
  `docembed`, which is the bulk of the payload. Measured 18× faster than parsing the whole line.
- **Fallback.** Any line the fast path fails on is re-parsed in full with `json.loads`.
- **Cross-validation.** On a deterministic 0.5% sample, the fast path's `(url, lang)` was compared
  against full-JSON parsing of the same line.

| | Window A | Window B |
|---|---:|---:|
| Lines seen | 372,499 | 94,254 |
| Parsed by the fast path | 372,499 | 94,254 |
| Needed the full-JSON fallback | 0 | 0 |
| **Lost (unparsable)** | **0** | **0** |
| **Parse fidelity** | **100.0000%** | **100.0000%** |
| Fast-path vs full-JSON agreement | **1,885 / 1,885** | **501 / 501** |

**Parse fidelity is 100.0000% on 466,753 lines, with 2,386 lines independently cross-validated and
zero disagreements.** #17's 99.96% was an artefact of its regex, not a property of the data: the
files parse completely as JSON.

The remaining silent-zero risk is *not* parsing but **host extraction**. Volume per outlet is the
count of records whose URL netloc equals the domain or ends with `"." + domain`, after stripping a
leading `www.`, any userinfo, and any port. Subdomain aggregation matters enormously and a host-exact
match would report many outlets as absent: Xinhua appears only as `english.news.cn` / `news.cn`,
Liberty Times only as `news.ltn.com.tw`, Al-Ahram only as `gate.ahram.org.eg`, Sputnik Serbia only as
`sputnikportal.rs`. **Every host in this document is reported at the granularity GDELT emits**, and
where a publisher spans several subdomains that is stated in the row.

### 1.3 The windows, and what they bias

Two windows, both **weekdays**, chosen deliberately because #17's two windows were both
weekend-adjacent and it flagged that as the weakest part of its evidence:

| | Window A | Window B |
|---|---|---|
| Span (UTC) | **2026-07-29 00:00 → 23:45** | 2026-07-30 00:00 → 23:00 |
| Day | **Wednesday** | Thursday |
| Sampling | **every** 15-minute slot — a complete census | 1 slot per hour |
| Slots requested / retrieved | 96 / **96**, 0 errors | 24 / **24**, 0 errors |
| Records | **372,499** | 94,254 |
| Gzipped payload streamed | 1,078 MB | 273 MB |
| Distinct hosts | 13,648 | 7,949 |

**Window A is the primary evidence**: every slot in the day was retrieved, so its counts are exact
records-per-day for 2026-07-29. **Window B is a second, independent day at one-quarter sampling** and
is used only as a presence check — its raw (un-multiplied) counts appear in the tables as `B=` so that
a domain present on Wednesday and absent on Thursday is visible. Window B counts are **not** scaled
up, to avoid inventing precision.

**What this choice biases, stated plainly:**

- **Two consecutive midweek days in late July.** Northern-hemisphere summer, parliamentary recess in
  much of Europe, and no major scheduled event. Seasonal and news-cycle effects are unmeasured.
- **Adjacent days are correlated.** A story running across 29–30 July inflates both windows together.
  Window B is therefore a weaker independent check than a window a week apart would have been; it was
  chosen to isolate weekday-vs-weekend against #17 rather than to bound week-to-week variance.
- **No weekend window of my own.** The weekday/weekend comparison in §2.4 is against #17's reported
  totals, i.e. across a different measurement run. It is a strong signal (the gap is ~70%) but it is
  not a within-run comparison.
- **No historical depth.** `gsg_docembed` archives back to 2020-01-01; none of it was sampled. "Has
  this outlet been monitored continuously" is unanswered for every row in this document.

### 1.4 What "polity of publication" is sourced to, and what it is not

The axis requires two facts per domain, kept distinct:

- **Polity of publication** — the jurisdiction the outlet publishes *from*: where the publishing
  entity sits and under whose law and media environment it operates.
- **Country of ownership** — where the controlling owner sits.

These differ in real cases and the table in §5 records both, with a **citable source per entry**.
The primary source used is the outlet's **own imprint / about / contact / legal-notice page**, which
is the appropriate primary source for polity of publication (and in the German-speaking market is a
legal requirement). Where that yielded nothing the cell says **"source not obtained"** and the row is
explicitly not usable as evidence for a label.

`RSS_METADATA` in `src/tensionr/config.py` was **not** inherited from. Per #15 it conflates country of
publication with country of ownership and is wrong on 4 of 23 entries; #17 confirmed those four
independently against GDELT's own language detection. Nothing in §5 derives from it.

**ccTLD is not treated as a source.** A `.de` domain is corroboration, never evidence: `dhnet.be`,
`vecernji.ba` and `sputnikportal.rs` are exactly the cases where the ccTLD names the polity of
publication correctly while the controlling owner sits in another state, and `boerse-express.com`,
`mignews.com` and `obozrevatel.com` are cases where a generic TLD hides the polity entirely.

### 1.5 What this document does not measure

The five that most change how the numbers below should be read. **The full list of 16 declared gaps is
§6** — this is the short version, up front, because this project has been damaged by numbers without a
referent:

- **Cluster co-occurrence is not measured.** As in #17: publication volume is necessary for a story
  to be jointly covered and is not sufficient. #2 measured that only ~15–20% of monitored articles
  pick up any similarity edge. **Nobody has measured how often two specific polities land in the same
  story cluster** — that is the number the quorum rule actually depends on, and it still does not
  exist. Every volume figure here is an upper bound on quorum participation.
- **Two adjacent midweek days.** See §1.3.
- **Machine-translation quality inside `gsg_docembed` is invisible** and unmeasurable from these
  files. Non-English titles are embedded from GDELT's own translation.
- **Ownership chains were not traced through registries.** Company registries, RSF's Media Ownership
  Monitor and US FARA filings were not consulted. Where ownership is asserted it is sourced to
  self-disclosure, and where self-disclosure is silent the cell says so.
- **No editorial or press-freedom assessment is made anywhere in this document.** The axis is
  deliberately a factual one. Where a press-freedom source is quoted it is to establish an
  institutional fact (e.g. that an agency is state-established), never to rank an outlet.

---

## 2. Findings that apply to every language

These five shape every table in §3 and are more consequential than any individual language.

### 2.1 About two-thirds of GDELT's highest-volume hosts are not news publishers

This is the ticket's question about how much of GDELT's volume is unusable, and the answer is: most of
the top of it.

The top 100 hosts of window A carry 71,150 of 372,499 records = **19.1% of all volume**. Classifying
each of those 100 hosts by whether it has an identifiable editorial home:

| Class | Hosts | Records/day | Share of top-100 volume |
|---|---:|---:|---:|
| **Identifiable news publisher** | 46 | 22,733 | **32.0%** |
| Aggregator / portal / UGC platform | 26 | 22,367 | 31.4% |
| Content farm, stale archive, or no identifiable editorial home | 10 | 13,386 | 18.8% |
| Real publisher, but not a news outlet | 18 | 12,664 | 17.8% |
| **Not an identifiable news publisher (sum of the three)** | **54** | **48,417** | **68.0%** |

**68% of the volume in GDELT's top 100 hosts is unusable for this purpose.** The classification is
mine and the boundary cases are named below so the figure can be recomputed under a different rule;
moving the four most arguable rows (`forbes.com`, `christianpost.com`, `moneycontrol.com`,
`boredpanda.com`, 2,209 records combined) into the news column lowers it to **64.9%**. It does not
approach a majority under any reading.

The eight highest-volume hosts in the whole census, with what they actually are:

| Rank | Host | Records/day | Slots present | What it is |
|---:|---|---:|---:|---|
| 1 | `zazoom.it` | 2,901 | 66/96 | Italian aggregator; republishes other outlets' items |
| 2 | `quicknews-africa.net` | 2,639 | **96/96** | Content farm. Default WordPress "Newsmag" theme; footer reads "Newsmag is your news, entertainment, music fashion website"; contact address is the theme's **placeholder** `contact@yoursite.com`; copyright "© SGA@2025"; body copy is republished **News Agency of Nigeria** wire dated 2015–2022 interleaved with 2026 items. No named editor, no company, no address |
| 3 | `whatweekly.com` | 2,415 | **96/96** | A **dead archive**. Its own front page: *"What Weekly was an online magazine celebrating Baltimore's creative renaissance. This site is preserved as an archive of that moment in time."* GDELT is re-crawling a closed arts magazine and emitting it as current news, in every slot of the day |
| 4 | `digbycourier.ca` | 1,840 | **96/96** | Content farm on the WordPress 7.0.2 / `td-` theme, generic SEO description, no masthead. Not the editorial operation the name implies |
| 5 | `northernpen.ca` | 1,753 | **96/96** | Same stack, page title literally `Home`, no masthead |
| 6 | `tnp.no` | 1,705 | 82/96 | "The Nordic Page", English-language, Norway. Footer copyright **2017** |
| 7 | `haberler.com` | 1,673 | 88/96 | Turkish aggregator |
| 8 | `baijiahao.baidu.com` | 1,601 | **96/96** | Baidu's user-publishing platform — UGC, not an outlet |

Two structural observations follow, and they matter more than the individual sites:

- **Presence in all 96 slots is an anti-signal, without exception.** Exactly **11** hosts appear in
  every one of the day's 96 slots, and **not one of them is a news publisher with an editorial home**:
  `quicknews-africa.net` (2,639), `whatweekly.com` (2,415), `digbycourier.ca` (1,840),
  `northernpen.ca` (1,753), `baijiahao.baidu.com` (1,601), `sublimemagazine.com` (1,305),
  `blog.udn.com` (927), `finance.yahoo.com` (860), `yahoo.com` (816), `51.ca` (494),
  `link.springer.com` (483). Real newsrooms have news cycles; automated republishing does not.
  **Perfect liveness is a reason to inspect a domain, not a quality signal** — and it means the pool
  cannot use continuous presence as a health criterion for admitting an outlet.
- **At least three of these farms share one operator's fingerprint.** `dailypolitical.com`,
  `tickerreport.com` and `themarketsdaily.com` all run WordPress 6.9.5, all carry the description
  template `"View News at <Site Name>"`, and all carry `© 2018-2026` in the same footer markup —
  1,989 records/day from what is very likely one algorithmic stock-summary operation presenting as
  three publications. A pool built on volume alone could admit all three as "three sources".

Others worth naming because they show the *kinds* of thing GDELT counts as news: `unitaid.eu`
(1,294/day — a global health financing agency's press releases), `link.springer.com` (483 — an
academic publisher), `prnewswire.com` (604 — a press-release wire),
`keskustelu.kauppalehti.fi` (443 — a Finnish **discussion forum**), `blog.udn.com` (927 — a Taiwanese
**blog host**, and the single largest `ChineseT` "host" and largest `Japanese` "host" in the census),
`klrc.com` (309 — a Christian-music radio station in Arkansas), `eichlernetwork.com` (1,008 — a
mid-century-modern **architecture and real-estate** magazine), `lolwot.com` (563 — celebrity net-worth
listicles), `tvguide.co.uk` (564 — TV listings), `investegate.co.uk` (450 — regulatory filings).

**Consequence for the pool.** Any per-language ranking by raw volume puts non-journalism at the top.
Every language table in §3 therefore names the aggregators and farms it is excluding, with the reason,
rather than silently dropping them. This is also the strongest argument in this document for the
quorum being defined over **polities** rather than outlets: a polity has an editorial home by
definition; a high-volume host may not.

### 2.2 GDELT's language tags split languages along political lines in at least four places

The ticket asks whether the `Chinese` / `ChineseT` split recurs. It does — three more times, and in
each case the split runs along a state boundary rather than a purely linguistic one. Window A:

| GDELT language values | Records/day | The boundary the split follows |
|---|---:|---|
| `Chinese` / `ChineseT` | 15,040 / 6,008 | Simplified vs traditional script — in practice PRC + Singapore + Malaysia on one side, Taiwan + Hong Kong + diaspora on the other |
| `SERBIAN` / `CROATIAN` / `BOSNIAN` | 2,854 / 2,087 / 628 | One Serbo-Croatian dialect continuum, cut three ways along the borders of Serbia, Croatia and Bosnia-Herzegovina |
| `INDONESIAN` / `MALAY` | 7,669 / 410 | One Malay language, cut along the Indonesia / Malaysia border |
| `URDU` / `HINDI` | 452 / **3** | Hindustani, cut along the Partition line — and one side of the cut is empty (§3.16) |

**This is useful rather than an obstacle, exactly as #20 anticipated** — GDELT is pre-partitioning
some languages by polity for free, which is the axis the pool wants. But it must be handled with two
cautions, both measured:

**Caution 1 — the tag correlates with polity, it does not equal it.** In the Serbo-Croatian case
the correlation is strong but leaks in every direction, and Bosnia is the biggest victim:

| Host | Polity | `SERBIAN` | `CROATIAN` | `BOSNIAN` |
|---|---|---:|---:|---:|
| `avaz.ba` (Dnevni Avaz) | Bosnia-Herzegovina | 11 | **72** | **76** |
| `oslobodjenje.ba` | Bosnia-Herzegovina | 10 | 37 | 29 |
| `klix.ba` | Bosnia-Herzegovina | 3 | 33 | 42 |
| `naslovi.net` (aggregator) | Serbia | **357** | 16 | 52 |
| `index.hr` | Croatia | — | **751** | 21 |
| `tanjug.rs` | Serbia | **129** | 5 | 40 |
| `rtcg.me` | Montenegro | 16 | 8 | 25 |

A Bosnian outlet is scattered across all three values, so **filtering `lang == "BOSNIAN"` does not
retrieve Bosnian publishers and filtering `lang == "CROATIAN"` returns Bosnian ones**. Any pool using
these tags must select on the sourced domain-to-polity table (§5) and treat `lang` as a coarse
pre-filter only. The same caution applies at the edges of the Chinese split (`cfi.net.cn`, a PRC
financial site, emits 748 `Chinese` and 37 `ChineseT`) and of the Malay split (14 Indonesian hosts
emit exactly 1 `MALAY` record each — classifier bleed, not Malaysian publishing).

**Caution 2 — treating the split as one language changes the verdict, in both directions.** For
Chinese, merging the two values adds Taiwan and Hong Kong to the PRC and makes a quorum trivially
available; but as §3.5 shows, **each value separately already clears a two-polity quorum on its own**,
which was not true in #17's data. For Malay/Indonesian, merging is what creates the quorum: separately,
`INDONESIAN` is effectively one polity (§3.14).

### 2.3 The polity axis is available in far more languages than the state-aligned axis was

The single largest substantive result. #17 found no adversarial pair in German, Russian, Japanese,
Persian and Hindi, and called French and Portuguese marginal. Under the polity axis, **German,
Russian, French and Portuguese all clear a two-polity quorum comfortably**, and they do so for a
structural reason: languages do not coincide with states, so a second polity almost always exists
wherever a language has any real volume. Specifically:

- **German** gains Austria (6 outlets, 88–226/day) and Switzerland (2 above the cut, 4 in total) — §3.3.
- **Russian** gains **Ukraine** (7 Russian-language outlets, 60–199/day), plus Belarus and Azerbaijan
  (2 each), Kyrgyzstan and Israel — §3.6. Russia vs Ukraine is the sharpest interest divergence
  available in any language in this document, and it exists in GDELT at volume — which is precisely
  what Russian *exile* media did not.
- **French** gains Belgium (3 outlets but only 3 publishers of 4 hosts), Senegal (4), Canada (2),
  Luxembourg, Switzerland and Vietnam (1 each) — §3.4.
- **Portuguese** gains Portugal (7 outlets) against Brazil — §3.8.

Conversely, three languages **lose** their #17 pair or gain nothing: Japanese and Hebrew have exactly
one polity each, and Ukrainian has one (its second polity is reachable only through the `RUSSIAN` tag).
The axis is not uniformly more permissive — it is differently shaped.

### 2.4 A weekday carries about 70% more volume than the weekend day #17 measured

| | Records in a full 24h census |
|---|---:|
| #17 window 1 — 2026-08-01 14:15 → 2026-08-02 14:00 (Sat→Sun) | 215,936 |
| **This window A — 2026-07-29 (Wednesday)** | **372,499** |
| Ratio | **1.73×** |

Distinct hosts rose from 10,554 to 13,648 and the percentiles moved with it (p50 6→9, p90 45→60,
p99 181→263; hosts at ≥100/day 314→660). **No per-outlet number in #17 should be compared with a
per-outlet number here**, and any volume floor chosen against #17's distribution is calibrated to a
weekend. This also means #17's zero readings are the weakest of its findings: a domain at 0 on a
Saturday may simply not publish at weekends.

Language mix shifted too, and not uniformly — Arabic barely moved (5,462 → 5,660, +4%) while German
doubled (9,633 → 19,257, +100%) and Spanish rose 62%. **Arabic's share of GDELT is a weekend
artefact in #17's numbers**: on a weekday Arabic is 1.5% of the corpus, behind Greek and Italian.

### 2.5 Slot presence measures intermittency better than a second window does, and it is bad

#17 could only detect intermittency by comparing two windows a week apart, which conflates
day-to-day variance with outlet death. Window A being a complete 96-slot census allows a direct
measure: **in how many of the day's 96 slots did this host appear at all?**

The result is that intermittency is severe and it is *within* the day, not only between days:

| Host | Records/day | Slots present |
|---|---:|---:|
| `merkur.de` | 691 | **31 / 96** |
| `m.tech.china.com` | 384 | **5 / 96** |
| `mersinhaber.com` | 353 | **16 / 96** |
| `politika.rs` | 282 | **16 / 96** |
| `rg.ru` | 421 | **24 / 96** |
| `vetogate.com` | 537 | **24 / 96** |
| `life.ru` | 330 | **22 / 96** |
| `index.hr` | 751 | 59 / 96 |
| `cna.com.tw` | 576 | 44 / 96 |

A host emitting 691 records in 31 of 96 slots is publishing in **bursts** — GDELT ingests a batch and
then nothing for hours. For the quorum rule this is the operative fact: **at 15-minute story
granularity, a polity represented by one bursty outlet will be absent from most windows even though
its daily volume looks healthy.** Every per-language table below therefore reports slots-present
alongside volume, and the "more than one outlet per polity" question in §3 is answered against both.

The corollary is that #17's headline intermittency examples were partly this effect misread as outlet
death. Al-Ahram (`gate.ahram.org.eg`) is at 267/day here in **17/96 slots** — it did not die, it
publishes in a few bursts a day, and a sampling scheme that misses the bursts reports zero.

---

## 3. Per language: which polities publish, and can two of them form a quorum

### 3.0 How to read these tables

- **Volume** is window A records/day (a complete 96-slot census of 2026-07-29). `B=` is window B's
  raw count from 24 hourly slots on 2026-07-30 — **not scaled**, present only so that a domain absent
  on the second day is visible.
- **Slots** is the number of the day's 96 slots in which the host appeared at all (§2.5). Two hosts
  with the same daily volume are not equally available if one publishes in 15 slots and the other in
  70.
- **"Measurable volume"** is taken as **≥50 records/day**, which is the 88th percentile of monitored
  hosts in this census. This is a *descriptive* cut for tabulation, **not a proposed floor** — the pool
  decision must choose its own, and §1.5's warning applies: volume is an upper bound on quorum
  participation, not a measure of it. Outlets below 50/day are shown only where they are the sole
  representative of a polity, and are flagged as such.
- **Polity of publication** is sourced in §5. Where §5 says "source not obtained", the polity label is
  a lead and the row is not evidence.
- **Aggregators, content farms and non-news hosts are excluded and named**, per §2.1. They are listed
  in each language so the exclusion is auditable rather than silent.
- **The quorum question is answered twice**: whether two polities are present at all, and whether each
  present polity has **more than one outlet**. A polity with one outlet is a single point of failure
  and the quorum will fail on it whenever that outlet is between bursts (§2.5).

### 3.1 English — quorum met, but the top of the distribution is unusable

**158,432 records/day across 7,711 hosts** — 42.5% of the whole census. Also the language where §2.1
bites hardest.

**Excluded, and why** — these are the 10 highest-volume English hosts and **not one is usable**:
`quicknews-africa.net` 2,639 (content farm, placeholder contact address, republished NAN wire),
`whatweekly.com` 2,415 (**self-described dead archive** of a closed Baltimore arts magazine),
`digbycourier.ca` 1,840 and `northernpen.ca` 1,753 (content farms on a shared WordPress theme, no
masthead), `tnp.no` 1,705 (The Nordic Page, footer copyright 2017), `sublimemagazine.com` 1,305
(sustainable-lifestyle magazine, not news), `unitaid.eu` 1,294 (a health-financing agency's press
releases), `eichlernetwork.com` 1,008 (architecture/real-estate magazine), `boredpanda.com` 993 (viral
content), `dailypolitical.com` 958 (algorithmic stock summaries; see §2.1 on its two sibling sites).
Further down: `finance.yahoo.com` 860, `aol.co.uk` 829, `yahoo.com` 816, `newsnow.co.uk` 571,
`tvguide.co.uk` 564, `lolwot.com` 563, `miragenews.com` 559, `prnewswire.com` 548, `tickerreport.com`
524, `themarketsdaily.com` 507, `allafrica.com` 502, `51.ca` 494, `link.springer.com` 483,
`dhal3.com` 482 (blank page, unidentifiable), `investegate.co.uk` 450, `newkerala.com` 446,
`bignewsnetwork.com` 444, `keskustelu.kauppalehti.fi` 443 (a Finnish discussion forum),
`markets.financialcontent.com` 931, `moneycontrol.com` 585, `klrc.com` 309 (Christian-music radio).

**Polities with measurable volume, after exclusions:**

| Polity | Outlets ≥50/day | Volume/day (slots/96) | >1 outlet? |
|---|---|---|---|
| **India** | `timesofindia.indiatimes.com`, `thehindu.com`, `economictimes.indiatimes.com`, `hindustantimes.com`, `aninews.in`, `freepressjournal.in`, `orissapost.com`, `prokerala.com` | 1,065 (76) · 745 (72) · 615 (68) · 378 (35) · 406 (22) · 288 (17) · 269 (34) · 286 (13) | **Yes — 8** |
| **United Kingdom** | `dailymail.com`, `express.co.uk`, `independent.co.uk`, `theguardian.com` | 676 (67) · 309 (28) · 294 (22) · 286 (59) | **Yes — 4** |
| **United States** | `latimes.com`, `forbes.com`, `christianpost.com`, `dailyridge.com`, `fool.com` | 281 (51) · 311 (18) · 320 (18) · 649 (48) · 287 (23) | **Yes — 5** |
| **Philippines** | `manilatimes.net` | 716 (45) | No — 1 |
| **Australia** | `perthnow.com.au` | 300 (25) | No — 1 |

**Verdict: a two-polity quorum is comfortably met in English**, and three of the five polities carry
four or more outlets each, so the quorum survives outlet-level intermittency. India is the single
largest national presence in English GDELT — larger than the UK and the US — which is a notable
inversion of the assumption `RSS_METADATA` encodes.

The real constraint in English is not the quorum, it is that **the volume ranking is actively
misleading**: an unfiltered top-20 English list is almost entirely farms, aggregators and non-news.
Any automated selection by volume would build a pool out of them.

### 3.2 Spanish — the strongest multi-polity case in the census

**37,118 records/day across 951 hosts.** Second-largest language, and unusually clean: no
content farm appears near the top, and the highest-volume hosts are national and regional dailies.

**Excluded:** `deperu.com` 200 (Peruvian portal/directory), `colombia.com` 172 and
`hsbnoticias.com` 152 (aggregating portals), `entornointeligente.com` 141 and `puentelibre.mx` 164
(both in 7–8 slots only, republishing aggregators), `marca.com` 141 and `mundodeportivo.com` 203
(sport, not news of record — noted rather than excluded on principle).

**Polities with measurable volume:**

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Spain** | `larazon.es` 462 (42) · `europapress.es` 400 (44) · `abc.es` 385 (62) · `20minutos.es` 293 (46) · `elperiodico.com` 278 (38) · `andaluciainformacion.es` 250 (37) · `lavozdegalicia.es` 233 (40) · `elconfidencial.com` 229 (21) · `lne.es` 203 (41) · `laprovincia.es` 189 (26) · `lavanguardia.com` 178 (10) · `eldiario.es` 175 (18) · `farodevigo.es` 156 (33) · `heraldo.es` 156 (11) · `informacion.es` 150 (24) · `elpais.com` 149 (28) · `elmundo.es` 148 (40) · and ~15 more | **Yes — 30+** |
| **Argentina** | `cadena3.com` 315 (22) · `tn.com.ar` 273 (24) · `lanacion.com.ar` 214 (22) · `mdzol.com` 203 (17) · `eldestapeweb.com` 194 (20) · `elintransigente.com` 189 (15) · `infobae.com` 183 (18) · `clarin.com` 154 (33) · `perfil.com` 140 (16) · `rionegro.com.ar` 140 (22) | **Yes — 10** |
| **Mexico** | `zocalo.com.mx` 223 (15) · `excelsior.com.mx` 211 (19) · `razon.com.mx` 195 (12) · `eluniversal.com.mx` 186 (12) · `vanguardia.com.mx` 149 (15) · `oem.com.mx` 138 (51) · `eldiariodechihuahua.mx` 133 (10) | **Yes — 7** |
| **Colombia** | `semana.com` 171 (24) · `eltiempo.com` 147 (30) | **Yes — 2** |
| **Chile** | `biobiochile.cl` 228 (16) · `latercera.com` 163 (21) | **Yes — 2** |
| **Peru** | `larepublica.pe` 156 (24) | No — 1 |
| **Paraguay** | `abc.com.py` 147 (19) | No — 1 |
| **Venezuela** | `ciudadccs.info` 179 (37) | No — 1 |

**Verdict: quorum met, with five polities carrying two or more outlets each.** Spanish is the
best-provisioned language in the census for this axis: Spain, Argentina, Mexico, Colombia and Chile
each survive an outlet going dark, and the interest divergence among them is real and current. It is
also worth noting against #17: the state-aligned/independent axis found Spanish workable only through
a 9–58/day state pole, whereas the polity axis finds five polities at 150–460/day.

**Venezuela is the interesting single point of failure.** `ciudadccs.info` at 179/day in 37 slots is
the only Venezuelan outlet in the census with volume, and #17 already flagged it as its
highest-volume state-aligned candidate with no source at all. Under the polity axis its *polity* is
sourceable even where its alignment is not — but with one outlet, Venezuela will drop out of the
quorum regularly.

### 3.3 German — quorum met. This reverses #17's clearest negative finding

**19,257 records/day across 408 hosts.** #17 concluded "**no pair exists in German**", because the
state-aligned pole was empty: zero German-language records from any state broadcaster or state agency,
and RSF's "the independence of public media is protected by law" made ARD/ZDF unusable as a state pole.

That finding stands on its own terms and is not contradicted here. But **under the polity axis German
clears a two-polity quorum without difficulty**, because German is spoken in three states and GDELT
carries all three.

**Excluded** — German has a large financial-wire contingent that republishes company announcements
rather than reporting: `finanznachrichten.de` 597, `finanzen.net` 435, `aktiencheck.de` 333,
`boerse-express.com` 193, `finanzen.ch` 176, `wallstreet-online.de` 148, `onvista.de` 101,
`boerse-online.de` 100. Also `news.de` 271 (aggregator) and `chip.de` 138 (consumer tech).
Note `finanznachrichten.de` splits 597 GERMAN / 583 ENGLISH — it is a bilingual wire, not a German
newsroom.

**Polities with measurable volume:**

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Germany** | `merkur.de` 691 (31) · `hna.de` 613 (73) · `kreiszeitung.de` 527 (45) · `az-online.de` 501 (33) · `welt.de` 459 (56) · `n-tv.de` 377 (28) · `zeit.de` 332 (67) · `op-online.de` 316 (27) · `badische-zeitung.de` 307 (25) · `wa.de` 285 (24) · `come-on.de` 277 (36) · `tz.de` 257 (19) · `fnp.de` 249 (24) · `focus.de` 238 (12) · `soester-anzeiger.de` 217 (20) · `t-online.de` 213 (24) · `mz.de` 197 (13) · `nordkurier.de` 187 (14) · `volksstimme.de` 178 (12) · `kreisbote.de` 175 (13) · `handelsblatt.com` 169 (35) · `schwaebische.de` 168 (13) · `nwzonline.de` 166 (18) · `sueddeutsche.de` 160 (23) · `freiepresse.de` 159 (13) · `ksta.de` 156 (27) · and ~20 more | **Yes — 45+** |
| **Austria** | `heute.at` 226 (13) · `meinbezirk.at` 161 (19) · `tele.at` 124 (24) · `vol.at` 124 (29) · `kurier.at` 101 (15) · `ots.at` 88 (18) | **Yes — 6** |
| **Switzerland** | `watson.ch` 104 (33) · `20min.ch` 61 (6) · plus `tagesanzeiger.ch` 46 (21) and `srf.ch` 31 (5) below the cut | **Yes — 2 above the cut, 4 in total** |

**Verdict: a three-polity quorum is available in German, and all three polities have more than one
outlet.** Germany + Austria is the robust pairing: Austria carries six outlets in the 88–226/day range,
so an Austrian outlet going dark does not remove Austria — exactly the resilience property Decision 2
on #20 requires.

**Switzerland is thin but not empty, and the thinness is specific.** Four Swiss German-language news
hosts appear: `watson.ch` 104, `20min.ch` 61, `tagesanzeiger.ch` 46, `srf.ch` 31 — three distinct
publishers (CH Media, TX Group, SRG SSR). `finanzen.ch` (176) is excluded as a financial-data portal.
But **`nzz.ch` and `blick.ch` are at 0 records/day**, so two of the four best-known Swiss titles are
absent, and no Swiss outlet exceeds 104/day. A DE+CH pairing is possible but sits an order of magnitude
below DE+AT on volume, and Switzerland's outlets are bursty (`20min.ch` in 6 of 96 slots, `srf.ch` in
5).

**A caution on Austria that the volume figures hide**: `heute.at`'s own imprint discloses its
publisher as `DJ Digitale Medien GmbH`, Walfischgasse 13, 1010 Wien, ultimately held via
`Heute Verlag Holding und Management GmbH`, whose disclosed shareholders include **`Alta GmbH, Vaduz`
(36.92%)** — i.e. a Liechtenstein entity. Polity of publication Austria; ownership partly outside it.
This is precisely the distinction #20 requires be kept, and §5 records both.

### 3.4 French — quorum met, and Senegal is the surprise

**9,697 records/day across 467 hosts.** #17 called French "marginal" because there is no domestic
state pole and the only sourced state candidates were translated wire copy at 21–29/day. Under the
polity axis French is comfortable.

**Excluded:** `fr.allafrica.com` 208 (aggregator), `boursorama.com` 132 / `abcbourse.com` 104 /
`tradingsat.com` 85 (financial portals), `footmercato.net` 59 (sport), `sciencepost.fr` 50 (science
digest). **A publisher-identity caution rather than an exclusion:** nine `*.maville.com` hosts appear
separately (`saint-brieuc` 84, `larochesuryon` 65, `brignoles` 57, `redon` 56, `toulon` 55, `hyeres`
54, `laseyne` 53, `draguignan` 53, `paris` 52 — 529/day combined). These are **one** publisher's local
network, not nine French voices. Counting hosts rather than publishers would triple-count France.

**Polities with measurable volume:**

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **France** | `sudouest.fr` 329 (44) · `ladepeche.fr` 242 (24) · `ici.fr` 187 (48) · `ledauphine.com` 137 (38) · `bfmtv.com` 133 (24) · `republicain-lorrain.fr` 129 (23) · `estrepublicain.fr` 128 (26) · `20minutes.fr` 125 (45) · `midilibre.fr` 118 (29) · `dna.fr` 117 (35) · `leparisien.fr` 113 (42) · `leprogres.fr` 109 (28) · `franceinfo.fr` 107 (26) · `nicematin.com` 105 (30) · `laprovence.com` 91 (16) · `lalsace.fr` 87 (22) · and ~10 more | **Yes — 25+** |
| **Belgium** | `dhnet.be` 113 (11) · `lalibre.be` 97 (13) · `lavenir.net` 65 (6) · plus `rtbf.be` 34 (17) below the cut | **Yes — 3 above the cut, but see below** |
| **Senegal** | `senenews.com` 65 (5) · `seneweb.com` 56 (7) · `pressafrik.com` 52 (8) · `senego.com` 51 (6) | **Yes — 4** |
| **Canada (Québec)** | `lapresse.ca` 70 (7) · `ledevoir.com` 49 (14, below cut) | Marginally — 2 |
| **Luxembourg** | `lessentiel.lu` 54 (5) | No — 1 |
| **Vietnam** | `lecourrier.vn` 66 (16) | No — 1 |
| **Switzerland** | `letemps.ch` 38 (7, below cut) | No — 1 |
| **Tunisia** | `lapresse.tn` 48 (8, below cut) | No — 1 |

**Verdict: quorum met in French — France plus Belgium or Senegal.**

Two findings inside this that matter more than the verdict:

- **Belgium's three high-volume outlets are not three voices.** `dhnet.be` and `lalibre.be` both give
  the same publisher address on their own contact pages — *"Rue des Francs 79, 1040 Bruxelles"* — i.e.
  one publishing house (IPM). `lavenir.net` (Namur) and `rtbf.be` (the public broadcaster, 34/day) are
  distinct. **Belgium is a three-publisher polity presenting as four outlets, and the host count
  overstates its resilience.** This is a general hazard: the "more than one outlet" test must be
  applied at publisher level, not host level, and this document flags it wherever it is visible but
  has *not* traced publisher identity for every polity in every language.
- **Senegal is the best-provisioned non-European French polity and nobody has considered it.** Four
  independent Dakar-based outlets at 51–65/day. Their weakness is not volume but burstiness: each
  appears in only 5–8 of 96 slots, so at story granularity Senegal will be present rarely even though
  it publishes daily.
- **`lecourrier.vn` is a genuine publication-vs-ownership case**: a French-language daily published
  from Hanoi, owned by Vietnam's Ministry of Information and Communications (§5). Polity of
  publication Vietnam, in a language whose other polities are all in Europe and Africa.

France's own national press of record remains largely absent, confirming #17 on a weekday too:
`lemonde.fr`, `liberation.fr`, `mediapart.fr`, `france24.com` and `francetvinfo.fr` are all at **0** in
this census, and `lefigaro.fr` is at 29/day in 5 slots. **French GDELT volume is regional and overseas,
not Parisian** — the largest French host is a Bordeaux regional daily.

### 3.5 Chinese — quorum met, and met *within each* of GDELT's two language values

**`Chinese` (simplified) 15,040/day across 429 hosts; `ChineseT` (traditional) 6,008/day across 94
hosts.** #17 found the Chinese pair "conditional": it worked only if the two values counted as one
language, and *within* either value alone there was no pair. **On the polity axis that condition
disappears — each value clears a two-polity quorum on its own.**

**`ChineseT` (traditional) — excluded first:** `blog.udn.com` **605/day in 96/96 slots** is a
Taiwanese *blog host*, not journalism, and it is the single largest `ChineseT` host in the census (it
also emits 226 `Japanese` and 87 `Chinese` records, which makes it the largest "Japanese" host too —
§3.10).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Taiwan** | `cna.com.tw` 576 (44) · `n.yam.com` 549 (40) · `setn.com` 507 (60) · `news.ltn.com.tw` 456 (50) · `chinatimes.com` 407 (33) · `udn.com` 391 (33) · `ettoday.net` 284 (31) · `newtalk.tw` 201 (23) · `news.cts.com.tw` 199 (26) · `storm.mg` 174 (17) | **Yes — 8+ distinct publishers** |
| **Hong Kong** | `hkcna.hk` 117 (10) · `hkcd.com` 81 (10) · `wenweipo.com` 75 (6) · `portal.sina.com.hk` 73 (32) | **Yes — 4** |
| **United States (diaspora)** | `ntdtv.com` 72 (8) · `singtaousa.com` 65 of 112 total (7) | **Yes — 2** |

**`Chinese` (simplified) — excluded first, and this is most of the volume:** the top of simplified
Chinese is commercial portals and UGC, not outlets — `baijiahao.baidu.com` 1,597 (Baidu's
user-publishing platform, 96/96 slots), `163.com` 1,535 (NetEase portal), `finance.sina.com.cn` 893,
`cfi.net.cn` 748, `itbear.com.cn` 503, `news.china.com` 400, `m.tech.china.com` 384 (in **5** of 96
slots), `hea.china.com` 269, `jinghua.cn` 258, `finance.eastmoney.com` 209. Roughly **5,700 of the
15,040 simplified-Chinese records/day come from hosts that are portals, financial-data sites or UGC
platforms.**

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **People's Republic of China** | `news.cn` (Xinhua) 111 `Chinese` of 411 all-language (10) · `people.com.cn` 155 `Chinese` of 205 · `news.china.com.cn` 120 (13) · `yangtse.com` 168 (8) · `news.dahe.cn` 131 (6) · `news.ifeng.com` 100 (19) · `news.ycwb.com` 103 (16) · `yicai.com` 96 (29) · `chinanews.com.cn` 81 (13) · `news.fznews.com.cn` 80 (7) · `cqnews.net` 79 (15) | **Yes — many** |
| **United States (diaspora)** | `epochtimes.com` 129 (10) · `blog.wenxuecity.com` 94 (24) + `wenxuecity.com` 69 (13) · `aboluowang.com` 90 (12) | **Yes — 3** |
| **Malaysia** | `orientaldaily.com.my` 135 (12) | No — 1 |
| **Singapore** | `zaobao.com.sg` 92 (11) | No — 1 |

**Verdict: quorum met in Chinese, three different ways.** Within `ChineseT`: Taiwan + Hong Kong, both
with multiple outlets. Within `Chinese`: PRC + United States diaspora, both with multiple outlets
(Malaysia and Singapore are one outlet each). Across the two values: PRC vs Taiwan, the pairing #20
identified as the case that pointed to this axis in the first place, and the highest-volume adversarial
pairing in the census.

**The finding that generalises:** GDELT's `Chinese`/`ChineseT` boundary is *approximately* the
PRC / Taiwan-HK boundary but not exactly — `cfi.net.cn`, a PRC financial site, emits 748 `Chinese`
**and 37 `ChineseT`**, and `blog.udn.com` (Taiwan) emits 87 `Chinese`. Selection must be on the sourced
domain table with `lang` as a pre-filter only (§2.2).

### 3.6 Russian — quorum met, and this is the largest reversal in this document

**13,218 records/day across 404 hosts.** #17's verdict was unambiguous: "**no pair exists in
Russian**", because every Russian-language exile outlet — Meduza, Novaya Gazeta Europe, The Insider,
Holod, IStories, TV Rain — is at exactly zero records/day. That remains true.

**But the polity axis does not need exile media, because Ukraine publishes in Russian at volume.**

**Excluded:** `news.mail.ru` 531 (Mail.ru portal aggregator), `pressorg24.com` 106 and `mngz.ru` 106
(republishing aggregators), `playground.ru` 100 and `ixbt.com` 88 (gaming / consumer tech).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Russia** | `rg.ru` 421 (24) · `ria.ru` 345 (73) · `life.ru` 330 (22) · `vesti.ru` 326 (26) · `iz.ru` 289 (45) · `aif.ru` 283 (31) · `lenta.ru` 270 (33) · `kommersant.ru` 268 (49) · `1prime.ru` 242 (20) · `vz.ru` 209 (24) · `vedomosti.ru` 191 (14) · `interfax.ru` 176 (37) · `ura.news` 173 (15) · `mk.ru` 172 (21) · `m24.ru` 162 (14) · `pravda.ru` 158 (47) · `russian.rt.com` 130 (21) · and ~15 more | **Yes — 30+** |
| **Ukraine** | `24tv.ua` 199 (61) · `unian.net` 137 (34) · `korrespondent.net` 107 (24) · `unn.ua` 105 (29) · `obozrevatel.com` 101 (29) · `focus.ua` 77 (13) · `gazeta.ua` 60 (22) | **Yes — 7** |
| **Belarus** | `sb.by` 114 (13) · `ont.by` 62 (10) | **Yes — 2** |
| **Azerbaijan** | `vesti.az` 80 (7) · `ru.apa.az` 68 (20) | **Yes — 2** |
| **Israel** | `mignews.com` 161 (42) | No — 1, and polity unsourced |
| **Kyrgyzstan** | `gazeta.kg` 86 (12) | No — 1 |

**Verdict: quorum met in Russian, and it is the sharpest interest divergence available in any language
in this census.** Russia vs Ukraine, in the same language, 30+ Russian outlets against 7 Ukrainian ones,
all above 60/day. Belarus and Azerbaijan add third and fourth polities with two outlets each.

Three things worth stating precisely, because this reversal is consequential:

- **It is not a disagreement with #17, it is a different question.** #17 asked whether a
  Russian-language outlet exists that a source calls independent, and correctly answered no. This asks
  whether two polities publish in Russian, and the answer is six.
- **Several Ukrainian outlets are bilingual and GDELT splits them across tags.** `24tv.ua` emits
  242 `UKRAINIAN` **and** 199 `RUSSIAN`; `unian.net`/`unian.ua`, `unn.ua`, `obozrevatel.com`,
  `focus.ua` and `korrespondent.net` likewise appear under both. Selecting Ukraine's Russian-language
  output requires filtering on `(domain, lang)` **jointly** — which is what this histogram is keyed on,
  and which a domain-only filter would get wrong.
- **`mignews.com` is a genuine polity puzzle** and is flagged rather than resolved: a Russian-language
  news site widely associated with Israel, at 161/day in 42 slots, whose **polity of publication could
  not be sourced** (no Wikidata `P17`/`P159`, no reachable imprint). It is a lead, not evidence.

### 3.7 Turkish — quorum met, on Turkey vs Northern Cyprus

**10,485 records/day across 165 hosts** — more than French, Arabic or Portuguese, and absent from the
project's corpus entirely.

**Excluded:** `haberler.com` **1,673/day in 88 of 96 slots** is Turkey's largest news aggregator and
the 7th-largest host in the whole census. Also `ensonhaber.com` 244, `haberaktuel.com` 205,
`haber7.com` 144, `internethaber.com` 143, `haber3.com` 76, `haber.mynet.com` 73, `f5haber.com` 55
(aggregating portals); `memurlar.net` 84 (civil-service notices); `fotospor.com.tr` 88 (sport).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Turkey** | `birgun.net` 435 (42) · `mersinhaber.com` 353 (16) · `dunya.com` 254 (35) · `bursadabugun.com` 227 (11) · `sabah.com.tr` 203 (38) · `sozcu.com.tr` 202 (21) · `haberturk.com` 195 (26) · `yeniakit.com.tr` 168 (34) · `yenisafak.com` 164 (19) · `turkiyegazetesi.com.tr` 152 (10) · `odatv.com` 142 (17) · `milliyet.com.tr` 138 (20) · `hurriyet.com.tr` 132 (20) · `evrensel.net` 132 (12) · `aa.com.tr` 117 (18) · `star.com.tr` 113 (43) · `cnnturk.com` 110 (27) · `aksam.com.tr` 95 (12) · `trthaber.com` 83 (6) · and ~20 more | **Yes — 40+** |
| **Northern Cyprus** | `kibrispostasi.com` 94 (6) · `kibrisgazetesi.com` 56 (5) · `havadiskibris.com` 54 (4) | **Yes — 3** |
| **Russia** | `anlatilaninotesi.com.tr` 77 (11) | No — 1, and polity unsourced |

**Verdict: quorum met in Turkish, on Turkey + Northern Cyprus.** Three Turkish Cypriot titles clear
50/day, so the second polity survives an outlet going dark — **but all three are extremely bursty
(4–6 slots of 96)**, so Northern Cyprus will be absent from the great majority of 15-minute windows.
This is the clearest case in the document of the distinction Decision 2 requires: a polity can have
outlet redundancy and still not be present most of the time.

**The accepted cost of #20 is visible here.** #17 found Turkish its strongest state-aligned /
independent pair (Sabah and TRT Haber against Sözcü). Under the polity axis Sabah, TRT Haber, Sözcü,
BirGün and Evrensel all fall into the **same** pole and the pair disappears. That is exactly the
within-polity dissent #20 accepted losing, and Turkish is where it costs most.

`anlatilaninotesi.com.tr` (77/day) is Sputnik's Turkish-language service under its post-2022 brand. Its
polity of publication is a real question rather than an obvious one, and §5 records it as **source not
obtained** rather than assigning one.

### 3.8 Portuguese — quorum met, Brazil vs Portugal

**9,194 records/day across 313 hosts.** #17 called Portuguese "marginal", with its only sourced state
pole at 26/day.

**Excluded:** `sapo.pt` 532 (Portuguese portal; note its sub-sites `executivedigest.sapo.pt` 117 and
`jornaleconomico.sapo.pt` 105 are separate editorial products merely hosted on it),
`infomoney.com.br` 117 (financial portal), `lance.com.br` 78 and `futebolinterior.com.br` 57 (sport),
`uol.com.br` 72 and `terra.com.br` 52 (portals), `boainformacao.com.br` 47 (aggregator).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Brazil** | `g1.globo.com` 597 (39) · `em.com.br` 247 (28) · `jornaldebrasilia.com.br` 225 (21) · `oglobo.globo.com` 208 (38) · `dgabc.com.br` 195 (15) · `www1.folha.uol.com.br` 192 (62) · `brasil247.com` 150 (15) · `otempo.com.br` 137 (22) · `estadao.com.br` 135 (28) · `veja.abril.com.br` 134 (23) · `correiobraziliense.com.br` 134 (26) · `correio24horas.com.br` 128 (20) · `correiodopovo.com.br` 120 (13) · `gazetadopovo.com.br` 103 (14) · and ~25 more | **Yes — 35+** |
| **Portugal** | `observador.pt` 201 (30) · `executivedigest.sapo.pt` 117 (36) · `jornaleconomico.sapo.pt` 105 (29) · `noticiasdecoimbra.pt` 96 (4) · `dnoticias.pt` 94 (6) · `rtp.pt` 55 (21) · `record.pt` 53 (10) | **Yes — 7** |

**Verdict: quorum met in Portuguese, on Brazil + Portugal, both with several outlets.** Portugal is the
polity #17 could not see, because it was looking for a state-aligned pole and Portugal's press is not
one.

**Lusophone Africa is absent, and that is a real limit on this language's reach.** Jornal de Angola,
ANGOP and Notícias (Mozambique) are at **0**. A Portuguese pool is a Brazil–Portugal pool: two polities
out of nine Portuguese-speaking states, both in the Atlantic north-west of the language.

### 3.9 Arabic — quorum met, and Arabic is the most polity-rich language relative to its volume

**5,660 records/day across 152 hosts.** Small — Arabic is 1.5% of this weekday census, behind Greek and
Italian — but it contains **more distinct polities than any other language here**.

**Excluded:** `eremnews.com` 104, `bokra.net` 64, `arabnet5.com` 35 (aggregators);
`arriyadiyah.com` 33 (sport); `arabic.euronews.com` 57 and `arabic.cnn.com` 44 (Arabic desks of
European/US broadcasters — a real polity signal, but translated wire rather than an Arabic newsroom).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Egypt** | `dostor.org` 716 (47) · `vetogate.com` 537 (24) · `shorouknews.com` 408 (75) · `gate.ahram.org.eg` 267 (17) · `almasryalyoum.com` 250 (12) · `nile.eg` 75 (13) · `akhbarelyom.com` 62 (10) | **Yes — 7** |
| **Morocco** | `hespress.com` 75 (23) · `ahdath.info` 46 (9) · `alyaoum24.com` 32 (4) | **Yes — 3** |
| **Saudi Arabia** | `alriyadh.com` 55 (5) · `slaati.com` 54 (22) · `almowaten.net` 52 (12) · `alwatan.com.sa` 30 (10) | **Yes — 3–4** |
| **Lebanon** | `almanar.com.lb` 61 (29) · `addiyar.com` 34 (12) · `tayyar.org` 32 (7) | **Yes — 3** |
| **United Arab Emirates** | `albayan.ae` 134 (7) · `emaratalyoum.com` 92 (16) | **Yes — 2** |
| **Algeria** | `ennaharonline.com` 51 (4) · `echoroukonline.com` 45 (4) | **Yes — 2** |
| **Qatar** | `aljazeera.net` 123 (24) · `raya.com` 26 (6) | Marginally — 2 |
| **Palestine** | `raya.ps` 49 (4) · `shfanews.net` 42 (4) · `pnn.ps` 36 (4) · `shasha.ps` 26 (4) | **Yes — 4**, all below the cut |
| **Jordan** | `alanbatnews.net` 44 (6) · `jo24.net` 42 (5) · `sarayanews.com` 35 (8) · `assabeel.net` 32 (10) · `khaberni.com` 23 (10) | **Yes — 5**, all below the cut |
| **Iraq** | `kitabat.com` 43 (4) · `almadapaper.net` 37 (14) · `azzaman.com` 36 (3) | **Yes — 3**, all below the cut |
| **Libya** | `libyaakhbar.com` 138 (15) | No — 1 |
| **Bahrain** | `albiladpress.com` 127 (8) | No — 1 |
| **Kuwait** | `annaharkw.com` 73 (**1**) | No — 1, in a single slot |
| **Syria** | `sana.sy` 50 (36) | No — 1 |
| **Yemen** | `26sep.net` 41 (5) | No — 1 |

**Verdict: quorum met in Arabic, with at least six polities carrying two or more outlets** (Egypt,
Morocco, Saudi Arabia, Lebanon, UAE, Algeria — plus Palestine, Jordan and Iraq if the cut is lowered).
The Egypt / Saudi Arabia / Qatar / UAE / Syria divergence #20 named is all present.

Two qualifications:

- **Egypt dominates the top by a factor of 2.3× everyone else combined.** The five largest Arabic hosts
  are all Egyptian, totalling 2,178/day against 123 for Qatar's Al Jazeera. A quorum satisfied by
  "Egypt plus anyone" will mostly measure Egypt against a much smaller counterparty.
- **#17's headline intermittency example was a sampling artefact.** It reported Al-Ahram at 348 → **0**
  between windows. Here `gate.ahram.org.eg` is at 267/day — alive — but in only **17 of 96 slots**: it
  publishes in bursts, and #17's hourly window-2 sampling missed them. `annaharkw.com` (Kuwait, 73/day
  in **1** slot) is the extreme form — an entire polity's presence resting on one host's single daily
  batch.

### 3.10 Italian — quorum met, and Italian has never been assessed by this project

**16,634 records/day across 654 hosts** — **larger than German** and 2.9× Arabic. Italian was reported
in #17's "other languages, not assessed" appendix at 9,834/day and has never been examined for a pair
or a quorum. On a weekday it is GDELT's fourth-largest language.

**Excluded:** `zazoom.it` **2,901/day** — the largest host in the entire census, and an aggregator
that republishes other Italian outlets. Also `teleborsa.it` 144, `borsaitaliana.it` 137,
`finanza.lastampa.it` 72, `milanofinanza.it` 65 (financial data); `tuttomercatoweb.com` 306,
`tuttonapoli.net` 73, `milannews.it` 70, `gazzetta.it` 58 (sport); `notizie.it` 70,
`today.it` 59 (aggregators); `italpress.com` 97 and `adnkronos.com` 86 are wire agencies, kept as
Italian outlets but noted as wire.

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Italy** | `ansa.it` 751 (63) · `ilpost.it` 369 (23) · `ilmessaggero.it` 257 (36) · `ilgazzettino.it` 151 (28) · `ilmattino.it` 145 (22) · `ilfattoquotidiano.it` 130 (24) · `ilgiornale.it` 123 (22) · `corriereadriatico.it` 113 (10) · `targatocn.it` 110 (24) · `ildispaccio.it` 102 (6) · `ilsole24ore.com` 99 (14) · `leggo.it` 89 (29) · `varesenews.it` 85 (45) · `newsbiella.it` 84 (26) · `corriere.it` 82 (7) · `lastampa.it` 63 (11) · and ~25 more | **Yes — 40+** |
| **Switzerland (Ticino)** | `tio.ch` 80 (6) · `laregione.ch` 75 (16) · `cdt.ch` 54 (8) · plus `rsi.ch` 25 (7) below the cut | **Yes — 3 above the cut, 4 in total** |

**Verdict: quorum met in Italian, on Italy + Italian-speaking Switzerland.** Three Ticinese titles clear
50/day — `tio.ch`, `laregione.ch` and `cdt.ch` (Corriere del Ticino) — plus the Swiss public
broadcaster's Italian service `rsi.ch` at 25. Four distinct Swiss publishers.

**Caveats specific to Italian:**

- **The Swiss pole is small and bursty**: 234/day combined against Italy's ~9,000, in 6–16 slots of 96.
- **San Marino and the Vatican are absent.** Checked rather than assumed: `sanmarinortv.sm`,
  `libertas.sm`, `giornalesm.com` and `vaticannews.va` are all at **0**, and `osservatoreromano.va`
  returns **2** records/day. So the two other sovereign Italian-language polities are not available, and
  Italian is an Italy–Switzerland quorum or nothing.
- Italian is a case where **the language's GDELT volume is out of all proportion to the project's
  attention**: 16,634/day against Arabic's 5,660, and it currently sits in neither the corpus nor any
  candidate list.

### 3.11 Greek — quorum met, Greece vs Cyprus

**9,571 records/day across 136 hosts** — larger than Arabic and French combined would have been in
#17's weekend numbers, and also never assessed by this project.

**Excluded:** `inewsgr.com` **1,570/day in 85 of 96 slots** (aggregator, the 9th-largest host in the
census); `bankingnews.gr` 216, `capital.gr` 189, `naftemporiki.gr` 181, `euro2day.gr` 113,
`sofokleous10.gr` 111, `sofokleousin.gr` 102, `mikrometoxos.gr` 62, `businessnews.gr` 71 (financial
portals — Greek GDELT has an unusually large financial-press contingent).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Greece** | `iefimerida.gr` 228 (23) · `newsbeast.gr` 223 (61) · `protothema.gr` 219 (40) · `newsbomb.gr` 207 (26) · `newsit.gr` 196 (24) · `tanea.gr` 192 (51) · `in.gr` 175 (32) · `skai.gr` 172 (21) · `sbctv.gr` 167 (11) · `voria.gr` 162 (21) · `cretalive.gr` 159 (11) · `news247.gr` 153 (11) · `kathimerini.gr` 147 (10) · `thetoc.gr` 142 (7) · `athensvoice.gr` 140 (19) · `pelop.gr` 139 (9) · `enikos.gr` 135 (11) · `efsyn.gr` 125 (9) · and ~25 more | **Yes — 40+** |
| **Cyprus** | `kathimerini.com.cy` 132 (9) · `philenews.com` 122 (36) · `sigmalive.com` 118 (16) · `dialogos.com.cy` 85 (20) · `tothemaonline.com` 58 (22) | **Yes — 5** |

**Verdict: quorum met in Greek, on Greece + Cyprus, and Cyprus carries five outlets at 58–132/day.**
Greek is one of the cleanest quorum cases in the census that nobody has proposed: two polities, both
with real redundancy, in a language with more GDELT volume than Arabic.

Note the polity relationship: `kathimerini.com.cy` is the Cypriot edition of an Athens title, so
**polity of publication Cyprus with editorial lineage in Greece** — the kind of case §5 records in two
columns rather than one.

### 3.12 Romanian — quorum met, Romania vs Moldova

**5,187 records/day across 147 hosts.** Never assessed by this project.

**Excluded:** `news.yam.md` **783/day** — the largest Romanian-language host in the census is a
**Moldovan aggregator**, not a newsroom, which is worth stating because excluding it changes Moldova's
apparent size by a factor of five. Also `ziare.com` 214 and `stiripesurse.ro` 242 (aggregating
portals); `business24.ro` 185, `bursa.ro` 102, `zf.ro` 94, `capital.ro` 79, `ziarulprofit.ro` 58,
`zfcorporate.ro` 72, `dailybusiness.ro` 27 (financial); `cancan.ro` 57, `click.ro` 78, `kudika.ro` 26
(celebrity/lifestyle); `gsp.ro` 42 (sport).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Romania** | `mediafax.ro` 146 (35) · `digi24.ro` 134 (13) · `antena3.ro` 118 (16) · `adevarul.ro` 112 (16) · `agerpres.ro` 108 (15) · `romaniatv.net` 107 (6) · `mesagerul.ro` 101 (13) · `stirileprotv.ro` 97 (9) · `hotnews.ro` 83 (13) · `jurnalul.ro` 79 (22) · `cotidianul.ro` 76 (7) · `realitatea.net` 63 (11) · `ziuaconstanta.ro` 53 (9) · `dcnews.ro` 52 (5) · `rador.ro` 50 (9) | **Yes — 15+** |
| **Moldova** | `ziarulnational.md` 72 (5) · plus `moldpres.md` 29 (9), `zdg.md` 29 (7) and `protv.md` 23 (6) below the cut | **Yes — 4 in total, only 1 above the cut** |

**Verdict: quorum met in Romanian, on Romania + Moldova — but Moldova is thin.** Only
`ziarulnational.md` clears 50/day; the state agency `moldpres.md`, the investigative weekly `zdg.md`
and `protv.md` sit at 23–29. Moldova has four publishers, which is the resilience Decision 2 wants, but
all four are bursty (5–9 slots of 96) and none is high-volume. Romania–Moldova is a real and current
interest divergence, and it is available at low volume rather than not at all.

### 3.13 Serbo-Croatian (`SERBIAN` + `CROATIAN` + `BOSNIAN`) — quorum met, and GDELT pre-splits it by polity

**2,854 + 2,087 + 628 = 5,569 records/day.** Treated here as one dialect continuum split across three
GDELT tags (§2.2), because that is what it is and because the tags do not cleanly separate the polities.

**Excluded:** `naslovi.net` 425 across all three tags (Serbian aggregator, 80/96 slots — the largest
single host in the group and not a publisher); `index.hr` 751 (Croatian portal — kept, it does original
reporting, but noted as portal-shaped); `kamatica.com` 11, `bizportal.rs` 16 (financial);
`zena.blic.rs`, `superzena.b92.net`, `najzena.alo.rs`, `hellomagazin.rs`, `lepotaizdravlje.rs`
(lifestyle verticals of parent titles, not separate voices).

| Polity | Outlets ≥50/day (volume/day, dominant tag) | >1 outlet? |
|---|---|---|
| **Serbia** | `politika.rs` 282 · `blic.rs` 242 · `informer.rs` 217 · `telegraf.rs` 179 · `danas.rs` 161 · `b92.net` 154 · `novosti.rs` 151 · `tanjug.rs` 129 · `alo.rs` 112 · `dnevnik.rs` 66 · `rts.rs` 64 · `sputnikportal.rs` 65 — all `SERBIAN` | **Yes — 12** |
| **Croatia** | `index.hr` 751 · `net.hr` 201 · `vecernji.hr` 110 · `jutarnji.hr` 91 · `24sata.hr` 71 · `dnevnik.hr` 59 · `novilist.hr` 54 — all `CROATIAN` | **Yes — 7** |
| **Bosnia and Herzegovina** | `avaz.ba` 159 across three tags · `rtrs.tv` 100 (`SERBIAN`) · `oslobodjenje.ba` 76 · `klix.ba` 78 · `slobodna-bosna.ba` 76 · `federalna.ba` 68 · `vecernji.ba` 67 · `srna.rs` 43 | **Yes — 8** |
| **Montenegro** | `rtcg.me` 49 · `dan.co.me` 33 · `portalanalitika.me` 17 — all below the cut | **Yes — 3**, all below the cut |

**Verdict: quorum met, with three polities carrying seven or more outlets each.** Serbia, Croatia and
Bosnia-Herzegovina are all well provisioned, and the interest divergence among them needs no argument.
Montenegro is present but only below 50/day.

**This is the language group where §2.2's caution matters most.** A Bosnian publisher's output is
scattered across all three GDELT tags — `avaz.ba` emits 76 `BOSNIAN`, 72 `CROATIAN` and 11 `SERBIAN` —
so `lang`-based selection cannot recover Bosnia, and `lang == "CROATIAN"` returns Bosnian outlets.
Bosnia is *also* internally split by polity in a way the state boundary does not capture: `rtrs.tv` and
`srna.rs` are Republika Srpska institutions while `federalna.ba` is a Federation one. **This document
records Bosnia as one polity of publication** — which is the legally correct answer and may not be the
analytically useful one. Flagged, not resolved.

### 3.14 Albanian — quorum met, three polities, and also never assessed

**2,755 records/day across 108 hosts.**

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **Kosovo** | `telegrafi.com` 215 (39) · `gazetaexpress.com` 159 (24) · `botasot.info` 144 (34) · `zeri.info` 136 (33) · `lajmi.net` 80 (20) · `portalifiks.com` 64 (41) · `kohajone.com` 55 (23) · `almakos.com` 54 (24) | **Yes — 8** |
| **Albania** | `24-ore.com` 260 (47) · `albeu.com` 154 (34) · `sot.com.al` 112 (18) · `syri.net` 77 (32) · `top-channel.tv` 67 (30) · `rtsh.al` 53 (23) | **Yes — 6** |
| **North Macedonia** | `koha.mk` 53 (17) · plus `zhurnal.mk` 36, `portalb.mk` 31, `aktuale.mk` 24, `tv21.tv` 21, `alsat.mk` 20 below the cut | **Yes — 6 in total, 1 above the cut** |

**Verdict: quorum met in Albanian, with Kosovo and Albania each carrying six or more outlets.** Note
that **Kosovo out-publishes Albania** in GDELT (856/day vs 723/day across the listed outlets), and that
Kosovo's status makes "polity of publication" a live rather than clerical distinction here — which is
exactly the kind of case the axis is designed to represent rather than smooth over.

### 3.15 Korean — quorum met only through a diaspora polity, and the DPRK is absent

**4,057 records/day across 55 hosts.** #17 did not assess Korean.

**Excluded:** `insight.co.kr` 134, `wikitree.co.kr` 70, `diodeo.com` 39 (viral/aggregator);
`zdnet.co.kr` 138, `etnews.com` 68, `inews24.com` 119, `ddaily.co.kr` 104, `kbench.com` 24
(consumer tech); `newspim.com` 364, `biz.heraldcorp.com` 349, `edaily.co.kr` 299, `fnnews.com` 287,
`etoday.co.kr` 259, `newsway.co.kr` 107, `newstomato.com` 58 (financial wires — this is the bulk of
Korean volume).

| Polity | Outlets ≥50/day (volume/day, slots/96) | >1 outlet? |
|---|---|---|
| **South Korea** | `hani.co.kr` 147 (24) · `ohmynews.com` 145 (14) · `womannews.net` 135 (6) · `kmib.co.kr` 126 (10) · `segye.com` 112 (8) · `hankookilbo.com` 98 (16) · `munhwa.com` 84 (5) · `busan.com` 77 (6) | **Yes — 8+** |
| **United States (Korean-American press)** | `koreatimes.com` 124 (6) · `heraldk.com` 72 (5) · `cunews.net` 46 (2) · `radioseoul1650.com` 38 (5) | **Yes — 4, one above the cut** |

**Verdict: a two-polity quorum exists in Korean, but only if the Korean-American press counts as a
distinct polity of publication.** `koreatimes.com` is published from Los Angeles (§5) and is a US
entity publishing in Korean; whether "United States" is a *useful* second polity for a Korean-language
index is a judgement, not a measurement, and it is left open here.

**What would make Korean a strong case is absent.** The DPRK is the obvious second polity and it is at
**zero**: `kcna.kp`, `rodong.rep.kp` and `uriminzokkiri.com` all return no records. `voakorea.com` (US
government, 10/day) and `kr.xinhuanet.com` (PRC, 15/day) are the only other foreign-published
Korean-language sources, both far below any usable threshold. So the polity divergence a Korean index
would want — the one across the DMZ — **cannot be built from GDELT.**

### 3.16 Where a two-polity quorum is impossible, and why

Five cases. Each is a different reason, and the reason matters more than the verdict.

#### Japanese — one polity, and its second-largest "Japanese" host is a Taiwanese blog platform

**2,124 records/day across 98 hosts.** Every host with volume is published from Japan:
`mainichi.jp` 185, `agara.co.jp` 123, `the-miyanichi.co.jp` 104, `toonippo.co.jp` 92,
`japan.cnet.com` 87, `sponichi.co.jp` 85, `nikkei.com` 78, `ascii.jp` 76, `shikoku-np.co.jp` 58,
`sankei.com` 57, `373news.com` 52 — largely prefectural dailies.

**No second polity exists at any usable volume.** The only non-Japanese publishers of Japanese-language
records in the census are `j.people.com.cn` (PRC, **11**/day), `jp.xinhuanet.com` (PRC, **7**),
`japan.focustaiwan.tw` (Taiwan, **5**) — and `blog.udn.com`, a Taiwanese blog host, which at **226/day
in 96/96 slots is the largest single source of `Japanese`-tagged records in the census**. That is an
artefact of GDELT's language detection on a user-blog platform, not a Taiwanese Japanese-language
newsroom.

**A two-polity quorum is impossible in Japanese.** Japan is the only polity publishing Japanese at
volume — which is what one would expect of a language spoken in one state, and it is the structural
reason, not a data gap. `yomiuri.co.jp`, Japan's largest newspaper, is at **9**/day; NHK is at 0.

#### Ukrainian — one polity, because its second polity uses the other tag

**4,743 records/day across 152 hosts**, and all of them are Ukrainian: `24tv.ua` 242, `tsn.ua` 237,
`unian.ua` 165, `glavcom.ua` 143, `ua.korrespondent.net` 140, `obozrevatel.com` 130,
`interfax.com.ua` 129, and so on. The only non-Ukrainian publisher is `radiosvoboda.org` (RFE/RL, US
government-funded, 55/day) — one outlet, and putting the US on the second pole of a Ukrainian index is
not a defensible reading of the axis.

**A two-polity quorum is impossible within `UKRAINIAN`.** Russia does not publish in Ukrainian.
The interesting adversarial content involving Ukraine is reachable — but through the **`RUSSIAN`** tag
(§3.6), where Ukraine has seven outlets. **So Ukrainian and Russian are the same quorum problem
approached from two sides, and only the Russian side has an answer.**

#### Hebrew — one polity, and no other polity publishes in it

**835 records/day across 36 hosts**, every one Israeli: `ynet.co.il` 123, `inn.co.il` 93,
`kikar.co.il` 83, `srugim.co.il` 75, `kipa.co.il` 59, `haaretz.co.il` 51, `one.co.il` 47,
`maariv.co.il` 45, `globes.co.il` 37, `news.walla.co.il` 31.

**A two-polity quorum is impossible in Hebrew, structurally.** Hebrew has one state of publication and
no foreign state broadcasts in it at volume. The divergence visible in the list is real but *within*
Israel — `haaretz.co.il` against `inn.co.il` (Arutz Sheva), `srugim.co.il` and `kikar.co.il` — i.e.
precisely the within-polity dissent #20 decided to give up. Hebrew is the language where that cost is
total: everything interesting about it is inside one polity.

#### Vietnamese — one polity

**6,136 records/day across 76 hosts** — substantial volume, and every host is Vietnamese:
`baomoi.com` 1,193 (an aggregator, excluded), `vietgiaitri.com` 269, `vnexpress.net` 263,
`baotintuc.vn` 243, `thanhnien.vn` 222, `dantri.com.vn` 219, `danviet.vn` 194, `vov.vn` 188,
`tuoitre.vn` 183, `tienphong.vn` 178, `kenh14.vn` 174.

**A two-polity quorum is impossible in Vietnamese.** No second polity publishes in it in this census —
no diaspora outlet, no foreign state service. (Note `lecourrier.vn`, §3.4, is Vietnam publishing in
*French*, the mirror image.) Vietnamese is also a case where the polity axis is arguably the wrong
instrument regardless of availability: `vnexpress.net` and `vov.vn` are both government-ministry-owned
(§5), so a Vietnamese pool would be one polity and one owner.

#### Persian and Hindi — fail on volume before the axis applies

**Persian: 139 records/day across 12 hosts.** Consistent with #17's 123. The hosts are `ipna.ir` 36
(Iran), `sputnik.af` 23 (Russian state, published for Afghanistan), `news.gooya.com` 20 (diaspora
aggregator), `khaama.com` 15 (Afghanistan), `bbc.com` 12 (UK), `kar-online.com` 7,
`radiofarda.com` 7 (US government), `spnfa.ir` 7 (Russian state), `afghanpaper.com` 6 (Afghanistan),
`iranpressnews.com` 3, `hra-news.org` 2 — **and `unitaid.eu` 1**, which is a health agency emitting one
mislabelled record and a useful reminder of the noise floor.

Several polities are nominally present — Iran, Afghanistan, Russia, UK, US — so this is **not** a
one-polity failure like Japanese. It fails on volume: **the entire language is 0.04% of the census**,
Iran is represented by one host at 36/day, and the largest single Persian "publisher" after that is a
Russian state service. Every Iranian state outlet (IRNA, Fars, Tasnim, Mehr, `presstv.ir`) is at 0, as
is Iran International.

**Hindi: 3 records/day** — `jagran.com` 1, `punjabkesari.in` 1, `digit.in` 1, in a 372,499-record
census. #17 measured 1 record; this measures 3. **No quorum can be assessed because there is no corpus
to assess it in.** For scale, in the same census GDELT emitted 537 Telugu, 511 Malayalam, 452 Urdu, 329
Latvian and 303 Azerbaijani records. India is heavily present in GDELT — it is the largest English-
language polity (§3.1) — but **not in Hindi**. Whether this is a crawl gap or a language-detection gap
is **unmeasured**; the effect on the pool is the same either way.

### 3.17 Two marginal cases worth recording rather than deciding

**Urdu — a quorum is arithmetically possible and substantively lopsided.** 452 records/day across 12
hosts. Pakistan: `express.pk` 133, `jang.com.pk` 112, `dailyaaj.com.pk` 72, `dailyausaf.com` 43,
`aaj.tv` 31, `javedch.com` 24, `dunyanews.tv` 6, `dawnnews.tv` 2 — eight outlets. India:
`sahilonline.net` 18, `etemaaddaily.com` 1, `theindianawaaz.com` 1. UK: `bbc.com` 9.
So Pakistan (8 outlets) vs India (1 usable outlet at 18/day) — the Partition boundary GDELT draws
between `URDU` and `HINDI` (§2.2) is real, but only one side of it publishes. **Recorded as marginal:
two polities exist, one has redundancy and the other does not, and the whole language is 0.12% of the
census.**

**Catalan — two polities, one of them tiny.** 672 records/day. Spain: `elpuntavui.cat` 98,
`regio7.cat` 79, `elperiodico.cat` 78, `diaridegirona.cat` 73, `segre.com` 57, `ara.cat` 55,
`vilaweb.cat` 33, `3cat.cat` 20 — eight outlets. **Andorra**: `diariandorra.ad` 44, `bondia.ad` 6,
`govern.ad` 7 (a government site, not a newsroom). So Catalan has a genuine second sovereign polity —
Andorra — carrying essentially **one** newspaper at 44/day. **Recorded as marginal**, and interesting
mainly because it is the clearest small case of a polity that exists, is sourceable, and is a single
point of failure.

### 3.18 Languages with real volume that were not assessed for polity here

Reported because §2.4 shows the language mix is a property of GDELT's crawl rather than of world news
production, and because several of these have more volume than languages the project has debated at
length. **No polity sourcing was done for these, so nothing here is a finding about quorum.**

| Language | Records/day (window A) | Note |
|---|---:|---|
| INDONESIAN | 7,669 | One polity in practice (Indonesia); `tribunnews.com` and `kompas.com` dominate through dozens of city subdomains that are one publisher each. Its second polity is reachable only through `MALAY` (Malaysia 5 outlets, Singapore 1) — the same structure as Chinese/ChineseT and Ukrainian/Russian |
| POLISH | 3,284 | Poland only, on inspection of the top 10 |
| BULGARIAN / MACEDONIAN | 1,791 / 926 | A further contested language boundary in the same region as §3.13; not investigated |
| DUTCH | 1,423 | Netherlands and Belgium (Flanders) both plausibly present; not sourced |
| HUNGARIAN | 1,673 | Hungary, Romania (Transylvania) and Slovakia all plausible; not sourced |
| LITHUANIAN | 1,356 | 18 hosts only |
| CZECH / SLOVAK | 1,298 / 979 | Another split-along-state-lines pair, unexamined |
| FINNISH | 1,255 | Note `keskustelu.kauppalehti.fi` (443, a discussion forum) is counted as ENGLISH by GDELT, not Finnish |
| SWEDISH / DANISH / NORWEGIAN | 1,103 / 957 / 566 | Sweden–Finland and Denmark–Norway–Faroes are real polity splits here |
| SLOVENIAN | 596 | |
| ARMENIAN / AZERBAIJANI | 609 / 303 | |
| TELUGU / MALAYALAM / TAMIL | 537 / 511 / 91 | All larger than Hindi by two orders of magnitude |
| THAI / LATVIAN | 392 / 329 | |

The pattern to carry forward: **GDELT's language mix reflects which national webs it successfully
crawls, not where news is produced.** Italian outranks Arabic by 2.9×; Greek outranks Arabic; Hindi is
absent while Telugu and Malayalam are present; Norwegian's largest English-language contributor is a
site whose copyright notice reads 2017.

---

## 4. Summary: which languages can and cannot meet a two-polity quorum

"Quorum possible" means: **at least two polities of publication, each with at least one outlet at
≥50 records/day, and the polity of publication sourced in §5.** "Resilient" adds the load-bearing
condition from Decision 2 on #20: **at least two polities each carrying more than one outlet**, so that
one outlet going dark does not remove a polity.

| Language | Rec/day | Polities with volume | Quorum? | Resilient? | Binding constraint |
|---|---:|---:|---|---|---|
| **English** | 158,432 | 5 | **Yes** | **Yes** — India 8, UK 4, US 5 | Not the quorum but the noise: the 10 highest-volume English hosts are all farms, dead archives, aggregators or non-news (§2.1) |
| **Spanish** | 37,118 | 8 | **Yes** | **Yes** — Spain 30+, Argentina 10, Mexico 7, Colombia 2, Chile 2 | Venezuela, Peru and Paraguay are one outlet each |
| **German** | 19,257 | 3 | **Yes** | **Yes** — Germany 45+, Austria 6, Switzerland 2–4 | Switzerland is an order of magnitude below Austria; `nzz.ch` and `blick.ch` at 0. **Reverses #17's "no pair"** |
| **Italian** | 16,634 | 2 | **Yes** | **Yes** — Italy 40+, Switzerland 3–4 | Swiss pole 234/day total, bursty. San Marino and Vatican at ~0. **Never previously assessed** |
| **Chinese** `Chinese` | 15,040 | 4 | **Yes** | **Yes** — PRC many, US diaspora 3 | ~38% of the volume is portals/UGC. Malaysia and Singapore 1 outlet each |
| **Russian** | 13,218 | 6 | **Yes** | **Yes** — Russia 30+, Ukraine 7, Belarus 2, Azerbaijan 2 | Bilingual Ukrainian outlets require `(domain, lang)` selection. **Reverses #17's "no pair"** |
| **Turkish** | 10,485 | 2–3 | **Yes** | **Yes** — Turkey 40+, N. Cyprus 3 | N. Cyprus present in only 4–6 of 96 slots. #17's cleanest pair collapses into one polity |
| **French** | 9,697 | 7 | **Yes** | **Yes** — France 25+, Belgium 3 (2 publishers), Senegal 4 | Senegal 5–8 slots of 96; Belgium's host count overstates it. **Upgrades #17's "marginal"** |
| **Greek** | 9,571 | 2 | **Yes** | **Yes** — Greece 40+, Cyprus 5 | Large financial-portal contingent excluded. **Never previously assessed** |
| **Portuguese** | 9,194 | 2 | **Yes** | **Yes** — Brazil 35+, Portugal 7 | Lusophone Africa entirely absent. **Upgrades #17's "marginal"** |
| **Chinese** `ChineseT` | 6,008 | 3 | **Yes** | **Yes** — Taiwan 8+, Hong Kong 4, US 2 | `blog.udn.com` (605/day, 96/96 slots) is a blog platform and the largest host |
| **Arabic** | 5,660 | 15 | **Yes** | **Yes** — Egypt 7, Morocco 3, Saudi 3, Lebanon 3, UAE 2, Algeria 2 | Egypt is 2.3× everyone else combined. Nine polities sit entirely below 50/day |
| **Serbo-Croatian** | 5,569 | 4 | **Yes** | **Yes** — Serbia 12, Croatia 7, Bosnia 8 | GDELT's three tags do not separate the polities; Bosnian output scatters across all three (§2.2) |
| **Romanian** | 5,187 | 2 | **Yes** | Partly — Romania 15+, Moldova 4 (1 above 50) | Moldova's largest host is an aggregator; its four publishers are all bursty. **Never previously assessed** |
| **Korean** | 4,057 | 2 | **Yes, conditionally** | Partly — S. Korea 8+, US diaspora 4 (1 above 50) | The DPRK — the polity a Korean index would want — is at **0**. Whether the Korean-American press is a useful second polity is a judgement, not a measurement |
| **Albanian** | 2,755 | 3 | **Yes** | **Yes** — Kosovo 8, Albania 6, N. Macedonia 6 | Kosovo out-publishes Albania. **Never previously assessed** |
| **Urdu** | 452 | 3 | **Marginal** | **No** — Pakistan 8, India 1 | India's single outlet is at 18/day and **unsourced**. Whole language is 0.12% of the census |
| **Catalan** | 672 | 2 | **Marginal** | **No** — Spain 8, Andorra 1 | Andorra is one newspaper at 44/day |
| **Indonesian** | 7,669 | 1 | **No** within the tag | — | Its second polity (Malaysia, 5 outlets) is reachable only through the separate `MALAY` tag — the same structure as Chinese and Ukrainian |
| **Vietnamese** | 6,136 | 1 | **No** | — | One polity. No diaspora or foreign-state Vietnamese-language source at any volume |
| **Ukrainian** | 4,743 | 1 | **No** within the tag | — | Russia does not publish in Ukrainian. The adversarial content exists — under `RUSSIAN` (§3.6) |
| **Japanese** | 2,124 | 1 | **No** | — | Structural: one state publishes Japanese. The largest `Japanese` host is `blog.udn.com`, a **Taiwanese blog platform** at 226/day |
| **Hebrew** | 835 | 1 | **No** | — | Structural. Everything divergent about Hebrew media is *within* Israel — the within-polity dissent #20 chose to give up |
| **Persian** | 139 | 5 | **No** | — | Polities exist (Iran, Afghanistan, Russia, UK, US) but the language is 0.04% of the census; Iran is one host at 36/day |
| **Hindi** | **3** | 0 | **No** | — | **Three records in 372,499.** No corpus to assess. India is in GDELT in English, not Hindi |

### Count

- **Quorum possible and resilient (≥2 polities each with >1 outlet): 13** — English, Spanish, German,
  Italian, `Chinese`, Russian, Turkish, French, Greek, Portuguese, `ChineseT`, Arabic, Serbo-Croatian.
- **Quorum possible but not resilient: 3** — Romanian, Korean (conditionally), and Arabic's lower tier.
- **Marginal: 2** — Urdu, Catalan.
- **Impossible: 6** — Japanese, Hebrew, Vietnamese, Persian, Hindi, and (within their own tag)
  Ukrainian and Indonesian.

### How this compares with #17

| | #17 (state-aligned vs independent) | This document (polity of publication) |
|---|---|---|
| Languages with a usable pole pair | 3 sourced + 1 conditional | **13 resilient + 3 non-resilient** |
| German | **No pair** | Quorum met, 3 polities |
| Russian | **No pair** | Quorum met, 6 polities |
| French | Marginal | Quorum met, 7 polities |
| Portuguese | Marginal | Quorum met, 2 polities |
| Chinese | Conditional on merging the two tags | Met **within each** tag as well as across |
| Turkish | Strongest pair in the document | Met, but #17's pair collapses into one polity |
| Japanese, Hebrew, Persian, Hindi | No pair | Still no quorum, **for a different reason** |

**The pattern is the one #20 predicted**: languages do not coincide with states, so a second polity
almost always exists wherever a language has real volume. The four languages that still fail are the
ones spoken in exactly one state (Japanese, Hebrew, Vietnamese) or barely present in GDELT at all
(Persian, Hindi) — and those are structural facts, not sourcing gaps.

**The axis also surfaced four languages nobody has considered, all of which meet the quorum**: Italian
(16,634/day — more than German), Greek (9,571 — more than Arabic), Romanian (5,187) and Albanian
(2,755). Against these, the project's current corpus languages are not where the evidence points.

---

## 5. The domain-to-polity table

**One citable source per row, or the row says so.** 226 rows; **200 carry a source for the polity of
publication, 26 do not** and are marked `source not obtained`. Those 26 are leads, not evidence, and no
verdict in §3 or §4 rests on a polity label taken from them.

### 5.1 How to read it, and four cautions about the source

- **`Rec/day` aggregates the domain and all its subdomains**, and sums across all languages. The §3
  tables instead report the **exact host** GDELT emits. So a figure here can be larger than the §3
  figure for the same outlet — `obozrevatel.com` is 101 `RUSSIAN` on the bare host in §3.6 and 334
  across all subdomains and languages here. Neither is wrong; they answer different questions.
- **`WD` = Wikidata, retrieved 2026-08-02**, matched by `P856` (official website) against the domain and
  its `www`/`http` variants, reading `P159` (headquarters location), `P291` (place of publication),
  `P17` (country), `P127` (owned by) and `P749` (parent organization). Owner domicile is a **second hop**:
  the owner entity's own `P17`/`P159`. **`Imprint` = the outlet's own imprint / contact / legal-notice
  page, retrieved 2026-08-02**, quoted in the note column where it is load-bearing.
- **Caution 1 — Wikidata's `P17` is sometimes the brand's country, not the place of publication.**
  `cnnturk.com` carries `P17 = United States` while its `P159` is Bağcılar, Istanbul. **This document
  takes polity of publication from `P159`/`P291` in preference to `P17`** and flags the discrepancy in
  the note rather than silently choosing. `hkcd.com` (`P17` = People's Republic of China, a Hong Kong
  daily) and `asahi.com` (`P17` = Japan **and** United States) are the other visible cases.
- **Caution 2 — Wikidata is a secondary source and it is wrong sometimes.** `vov.vn`'s owner is recorded
  as Vietnam's Ministry of Finance, which is almost certainly a data error for a state broadcaster; the
  row says so. Where a row's polity rests on Wikidata alone and the outlet is politically consequential,
  the note says the label is weakly sourced.
- **Caution 3 — "not stated in source" is not "independent".** Many rows have a sourced polity and no
  ownership statement. That is an absence of data about ownership, and nothing follows from it.
- **Caution 4 — ownership chains were traced exactly one hop.** Where the owner is itself a subsidiary,
  the ultimate domicile is not established. `n-tv.de` is the clearest example: Wikidata gives RTL
  Deutschland [Germany], while the outlet's own imprint discloses the chain onward to RTL Group
  (Luxembourg-domiciled) and Bertelsmann. Both are recorded; neither is followed further.

### 5.2 The cases where polity of publication and country of ownership genuinely differ

These are the rows that justify #20's insistence on two columns, and the reason `RSS_METADATA`'s single
`country` field cannot express the axis:

| Domain | Publishes from | Owned from | Source |
|---|---|---|---|
| `scmp.com` | **Hong Kong** | mainland China (Alibaba Group) | WD |
| `heute.at` | **Austria** (Walfischgasse 13, 1010 Wien) | partly **Liechtenstein** — `Alta GmbH, Vaduz`, 36.92% | the outlet's own imprint |
| `blic.rs` | **Serbia** (Belgrade) | **Switzerland** (Ringier) | WD |
| `vecernji.hr` | **Croatia** (Zagreb) | **Austria** (Styria Media Group) | WD |
| `20minutes.fr` | **France** (Levallois-Perret) | **Belgium** (Rossel, hq Brussels) | WD |
| `lastampa.it` | **Italy** (Turin) | **Netherlands** (Fiat Chrysler Automobiles domicile) | WD |
| `haaretz.co.il` | **Israel** | partly **Germany** (DuMont Media Group) | WD |
| `cnnturk.com` | **Turkey** (Istanbul) | Turkey (Demirören) **and United States** (WarnerMedia) | WD |
| `n-tv.de` | **Germany** (Cologne) | Germany (RTL Deutschland) → **Luxembourg** (RTL Group) | WD + imprint |
| `163.com` | **China** (Hangzhou) | listed via a **Cayman Islands** holding company | WD |
| `segye.com` | **South Korea** | Unification Church — Japan, South Korea, US and Portugal | WD |
| `lecourrier.vn` | **Vietnam** (Hanoi) | Vietnam (Ministry of Information and Communications) | WD |

And four cases where the **ccTLD points at the wrong polity or at none**, which is why §1.4 refuses to
treat it as a source:

| Domain | ccTLD suggests | Actually publishes from | Source |
|---|---|---|---|
| `storm.mg` | Madagascar | **Taiwan** (Taipei) | WD |
| `srna.rs` | Serbia | **Bosnia and Herzegovina** | WD |
| `obozrevatel.com` | nothing | **Ukraine** (Kyiv) | WD |
| `boerse-express.com` | nothing | **Austria** (A-1080 Wien) | WD + imprint |

### 5.3 The table

#### ENGLISH

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `timesofindia.indiatimes.com` | 1065 (215) | 76 | ENGLISH 1065 | **India** | Mumbai | The Times Group [India] | WD |  |
| `thehindu.com` | 748 (165) | 72 | ENGLISH 748 | **India** | Chennai | not stated in source | WD |  |
| `hindustantimes.com` | 378 (79) | 35 | ENGLISH 378 | **India** | New Delhi | HT Media / Birla family [India] | WD |  |
| `theguardian.com` | 286 (87) | 59 | ENGLISH 286 | **United Kingdom** | London | Guardian Media Group [UK] | WD |  |
| `independent.co.uk` | 294 (134) | 22 | ENGLISH 294 | **United Kingdom** | London | Alexander Lebedev | WD | owner domicile not resolved |
| `dailymail.com` | 676 (134) | 67 | ENGLISH 676 | **United Kingdom** | — | — | **source not obtained** | no Wikidata P856 match; polity of publication not sourced |
| `latimes.com` | 301 (82) | 51 | ENGLISH 281, SPANISH 20 | **United States** | El Segundo, CA | Patrick Soon-Shiong | WD |  |
| `manilatimes.net` | 716 (148) | 45 | ENGLISH 716 | **Philippines** | — | not stated in source | WD |  |
| `perthnow.com.au` | 300 (66) | 25 | ENGLISH 300 | **Australia** | Perth | Seven West Media [Australia] | WD |  |
| `straitstimes.com` | 63 (12) | 6 | ENGLISH 63 | **Singapore** | — | Singapore Press Holdings [Singapore] | WD |  |
| `scmp.com` | 115 (31) | 30 | ENGLISH 115 | **Hong Kong** | Tai Po, Hong Kong | Alibaba Group [PRC] | WD | **publication ≠ ownership**: published in Hong Kong, owned from mainland China |
| `arabnews.com` | 81 (16) | 17 | ENGLISH 81 | **Saudi Arabia** | Jeddah | Saudi Research and Media Group [Saudi Arabia] | WD |  |

#### SPANISH

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `larazon.es` | 463 (118) | 42 | SPANISH 462, CATALAN 1 | **Spain** | Madrid | Grupo Planeta [Spain] | WD |  |
| `abc.es` | 392 (66) | 62 | SPANISH 391, GALICIAN 1 | **Spain** | Madrid | Vocento [Spain] | WD |  |
| `europapress.es` | 403 (121) | 44 | SPANISH 400, ENGLISH 2, GALICIAN 1 | **Spain** | Madrid | not stated in source | WD |  |
| `elpais.com` | 180 (27) | 28 | SPANISH 150, ENGLISH 30 | **Spain** | Madrid | Grupo PRISA [Spain] | WD |  |
| `elmundo.es` | 148 (29) | 40 | SPANISH 148 | **Spain** | Madrid | Unidad Editorial [Spain] | WD |  |
| `cadena3.com` | 315 (18) | 22 | SPANISH 315 | **Argentina** | — | not stated in source | WD |  |
| `lanacion.com.ar` | 214 (18) | 22 | SPANISH 214 | **Argentina** | Buenos Aires | Bartolomé Mitre | WD |  |
| `clarin.com` | 159 (14) | 33 | SPANISH 159 | **Argentina** | Buenos Aires | Clarín Group [Argentina] | WD |  |
| `infobae.com` | 183 (36) | 18 | SPANISH 183 | **Argentina** | Buenos Aires | Grupo Infobae | WD |  |
| `eluniversal.com.mx` | 186 (42) | 12 | SPANISH 186 | **Mexico** | Mexico City | not stated in source | WD |  |
| `excelsior.com.mx` | 211 (71) | 19 | SPANISH 211 | **Mexico** | Mexico City | Grupo Imagen [Mexico] | WD |  |
| `biobiochile.cl` | 228 (89) | 16 | SPANISH 228 | **Chile** | Concepción | not stated in source | WD |  |
| `latercera.com` | 163 (18) | 21 | SPANISH 163 | **Chile** | Las Condes | Copesa [Chile] | WD |  |
| `semana.com` | 171 (50) | 24 | SPANISH 171 | **Colombia** | — | not stated in source | WD |  |
| `eltiempo.com` | 150 (13) | 30 | SPANISH 148, ENGLISH 2 | **Colombia** | Bogotá | not stated in source | WD |  |
| `larepublica.pe` | 156 (15) | 24 | SPANISH 156 | **Peru** | Lima | not stated in source | WD |  |
| `abc.com.py` | 147 (45) | 19 | SPANISH 147 | **Paraguay** | Asunción | not stated in source | WD |  |
| `ciudadccs.info` | 179 (39) | 37 | SPANISH 179 | **Venezuela** | Caracas | Venezuelan Ministry of Communications and Information [Venezuela] | WD | #17 marked this row unusable for lack of any source; the polity axis sources both columns |

#### GERMAN

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `merkur.de` | 691 (223) | 31 | GERMAN 691 | **Germany** | Munich | Ippen Digital / Dirk Ippen [Germany] | WD+Imprint |  |
| `hna.de` | 613 (87) | 73 | GERMAN 613 | **Germany** | Kassel | Ippen group [Germany] | WD |  |
| `kreiszeitung.de` | 527 (115) | 45 | GERMAN 527 | **Germany** | Syke, Lower Saxony | Ippen Digital [Germany] | WD |  |
| `welt.de` | 459 (92) | 56 | GERMAN 459 | **Germany** | Berlin | Axel Springer SE [Germany] | WD |  |
| `zeit.de` | 332 (84) | 67 | GERMAN 332 | **Germany** | Hamburg | Holtzbrinck Publishing Group | WD+Imprint | imprint: Zeitverlag Gerd Bucerius GmbH & Co. KG, 20095 Hamburg |
| `n-tv.de` | 377 (136) | 28 | GERMAN 377 | **Germany** | Cologne | RTL Deutschland [Germany] | WD+Imprint | imprint adds: "ein Unternehmen der RTL Deutschland GmbH, die zur RTL Group gehört" — RTL Group is Luxembourg-domiciled, **publication ≠ ownership** |
| `sueddeutsche.de` | 160 (30) | 23 | GERMAN 160 | **Germany** | Munich | not stated in source | WD |  |
| `bild.de` | 99 (34) | 21 | GERMAN 99 | **Germany** | Berlin | Axel Springer SE [Germany] | WD |  |
| `handelsblatt.com` | 169 (42) | 35 | GERMAN 169 | **Germany** | Düsseldorf | Handelsblatt Media Group [Germany] | WD |  |
| `t-online.de` | 213 (89) | 24 | GERMAN 213 | **Germany** | Berlin | Ströer Media / Deutsche Telekom | WD |  |
| `heute.at` | 226 (32) | 13 | GERMAN 226 | **Austria** | Walfischgasse 13, 1010 Wien | Heute Verlag Holding; shareholder **Alta GmbH, Vaduz (36.92%)** [Liechtenstein] | Imprint | **publication ≠ ownership**, disclosed by the outlet itself. No Wikidata P17 |
| `kurier.at` | 101 (49) | 15 | GERMAN 101 | **Austria** | Leopold-Ungar-Platz 1, A-1190 Wien | KURIER Zeitungsverlag / Mediaprint [Austria] | WD+Imprint |  |
| `vol.at` | 134 (28) | 29 | GERMAN 124, ENGLISH 10 | **Austria** | — | not stated in source | WD |  |
| `ots.at` | 96 (48) | 18 | GERMAN 88, ENGLISH 8 | **Austria** | — | Austria Press Agency [Austria] | WD |  |
| `meinbezirk.at` | 161 (19) | 19 | GERMAN 161 | **Austria** | 1060 Wien | RegionalMedien Austria AG [Austria] | Imprint | no Wikidata P856 match; sourced to its own imprint |
| `tele.at` | 124 (23) | 24 | GERMAN 124 | **Austria** | — | not stated in source | WD | Wikidata gives language German and no country; polity **weakly sourced** |
| `boerse-express.com` | 193 (47) | 28 | GERMAN 193 | **Austria** | A-1080 Wien | boerse-express.com GmbH & Co. KG | WD+Imprint | a `.com` domain publishing from Vienna — see §1.4 on why ccTLD is not a source |
| `watson.ch` | 104 (33) | 33 | GERMAN 104 | **Switzerland** | Zurich | CH Media [Switzerland] | WD |  |
| `20min.ch` | 61 (16) | 6 | GERMAN 61 | **Switzerland** | — | — | **source not obtained** | no Wikidata P856 match |
| `tagesanzeiger.ch` | 46 (2) | 21 | GERMAN 46 | **Switzerland** | Zurich | TX Group [Switzerland] | WD |  |
| `srf.ch` | 31 (5) | 5 | GERMAN 31 | **Switzerland** | Zurich | Swiss Broadcasting Corporation [Switzerland] | WD |  |

#### FRENCH

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `sudouest.fr` | 329 (116) | 44 | FRENCH 329 | **France** | Bordeaux | not stated in source | WD |  |
| `ladepeche.fr` | 242 (55) | 24 | FRENCH 242 | **France** | Toulouse | not stated in source | WD |  |
| `ledauphine.com` | 137 (42) | 38 | FRENCH 137 | **France** | Grenoble | EBRA Group [France] | WD |  |
| `bfmtv.com` | 159 (67) | 24 | FRENCH 159 | **France** | Paris | RMC BFM [France] | WD |  |
| `leparisien.fr` | 113 (19) | 42 | FRENCH 113 | **France** | Paris | LVMH [France] | WD |  |
| `20minutes.fr` | 125 (16) | 45 | FRENCH 125 | **France** | Levallois-Perret | Rossel [hq Brussels, **Belgium**] | WD | **publication ≠ ownership** |
| `franceinfo.fr` | 175 (36) | 26 | FRENCH 175 | **France** | Paris | Radio France + France Télévisions [France] | WD |  |
| `dhnet.be` | 113 (23) | 11 | FRENCH 113 | **Belgium** | Rue des Francs 79, 1040 Bruxelles | IPM group | WD+Imprint | same publisher address as `lalibre.be` — one publisher, two hosts |
| `lalibre.be` | 97 (5) | 13 | FRENCH 97 | **Belgium** | Rue des Francs 79, 1040 Bruxelles | IPM group | WD+Imprint | same publisher address as `dhnet.be` |
| `lavenir.net` | 67 (19) | 6 | FRENCH 67 | **Belgium** | Namur | not stated in source | WD |  |
| `rtbf.be` | 34 (2) | 17 | FRENCH 34 | **Belgium** | Brussels | French Community of Belgium [Belgium] | WD |  |
| `lapresse.ca` | 70 (10) | 7 | FRENCH 70 | **Canada** | Montreal | Gesca Limitée [Canada] | WD |  |
| `ledevoir.com` | 49 (9) | 14 | FRENCH 49 | **Canada** | Montreal | not stated in source | WD |  |
| `lecourrier.vn` | 66 (9) | 16 | FRENCH 66 | **Vietnam** | Hanoi | Ministry of Information and Communications [Vietnam] | WD | French-language daily published from Hanoi and state-owned |
| `letemps.ch` | 38 (9) | 7 | FRENCH 38 | **Switzerland** | — | Fondation Aventinus [Switzerland] | WD |  |
| `senenews.com` | 65 (26) | 5 | FRENCH 65 | **Senegal** | — | — | **source not obtained** | no Wikidata P856 match; imprint page yielded no publisher block. Polity **not sourced** |
| `seneweb.com` | 56 (12) | 7 | FRENCH 56 | **Senegal** | — | — | **source not obtained** | Wikidata item exists but carries no P17/P159/P291 |
| `pressafrik.com` | 52 (15) | 8 | FRENCH 52 | **Senegal** | — | — | **source not obtained** | no page obtained at any candidate path |
| `lessentiel.lu` | 56 (14) | 5 | FRENCH 54, GERMAN 2 | **Luxembourg** | — | — | **source not obtained** | no Wikidata P856 match; imprint not extractable |

#### ITALIAN

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `ansa.it` | 770 (255) | 63 | ITALIAN 751, ARABIC 12, ENGLISH 3 | **Italy** | Rome | not stated in source | WD | national wire agency |
| `ilpost.it` | 369 (50) | 23 | ITALIAN 369 | **Italy** | Milan | not stated in source | WD |  |
| `ilmessaggero.it` | 273 (65) | 36 | ITALIAN 273 | **Italy** | Rome | Caltagirone Editore [Italy] | WD |  |
| `corriere.it` | 202 (60) | 7 | ITALIAN 202 | **Italy** | Milan | RCS MediaGroup [Italy] | WD |  |
| `ilfattoquotidiano.it` | 130 (21) | 24 | ITALIAN 130 | **Italy** | Italy | not stated in source | WD |  |
| `ilgiornale.it` | 123 (30) | 22 | ITALIAN 123 | **Italy** | Milan | Fininvest [Italy] | WD |  |
| `lastampa.it` | 135 (46) | 11 | ITALIAN 135 | **Italy** | Turin | Fiat Chrysler Automobiles [**Netherlands**] | WD | **publication ≠ ownership** as recorded by the source |
| `laregione.ch` | 75 (30) | 16 | ITALIAN 75 | **Switzerland** | Bellinzona | not stated in source | WD+Imprint | imprint: Via Ghiringhelli 9, 6500 Bellinzona |
| `cdt.ch` | 54 (29) | 8 | ITALIAN 54 | **Switzerland** | Muzzano / Lugano | Gruppo Corriere del Ticino | WD+Imprint | imprint: Via Industria, 6933 Muzzano (Lugano) |
| `rsi.ch` | 25 (0) | 7 | ITALIAN 25 | **Switzerland** | Lugano | Swiss Broadcasting Corporation [Switzerland] | WD |  |
| `tio.ch` | 80 (32) | 6 | ITALIAN 80 | **Switzerland** | — | — | **source not obtained** | no Wikidata P856 match; imprint yielded only an email. Polity **not sourced** |

#### GREEK

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `protothema.gr` | 219 (17) | 40 | GREEK 219 | **Greece** | Marousi | not stated in source | WD |  |
| `tanea.gr` | 192 (51) | 51 | GREEK 192 | **Greece** | Athens | Alter Ego Media [Greece] | WD |  |
| `kathimerini.gr` | 147 (37) | 10 | GREEK 147 | **Greece** | Athens | Aristidis Alafouzos | WD |  |
| `in.gr` | 176 (36) | 32 | GREEK 175, ENGLISH 1 | **Greece** | Athens | Alter Ego Media [Greece] | WD | P17 absent; polity taken from P159 Athens |
| `efsyn.gr` | 125 (40) | 9 | GREEK 125 | **Greece** | — | not stated in source | WD | Wikidata item carries no country or HQ; polity **weakly sourced** |
| `kathimerini.com.cy` | 132 (5) | 9 | GREEK 132 | **Cyprus** | — | not stated in source | WD | Cypriot edition of an Athens title — polity of publication Cyprus, editorial lineage Greece |
| `sigmalive.com` | 133 (28) | 16 | GREEK 133 | **Cyprus** | Nicosia / Strovolos | not stated in source | WD |  |
| `dialogos.com.cy` | 85 (12) | 20 | GREEK 85 | **Cyprus** | Nicosia | Dialogos Media Group | WD+Imprint |  |
| `philenews.com` | 122 (24) | 36 | GREEK 122 | **Cyprus** | — | — | **source not obtained** | no Wikidata P856 match; front page names `HARCO TRADING LTD` but states no place. Polity **not sourced** |

#### PORTUGUESE

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `globo.com` | 1033 (186) | 0 | PORTUGUESE 1033 | **Brazil** | — | Globo [Brazil] | WD | the `g1.globo.com` and `oglobo.globo.com` hosts |
| `estadao.com.br` | 135 (56) | 28 | PORTUGUESE 135 | **Brazil** | São Paulo | OESP Group [Brazil] | WD |  |
| `correiobraziliense.com.br` | 144 (33) | 26 | PORTUGUESE 144 | **Brazil** | — | not stated in source | WD |  |
| `observador.pt` | 201 (42) | 30 | PORTUGUESE 201 | **Portugal** | — | not stated in source | WD |  |
| `dnoticias.pt` | 94 (33) | 6 | PORTUGUESE 94 | **Portugal** | Funchal, Madeira | not stated in source | WD |  |
| `rtp.pt` | 55 (19) | 21 | PORTUGUESE 55 | **Portugal** | Lisbon | Government of Portugal [Portugal] | WD |  |
| `record.pt` | 53 (14) | 10 | PORTUGUESE 53 | **Portugal** | — | Medialivre [Portugal] | WD |  |
| `publico.pt` | 0 (0) | 0 | — | **Portugal** | Lisbon | Sonae [Portugal] | WD | at 0 records/day in this census |
| `sapo.pt` | 831 (143) | 50 | PORTUGUESE 831 | **Portugal** | Lisbon | Altice Portugal [Portugal] | WD | excluded as a portal in §3.8; listed because two editorial sub-sites run on it |

#### ARABIC

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `dostor.org` | 716 (233) | 47 | ARABIC 716 | **Egypt** | Cairo | Sayyid Badawi; Essam Ismail Fahmy | WD |  |
| `vetogate.com` | 537 (188) | 24 | ARABIC 537 | **Egypt** | Cairo | not stated in source | WD |  |
| `almasryalyoum.com` | 250 (67) | 12 | ARABIC 250 | **Egypt** | Cairo | not stated in source | WD |  |
| `gate.ahram.org.eg` | 267 (72) | 17 | ARABIC 267 | **Egypt** | Cairo | state-owned per RSF (see #17) | **source not obtained** | no Wikidata P856 match on this host; polity corroborated by ccTLD only — **not sourced to this document's standard** |
| `shorouknews.com` | 408 (103) | 75 | ARABIC 408 | **Egypt** | — | — | **source not obtained** | no Wikidata P856 match |
| `albayan.ae` | 134 (59) | 7 | ARABIC 134 | **United Arab Emirates** | Dubai | Dubai Media [UAE] | WD |  |
| `emaratalyoum.com` | 92 (17) | 16 | ARABIC 92 | **United Arab Emirates** | — | — | **source not obtained** | no Wikidata P856 match |
| `alriyadh.com` | 55 (41) | 5 | ARABIC 55 | **Saudi Arabia** | Riyadh | not stated in source | WD |  |
| `albiladpress.com` | 127 (32) | 8 | ARABIC 127 | **Bahrain** | — | not stated in source | WD |  |
| `aljazeera.net` | 123 (42) | 24 | ARABIC 123 | **Qatar** | Doha (also London, Washington DC) | Al Jazeera Media Network [Qatar] | WD | the multi-site case #21 names: a Qatari network with London and Washington operations. Polity of publication of **this domain** is Qatar; the bureaux are not separate polities of publication |
| `hespress.com` | 75 (11) | 23 | ARABIC 75 | **Morocco** | — | not stated in source | WD |  |
| `almanar.com.lb` | 61 (15) | 29 | ARABIC 61 | **Lebanon** | Haret Hreik | Hezbollah [Lebanon] | WD | #17 recorded this as source-not-obtained; ownership is now sourced |
| `ennaharonline.com` | 51 (7) | 4 | ARABIC 51 | **Algeria** | — | not stated in source | WD |  |
| `sana.sy` | 164 (47) | 36 | ARABIC 50, FRENCH 37, ENGLISH 26 | **Syria** | Damascus | Ministry of Information (self-disclosed, per #17) | **source not obtained** | no Wikidata P856 match; #17's self-disclosure quote stands as the source for ownership |

#### RUSSIAN

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `rg.ru` | 421 (126) | 24 | RUSSIAN 421 | **Russia** | Moscow | Government of Russia [Russia] | WD |  |
| `ria.ru` | 349 (83) | 73 | RUSSIAN 349 | **Russia** | Moscow | Rossiya Segodnya [Russia] | WD |  |
| `vesti.ru` | 326 (104) | 26 | RUSSIAN 326 | **Russia** | Moscow | VGTRK [Russia] | WD |  |
| `iz.ru` | 289 (55) | 45 | RUSSIAN 289 | **Russia** | Moscow | National Media Group [Russia] | WD |  |
| `kommersant.ru` | 268 (46) | 49 | RUSSIAN 268 | **Russia** | Moscow | Alisher Usmanov | WD |  |
| `lenta.ru` | 270 (45) | 33 | RUSSIAN 270 | **Russia** | Moscow | Rambler&Co [Russia] | WD |  |
| `life.ru` | 330 (144) | 22 | RUSSIAN 330 | **Russia** | Moscow | Aram Gabrelyanov | WD |  |
| `russian.rt.com` | 130 (44) | 21 | RUSSIAN 130 | **Russia** | — | — | **source not obtained** | no Wikidata P856 match on this host; EU Reg. 2022/350 (per #17) names RT entities but not this edition |
| `24tv.ua` | 513 (101) | 61 | UKRAINIAN 303, RUSSIAN 210 | **Ukraine** | Kyiv | Teleradiocompany "Lux" [Ukraine] | WD | emits 242 UKRAINIAN + 199 RUSSIAN — select on (domain, lang) |
| `korrespondent.net` | 248 (44) | 24 | UKRAINIAN 141, RUSSIAN 107 | **Ukraine** | — | Korrespondent | WD |  |
| `unn.ua` | 222 (86) | 29 | UKRAINIAN 117, RUSSIAN 105 | **Ukraine** | Kyiv | not stated in source | WD |  |
| `obozrevatel.com` | 334 (96) | 29 | UKRAINIAN 184, RUSSIAN 150 | **Ukraine** | Kyiv | Mykhailo Brodskyy | WD | a `.com` domain published from Kyiv — ccTLD would have missed it |
| `focus.ua` | 187 (66) | 13 | RUSSIAN 104, UKRAINIAN 83 | **Ukraine** | Kyiv | not stated in source | WD |  |
| `ukrinform.ua` | 107 (81) | 8 | UKRAINIAN 107 | **Ukraine** | Kyiv | Cabinet of Ministers of Ukraine [Ukraine] | WD |  |
| `unian.net` | 141 (31) | 34 | RUSSIAN 141 | **Ukraine** | — | — | **source not obtained** | no Wikidata P856 match on this host |
| `sb.by` | 132 (59) | 13 | RUSSIAN 114, ENGLISH 18 | **Belarus** | Minsk | not stated in source | WD |  |
| `ont.by` | 62 (0) | 10 | RUSSIAN 62 | **Belarus** | Minsk | Ministry of Information of Belarus [Belarus] | WD |  |
| `vesti.az` | 80 (19) | 7 | RUSSIAN 80 | **Azerbaijan** | — | — | **source not obtained** | no Wikidata P856 match |
| `gazeta.kg` | 86 (31) | 12 | RUSSIAN 86 | **Kyrgyzstan** | — | — | **source not obtained** | no Wikidata P856 match |
| `mignews.com` | 161 (38) | 42 | RUSSIAN 161 | ****not sourced**** | — | — | **source not obtained** | widely associated with Israel; no Wikidata P17/P159, no reachable imprint. Listed as a lead |

#### TURKISH

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `sabah.com.tr` | 220 (47) | 38 | TURKISH 220 | **Turkey** | Beşiktaş, Istanbul | Çalık Holding [Turkey] | WD |  |
| `sozcu.com.tr` | 202 (53) | 21 | TURKISH 202 | **Turkey** | Istanbul | not stated in source | WD |  |
| `birgun.net` | 435 (102) | 42 | TURKISH 435 | **Turkey** | Şişli, Istanbul | not stated in source | WD | #17 recorded polity/ownership as not obtained; polity is now sourced |
| `hurriyet.com.tr` | 147 (16) | 20 | TURKISH 146, ALBANIAN 1 | **Turkey** | Bağcılar, Istanbul | Demirören Group [Turkey] | WD |  |
| `milliyet.com.tr` | 173 (58) | 20 | TURKISH 173 | **Turkey** | Bağcılar, Istanbul | Demirören Group [Turkey] | WD |  |
| `trthaber.com` | 83 (11) | 6 | TURKISH 83 | **Turkey** | Ankara | Turkish Radio and Television Corporation [Turkey] | WD |  |
| `cnnturk.com` | 110 (21) | 27 | TURKISH 110 | **Turkey** | Bağcılar, Istanbul | Demirören Group [Turkey] + WarnerMedia [**United States**] | WD | **publication ≠ ownership**. Note Wikidata's `P17` for this item is *United States* — the brand's country, not the place of publication. This document uses `P159`/`P291`; see §5.1 |
| `aa.com.tr` | 216 (41) | 18 | TURKISH 117, ENGLISH 99 | **Turkey** | — | — | **source not obtained** | no Wikidata P856 match; #17 could not source it either. Still **unsourced** |
| `kibrisgazetesi.com` | 56 (32) | 5 | TURKISH 56 | **Northern Cyprus** | — | not stated in source | WD | Wikidata records the polity of publication as Northern Cyprus explicitly |
| `kibrispostasi.com` | 94 (0) | 6 | TURKISH 94 | **Northern Cyprus** | Nicosia | not stated in source | WD | P17 absent; polity taken from P159 Nicosia |
| `havadiskibris.com` | 54 (0) | 4 | TURKISH 54 | **Northern Cyprus** | — | — | **source not obtained** | no Wikidata P856 match |
| `anlatilaninotesi.com.tr` | 77 (27) | 11 | TURKISH 77 | ****not sourced**** | — | — | **source not obtained** | Sputnik's Turkish service under its post-2022 brand; polity of publication not sourced |

#### CHINESE / CHINESET

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `news.cn` | 411 (87) | 10 | ENGLISH 233, Chinese 111, ARABIC 46 | **People's Republic of China** | Beijing | State Council of the PRC [PRC] | WD | Xinhua |
| `people.com.cn` | 205 (83) | 0 | Chinese 155, ARABIC 21, FRENCH 18 | **People's Republic of China** | Beijing | Central Committee of the Chinese Communist Party [PRC] | WD |  |
| `chinanews.com.cn` | 102 (21) | 13 | Chinese 102 | **People's Republic of China** | Beijing | Overseas Chinese Affairs Office [PRC] | WD |  |
| `163.com` | 1536 (444) | 69 | Chinese 1536 | **People's Republic of China** | Hangzhou | NetEase | WD | **publication ≠ ownership**: Wikidata records the entity's country as both PRC and **Cayman Islands** (the listed holding company). Excluded as a portal in §3.5 |
| `zaobao.com.sg` | 92 (37) | 11 | Chinese 92 | **Singapore** | — | — | **source not obtained** | not queried; polity corroborated by ccTLD only |
| `orientaldaily.com.my` | 135 (59) | 12 | Chinese 135 | **Malaysia** | — | not stated in source | WD |  |
| `cna.com.tw` | 578 (188) | 44 | ChineseT 578 | **Taiwan** | Taipei | not stated in source | WD |  |
| `setn.com` | 627 (166) | 60 | ChineseT 627 | **Taiwan** | Taipei | Sanlih E-Television [Taiwan] | WD |  |
| `ltn.com.tw` | 744 (191) | 0 | ChineseT 738, ENGLISH 6 | **Taiwan** | Taipei | not stated in source | WD | the `news.ltn.com.tw` host |
| `chinatimes.com` | 419 (85) | 33 | ChineseT 419 | **Taiwan** | Taipei | China Times Group [Taiwan] | WD |  |
| `udn.com` | 1382 (370) | 33 | ChineseT 1058, Japanese 226, Chinese 87 | **Taiwan** | New Taipei City | United Daily News Group [Taiwan] | WD | note `blog.udn.com` is a **blog platform** on the same second-level domain and is excluded |
| `ettoday.net` | 448 (65) | 31 | ChineseT 448 | **Taiwan** | — | Eastern Media International [Taiwan] | WD |  |
| `newtalk.tw` | 201 (64) | 23 | ChineseT 201 | **Taiwan** | — | not stated in source | WD |  |
| `cts.com.tw` | 199 (43) | 0 | ChineseT 199 | **Taiwan** | Taipei | not stated in source | WD | the `news.cts.com.tw` host |
| `storm.mg` | 174 (27) | 17 | ChineseT 174 | **Taiwan** | Taipei | not stated in source | WD | a `.mg` (Madagascar) domain published from Taipei — a clean counter-example to ccTLD inference |
| `orientaldaily.on.cc` | 15 (0) | 1 | ChineseT 15 | **Hong Kong** | Tai Po, Hong Kong | Oriental Media Group | WD |  |
| `hkcd.com` | 81 (49) | 10 | ChineseT 81 | **Hong Kong** | — | not stated in source | WD | Wikidata records `P17` as **People's Republic of China**, not Hong Kong. Recorded as stated; the discrepancy is the finding, not an error to smooth over |
| `wenweipo.com` | 75 (5) | 6 | ChineseT 75 | **Hong Kong** | — | — | **source not obtained** | not resolved |
| `epochtimes.com` | 129 (14) | 10 | Chinese 129 | **United States** | New York City | Epoch Media Group [United States] | WD | Chinese-language, published from the US |
| `ntdtv.com` | 72 (38) | 8 | ChineseT 72 | **United States** | New York City | Epoch Media Group / Falun Gong [United States] | WD |  |

#### BCMS / ALBANIAN / ROMANIAN

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `politika.rs` | 348 (92) | 16 | SERBIAN 339, BOSNIAN 7, ENGLISH 1 | **Serbia** | Belgrade | Politika AD [Serbia] | WD |  |
| `blic.rs` | 274 (72) | 59 | SERBIAN 269, BOSNIAN 3, CROATIAN 2 | **Serbia** | Belgrade | Ringier [**Switzerland**] | WD | **publication ≠ ownership** |
| `informer.rs` | 228 (104) | 14 | SERBIAN 217, BOSNIAN 7, CROATIAN 4 | **Serbia** | Belgrade | not stated in source | WD |  |
| `danas.rs` | 182 (30) | 63 | SERBIAN 161, BOSNIAN 16, CROATIAN 5 | **Serbia** | — | not stated in source | WD |  |
| `tanjug.rs` | 179 (58) | 17 | SERBIAN 129, BOSNIAN 40, CROATIAN 5 | **Serbia** | Belgrade | Government of Serbia [Serbia] | WD |  |
| `rts.rs` | 64 (26) | 18 | SERBIAN 64 | **Serbia** | Belgrade | Radio Television of Serbia [Serbia] | WD |  |
| `index.hr` | 772 (221) | 59 | CROATIAN 751, BOSNIAN 21 | **Croatia** | — | not stated in source | WD | Wikidata item has no P17/P159; polity **weakly sourced** |
| `vecernji.hr` | 116 (30) | 28 | CROATIAN 110, BOSNIAN 6 | **Croatia** | Zagreb | Styria Media Group [**Austria**] | WD | **publication ≠ ownership** |
| `jutarnji.hr` | 95 (27) | 13 | CROATIAN 91, BOSNIAN 3, SERBIAN 1 | **Croatia** | — | Europapress Holding [Croatia] | WD |  |
| `hrt.hr` | 23 (5) | 0 | CROATIAN 22, BOSNIAN 1 | **Croatia** | Zagreb | Croatian Radiotelevision [Croatia] | WD |  |
| `avaz.ba` | 159 (42) | 43 | BOSNIAN 76, CROATIAN 72, SERBIAN 11 | **Bosnia and Herzegovina** | Avaz Twist Tower, Sarajevo | not stated in source | WD | emits BOSNIAN, CROATIAN **and** SERBIAN — see §2.2 |
| `oslobodjenje.ba` | 76 (10) | 13 | CROATIAN 37, BOSNIAN 29, SERBIAN 10 | **Bosnia and Herzegovina** | Sarajevo | Sarajevska Pivara [BiH] | WD |  |
| `klix.ba` | 78 (33) | 15 | BOSNIAN 42, CROATIAN 33, SERBIAN 3 | **Bosnia and Herzegovina** | — | not stated in source | WD |  |
| `federalna.ba` | 71 (7) | 9 | BOSNIAN 48, CROATIAN 20, SERBIAN 3 | **Bosnia and Herzegovina** | Sarajevo | RTV of the Federation of Bosnia and Herzegovina [BiH] | WD | a Federation institution |
| `rtrs.tv` | 100 (38) | 7 | SERBIAN 100 | **Bosnia and Herzegovina** | Banja Luka | Radio Television of Republika Srpska [BiH] | WD | a Republika Srpska institution — same polity of publication as `federalna.ba` in law, different sub-state authority. See §3.13 |
| `srna.rs` | 43 (8) | 7 | SERBIAN 43 | **Bosnia and Herzegovina** | — | not stated in source | WD | a `.rs` domain whose polity of publication is Bosnia — ccTLD would have assigned Serbia |
| `rtcg.me` | 49 (9) | 6 | BOSNIAN 25, SERBIAN 16, CROATIAN 8 | **Montenegro** | Podgorica | not stated in source | WD |  |
| `dan.co.me` | 38 (15) | 5 | BOSNIAN 18, CROATIAN 10, SERBIAN 10 | **Montenegro** | Podgorica | not stated in source | WD |  |
| `sputnikportal.rs` | 65 (21) | 7 | SERBIAN 65 | ****not sourced**** | — | — | **source not obtained** | Sputnik's Serbian service; no Wikidata P856 match |
| `telegrafi.com` | 216 (105) | 39 | ALBANIAN 215, ENGLISH 1 | **Kosovo** | Kosovo | not stated in source | WD |  |
| `gazetaexpress.com` | 161 (30) | 24 | ALBANIAN 159, ENGLISH 2 | **Kosovo** | Pristina | not stated in source | WD |  |
| `koha.net` | 15 (11) | 7 | ALBANIAN 15 | **Kosovo** | Pristina | not stated in source | WD |  |
| `rtsh.al` | 53 (28) | 23 | ALBANIAN 53 | **Albania** | Tirana | not stated in source | WD |  |
| `albeu.com` | 162 (50) | 34 | ALBANIAN 154, ENGLISH 8 | **Albania** | — | — | **source not obtained** | no Wikidata P856 match |
| `agerpres.ro` | 109 (42) | 15 | ROMANIAN 108, HUNGARIAN 1 | **Romania** | Bucharest | not stated in source | WD | state news agency |
| `mediafax.ro` | 149 (44) | 35 | ROMANIAN 146, ENGLISH 3 | **Romania** | Bucharest | Mediafax Group [Romania] | WD |  |
| `digi24.ro` | 134 (55) | 13 | ROMANIAN 134 | **Romania** | Bucharest | not stated in source | WD |  |
| `adevarul.ro` | 112 (19) | 16 | ROMANIAN 112 | **Romania** | Bucharest | Adevărul Holding [Romania] | WD |  |
| `hotnews.ro` | 83 (28) | 13 | ROMANIAN 83 | **Romania** | — | not stated in source | WD |  |
| `moldpres.md` | 29 (8) | 9 | ROMANIAN 29 | **Moldova** | Chișinău | not stated in source | WD | state news agency |
| `zdg.md` | 29 (7) | 7 | ROMANIAN 29 | **Moldova** | Chișinău | not stated in source | WD |  |
| `protv.md` | 23 (8) | 6 | ROMANIAN 23 | **Moldova** | — | not stated in source | WD |  |
| `news.yam.md` | 783 (292) | 66 | ROMANIAN 783 | **Moldova** | — | not stated in source | WD | excluded as an aggregator, §3.12 |
| `ziarulnational.md` | 72 (28) | 5 | ROMANIAN 72 | **Moldova** | — | — | **source not obtained** | no Wikidata P856 match |

#### OTHER LANGUAGES

| Domain | Rec/day (B) | Slots /96 | GDELT `lang` | **Polity of publication** | Place as stated | Owner (and owner's domicile) | Source | Note |
|---|---:|---:|---|---|---|---|---|---|
| `mainichi.jp` | 188 (49) | 25 | Japanese 188 | **Japan** | Tokyo | The Mainichi Newspapers Co. [Japan] | WD |  |
| `sankei.com` | 57 (10) | 24 | Japanese 57 | **Japan** | Tokyo | Sankei Shimbun Co. [Japan] | WD |  |
| `nikkei.com` | 90 (29) | 28 | Japanese 83, ENGLISH 7 | **Japan** | Tokyo | not stated in source | WD |  |
| `asahi.com` | 59 (22) | 18 | Japanese 38, ENGLISH 21 | **Japan** | Tokyo | Asahi Shimbun Company [Japan] | WD | Wikidata lists `P17` as Japan **and** United States (a US edition); place of publication Tokyo |
| `ynet.co.il` | 125 (35) | 31 | HEBREW 125 | **Israel** | — | Yedioth Ahronoth [Israel] | WD |  |
| `haaretz.co.il` | 51 (13) | 29 | HEBREW 51 | **Israel** | — | Salman Schocken family; Leonid Nevzlin; **DuMont Media Group [Germany]** | WD | **publication ≠ ownership** |
| `hani.co.kr` | 174 (77) | 24 | Korean 151, ENGLISH 23 | **South Korea** | Mapo District, Seoul | not stated in source | WD |  |
| `kmib.co.kr` | 126 (22) | 10 | Korean 126 | **South Korea** | Seoul | not stated in source | WD |  |
| `segye.com` | 112 (33) | 8 | Korean 112 | **South Korea** | — | Unification Church | WD | Wikidata lists the owner's country as Japan, Portugal, South Korea and United States — ownership domicile is genuinely multi-national and is recorded as such |
| `koreatimes.com` | 124 (27) | 6 | Korean 124 | **United States** | Los Angeles | not stated in source | WD | Korean-language, published from the US — the second polity in §3.15 |
| `antaranews.com` | 659 (141) | 66 | INDONESIAN 598, ENGLISH 60, MALAY 1 | **Indonesia** | Jakarta | not stated in source | WD | state news agency |
| `tribunnews.com` | 2748 (596) | 55 | INDONESIAN 2743, MALAY 5 | **Indonesia** | — | Kompas Gramedia Group [Indonesia] | WD | its dozens of city subdomains are one publisher |
| `tempo.co` | 110 (34) | 7 | INDONESIAN 65, ENGLISH 45 | **Indonesia** | Jakarta | not stated in source | WD |  |
| `kompas.com` | 979 (243) | 50 | INDONESIAN 977, MALAY 2 | **Indonesia** | — | Kompas Cyber Media | WD | P17 absent; polity **weakly sourced** |
| `utusan.com.my` | 114 (0) | 6 | MALAY 114 | **Malaysia** | — | not stated in source | WD |  |
| `astroawani.com` | 72 (0) | 5 | MALAY 72 | **Malaysia** | — | not stated in source | WD |  |
| `kosmo.com.my` | 71 (52) | 6 | MALAY 71 | **Malaysia** | — | The Utusan Group [Malaysia] | WD |  |
| `beritaharian.sg` | 23 (2) | 6 | MALAY 22, INDONESIAN 1 | **Singapore** | — | not stated in source | WD |  |
| `vnexpress.net` | 263 (160) | 33 | VIETNAMESE 263 | **Vietnam** | Hanoi | Ministry of Science and Technology [Vietnam] | WD |  |
| `vov.vn` | 188 (82) | 12 | VIETNAMESE 188 | **Vietnam** | Hanoi | a Vietnamese government ministry [Vietnam] | WD | Wikidata names the Ministry of Finance, which is likely a data error for a state broadcaster; state ownership is not in doubt, the specific ministry is |
| `tsn.ua` | 242 (46) | 22 | UKRAINIAN 242 | **Ukraine** | — | not stated in source | WD |  |
| `express.pk` | 133 (37) | 39 | URDU 133 | **Pakistan** | — | not stated in source | WD |  |
| `jang.com.pk` | 112 (47) | 14 | URDU 112 | **Pakistan** | Karachi | Jang Media Group [Pakistan] | WD |  |
| `sahilonline.net` | 18 (7) | 3 | URDU 18 | **India** | — | — | **source not obtained** | no Wikidata P856 match; the only Urdu outlet on India's side of §3.17 and it is **unsourced** |
| `elpuntavui.cat` | 98 (22) | 31 | CATALAN 98 | **Spain** | Barcelona / Girona | not stated in source | WD |  |
| `diariandorra.ad` | 44 (0) | 6 | CATALAN 44 | **Andorra** | Andorra la Vella | Premsa Andorrana [Andorra] | WD | the single Andorran newspaper carrying Catalan volume, §3.17 |
| `ara.cat` | 57 (6) | 8 | CATALAN 57 | **Spain** | — | not stated in source | WD | P17 absent; polity **weakly sourced** |

<!-- rows=226 sourced=200 unsourced=26 -->

---

## 6. Declared gaps: what I could not measure, and why

Stated in full, because a stated gap is worth more than a confident guess and this project has been
damaged by numbers without a referent.

**Measurement gaps**

1. **Cluster co-occurrence is still not measured, and it is the number the quorum rule actually needs.**
   This document measures publication volume. The quorum rule fires when two polities are *present on
   the same story*. Nobody has measured how often two specific polities land in the same
   `gsg_docembed` similarity cluster; #2 measured that only ~15–20% of monitored articles pick up any
   similarity edge at all. **Every "quorum met" verdict here is an upper bound.** It says the polities
   publish; it does not say they will co-occur.
2. **Two adjacent weekdays only.** 2026-07-29 and 2026-07-30, late July, northern-hemisphere summer.
   Adjacent days are correlated, so window B bounds day-to-day presence weakly and week-to-week variance
   not at all. Seasonal effects, election periods and major-event days are unmeasured.
3. **No historical depth.** `gsg_docembed` archives to 2020-01-01 and none of it was sampled. "Has this
   outlet been monitored continuously" is unanswered for all 226 rows. This matters most for the small
   polities the quorum depends on — Northern Cyprus, Senegal, Moldova, Andorra — where one outlet
   disappearing removes the polity.
4. **Publisher identity was not resolved systematically.** I found by accident that `dhnet.be` and
   `lalibre.be` share a publisher, that nine `*.maville.com` hosts are one French network, and that
   `tribunnews.com`'s dozens of city subdomains are one Indonesian publisher. **I did not check this for
   every polity in every language.** Wherever a polity's resilience rests on a small number of hosts, the
   "more than one outlet" claim in §3 could be overstated by shared ownership I did not detect. This is
   the largest soft spot in the evidence.
5. **The volume cut of ≥50/day is descriptive, not justified.** It is the 88th percentile of this
   census. It is used to make tables finite, not because 50 is meaningful. Nine Arabic polities and
   several others sit entirely below it and are reported anyway.
6. **Slot presence is a proxy for availability, not a measure of it.** A host in 17 of 96 slots is
   bursty, but I did not measure *when* the bursts fall, so I cannot say whether two polities' bursts
   overlap. For the quorum, overlap is what matters.
7. **Machine-translation quality inside `gsg_docembed` is invisible** and unmeasurable from these files.
   Non-English titles are embedded from GDELT's own translation of unknown quality.
8. **The aggregator/farm classification in §2.1 is mine and is a judgement.** It covers the top 100
   hosts only, is reported with its boundary cases named, and the 68% figure moves to 64.9% under the
   most permissive reasonable reading. **I did not classify the long tail**, which is 81% of the volume,
   so the true unusable share across all of GDELT is unknown — 68% is a measurement of the top, not an
   estimate of the whole.
9. **`dhal3.com` (482/day, 61 of 96 slots) could not be identified at all.** It serves a blank page.
   It is excluded as unusable on that basis, which is a decision made on absence of evidence.

**Sourcing gaps**

10. **26 of 226 rows have no source for polity of publication** and are marked as such. The
    consequential ones: `mignews.com` (161/day, Russian, polity unknown),
    `anlatilaninotesi.com.tr` and `sputnikportal.rs` (Sputnik services, polity unknown),
    `aa.com.tr` (Anadolu Agency — **also unsourced in #17**, so this is now a twice-failed lookup),
    `shorouknews.com` and `gate.ahram.org.eg` (two of the five largest Arabic hosts),
    `philenews.com` and `tio.ch` (second-polity outlets in Greek and Italian), and the three
    Senegalese domains, which means **the French quorum's Senegal option is not sourced**.
11. **Ownership was traced exactly one hop** (§5.1, caution 4). Ultimate beneficial ownership is not
    established for any row. No company registry, no RSF Media Ownership Monitor, no FARA filing was
    consulted — the same gap #17 declared, unchanged.
12. **RSF's country pages were not used as a source in this document.** The 2026 slugs have shifted
    (`rsf.org/en/country/turkiye` returns 404) and, more importantly, RSF measures press freedom, which
    is not the fact this axis needs. Where #17's RSF quotations are relied on the row says so.
13. **Wikidata is a secondary source.** It is citable and verifiable and it separates place of
    publication from ownership by design, which is why it was used. It is not a primary record, it
    contains errors (§5.1), and 26 domains simply have no `P856` statement. A pool decision that turns
    on a single row should re-source that row primarily.
14. **Polity of publication is recorded at state granularity, and for two cases that is inadequate.**
    Bosnia's `rtrs.tv` (Republika Srpska) and `federalna.ba` (the Federation) are one polity in law and
    arguably two in interest (§3.13). Hong Kong is recorded as distinct from the PRC, which is a choice;
    Wikidata itself records `hkcd.com`'s country as the PRC. **Neither is resolved here.**

**Out of scope by instruction, and genuinely not done**

15. **No pool is chosen and no outlet is recommended.** No volume floor, no slot-presence floor and no
    polity set is proposed. §4's "resilient" column is a report of a measured property, not a shortlist.
16. **No press-freedom, editorial-quality or bias assessment appears anywhere in this document.**

---

## 7. Reproducing the measurement

```
http://data.gdeltproject.org/gdeltv3/gsg_docembed/{YYYYMMDDHHMMSS}.gsg.docembed.json.gz
```

- Slots exist at `:00`, `:15`, `:30`, `:45`; publication lag ≈ 21 minutes. Window A = the 96 slots
  `20260729000000` … `20260729234500`. Window B = the 24 hourly slots `20260730000000` …
  `20260730230000`. All 120 requests returned HTTP 200; 1,351 MB gzipped, 6 parallel workers, no
  throttling and no retries needed.
- Each file is newline-delimited JSON, one object per line, keys in fixed order `date`, `url`, `lang`,
  `title`, `model`, `docembed`. **Fields are separated by `", "` — with a space after the colon.** A
  regex written without the space matches nothing and silently yields zero records on a perfectly
  successful download. #17 made and caught that mistake; this run avoided it by not using a regex.
- **Parse the JSON, do not regex it, and do not decode the embeddings.** Truncating each line at the
  first `"title":` and closing the prefix with `}` yields a 3-key object that `json.loads` handles in
  1/18th the time of the full line, never touches title escaping, and skips the 512-float array
  entirely. Validate it: on a 0.5% sample this run compared the fast path against full-JSON parsing of
  the same line and got **2,386/2,386 agreement**, with **0** lines lost out of 466,753.
- **Report parse fidelity as a number.** A silent zero on good data is the same failure class as the
  Frontpage Graph's 200-OK-empty-payload.
- Volume per outlet = count of records whose URL netloc equals the domain or ends with `"." + domain`,
  after stripping a leading `www.`, any userinfo and any port. **Subdomain aggregation is not optional**:
  Xinhua appears only as `english.news.cn` / `news.cn`, Liberty Times only as `news.ltn.com.tw`, Al-Ahram
  only as `gate.ahram.org.eg`, Sputnik Serbia only as `sputnikportal.rs`. A host-exact match reports all
  of these as absent.
- **Keep only aggregates.** `(host, lang) → count`, `host → slots-present`, `lang → slots-present`.
  Discard each slot before fetching the next; peak retained state is a few MB against 1,351 MB streamed.
  Slots-present is worth keeping — it is the only cheap intermittency signal, and it is what shows that
  #17's "Al-Ahram 348 → 0" was bursty publication rather than an outlet going dark.
- **Do not use the DOC 2.0 API.** 5 of 5 attempts returned HTTP 429 (#2, #15).

**Sources for §5, all retrieved 2026-08-02:**

| Source | Endpoint / method | Note |
|---|---|---|
| Wikidata Query Service | `POST https://query.wikidata.org/sparql`, matched on `P856`; properties `P159`, `P291`, `P17`, `P127`, `P749`, `P31`, `P407`; owner domicile via a second hop on the owner entity's `P17`/`P159` | **Rate-limited to 1 request/minute** during a WDQS outage on the day of measurement. Batch ~40 domains per request using `VALUES ?site { <url> … }` on the full `http`/`https` × `www` URL variants — an index-backed match. A `FILTER(STRSTARTS(…))` formulation over all `P856` values times out |
| Outlet imprint / contact / legal-notice pages | `GET https://<domain>/{impressum,imprint,mentions-legales,about,contact,contacto,contatti,iletisim,…}` with a browser user-agent | Hit rate roughly 1 in 3. German-language sites are the most reliable (an *Impressum* is legally required); JS-only sites and Cloudflare-fronted sites yield nothing |
| Freedom House, *Freedom in the World 2025* | `https://freedomhouse.org/country/<country>/freedom-world/2025` | Reachable; **not used as a source in this document** — it measures freedom, not polity |
| RSF *World Press Freedom Index 2026* country pages | `https://rsf.org/en/country/<slug>` | Reachable with a browser user-agent, but **2026 slugs have shifted** (`turkiye` → 404). Not used here; where #17's RSF quotes are relied on, the row says so |

**Not obtained:** company registries; RSF Media Ownership Monitor; US FARA filings; ultimate beneficial
ownership for any row; and a `P856` statement in Wikidata for the 26 domains listed as
`source not obtained` in §5.
