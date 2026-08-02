# Grouping events from multilingual headlines: state of the art

Research for [tensionr#2](https://github.com/exdsgift/tensionr/issues/2), under the map
[tensionr#1](https://github.com/exdsgift/tensionr/issues/1). Date: 2026-08-02.

**The question.** tensionr's thesis is that the project measures *disagreement between the outlets that
tell an event*, not "world tension". The load-bearing mechanism is grouping articles that describe the
**same event** across sources and languages. The only text available is the headline (~10 words). If that
grouping does not hold, the thesis collapses.

**The answer, up front.** The highest-leverage question in the ticket — *does GDELT already give us a
reusable grouping?* — turns out to be **yes, largely**. GDELT's **Global Similarity Graph** publishes
precomputed cross-language article-pair similarity edges (~22 MB/day) and precomputed 512-dimensional
multilingual document embeddings (~7.5 MB per 15-minute slot). That moves the centre of gravity of this
document: the primary question is no longer *"which embedding model should we run?"* but *"can we use
GDELT's grouping, and what still has to be decided if we do?"*

So this document is organised as:

| § | Question |
|---|---|
| **0** | Corrections — three premises in the ticket and the map do not survive contact with the data |
| **A** | What I measured on tensionr's own 500 headlines, and what it says about the project's core risk |
| **1** | Does GDELT already give us the clusters? (the answer, and what it costs) |
| **2** | Multilingual embeddings — now the **fallback**, and the answer for the ~80% of articles GSG leaves as singletons |
| **3** | Clustering with unknown *k*, and how to choose a threshold non-arbitrarily |
| **4** | How cluster quality gets evaluated |
| **5** | Recommendation, implementation sketch, cost |

Everything below is either sourced to a primary reference (paper, official documentation, model card,
repository) or measured by me on this repository's actual data. Measurements are marked **[measured]** and
their conditions are stated. Estimates are marked **[estimate]**. Where I could not establish something, I
say so instead of guessing.

**A note on the risk verdict**, since it is the reason this ticket exists. The map calls the clustering the
project's *structural risk*: if it does not hold, the thesis collapses. It holds — but not at the grain the
map assumes. Measured on tensionr's own corpus (§A.6): grouping headlines into **cross-lingual story
clusters** works (recall 1.00 on a hand-labelled gold set, hand-judged precision ~0.86). Grouping them into
**events** does not (precision ~0.23 at the same operating point). The mechanism is sound; the *word* has to
change from "event" to "story".

---

## 0. Corrections to the premises of the ticket

Before any of the research: three of the assumptions in the ticket and the map do not survive contact with
`data/news.json` and `src/fetch_gdelt.py`. They change the shape of the problem, so they come first.

### 0.1 The corpus is not "~9 languages". It is 5, and the `language` field is wrong for 4 of 18 sources

**[measured]** on `data/news.json` (500 articles, 18 domains, `seendate` between `20260621T075639Z` and
`20260622T124012Z`).

The `language` field is not detected — it is a hardcoded lookup keyed by domain, in
`fetch_gdelt.py:292-316` (`rss_metadata`). Four entries are wrong:

| domain | declared `language` | actual language of the titles | n |
|---|---|---|---|
| `www.spiegel.de` | `English` | **German** | 20 |
| `en.mercopress.com` | `Spanish` | **English** (it is the English edition) | 10 |
| `www.japantimes.co.jp` | `Japanese` | **English** (it is the English edition) | 21 |
| `www.rt.com` | `Russian` | **English** (`/rss/news/` is the English edition) | 16 |

Verified by Unicode-script analysis of the titles plus reading them. Examples: Spiegel, declared `English`
— *"Keir Starmer kündigt Rücktritt an - Nigel Farage fordert Neuwahlen"*. RT, declared `Russian` —
*"Trump-backed 'Tiger' projected to win Colombian election"*.

The **real** distribution is therefore:

| language | articles | share | distinct sources |
|---|---|---|---|
| English | 341 | 68.2% | 14 |
| Arabic | 79 | 15.8% | **1** (`aljazeera.net`) |
| French | 36 | 7.2% | **1** (`lemonde.fr`) |
| Spanish | 24 | 4.8% | **1** (`elpais.com`) |
| German | 20 | 4.0% | **1** (`spiegel.de`) |

Two consequences, both material:

1. **The cross-lingual problem is smaller than the ticket assumes** (5 languages, 2 scripts, 68% English) —
   which is good news for feasibility.
2. **There is exactly one source per non-English language.** "Disagreement between outlets" cannot be
   measured *within* French, Spanish, German or Arabic at all — only *between* one representative of each.
   This is a limitation of the corpus, not of the clustering, and no algorithm fixes it. It is a source-list
   problem, and it should be fixed before or alongside the prototype.

### 0.2 GDELT is currently contributing zero articles

**[measured]** all 500 articles in `data/news.json` have `source == "rss"`. Not one has `source == "gdelt"`,
even though `fetch_gdelt_data()` (`fetch_gdelt.py:374-393`) sets `a["source"] = "gdelt"` on everything the
DOC API returns. The GDELT call is either failing silently (it is wrapped in a bare `except` that prints and
continues) or being crowded out by the 500-article cap at `fetch_gdelt.py:468`.

The call itself is also very conservative: `maxrecords=50`, no `timespan`, no `sourcelang`, and a single
free-text query `"war conflict economy military finance"`.

So the corpus that the clustering must work on today is **RSS-only**, and the multilingual richness that
GDELT could supply is not being used. Section 1 is therefore not just "can we save work" — it is also "can
we fix the corpus".

### 0.3 `seendate` is the fetch timestamp, not the publication time

**[measured]** `fetch_gdelt.py:332` sets `"seendate": datetime.now().strftime(...)` for every RSS article.
It is not the article's publication date.

This matters for clustering: **time proximity cannot be used as a blocking or gating signal**, which is the
single cheapest and most standard trick in news event detection (events are local in time; comparing only
articles within a ±N-hour window cuts the pair count and kills a large class of false positives). Right now
all articles fetched in one run share a timestamp to the second, so the signal is not merely noisy — it is
absent. RSS entries almost always carry a real `published`/`updated` field that `feedparser` exposes; this
is a small fix with a large payoff for the mechanism.

Two more corpus facts worth recording:

- **The feed list is randomised per run.** `fetch_rss_news` takes `random.sample(ALL_FEEDS, 15)` of 23 feeds
  and only `entries[:10]` from each (`fetch_gdelt.py:287`, `:327`). Cross-source redundancy — the very thing
  the mechanism needs — is partly randomised away, and a maximum of ~150 articles enters per run.
- **Al Jazeera's Arabic feed is a general feed, not world news.** **[measured]** of its 79 articles, roughly
  half are 2026 World Cup football. Since Arabic is 100% of the corpus's second script, this substantially
  dilutes the only real cross-script test we have.

### 0.4 The compute budget is larger than the ticket assumes

The ticket states the constraint as "a free GitHub Action, today with `timeout 600`". Two clarifications
that widen the envelope considerably:

- **`tensionr` is a public repository** (verified: `gh repo view exdsgift/tensionr` → `"visibility":
  "PUBLIC"`). Standard GitHub-hosted runners for **public** repositories are **4 vCPU / 16 GB RAM / 14 GB
  SSD** for Linux, not the 2 vCPU / 8 GB that private repositories get.
  Source: <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>
- **`timeout 600` is self-imposed, not a platform limit.** It is a shell `timeout` on one workflow step
  (`.github/workflows/update_data.yml`, "Fetch data from GDELT"). GitHub's actual limit is *"Each job in a
  workflow can run for up to 6 hours of execution time."*
  Source: <https://docs.github.com/en/actions/reference/limits>

Also note that `timeout 600` wraps **only** the Python run. Dependency installation is a separate,
`uv`-cached step and is not counted against the 600 seconds. A model download, however, *would* happen
inside the Python run unless it is cached separately with `actions/cache` keyed on the model revision.

The practical budget is therefore: 4 cores, 16 GB, and as many minutes as we are willing to justify — with
the caveat that the workflow currently runs **hourly** (`cron: '0 * * * *'`), so runtime is multiplied by
24/day. Keeping the run in the low minutes is a good discipline, but it is a choice, not a hard wall.

---

## A. What I measured on tensionr's own 500 headlines

The literature answers "what is possible in general". It does not answer "does it work on *this* corpus".
So before reviewing the state of the art, I ran the experiment. Everything in this section is **[measured]**.

### A.1 Setup

- **Data**: `data/news.json` as committed, all 500 headlines, no filtering.
- **Hardware**: Intel Core i5-8257U @ 1.40 GHz, 4 physical / 8 logical cores, `torch.get_num_threads()==4`,
  CPU only. This is *slower* than a GitHub public-repo runner (4 vCPU of a modern server part), so the
  timings below are a conservative upper bound on runtime.
- **Stack**: `torch==2.2.2`, `transformers==4.44.2`, `sentence-transformers==3.0.1`, `scikit-learn==1.9.0`,
  `numpy==1.26.4`, Python 3.12.
- **Gold set**: I hand-labelled **6 narrow events / 43 articles** by reading titles, before running any
  model. They yield **162 gold pairs, 98 of them cross-lingual**.

  | event | n | languages |
  |---|---|---|
  | Starmer announces his resignation | 8 | de, en, fr |
  | De la Espriella wins the Colombian runoff | 12 | ar, de, en, fr |
  | Ras Laffan (Qatar) gas plant explosion | 5 | ar, en, fr |
  | Alan Greenspan dies | 3 | en |
  | France restricts alcohol during the heatwave | 5 | en |
  | First round of US–Iran talks ends | 10 | de, en, fr |

  **This gold set is a smoke test, not a benchmark.** It measures *recall* on events I happened to notice.
  It cannot measure precision over the other 457 articles, and it says nothing about events with no
  cross-lingual coverage. Treat every number below as directional.

Metrics reported: `rec` = fraction of the 162 gold pairs placed in the same cluster; `recXL` = same,
restricted to the 98 cross-lingual pairs; `contam` = mean fraction of a gold event's host cluster that is
*not* part of that event (an **upper bound** on error — see A.5); `nclus` / `largest` / `xling` = number of
clusters of size > 1, size of the biggest, and how many span more than one language.

### A.1b End-to-end cost, measured

Full recommended pipeline, warm Hugging Face cache, on the same slow laptop:

```
import libs       23.54 s     <- importing torch dominates; easy to forget
model load         9.87 s
encode 500        37.38 s     (13 titles/s)
similarity + connected components + multi-source filter   0.08 s
------------------------------------------------
TOTAL             70.88 s
```

Seventy seconds against a 600-second budget, on hardware slower than the runner. **The compute constraint
is not the binding constraint.** Notable details: the O(n²) similarity step is free at this size (a 500×500
float32 matrix is 1.0 MB), and importing torch costs more than clustering by two orders of magnitude.

Projected scaling from the measured rate:

| corpus size | encode | similarity matrix |
|---|---|---|
| 1,000 | ~75 s | 4 MB |
| 2,000 | ~150 s | 16 MB |
| 5,000 | ~374 s | 100 MB |
| 10,000 | ~748 s | 400 MB |

The brute-force O(n²) approach stays comfortable to roughly 5,000 articles. Beyond that, encoding — not
clustering — becomes the bottleneck, and only then is an approximate-nearest-neighbour index worth adding.

### A.2 The lexical baseline: good within a script, blind across scripts

TF-IDF over character 3–5-grams (`char_wb`), cosine, connected components:

| threshold | rec | recXL | clusters | largest |
|---|---|---|---|---|
| 0.50 | 0.04 | 0.00 | 21 | 4 |
| 0.40 | 0.15 | 0.00 | 28 | 10 |
| 0.35 | 0.36 | 0.14 | 34 | 15 |
| 0.30 | 0.44 | 0.14 | 36 | 24 |
| 0.25 | 0.59 | 0.36 | 38 | 34 |

The pattern is exactly what you would predict. Lexical overlap recovers same-language near-duplicates very
well — *"Alan Greenspan, architect of the modern American economy, dies aged 100"* (BBC) / *"…former US Fed
Reserve chair, dies aged 100"* (SCMP) / *"…longtime U.S. Federal Reserve chairman, dies aged 100"*
(The Hindu) group perfectly. Cross-lingual recall is non-zero **only** where a proper noun survives
transliteration (`Espriella`, `Colombi-`), and is **exactly zero across scripts**: not one Arabic article
ever joined an English one, at any threshold.

It also produces confident nonsense. At Dice ≥ 0.35 the Starmer cluster absorbs *"Barbados prime minister
announces manifesto for slavery reparations"* (shared trigram "prime minister announces"), and three
*different* World Cup matches (Argentina–Austria, Egypt–New Zealand, Uruguay–Cape Verde) merge into one
cluster because they share the Arabic template "كأس العالم 2026".

**Conclusion**: a lexical baseline is a genuinely useful component and costs nothing, but it cannot do the
one job the thesis actually requires — bridging languages. This is the precise gap embeddings must fill.

For reference, the repo's existing `generate_narrative_graph()` (`src/analytics.py:70-108`) is a weaker
version of this: whitespace-token overlap ≥ 2 after an 11-word English stopword list, on the first 100
articles only. It correctly links the three Greenspan headlines, and it also links *"Former Kenyan justice
minister blocked from entering Uganda"* to an Iran live-blog. It is not a clustering mechanism.

### A.3 Model comparison: the retrieval-vs-similarity distinction dominates

Encoding all 500 headlines, CPU, batch 32, normalised:

| model | dim | max_seq | encode 500 | throughput | load (cold, incl. download) |
|---|---|---|---|---|---|
| `intfloat/multilingual-e5-small` (prefix `query: `) | 384 | 512 | 36.3 s | 14 titles/s | 234 s |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | 128 | 33.2 s | 15 titles/s | 154 s |

The decisive difference is not speed — it is the **shape of the similarity distribution**:

| model | background p50 | background p99 | background p99.9 | gold pairs p10 | gold pairs p50 |
|---|---|---|---|---|---|
| multilingual-e5-small | 0.759 | 0.854 | 0.916 | 0.809 | 0.864 |
| paraphrase-multilingual-MiniLM-L12-v2 | 0.076 | 0.559 | 0.767 | 0.510 | 0.660 |

e5-small squeezes every pair in the corpus into the band **0.76–0.92**. This is the well-known anisotropy
of retrieval-tuned encoders: they are trained to *rank*, and ranking is invariant to the absolute scale, so
nothing forces unrelated texts apart. MiniLM — distilled specifically for *semantic similarity* — uses the
range **0.08–0.77**, roughly a ten-fold wider dynamic range.

That matters enormously, because a clustering threshold is an *absolute* quantity.

### A.4 Algorithm results, and the chaining cliff

**multilingual-e5-small**, connected components on the similarity graph:

| threshold | rec | recXL | clusters | largest |
|---|---|---|---|---|
| 0.90 | 0.43 | 0.08 | 37 | 26 |
| 0.88 | 0.65 | 0.45 | 38 | 40 |
| 0.86 | 0.93 | 0.89 | 37 | 109 |
| **0.84** | 1.00 | 1.00 | 9 | **366** |
| 0.80 | 1.00 | 1.00 | 1 | **500** |

Between 0.86 and 0.84 — **two hundredths** — the corpus collapses from 37 clusters into a single
366-article blob. This is textbook single-link chaining, and it makes connected-components on e5 embeddings
unusable: there is no threshold a person could defend, because the answer changes completely within the
noise of the choice.

Average-linkage agglomerative on the same embeddings is better but still knife-edge: `distance_threshold`
0.20 gives 65 clusters (rec 0.90, recXL 0.84); 0.25 gives 5 clusters, largest 389. A 0.05-wide window.

**paraphrase-multilingual-MiniLM-L12-v2**, connected components:

| threshold | rec | recXL | clusters | largest |
|---|---|---|---|---|
| 0.80 | 0.23 | 0.10 | 31 | 10 |
| 0.75 | 0.56 | 0.54 | 36 | 24 |
| 0.70 | 0.84 | 0.78 | 34 | 49 |
| **0.65** | **1.00** | **1.00** | 33 | 64 |
| 0.60 | 1.00 | 1.00 | 33 | 138 |
| 0.55 | 1.00 | 1.00 | 25 | 227 |

At **0.65** every one of the 162 gold pairs — including all 98 cross-lingual ones — lands in the right
cluster, and **no two distinct gold events are merged with each other**. The degradation on either side is
gradual over ~0.10, not a cliff. This is a defensible operating point in a way that nothing on e5 was.

Two other algorithms, for completeness:

- **HDBSCAN** (`sklearn.cluster.HDBSCAN`, `cluster_selection_method="leaf"`, euclidean on unit-norm
  vectors) was the weakest option on both models. On e5-small with `min_cluster_size=2` it reached
  `recXL=0.07` and dumped 232/500 articles into noise; with `min_cluster_size=3`, `recXL=0.07` and 334 in
  noise. On MiniLM, `min_cluster_size=3` gave `rec=0.48 / recXL=0.44` with 348 in noise. It systematically
  fails to bridge languages here — cross-lingual counterparts are near neighbours but they do not form a
  *density* peak, which is exactly the assumption HDBSCAN needs.
- **`sentence_transformers.util.community_detection`** behaved much better than connected components on
  e5-small (at 0.85: rec 0.70, recXL 0.60, 65 clusters, 22 cross-lingual) precisely because it is
  centroid-anchored rather than transitive, so it cannot chain. On MiniLM it was more conservative than
  connected components at the same thresholds, leaving 289–470 articles unassigned.

I also tested **mean-centering** the embeddings (subtract the corpus mean, re-normalise), the standard
cheap fix for anisotropy. On e5-small it widened the usable threshold window roughly ten-fold — the
collapse moved from a 0.02-wide band to a ~0.20-wide one — **but it destroyed cross-lingual recall**
(`recXL` fell from 0.84 to 0.07 at comparable cluster counts). The component being removed was evidently
carrying much of the cross-lingual alignment. Worth recording as a tried-and-rejected idea rather than
repeating it.

### A.5 What the clusters actually look like — and the finding that matters most

Numbers hide the important thing. Here is MiniLM at threshold 0.65: **33 clusters of size > 1, 276
singletons** (55% of the corpus clusters with nothing).

Clusters that are genuinely right, at event grain:

```
[n=6 langs=ar,en,fr srcs=6]   <- Ras Laffan gas plant explosion
   fr lemonde.fr        Qatar : l'explosion d'un complexe gazier fait 54 blessés et 18 disparus
   en nytimes.com       Explosion at Qatar Gas Plant Leaves at Least 54 Injured
   en rt.com            Massive explosion rocks Qatari gas processing hub (VIDEO)
   ...
```

Clusters that are right but at **story** grain, not event grain:

```
[n=27 langs=ar,de,en,es,fr srcs=14]  <- the whole Colombian election
[n=25 langs=ar,de,en,es,fr srcs=12]  <- everything Starmer
[n=64 langs=ar,de,en,fr    srcs=13]  <- Iran talks + Gaza + Hezbollah + Syria, all as one
```

And a clear failure mode:

```
[n=9 langs=ar srcs=1]  <- one source, one language, no shared subject
   ar aljazeera.net   Islamabad memorandum: nuclear file, Hormuz, Lebanon
   ar aljazeera.net   Hydration breaks: a tactical weapon at the 2026 World Cup
   ar aljazeera.net   Humpback whales of the Arabian Sea
   ar aljazeera.net   Whoever owns electricity owns AI: the Gulf and Africa in the data-centre race
```

That last cluster shares no subject at all. The model has grouped it by **language and register**. Note
that a **multi-source requirement** — a cluster must contain at least two distinct domains — removes it for
free, and is *not* an arbitrary filter: tensionr's thesis is about disagreement *between outlets*, so a
single-source cluster is definitionally useless to it.

**The finding that matters most is the grain.** At the threshold where cross-lingual recall is complete,
most large clusters are **stories or topics, not events**. This is not a tuning failure; it is intrinsic. A
10-word headline frequently does not contain enough information to distinguish *"Starmer is expected to
resign"* from *"Starmer has resigned"* from *"the race to replace Starmer"* — and human annotators disagree
about those too. This is also why the `contam` numbers above should not be read as error rates: my gold
events are deliberately narrow, so a perfectly sensible *story* cluster scores as ~50% "contaminated".

The honest formulation of the result:

> On this corpus, multilingual embeddings on headlines reliably group articles into **cross-lingual story
> clusters**. They group articles into **event clusters** only when the event is sharp, recent and named
> (an explosion, a death, an election result). They do not reliably separate sub-events of a running story.

For tensionr this is *less bad than it sounds*, and the reason is worth stating plainly: a story cluster
with 12–14 distinct outlets across 5 languages is a **better** substrate for measuring framing divergence
than a strict 3-article event cluster, because it has enough members for the divergence to mean anything.
What is not acceptable is calling it an "event". The map's own warning — the project's original sin was
promising more than it measured — applies directly here. If the unit is a story, the interface, the schema
and the copy must all say *story*.

### A.6 Precision, measured by hand — the number that decides the question

Recall was easy to measure; precision needed labelling. I drew a random sample of **22 cross-source
within-cluster pairs** from the multi-source clusters produced by MiniLM at threshold 0.65 (25 such
clusters, 2,548 such pairs) and judged each one myself, at two grains.

| grain | correct | precision | 95% Wilson CI |
|---|---|---|---|
| **same story** | 19 / 22 | **0.86** | [0.67, 0.95] |
| **same event** | 5 / 22 | **0.23** | [0.10, 0.43] |

Correct at both grains — a real cross-script event match:

```
cos=0.611  en/ar
  rt.com         Massive explosion rocks Qatari gas processing hub (VIDEO)
  aljazeera.net  الداخلية القطرية: انفجار بمصنع في رأس لفان نتيجة عطل فني
                 (Qatari Interior Ministry: explosion at Ras Laffan factory caused by a technical fault)
```

Correct as *story*, wrong as *event* — the single most common case:

```
cos=0.571  en/en
  nytimes.com    U.K. Live Updates: Starmer Announces Resignation; Burnham Wins Key Endorsement
  timesofindia   Why Starmer is facing fresh pressure to exit after Labour rival Burnham's victory
```

Wrong at both grains — 3 of 22:

```
cos=0.317  ar/en
  aljazeera.net  23 shots to no avail: Iran's biggest-ever line-up frustrates Belgium's attack   [FOOTBALL]
  straitstimes   Trump threatens Iran with fresh strikes as Vance leads peace talks in Switzerland
```

Two honest caveats, both of which cut against reading too much into these numbers:

1. **Single annotator, n=22.** The confidence intervals are wide and there is no inter-annotator agreement
   check. I labelled the same data I had already inspected while building the gold set, which risks bias.
2. **Pair-level precision is dominated by the largest cluster.** The 64-article Iran/Middle East cluster
   contributes 2,016 of the 2,548 cross-source pairs — **79%** of the population I sampled from. So "0.86
   story precision" largely measures whether that one blob is topically coherent (it mostly is). A
   cluster-weighted or B-cubed measure would report something different and probably worse. Whichever
   measure the prototype adopts, it must be fixed *before* looking at results.

Taken together with recall, this is the answer to the risk question the map poses:

> **Cross-lingual *story* clustering from headlines works** — recall 1.00 on the gold events, precision
> ~0.86, all five languages bridged including across scripts.
> **Cross-lingual *event* clustering from headlines does not** — precision ~0.23 at the same operating
> point. Headlines simply do not carry enough information to separate sub-events of a running story.

### A.7 Picking the threshold without looking at the answer

I tested subsample stability as a **label-free** selector: for each threshold, draw 20 pairs of 80%
subsamples, cluster each independently, and measure Adjusted Rand Index between the two labelings
restricted to the articles present in both. MiniLM embeddings, connected components:

| threshold | stability (ARI, mean ± sd) | multi-source clusters | largest | *(gold rec / recXL)* |
|---|---|---|---|---|
| 0.850 | 0.981 ± 0.027 | 21 of 23 | 4 | *0.08 / 0.02* |
| 0.800 | 0.906 ± 0.069 | 29 of 31 | 10 | *0.23 / 0.10* |
| 0.775 | 0.789 ± 0.101 | 28 of 30 | 16 | *0.40 / 0.32* |
| 0.750 | 0.840 ± 0.076 | 32 of 36 | 24 | *0.56 / 0.54* |
| 0.725 | 0.875 ± 0.069 | 29 of 37 | 38 | *0.74 / 0.71* |
| 0.700 | 0.865 ± 0.056 | 27 of 34 | 49 | *0.84 / 0.78* |
| **0.675** | **0.897 ± 0.056** | 25 of 32 | 51 | *0.96 / 0.94* |
| **0.650** | **0.892 ± 0.058** | 25 of 33 | 64 | *1.00 / 1.00* |
| 0.625 | 0.818 ± 0.079 | 27 of 32 | 94 | *1.00 / 1.00* |
| 0.600 | 0.779 ± 0.108 | 27 of 33 | 138 | *1.00 / 1.00* |
| 0.550 | 0.792 ± 0.100 | 21 of 25 | 227 | *1.00 / 1.00* |

The gold columns are shown *only* to check the answer afterwards — they played no part in the selection.

Two conclusions, one negative and one positive:

- **Global stability is not a usable criterion.** It is maximised at 0.85, where the clustering is nearly
  trivial (23 tiny clusters, recall 0.08). This is the known degenerate behaviour of stability-based
  selection: trivial solutions are perfectly reproducible. Anyone who maximises stability will pick a
  useless threshold.
- **A *local* maximum in the non-trivial region does agree with the gold set.** Stability dips at 0.775,
  recovers to a local peak at **0.675–0.65**, and falls away below 0.625 as chaining sets in. That peak is
  exactly where gold recall reaches 1.00. **[honest caveat]** the differences (0.897 vs 0.865 vs 0.892) are
  smaller than one standard deviation (~0.056) over 20 resamples, so this agreement is suggestive, not
  established.

A blunter criterion turned out to be more discriminating, and I would use it as the primary rule:
**percolation**. Track the largest cluster as a fraction of the corpus while lowering the threshold. It
grows slowly (4 → 10 → 24 → 38 → 49 → 64 articles) and then explodes (94 → 138 → 227). Rule: *take the
lowest threshold at which the largest cluster stays under ~15% of the corpus.* On this data that gives
0.65 — the same answer, obtained without a single label, and it directly targets the failure mode
(chaining) rather than a proxy for it.

Both procedures should be re-run whenever the model, the source list or the corpus size changes. A
threshold is a property of a *configuration*, not a constant.

---

## 1. Does GDELT already give us the clusters?

**Yes — largely.** The detailed survey of every GDELT surface (all DOC 2.0 `mode` values, GKG 2.0, Events,
Mentions, `GlobalEventID` semantics, Web NGrams, the dead Entity Graph and Frontpage Graph) is recorded as a
comment on [tensionr#2](https://github.com/exdsgift/tensionr/issues/2) and is not repeated here. This
section states the conclusion, the two caveats that cost us work, and my own independent verification.

### 1.1 The short version

| surface | verdict |
|---|---|
| **GSG similarity edges** — `data.gdeltproject.org/gdeltv3/gsg/` | **USABLE, and it is the answer.** Precomputed article-pair similarity edges with `simScore`, and inline `fromTitle`/`fromLang`/`toTitle`/`toLang` — no join needed. ~22 MB/day. 37% of edges are cross-language. |
| **GSG document embeddings** — `gdeltv3/gsg_docembed/` | **USABLE as the complement.** 512-float Universal Sentence Encoder v4 vectors, one per article. ~7.5 MB per 15-minute slot. |
| **DOC 2.0 API** (`mode=ArtList` etc.) | **Discovery only.** 8 fields, no grouping in any mode, hard 250-record cap, severe throttling. |
| **GKG 2.0 CSVs** | **USABLE for enrichment.** Everything the DOC API withholds — themes, locations, tone, names — joinable by URL via `V2DOCUMENTIDENTIFIER`. |
| **Events / `GlobalEventID` / Mentions** | **Not a substitute.** CAMEO groups actor-action tuples, not stories, and does not bridge languages. |
| **Article body text** | **Never available**, by design, from any GDELT surface. |
| **Global Entity Graph**, **Global Frontpage Graph** | **DEAD.** The Frontpage Graph returns HTTP 200 with a 45-byte empty gzip — a silent failure. |

The single most important consequence: **the ticket's framing "the corpus has only the titles" is a
self-imposed limitation, not an external one.** GDELT will hand us far richer metadata and a far better
corpus than 18 randomly-sampled RSS feeds.

### 1.2 My independent verification of `gsg_docembed`

The posted findings are marked as not yet human-verified, and the recommendation below leans on them, so I
spot-checked the load-bearing claims myself. **[measured]** 2026-08-02, slot `20260802130000`:

```
$ curl -sI http://data.gdeltproject.org/gdeltv3/gsg_docembed/20260802130000.gsg.docembed.json.gz
HTTP/1.1 200 OK          # live today
$ curl -s -o gsg.json.gz ...
bytes=7539637 time=2.152 # 7.54 MB in 2.15 s
```

| property | measured |
|---|---|
| records in one 15-min slot | **2,604** |
| schema | `date`, `url`, `lang`, `title`, `model`, `docembed` — exactly as described |
| `model` | `USEv4` on 100% of records |
| embedding dimension | **512** |
| titles present | 2,599 / 2,604 |
| distinct languages | **43** |
| English share | **36.4%** (vs **68.2%** in tensionr's RSS corpus) |
| parse (gzip + JSON lines) | 1.51 s |
| normalise + full 2604² cosine matrix | 0.35 s (27.1 MB) |
| one connected-components pass | 0.10 s |

Language mix in that one slot: English 947, Spanish 241, Italian 180, Turkish 156, German 142, Indonesian
99, Arabic 95, Russian 81, Traditional Chinese 71, Greek 70, Ukrainian 56, Romanian 54, Albanian 52,
Chinese 39, Portuguese 36, French 34, Serbian 24, Korean 22, … 43 in all.

This corroborates the posted findings and adds a number that matters a great deal: **GDELT's corpus is
2,604 articles per 15 minutes across 43 languages, against tensionr's 500 articles across 5 languages
accumulated over two days.** The multilingual thinness diagnosed in §0.1 — one single source for each of
French, Spanish, German and Arabic — is not a hard constraint. It is a consequence of the current RSS list.

### 1.3 The similarity distribution is well-behaved, and percolation tames the blob

The posted caveat about the giant component is real and important, but I measured it on the **embeddings**
rather than the edge files, and the picture is more tractable there.

**[measured]** pairwise cosine over all 2,604 documents: p50 **0.237**, p99 **0.500**, p99.9 **0.658**. That
is a wide, well-spread distribution — unlike the multilingual-e5 family, which compresses everything into
0.76–0.92 (§A.3). USEv4 vectors are directly usable with an absolute threshold.

Applying the percolation rule from §A.7 (lower the threshold until the largest cluster exceeds ~15% of the
corpus, then back off):

| threshold | clusters >1 | multi-source | ≥2 languages | ≥3 languages | largest | % of corpus |
|---|---|---|---|---|---|---|
| 0.85 | 155 | 119 | 3 | 0 | 19 | 0.7% |
| 0.80 | 180 | 138 | 11 | 5 | 19 | 0.7% |
| 0.78 | 200 | 151 | 15 | 9 | 19 | 0.7% |
| 0.75 | 214 | 160 | 18 | 9 | 29 | 1.1% |
| **0.72** | **224** | **159** | **22** | **11** | **44** | **1.7%** |
| **0.70** | 234 | 161 | 25 | 8 | 94 | 3.6% |
| 0.68 | 239 | 172 | 40 | 11 | 105 | 4.0% |
| 0.65 | 227 | 167 | 46 | 12 | **419** | **16.1%** |
| 0.60 | 153 | 108 | 31 | 7 | **1,202** | **46.2%** |

The percolation transition is sharp and easy to locate: the largest cluster sits at 1.7–4.0% of the corpus
down to 0.68, then jumps to 16% at 0.65 and 46% at 0.60. **The rule picks 0.68–0.70 without using a single
label**, and at that point the giant component is 3.6–4.0% — not the 10–20% blob the edge files produce at
`simScore ≥ 0.3`.

This is a genuinely useful result: **plain connected components on `gsg_docembed`, with a
percolation-selected threshold, may be sufficient**, and cheaper than the weighted community detection the
posted findings call for on the edge files. It is worth testing both in #7 before committing to Louvain/Leiden.

### 1.4 The clusters are real

**[measured]**, connected components at 0.72, three largest multi-language clusters:

```
[n=44  langs=12  sources=34]   Ceuta migration crisis
   ENGLISH   EU Ministers Meet Tuesday on Ceuta Migrant Crisis
   ENGLISH   22 EU leaders urge tougher migration response after Ceuta crisis
   ENGLISH   72 Migrants Die in Spain's Ceuta Enclave Rush
   ...

[n=35  langs=14  sources=31]   Trump pauses planned Iran strikes
   ENGLISH   Trump says he will hold off on fresh Iran attack in hope of quick deal
   ENGLISH   Trump Pauses Planned Iran Strikes as Diplomatic Efforts Continue
   ...

[n=31  langs=7   sources=25]   Indonesian ferry fire
   ENGLISH   A blaze on an Indonesian passenger ferry leaves at least 5 dead and dozens missing
   ENGLISH   Five dead and dozens missing after fire breaks out on ferry carrying 285 people
   ...
```

These are the unit the project is built on: a single event, many outlets, many languages.

### 1.5 Three caveats to carry into #7

1. **Coverage is partial.** Per the posted findings, only ~15–20% of the articles GDELT embeds pick up any
   similarity *edge*; the rest are singletons. This is arguably the right behaviour — an event covered by one
   outlet has no divergence to measure — but it must be a **stated property of the index, not a silent
   filter**. My own measurement on the embeddings gives a comparable picture: at threshold 0.70, 234
   clusters of size > 1 cover a minority of the 2,604 documents.
2. **Syndication is a confound, and it is serious for *this* thesis.** In the ferry cluster above, the same
   wire headline (*"Blaze on Indonesian passenger ferry leaves at least five dead"*) appears **six or more
   times verbatim** from different domains. GSG even labels such edges `type: "title"` rather than `"sim"`.
   For a project whose output is *disagreement between outlets*, counting 20 reprints of one AP story as 20
   independent outlets would **systematically understate divergence**. Near-duplicate collapse before
   measuring is not optional polish — it is a correctness requirement. GSG's own `type` field gives us the
   signal for free.
3. **Embeddings are of machine-translated English.** Non-English articles are embedded from GDELT's
   machine translation, which is why cross-language cosine works at all. Translation errors therefore
   propagate into the clustering, and quality will vary by language in ways we do not control and cannot
   inspect. This is a real, unquantified uncertainty.

Two smaller ones, both worth engineering against: GSG edges never span more than 15 minutes, so linking a
story over hours requires accumulating files; and the Frontpage Graph's failure mode — **HTTP 200 with a
45-byte empty payload** — is a warning about the current pipeline, whose validation step is a `jq .` that
prints a warning and continues (§0.2 shows the same class of silent failure already costing us all GDELT
data). Any data gate must assert on **payload size and record count**, not status codes.

---

## 2. Multilingual embeddings for short text — the fallback

Section 1 makes this section secondary, but not optional. It matters in three cases:

1. **If GSG proves unusable** — coverage too thin, the giant component untameable, or the feed decaying the
   way the Frontpage Graph did.
2. **For the ~80% of articles GSG leaves with no edge.** If tensionr wants to say anything about those, it
   needs its own embeddings.
3. **To keep tensionr's own source list meaningful.** GDELT decides which outlets it monitors; if the project
   wants a curated, declared source list (and for an index about *who* is talking, it probably does), it must
   be able to embed those sources itself.

Read it as a decision already scoped: *if* we embed ourselves, this is what to use and what it costs.

### 2.1 The comparison table

Disk sizes are the actual file sizes reported by the Hugging Face API (`?blobs=true`) for each repo's main
weights. Benchmark scores are v-measure ×100 (clustering) or accuracy/F1 (bitext), taken from the official
MTEB results repository <https://github.com/embeddings-benchmark/results>. `n=` is the number of subsets an
average covers — **averages over different `n` are not comparable**, which is why some cells are empty.

| model | params | disk | dim | max seq | langs | prefix | MasakhaNEWS-S2S (headlines, n=16) | 20NG v2 | Arxiv-S2S | Tatoeba (n=112) | licence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | 117.7M | **448.8 MB** (int8 ONNX **112.9 MB**) | 384 | 512 | 100 | **`"query: "`** | 39.19 | 33.36 | 33.05 | 68.94 | MIT |
| `intfloat/multilingual-e5-base` | 278.0M | 1060.7 MB (int8 265.8 MB) | 768 | 512 | 100 | `"query: "` | 39.41 | 35.80 | 36.31 | 68.06 | MIT |
| `intfloat/multilingual-e5-large` | 559.9M | 2135.9 MB | 1024 | 512 | 100 | `"query: "` | – | – | 38.71 | – | MIT |
| `intfloat/multilingual-e5-large-instruct` | 559.9M | 1067.9 MB (fp16) | 1024 | 512 | 100 | `Instruct: …\nQuery: ` | **59.23** | 50.74 | 40.49 | **83.73** | MIT |
| `sentence-transformers/LaBSE` | 470.9M | 1796.5 MB | 768 | 256 | 109 | none | 39.16 | 24.19 | 21.98 | **81.14** | Apache-2.0 |
| `paraphrase-multilingual-MiniLM-L12-v2` | 117.7M | 448.8 MB (int8 112.9 MB) | 384 | 128 | 50 (**no `zh`**) | none | 33.82 | **40.72** | 31.56 | 56.63 | Apache-2.0 |
| `paraphrase-multilingual-mpnet-base-v2` | 278.0M | 1060.7 MB | 768 | 128 | 50 (**no `zh`**) | none | 37.73 | 45.19 | 31.69 | 62.17 | Apache-2.0 |
| `distiluse-base-multilingual-cased-v2` | 134.7M | 514.0 MB | 512 | 128 | 50 | none | *no MTEB results published* | – | – | – | Apache-2.0 |
| `BAAI/bge-m3` | ~568M | 2165.9 MB | 1024 | 8192 | 100+ | none | 40.65 | – | – | 73.65 | MIT |
| `Alibaba-NLP/gte-multilingual-base` | 305.4M | 582.5 MB (fp16) | 768 | 8192 | 70+ | none | 45.70 | 50.15 | **41.07** | 68.08 | Apache-2.0 |
| `jinaai/jina-embeddings-v3` | 572.3M | 1091.7 MB | 1024 | 8192 | 30/100 | task LoRA `separation` | 46.16 | 51.46 | – | 71.13 | **CC-BY-NC-4.0** |
| `google/embeddinggemma-300m` | 302.9M | 1155.4 MB | 768 | 2048 | 100+ | `task: clustering \| query: ` | 43.46 | 51.29 | – | 51.35 | Gemma (**gated**) |
| `Snowflake/snowflake-arctic-embed-l-v2.0` | 567.8M | 2165.9 MB | 1024 | 8192 | 74 | query-only | 42.94 | 42.41 | 34.71 | 66.85 | Apache-2.0 |
| `Qwen/Qwen3-Embedding-0.6B` | 595.8M | 1136.4 MB (bf16) | 1024 | 32768 | 100+ | optional | 53.24 | 51.73 | 46.50 | 58.05 | Apache-2.0 |
| `static-similarity-mrl-multilingual-v1` | 108.4M | 413.6 MB (int8 103.4 MB) | 1024 | ∞ | 51 | none | **30.61** | **17.90** | 19.90 | 50.20 | Apache-2.0 |
| `minishlab/potion-multilingual-128M` | 128.1M | 488.6 MB | 256 | ∞ | 101 | none | 37.16 | 25.10 | 18.43 | 32.56 | MIT |

### 2.2 LaBSE is the wrong tool, and the benchmark says so

The ticket lists LaBSE first, which is the natural instinct: it is *the* cross-lingual sentence encoder. The
measurements say do not use it here.

LaBSE is trained with a **dual-encoder translation-ranking objective with additive margin softmax** and
reports **83.7% Tatoeba accuracy across 112 languages vs 65.5% for LASER**
([Feng et al., 2020, arXiv:2007.01852](https://arxiv.org/abs/2007.01852)). That objective optimises one
thing: *is B the translation of A?* It does not optimise *are A and B about the same thing?*

The consequence shows up starkly in MTEB. LaBSE (470.9M params, 1796.5 MB) versus multilingual-e5-small
(117.7M, 448.8 MB — a quarter of the disk):

| task | LaBSE | multilingual-e5-small |
|---|---|---|
| Tatoeba — bitext mining | **81.14** | 68.94 |
| BUCC.v2 — bitext mining | **98.77** | 97.41 |
| TwentyNewsgroups.v2 — clustering | 24.19 | **33.36** |
| StackExchange.v2 — clustering | 30.23 | **50.21** |
| ArxivClusteringS2S — clustering | 21.98 | **33.05** |

Corroborated by the first-party MMTEB task-type aggregate published on the
[potion-multilingual-128M card](https://huggingface.co/minishlab/potion-multilingual-128M):
LaBSE **BitextMining 76.35 / Clustering 38.08 / STS 65.35**.

**Honest caveat**: the LaBSE paper contains *no* limitations statement admitting this. The abstract only
claims the model "still perform[s] competitively on monolingual transfer learning benchmarks." The weakness
is established by third-party measurement (MTEB), not by the authors.

Worth knowing structurally: **81.7% of LaBSE's parameters are the input embedding table** (501,153 vocab ×
768 = 384.9M of 470.9M). You pay 1.8 GB of disk for a BERT-base-sized encoder.

### 2.3 The MTEB clustering scores do not predict what we need — and my measurement shows why

This is the most important caveat in this whole section, and it reconciles the table above with my results
in §A.

MTEB's clustering protocol, read from the source, is:

```python
MiniBatchKMeans(n_clusters=len(set(labels)), batch_size=500, n_init="auto", random_state=seed)
```

scored by **v-measure**
([`clustering_evaluator.py`](https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/_evaluators/clustering_evaluator.py),
[`clustering_legacy.py`](https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/abstasks/clustering_legacy.py)).

Two things follow, and both are fatal to using these scores directly:

1. **MTEB is told the true `k`.** Our entire problem is that `k` is unknown.
2. **k-means is invariant to the absolute similarity scale.** MTEB therefore cannot detect the property that
   turned out to matter most in §A — whether a model's cosine values are *spread out enough* for a fixed
   threshold to be meaningful.

That is exactly the discrepancy I hit. On MasakhaNEWS-S2S (real news headlines, 16 languages)
multilingual-e5-small scores 39.19 and MiniLM 33.82 — e5 looks better. But on tensionr's own corpus, with
`k` unknown and a threshold, **MiniLM was decisively better** (all 162 gold pairs recovered with no event
merging at a stable threshold; e5-small collapsed from 37 clusters to a 366-article blob across two
hundredths of similarity). The reason is visible in the distributions: e5-small compresses every pair into
0.76–0.92, MiniLM spreads them over 0.08–0.77.

**Practical rule: for threshold-based clustering with unknown `k`, prefer models trained for *semantic
similarity* (the `paraphrase-*` distillation family, [Reimers & Gurevych 2020,
arXiv:2004.09813](https://arxiv.org/abs/2004.09813)) over models trained for *retrieval* (the E5/GTE/BGE
family) — or accept that you must calibrate the threshold per-model, empirically, every time.**

I want to be careful not to overclaim: this is one corpus, one day, 43 gold articles. It is enough to
justify testing both in the prototype; it is not enough to declare a general law.

### 2.4 Static / token-only models: fast, but not for this

`sentence-transformers/static-similarity-mrl-multilingual-v1` is tempting for the CPU constraint. The
[official model card](https://huggingface.co/sentence-transformers/static-similarity-mrl-multilingual-v1)
and [HF blog](https://huggingface.co/blog/static-embeddings) claim **~125× faster on CPU than
multilingual-e5-small**, retaining 92.3% of STS quality.

But that retention figure is for STS. On **clustering** it collapses: MasakhaNEWS-S2S **30.61** vs e5-small
39.19; 20NG **17.90** vs 33.36; SIB200-S2S **5.91** vs LaBSE's 18.79. Since a static model is a bag of
token vectors with no contextual mixing, this is unsurprising — word order and composition are exactly what
distinguishes *"Israel strikes Lebanon"* from *"Lebanon strikes Israel"*.

**Verdict: dead end for this task**, despite being perfect on cost. Same conclusion for
`potion-multilingual-128M`.

### 2.5 Cost of installation — the real constraint, and a 2 GB trap

Measured from the PyPI JSON API and the official PyTorch CPU index:

- **`pip install torch` on Linux pulls the CUDA stack.** The manylinux x86_64 wheel is ~502 MB and its
  Linux `requires_dist` drags in `nvidia-cudnn` (~528 MB), `nvidia-nccl` (~206 MB), `triton` (~189 MB),
  `nvidia-cusparselt` (~164 MB) and more — **well over 2 GB of downloads** on a machine with no GPU.
- **`torch==…+cpu` from `--index-url https://download.pytorch.org/whl/cpu` is ~183 MB** (cp312,
  manylinux_2_28_x86_64).

**Using the CPU index is mandatory, and saves >2 GB per run.** `requirements.txt` today has no torch at all,
so this is a new dependency and must be added correctly the first time.

Other wheels are small: `sentence-transformers` 0.6 MB, `transformers` ~11 MB, `scikit-learn` 8.7 MB,
`onnxruntime` 18.3 MB, `numpy` 15.9 MB, `scipy` 33.7 MB.

Torch-free alternatives exist but are constrained:
- `model2vec` needs only numpy/tokenizers/safetensors (~20 MB) — but §2.4 rules its models out on quality.
- `fastembed` needs onnxruntime + hub + numpy (~45 MB, no torch) — but its multilingual catalogue is thin:
  it supports `paraphrase-multilingual-MiniLM-L12-v2` and `-mpnet-base-v2` and `multilingual-e5-large`, and
  **does not support `multilingual-e5-small` or `bge-m3`**
  ([supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/)).
  Note this list *does* include the model §A found best.

`sentence-transformers` officially supports ONNX and OpenVINO backends
(`SentenceTransformer(..., backend="onnx"|"openvino")`,
[efficiency docs](https://sbert.net/docs/sentence_transformer/usage/efficiency.html)). The published CPU
speedups on short text (`stsb`, 38.9 avg chars) are modest: **1.39× ONNX, 1.29× OpenVINO** over PyTorch,
benchmarked on an i7-13700K. Pre-built int8 artifacts are already on the Hub for e5 and the paraphrase
models (112.9 MB int8 for both `multilingual-e5-small` and `paraphrase-multilingual-MiniLM-L12-v2`).

### 2.6 Throughput

**[measured]** on my hardware (i5-8257U, 4 torch threads), 500 headlines, fp32 PyTorch:
`multilingual-e5-small` **36.3 s** (14/s), `paraphrase-multilingual-MiniLM-L12-v2` **33.2 s** (15/s).

No first-party CPU throughput figures exist for LaBSE, E5, bge-m3, gte, jina-v3 or arctic on
runner-class hardware; I did not find any and will not invent them. **[estimate]**, extrapolating from
non-embedding parameter counts (a headline is ~30 subword tokens), a 4-vCPU public runner should be
*faster* than my laptop; the ~35 s figure is a safe upper bound for the small models. `multilingual-e5-large`,
`bge-m3` and `arctic-l-v2.0` (~303M non-embedding params) are roughly 14× the compute of e5-small and are
the ones at genuine risk of not fitting a tight budget.

### 2.7 Traps worth knowing before choosing

- `paraphrase-multilingual-MiniLM-L12-v2` and `-mpnet-base-v2` list **50 languages and Chinese is not among
  them**. Today's corpus (en/fr/es/de/ar) is fully covered, but the source list contains SCMP, China Daily
  and Japan Times — currently their *English* editions. **If native Chinese or Japanese sources are ever
  added, MiniLM stops being viable** and the model choice must be revisited. This is a real coupling
  between the source-list decision and the model decision.
- `jina-embeddings-v3` is **CC-BY-NC-4.0** — non-commercial only.
- `google/embeddinggemma-300m` is **gated** (manual license acceptance + an `HF_TOKEN` secret in the Action).
- `gte-multilingual-base` and `jina-embeddings-v3` require **`trust_remote_code=True`** — executing
  arbitrary code from the Hub inside CI.
- E5 requires a prefix even for clustering. Verbatim from the
  [model card](https://huggingface.co/intfloat/multilingual-e5-small): *"Use 'query: ' prefix if you want to
  use embeddings as features, such as linear probing classification, **clustering**."*

---

## 3. Clustering with an unknown number of clusters

The setting is specific and it rules things out: *k* is unknown and varies daily; clusters are small (2–40);
most items are singletons; and the vectors are high-dimensional and unit-normalised. What follows combines
the algorithms' own documentation with what I measured in §A.4 and §1.3.

### 3.1 The four candidates, ranked by how they actually behaved

**1. Connected components on a thresholded similarity graph** — equivalent to single-linkage cut at the
threshold. `scipy.sparse.csgraph.connected_components`
([docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.connected_components.html)).

*Pro*: trivial, O(E) after the similarity matrix, no parameters but the threshold, and it naturally leaves
singletons as singletons. **[measured]** 0.08–0.10 s on 500 and on 2,604 documents.

*Con*: **transitive, therefore prone to chaining.** This is its defining failure and I measured it twice. On
multilingual-e5-small the corpus collapsed from 37 clusters to a single 366-article blob between thresholds
0.86 and 0.84 — two hundredths (§A.4). On `gsg_docembed` the giant component went 4.0% → 16.1% → 46.2%
between 0.68, 0.65 and 0.60 (§1.3).

*Verdict*: **viable, but only with a threshold chosen by an explicit anti-chaining criterion** (§3.2) and a
guard-rail that fails the run if the giant component is too large. On well-spread embeddings (MiniLM,
USEv4) it was the best-performing option I tested. On compressed ones (e5) it is unusable.

**2. Agglomerative clustering with a distance threshold** —
`sklearn.cluster.AgglomerativeClustering(n_clusters=None, distance_threshold=…, metric="cosine",
linkage="average")`
([docs](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html)).

Note from the documentation: `linkage="ward"` **requires** `metric="euclidean"`, so for cosine you must use
`average`, `complete` or `single`. `average` is the sensible default — `single` reproduces the chaining of
connected components, `complete` fragments.

*Pro*: averaging over cluster members resists chaining better than single-link. **[measured]** on e5-small,
`dt=0.20` gave the best e5 result of any algorithm (rec 0.90, recXL 0.84, 65 clusters).

*Con*: O(n²) memory and O(n³) worst-case time in the general case; and it still had a knife-edge threshold
on e5 (65 clusters at `dt=0.20`, 5 clusters at `dt=0.25`). It also assigns *every* point to a cluster, so
singletons have to be recovered by post-filtering on size.

*Verdict*: **the best fallback**, and the right choice if the embeddings are compressed.

**3. `sentence_transformers.util.community_detection`**
([docs](https://sbert.net/docs/package_reference/util.html)) — a fast centroid-anchored algorithm: for each
point, take everyone above `threshold`; keep groups of at least `min_community_size`; sort by size and
greedily emit non-overlapping communities.

*Pro*: **not transitive, so it cannot chain.** That is exactly the right property here. **[measured]** on
e5-small at 0.85 it produced 65 clusters with 22 cross-lingual — where connected components at any threshold
gave either 37 clusters or one blob.

*Con*: it is greedy and order-dependent, and it is conservative — it left 183–470 of 500 articles unassigned
depending on threshold. Its behaviour is not described in a paper, only in code.

*Verdict*: **the best insurance against chaining**, and cheap to try. Genuinely useful on anisotropic
embeddings.

**4. HDBSCAN** — `sklearn.cluster.HDBSCAN` (added in scikit-learn 1.3;
[docs](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html)), from Campello,
Moulavi & Sander, *Density-Based Clustering Based on Hierarchical Density Estimates*, PAKDD 2013
([doi:10.1007/978-3-642-37456-2_14](https://doi.org/10.1007/978-3-642-37456-2_14)); reference implementation
McInnes, Healy & Astels, JOSS 2017 ([doi:10.21105/joss.00205](https://doi.org/10.21105/joss.00205)).

`min_cluster_size` does go down to 2, so it *can* in principle find pairs, and
`cluster_selection_method="leaf"` biases it towards small fine-grained clusters instead of the default
`"eom"`.

*Con*: **it was the worst option in both of my experiments, and the reason is structural.** HDBSCAN needs
clusters to be *density* peaks. Cross-lingual counterparts of the same story are near neighbours but there
are only a handful of them, so they do not form a density peak against a background of 500 unrelated
headlines. **[measured]** on e5-small, `min_cluster_size=2, leaf`: cross-lingual recall **0.07** with 232 of
500 articles in noise; `min_cluster_size=3`: recXL **0.07**, 334 in noise. On MiniLM, `min_cluster_size=3`
reached rec 0.48 / recXL 0.44 but with 348 in noise.

*Verdict*: **do not use for this.** The usual remedy — UMAP first — adds a stochastic, parameter-heavy step
whose output nobody can inspect, in exchange for fixing an assumption that is wrong here anyway.

**Weighted community detection** — Louvain (Blondel, Guillaume, Lambiotte & Lefebvre, *Fast unfolding of
communities in large networks*, J. Stat. Mech. 2008, [arXiv:0803.0476](https://arxiv.org/abs/0803.0476)) and
Leiden (Traag, Waltman & van Eck, *From Louvain to Leiden: guaranteeing well-connected communities*,
Scientific Reports 9:5233, 2019, [arXiv:1810.08473](https://arxiv.org/abs/1810.08473)) — is what the posted
GDELT findings recommend for the edge files, because it uses `simScore` as a weight rather than throwing it
away at a threshold. Leiden's contribution is directly relevant: it exists **because Louvain can produce
internally disconnected communities**, which is a close cousin of the chaining problem.

Two honest caveats. First, modularity maximisation has a documented **resolution limit** (Fortunato &
Barthélemy, PNAS 2007, [arXiv:physics/0607100](https://arxiv.org/abs/physics/0607100)): it tends to merge
small communities below a size that depends on total graph size — and our clusters are small by nature.
`resolution` / CPM then becomes another parameter to justify, which is the problem we were trying to escape.
Second, `python-louvain`, `igraph` and `leidenalg` are new dependencies. Given §1.3, **I would test
percolation-thresholded connected components first and only reach for Leiden if the giant component resists.**

I did **not** review incremental/streaming clustering, which is a real gap: the pipeline runs hourly on a
rolling window, so clusters should ideally persist and grow rather than being recomputed from scratch. That
is a #7 concern (stable story IDs across runs) and it is not answered here.

### 3.2 Choosing the threshold without cheating

The honest starting point: **any threshold picked by eyeballing the output is tuning on the test set.** If
you look at the clusters, adjust, and look again, you have fitted the threshold to the data you are judging
it on, and the quality number you report afterwards is not a measurement. The only defences are to fix the
procedure in advance, and to keep a held-out set the procedure never sees.

Four methods, in the order I would trust them here.

**1. Percolation / giant-component control — recommended.** Lower the threshold while tracking the largest
cluster as a fraction of the corpus; stop when it exceeds a pre-declared ceiling. **[measured]** it works on
both corpora and gives a sharp answer: 0.65 on tensionr's MiniLM embeddings, 0.68–0.70 on `gsg_docembed`
(§1.3). It uses **no labels**, costs one connected-components pass per candidate (0.1 s), and it targets the
actual failure mode rather than a proxy for it. Its one arbitrary quantity is the ceiling — but a ceiling
like "no story may exceed 15% of a day's news" is a *statement about the domain* that can be argued about in
the open, which is exactly what an arbitrary threshold is not.

**2. Subsample stability — useful only as a cross-check, and dangerous alone.** Cluster repeated subsamples
and measure agreement (Ben-Hur, Elisseeff & Guyon, *A stability based method for discovering structure in
clustered data*, PSB 2002; Monti et al., *Consensus Clustering*, Machine Learning 52:91–118, 2003). I
**[measured]** it in §A.7 with 20 pairs of 80% subsamples scored by Adjusted Rand Index, and it exhibited
the known pathology plainly: stability is **maximised at the most trivial clustering** (0.981 at threshold
0.85, where recall is 0.08). Anyone who maximises stability picks a useless threshold. A *local* maximum in
the non-trivial region did agree with the gold optimum (0.675–0.65), but the differences were smaller than
one standard deviation, so it is suggestive at best.

**3. The knee of the sorted-similarity curve** (Satopää, Albrecht, Irwin & Raghavan, *Finding a "Kneedle" in
a Haystack*, ICDCS workshops 2011; [`kneed`](https://github.com/arvkevi/kneed)). **[measured]** this failed
outright on my data — the sorted top-similarity curve is dominated by near-duplicates, so the detected knee
sat at 1.000, which is no threshold at all. Not recommended.

**4. A hand-labelled dev set, with a held-out test set.** The only method that measures what we actually
care about. Label a sample, tune on the dev half, report on the test half **once**. Expensive but honest, and
§4 sets out how much labelling is enough.

**What I would do**: fix the ceiling and the percolation rule in advance, in code; recompute the threshold
**every run** rather than hard-coding it, because it is a property of a configuration and a corpus, not a
constant; and keep a small held-out labelled set to *report* quality, never to choose the threshold.

---

## 4. How cluster quality gets evaluated

### 4.1 The metric: B-cubed, and why not the alternatives

The standard in event/entity coreference clustering is **B-cubed** (Bagga & Baldwin, *Entity-based
cross-document coreferencing using the vector space model*, COLING-ACL 1998,
[ACL Anthology C98-1012](https://aclanthology.org/C98-1012/)). It computes precision and recall
**per item** — for each article, what fraction of its predicted cluster is genuinely in its true cluster
(precision) and what fraction of its true cluster made it into its predicted cluster (recall) — then averages
over items.

The reason to prefer it is not tradition. Amigó, Gonzalo, Artiles & Verdejo (*A comparison of extrinsic
clustering evaluation metrics based on formal constraints*, Information Retrieval 12:461–486, 2009,
[doi:10.1007/s10791-008-9066-8](https://doi.org/10.1007/s10791-008-9066-8)) show that B-cubed is the only
one of the common metrics satisfying all four of their formal constraints — in particular **cluster
homogeneity** and the **rag bag** constraint, and critically it does not reward putting everything in one
cluster. That property is exactly what my experiments needed: several of my configurations achieved recall
1.00 by merging the entire corpus, and any metric that cannot see through that is useless here.

For the others, briefly:

- **Pairwise precision/recall/F1** — intuitive, and what I used in §A.6. Its flaw is that it is dominated by
  large clusters: a cluster of *n* contributes *n(n−1)/2* pairs, so my 64-article blob supplied **79%** of
  all the pairs I sampled from. Report it, but never alone.
- **V-measure / homogeneity / completeness** (Rosenberg & Hirschberg, EMNLP-CoNLL 2007,
  [ACL Anthology D07-1043](https://aclanthology.org/D07-1043/)) — `sklearn.metrics.v_measure_score`. This is
  what MTEB uses. It requires a full partition of a labelled set, which we will not have.
- **ARI / AMI** — `sklearn.metrics.adjusted_rand_score`, `adjusted_mutual_info_score`. Chance-corrected and
  good for comparing two *clusterings* to each other; that is why I used ARI for the stability test in §A.7.
  Not the right primary metric against a gold standard with unlabelled remainder.
- **Purity** — trivially gamed by making clusters small. Do not report it alone.

**Practical note: B-cubed is not in scikit-learn.** V-measure, ARI and AMI are; B-cubed has to be written
(it is about fifteen lines). Budget for that in #7.

### 4.2 Benchmarks to borrow the protocol from

I could not review these as thoroughly as the rest of the document — this is the thinnest section and should
be treated as leads rather than conclusions.

- **Miranda et al., *Multilingual Clustering of Streaming News*, EMNLP 2018**
  ([arXiv:1809.00540](https://arxiv.org/abs/1809.00540)) — the closest published match to tensionr's problem:
  monolingual clusters merged into cross-lingual ones over a *stream*, evaluated with B-cubed. If any one
  paper should be read before #7, it is this one.
- **SemEval-2022 Task 8: Multilingual News Article Similarity**
  ([ACL Anthology 2022.semeval-1.155](https://aclanthology.org/2022.semeval-1.155/)) — pairs of news
  articles in multiple languages, annotated for similarity on several dimensions with *geography, entities
  and time* separated from *style and tone*. The dimension separation is directly useful to this project,
  because tensionr's thesis needs precisely that distinction: articles that agree on **what happened** and
  differ on **how it is told**. That is the sharpest conceptual borrow available.
- **MTEB clustering tasks** — usable for *model screening only*, with the caveat established in §2.3: MTEB
  gives k-means the true *k* and scores v-measure, so it cannot detect whether a model's similarity scale
  supports a threshold. It also labels **topics**, not events.

### 4.3 A protocol proportionate to this project

Nobody is going to hand-label thousands of headlines. What follows is what I think is genuinely defensible at
this scale, and it is roughly what I did in §A:

1. **Sample two disjoint sets of days** — one dev, one test. Tune on dev; run on test once, at the end.
2. **Label at both grains, and declare which one the product claims.** My experience in §A.5–A.6 is that
   this is the single most important decision: the same clustering scored precision **0.86** as *stories* and
   **0.23** as *events*. Every number is meaningless until the unit is fixed. Write the annotation guideline
   down before labelling — one paragraph, with two borderline examples resolved.
3. **Two ways to sample, because they answer different questions.** Sample *clusters* and judge whether each
   is coherent (this catches the "quote of the day" and single-source junk clusters of §A.5). Sample *pairs*
   from within clusters for precision (§A.6). Around 30–50 of each is enough for a usable estimate.
4. **Recall needs a seeded gold set**, since you cannot find missed links by sampling clusters. Pick 5–10
   events by hand from multilingual keyword probes — as in §A.1 — and check whether the clustering recovers
   them. Report cross-lingual recall separately: it is the number that justifies the whole approach, and it
   is the first thing to collapse (in my runs recXL was consistently well below overall recall).
5. **Report intervals, not point estimates.** With n ≈ 22 my precision estimate had a 95% Wilson interval of
   [0.67, 0.95] — wide enough that "0.86" alone would have been misleading. Use Wilson for proportions,
   bootstrap for B-cubed.
6. **Report coverage as a first-class number**: how many articles are in any multi-source cluster. In §1.3
   this was a minority of the corpus, and in the RSS corpus 276 of 500 headlines were singletons. An index
   computed over 25 stories should say so.
7. **Have a second person label ~20 items and report agreement.** My own labels are single-annotator on data
   I had already inspected — a real bias I could not remove. If the project claims a precision figure
   publicly, it needs at least a sanity check from someone else.

---

## 5. Recommendation

### 5.1 What to try first

**Build the prototype on GDELT's `gsg_docembed`, cluster it with percolation-thresholded connected
components, and require every cluster to span at least two distinct sources after near-duplicate collapse.**

The reasoning, in order of weight:

1. **It removes the largest cost and the largest risk at once.** No 450 MB model download, no 183 MB torch
   wheel, no 23-second import — GDELT has already done the encoding. §1.2: 7.5 MB and ~4 seconds gets 2,604
   articles across 43 languages, already embedded.
2. **It fixes the corpus, which is the real problem.** §0.1 found the current corpus has five languages with
   exactly *one source each* for four of them. No clustering algorithm can extract "disagreement between
   outlets" from one outlet per language. GDELT gives 43 languages and 36% English instead of 68%.
3. **The vectors are well-behaved for thresholding.** §1.3: cosine p50 0.237 / p99 0.500, and a sharp,
   locatable percolation transition. This is the property the multilingual-e5 family lacked (§A.3), and it is
   what makes the cheap algorithm sufficient.
4. **The clusters are visibly right** (§1.4) and the cost is negligible (§5.4).

Start with the **embeddings**, not the edge files, despite the posted findings recommending edges. Two
reasons: the edge files cap at a 15-minute horizon, while a story unfolds over hours; and §1.3 suggests the
giant-component problem is more tractable on the embeddings with a percolation threshold than on the edges at
`simScore ≥ 0.3`. Keep the edge files as the cheap cross-check — they are ~22 MB/day against ~660 MB/day, and
their `type: "sim"` vs `type: "title"` distinction is the ready-made syndication detector §1.5 says we need.

**Do not** start by adding `sentence-transformers` to `requirements.txt`. §2 is the fallback, and the
prototype should establish whether it is needed before paying for it.

### 5.2 If we do have to embed ourselves

Then, on the evidence in §2 and §A: **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** — 448.8
MB fp32 (112.9 MB int8 ONNX), 384 dimensions, **[measured]** 15 titles/s on a slow laptop, and the only model
I tested whose similarity scale supported a stable threshold (§A.4: all 162 gold pairs recovered with no
event merging at 0.65, degrading gracefully over ~0.10 rather than falling off a cliff).

Explicitly rejected, with reasons:

- **LaBSE** — 1.8 GB for a model that is *worse at clustering* than a 449 MB one (§2.2: 24.19 vs 33.36 on
  TwentyNewsgroups, 21.98 vs 33.05 on ArxivClusteringS2S). It is optimised for bitext mining, which is a
  different task. This directly contradicts the ticket's instinct to reach for LaBSE first.
- **multilingual-e5 (small and base)** — both **[measured]** unusable with a fixed threshold: anisotropic,
  everything within 0.76–0.92, and a 366-article blob appearing across two hundredths of similarity.
  Retrieval-tuned, not similarity-tuned.
- **Static / Model2Vec models** — ~125× faster and rightly tempting for a CPU budget, but §2.4: clustering
  quality collapses (30.61 vs 39.19 on MasakhaNEWS-S2S, 17.90 vs 33.36 on 20NG). A bag of token vectors
  cannot tell *"Israel strikes Lebanon"* from *"Lebanon strikes Israel"*.

One coupling to keep visible: MiniLM covers 50 languages and **Chinese is not among them**. Fine for today's
corpus; a blocker the moment a native Chinese or Japanese source is added.

### 5.3 Implementation sketch

Note this deliberately has **no torch dependency** — `numpy` and `scipy` are already in `requirements.txt`
via `pandas`/`scikit-learn`.

```python
# src/stories.py  — group GDELT-embedded articles into cross-lingual story clusters.
from __future__ import annotations

import collections
import gzip
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import requests
from scipy.sparse import csr_matrix, triu
from scipy.sparse.csgraph import connected_components

GSG_DOCEMBED = "http://data.gdeltproject.org/gdeltv3/gsg_docembed/{ts}.gsg.docembed.json.gz"
WINDOW_HOURS = 6            # accumulate 24 slots
MAX_GIANT_FRACTION = 0.15   # declared ceiling: no story is >15% of the window
MIN_SOURCES = 2             # a single-source cluster shows no disagreement
CANDIDATE_THRESHOLDS = np.arange(0.85, 0.59, -0.01)


@dataclass(frozen=True)
class Story:
    members: tuple[int, ...]
    sources: tuple[str, ...]
    languages: tuple[str, ...]
    threshold: float


def slots(window_hours: int = WINDOW_HOURS, lag_minutes: int = 30) -> list[str]:
    """15-minute slot timestamps, oldest first, allowing for publication lag."""
    now = datetime.now(timezone.utc) - timedelta(minutes=lag_minutes)
    now = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    return [(now - timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S")
            for i in range(window_hours * 4)][::-1]


def fetch(ts: str, timeout: int = 30) -> list[dict]:
    resp = requests.get(GSG_DOCEMBED.format(ts=ts), timeout=timeout)
    if resp.status_code != 200 or len(resp.content) < 100_000:
        # Guard against the Frontpage-Graph failure mode: 200 OK, empty payload.
        raise LookupError(f"gsg_docembed {ts}: status={resp.status_code} bytes={len(resp.content)}")
    out = []
    for line in gzip.decompress(resp.content).decode("utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def pick_threshold(sim: np.ndarray) -> float:
    """Lowest threshold whose largest component stays under the declared ceiling."""
    ceiling = MAX_GIANT_FRACTION * sim.shape[0]
    chosen = float(CANDIDATE_THRESHOLDS[0])
    for t in CANDIDATE_THRESHOLDS:
        _, labels = connected_components(
            csr_matrix(triu(csr_matrix(sim >= t), k=1)), directed=False)
        if max(collections.Counter(labels).values()) > ceiling:
            break
        chosen = float(t)
    return chosen


def group(records: list[dict]) -> list[Story]:
    emb = np.asarray([r["docembed"] for r in records], dtype=np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    sim = emb @ emb.T

    threshold = pick_threshold(sim)
    _, labels = connected_components(
        csr_matrix(triu(csr_matrix(sim >= threshold), k=1)), directed=False)

    domains = [r["url"].split("/")[2] for r in records]
    buckets: dict[int, list[int]] = collections.defaultdict(list)
    for i, lab in enumerate(labels):
        buckets[lab].append(i)

    stories = []
    for members in buckets.values():
        # Collapse syndication before counting sources, or 20 reprints of one
        # wire story look like 20 independent outlets and divergence reads low.
        by_title = {records[i]["title"].strip().lower(): i for i in members}
        deduped = sorted(by_title.values())
        sources = {domains[i] for i in deduped}
        if len(deduped) < 2 or len(sources) < MIN_SOURCES:
            continue
        stories.append(Story(
            members=tuple(deduped),
            sources=tuple(sorted(sources)),
            languages=tuple(sorted({records[i]["lang"] for i in deduped})),
            threshold=threshold,
        ))
    return sorted(stories, key=lambda s: len(s.members), reverse=True)
```

Starting parameters, all of them **[measured]** or explicitly declared rather than guessed:

| parameter | value | where it comes from |
|---|---|---|
| threshold | computed per run, ~0.68–0.70 | §1.3 percolation on real data |
| `MAX_GIANT_FRACTION` | 0.15 | declared domain assumption, argue in the open |
| `MIN_SOURCES` | 2 | the thesis: no disagreement within one outlet |
| `WINDOW_HOURS` | 6 | GSG edges span ≤15 min, so a window is required; 6 h is a starting guess and **should be swept** |
| lag | 30 min | posted findings measured ~21 min for docembed |

The one parameter I have no evidence for is `WINDOW_HOURS`. It trades recall (a story unfolds over hours)
against the giant component (more articles, more chances to chain). It needs the same percolation treatment
as the threshold.

### 5.4 Cost against the free-Action budget

Budget: **4 vCPU / 16 GB** (public repo), job limit 6 h, self-imposed `timeout 600` (§0.4).

**GSG route** — extrapolated from §1.2 measurements, one 15-minute slot measured at 7.54 MB / 2.15 s
download, 1.51 s parse, 0.35 s cosine, 0.10 s clustering:

| step | 6 h window (24 slots, ~30k articles) |
|---|---|
| download | ~180 MB, **~50 s** |
| parse | **~36 s** |
| cosine matrix | 30k² float32 = **3.6 GB** ← **the binding constraint** |

At 30,000 articles the dense similarity matrix does not fit comfortably in 16 GB. **This is the one real
engineering problem in the recommendation.** Three ways out, in order of preference: (a) shorten the window
to ~1–2 h (5–10k articles, 100–400 MB matrix — comfortable); (b) block by language-pair or by GKG theme
before comparing; (c) use `sklearn.neighbors.NearestNeighbors` or FAISS to build a sparse k-NN graph instead
of a dense matrix, which is the proper fix and is what the edge files effectively are. **A 1-hour window
costs roughly 8 s download + 6 s parse + a 400 MB matrix — comfortably inside 600 s.** Start there.

**Own-embedding route** — fully **[measured]** end-to-end on 500 headlines, warm cache (§A.1b):

```
import libs   23.54 s      model load    9.87 s
encode 500    37.38 s      cluster        0.08 s
TOTAL         70.88 s
```

70 s on hardware slower than the runner, plus a one-off 449 MB model download that must be cached with
`actions/cache` keyed on the model revision, plus a mandatory
`--extra-index-url https://download.pytorch.org/whl/cpu` to avoid pulling >2 GB of CUDA libraries (§2.5).

**Neither route is compute-bound.** The GSG route is memory-bound at large windows, and the own-embedding
route is dependency-bound. The `timeout 600` is not the constraint; the ticket's framing of the budget as the
main risk turned out to be wrong.

### 5.5 What I would fix in the pipeline regardless

These are cheap, they are prerequisites for the mechanism, and they are all bugs rather than design choices
(§0.1–0.3). They belong in #7 or its own ticket:

1. **Detect the language instead of hardcoding it.** Four of 18 domains are mislabelled — Spiegel's German
   is labelled English, RT's and Japan Times' English are labelled Russian and Japanese. Any per-language
   analysis is currently wrong. If the GSG route lands, `lang` comes from GDELT and this disappears.
2. **Use the RSS `published` date, not `datetime.now()`.** `seendate` is currently the fetch timestamp, which
   destroys the cheapest and most standard signal in news event detection: time proximity.
3. **Stop randomising the feed list.** `random.sample(ALL_FEEDS, 15)` of 23 feeds, 10 entries each, actively
   discards the cross-source redundancy the mechanism depends on.
4. **Make the GDELT failure loud.** A non-200 currently yields zero articles silently (§0.2) — which is why
   `data/news.json` contains no GDELT data at all today. Assert on record counts, and remember the Frontpage
   Graph's 200-OK-with-empty-payload (§1.5).
5. **Add more than one source per non-English language**, or stop claiming cross-source disagreement in
   those languages.

### 5.6 The verdict, stated plainly

**The mechanism is viable. The word "event" is not.**

Cross-lingual grouping of headlines works, on tensionr's own data and better still on GDELT's: recall 1.00 on
a hand-labelled gold set, hand-judged precision ~0.86 at story grain, five languages bridged including
across scripts, and real multilingual clusters out of GDELT at 43 languages for 7.5 MB. The map's structural
risk — *"if the clustering does not hold, the thesis collapses"* — does not materialise.

What does not work is **event**-grain clustering: precision ~0.23 at the same operating point, with a 95%
interval of [0.10, 0.43]. A 10-word headline usually cannot separate *"Starmer is expected to resign"* from
*"Starmer has resigned"* from *"the race to replace Starmer"*, and neither can human annotators without a
guideline. That is a property of the input, not a tuning failure, and no amount of model shopping fixes it.

The honest version of the thesis is therefore: **tensionr measures disagreement between outlets covering the
same *story*.** That is still a real, defensible, interesting measurement — and a story cluster carrying
12–14 outlets across 5 languages is a *better* substrate for a divergence index than a strict 3-article
event cluster, because it has enough members for the number to mean anything.

Two things must be true for it to stay honest, and both are decisions for other tickets: the unit must be
called a story everywhere — schema, interface, copy; and **coverage must be published as part of the index**,
because a majority of articles will always be singletons and an index computed over ~25 stories a day is a
different claim from one computed over the news.

### 5.7 What remains genuinely uncertain

- **Whether GSG stays alive.** The Global Entity Graph stopped in June 2026 and the Frontpage Graph decayed
  to an empty payload while still returning 200. GSG is live today; there is no guarantee, and depending on
  it is a real risk. §2 exists for that reason.
- **Machine-translation quality inside `gsg_docembed`.** Non-English articles are embedded from GDELT's own
  translation. Errors propagate into the clustering, quality varies by language, and we cannot inspect it.
  Unquantified.
- **Whether ~15–20% edge coverage leaves enough stories per day** to compute an index that is not noise.
  Untested, and it is a prerequisite for the whole index ticket.
- **How much syndication inflates apparent source counts**, and therefore deflates measured divergence. I saw
  6+ verbatim copies of one wire headline in a single cluster. Not quantified.
- **My precision figure.** Single annotator, n=22, on data I had already read, dominated by one large
  cluster. Directional only.
- **Whether MiniLM's advantage over e5 generalises.** One corpus, one day, 43 gold articles. Enough to test
  both in #7; not enough to state as a law.
- **Incremental clustering across runs.** Not reviewed. Stories need stable identity over hours for the
  anomaly work in the map to be possible at all.
