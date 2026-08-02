# What the 0.189 language residual is made of, and what a published figure can do

Research for [#23](https://github.com/exdsgift/tensionr/issues/23), under the map in
[#1](https://github.com/exdsgift/tensionr/issues/1), building on
[#22](https://github.com/exdsgift/tensionr/issues/22)'s measurement and on
[#11](https://github.com/exdsgift/tensionr/issues/11)'s decision that the published unit
is a per-(story, actor) figure carrying this residual. Written 2026-08-02.

**Question.** #22 measured that presence built on the recommended design — `V1LOCATIONS`
plus a Wikidata alias table — carries a **0.189** English-vs-other gap against a null of
−0.021, and named four candidate causes without separating them: machine-translation
quality varying by language, morphology, alias-table coverage differing by script, and
genuine editorial difference correlated with language. The last is not an artefact at all.
This document separates them as far as two days of live data allow, establishes how far a
*published* figure can move, prices every correction, and drafts the sentence to publish
if none of them works.

Everything below is measured on live GDELT for two windows, **2026-08-02 13:30–15:15 UTC**
(the window #22 used) and **2026-08-01 13:30–15:15 UTC** (a replication #22 did not have).
§7 says what could not be measured.

---

## 0. Verdict first

1. **Most of the residual is not an artefact.** With group sizes matched so the estimator's
   small-sample bias is identical in every cell, crossing a **polity** boundary while
   holding the **language** constant reproduces **+0.086** of gap (95% CI **[+0.026,
   +0.145]**, P(≤0) = 0.001). Crossing the language boundary on top of that adds only
   **+0.037** (95% CI **[−0.013, +0.087]**, P(≤0) = 0.074) — **not distinguishable from
   zero**. Roughly **70%** of the excess is editorial difference between polities, which is
   the signal the product exists to show. The share itself is imprecise: 95% CI
   [25%, 111%].

2. **The design has power, because it recovers the known answer on the known-bad channel.**
   Run identically on raw `V2.1ALLNAMES` — the design #22 refuted — the same test attributes
   the excess to **language, +0.104 [+0.080, +0.130]**, and finds no significant polity term.
   The method distinguishes the two, and it says the recommended design's residue is mostly
   editorial while the naive design's is mostly translation.

3. **The residual does not transfer to a published figure as an error of 19 points.** The
   0.189 is a property of the *estimator that detected it* — it selects actors on one
   language group's presence, which forces the gap positive. On the actual published unit,
   the signed English-minus-other gap has **mean +1.5pp and median −0.7pp** over 408 figures.
   Re-weighting a figure so every publishing language counts equally moves it by **1.1pp at
   the median, 8.1pp at the 90th percentile, 33pp at worst** (window B: 1.2 / 7.4 / 36pp).

4. **The move is predictable from the denominator, which the row already shows.** At
   `M ≥ 50` evaluable sources the median move is **0.7pp** and the p90 **3.7pp**. Below
   `M = 20` it is **4.9pp** and **16.7pp**. Big-denominator figures are safe; thin ones are
   not, and the floor left "to be calibrated" on #11 is the lever that decides which.

5. **What does *not* survive is the ranking, and it fails for a reason nothing can fix.**
   Ordering by division, `H(p)`, is flat near p = 0.5: five rows sit within **0.005** of the
   top score, while the p90 language re-balancing move is worth **dH ≈ 0.004** at p = 0.5.
   So the artefact cannot move a figure much and can still decide which row is the headline.
   Top-10 overlap between the as-published and language-balanced orderings is **3/10** at a
   floor of 10 sources, rising to **8/10** at 30 and **9/10** at 50. **The #1 row is never
   stable.**

6. **Per-language calibration is refuted by measurement.** A per-language main effect
   explains **1.2%** of the variance of the per-(figure, language) deviation; rms deviation
   falls from 11.1pp to 11.0pp; and the fitted offsets do not replicate between the two
   windows (**r = +0.11**). There is no stable per-language bias to calibrate away. This is
   the fourth measure in this project refuted by measurement rather than argument.

7. **What is available, at zero cost in coverage**: publish the figure with its
   **language-balanced twin** or its **leave-one-language-out band** (median width 2.1pp),
   raise the evaluable-source floor to **≥30**, and stop claiming a unique #1. Restricting
   to one script costs 25% of sources for a residual of 0.4pp — not worth it. Restricting to
   English costs **68% of sources** and defeats the product.

8. **The honest sentence, drafted in §6**, is publishable and the numbers in it are
   per-figure rather than corpus-wide.

---

## 1. What this was measured on

Both windows were clustered by the method of
[`prototypes/cluster_proto.py`](https://github.com/exdsgift/tensionr/tree/prototype/event-clustering) —
connected components over cosine similarity of the 512-dim USEv4 embeddings — with the
percolation transition located per run as #22 requires.

| | window A (2026-08-02) | window B (2026-08-01) |
|---|---|---|
| slots, 13:30–15:15 UTC | 8 | 8 |
| distinct article URLs | 21,975 | 22,514 |
| languages / domains | 57 / 3,419 | 58 / 3,608 |
| percolation transition | **0.76** | **0.76** |
| stories with ≥3 domains | 656 | 694 |
| of those, ≥2 languages | **100** (3,238 articles) | **101** (3,031 articles) |
| GKG join on `V2DOCUMENTIDENTIFIER` | **3,085 / 3,238 = 95.3%** | **2,876 / 3,031 = 94.9%** |

Window A reproduces #22's corpus exactly — same article count, same threshold, same 656 and
100, same 95.3% join. That is deliberate: this document had to be comparable with the 0.189,
not merely adjacent to it.

**A third independent reading of the percolation threshold.** #2 located it at 0.68–0.70,
#7 at 0.75, #22 at 0.76. Here it is **0.76 on both days**. It is still not a constant of the
method and must be located per run, but 0.76 has now held across two windows on two days.

### The resolution channels

#22's design D8 was rebuilt from its recipe rather than inherited, since no code was
committed with it. The alias table was rebuilt from Wikidata by eight SPARQL queries, with
every QID **resolved by label and audited** — #22 recorded that 34 of 65 hand-written QIDs
were silently wrong, and that trap is not worth re-entering.

| | this rebuild | #22 |
|---|---|---|
| states / leaders / capitals | 232 / 425 / 212 | 232 / 427 / 216 |
| straits / IGOs / curated | 109 / 156 / 52 | 102 / 53 / 80 |
| **entities** | **1,186** | 1,094 |
| alias rows, 81 languages | 117,717 | 56,801 |
| index keys after hygiene | 107,079 | — |

#22's three hygiene rules were applied and matter as it said: ASCII-only code-shape filter,
script-aware minimum alias length, and dropping single-token English aliases that share no
token with the canonical label. Property ids were verified by reading their labels back
(`P463` → *member of*, `P901` → *FIPS 10-4*), and FIPS country codes were mapped to QIDs so
that `V1LOCATIONS` and the alias table share one key space and the union channel cannot
count one actor twice.

Channels, in #22's notation: **D1** `V1LOCATIONS` country codes; **D2** raw GKG name fields;
**D7** GKG names canonicalised through the alias table on three keys (exact, sorted token
multiset, token multiset minus function words); **D5** alias table over the original-language
title, language-scoped plus English, prefix-tolerant; **D5x** the same without prefix
tolerance; **D8 = D1 ∪ D7 ∪ D5**.

### The rebuild reproduces #22's headline table

Same estimator, same splits, groups of ≥8 per side — which on window A is the same **9
stories** #22 reported:

| split | D2 | D1 | D7 | D5 | D8 |
|---|---|---|---|---|---|
| English vs non-English | +0.518 | **+0.179** | +0.294 | +0.238 | **+0.208** |
| two largest non-English | +0.444 | +0.136 | +0.006 | −0.078 | +0.115 |
| null: English, random halves | +0.072 | +0.003 | +0.028 | +0.029 | +0.007 |
| null: one non-English language, halves | +0.046 | −0.027 | +0.004 | +0.082 | −0.019 |

**#22's 0.179 on D1 is reproduced to the digit**, D2's 0.501 as 0.518, D8's 0.189 as 0.208,
and the nulls sit at zero. The residual is real and it is where #22 left it.

**One thing #22 could not see, which changes how the rest is read.** Lower the minimum group
size from 8 to 3 and the *nulls* stop being zero: D8's English-random-halves null goes from
+0.007 to **+0.103**, D2's from +0.072 to +0.139. The plug-in estimator is biased upward at
small denominators, exactly as #3 found, and at the group sizes available in most stories the
bias is comparable to the effect being measured. **Every comparison below therefore matches
group sizes to exactly *m* articles per side by resampling**, so the bias is identical in
every cell of the design and only the differences between cells are read.

---

## 2. The decomposition

### 2.1 The design

Four kinds of pair, all drawn inside a single story, all resampled to *m* = 3 sources per
side, 40 resamples per pair, both windows pooled. Sources are collapsed first — one voice per
verbatim title, one article per domain — as #11 decided. Polity comes from the publisher's
ccTLD (an IANA delegation fact) plus a curated list for gTLD outlets; it resolves for **57.8%
/ 62.3%** of articles, and unresolved outlets are excluded rather than guessed.

| design cell | what it contains |
|---|---|
| same language, same polity | estimator bias + variation between outlets inside one polity |
| same language, **different polity** | + editorial difference across polities, **language held constant** |
| **different language**, same polity | + language artefact, **editorial held roughly constant** |
| different language, different polity | + both — this is what #22 measured |

### 2.2 The result, on the recommended design

Channel D8, both windows pooled:

| design cell | pairs | mean Δ | increment |
|---|---|---:|---|
| same language, same polity | 71 | +0.133 | baseline |
| same language, **DIFFERENT polity** | 68 | **+0.219** | **editorial +0.086**, 95% CI [+0.026, +0.145], P(≤0) = 0.001 |
| DIFFERENT language, same polity | 6 | +0.156 | (too few pairs to quote — see §7) |
| DIFFERENT language, DIFFERENT polity | 2,082 | **+0.256** | **language +0.037**, 95% CI [−0.013, +0.087], P(≤0) = 0.074 |

Editorial share of the excess: **70%**, 95% CI [25%, 111%]. The interval on the share is
wide enough that "roughly two thirds to all of it" is the honest reading, and "none of it" is
excluded at the 5% level in the sense that the editorial term is significantly positive while
the language term is not.

It replicates on each window separately:

| | editorial increment | language increment |
|---|---|---|
| window A alone (30 / 1,008 pairs) | +0.104 [+0.017, +0.191] | +0.028 [−0.054, +0.105] |
| window B alone (38 / 1,074 pairs) | +0.089 [−0.005, +0.186] | +0.039 [−0.022, +0.099] |
| pooled (68 / 2,082 pairs) | **+0.086 [+0.026, +0.145]** | **+0.037 [−0.013, +0.087]** |

The same-language cross-polity pairs are real newsroom rivalries, not a construction:

| contrast | pairs | mean Δ |
|---|---:|---:|
| Spanish, Spain ↔ Argentina | 12 | +0.216 / +0.281 |
| Spanish, Spain ↔ Mexico | 6 | +0.270 / +0.165 |
| Spanish, Mexico ↔ Argentina | 6 | +0.232 / +0.214 |
| Spanish, Argentina ↔ Dominican Republic | 2 | +0.621 / +0.667 |
| German, Germany ↔ Austria | 8 | +0.246 / +0.512 |
| French, France ↔ Switzerland | 8 | +0.233 / +0.066 |
| Portuguese, Brazil ↔ Portugal | 4 | +0.364 / +0.030 |
| Romanian, Romania ↔ Moldova | 4 | +0.135 / +0.158 |
| **Russian, Ukraine ↔ Russia** | 4 | +0.211 / +0.033 |
| Russian, Russia ↔ Israel | 2 | +0.293 / +0.267 |
| Arabic, Egypt ↔ Palestine | 2 | +0.095 / +0.148 |
| English, UK ↔ United States | 2 | +0.074 / +0.062 |
| English, UK ↔ India | 2 | +0.256 / −0.194 |

Two Russian-language outlets, one in Kyiv and one in Moscow, covering the same story, differ
by about as much as a Greek outlet differs from a Turkish one. That is the finding in one
sentence.

### 2.3 The validation: the same test on the channel already known to be broken

If this design could not detect a language artefact, the result above would be worthless.
Run on **D2**, raw `V2.1ALLNAMES` — which #22 proved is a translation artefact — it detects
it and attributes it correctly:

| channel | editorial increment | language increment |
|---|---|---|
| **D2** GKG names, raw | +0.027 [−0.004, +0.059] | **+0.104 [+0.080, +0.130]** |
| **D1** `V1LOCATIONS` | **+0.109 [+0.046, +0.172]** | +0.014 [−0.040, +0.067] |
| **D7** GKG names → alias table | +0.015 [−0.080, +0.104] | **+0.104 [+0.039, +0.175]** |
| **D5** alias over source title, prefix-tolerant | −0.013 [−0.088, +0.062] | **+0.053 [+0.001, +0.109]** |
| **D5x** the same, exact matching only | −0.044 [−0.122, +0.032] | **+0.083 [+0.025, +0.143]** |
| **D8** the recommended union | **+0.086 [+0.026, +0.145]** | +0.037 [−0.013, +0.087] |

D2 and D8 have almost the same *total* excess over the same-language same-polity baseline
(+0.133 and +0.132 on window A) and **opposite composition**. That is what #22's channel
comparison could not show and what the ticket asked for.

### 2.4 #22's four candidate causes, separated as far as the data allows

**Cause 4 — genuine editorial difference correlated with language: the largest term, and
not an artefact.** +0.086 [+0.026, +0.145], significantly positive, replicated on both
windows, and reproduced by rival polities publishing in the *same* language. It belongs in
the measure. Note what this implies: an actor-presence figure is doing its job, and the
reason its cross-language gap is large is mostly that outlets in different polities really do
name different actors.

**Cause 1 — machine-translation quality: the artefact that remains, and it lives entirely in
the name channels.** The language increment is significant on the two channels that read
GDELT's machine-translated name strings or the source title (D7 +0.104, D5 +0.053) and
indistinguishable from zero on the one channel that is genuinely gazetteer-resolved
(D1 +0.014 [−0.040, +0.067]). The union inherits a diluted version, +0.037. This is a
channel-level attribution, not a per-language one; see the next point for why a per-language
attribution turned out to be unavailable.

**Cause 2 — morphology: measurable, and about a third of the title channel's artefact.**
The only clean handle is #22's prefix-tolerant matching, which is a proxy for a stemmer.
Turning it on cuts the title channel's language increment from **+0.083** to **+0.053** — so
inflection accounts for roughly **0.030** of it, and **0.053 survives the cheap fix**.
Morphology is real, it is worth the 1.8 points of precision #22 measured, and it is not the
main thing left. Per-language title recall still ranges from 0.0% (Traditional Chinese, on 30
articles) to 77.2% (Arabic) with sd 19.9 points — but on the **union** channel the spread
closes to **79.5% (Greek) to 100%**, sd 5.0. #22's proposed procedural gate — refuse a
comparison whose per-language recall differs too much — almost never fires on the union
channel, which is the channel that ships.

**Cause 3 — alias-table coverage differing by script: refuted as a driver.** If the residue
were script-linked coverage, pairs crossing a script boundary would carry more of it. They
carry less:

| D8, cross-polity pairs | pairs | mean Δ | language increment |
|---|---:|---:|---|
| same language | 68 | +0.219 | baseline |
| different language, **same script** | 1,114 | +0.271 | **+0.051 [+0.000, +0.100]** |
| different language, **different script** | 968 | +0.238 | **+0.018 [−0.036, +0.067]** |

This is consistent with #22's own §3.1: GDELT machine-translates before extraction, so GKG's
name fields are 100% Latin whatever the source script, and script never enters D1 or D7 at
all. It enters only through D5, and there the ordering does reverse as it should — same-script
+0.043 [−0.009, +0.100] against cross-script **+0.066 [+0.013, +0.118]** — but on 883–924
pairs with overlapping intervals, so this is a direction, not a quantity.

**The `not evaluable` gate stays cheap and stays necessary.** Across the published figures it
excludes a median of **0.5%** of a figure's sources (p90 3.3%, max 40.7%), and **50.8%** of
figures exclude at least one. #22 found the gate never fires; at figure level it fires
constantly but small, which is exactly the behaviour #11 decided to publish beside `M`.

### 2.5 What this decomposition cannot do

- It cannot put a number on machine-translation quality *per language*, only on the channels
  that depend on it. §4E shows why: there is no stable per-language offset to estimate.
- The fourth cell of the 2×2 — different language, **same** polity — has **6 pairs** across
  both windows (Ukraine Ukrainian/Russian, Israel Hebrew/Russian). Read against the
  same-language same-polity baseline it gives +0.156 − +0.133 = **+0.023**, which is
  consistent with the +0.037 obtained the other way, and 6 pairs cannot confirm anything, so
  it is not used above. The design's second, independent route to the same quantity is
  therefore **not established**.
- Additivity is assumed: the language increment is read as
  (different language, different polity) − (same language, different polity). If crossing a
  language boundary interacts with crossing a polity boundary, that reading is wrong and
  nothing here would detect it.
- The editorial term is measured on the polities whose outlets use ccTLDs plus a curated
  gTLD list. English-language United States outlets are systematically under-represented in
  it, which is the largest polity in the corpus.

---

## 3. Per-figure sensitivity

### 3.1 The unit, built as #11 decided it

Source = domain, after collapsing verbatim titles to one voice. `M` = evaluable sources,
`N` of which name the actor, `not evaluable` excluded and counted. Floor: `M ≥ N_floor`
**and** ≥2 polities. Ranking by division, `H(p)`.

At a floor of 10 evaluable sources: **563 publishable figures over 24 stories** (window A)
and **545 over 21** (window B). Median `M` = 120, median 18 languages per figure.

### 3.2 How far a figure moves

| perturbation | window A: median / p75 / p90 / max | window B |
|---|---|---|
| **language-balanced − as published** | **1.1 / 3.4 / 8.1 / 33.3 pp** | 1.2 / 3.3 / 7.4 / 35.7 pp |
| polity-balanced − as published | 1.7 / 4.8 / 11.1 / 91.3 pp | 2.0 / 5.3 / 12.2 / 75.0 pp |
| leave-one-language-out, largest move | 1.6 / 5.2 / 8.5 / 47.8 pp | 1.9 / 4.3 / 8.4 / 67.9 pp |
| \|p(English) − p(non-English)\| | 2.8 / 10.0 / 18.0 / 66.7 pp | 2.4 / 7.7 / 20.0 / 75.0 pp |
| spread of p across languages | 16.7 / 37.5 / 75.0 / 100 pp | 16.7 / 40.0 / 66.7 / 100 pp |

The spread *across* languages is large — a figure's languages disagree with each other by
tens of points — while the figure itself barely moves, because with 18 languages the
disagreement averages out. That is the whole reason a per-(story, actor) figure is more robust
than the corpus statistic that was used to find the artefact.

### 3.3 Which figures are safe, and it is legible from the row

By denominator (window A, language-balancing move):

| | figures | median | p90 | max |
|---|---:|---:|---:|---:|
| M < 20 | 72 | **4.9pp** | 16.7pp | 33.3pp |
| 20 ≤ M < 50 | 146 | 2.2pp | 10.5pp | 26.2pp |
| **M ≥ 50** | 345 | **0.7pp** | **3.7pp** | 19.7pp |

By level — figures near p = 0.5, which are the ones the ledger promotes, move most:

| | figures | median | p90 |
|---|---:|---:|---:|
| p < 0.25 | 486 | 0.9pp | 5.1pp |
| **0.25 ≤ p < 0.5** | 33 | **8.3pp** | 16.7pp |
| 0.5 ≤ p < 0.75 | 13 | 3.6pp | 15.7pp |
| p ≥ 0.75 | 31 | 2.0pp | 8.3pp |

**The ledger's selection rule promotes exactly the figures that move most.** Ranking by
division picks p ≈ 0.5, and p ≈ 0.5 is where the language composition has the most room to
push. This is not a coincidence to be managed away; it is a structural property of ordering
on entropy.

By provenance — which channel produced the marks:

| | figures | share |
|---|---:|---:|
| gazetteer (`V1LOCATIONS` on ≥90% of marks) | 403 | **71.6%** |
| mixed | 8 | 1.4% |
| **name / title channels only** | 152 | **27.0%** |

Every strait, waterway, organisation, group, leader and capital figure is name/title-only —
which is #22's finding restated at figure level: `V1LOCATIONS` contains no straits, so the
actor class that carried #8's result is reachable only through the channels where §2.4 located
the surviving artefact. **Provenance is the per-figure safety flag, and the flag should be
stored with the row.** Composition sensitivity does *not* substitute for it: name-only
figures move *less* under re-balancing (median 0.7pp) purely because they sit at low p.

### 3.4 The 0.189 does not transfer to a figure, and here is why

Signed p(English) − p(non-English), per published figure, 408 figures with ≥5 sources on
each side:

| | figures | mean | median | p10 | p90 |
|---|---:|---:|---:|---:|---:|
| all | 408 | **+1.5pp** | **−0.7pp** | −10.0pp | +16.7pp |
| gazetteer marks | 280 | +1.3pp | −0.7pp | −10.0pp | +16.7pp |
| name/title marks only | 121 | +1.9pp | −0.5pp | −5.5pp | +11.9pp |
| kind = leader | 28 | +3.5pp | +1.2pp | −7.3pp | +16.7pp |

Centred on zero and roughly symmetric. #22's 0.501 and 0.189 are large because its estimator
selects actors named in ≥25% of one side's articles, which forces the difference positive by
construction — #22 says so, and its nulls are built to absorb it. **A published figure is not
selected that way, so it does not inherit the number.** The largest single case in the corpus
runs the other way: `Greece 149/312`, p = 0.478, English 0.286 against non-English 0.575, a
gap of **−28.9pp** — Greek outlets naming Greece, which is editorial and obvious.

### 3.5 Where it does bite: the low-p figures the product leads on

On figures with p < 0.25 and at least 5 marks, the ratio p(non-English) / p(English) has
**median 0.55** (p10 0.09, p90 2.18); on name/title-only figures, **median 0.40**. In
absolute terms these are small moves, because p is small. In relative terms they are the
difference between "a tenth of the coverage names it" and "a twentieth does".

Named cases, window A story 1 (Iran/Trump, 259 evaluable sources, 36 languages, 47 polities):

| figure | p | English | non-English | gap | provenance |
|---|---:|---:|---:|---:|---|
| **Strait of Hormuz 19/259** | 0.073 | 0.074 | 0.073 | **+0.0pp** | name/title |
| Persian Gulf 20/259 | 0.077 | 0.044 | 0.089 | −4.5pp | name/title |
| Gaza Strip 23/259 | 0.089 | 0.176 | 0.058 | +11.9pp | name/title |
| White House 28/259 | 0.108 | 0.235 | 0.063 | **+17.2pp** | name/title |
| Islamic Revolutionary Guard Corps 10/248 | 0.040 | 0.132 | 0.006 | **+12.7pp** | name/title |
| Saudi Arabia 127/259 | 0.490 | 0.515 | 0.482 | +3.3pp | gazetteer |
| United States 160/259 | 0.618 | — | — | — | gazetteer |

**Hormuz — the figure this project has been carrying since #8 — is clean**: 7.4% of English
sources and 7.3% of non-English name it, and language re-balancing moves it from 0.073 to
0.10. The two figures beside it are not: `White House` and `IRGC` are named by English
sources at three to twenty times the non-English rate. Whether that is Washington-centric
framing or the alias table failing on *Casa Blanca* / *Sepah* variants **cannot be told
apart at the level of a single figure** — §2 bounds it in aggregate at +0.087 and no more,
but it cannot allocate a specific row.

A worse case on a large denominator: `Donald Trump 78/183`, p = 0.426, language-balanced
**0.229** — a **20pp** move, with 78 further sources marked `not evaluable`. That row should
not be published as a point value.

### 3.6 The ranking, which is the part that fails

| floor | figures | top-1 | top-5 | top-10 | top-20 | median rank move |
|---|---:|---:|---:|---:|---:|---:|
| M ≥ 10 | 563 | 0/1 | 1/5 | **3/10** | 13/20 | 42 of 563 |
| M ≥ 30 | 380 | 0/1 | 2/5 | **8/10** | 16/20 | 30 of 380 |
| M ≥ 50 | 345 | 0/1 | 2/5 | **9/10** | 16/20 | 24 of 345 |

Overlap between the as-published ordering and the language-balanced ordering. Window B is the
same shape (3/10 at floor 10). Raising the floor fixes the *set* and never fixes the **#1**.

Why: at floor 30, **5 rows sit within 0.005** of the top division score and 8 within 0.020,
while the p90 language re-balancing move of 3.8pp is worth **dH ≈ 0.004** at p = 0.5. The
artefact is the same size as the gap between the top five rows.

| the rows that can be #1 (window A, floor 30) | figure | p | H | balanced p | balanced H |
|---|---:|---:|---:|---:|---:|
| People's Republic of China | 26/53 | 0.491 | 0.9997 | 0.410 | 0.9764 |
| Saudi Arabia | 127/259 | 0.490 | 0.9997 | 0.512 | 0.9996 |
| Turkey | 22/46 | 0.478 | 0.9986 | 0.333 | 0.9183 |
| Greece | 149/312 | 0.478 | 0.9985 | 0.606 | 0.9676 |
| Romania | 33/61 | 0.541 | 0.9951 | 0.395 | 0.9679 |

**Ranking on `H(p)` cannot support a claim about a unique sharpest row.** It can support a
claim about a band. #11 chose division "because that is honest and available now", and it is
— but its top is a tie, and the product must say so rather than pick.

---

## 4. Corrections, and what each costs

| | figures kept | sources kept | residual |
|---|---:|---:|---|
| **A. language-balanced (or polity-balanced) value beside the figure** | 94.1% / 98.2% | **100%** | removes composition only; does not touch channel bias |
| **B. restrict to Latin-script sources** | 89.3% / 94.1% | **74.9% / 73.1%** | \|p − p(Latin)\| median **0.4pp**, p90 2.6pp, max 22.8pp |
| **C. restrict to English sources** | 78.2% / 77.6% | **32.0% / 28.2%** | not measurable — the comparison is gone |
| **D. leave-one-language-out band instead of a point** | 100% | 100% | width median **2.1pp**, p90 15.2 / 12.1pp, max 68.8 / 80.0pp |
| **E. per-language calibration** | — | — | **refuted, see below** |
| **F. raise the evaluable-source floor to ≥30** | 380 of 563 = 67.5% | 100% | p90 move 8.1pp → **3.8pp**; top-10 stability 3/10 → 8/10 |

**B is the option that looked most attractive and is not worth taking.** Restricting a figure
to sources sharing a script changes it by 0.4pp at the median and costs a quarter of the
panel. Given §2.4 found cross-script pairs carry *less* language artefact than same-script
ones, that is the expected result — and it means #23's "restricting a figure to sources
sharing a script" can be closed as measured and rejected.

**C defeats the product**, as the ticket anticipated: 68% of sources discarded to remove an
effect whose per-figure mean is +1.5pp.

**E, per-language calibration, is refuted by measurement.** Over 11,266 (figure, language)
observations with ≥3 sources each, across 1,108 figures and 33 languages:

- the largest fitted per-language offset is **−4.8pp** (Bosnian, 83 observations); most are
  under 2pp; English is **+1.5pp** against a within-language sd of **8.1pp**;
- a per-language main effect explains **1.2%** of the variance of the deviation, and rms
  deviation falls from **11.1pp to 11.0pp**;
- the offsets do not replicate between the two windows: **r = +0.11** over 27 languages with
  ≥15 observations in both. Italian is +1.3pp one day and −1.7pp the next; Russian +1.5pp then
  −2.2pp; Croatian +5.0pp then −1.6pp.

There is no stable per-language bias. Fitting one would be fitting a day's noise, and
applying yesterday's coefficients would inject error rather than remove it.

**So the answer to "what correction is available" is: A, D and F, none of which discards a
source.** Publish the language-balanced twin, publish the band, raise the floor. The channel
bias identified in §2.4 is *not* corrected by any of them and has to be stated.

---

## 5. What this means for the figure the product publishes

1. **State the residual as a per-figure quantity, not as 0.189.** The corpus statistic
   answers a different question. On a published figure the honest numbers are: 1pp typical,
   8pp at the ninetieth percentile, 33pp worst observed, falling to 4pp at p90 if the floor
   is ≥30 sources.
2. **Set #11's undecided `N` from stability, not only from story yield.** 10 sources leaves
   the top ten 30% stable; 30 leaves it 80% stable at the cost of a third of the rows. That
   is the trade #11 recorded as "to be calibrated, with the procedure declared" — here is the
   procedure and the measurement.
3. **Do not publish a unique #1.** Publish the top band, with the count of rows inside the
   artefact's width. The alternative is a headline that changes when nothing in the world does.
4. **Store the provenance of every mark and show it.** A figure resolved from the gazetteer
   carries no language artefact this study could detect. A figure resolved only from
   translated names or titles carries up to +0.18 on the pair estimator, and every chokepoint,
   organisation and leader figure is in that class — including the ones the product most wants
   to lead on.
5. **Keep the three marks and the excluded count.** `not evaluable` fires on half of all
   figures, small each time. #11 decided to publish it; that decision is load-bearing.

---

## 6. The honest published statement

No correction removes the artefact, so it must be stated. Drafted for the row and for the page:

> **On a figure.** `Strait of Hormuz — named by 19 of 259 evaluable sources (7%), across 36
> languages and 47 polities; 2 sources could not be evaluated.` *Weighting every publishing
> language equally instead gives 10%. This figure is resolved from translated names rather
> than from a gazetteer, so it carries a language artefact we can bound but not remove: up to
> 9 percentage points on a comparison between two language groups.*

> **On the page, once.** *These figures count sources, and sources publish in different
> languages. We measured what that does. Crossing a language boundary adds 0.04 to a measured
> presence gap (95% confidence −0.01 to +0.09); crossing a national boundary while holding
> the language constant adds 0.09 (+0.03 to +0.15) — so most of what looks like a translation
> artefact is editorial difference, which is what these figures are for. On an individual
> figure the effect is 1 percentage point at the median and under 8 for nine figures in ten.
> We do not correct it, because the per-language offsets we measured do not hold from one day
> to the next. We publish each figure's language-balanced value beside it so you can see the
> size of the effect on that row, and we do not claim a single sharpest row, because the
> artefact is larger than the gap between the top few.*

The short form, if only one sentence fits:

> *This figure carries a language artefact of up to 8 percentage points (median 1), and we
> publish its language-balanced value beside it so you can see how much.*

That sentence is defensible on the measurements in §3.2, and the "up to" is a p90 rather than
a maximum — the maximum observed is 33pp on a 12-source denominator, which is a further
argument for the floor in §5.2.

---

## 7. What could not be measured, and why

- **Two windows, two consecutive days, one time of day.** 2026-08-01 and 2026-08-02,
  13:30–15:15 UTC, Saturday and Sunday. No weekday contrast, no different hour, no different
  season of news. The percolation threshold landing on 0.76 both times is encouraging and is
  not a proof of stability — it moved between #2's window and #22's.
- **The fourth cell of the 2×2 is effectively empty.** Six same-polity, cross-language pairs.
  The decomposition therefore rests on the *difference* between two cells rather than on two
  independent estimates of the same quantity, and it assumes additivity. This is the single
  largest weakness in §2 and no amount of resampling fixes it — it needs polities that
  genuinely publish in two languages at volume (Ukraine, Israel, Switzerland, Canada, Bosnia),
  measured over days rather than hours.
- **The editorial term rests on 68 pairs.** Its interval is [+0.026, +0.145]; the ratio of
  editorial to language is quoted as 70% with a 95% interval of [25%, 111%], which is another
  way of saying two days cannot pin the share. What two days *can* say is that the editorial
  term is positive and the language term is not distinguishable from zero.
- **Polity is proxied by ccTLD plus a curated gTLD list**, resolving 58–62% of articles. It
  is precise where it fires and blind to `.com` outlets, which under-represents the United
  States — the largest English-language polity — in exactly the cell that estimates the
  editorial term. #21's sourced domain-to-polity table would replace this and should.
- **No human ground truth.** As in #22, every precision-like quantity is measured against
  GDELT's own extraction, which for non-English articles is itself machine-translated. The
  reference is correlated with the thing being measured.
- **Machine-translation quality is attributed to channels, not to languages.** §4E shows
  there is no stable per-language offset to estimate, so "MT quality varies by language"
  could not be turned into per-language numbers. It may still be true and simply be swamped
  by per-figure variation at these sample sizes.
- **Morphology is bounded only through prefix-tolerant matching.** No stemmer or
  morphological analyser was tested, so the 0.030 attributed to inflection is what the cheap
  proxy recovers, not what a real analyser would.
- **The alias table is a rebuild, not #22's artefact.** 1,186 entities against 1,094, more
  IGOs and straits, 81 languages. The channel recalls land close to #22's (union 93.5% / 89.7%
  against its 96.0%; title 47.7% / 43.4% against 47.8%) and D1's residual reproduces to the
  digit, but it is not the same file. One curated seed — Gulf Cooperation Council — failed to
  resolve by English label, as several did for #22.
- **`H(p)` rank stability was tested against language re-balancing only.** Syndication
  collapse at owner level (#11's second stage), the small-sample bias correction #20 made
  mandatory, and per-source sampling all move the same ranking, and their combined effect on
  the top band is not measured here.
- **No claim is made about GKG's survival.** The design leans on it exactly as #22's does,
  and #22's warning stands.

---

## 8. Recommendation

**The 0.189 does not disqualify a published per-(story, actor) figure. It disqualifies the
claim that one row is the sharpest.**

1. **Publish the figure.** Adopt D8 as #22 recommends. The residual on the published unit is
   1pp at the median and under 8pp for nine figures in ten.
2. **Publish the language-balanced value beside it.** Zero cost in coverage, and it shows the
   reader the size of the effect on that row rather than a corpus average.
3. **Set the evaluable-source floor at ≥30**, on the stability measurement in §3.6 rather
   than on story yield alone. Below it, keep #11's rule: counts, no fraction, no rank.
4. **Publish a top band, not a #1.** Report how many rows fall within the artefact's width
   of the top division score — 5 within 0.005 on this window.
5. **Store and show mark provenance.** Gazetteer-resolved figures are clean; name- and
   title-resolved figures carry up to +0.18 on the pair estimator, and that class contains
   every chokepoint the product cares about.
6. **Do not build a per-language calibration**, do not restrict figures by script, and do not
   fall back to English-only. All three are measured and priced above; the first is noise, the
   second buys 0.4pp for a quarter of the panel, the third destroys the product.
7. **Say it out loud.** The sentence in §6 is publishable. Silence is not, and neither is
   "0.189" — because on the unit that actually gets published, that number is not the error.
