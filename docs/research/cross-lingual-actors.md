# Matching actors across languages: what GDELT already resolves, and what it does not

Research for [#22](https://github.com/exdsgift/tensionr/issues/22), under the map in
[#1](https://github.com/exdsgift/tensionr/issues/1). Written 2026-08-02.

**Question.** How do we recognise that `طهران`, `Tehran`, `Teherán` and `Тегеран` are one actor,
cheaply enough to run in a free GitHub Action? [#8](https://github.com/exdsgift/tensionr/issues/8)
established that framing divergence lives in the surface text and validated actor presence
**English-only on purpose**; the product measures divergence between polities publishing in
different languages, so the untested step is the one the product depends on.

Every number below was measured on live GDELT data for the window
**2026-08-02 13:30–15:15 UTC**, on story clusters produced by the method of
[`prototype/event-clustering`](https://github.com/exdsgift/tensionr/tree/prototype/event-clustering).
Where a claim could not be measured, §8 says so.

---

## 0. Verdict first

**GDELT's GKG solves half of it, and the half it does not solve is the half that carries the
signal.**

1. **The URL join works, and the prior 23% figure was an artifact of using a single timestamp.**
   Accumulating both GKG feeds over the cluster window ±1 hour and indexing by
   `V2DOCUMENTIDENTIFIER` joins **6,598 of 6,924 clustered articles = 95.3%**. Median per-story join
   rate **100%**, and **not one** of the 100 multi-language stories failed to join.

2. **The surface-language problem does not exist. GKG's name fields are 100% Latin script even for
   Arabic, Chinese, Greek, Hebrew, Russian, Ukrainian, Serbian, Macedonian, Bulgarian and Persian
   sources** — GDELT machine-translates first and runs the English pipeline over the translation.
   `Teherán` vs `طهران` never arises. Measured over 40 (language × field) cells with ≥30 names:
   **Latin 100.0%, native script 0.0%, in every cell.**

3. **But normalising the script is not resolving the entity, and the residue is worse than it looks.
   MT preserves source-language word order and invents variants.** In one real story cluster, the
   non-English articles name the United States as `States Attached`, Saudi Arabia as `Arabia Saudi`,
   the Persian Gulf as `Persian Bay` and `Gulf Persian`, the Strait of Hormuz as `Sound Of Hormuz`,
   the White House as `Home White`, the Middle East as `Halfway East`, `Low East`, `East Average`
   and `Close East`.

4. **Building actor presence directly on those strings would manufacture the divergence the measure
   is supposed to detect.** For actors named in ≥25% of a story's English articles, the mean
   presence gap against the same story's non-English articles is **0.501 on `V2.1ALLNAMES`** and
   **0.508 on `V1PERSONS`+`V1ORGANIZATIONS`**, with **97.6%** and **98.4%** of actors showing a gap
   above 0.20. On the same articles the gazetteer-resolved `V1LOCATIONS` channel gives **0.179**, and
   the null — two random halves of the *English* articles only — gives **0.03 or less on every
   channel**. Between two *non-English* languages the surface channel still gives **0.463** while
   resolved locations give **0.117**. The artifact is cross-lingual, it is not about English, and it
   is four to six times the size of the resolved channel.

5. **`V1LOCATIONS` is genuinely resolved** — canonical English name plus FIPS country code, ADM1
   code, coordinates and a GNS/GNIS feature id, identical across languages. It is the one GKG field
   that can be trusted as an entity identifier. **It contains no straits.** `hormuz` appears 0 times
   in `V1LOCATIONS` across 6,598 joined articles and 32 times in `V2.1ALLNAMES`; `strait` 0 versus
   38. The actor that carried #8's finding — *only 9 of 43 domains name Hormuz* — is invisible to the
   only properly resolved GKG field.

6. **Recommendation: a hybrid, and the alias table is not optional.**
   `V1LOCATIONS` for the geographic axis, plus a **1,094-entity Wikidata alias table (2.1 MB JSON,
   0.53 MB gzipped, no model download)** used two ways: to canonicalise GKG's machine-translated name
   strings, and to read the original-language title directly. Measured on the same 100 multi-language
   stories: presence gap **0.189** English-vs-non-English and **0.160** between two non-English
   languages, against **0.504 / 0.449** for the naive design — with **96.0% article recall** (95.4%
   on non-English articles) and 6.3 comparable actors per story. Hormuz is recovered at **25/480**
   articles in the Iran/Trump story, where every GKG-only design recovers **zero**.

7. **An unresolved name must never enter the measure.** Because omission is the signal, the measure
   is computed over the resolved vocabulary only, and a polity is marked *not evaluable* for an actor
   rather than *absent* whenever the table cannot see that actor in that polity's language. Measured:
   the alias inventory covers 66–99% of entities per language, so this gate costs almost nothing —
   which is also why it is not the real risk. **The real risk is morphology, not a missing entity**
   (§6.4).

---

## 1. The corpus this was measured on

`gsg_docembed`, 8 consecutive 15-minute slots, `20260802133000`–`20260802151500`:
**21,975 distinct article URLs, 57 languages, 3,419 domains**, 0 unparseable records.

Clustering follows `prototypes/cluster_proto.py`: connected components over cosine similarity of the
512-dim USEv4 embeddings. The percolation transition on this window is at **0.76**, not the 0.68–0.70
of #2's spot-check — at 0.70 the largest component is 5,745 articles (26.1% of the corpus) and
visibly conflates stories:

| threshold | clusters | largest | largest % | ≥3 domains | ≥3 dom & ≥2 lang | ≥3 dom & ≥3 lang |
|---|---|---|---|---|---|---|
| 0.68 | 1,495 | 7,829 | 35.6% | 459 | 125 | 54 |
| 0.70 | 1,730 | 5,745 | 26.1% | 553 | 124 | 54 |
| 0.74 | 1,919 | 2,195 | 10.0% | 637 | 114 | 52 |
| **0.76** | **1,970** | **605** | **2.8%** | **656** | **100** | **44** |
| 0.80 | 1,971 | 417 | 1.9% | 689 | 74 | 32 |

**The operating point is not a constant of the method.** #2 located it at 0.68–0.70 on a different
window; here that value produces a blob. Anything shipped must locate the transition per run, or the
clusters are not what the code thinks they are.

At 0.76: **656 stories with ≥3 distinct domains (6,924 articles)**, of which **100 also span ≥2
languages (3,238 articles, 50 languages)**. Those 100 are the test set for everything below. The
largest are real:

| story | articles | domains | languages | English headline |
|---|---|---|---|---|
| #0 | 605 | 449 | 31 | Thousands under evacuation order from wildfires in Spokane, Wash. |
| #1 | 516 | 345 | 38 | Iran's Defence Minister calls every threat to country as… |
| #2 | 295 | 194 | 30 | Moscow mayor calls Saturday's deadly bomb attack a 'terrorist act' |
| #3 | 270 | 204 | 24 | US and Israel staged Spain migration invasion |
| #4 | 210 | 204 | 25 | Blaze on Indonesian passenger ferry leaves at least five dead |

Language mix of the multi-language subset: English 34.9%, Spanish 12.2%, Russian 5.9%, Greek 5.4%,
German 5.3%, Italian 4.1%, Arabic 3.0%, Romanian 2.7%, Ukrainian 2.7%, Turkish 2.3%, Serbian 2.3%,
Albanian 2.2%, French 2.2%, Portuguese 2.0%, then a 30-language tail. **This is a far better substrate
than `data/news.json`'s one-source-per-language corpus** — 3,419 domains, and the confound #3
identified is gone.

---

## 2. The GKG join: measured, not assumed

Both feeds, `{ts}.gkg.csv.zip` and `{ts}.translation.gkg.csv.zip`, over
`20260802123000`–`20260802161500` — the cluster window ±1 hour, **16 slots × 2 feeds**.

- 31 of 32 files served. `20260802161500.translation.gkg.csv.zip` was not yet published (HTTP error,
  not a 200-with-empty-payload).
- **158 MB of zipped CSV**, 10,821 rows from the English feed and 27,547 from the translation feed,
  **38,368 distinct `V2DOCUMENTIDENTIFIER` values**.
- Parsing and URL-indexing all 38,368 rows: **51 s** on a laptop. Note `csv.field_size_limit` must be
  raised — `V2GCAM` exceeds Python's 128 KB default field limit and the reader raises.

### Coverage

| measure | value |
|---|---|
| clustered articles with a GKG row, exact URL | **6,598 / 6,924 = 95.3%** |
| same, after URL normalisation (host lowercase, strip `www.`, strip trailing `/`) | 6,598 = 95.3% |
| per-story join rate, 100 multi-language stories | mean **95.7%**, median **100.0%**, min 20.0% |
| stories with zero joined articles | **0 / 100** |

**URL normalisation buys exactly nothing** — `V2DOCUMENTIDENTIFIER` is byte-identical to the
`gsg_docembed` `url` field. #2's claim holds without qualification, and the 23% overlap it reported
was a single-timestamp artifact: the feeds sit on offset publication schedules, and a ±1 hour
accumulation window closes the gap entirely.

Per language, articles with ≥100 in the set:

| language | joined | language | joined |
|---|---|---|---|
| English | 90.8% | Chinese | 98.8% |
| Spanish | 98.3% | Arabic | **100.0%** |
| German | 99.4% | French | 97.6% |
| Turkish | 98.0% | Portuguese | 98.3% |
| Greek | **100.0%** | Romanian | **100.0%** |
| Italian | 96.3% | Ukrainian | **100.0%** |
| Russian | 98.4% | Vietnamese | 81.9% |
| Albanian | 93.5% | Serbian | **100.0%** |

English is the *worst-covered* language at 90.8%, and every non-English language except Vietnamese is
above 93%. Field population over the 6,598 joined rows:

| field | populated |
|---|---|
| `V2.1ALLNAMES` | 97.9% |
| `V1THEMES` | 92.9% |
| `V1LOCATIONS` | 89.5% |
| `V1ORGANIZATIONS` | 72.3% |
| `V2.1TRANSLATIONINFO` | 64.0% |
| `V1PERSONS` | **52.9%** |

`V1PERSONS` is populated on barely half the rows. Any design that needs leaders needs a second path
to them.

**Cost.** ~10 MB zipped per 15-minute slot across both feeds ⇒ **~960 MB/day**, or ~158 MB per run
for a 2-hour window with the ±1h margin. That is 43× the 22 MB/day of the GSG edge files and it is
the main new cost this design introduces. It is affordable on a public runner (14 GB disk) but it is
not free, and it must be budgeted in [#11](https://github.com/exdsgift/tensionr/issues/11).

---

## 3. Are the names normalised across languages? Yes in script, no in form

### 3.1 Script: fully normalised

Script of every extracted name, for articles whose source language uses a non-Latin script. All 40
cells with ≥30 names:

| language | field | names | Latin | native script |
|---|---|---|---|---|
| Arabic | `V2.1ALLNAMES` | 1,789 | 100.0% | 0.0% |
| Arabic | `V1PERSONS` | 341 | 100.0% | 0.0% |
| Chinese | `V2.1ALLNAMES` | 3,674 | 100.0% | 0.0% |
| Greek | `V2.1ALLNAMES` | 2,254 | 100.0% | 0.0% |
| Russian | `V2.1ALLNAMES` | 1,539 | 100.0% | 0.0% |
| Hebrew | `V2.1ALLNAMES` | 152 | 100.0% | 0.0% |
| Ukrainian | `V2.1ALLNAMES` | 556 | 100.0% | 0.0% |
| Serbian, Macedonian, Bulgarian, Persian, ChineseT | all fields | 30–639 each | 100.0% | 0.0% |

Not one native-script name in any field, in any language. `V2.1TRANSLATIONINFO` records the source
(`srclc:rus;eng:GT-RUS 1.0`), confirming the mechanism: the translation feed is GDELT's own MT
pipeline, and the English GKG extractor runs over the translation.

**So the decisive question of the ticket has a clean answer: the translation feed's names are given in
English, not in the source language.** There is no cross-script alias problem in GKG.

### 3.2 Form: not normalised at all

The most frequent `V2.1ALLNAMES` strings in story #1 (Iran/Trump, 516 articles, 38 languages),
English articles versus non-English articles:

| English articles | non-English articles |
|---|---|
| `Donald Trump` (116), `Saudi Arabia` (77), `United States` (58), `Middle East` (52), `White House` (43), `Islamic Republic` (41), `Petroleum Exporting Countries` (36), `Truth Social` (34), `Persian Gulf` (10) | `United States` (69), `Saudi Arabia` (55), `Middle East` (47), **`States Attached`** (41), **`Before Body Parts`** (22), **`East Average`** (19), `Donald Trump` (18), **`Republic Islamic`** (17), **`East Sunday`** (16), **`Persian Bay`** (13), **`Guard Revolutionary`** (11), **`Emirates Arab Attached`** (11), **`Army Israeli`** (10), **`Countries Exporters`** (10), **`Gulf Persian`** (10), **`Sound Of Hormuz`** (10), **`Close East`** (10), **`Home White`** (9), **`Truth Socialtext`** (9), **`Arabia Saudi`** (8) |

Three mechanisms, all visible: **word-order inversion carried over from the source language**
(`Arabia Saudi` ← *Arabia Saudita*, `Republic Islamic`, `Guard Revolutionary`, `Home White`),
**lexical mistranslation of a fixed name** (`States Attached` ← *Estados Unidos*, `Emirates Arab
Attached`, `Persian Bay`, `East Average` / `Close East` / `Halfway East` / `Low East` ← *Middle
East*), and **tokenisation damage** (`Truth Socialtext`).

The effect is measurable in the vocabulary itself. Distinct name strings per article, over the 100
multi-language stories:

| field | English | non-English |
|---|---|---|
| `V2.1ALLNAMES` | 1.97 | **3.78** |
| `V1PERSONS`+`V1ORGANIZATIONS` | 1.35 | 0.98 |
| `V1LOCATIONS` (resolved key) | 0.49 | 0.33 |

Non-English articles generate **1.9× more distinct `ALLNAMES` strings per article**, while producing
*fewer* resolved locations and *fewer* persons/organisations. That is the signature of a channel whose
vocabulary is being inflated by noise rather than by content.

### 3.3 What `V1LOCATIONS` actually contains

```
4#Jerusalem, Israel (General), Israel#IS#IS00#31.7667#35.2333#-797092;1#Israel#IS#IS#31.5#34.75#IS
4#Athens, AttikíR, Greece#GR#GR35#37.9833#23.7333#-814876;1#Greece#GR#GR#39#22#GR;1#Spain#SP#SP…
```

Type, canonical English full name, FIPS country code, ADM1 code, coordinates, and a GNS/GNIS feature
id. Two examples from the same story, in different languages:

- Chinese article → `Israel; Lebanon; Iran; Saudi Arabia; Iraq; United States`
- Greek article → `Algeria; Iraq; Saudi Arabia; Russia; Kuwait; Israel`
- Russian article → `Moscow, Moskva, Russia; Oman; Washington, Washington, United States; Tehran, Tehran, Iran; Iran`
- English article → `Iran; United States; Israel; Tehran, Tehran, Iran`

**This is a real entity identifier and it is stable across languages.** It is also restricted to the
geographic gazetteer: no persons, no organisations, no straits, no canals.

---

## 4. The correctness trap, measured

The measure is per-actor presence per polity. If a resolution failure is language-correlated, it
reads as omission — and omission is the signal. This is the failure mode #8 warned about, and it is
directly measurable with a within-article control: **the same articles, the same stories, the same
selection rule, different channels.**

For each story and each channel, take every actor present in ≥25% of group A's articles and record
Δ = p(A) − p(B). Selecting on p(A) biases Δ upward by construction, which is why the null uses the
*same* selection rule on a split that cannot carry a language effect.

| split | `V2.1ALLNAMES` | `V1PERSONS`+`V1ORG` | `V1LOCATIONS` country (resolved) |
|---|---|---|---|
| **English vs non-English** | **0.501** (97.6% > 0.2) | **0.508** (98.4% > 0.2) | **0.179** (38.2% > 0.2) |
| **two largest non-English languages** | **0.463** (96.7%) | **0.395** (96.9%) | **0.117** (34.5%) |
| null: English vs English, random halves | −0.002 (5.8%) | −0.006 (9.6%) | −0.029 (0.0%) |
| null: non-English vs non-English, random halves | 0.068 (27.5%) | 0.056 (26.1%) | 0.011 (2.0%) |
| null: one single non-English language, random halves | 0.073 (24.4%) | 0.050 (22.0%) | 0.048 (13.5%) |

Read the rows in order. The estimator is unbiased under the null (row 3, ≈0). It is nearly unbiased
*within* one non-English language (row 5, 0.073) — so the channel works fine when both sides went
through the same MT path. It breaks the moment the two sides are different languages, whether or not
either is English (rows 1 and 2, ≈0.46–0.51, with **97% of all actors showing a gap above 0.20**).

**An actor-presence table built on `V2.1ALLNAMES` would report that non-English outlets omit
essentially every actor.** Every story would look maximally divergent, and the ranking would be
driven by how many languages a story spans. That is the third measure in this project to be refuted
by measurement rather than by argument, and it would have been invisible from the field
documentation, which says only that the field is populated.

The resolved channel is better by a factor of 3–4 but **it is not zero**: 0.179 and 0.117. Part of
that is genuine — non-English outlets do write about different geography — and part is the geocoder
having lower recall on translated text. **I cannot decompose it** (§8), which is exactly why only the
*difference between channels on the same articles* is interpretable here, never the absolute level.

---

## 5. The alias table: what it costs and what it covers

Since GKG resolves places but not persons, organisations or chokepoints, and since GDELT surfaces
have a demonstrated habit of dying (the Global Entity Graph stopped 2026-06-18; the Global Frontpage
Graph decayed to a 45-byte payload while still returning HTTP 200), the alias table #3 judged the
only practicable option was built and measured.

### 5.1 Inventory, resolved rather than remembered

Eight SPARQL queries against `query.wikidata.org`, **~5 minutes wall time, run offline, outside CI**:

| kind | how selected | entities |
|---|---|---|
| state | `wdt:P463 wd:Q1065` (UN member) + Kosovo, Palestine, Taiwan, Vatican | 232 |
| leader | `P35` head of state and `P6` head of government of each, `P31 = Q5` | 427 |
| capital | `P36` of each | 216 |
| strait | `P31/P279* wd:Q37901` with ≥25 sitelinks | 102 |
| igo | `P31/P279* wd:Q245065` with ≥60 sitelinks | 53 |
| group | 41 militant/political groups and government seats, by exact English label with a sitelink floor | 41 |
| waterway | 23 named seas, gulfs and canals, by exact English label | 23 |
| territory | 16 disputed territories, by exact English label | 16 |
| **total** | | **1,094** |

Two process notes that matter more than they look.

**Do not write QIDs from memory.** My first attempt hardcoded them, and 34 of 65 were wrong in ways
that pass silently: `Q47740` is *Muslim*, not the Gulf of Aden; `Q39816` is *valley*, not the Gaza
Strip; `Q118863` is *North Island*, not the Strait of Malacca; `Q1249` is *bohrium*. The table looked
fine and quietly scored a wildfire story as mentioning Xinjiang. Every entry now carries its QID,
seed name, sitelink count and English description in `curated_qids.json`, so the inventory is
auditable.

**Exact-label resolution has known holes.** 7 of 48 curated names did not resolve because Wikidata's
English label differs from common usage: Houthi movement, Hayat Tahrir al-Sham, OECD, UNHCR, GCC,
Kremlin, Ansar Allah. That is a documented gap, not a solved problem.

### 5.2 Size

| artifact | size |
|---|---|
| alias index, JSON | **2.09 MB** |
| alias index, gzipped | **0.53 MB** |
| aliases indexed | 56,801 in 68 languages |
| ambiguous keys dropped (same string, two entities) | 401 |
| code-shaped aliases dropped | 7,056 |
| model download required | **none** |

0.53 MB shipped, against ≥3.05 GB for mGENRE and 130 GiB for a Wikidata dump. Wikidata content is
CC0. Runtime cost is a dict lookup.

### 5.3 Alias availability is not the bottleneck

Fraction of the 1,094 entities that have at least one Wikidata label or alias in the article's own
language:

| language | availability | language | availability |
|---|---|---|---|
| English | 99.8% | Turkish | 94.3% |
| French | 98.7% | Greek | 93.9% |
| Spanish | 98.3% | Hebrew | 92.8% |
| Russian | 98.3% | Arabic | 92.2% |
| Chinese | 97.5% | Indonesian | 90.3% |
| German | 97.4% | Romanian | 86.6% |
| Portuguese | 95.8% | Serbian | 78.4% |
| Ukrainian | 94.6% | Bulgarian | 74.8% |
| Italian | 94.6% | Slovak | 71.9% |
| | | Lithuanian | 67.8% |
| | | Croatian | 67.4% |
| | | **Macedonian** | **65.9%** |

Wikidata's multilingual labels are dense for exactly the class of actors this project cares about.
Gating on availability (§7) therefore changes almost nothing — measured, the gated and ungated
divergence figures are **identical** on this window. The inventory is not where this design fails.

### 5.4 Coverage on real clusters, and two configuration bugs worth inheriting

Articles whose **original-language title** yields ≥1 resolved actor:

| matcher variant | all ≥3-domain stories | multi-language stories | multi-language, n≥30 | place precision vs GDELT's own gazetteer |
|---|---|---|---|---|
| all-language index, exact n-gram | 35.8% | 45.2% | 48.1% | 73.4% |
| all-language, prefix-tolerant | 43.3% | 55.2% | 58.4% | 70.8% |
| **language-scoped, exact** | 28.1% | 39.7% | 43.0% | **89.9%** |
| language-scoped, prefix-tolerant | 33.7% | 48.6% | 52.8% | 88.1% |
| language+English scoped, exact | 31.8% | 42.4% | 45.6% | 77.7% |
| language+English, prefix-tolerant | 37.6% | 51.5% | 55.5% | 77.5% |

Precision is measured against an independent reference — GDELT's own gazetteer-resolved
`V1LOCATIONS` and extracted names on the same article — and restricted to states, capitals and
waterways where that reference is meaningful. **It is a lower bound**: a match is counted wrong
whenever GDELT failed to extract the entity, which happens (the residual unattested cases are led by
`United States`/Spanish, `European Union`/Spanish and `Donald Trump`/Arabic, all almost certainly
real mentions the reference missed).

Two hygiene rules, with their measured effect:

- **Drop ISO-3166 / IOC-style code aliases** (`POR`, `PER`, `IRI`, `SG`). Wikidata carries them as
  aliases and they collide with common function words: `per` is a preposition in Italian and
  Albanian, `por` in Spanish and Portuguese. Precision **69.5% → 85.5%**, coverage 42.4% → 37.4%.
  Clear win.
- **Drop single-token English aliases that share no token with the canonical English label**
  (`northwest`, `jiang` → Xinjiang; `indian sea` → Arabian Sea). Attestation **79.6% → 81.0%**.
  Applying the same rule to *all* languages instead is a trap: it deletes precisely the native-script
  single-token labels the cross-lingual case depends on, and non-English title recall collapses
  **44.8% → 19.1%**. **Alias hygiene must be script-aware or it destroys the thing it is protecting.**

And two configuration bugs I introduced and then measured, both of which any implementation will hit:

- **A code-shape filter must be ASCII-only.** `len(s) <= 4 and s.upper() == s and s.isalpha()` is
  true for every short CJK, Arabic and Hebrew string, because those scripts are caseless. It silently
  deleted `中国`, `伊朗`, `イラン`, `이란`. Restricting the rule to ASCII lifts Korean title coverage
  **0% → 80%**.
- **A minimum alias length must be script-aware.** A flat ≥4-character floor deletes essentially
  every Chinese label, since `中国` is two characters. With a floor of 2 for CJK: Chinese
  **0% → 23.1%**, Traditional Chinese **0% → 60.0%**, and the probes now resolve
  (`美国` → Q30, `伊朗` → Q794, `特朗普` → Q22686 Donald Trump).

Per-language title coverage after both fixes, on the multi-language stories:

| language | coverage | language | coverage |
|---|---|---|---|
| Turkish | 75.7% | Albanian | 48.6% |
| French | 75.0% | German | 44.7% |
| Vietnamese | 74.5% | Romanian | 39.8% |
| Arabic | 73.5% | Indonesian | 32.4% |
| Portuguese | 71.9% | Russian | 27.1% |
| Korean | 80.0% | Greek | 13.8% |
| Hebrew | 61.9% | Ukrainian | 24.1% |
| ChineseT | 60.0% | Chinese | 23.1% |
| Italian | 56.7% | Croatian | 16.7% |
| Spanish | 51.9% | Finnish | 14.5% |

**The bottom of that table is a morphology problem, not a coverage problem.** Wikidata has a Russian
label for 98.3% of the entities and a Ukrainian one for 94.6%, yet Russian titles resolve at 27% and
Ukrainian at 24%, because the title says *Ірану* / *Іраном* and the label says *Іран*.
Prefix-tolerant matching — accept a match when an alias is a prefix of a title token of length ≥5 —
is the cheap proxy for a stemmer, and it is where the gains are:

| language | exact | prefix-tolerant |
|---|---|---|
| Russian | 21.1% | **34.0%** |
| Ukrainian | 11.3% | **21.6%** |
| Finnish | 1.8% | **14.5%** |
| Slovak | 25.0% | **53.1%** |
| Polish | 39.3% | **60.7%** |
| Hungarian | 47.1% | **67.6%** |
| Romanian | 42.2% | **59.6%** |
| Lithuanian | 24.2% | **33.9%** |

at a precision cost of 1.8 points (89.9% → 88.1%). Take it.

### 5.5 Transliteration: not needed, and not harmful at this volume

Romanising Cyrillic and Greek titles (ISO-9-ish) and matching against the Latin-language alias sets
adds **31 matches over 692 Cyrillic/Greek articles**, of which **27 are attested and 4 are not**
(87.1%). The wins are the cases where a Cyrillic rendering lands on the international form —
`Moscow` from Russian and Ukrainian, `Ukraine`, `Belarus`, `Tehran` from Serbian. The failures are
false friends (`Chile` from Ukrainian and Macedonian).

**Verdict: transliteration is unnecessary, because Wikidata already supplies native-script labels for
92–98% of the inventory in every script that matters.** It neither rescues much nor breaks much. Do
not build it; if a later gap appears, revisit with a real sample — 31 events is far too few to
characterise its precision, and the 87.1% above should not be quoted as if it were.

---

## 6. Designs compared on the same 100 stories

All figures are over the same 3,085 joined articles in 100 multi-language stories, same selection
rule, same nulls.

| design | actors/story | EN vs non-EN Δ | two non-EN languages Δ | null Δ | article recall, all | recall, non-EN |
|---|---|---|---|---|---|---|
| **D1** GKG `V1LOCATIONS` only | 3.8 | 0.179 | 0.117 | −0.029 | 94.6% | 93.7% |
| **D2** GKG name fields, raw | 16.2 | **0.504** | **0.449** | 0.023 | 98.1% | 97.5% |
| **D5** alias table over the source-language title | 0.9 | 0.224 | 0.360 | 0.019 | 47.8% | 44.3% |
| **D7** GKG names → alias table, token-set + stopword-stripped keys | 2.0 | 0.241 | 0.231 | −0.006 | 67.1% | 65.5% |
| **D8 = D1 ∪ D7 ∪ D5** | **6.3** | **0.189** | **0.160** | **−0.021** | **96.0%** | **95.4%** |

D2 is the design a reader of the GKG documentation would build. It has the best raw recall and it is
unusable: 16 actors per story of which 97% are language artifacts.

**D7 is the step that makes GKG's name fields usable.** Look up each MT-English name string in the
alias table under three keys in order: the exact normalised string, the sorted token multiset, and
the sorted token multiset with function words removed. The second key absorbs MT's word-order
inversions; the third bridges Wikidata's *Strait of Hormuz* to MT's *Hormuz Strait*. Measured, the
token-set key alone recovers `European Union` from Spanish (41 articles), Italian (36) and Portuguese
(9), plus `Persian Gulf`, `Black Sea`, `Red Sea`, `Israel Defense Forces`, `Western Sahara`,
`United States` and `European Commission` from Romance-language sources — all cases where the raw
string had the modifier on the wrong side.

Between two non-English languages, D7's Δ of 0.231 is worse than D1's 0.117 but half of D2's 0.449;
D5's 0.360 is the per-language recall spread of §5.4 showing up as false divergence. **Neither
channel alone is clean; the union is, because their recall failures are uncorrelated** — D8's Δ is
below every component's on both splits while its null stays at −0.021.

### The chokepoint axis, which is the whole point

Story #1 (Iran/Trump, 516 articles, 38 languages, 480 joined). Straits, waterways and territories
recovered:

| design | recovered |
|---|---|
| D1 GKG `V1LOCATIONS` | **none** |
| D2 GKG names, raw | **none** |
| D4 GKG names → alias, token-set only | `Gaza Strip` 83/480, `Persian Gulf` 31, `Red Sea` 23, `West Bank` 8 |
| D7 + stopword-stripped keys | `Gaza Strip` 83, `Persian Gulf` 31, `Red Sea` 23, **`Strait of Hormuz` 21**, `West Bank` 10 |
| D5 alias over source title | `Gaza Strip` 56, **`Strait of Hormuz` 4**, `West Bank` 2, `Crimea` 1 |
| **D8** | `Gaza Strip` 113, `Persian Gulf` 31, **`Strait of Hormuz` 25**, `Red Sea` 23, `West Bank` 10 |

**#8's signal — Hormuz named by a minority of the coverage — survives the cross-lingual step only
through the alias table, and only with stopword-stripped token-set keys.** Every GKG-only design
scores it zero, which would read as "no outlet in 38 languages mentioned the strait" in a story that
is about the strait.

### False positives

81.0% of D7's matches are attested by the same article's own GKG name or location strings. The
unattested residue is led by `Sanaa`/English (51), `United States`/Spanish (44), `European
Union`/Spanish (41), `Abiy Ahmed`/English (35), `Washington, D.C.`/Russian (19). At least the
`United States` and `European Union` cases are D7 working correctly on strings the reference itself
mangled, so **81.0% is a floor, not an estimate.** `Sanaa` and `Abiy Ahmed` are genuine alias
collisions and would need per-entity alias review — the audit list is the tool for that, and it
should be regenerated on every table rebuild.

---

## 7. What happens when an actor is missing

This is the correctness requirement in the ticket, and it decides the schema, not just the code.

**1. The measure is computed over the resolved vocabulary only.** An unresolved surface string is
never an actor. It cannot be present, so it cannot be absent, so it cannot manufacture an omission.
This inverts D2's failure mode: the naive design turns every resolution failure into an omission;
this design turns every resolution failure into a *non-observation*.

**2. Presence is compared only where the actor is evaluable.** For actor *a* and polity *P*, the cell
is `evaluable` only if (i) the alias table carries an alias for *a* in at least one of *P*'s
publication languages, and (ii) *P*'s articles joined GKG. Otherwise the cell is **`not evaluable`**,
which is a third state distinct from `named` and `not named`, and it must exist in the stored schema
and in the interface copy, not only in the computation. Measured on this window: the gate changes
nothing (identical Δ gated and ungated), because §5.3's availability is 66–99%. **It is cheap
insurance, and the fact that it never fires here is itself the finding** — a missing *entity* is not
the real hazard.

**3. The real hazard is a missing inflected form, and the gate cannot see it.** Wikidata has a
Ukrainian label for 94.6% of the inventory while Ukrainian titles resolve at 24.1%. The alias exists;
the matcher misses the case ending. This is invisible to an availability check and it is
language-correlated, which makes it exactly the failure that manufactures divergence. The only
defence that is measurable today: **publish the per-language matcher recall next to every divergence
number, and refuse to compare two polities whose recall differs by more than a stated threshold.**
On this window the spread runs from 13.8% (Greek) to 75.7% (Turkish); a Greek-vs-Turkish comparison
on the title channel is not admissible and the code must say so rather than emit a number.

**4. Refresh.** States, capitals, straits, IGOs and territories are effectively static. Heads of
state and government are not — 427 of the 1,094 entities are people whose office changes. Rebuild
offline on a schedule (weekly is ample; the build is 8 SPARQL queries and ~5 minutes), commit the
0.53 MB artifact, and regenerate the false-positive audit list in the same job. **Entity linking is
never a per-run cost**, which was #3's conclusion and survives measurement.

---

## 8. What I could not measure, and why

- **One window, one day.** Everything rests on 2026-08-02 13:30–15:15 UTC. There is no temporal
  replication, no weekday/weekend contrast, no different news mix. The percolation threshold already
  moved from #2's 0.68–0.70 to 0.76 between two windows, so treating any of these numbers as
  constants would be a mistake.
- **No human ground truth.** Every precision figure is measured against GDELT's own extraction,
  which for non-English articles is itself derived from machine translation. Both the 89.9% and the
  81.0% are therefore **lower bounds with a correlated reference**, and neither is a substitute for
  hand-labelling a sample of clusters.
- **The 0.179 residual on the resolved channel is not decomposed.** I cannot separate "non-English
  outlets genuinely write about different geography" from "GDELT's geocoder has lower recall on
  translated text". Only the *difference between channels on the same articles* is interpretable
  here; the absolute Δ level is not a divergence measurement and must not be reported as one.
- **Small story counts on the headline splits.** Only 9 stories in this window had ≥8 English and ≥8
  non-English joined articles, and 13 had two non-English languages with ≥5 articles each. The
  actor counts (34–178) are larger but actors within a story are not independent. Nothing here
  carries a confidence interval.
- **Polity is proxied by publication language**, as in #8, not by the sourced polity table from
  [#21](https://github.com/exdsgift/tensionr/issues/21). Every "language" row above will need
  re-measuring once polities exist.
- **Titles are assumed to be original-language.** `gsg_docembed`'s `title` appeared to be the
  source-language headline in every case I inspected, and the language distribution is consistent
  with that, but I did not verify it systematically against the articles.
- **Japanese is uninformative here.** All 43 Japanese articles in the cluster set are entertainment
  or local news containing no state, leader, organisation or chokepoint, so 0% coverage measures the
  sample, not the matcher. Korean rests on 5 articles.
- **I did not test whether GKG stays alive.** Given that the Global Entity Graph stopped in June 2026
  and the Frontpage Graph decayed to a 45-byte payload behind a 200 OK, D8's dependence on GKG is a
  live risk. It is partly mitigated by design — D5 needs only `gsg_docembed` and the alias table —
  but the degradation path (D8 → D5 alone, Δ 0.189 → 0.224 English/non-English but 0.160 → 0.360
  between non-English languages, recall 96.0% → 47.8%) is bad enough that it should be a monitored
  condition, with a payload-size check rather than a status-code check.
- **No stemmer was tested.** Prefix-tolerant matching is a proxy. A real morphological analyser for
  Russian, Ukrainian, Greek, Finnish and the Slavic languages would plausibly close most of the
  remaining gap, and I have no measurement of its size or cost.
- **7 curated entities remain unresolved** (Houthi movement, Hayat Tahrir al-Sham, OECD, UNHCR, GCC,
  Kremlin, Ansar Allah). The Houthis in particular are a recurring actor in exactly the stories this
  project targets.

---

## 9. Recommendation

**Adopt D8. Do not build actor presence on `V2.1ALLNAMES`.**

1. **Join GKG by URL.** Accumulate both `{ts}.gkg.csv.zip` and `{ts}.translation.gkg.csv.zip` over
   the cluster window ±1 hour and index on `V2DOCUMENTIDENTIFIER`. 95.3% coverage, 100% median per
   story, no normalisation needed. Budget ~158 MB per run and raise `csv.field_size_limit`. Validate
   on row count, not on HTTP status.
2. **Take the geographic axis from `V1LOCATIONS`**, keyed on the feature id and FIPS code, never on
   the display name.
3. **Canonicalise `V2.1ALLNAMES`, `V1PERSONS` and `V1ORGANIZATIONS` through the alias table** with
   three lookup keys in order: exact normalised string, sorted token multiset, sorted token multiset
   minus function words. Discard every string that does not resolve.
4. **Additionally match the alias table against the original-language title**, language-scoped plus
   English, prefix-tolerant. This is the only path that reaches chokepoints and it is the fallback if
   GKG degrades.
5. **Ship the table as a 0.53 MB gzipped artifact**, rebuilt weekly offline. Keep
   `curated_qids.json` in the repo so the inventory is auditable, and regenerate the false-positive
   audit on every rebuild.
6. **Store three states per (actor, polity) cell — `named`, `not named`, `not evaluable`** — and
   publish per-language matcher recall next to every divergence figure. Refuse the comparison when
   two polities' recall differs beyond a stated threshold.
7. **Fix the two script bugs before anything else**: code-shape filters ASCII-only, minimum alias
   length script-aware. They are one-line changes and without them Chinese, Japanese and Korean
   resolve at zero.

What this does **not** deliver: a defensible single divergence number. #8's conclusion stands — the
per-actor presence table is the explainable artifact. What changes with this work is that the table
can now be built across languages without the resolution failure masquerading as editorial omission,
and that the claim can be checked: **0.189 against 0.504.**
