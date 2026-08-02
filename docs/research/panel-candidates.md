# Panel candidates: is there an adversarial pair per language?

Evidence for [#17](https://github.com/exdsgift/tensionr/issues/17), applying the selection procedure
fixed by Decision 3 on [#5](https://github.com/exdsgift/tensionr/issues/5).

**This document does not choose the panel.** It measures three things per candidate outlet — GDELT
monitoring volume, position on the state-aligned / independent axis with a cited source, and language
of publication — and then reports, per language, whether a pair can be formed at all. Where no pair
exists that is stated as a finding, not worked around. No outlet is recommended for adoption.

Measured against `origin/master` = `ff9a706`. The existing feed list is
`src/tensionr/config.py`: `RSS_FEEDS` (line 31), `RSS_METADATA` (line 58). No project file was
modified.

---

## 1. Method

### 1.1 GDELT volume — measured, not assumed

Source: `http://data.gdeltproject.org/gdeltv3/gsg_docembed/YYYYMMDDHHMMSS.gsg.docembed.json.gz`,
15-minute buckets. Each record is one article with `date`, `url`, `lang`, `title`, `model`
(`USEv4`) and a 512-float `docembed`. Volume per outlet = number of records whose `url` host matches
the outlet's domain (or a subdomain of it).

The **DOC 2.0 API was not used**, per the ticket and per [#2](https://github.com/exdsgift/tensionr/issues/2)
/ [#15](https://github.com/exdsgift/tensionr/issues/15): 5 of 5 attempts returned HTTP 429 and GDELT
itself asks high-volume users off its search tier.

| | Window 1 | Window 2 |
|---|---|---|
| Span (UTC) | 2026-08-01 14:15 → 2026-08-02 14:00 | 2026-07-26 00:00 → 23:00 |
| Sampling | **every** 15-minute slot | 1 slot per hour |
| Slots requested / retrieved | 96 / **96** (0 errors) | 24 / **24** (0 errors) |
| Records parsed | **215,936** | 54,039 |
| Gzipped volume downloaded | 624 MB | 155 MB |
| Records per slot | min 1,456 · median 2,268 · max 3,064 | — |

Window 1 is a **complete 24-hour census**: every slot in the window was retrieved, so its counts are
exact records-per-day for that day. Window 2 samples one slot in four; its counts are multiplied by 4
and reported as an **estimate**, present only as an independent check that a window-1 number is not a
one-day artefact. Where the two disagree sharply, that disagreement is the finding (see §2.2).

Parse fidelity: 215,936 records extracted from 216,032 lines = **99.96%**. The 96 unparsed lines
(0.04%) are lines whose title contained the field-delimiter sequence; they are lost from the counts
and are not attributable to any outlet.

**Volume distribution, window 1** — context for reading any single number. 10,554 distinct hosts:

| percentile | records/day | | |
|---|---|---|---|
| p50 | 6 | hosts ≥ 20/day | 2,605 |
| p75 | 19 | hosts ≥ 50/day | 900 |
| p90 | 45 | hosts ≥ 100/day | 314 |
| p95 | 72 | share of all records from hosts ≥ 100/day | 35.9% |
| p99 | 181 | | |

So 100 records/day is roughly the 97th percentile of monitored hosts. **No volume floor is proposed
here** — that is a panel decision. The distribution is given so that a floor can be chosen against
real numbers.

### 1.2 Position on the axis — cited, never asserted

Every label below carries a source and its retrieval date. Sources used, all retrieved
**2026-08-02**:

- **RSF World Press Freedom Index 2026**, country pages, `https://rsf.org/en/country/<country>`.
  The 2026 edition is live; 2025 scores are also shown on the same pages. Cited as *RSF 2026*.
- **Freedom House, Freedom in the World 2025** country reports,
  `https://freedomhouse.org/country/<country>/freedom-world/2025`. Cited as *FH 2025*.
- **Council Regulation (EU) 2022/350 of 1 March 2022**, Annex, "List of legal persons, entities or
  bodies referred to in Article 2f":
  `RT- Russia Today English`, `RT- Russia Today UK`, `RT - Russia Today Germany`,
  `RT - Russia Today France`, `RT- Russia Today Spanish`, `Sputnik`. The recitals state the
  propaganda "has been channelled through a number of media outlets under the permanent direct or
  indirect control of the leadership of the Russian Federation."
  `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0350`.
- **Outlet self-disclosure**, where obtained:
  - Al Jazeera, *About Us*: "Al Jazeera is an independent news organisation funded in part by the
    Qatari government." `https://www.aljazeera.com/about-us/`
  - SANA, *About*: "The official national news agency of Syria, established on June 24, 1965. It is
    affiliated with the Ministry of Information and headquartered in Damascus."
    `https://sana.sy/en/?page_id=2`

Where a source could not be obtained the cell says **"source not obtained"**. Such a row is not
usable as evidence for a label — it is a lead, and it is marked as one rather than filled with a
plausible guess.

Where sources disagree the disagreement is recorded in the row, not resolved.

### 1.3 Language of publication, kept distinct from country of ownership

Two independent signals, both used:

1. GDELT's own `lang` field on each record — this is *language of the article*, assigned per article,
   so an outlet publishing in several languages shows several values.
2. Inspection of the `title` field of sampled records per candidate domain, to confirm the script and
   language match the `lang` label.

Country of ownership is reported separately, in the source column, and is never used to infer
language. This is the defect [#15](https://github.com/exdsgift/tensionr/issues/15) found in
`RSS_METADATA` (4 of 23 `lang` values wrong: Spiegel→English, Japan Times→Japanese, RT→Russian,
MercoPress→Spanish). §5 re-measures every current config domain against GDELT and does not inherit
those labels.

One GDELT-specific subtlety that matters for one language: GDELT emits **`Chinese` and `ChineseT` as
two distinct values** (simplified and traditional). See §4.2.

### 1.4 What I could not measure, and why

Declared gaps, per the ticket's instruction that a declared gap beats a plausible guess:

- **Cluster membership was not measured.** I measured how many articles each outlet publishes into
  `gsg_docembed`, which is a necessary condition for appearing in a cluster, not a sufficient one.
  [#2](https://github.com/exdsgift/tensionr/issues/2) measured that only ~15–20% of monitored
  articles pick up any similarity edge, and clustering needs ≥2 distinct sources on the same story.
  Nobody has measured **how often two specific candidate outlets land in the same cluster** — that is
  the number a panel decision actually wants, and it does not exist yet. Every volume figure here
  should be read as an upper bound on cluster participation.
- **Two days only.** Window 1 is one day (a Saturday–Sunday boundary), window 2 one day a week
  earlier (a Sunday). Weekday/weekend and seasonal effects are unmeasured. Given §2.2, this is the
  weakest part of the evidence.
- **No historical depth.** `gsg_docembed` archives back to 2020-01-01 but I did not sample it, so
  "has this outlet been monitored continuously for a year" is unanswered for every row.
- **Translation quality is invisible.** Non-English articles are embedded from GDELT's own machine
  translation. Whether a state outlet's framing survives that translation intact is unmeasured and
  unmeasurable from these files.
- **Ownership registries were not consulted directly.** RSF and Freedom House country reports plus
  outlet self-disclosure were used. National company registries, RSF's Media Ownership Monitor and
  US FARA filings were not retrieved (`rsf.org` blocks the fetch tool but not `curl`; FARA's portal is
  a JS application that `curl` cannot query). Several rows are consequently "source not obtained".
- **RSF country scores are country-level, not outlet-level.** They are quoted as context for a media
  system, never as a label for an individual outlet. Only sentences that name an outlet are used as
  outlet evidence.

---

## 2. Findings that apply to every language

These three shape every table below and are more consequential than any individual pair.

### 2.1 GDELT does not monitor the outlets this project assumed it did

The `gsg_docembed` stream is heavily skewed towards regional, local and aggregator sites, and away
from exactly the large national outlets a panel would reach for first. Measured, window 1 census,
records/day:

| Outlet | Records/day | Outlet | Records/day |
|---|---:|---|---:|
| Reuters (`reuters.com`) | **0** | Le Monde (`lemonde.fr`) | **0** |
| AP (`apnews.com`) | **0** | Libération | **0** |
| Washington Post | **0** | Mediapart | **0** |
| WSJ (`wsj.com`) | **0** | France 24 | **0** |
| NYT | 5 | `francetvinfo.fr` | **0** |
| FT / Economist / Telegraph / Times (UK) | **0** each | Cumhuriyet | **0** |
| Daily Mail (`dailymail.co.uk`) | **0** | Meduza | **0** |
| USA Today / Politico / The Hill | **0** each | Novaya Gazeta Europe | **0** |
| Times of Israel | **0** | The Insider (`theins.ru`) | **0** |
| Haaretz (English) | 3 | Caixin | **0** |
| CGTN | **0** | Ming Pao | **0** |
| TASS (`.com` and `.ru`) | **0** | The Initium | **0** |
| TRT World | **0** | Página/12 | **0** |
| Press TV (`presstv.ir`) | **0** | Granma | **0** |

Meanwhile the top English-language hosts by volume are `quicknews-africa.net` (2,557/day),
`whatweekly.com` (2,417), `digbycourier.ca` (1,815), `northernpen.ca` (1,769) and
`sublimemagazine.com` (1,323) — aggregators and small local titles, not news of record.

**Consequence for panel selection:** the constraint created by Decision 1 on #5 ("a panel outlet that
GDELT does not monitor contributes nothing") is not a formality. It eliminates most of the obvious
candidates before any editorial judgement is made, and it is the reason several languages below fail.

### 2.2 Per-outlet presence is intermittent at day granularity

Some outlets present in one window are **wholly absent** in the other. This is not sampling noise —
window 2 covers 24 hours at hourly resolution, so an outlet emitting 348 records/day should appear in
roughly 87 of those sampled records, not zero:

| Outlet | Window 1 (census) | Window 2 (est.) |
|---|---:|---:|
| Al-Ahram (`gate.ahram.org.eg`) | 348 | **0** |
| Al-Quds Al-Arabi (`alquds.co.uk`) | 90 | **0** |
| `taz.de` | 31 | **0** |
| RT Arabic (`arabic.rt.com`) | 14 | **0** |
| Xinhua Arabic / Russian | 21 / 12 | **0** / **0** |
| BirGün (`birgun.net`) | 262 | 68 |
| ETtoday | 177 | 48 |
| Der Standard | 52 | 12 |

And in the other direction: `merkur.de` 473 → 848, Ciudad CCS 123 → 320, `asahi.com` 28 → 100.

**Consequence:** a single-day volume measurement is not a reliable liveness signal for a specific
outlet. Any panel needs continuous per-outlet health monitoring, which is precisely the operating rule
Decision 3 already adopted ("a silent source is data, not an error"). It also means every number in
this document carries day-to-day variance that two windows cannot bound.

### 2.3 The axis has no domestic pole in a free-press system

The state-aligned / independent axis is a real axis in Russia, China, Iran, Egypt, Syria, Turkey,
Venezuela and Cuba, where third parties document state ownership or control of named outlets. It is
**not** a within-country axis in Germany, France, Spain or the UK: what exists there is state
*ownership* of public broadcasters whose independence is legally protected and whom RSF does not
classify as state-controlled.

- RSF 2026, Germany: "The broadcast sector includes both privately owned and public broadcasters, the
  latter (ARD, ZDF and Deutschlandfunk) providing regional, national and international reporting. […]
  The independence of public media is protected by law."
- RSF 2026, France: "The public television channels and radio stations of France Télévisions and
  Radio France compete with private broadcasters" — described as competition inside a pluralist
  market, not as a state pole.
- RSF 2026, Spain: "The privately owned media groups Atresmedia and Mediaset and the public
  broadcaster RTVE have a monopoly on the market" — a concentration finding, not a control finding.

So in those languages the state-aligned pole can only be occupied by a **foreign** state's
language service (Xinhua's French/Spanish/German desks, RT's language editions, Sputnik). Those are
the outlets GDELT carries at 12–58 records/day, or not at all, and several of them are banned in the
EU by the regulation cited in §1.2. This is a structural result, not bad luck, and it decides German
and French below.

---

## 3. Languages present in the corpus today

### 3.1 English — a pair can be formed

English is the only language where both poles have volume comfortably above the p99 of monitored
hosts. Total English records in window 1: 89,088/day across 5,705 hosts.

**State-aligned side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Xinhua English | `english.news.cn` | 119 | 132 | ENGLISH | State-owned | RSF 2026 China (13.85, 178/180): "Major Chinese media groups, such as Xinhua News Agency, China Central Television (CCTV) […] and newspapers China Daily, People's Daily and the Global Times, are state-owned and directly controlled by the authorities." |
| Arab News | `arabnews.com` | 99 | 116 | ENGLISH | Saudi, state-aligned media system | RSF 2026 Saudi Arabia (19.11, 176/180): "Even privately owned Saudi media follow government guidelines set out by the Saudi Press Agency (SPA)." No ownership registry consulted for this title specifically — **outlet-level source not obtained** |
| Asharq Al-Awsat English | `english.aawsat.com` | 58 | 12 | ENGLISH | Same as above | As above; **outlet-level source not obtained** |
| Daily Sabah | `dailysabah.com` | 56 | 16 | ENGLISH | Turkey, pro-government press | RSF 2026 Türkiye (27.94, 163/180): "With 90% of national media outlets under government control…" — does not name Sabah. **Outlet-level source not obtained** |
| Anadolu Agency (English desk) | `aa.com.tr` | 41 of 123 | — | ENGLISH (41) + TURKISH (82) | Turkish state news agency | See §4.4; **direct self-disclosure not obtained** (corporate page fetched but text not extractable) |
| Press TV | `presstv.co.uk` | 36 | 80 | ENGLISH | Iranian state broadcaster (IRIB) | RSF 2026 Iran (17.45, 177/180): "the country's media is largely controlled by the Islamic regime". **Outlet-level ownership source not obtained**; note `presstv.ir` itself is at **0** |
| China Daily | `chinadaily.com.cn` (3 subdomains) | 46 | 52 | ENGLISH | State-owned | RSF 2026 China, quoted above (names China Daily explicitly) |
| Sputnik | `sputnikglobe.com` | 13 | 12 | ENGLISH | Under Russian state control | Council Regulation (EU) 2022/350, Annex, entry `Sputnik` |
| Global Times | `globaltimes.cn` | 10 | 4 | ENGLISH | State-owned | RSF 2026 China, quoted above (names Global Times explicitly) |

**Independent side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| The Hindu | `thehindu.com` | 473 | — | ENGLISH | Privately owned; India's media system rated hostile | RSF 2026 India (31.96, 157/180) describes concentration and government pressure but **does not name The Hindu**. **Outlet-level source not obtained** |
| Los Angeles Times | `latimes.com` | 205 (199 EN) | — | ENGLISH + SPANISH (6) | Privately owned | **Source not obtained** |
| Sydney Morning Herald | `smh.com.au` | 181 | — | ENGLISH | Privately owned (Nine) | **Source not obtained** |
| The Guardian | `theguardian.com` | 154 | 164 | ENGLISH | Trust-owned, editorially independent | RSF 2026 UK (79.45, 18/180) — country-level only. Scott Trust page returned an empty body; **outlet-level source not obtained** |
| BBC | `bbc.co.uk` | 142 | 180 | ENGLISH | Public broadcaster; independence contested by some sources, affirmed by RSF's UK ranking | RSF 2026 UK, country-level. Note: RSF 2026 Russia lists the BBC among "western media […] no longer accessible" in Russia |
| The Independent | `independent.co.uk` | 122 | — | ENGLISH | Privately owned | **Source not obtained** |
| CBC | `cbc.ca` | 121 | — | ENGLISH | Canadian public broadcaster | **Source not obtained** |
| Fox News | `foxnews.com` | 94 | — | ENGLISH | Privately owned | **Source not obtained** |
| SCMP | `scmp.com` | 72 | 124 | ENGLISH | Alibaba-owned; Hong Kong | Self-disclosure (`scmp.com/about-us`) states only "South China Morning Post Publishers Limited […] most trusted news media organisation in Hong Kong" — **does not disclose ownership**. RSF 2026 Hong Kong (39.49, 140/180) does not name SCMP |
| Straits Times | `straitstimes.com` | 50 | — | ENGLISH | SPH Media; Singapore | **Source not obtained** |

**Verdict: a pair can be formed in English.** Both poles clear 100 records/day, and the state side is
plural (Chinese, Saudi, Turkish, Iranian and Russian state outlets are all present), which means the
pair does not depend on any single fragile domain. The weakness is not volume, it is sourcing: the
independent-side labels are the *least* well sourced in this document, because RSF and Freedom House
name state outlets by name and describe independent media as a class. Anyone choosing the English
pair should expect to do outlet-level ownership work that this ticket did not complete.

### 3.2 Arabic — a pair can be formed, but the independent pole is contested

Total Arabic records, window 1: 5,462/day across 148 hosts. Note how few hosts: Arabic in GDELT is
concentrated, and dominated by Egyptian titles.

**State-aligned / state-funded side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Al-Ahram | `gate.ahram.org.eg` | 348 | **0** | ARABIC | State-owned | RSF 2026 Egypt (24.92, 169/180): "Al-Akhbar, Al-Ahram and Al-Gomhuriya are the three most popular state-owned national newspapers." |
| Akhbar El-Yom | `akhbarelyom.com` | 104 | 128 | ARABIC | State-owned (Al-Akhbar house) | RSF 2026 Egypt, as above |
| Al Jazeera | `aljazeera.net` | 103 | 148 | ARABIC | **Sources disagree.** Self-disclosure: "an independent news organisation funded in part by the Qatari government". RSF 2026 Qatar (59.79, 75/180): "The state-funded Al Jazeera TV news broadcaster has considerable resources and a pool of presenters who are paid well enough to ignore subjects that could embarrass their employer" and "Qatari media coverage has been directly aligned with the Qatari government's official stance" | Al Jazeera *About Us*; RSF 2026 Qatar |
| Nile TV / `nile.eg` | `nile.eg` | 78 | 16 | ARABIC | State broadcaster | **Source not obtained** |
| SANA | `sana.sy` | 58 of 176 | — | ARABIC (58), TURKISH (33), ENGLISH (31), FRENCH (29), SPANISH (25) | State agency | Self-disclosure: "The official national news agency of Syria […] affiliated with the Ministry of Information." Note RSF 2026 Syria jumped from 15.82 (177/180, 2025) to 39.44 (141/180, 2026) after the regime's fall — the label may be historically stale |
| Al-Riyadh | `alriyadh.com` | 45 | — | ARABIC | Saudi conservative daily | RSF 2026 Saudi Arabia: "the Al-Watan and Okaz dailies represent the 'liberal' side while Al-Riyadh leads the conservative side" — names it, but as a political camp, not as state-owned |
| Al-Manar | `almanar.com.lb` | 40 | 32 | ARABIC | Hezbollah-affiliated broadcaster | **Source not obtained** (RSF 2026 Lebanon does not name it) |
| Xinhua Arabic | `arabic.news.cn` | 21 | **0** | ARABIC | State-owned | RSF 2026 China |
| Asharq Al-Awsat | `aawsat.com` | 15 | 48 | ARABIC | Saudi (SRMG) | RSF 2026 Saudi Arabia, system-level only; **outlet-level source not obtained** |
| RT Arabic | `arabic.rt.com` | 14 | **0** | ARABIC | Russian state control | Council Regulation (EU) 2022/350 names the English, UK, German, French and Spanish RT entities — **not the Arabic one**. The label is an inference; treat as **source not obtained for this edition** |

**Nominally independent side — and why it is contested**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Al-Dostor | `dostor.org` | 850 | 496 | ARABIC | Egyptian private | See caveat below |
| Veto Gate | `vetogate.com` | 460 | 388 | ARABIC | Egyptian private | See caveat below |
| Al-Shorouk | `shorouknews.com` | 447 | 392 | ARABIC | Egyptian private | See caveat below |
| Al-Masry Al-Youm | `almasryalyoum.com` | 235 | 268 | ARABIC | Egyptian private | See caveat below |
| Al-Bayan | `albayan.ae` | 83 | 124 | ARABIC | UAE | RSF 2026 UAE (30.86, 158/180); **outlet-level source not obtained** |
| Al-Quds Al-Arabi | `alquds.co.uk` | 90 | **0** | ARABIC | London-based pan-Arab, privately owned | **Source not obtained**; and absent from window 2 entirely |

**The caveat that decides this language.** The four highest-volume Arabic outlets in GDELT are all
Egyptian private titles, and both reference sources say Egyptian private ownership does not imply
independence:

- FH 2025 Egypt: "The Egyptian media sector is dominated by progovernment outlets; most critical or
  opposition-oriented outlets have been shut down since 2013. **Private media outlets are generally
  owned by businesspeople linked to the military and intelligence services.**"
- RSF 2026 Egypt: "Pluralism is almost non-existent in Egypt. […] Independent media outlets are
  censored and targeted by prosecutors."

Genuinely independent Arabic outlets are **absent from GDELT entirely**: Mada Masr, Daraj, Raseef22,
Al-Araby Al-Jadeed, Al-Akhbar (Lebanon), Al-Modon, Al-Arab — all **0 records/day** in window 1.
Al-Arabiya (`alarabiya.net`) and Sky News Arabia are also at **0**, so the Saudi/UAE state-aligned
broadcasters are missing too.

**Verdict: a pair can be formed in Arabic, but only in a weak sense.** Al-Ahram or Akhbar El-Yom
(state-owned, sourced) against Al-Quds Al-Arabi (independent but unsourced, and absent from one of
two windows) is the only pairing where the two sides are genuinely on opposite poles — and it depends
on the two most intermittent domains in the whole Arabic set. Pairing Al-Ahram against the
high-volume Egyptian private titles would put both sides of the axis inside the same
intelligence-linked ownership network, per FH 2025. **This is the finding, and it is not resolved by
picking a different Egyptian outlet.**

### 3.3 German — **no pair exists**

Total German records, window 1: 9,633/day across 312 hosts. Volume is not the problem. The
state-aligned pole is empty.

**Searched for, and found at exactly zero records/day in the 24-hour census:**

| Candidate | Records/day |
|---|---:|
| RT DE (`de.rt.com`) | **0** (also EU-listed, Council Regulation (EU) 2022/350: `RT - Russia Today Germany`) |
| Sputnik Deutschland (`de.sputniknews.com`) | **0** (EU-listed, entry `Sputnik`) |
| Xinhua German (`german.xinhuanet.com`) | **0** |
| CRI German (`german.cri.cn`, `cri.cn`) | **0** |
| TRT Deutsch (`trtdeutsch.com`) | **0** |
| Anadolu German desk | **0** German-language records (`aa.com.tr` emits only TURKISH and ENGLISH) |
| junge Welt (`junge-welt.de`) | **0** |
| Anti-Spiegel | **0** |

A direct scan of all 312 German-language hosts for any state broadcaster or state news agency
(Xinhua, RT, Sputnik, CRI, TRT, Anadolu, CGTN, IRIB, Press TV, RIA, TASS, any `.cn` host) returned
**zero matches**.

**What is available, all on the independent side of the axis:**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Merkur | `merkur.de` | 473 | 848 | GERMAN | Private (Ippen) | **Source not obtained** |
| HNA | `hna.de` | 321 | — | GERMAN | Private (Ippen) | **Source not obtained** |
| Kreiszeitung | `kreiszeitung.de` | 288 | — | GERMAN | Private | **Source not obtained** |
| Die Zeit | `zeit.de` | 218 | 256 | GERMAN | Private | **Source not obtained** |
| Die Welt | `welt.de` | 216 | 320 | GERMAN | Private (Axel Springer) | **Source not obtained** (Springer IR page returned 404) |
| n-tv | `n-tv.de` | 184 | — | GERMAN | Private (RTL) | **Source not obtained** |
| t-online | `t-online.de` | 130 | — | GERMAN | Private | **Source not obtained** |
| Focus | `focus.de` | 127 | — | GERMAN | Private | **Source not obtained** |
| ORF (Austria) | `orf.at` | 98 | 8 | GERMAN | Austrian public broadcaster | **Source not obtained** |
| Süddeutsche Zeitung | `sueddeutsche.de` | 71 | 72 | GERMAN | Private | **Source not obtained** |
| Der Spiegel | `spiegel.de` | 35 | 16 | **GERMAN** | Private | Language confirmed: 35 of 35 records labelled GERMAN, German-language titles. **`RSS_METADATA` says English — wrong** |
| Deutschlandfunk | `deutschlandfunk.de` | 34 | — | GERMAN | Public radio | RSF 2026 Germany (82.17, 14/180): "public broadcasters, the latter (ARD, ZDF and Deutschlandfunk) […] The independence of public media is protected by law" |
| taz | `taz.de` | 31 | **0** | GERMAN | Cooperative-owned | **Source not obtained** |
| WDR / MDR / SWR / BR / rbb | various | 10–27 each | — | GERMAN | Public broadcasters | RSF 2026 Germany, as above |
| ARD *Tagesschau* | `tagesschau.de` | 24 | 12 | GERMAN | Public broadcaster | RSF 2026 Germany, as above |
| Deutsche Welle, German output | `dw.com` | **5** | — | GERMAN (5 of 157) | Federally funded external broadcaster | See below |
| FAZ | `faz.net` | 13 | 12 | GERMAN | Private | **Source not obtained** |
| ZDF (`zdf.de`), NZZ (`nzz.ch`) | — | **0** | **0** | — | — | Not monitored |

**Deutsche Welle is not a German-language option.** `dw.com` emits 157 records/day but only **5** of
them are German. Its GDELT output is ENGLISH (24), SPANISH (20), UKRAINIAN (18), RUSSIAN (13),
SWAHILI (12), POLISH (11), PORTUGUESE (10), TURKISH (9) and more — DW is a *multilingual* source in
GDELT and its German desk is effectively invisible there. Worth noting independently of the panel:
`RSS_METADATA` lists `www.dw.com` as `{country: Germany, lang: English}`, and English happens to be
its single largest GDELT language, but the feed itself is dead (HTTP 404, #15).

**Verdict: no pair exists in German.** Both candidate poles resolve to the independent side. Making a
German pair would require either (a) classifying ARD / ZDF / Deutschlandfunk as state-aligned, which
directly contradicts the only source available on the question (RSF 2026: "The independence of public
media is protected by law"), or (b) using an outlet with zero GDELT presence. Neither is permissible
under Decision 3's rule that classifications are cited, never asserted.

### 3.4 Spanish — a pair can be formed, with a low-volume state pole

Total Spanish records, window 1: 22,961/day across 803 hosts — the second-largest language in GDELT
after English, and far larger than its 3.2% share of the current RSS corpus.

**State-aligned side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Ciudad CCS | `ciudadccs.info` | 123 | 320 | SPANISH | Caracas outlet, reported as government-aligned | **Source not obtained.** Highest-volume state-aligned Spanish candidate and the least documented — this row is not usable as evidence for a label |
| RT en Español | `actualidad.rt.com` | 58 | 12 | SPANISH (57) | Under Russian state control | Council Regulation (EU) 2022/350, Annex: `RT- Russia Today Spanish` |
| HispanTV | `hispantv.com` | 35 | 28 | SPANISH | Iranian state broadcaster's Spanish channel | **Source not obtained** (site redirects); RSF 2026 Iran describes state control of the media system generally |
| TeleSUR | `telesurtv.net` | 32 | 36 | SPANISH | Multi-state Latin American broadcaster | **Source not obtained** — RSF 2026 Venezuela does not name it |
| Prensa Latina | `prensa-latina.cu` | 29 | 28 | SPANISH | Cuban state agency | RSF 2026 Cuba (29.22, 160/180), quoting the Cuban constitution: "the main social communication media, regardless of their format or platform, belong to the people under a regime of socialist ownership […] Any other form of ownership is prohibited", and "Granma is the most widely distributed newspaper, and like all media, it is under state control" |
| RTVE | `rtve.es` | 28 | 44 | SPANISH | Spanish public broadcaster — but see §2.3 | RSF 2026 Spain (75.42, 29/180): "the public broadcaster RTVE" named in a *concentration* finding, not a control finding |
| EFE | `efe.com` | 23 | 28 | SPANISH | Spanish state-majority-owned agency | **Source not obtained** (EFE's own corporate page yielded no usable text) |
| Xinhua Spanish | `spanish.xinhuanet.com` | 17 | 24 | SPANISH | State-owned | RSF 2026 China |
| Cubadebate | `cubadebate.cu` | 9 | 20 | SPANISH | Cuban, therefore state under the constitutional prohibition above | RSF 2026 Cuba, as above |
| Granma (`granma.cu`), Sputnik Mundo (`sputniknews.lat`), VTV (`vtv.gob.ve`) | — | **0** | — | — | — | Not monitored |

**Independent side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| La Razón | `larazon.es` | 319 | 304 | SPANISH | Private, Spain | RSF 2026 Spain, country-level: "There is more diversity in the print media sector." **Outlet-level source not obtained** |
| ABC | `abc.es` | 248 (+1 GALICIAN) | 116 | SPANISH | Private, Spain | As above |
| Europa Press | `europapress.es` | 206 | — | SPANISH | Private agency, Spain | As above |
| 20minutos | `20minutos.es` | 159 | — | SPANISH | Private, Spain | As above |
| La Vanguardia | `lavanguardia.com` | 152 | — | SPANISH | Private, Spain | As above |
| El Universal | `eluniversal.com.mx` | 142 | — | SPANISH | Private, Mexico | RSF 2026 Mexico (45.23, 122/180) describes extreme concentration; **outlet-level source not obtained** |
| La Nación | `lanacion.com.ar` | 135 | — | SPANISH | Private, Argentina | RSF 2026 Argentina (52.44, 98/180) names "the media groups La Nación, América, Indalo, Werthein, Fígoli, Octubre and Telefe […] as well as the news site Infobae" as the private-sector players |
| Infobae | `infobae.com` | 128 | — | SPANISH | Private, Argentina | RSF 2026 Argentina, as above (names Infobae) |
| La Jornada | `jornada.com.mx` | 120 | 76 | SPANISH | Private, Mexico | **Source not obtained** |
| Clarín | `clarin.com` | 107 | — | SPANISH | Private, Argentina | RSF 2026 Argentina: "The Clarín group, the media industry's main player, wields a great deal of influence over the media landscape" |
| El Mundo | `elmundo.es` | 96 | — | SPANISH | Private, Spain | RSF 2026 Spain, country-level |
| eldiario.es | `eldiario.es` | 96 (+4 CATALAN) | 88 | SPANISH | Private, Spain | As above |
| El País | `elpais.com` | 77 | 144 | SPANISH | Private, Spain | As above. Currently the corpus's only Spanish source |
| Público | `publico.es` | 40 | — | SPANISH | Private, Spain | As above |
| MercoPress | `mercopress.com` | **0** | **0** | — | — | Not monitored. Also publishes in **English**, not Spanish — `RSS_METADATA` is wrong (#15) |

**Verdict: a pair can be formed in Spanish.** The best-sourced pairing is Prensa Latina or Cubadebate
(state, sourced to the Cuban constitution via RSF 2026) or RT en Español (state, sourced to EU
Regulation 2022/350) against any of a dozen private outlets at 77–319 records/day. The asymmetry is
the honest problem: the sourced state pole sits at 9–58 records/day (p75–p95 of monitored hosts) while
the independent pole sits roughly an order of magnitude higher, so the two sides will not appear in
clusters at comparable rates. The one high-volume state-aligned candidate, Ciudad CCS at 123–320/day,
has **no source at all** and cannot be used as evidence for a label.

### 3.5 French — the pair is marginal, and there is no domestic state pole

Total French records, window 1: 5,440/day across 355 hosts. French is the clearest illustration of
§2.1: **every French national outlet of record is absent from GDELT.**

| Outlet | W1/day | W2 est/day |
|---|---:|---:|
| Le Monde (`lemonde.fr`) | **0** | **0** |
| Libération | **0** | — |
| Mediapart | **0** | — |
| La Croix | **0** | — |
| France 24 | **0** | — |
| `francetvinfo.fr` | **0** | — |
| Marianne | **0** | — |
| Le Soir (BE) | **0** | — |
| L'Orient-Le Jour | **0** | — |
| Le Figaro | 9–11 | **0** |
| RT France | **0** | — (also EU-listed: `RT - Russia Today France`) |
| Sputnik Afrique | **0** | — |

**State-aligned side — what actually exists**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| SANA, French desk | `sana.sy` | 29 of 176 | — | FRENCH (29) | Syrian state agency | Self-disclosure: "official national news agency of Syria […] affiliated with the Ministry of Information" |
| Xinhua French | `french.xinhuanet.com` | 21 | 32 | FRENCH | State-owned | RSF 2026 China |
| RFI | `rfi.fr` | 13 | 12 | FRENCH | France Médias Monde, state-owned but legally independent — see §2.3 | RSF 2026 France (76.68, 25/180) treats public broadcasters as market participants, not as a state pole |

**Independent side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| La Dépêche du Midi | `ladepeche.fr` | 160 | 120 | FRENCH | Regional private | RSF 2026 France, country-level: "The media landscape offers a wide range of choices across all segments, both nationally and locally." **Outlet-level source not obtained** |
| L'Est Républicain | `estrepublicain.fr` | 119 | — | FRENCH | Regional private (EBRA) | As above |
| Le Dauphiné Libéré | `ledauphine.com` | 112 | — | FRENCH | Regional private (EBRA) | As above |
| BFM TV | `bfmtv.com` | 78–85 | 84 | FRENCH | Private broadcaster | RSF 2026 France names "private broadcasters, such as TF1, M6, RTL and BFM TV" |
| Le Parisien | `leparisien.fr` | 68 | 84 | FRENCH | Private | **Source not obtained** |
| franceinfo | `franceinfo.fr` | 66 | 76 | FRENCH | Public (Radio France / France Télévisions) | RSF 2026 France, as above |
| 20 Minutes | `20minutes.fr` | 66 | — | FRENCH | Private | **Source not obtained** |
| La Libre Belgique | `lalibre.be` | 53 | 60 | FRENCH | Private, Belgium | **Source not obtained** |
| La Presse (Québec) | `lapresse.ca` | 34 | — | FRENCH | Canada | **Source not obtained** |
| Le Temps | `letemps.ch` | 32 | 32 | FRENCH | Private, Switzerland | **Source not obtained** |
| RTBF | `rtbf.be` | 13 | — | FRENCH | Belgian public broadcaster | **Source not obtained** |

**Verdict: technically a pair, in practice marginal.** A pair with sourced labels on both sides exists
— SANA's French desk or Xinhua French (state, sourced) against BFM TV or a regional daily
(independent, sourced at country level only) — but the state pole sits at **21–29 records/day**, the
p75–p85 band of monitored hosts, and both of those outlets publish translated wire copy rather than
editorial framing, which is the thing the index is meant to detect. There is **no French outlet that
any consulted source classifies as aligned to the French state**: France Médias Monde is state-owned
and legally independent, and RFI is at 13 records/day regardless. Le Monde, the corpus's current
French source, is **not monitored by GDELT at all** in either window.

---

## 4. Languages absent from the corpus today

### 4.1 Turkish — a pair can be formed, and it is the best-sourced pair in this document

Total Turkish records, window 1: **7,094/day** across the language — more than Arabic (5,462) and
more than French (5,440). Turkish is absent from the current corpus entirely.

**State-aligned side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Sabah | `sabah.com.tr` | 166 | 240 | TURKISH | Owned by Kalyon Group via Zirve Holding; pro-government | RSF / BIA **Media Ownership Monitor Turkey**, Sabah outlet page: "In 2008, ATV and Sabah were acquired by Çalık Group, close to the AKP […] The Competition Board approved the sale of ATV-Sabah to Zirve Holding, owned by Kalyon Group, in 2013. **The daily is known for its support for President Erdoğan and the ruling AKP.**" (MOM's underlying survey data predates 2026 — cite the retrieval date and the project's own vintage) |
| Yeni Şafak | `yenisafak.com` | 136 | — | TURKISH | Pro-government daily | **Source not obtained** |
| Anadolu Agency | `aa.com.tr` | 123 (82 TR + 41 EN) | 116 | TURKISH + ENGLISH | Turkish state news agency | **Source not obtained.** MOM's Anadolu page 404s; Anadolu's own corporate page yielded no extractable text. Do not use this row as evidence |
| Milliyet | `milliyet.com.tr` | 132 | — | TURKISH | Demirören Group | **Source not obtained** |
| Akşam | `aksam.com.tr` | 95 | — | TURKISH | — | **Source not obtained** |
| Hürriyet | `hurriyet.com.tr` | 99 | — | TURKISH | Demirören Group | **Source not obtained** |
| TRT Haber | `trthaber.com` | 55 | 36 | TURKISH | State broadcaster | MOM Turkey, TRT Haber outlet page: "It is a sub-channel of **state channel, TRT**." |
| Daily Sabah | `dailysabah.com` | 56 | 16 | **ENGLISH** | Sabah's English edition | See Sabah row; language is English, not Turkish |

**Independent / opposition side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| BirGün | `birgun.net` | 262 | 68 | TURKISH | Left-wing opposition daily | **Source not obtained** (MOM page returned 503; RSF 2026 does not name it) |
| Sözcü | `sozcu.com.tr` | 137 | 200 | TURKISH | Independent and critical of power | RSF 2026 Türkiye (27.94, 163/180): "With 90% of national media outlets under government control, the public has turned towards media outlets of varying political stances that are **independent and critical of power** […] These outlets include Now TV, Halk TV, Tele1 and **Sözcü**" |
| Evrensel | `evrensel.net` | 116 | 88 | TURKISH | Left-wing opposition daily | **Source not obtained** |
| Habertürk | `haberturk.com` | 157 | — | TURKISH | Mainstream commercial | **Source not obtained** |
| Dünya | `dunya.com` | 73 | — | TURKISH | Business daily | **Source not obtained** |
| CNN Türk | `cnnturk.com` | 72 | — | TURKISH | Demirören Group | **Source not obtained** |
| NTV | `ntv.com.tr` | 63 | — | TURKISH | Doğuş Group | **Source not obtained** |
| DW Turkish / BBC Turkish / VOA Turkish | `dw.com`, `bbc.com` | 9 / 4 / **0** | — | TURKISH | Named by RSF as independent alternatives | RSF 2026 Türkiye, quoted above (names BBC Turkish, VOA Turkish, Deutsche Welle Turkish) — but their GDELT volume is negligible |
| Cumhuriyet, Halk TV, Tele1, Now TV, Gazete Duvar, Diken | — | **0** each | — | — | Named by RSF as independent | **Not monitored by GDELT at all**, including three of the four outlets RSF names |

**Verdict: a pair can be formed in Turkish, and it is the strongest case in this document.**
Sabah (166–240/day, ownership and political alignment documented by RSF's own Media Ownership
Monitor) or TRT Haber (55/day, documented as a state channel by the same source) against Sözcü
(137–200/day, named by RSF 2026 as independent and critical of power). Both sides clear 100 records/day
in at least one window, both sides carry an outlet-level source, and the poles are genuinely opposed
in a media system RSF scores at 27.94/100.

Two caveats: three of the four outlets RSF names as independent (Now TV, Halk TV, Tele1) and
Cumhuriyet are **not in GDELT at all**, so the independent side rests on Sözcü alone; and BirGün, the
highest-volume opposition candidate, has no source and swung 262 → 68 between windows.

### 4.2 Chinese — the expectation is **refuted, but only across a language boundary GDELT itself draws**

The ticket expects Chinese to fail because China Daily is state-owned and SCMP is Alibaba-owned. Both
of those facts hold. But the reasoning is incomplete, because **Chinese-language independent press
exists in Taiwan and GDELT carries it at high volume.**

The complication: GDELT emits **two distinct language values**. Window 1: `Chinese` (simplified)
7,656 records/day across 308 hosts; `ChineseT` (traditional) 3,724/day across 88 hosts. PRC state
media publish in `Chinese`; Taiwanese outlets publish in `ChineseT`. Whether these count as one
language for the panel is a decision, not a measurement — and it is the decision on which the Chinese
verdict turns.

**State-aligned side (all `Chinese`, simplified)**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Xinhua | `news.cn` (all desks) | 208 (56 `Chinese`, 119 ENGLISH, 21 ARABIC, 12 RUSSIAN) | 140 | multiple | State-owned, directly controlled | RSF 2026 China (13.85, 178/180): "Major Chinese media groups, such as Xinhua News Agency, China Central Television (CCTV), China National Radio (CNR), and newspapers China Daily, People's Daily and the Global Times, are **state-owned and directly controlled by the authorities**. The Propaganda Department of the Chinese Communist Party sends a detailed notice to all media every day that includes editorial guidelines and censored topics." |
| Xinhua, language desks | `xinhuanet.com` | 104 (57 `Chinese`, 21 FRENCH, 17 SPANISH, 9 Korean) | — | multiple | As above | As above |
| People's Daily | `people.com.cn` | 97 | 24 | `Chinese` | State-owned | RSF 2026 China, names People's Daily |
| China.com.cn | `news.china.com.cn` | 90 | — | `Chinese` | State-run portal | **Source not obtained** |
| China Daily | `chinadaily.com.cn` | 46 | 52 | **ENGLISH** | State-owned | RSF 2026 China, names China Daily. Note: publishes in **English** — `RSS_METADATA` labels it English correctly, but the feed is frozen since 2017-12-12 (#15) |
| Global Times | `globaltimes.cn` | 10 | 4 | ENGLISH | State-owned | RSF 2026 China, names Global Times |
| CCTV (`cctv.com`), CGTN (`cgtn.com`) | — | **0** | — | — | State-owned | Not monitored |
| Wen Wei Po | `wenweipo.com` | 46 | — | `ChineseT` | Pro-Beijing Hong Kong daily | **Source not obtained** |
| Lianhe Zaobao | `zaobao.com.sg` | 70 | — | `Chinese` | SPH Media, Singapore | **Source not obtained** |

Large `Chinese`-language hosts that are **commercial PRC portals, not editorial voices**: `163.com`
(NetEase) 915/day, `baijiahao.baidu.com` 792, `finance.sina.com.cn` 356, `itbear.com.cn` 286,
`ifeng.com` 184. These operate under the same Propaganda Department regime RSF describes, but they are
aggregators; **no source was obtained for any of them** and none is a candidate for a panel voice.

**Independent side (all `ChineseT`, traditional — Taiwan)**

RSF 2026 Taiwan: 75.44 / 100, **28 of 180** — three places above Spain, fourteen above France.
"The media landscape, although free, suffers from strong political polarisation, undeclared
advertising, sensationalism, and the pursuit of profit."

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| UDN (United Daily News) | `udn.com` | 1,092 total / 319 on the main host | 368 | `ChineseT` (781), `Chinese` (192), Japanese (104) | Private, Taiwan | **Source not obtained.** Note 722 of the 1,092 are `blog.udn.com` — **user blogs, not journalism**; the editorial host is `udn.com` at 319/day |
| Liberty Times | `news.ltn.com.tw` | 403 (566 across all `ltn.com.tw`) | 456 | `ChineseT` (380) + ENGLISH (23) | Private, Taiwan | **Source not obtained** |
| Yam News | `n.yam.com` | 438 | 364 | `ChineseT` | Private portal, Taiwan | **Source not obtained** |
| SET News | `setn.com` | 291 | 192 | `ChineseT` | Private broadcaster | RSF 2026 Taiwan names "Sanlih E-Television News (SET News)" among the most-watched channels |
| CNA (Taiwan) | `cna.com.tw` | 245 | 148 | `ChineseT` | **State-established with a statutory independence mandate — sources describe both** | Self-disclosure (Focus Taiwan / CNA, `focustaiwan.tw/aboutus`): "The Central News Agency (CNA) is the **national news agency of the Republic of China (ROC)** […] CNA was restructured into a nonprofit corporation and became the country's national news agency through a law passed by the Legislative Yuan in 1996. Under the law, **it is required to independently fulfill three missions**" |
| China Times | `chinatimes.com` | 222 | 216 | `ChineseT` | Private (Want Want group); widely reported as pro-Beijing | **Source not obtained** — and this label matters, so the row is unusable as evidence |
| ETtoday | `ettoday.net` | 177 | 48 | `ChineseT` | Private | RSF 2026 Taiwan names "Etoday Online" among widely used online outlets |
| Newtalk | `newtalk.tw` | 90 | 64 | `ChineseT` | Private | **Source not obtained** |
| Storm Media | `storm.mg` | 81 | 64 | `ChineseT` | Private | **Source not obtained** |
| TVBS | `news.tvbs.com.tw` | 37 (50 all hosts) | — | `ChineseT` | Private broadcaster | RSF 2026 Taiwan names "TVBS News" |
| CTS | `news.cts.com.tw` | 79 | — | `ChineseT` | Public broadcaster, Taiwan | RSF 2026 Taiwan: "Public Television Service, an independent public broadcaster, scores as one most trusted TV channel in Taiwan" |
| SCMP | `scmp.com` | 72 | 124 | **ENGLISH** | Alibaba-owned, Hong Kong | Self-disclosure does **not** state ownership; RSF 2026 Hong Kong (39.49, 140/180) does not name it. Publishes in English, so it is not a Chinese-language candidate at all |
| Ming Pao, HK01, HKET, InMedia, Initium, RTHK Chinese, RFA Mandarin, Caixin, The Paper, Jiemian | — | **0** each | — | — | — | **Not monitored.** Every Hong Kong independent or semi-independent outlet, and every PRC commercially-driven outlet with a reputation for investigation, is absent |

**Verdict: a pair can be formed *if* simplified and traditional Chinese count as one language.**
Xinhua or People's Daily (state-owned, sourced to RSF 2026 by name, 56–97 `Chinese` records/day)
against SET News or ETtoday (private, named by RSF 2026 Taiwan, 177–291 `ChineseT` records/day). Both
poles have volume and both have sources.

**If they count as two languages, both fail:**
- Simplified `Chinese`: no independent outlet with a sourced label. The only high-volume non-state
  hosts are commercial portals operating under the Propaganda Department's daily editorial notice, and
  Lianhe Zaobao (Singapore, 70/day, unsourced).
- Traditional `ChineseT`: no state-aligned outlet with a sourced label. Wen Wei Po (46/day) is the
  only pro-Beijing candidate and it has no source; CNA is state-established *with* a statutory
  independence mandate, which puts it on both poles at once.

So the ticket's expectation is **refuted in substance but not in effect**: China Daily is indeed
state-owned and SCMP is indeed not a usable independent counterweight (it is Alibaba-owned, publishes
in English, and its own about page declines to disclose ownership). The pair that does exist is a
cross-strait pair, and it works only under a decision about what counts as "Chinese" that this
document deliberately does not make.

### 4.3 Russian — **no pair exists**

Total Russian records, window 1: 6,496/day across 316 hosts. The state pole is the strongest of any
language in this document. The independent pole is empty.

**State-aligned side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Vesti (VGTRK) | `vesti.ru` | 256 | 164 | RUSSIAN | State broadcaster | FH 2025 Russia: "The government controls, directly or through state-owned companies and friendly business magnates, **all national television networks** and most radio and print outlets" |
| RIA Novosti | `ria.ru` | 215 | 192 | RUSSIAN | State agency | RSF 2026 Russia (23.15, 172/180): "The remaining media are **owned by the state or by Kremlin allies**. Their employees must follow orders issued by the president's office regarding subjects…" |
| Izvestia | `iz.ru` | 142 | 116 | RUSSIAN | Kremlin-aligned | RSF 2026 Russia, as above |
| Vzglyad | `vz.ru` | 128 | — | RUSSIAN | Kremlin-aligned | RSF 2026 Russia, as above |
| Rossiyskaya Gazeta | `rg.ru` | 119 | — | RUSSIAN | Government newspaper of record | RSF 2026 Russia, as above |
| RT Russian | `russian.rt.com` | 106 | 72 | RUSSIAN | Under Russian state control | Council Regulation (EU) 2022/350 lists the RT entities; the Russian-language edition is not itself named — the recitals' "permanent direct or indirect control of the leadership of the Russian Federation" covers RT as a whole |
| Pravda.ru | `pravda.ru` | 104 | — | RUSSIAN | — | **Source not obtained** |
| Channel One | `1tv.ru` | 41 | — | RUSSIAN | State broadcaster | FH 2025 Russia, as above |
| TASS (`tass.ru`, `tass.com`) | — | **0** | **0** | — | State agency | Not monitored |

**Independent side — measured, and empty**

| Outlet | W1/day | W2 est/day |
|---|---:|---:|
| Meduza (`meduza.io`) | **0** | **0** |
| Novaya Gazeta Europe (`novayagazeta.eu`) | **0** | — |
| The Insider (`theins.ru`) | **0** | — |
| Holod (`holod.media`) | **0** | — |
| IStories (`istories.media`) | **0** | — |
| Agentstvo (`agentstvo.media`) | **0** | — |
| TV Rain / Current Time (`currenttime.tv`) | **0** | — |
| The Moscow Times (English) | 4 | — |
| RFE/RL Russian (`svoboda.org`) | 17 | — |
| Kommersant (`kommersant.ru`) | 79 | — |
| Fontanka (`fontanka.ru`) | 59 | — |

RSF 2026 Russia explains why: "The media regulator, Roskomnadzor, has censored most independent news
sites, and the most popular ones, such as **Meduza and TV Rain, have been declared 'undesirable
organisations'**, which means that mentioning them or quoting them can lead to criminal proceedings."
Kommersant and Fontanka are privately owned but fall under the same source's "owned by the state or by
Kremlin allies", so they cannot be used as the independent pole without contradicting the citation.

**Verdict: no pair exists in Russian.** Not because the axis does not apply — it applies more sharply
here than anywhere — but because GDELT does not monitor a single Russian-language outlet that any
consulted source classifies as independent. Every exile outlet is at exactly zero records/day, in both
windows.

### 4.4 Portuguese — the pair is marginal, same shape as French

Total Portuguese records, window 1: 4,909/day across 239 hosts.

**State-aligned side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Agência Brasil (EBC) | `agenciabrasil.ebc.com.br` | 26 | 36 | PORTUGUESE | Brazilian state media | RSF 2026 Brazil (66.37, 52/180): "**State-owned media face relative budgetary fragility and are subject to attempts at editorial interference by the government.**" |
| RTP | `rtp.pt` | 35 | — | PORTUGUESE | Portuguese public broadcaster | RSF 2026 Portugal (83.71, 10/180) names RTP among the five dominant groups — a concentration finding, not a control finding; see §2.3 |
| EBC other channels | `tvbrasil.ebc.com.br`, `radionacional.ebc.com.br` | 6 + 2 | — | PORTUGUESE | As Agência Brasil | RSF 2026 Brazil, as above |
| Xinhua Portuguese, RT Brasil, Sputnik Brasil | — | **0** each | — | — | — | Not monitored |
| Jornal de Angola, ANGOP, Notícias (Mozambique) | — | **0** each | — | — | State-owned African Lusophone press | Not monitored. `jornalnoticias.co.mz` returns 5/day |

**Independent side**

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Globo group | `globo.com` (g1, O Globo, Extra, CBN) | 576 | 756 | PORTUGUESE | Private conglomerate | RSF 2026 Brazil: "Ten major corporate conglomerates, belonging to as many families, share the market. **The five biggest are Globo, Record, SBT, Bandeirantes and Folha.**" |
| SAPO | `sapo.pt` | 402 | — | PORTUGUESE | Portal, Portugal | **Source not obtained** |
| Folha de S.Paulo | `www1.folha.uol.com.br` | 117 | 56 | PORTUGUESE | Private | RSF 2026 Brazil, names Folha |
| Observador | `observador.pt` | 93 | 104 | PORTUGUESE | Private, Portugal | **Source not obtained** |
| Brasil 247 | `brasil247.com` | 78 | 108 | PORTUGUESE | Private, left-wing | **Source not obtained** |
| Estadão | `estadao.com.br` | 61 | — | PORTUGUESE | Private | **Source not obtained** |
| Gazeta do Povo | `gazetadopovo.com.br` | 51 | — | PORTUGUESE | Private, right-wing | **Source not obtained** |
| Público (`publico.pt`), Expresso | — | **0** | — | — | — | Not monitored |

**Verdict: technically a pair, in practice marginal — and structurally identical to French.** The only
sourced state-aligned pole is Brazilian state media at **26–36 records/day**, and RSF's language for it
("subject to *attempts* at editorial interference") is much weaker than the language it uses for
Russia or China. There is no foreign-state Portuguese-language service in GDELT at all. Whether a
26/day pole is usable is a volume decision; the *label* on it is defensible but weak.

### 4.5 Japanese — **no pair exists**

Total Japanese records, window 1: 1,130/day across 76 hosts. Small, and with no state pole whatsoever.

| Outlet | Domain | W1/day | W2 est/day | GDELT `lang` | Position | Source (retrieved 2026-08-02) |
|---|---|---:|---:|---|---|---|
| Mainichi | `mainichi.jp` | 139 | 36 | Japanese | Private conglomerate | RSF 2026 Japan (62.90, 62/180): "Mainstream newspapers and broadcasters are owned by the country's five major media conglomerates: **Yomiuri, Asahi, Nihon-Keizai, Mainichi and Fuji-Sankei.**" |
| Sankei | `sankei.com` | 32 | 104 | Japanese | Private (Fuji-Sankei) | RSF 2026 Japan, as above |
| Asahi | `asahi.com` | 28 (+3 ENGLISH) | 100 | Japanese | Private | RSF 2026 Japan, as above |
| Jiji Press | `jiji.com` | 19 | — | Japanese | Private agency | **Source not obtained** |
| Nikkei | `nikkei.com` | 20 (14 JA + 6 EN) | — | Japanese + ENGLISH | Private | RSF 2026 Japan names Nihon-Keizai |
| Tokyo Shimbun | `tokyo-np.co.jp` | 9 | — | Japanese | Private | **Source not obtained** |
| Yomiuri | `yomiuri.co.jp` | **1** | — | Japanese | Private | RSF 2026 Japan names Yomiuri as the largest — GDELT carries one record/day |
| **NHK** (`nhk.or.jp`, `www3.nhk.or.jp`) | — | **0** | **0** | — | Public broadcaster | RSF 2026 Japan: "Nippon Hōsō Kyōkai (NHK) is one of the world's largest public broadcasters" — **not monitored by GDELT** |
| Sputnik Japan, CRI Japanese, Xinhua Japanese, CGTN Japanese, Kyodo | — | **0** each | — | — | — | Not monitored |
| Japan Times | `japantimes.co.jp` | **0** | **0** | — | Private | Not monitored. Publishes in **English** — `RSS_METADATA` says Japanese, which is wrong (#15) |

The rest of the Japanese volume is regional dailies (`agara.co.jp` 70, `toonippo.co.jp` 54,
`373news.com` 47, `ibarakinews.jp` 44, `iwate-np.co.jp` 43…) plus `blog.udn.com` (104 Japanese-labelled
records from a Taiwanese blog host — an artefact, not a Japanese outlet).

**Verdict: no pair exists in Japanese.** No outlet on the state-aligned pole exists at any volume: NHK
is at zero, and there is no foreign-state Japanese-language service in GDELT. RSF 2026 Japan describes
a landscape of five private conglomerates plus a public broadcaster, and identifies the *kisha club*
system rather than state ownership as the press-freedom problem — i.e. Japan's real media axis is
access and self-censorship, which is not the axis Decision 3 chose.

### 4.6 Hindi — **fails on the first criterion, decisively**

**GDELT emitted 1 (one) Hindi-language record in the entire 24-hour census** — `prabhasakshi.com`, a
single article out of 215,936. Window 2 is consistent (Hindi does not appear in its top languages).

For scale, GDELT's 24-hour Indic-language output in window 1 was: MALAYALAM 457, TELUGU 391, URDU 337,
PUNJABI 172, TAMIL 165, GUJARATI 118, KANNADA 30, SINHALESE 64, **HINDI 1**, BIHARI 1. India *is*
heavily represented in GDELT — `timesofindia.indiatimes.com` 854/day, `thehindu.com` 473,
`hindustantimes.com` 289, `economictimes.indiatimes.com` 317, `aninews.in` 261 — but **in English**.

No pair can be assessed, because there is no Hindi-language corpus to assess it in. Every Hindi
candidate — Dainik Jagran, Dainik Bhaskar, Amar Ujala, Navbharat Times, DD News, The Wire Hindi,
Satyahindi, Aaj Tak — returned **0 records/day**. Whether this is a GDELT translation-pipeline gap or a
crawl gap is **unmeasured**; either way the effect on the panel is the same.

### 4.7 Persian — **fails on volume, and the state pole is absent**

**123 Persian-language records/day across 11 hosts** in the census — 0.06% of GDELT's output, below
Armenian and Malayalam.

| Host | W1/day | Note |
|---|---:|---|
| `ipna.ir` | 26 | **Source not obtained** |
| `news.gooya.com` | 23 | Diaspora aggregator; **source not obtained** |
| `sputnik.af` | 20 | Sputnik Afghanistan — EU-listed entity `Sputnik` |
| `khaama.com` | 15 (+25 ENGLISH) | Afghan outlet |
| `spnfa.ir` | 13 | Sputnik Persian; EU-listed entity `Sputnik` |
| `bbc.com` (Persian) | 7 | |
| `kar-online.com` | 7 | |
| `radiofarda.com` | 5 | RFE/RL Persian — US-government-funded |
| `iranpressnews.com` | 4 | |
| `afghanpaper.com` | 2 | |
| `dw.com` (Persian) | 1 | |

**Every Iranian state outlet is at zero**: IRNA, Fars, Tasnim, Mehr, Press TV Persian (`presstv.ir`),
Tehran Times. Press TV reaches GDELT only through `presstv.co.uk`, and only **in English** (36/day).
Iran International is also at zero.

RSF 2026 Iran (17.45, 177/180) states the reason a domestic pole cannot be built: "As the country's
media is largely controlled by the Islamic regime, the main sources of news and information come from
media outlets based abroad." Even so, **no pair exists**: the state side is unmonitored, and the
"independent" side consists of foreign-state-funded broadcasters (Radio Farda, BBC Persian, DW) at
1–7 records/day — which would put a foreign state on the *independent* pole, an incoherence the axis
cannot absorb.

### 4.8 Other languages, not assessed on the axis

Reported because the volume is surprising and bears on which languages are worth assessing next. These
were **not** assessed for an adversarial pair — no outlet-level sourcing was done — so nothing here is
a finding about pairs.

| Language | Records/day (W1) | vs. corpus languages |
|---|---:|---|
| ITALIAN | 9,834 | larger than German (9,633), **1.8× Arabic**, 1.8× French |
| GREEK | 5,686 | larger than Arabic (5,462) and French (5,440) |
| INDONESIAN | 4,408 | comparable to Portuguese |
| VIETNAMESE | 4,367 | comparable to Portuguese |
| UKRAINIAN | 2,590 | half of Arabic. Relevant to the Russian finding: `24tv.ua`, `unian.net`, `obozrevatel.com`, `unn.ua` publish in both Ukrainian and Russian |
| ALBANIAN | 2,298 | |
| ROMANIAN / SERBIAN | 2,263 / 2,030 | |
| Korean | 1,811 | larger than Japanese (1,130) |
| HEBREW | 594 | small; `jpost.com` (132/day) publishes in **English** |

The pattern to note: **GDELT's language mix does not match the world's news production**, it matches
which national webs GDELT successfully crawls. Italian and Greek outrank Arabic; Hindi is absent
while Malayalam and Telugu are present. Any claim that the index "covers" a language should be
measured against this file, not assumed from population.

---

## 5. The current 23 feeds, measured against GDELT

Every domain in `RSS_FEEDS` / `RSS_METADATA` (`src/tensionr/config.py`, `origin/master` = `ff9a706`),
against the window-1 census. "GDELT `lang`" is what GDELT actually observed; the config's `lang` value
is shown beside it. Feed liveness is from [#15](https://github.com/exdsgift/tensionr/issues/15),
probed 2026-08-02 14:05–14:35 UTC.

| Feed host | GDELT domain | GDELT records/day | GDELT `lang` (observed) | Config `lang` | Verdict |
|---|---|---:|---|---|---|
| `timesofindia.indiatimes.com` | same | **854** | ENGLISH | English | ok |
| `www.thehindu.com` | `thehindu.com` | **473** | ENGLISH | English | ok |
| `www.dw.com` | `dw.com` | 157 | 8+ languages, GERMAN only **5** | English | feed dead (404); label technically matches its largest GDELT language by accident |
| `www.theguardian.com` | same | 154 | ENGLISH | English | ok |
| `feeds.bbci.co.uk` | `bbc.co.uk` | 142 | ENGLISH | English | ok |
| `www.jpost.com` | `jpost.com` | 132 | ENGLISH | English | ok (feed emits future timestamps, #15) |
| `www.cbc.ca` | `cbc.ca` | 121 | ENGLISH | English | feed dead (404) |
| `www.aljazeera.net` | same | 103 | ARABIC | Arabic | ok |
| `www.abc.net.au` | same | 78 | ENGLISH | English | feed dead (404) |
| `feeds.elpais.com` | `elpais.com` | 77 | SPANISH | Spanish | ok |
| `www.scmp.com` | `scmp.com` | 72 | ENGLISH | English | ok |
| `www.straitstimes.com` | same | 50 | ENGLISH | English | ok |
| `www.chinadaily.com.cn` | same | 46 | ENGLISH | English | feed frozen since 2017-12-12 |
| `www.spiegel.de` | same | 35 | **GERMAN** | **English** | **label wrong** (#15 confirmed) |
| `www.rt.com` | `rt.com` + subdomains | 178 (0 on the bare host) | **RUSSIAN 106, SPANISH 57, ARABIC 14, ENGLISH 1** | **Russian** | **label wrong** — the `www.rt.com/rss/news/` feed is English; GDELT sees RT mostly as Russian and Spanish via subdomains the config does not name |
| `rss.nytimes.com` | `nytimes.com` | 5 | ENGLISH | English | effectively unmonitored |
| `feeds.a.dj.com` | `wsj.com` | **0** | — | English | feed frozen since 2025-01-27; unmonitored |
| `www.lemonde.fr` | `lemonde.fr` | **0** | — | French | **unmonitored** — the corpus's only French source |
| `www.france24.com` | `france24.com` | **0** | — | English | **unmonitored** |
| `www.japantimes.co.jp` | `japantimes.co.jp` | **0** | — | **Japanese** | **unmonitored** and **label wrong** (publishes in English) |
| `en.mercopress.com` | `mercopress.com` | **0** | — | **Spanish** | **unmonitored** and **label wrong** (publishes in English) |
| `feeds.reuters.com` | `reuters.com` | **0** | — | English (country `"Global"`) | feed dead (DNS); **unmonitored** |
| `www.washingtonpost.com` | `washingtonpost.com` | **0** | — | English | feed dead; **unmonitored** |

**7 of 23 domains are at zero GDELT records/day**, independently of whether their RSS feed works
(WSJ, Le Monde, France 24, Japan Times, MercoPress, Reuters, Washington Post). NYT at 5 is effectively
a zero. China Daily (46) and Der Spiegel (35) sit below the p90 of monitored hosts.

Intersecting with #15's liveness result (8 of 23 feeds inert), the domains that are **both** on a live
feed **and** monitored at ≥50 GDELT records/day number **10 of 23**: Times of India 854, The Hindu 473,
RT 178 (via subdomains only), The Guardian 154, BBC 142, Jerusalem Post 132, Al Jazeera 103, El País 77,
SCMP 72, Straits Times 50. Three of the ten are non-English by GDELT's own labelling — Al Jazeera
(Arabic), El País (Spanish), and RT (Russian and Spanish, via subdomains the config never names, while
the configured feed URL is RT's English one). DW, CBC and ABC Australia clear the volume bar but their
feeds are dead; Der Spiegel's feed is alive but it sits at 35/day.

The four wrong `lang` labels from #15 are confirmed independently here, by GDELT's own per-article
language detection rather than by RSS `<language>` tags: Spiegel is German, Japan Times and MercoPress
are English, and RT is *not* a Russian-language feed at the URL the config uses.

---

## 6. Summary: which languages can be covered

"Pair" means: at least one outlet on each pole, **each carrying an outlet-level source**, both
monitored by GDELT. Volumes are window-1 census records/day for the best-sourced candidate on each
side. No volume floor is asserted — see §1.1 for the distribution against which one can be chosen.

| Language | GDELT vol/day | Pair? | State-aligned pole (sourced) | Independent pole (sourced) | Binding constraint |
|---|---:|---|---|---|---|
| **Turkish** | 7,094 | **Yes — strongest** | Sabah 166 (MOM Turkey); TRT Haber 55 (MOM Turkey) | Sözcü 137 (RSF 2026 names it) | 3 of 4 RSF-named independents, and Cumhuriyet, are at 0 in GDELT |
| **English** | 89,088 | **Yes** | Xinhua English 119, China Daily 46, Global Times 10 (RSF 2026 names all three) | Guardian 154, BBC 142 (country-level source only) | Independent-side labels are the weakest-sourced in this document |
| **Spanish** | 22,961 | **Yes** | Prensa Latina 29 / Cubadebate 9 (RSF 2026 + Cuban constitution); RT en Español 58 (EU Reg. 2022/350) | El País 77 … La Razón 319 (country-level source only) | State pole is 5–10× smaller than the independent pole |
| **Chinese** | 7,656 `Chinese` + 3,724 `ChineseT` | **Conditional** | Xinhua 56 `Chinese`, People's Daily 97 (RSF 2026 names both) | SET News 291, ETtoday 177 — both `ChineseT` (RSF 2026 Taiwan names both) | Only works if simplified and traditional count as **one** language. Within either alone: no pair |
| **Arabic** | 5,462 | **Weak yes** | Al-Ahram 348 (RSF 2026 names it as state-owned) | Al-Quds Al-Arabi 90 (**no source**) | Both sides are the two most intermittent Arabic domains (348→0 and 90→0 between windows); all genuinely independent Arabic outlets are at 0 |
| **French** | 5,440 | **Marginal** | Xinhua French 21; SANA French 29 (self-disclosure) | BFM TV 78 (RSF 2026 names it) | No domestic state pole exists; both foreign-state candidates publish translated wire copy at ~p80 volume. Le Monde is at **0** |
| **Portuguese** | 4,909 | **Marginal** | Agência Brasil 26 (RSF 2026: state media "subject to attempts at editorial interference") | Globo 576, Folha 117 (RSF 2026 names both) | State pole at 26/day; no foreign-state Portuguese service in GDELT at all |
| **German** | 9,633 | **No** | **none** — zero German-language records from any state broadcaster or state agency | Zeit 218, Welt 216, Tagesschau 24 | RSF 2026: "The independence of public media is protected by law", so ARD/ZDF cannot be labelled state-aligned |
| **Russian** | 6,496 | **No** | RIA 215, Vesti 256, Izvestia 142, RT ru 106 (RSF 2026 + FH 2025) | **none** — Meduza, Novaya Gazeta Europe, The Insider, Holod, IStories, TV Rain all at **0** | The state pole is the strongest of any language; the independent pole is unmonitored |
| **Japanese** | 1,130 | **No** | **none** — NHK at 0, no foreign-state Japanese service | Mainichi 139, Asahi 28, Sankei 32 (RSF 2026 names all) | No state pole at any volume; RSF identifies *kisha club* access, not state ownership, as Japan's axis |
| **Persian** | **123** | **No** | **none** — IRNA, Fars, Tasnim, Mehr, Press TV Persian all at **0** | Radio Farda 5, BBC Persian 7 — both foreign-state-funded | Fails on volume (0.06% of GDELT) and the "independent" side would put a foreign state on the independent pole |
| **Hindi** | **1** | **No** | not assessable | not assessable | **One Hindi record in a 215,936-record census.** India is in GDELT in English, not Hindi |

### Count

- **Pair can be formed, with outlet-level sources on both poles: 3** — Turkish, English, Spanish.
- **Pair conditional on a definitional decision: 1** — Chinese (simplified vs traditional).
- **Pair exists but is weak or marginal on volume, intermittency, or source quality: 3** — Arabic,
  French, Portuguese.
- **No pair exists: 5** — German, Russian, Japanese, Persian, Hindi.

### Where the corpus stands against this

Of the five languages in the corpus today (English 68.6%, Arabic 14.6%, French 9.0%, German 4.6%,
Spanish 3.2%, per #15), **two — German and French — are the two hardest cases in this document**, and
German is one of the five where no pair exists at all. The two languages with the cleanest pairs,
**Turkish and Chinese, are absent from the corpus**, while Turkish alone has more GDELT volume than
Arabic and French combined.

### The three things a panel decision still needs, which this ticket did not produce

1. **Co-occurrence, not volume.** Nobody has measured how often two candidate outlets land in the
   *same* story cluster. Volume is necessary and not sufficient (§1.4).
2. **A volume floor, chosen against the distribution in §1.1** — and a stated position on what happens
   when a pole only clears it on some days (§2.2).
3. **Outlet-level ownership sourcing for the independent poles.** RSF and Freedom House name state
   outlets by name and describe independent media as a class, so most independent-side rows in this
   document say "source not obtained". That is the single largest gap in the evidence, and it affects
   English and Spanish — the two languages that otherwise look easiest.

---

## 7. Reproducing the measurement

```
http://data.gdeltproject.org/gdeltv3/gsg_docembed/{YYYYMMDDHHMMSS}.gsg.docembed.json.gz
```

- Slots exist at `:00`, `:15`, `:30`, `:45`; publication lag ≈ 21 minutes. A not-yet-published slot
  returns **HTTP 416** to a ranged request, not 404.
- Each file is newline-delimited JSON, one object per line, keys in fixed order:
  `date`, `url`, `lang`, `title`, `model`, `docembed`. **Fields are separated by `", "` with a space
  after the colon** — a regex written without the space matches nothing and silently yields zero
  records. That mistake was made and caught during this measurement; it is the exact failure mode #2
  warns about (a successful download that parses to nothing).
- Window 1 = the 96 consecutive slots ending `20260802140000`. Window 2 = the 24 hourly slots
  `20260726000000` … `20260726230000`.
- Volume per outlet = count of records whose `url` netloc equals the domain or ends with `"." + domain`,
  after stripping a leading `www.` and any `:443` suffix. Subdomain aggregation matters a great deal:
  RT appears only as `russian.rt.com` / `actualidad.rt.com` / `arabic.rt.com` (the bare `rt.com` is at
  zero), Xinhua only as `english.news.cn` / `french.xinhuanet.com` / etc., Al-Ahram only as
  `gate.ahram.org.eg`, Liberty Times only as `news.ltn.com.tw`. A host-exact match would report all of
  these as absent.
- Cost: 624 MB gzipped for window 1, 155 MB for window 2, both retrieved with 5 parallel workers and
  no throttling or errors (120/120 requests succeeded).

Sources, all retrieved **2026-08-02**:

| Source | URL |
|---|---|
| RSF World Press Freedom Index 2026, country pages | `https://rsf.org/en/country/<country>` (blocks generic fetch agents; responds to `curl` with a browser user-agent) |
| Freedom House, Freedom in the World 2025 | `https://freedomhouse.org/country/<country>/freedom-world/2025` |
| Council Regulation (EU) 2022/350 of 1 March 2022 | `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R0350` |
| RSF / BIA Media Ownership Monitor Turkey | `https://turkey.mom-gmr.org/en/media/detail/outlet/<outlet>/` (several outlet slugs 404 or 503) |
| Al Jazeera, *About Us* | `https://www.aljazeera.com/about-us/` |
| SANA, *About* | `https://sana.sy/en/?page_id=2` |
| CNA Taiwan / Focus Taiwan, *About* | `https://focustaiwan.tw/aboutus` |
| SCMP, *About us* | `https://www.scmp.com/about-us` (does not disclose ownership) |

Sources attempted and **not** obtained: RSF Media Ownership Monitor pages for Anadolu Agency,
Cumhuriyet and BirGün (404 / 503); the Scott Trust (empty body); Axel Springer shareholder structure
(404); Deutsche Welle and France Médias Monde corporate pages (404); EFE, TeleSUR, HispanTV, EBC and
Ciudad CCS corporate pages (404 / redirect / timeout); Press TV (TLS failure); US FARA registry (a JS
application `curl` cannot query). Every row depending on one of these is marked
**"source not obtained"** rather than filled in.
