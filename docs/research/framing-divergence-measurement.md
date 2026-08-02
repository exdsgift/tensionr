# Measuring framing divergence between sources: state of the art

Research for [#3](https://github.com/exdsgift/tensionr/issues/3), under the map in
[#1](https://github.com/exdsgift/tensionr/issues/1). Written 2026-08-02.

**Question.** Given a group of articles about the same event from different sources and languages,
how do you measure — defensibly — how differently they frame it?

Everything below is either a primary source with a URL, or a measurement taken on this repository's
own `data/news.json` and `src/fetch_gdelt.py`. Where a claim is unsupported, that is stated.

---

## 0. Verdict first

**The signal is real and it is visible in headlines.** Two days of this project's own corpus contain
seven different descriptors for the same politician, a casualty count that varies from "54 injured
and 18 missing" to "several injured" to nothing, and one source attributing the Strait of Hormuz
closure to Trump while another attributes it to Tehran. None of that needed the article body.

**The infrastructure to find those groups works, on CPU, inside the existing budget.** Measured
below: a 117M-parameter multilingual encoder embeds the whole corpus in 33 seconds and roughly
doubles the number of multi-source clusters versus a lexical baseline, while recovering the Arabic
documents that lexical matching cannot touch at all.

**But the corpus cannot currently support the measure the project wants**, for three reasons that
are about data collection rather than modelling:

1. There is **exactly one source per non-English language**. Language and outlet are perfectly
   confounded, so every cross-lingual number is a single-outlet effect with a language label on it.
2. Each source contributes **1-3 headlines per event**. Per-source-per-event statistics estimated
   from n=1 are noise, and — worse — distributional divergence estimators are *upward biased* at
   that sample size, so they will report divergence that is not there.
3. The archive stores **daily scalars only**, so nothing can be validated retrospectively.

**The cheapest high-value change in this document is not a better model. It is a second outlet per
language and more items per feed** — a dozen lines in `ALL_FEEDS` and one changed slice — which
converts an unidentifiable measurement into an identifiable one.

**On the current pipeline:** the GoEmotions-derived `manipulation_score` should be removed, not
reweighted. Section 4 gives the argument; the short version is that in this deployment its strongest
empirical correlate is *whether the headline is written in English*, it is inversely ordered by
emotional charge because of a code defect, and the construct it estimates has κ = 0.09 human
agreement on headlines — so it cannot be validated even in principle.

**Recommended measure:** actor presence/absence over cross-lingually linked entities (M1), because
it targets the more frequent form of bias, is the most robust to the small-sample problem, and is
the only candidate whose ground truth humans agree on. Named for what it measures, which is
selection and coverage — not "framing".

---

## 1. What the corpus actually is

Measured on `data/news.json`: 500 articles, 493 unique titles, 18 domains, 2026-06-21/22.
Title length mean 12.0 words, median 11. **The title is the only text field.**

### Correction: the corpus is 5 languages, not ~9, and the language metadata is wrong

The ticket and the map both say "~9 lingue". The `language` field is a hardcoded per-domain lookup
in `rss_metadata`, and it is factually wrong for 4 of 18 domains:

| domain | declared | actual |
|---|---|---|
| www.spiegel.de | English | German |
| www.japantimes.co.jp | Japanese | English |
| www.rt.com | Russian | English |
| en.mercopress.com | Spanish | English |

Script analysis of all 500 titles: only Arabic is non-Latin. The real mix is English ~341 (68%),
Arabic 79 (16%, one feed), French 36 (one feed), Spanish 24 (one feed), German 20 (one feed).

**For every non-English language there is exactly one source.** This is the single most consequential
fact in this document. "German framing" is not separable from "Der Spiegel framing" because Spiegel
is the only German outlet. No model fixes it; adding feeds does.

### Sampling is random, and per-source volume is thin

`selected_feeds = random.sample(ALL_FEEDS, 15)` with `len(ALL_FEEDS) == 23`, so each source appears
in ~65% of hourly runs at random, and `feed.entries[:10]` caps each feed at 10 items per run. Median
22.5 unique titles per source over two days. A source × source matrix has 153 cells whose occupancy
changes hourly for reasons unrelated to the news.

### The archive cannot validate anything

`data/archive/*.json` — 32 daily files, schema `{date, gti, sitrep, top_keywords, top_domains}`.
Aggregate scalars only: no articles, no per-source data, no titles. There is nothing to backtest.

### GDELT is silently dead

`fetch_gdelt_data()` queries the DOC 2.0 API with `mode=ArtList&maxrecords=50`, but **not one of the
500 articles has `source == "gdelt"`** — all 500 are `"rss"`. Given that GDELT is the only
licensing-clean route to Arabic and Chinese coverage at scale (§3), this deserves attention.

---

## 2. Literature: framing, stance, media bias — and what survives on headlines

### 2.1 What framing detection achieves with the whole article

Entman's definition — to frame is "to select some aspects of a perceived reality and make them more
salient … so as to promote a particular problem definition, causal interpretation, moral evaluation,
and/or treatment recommendation" (Entman 1993, *Journal of Communication* 43(4):51-58,
https://doi.org/10.1111/j.1460-2466.1993.tb01304.x) — is operationalised in NLP almost entirely
through the **Media Frames Corpus** and its 15 Policy Frames Codebook dimensions (Card et al.,
ACL 2015, https://aclanthology.org/P15-2072/).

Full article, 15 frames, MFC immigration, 10-fold CV (Khanehzar et al., NAACL 2021,
https://aclanthology.org/2021.naacl-main.174/): Card et al. 2016 accuracy 56.8 → RoBERTa-S 66.4
(macro-F1 58.1) → FRISS **69.7 (macro-F1 60.5)**. Six years of modelling for 13 points, with the
whole article available.

**SemEval-2023 Task 3** (Piskorski et al., https://aclanthology.org/2023.semeval-1.317/), 14 generic
frames, document level, official micro-F1:

| language | best micro-F1 | best macro-F1 | char-5-gram SVM baseline |
|---|---|---|---|
| German | .711 | .660 | .487 |
| Polish | .673 | .638 | **.594** |
| Italian | .617 | .545 | .486 |
| English | .579 | .539 | .350 |
| Spanish (zero-shot) | .571 | .455 | .120 |
| French | .553 | .537 | .329 |
| **Russian** | **.450** | **.303** | .230 |

The best system in the world reaches macro-F1 0.303 on Russian. On Polish a character-n-gram SVM
beat 9 of 19 submitted systems including transformer ensembles; on Russian three fell below it.
Independent replication on Chinese (Zhang et al., https://arxiv.org/abs/2503.04439) reaches
F1-micro 0.719 with XLM-R, and finds **GPT-4o zero-shot at 0.508-0.603 — worse than fine-tuned
XLM-R in every language.** Cross-country transfer degrades: MFC → Brazilian Portuguese drops XLM-R
from accuracy 0.67 to 0.53 (Daffara et al., https://arxiv.org/abs/2506.16337).

Framing detection is not a capability that can simply be imported.

### 2.2 The binding constraint is label reliability

- SemEval-2023 Task 3: **Krippendorff α = 0.342**, and the organisers state it is "lower than the
  recommended threshold of 0.667".
- MFC reports **no scalar agreement figure**. Span-level unitised α is **0.08-0.23**, i.e. span
  annotations are close to independent. Card et al. defend this — "We view these disagreements not
  as a weakness, but as a source of useful information about the diversity of ways in which the same
  text can be interpreted" — good social science, a problem as a gold standard.
- BASIL span-level inter-annotator F1: **0.34 informational, 0.14 lexical**. Once both annotators
  find the same span they agree well (Cohen κ 0.84 polarity, 0.92 target). *Deciding what counts as
  bias* is unreliable; *describing it once found* is not.
- The gradient, from one group's own comparison (https://arxiv.org/abs/2112.07421): MTurk α = 0.101,
  Prolific 0.144, trained experts 0.419, with the note that "α = .667 [is] the lowest conceivable
  limit. No available dataset [reaches it]."
- Across a decade and a dozen teams, word/sentence-level bias annotation sits at
  **α ∈ [-0.05, 0.47]**. Färber et al. 2020 report α = -0.05, worse than chance.

Reported F1 around 0.80 measures agreement with one small annotator pool's majority vote on one
corpus. Any claim this project makes inherits that ceiling.

### 2.3 The replication result that matters most here

Baly et al., *We Can Detect Your Bias*, EMNLP 2020,
https://aclanthology.org/2020.emnlp-main.404/ — same test set, two splits:

| model | split | macro-F1 | accuracy |
|---|---|---|---|
| majority | – | 19.61 | 41.67 |
| BERT | random | 80.19 | 79.83 |
| BERT | **media-disjoint** | **35.53** | **36.75** |

BERT loses 44.7 macro-F1 points purely from a publisher-disjoint split, landing **below the majority
baseline**. Their confirming experiment: predicting *which of 73 outlets* published an article is
80.12% accurate. Outlet identity is trivially recoverable from text; ideology is not. Their best
configuration wins by re-injecting outlet-level Twitter-follower features, and those features
**alone, with no article text**, score 60.30 — better than any text-only model.

Every time the field has switched to a disjoint split, performance has collapsed: Baly 80.19 →
35.53; Hanselowski 0.609 → 0.40; Daffara 0.68 → 0.48; Pastorino 76.3 → 69.2.

This is the literature's version of what §4 measures directly on this repo (eta² = 0.27 for source
identity; Spiegel opens 90% of headlines with a colon, the BBC 0%). **A measure must be evaluated
with source-disjoint or within-cluster contrasts, and any source-level feature rate must be
differenced against that source's own baseline.**

### 2.4 What headlines carry

The one like-for-like comparison in the literature. Liu et al. (CoNLL 2019,
https://aclanthology.org/K19-1047/) ran headline-only BERT on MFC headlines, 15 frames, 10-fold CV:

| MFC issue | headlines | headline-only accuracy |
|---|---|---|
| Immigration | 7,231 | **52.38** |
| Tobacco | 3,959 | 67.94 |
| Same-sex marriage | 3,842 | 71.50 |
| Immigration, **top-5 frames** | 4,175 | 67.28 |
| Tobacco, top-5 frames | 2,759 | 82.32 |
| Same-sex, top-5 frames | 2,937 | 83.07 |

Against Khanehzar's full-article 69.7% on the same corpus and protocol, headline-only is 52.38%: a
**~17-point loss**. Honest caveat — the two papers used different filtering (7,231 headlines vs
5,933 labelled articles) and neither ran the ablation deliberately. The direction and magnitude are
trustworthy; the exact 17 points are not.

**The second half of the table is the more useful result.** Collapsing to the top-5 frames buys back
15 points on immigration and 12 on same-sex marriage. And GVFC's **9 issue-specific frames on
headlines alone reach 84.23% micro-accuracy** (2,990 headlines, no body text, calibration α = 0.90).

**Headlines carry enough signal for a small, well-separated, issue-tuned inventory, and not enough
for a full 15-way generic scheme.** Keep the label space small, or use no labels at all.

Reliability floors on headline judgments are worse than the accuracy figures suggest: emotion
dominant label Fleiss **κ = 0.09** (GoodNewsEveryone, https://aclanthology.org/2020.lrec-1.194/);
clickbait strength — arguably the easiest headline judgment — Fleiss **κ = 0.21**, best system F1
0.683 (https://arxiv.org/abs/1812.10847); multi-class framing on European anti-vax headlines,
intercoder reliability 0.58 rising to 0.66 after a third calibration round
(https://arxiv.org/abs/2304.14456).

And one result that bears directly on §4: Pastorino et al. (https://arxiv.org/abs/2402.11621) find
GPT-4's F1 on "is this headline framed" falls from 64.96 to 47.40 **from a prompt wording change
alone**, collapses to **F1 = 3.60 on the contested subset**, and exhibits a systematic failure mode
in which it **"conflates emotional language with framing"**. The exact confusion this project is
trying to escape is a documented failure mode of frontier models.

### 2.5 Stance detection is not applicable here

SemEval-2016 Task 6 (https://aclanthology.org/S16-1003/): **no participating system beat the
organisers' n-gram SVM baseline** (68.98 vs best team 67.82; majority 65.22). And split by whether
the text's opinion target is the queried target:

| | opinion toward target | opinion toward other |
|---|---|---|
| Task A (MITRE) | 72.49 | **44.48** |
| Task B zero-shot | 67.19 | **25.77** |

25.77 is **below the 29.72 majority baseline**. X-Stance (https://arxiv.org/abs/2003.08385, MIT,
German/French/Italian) confirms target dependence: removing the target costs 3.4 points, a *random*
target costs 20.6 (76.6 → 56.0), and replacing a natural-language question with a learned target
embedding costs 6.5. Open-topic zero-shot stance (VAST,
https://aclanthology.org/2020.emnlp-main.717/) reaches macro-F1 ≈ 0.67, α = 0.427. On the
ten-dataset robustness benchmark (https://arxiv.org/abs/2001.01565) the best model averages .6695
against human .75-.91, and a **negation attack costs 12.3 points** — with the stronger multi-dataset
model being *less* robust.

**Verdict: stance detection requires a stated target and degrades below baseline precisely when the
text is about something adjacent to it — the normal case for a 12-word headline in an unfiltered
feed.** Adopting it means first solving target selection, which is harder than the problem being
solved.

### 2.6 Cross-source divergence: the slot is genuinely open

**There is no established, replicated metric for "how far apart are outlets A and B on this
event".** The literature splits into disconnected families:

- **Hamborg's line** (NewsBird, https://doi.org/10.1109/JCDL.2017.7991561; NewsWCL50; Newsalyze,
  https://arxiv.org/abs/2110.09158) is structurally comparative but yields **no scalar divergence** —
  matrices, concept chains, clustering, evaluated by case study. It carries a direct warning:
  opposing articles on the same topic have **high** TF-IDF cosine similarity "because articles on
  the same topic share many topic-specific keywords". Naive TF-IDF or embedding contrast on
  same-event articles measures topic, not framing.
- **Econometric slant.** Gentzkow & Shapiro (Econometrica 2010, https://doi.org/10.3982/ECTA7195)
  report their own validation candidly: their index correlates **0.61** with true ideology, so
  "63 percent of the variation in slant among newspapers is likely to be noise". That is the honest
  calibration for a text-only outlet-level measure.
- **Recommender diversity has the best reusable formalism.** RADio
  (https://arxiv.org/abs/2209.13520) defines a rank-aware f-divergence with MRR weighting and
  smoothing `Q̄ = (1-α)Q + αP`, and **prefers JSD over KL because it is symmetric and bounded in
  [0,1], making scores comparable**. Its stated limitation applies here: KL/JSD over frame
  categories treats frames as independent, ignoring that some are closer than others.
- **Per-item contributions.** Lu, Henchion & Namee, LREC 2020
  (https://aclanthology.org/2020.lrec-1.832/) give the decomposition that makes a JSD explainable:
  `D_JS,i(P‖Q) = -m_i log2 m_i + ½(p_i log2 p_i + q_i log2 q_i)`. **This is what turns a cluster
  scalar into the per-token table a reader can see.** The same paper shows the size-weighted
  (Gallagher) JSD variant's rankings shift with relative corpus size and **recommends against it** —
  relevant, since outlets here publish 5 to 79 headlines each.
- **The closest published template** is Demszky et al., NAACL 2019
  (https://aclanthology.org/N19-1304/): 21 mass shootings, per-event partisanship decomposed across
  topic choice, framing and affect, with a bias-corrected estimator.
- **NeuS** (https://arxiv.org/abs/2204.04902) supplies 3,564 same-event triplets and performs its
  framing-bias analysis **on titles**, "since they are simpler to compare and are representative".
- **SemEval-2022 Task 8** (https://aclanthology.org/2022.semeval-1.155/) rates ~10,000 multilingual
  article pairs on seven dimensions, defining OVERALL as "covering the same substantive news story,
  **excluding** style, framing, and tone", with STYLE and TONE annotated separately. **It factorises
  "same event" from "different treatment" — exactly the separation needed between the clustering
  step and the divergence step**, and it does so multilingually.
- **Reuver et al.** (https://arxiv.org/abs/2309.06192) find **SBERT + agglomerative clustering
  substantially beats TF-IDF/cosine and BM25F** for story-chain clustering — independently
  confirming §5 below.
- **FrameAxis** (https://arxiv.org/abs/2002.08608) distinguishes *bias* (mean position on an antonym
  axis) from *intensity* (second moment about the corpus baseline). Two outlets can have identical
  bias and very different intensity — a genuine "what they emphasise differently" signal.

#### The technical warning that could sink a naive implementation

Gentzkow, Shapiro & Taddy (Econometrica 2019, https://doi.org/10.3982/ECTA16566) show that
**plug-in estimators of distributional divergence suffer severe finite-sample bias: with a large
vocabulary and limited tokens, two samples from the identical distribution look divergent.** Using
the naive MLE, US congressional partisanship appears no higher today than historically; correcting
the bias reverses the conclusion.

This project's exposure is extreme: **1-3 headlines of ~12 words per source per cluster** against an
open vocabulary. A naive per-source unigram JSD would report large divergence between outlets saying
the same thing, purely from sampling — and the bias is *larger for low-volume sources*, so it would
systematically rank small outlets as more divergent.

Mitigations: the permutation test (V1) as a bias control and not merely a significance test; a
leave-out or L1-penalised estimator as GST recommend; restricting to a small closed high-salience
vocabulary — which is what makes the **entity-based M1 far safer than the token-based M3**; and
reporting divergence only above a minimum document count. **This is the strongest single argument
for preferring M1**, and it is not visible from the ticket's framing of the problem.

---

## 3. Reusable resources

### 3.1 The governing constraint

**Every purpose-built media-bias and framing corpus is English-only** — BASIL, NELA-GT, BABE, MBIC,
MFC, GVFC, MBIB, NewsUnfold. For a corpus that is 32% non-English, this decides what can be borrowed
rather than built. Genuinely multilingual resources number four, each with a catch:

| resource | languages | overlap here | licence |
|---|---|---|---|
| SemEval-2023 Task 3 | EN FR DE IT PL RU ES EL KA | FR DE ES RU | **restricted** — registration, no redistribution |
| SemEval-2025 Task 10 (entity framing) | BG EN HI PT RU | RU | paper CC BY 4.0, data licence unstated |
| x-stance | DE FR IT | FR DE | **MIT** — but not news |
| GDELT GKG | 65 | all | **unrestricted + attribution** — but no bias labels |

**No labelled bias or framing dataset covers Arabic**, which is 16% of this corpus and its only
non-Latin script. Plan around it.

### 3.2 BASIL — the one dataset shaped like this exact problem

Fan et al., EMNLP 2019, https://aclanthology.org/D19-1664/ — corrected release at
https://github.com/launchnlp/BASIL.

**100 event triplets × 3 outlets = 300 articles** (Fox / NYT / HuffPost), 1,727 annotated bias
spans. `title` is a **separate field** from `bodyParagraphs`, alongside `mainEvent`, `mainEntities`,
`tripletUuid`. That is precisely a cross-source divergence schema.

It separates **lexical bias** ("word choice and syntax") from **informational bias** ("factual
content that can nevertheless be deployed to sway reader opinion") and finds **informational bias is
the more frequent of the two** — the empirical basis for prioritising the omission proxy over the
affect proxy.

English only. **No licence file** (GitHub reports `license: null` on both repos), and it
redistributes copyrighted body text verbatim. Research-by-convention, not by grant.
**Use it as the external validation set (V5), not as training data** — 100 triplets is too small to
train on and the right size to calibrate against.

### 3.3 The rest, briefly

- **NELA-GT 2018-2022** (latest is 2022; no 2023/2024). 700k-1.9M articles/year, `title` and
  `content` separate, but **labels are outlet-level only**, from a Media Bias/Fact Check aggregation
  — and the 2021/2022 releases ship *2020-vintage* MBFC labels. English. **No licence declared**
  (DataCite `rightsList` empty for all five DOIs). Critical: **body text is deliberately corrupted**
  — 7 tokens per 100 replaced with `@` in long articles, up to 5-in-20 in short ones. Fine for
  bag-of-words, fatal for span extraction. https://github.com/MELALab/nela-gt
- **nela-features** (PyPI, **MIT**, https://github.com/BenjaminDHorne/NELAFeatures) — the most
  directly reusable *code*: six feature groups (style, complexity, bias, affect, moral, event) from
  lexicons and POS counts; dependencies limited to nltk / vaderSentiment / datefinder / numpy;
  **no neural model, no GPU.** But every lexicon is English, so porting it means building parallel
  lexicons per language — a work item, not a config change.
- **BABE** (https://aclanthology.org/2021.findings-emnlp.101/) — ~3.7-4.1k sentences, expert
  annotators, α = 0.39-0.40 for bias. English. **Code is AGPL-3.0** (network copyleft — relevant if
  this ever becomes a service); **data licence unstated.** Its distant-supervision auxiliaries
  (`news_headlines_usa_biased.csv` / `_neutral.csv`) are pure headlines. Note BABE's headline
  distant-supervision gain is within noise: BERT 0.804 vs 0.789 (~1 SE, no significance test), and
  RoBERTa gains exactly 0.000.
- **MBIC** (https://zenodo.org/records/4474336) — 1,700 statements, 10 annotators each, with full
  annotator demographics; **CC BY 4.0, the cleanest licence of any expert-annotated bias set.**
  Fleiss κ = 0.21, and 149 sentences could not be labelled at all for lack of majority. Its own
  finding is worth keeping: agreement is higher *between ideologically similar annotators* — the
  label partly measures the annotator.
- **Media Frames Corpus** (https://aclanthology.org/P15-2072/) — source of the 15 dimensions.
  **Article text was never redistributed** (Lexis-Nexis copyright) and the repo is **formally
  deprecated**: its README opens "this repo has been deprecated, due to changes to the Lexis-Nexis
  interface", the pipeline is Python 2.7 + Selenium against a UI that no longer exists.
  **Taxonomy reusable; corpus effectively unobtainable.**
- **GVFC** (https://aclanthology.org/K19-1047/) — 2,990 US gun-violence **headlines**, expert
  annotated, 9 issue-specific frames, **no body text at all**. The one corpus that is natively
  headline-only, and therefore the natural place to test "can frames be recovered from headlines".
  English, **no licence stated**, distributed as a Google Drive file. Note the released corpus is
  **single-coded**; α = 0.90 was established on a 100-headline calibration set only.
- **SemEval-2023 Task 3** — 2,049 documents, 9 languages, per-language counts small (train: EN 446,
  IT 227, FR 158, PL 145, RU 143, DE 132). Licence is the blocker: usable "only in the context of
  this shared task", no redistribution. **Taxonomies are not the licensed artifact** — adopting the
  14-frame label set costs nothing; obtaining the data requires asking.
- **MBIB** (https://arxiv.org/abs/2304.13148) — meta-benchmark over 22 datasets, but
  **CC BY-NC-ND 4.0**: non-commercial *and* no-derivatives, which arguably forbids redistributing a
  filtered version. It also does **not** use publisher-disjoint splits, and its Cognitive Bias task
  scores macro-F1 0.4995 on a balanced binary problem — chance. Prefer pulling components under
  their own licences.
- **AllSides** — ⚠️ **could not be verified.** Every endpoint returned HTTP 403 to non-browser
  clients and the Internet Archive was unreachable. What is certain: a commercial entity that sells
  a ratings licence, no open licence, no public API, no free bulk download. **Assume not
  redistributable.** NELA-GT uses MBFC, not AllSides, and MBFC is the more practical source.
- **MultiClimate** — despite the name it is **English-only**; "multi" means multimodal, and
  non-English-transcript videos were explicitly filtered out. Easy to miscite.

### 3.4 GDELT, which this project already touches

GDELT's terms are the most permissive surveyed: "unlimited and unrestricted use" for academic,
commercial or governmental purposes, redistribution and mirroring explicitly allowed, conditioned
only on attribution (https://www.gdeltproject.org/about.html). The GKG covers **65 live-translated
languages** — the only resource here reaching Arabic and Chinese.

Useful GKG fields: `V1.5TONE` (including **Polarity**, emotional chargedness independent of
direction), `V2ENHANCEDTHEMES` with character offsets, `V2GCAM`, `V2.1QUOTATIONS`,
`V2ENHANCEDPERSONS/ORGANIZATIONS/LOCATIONS` with offsets, and **`V2.1TRANSLATIONINFO`, which records
each document's source language** — directly useful for the language-residualisation in M2.

Two caveats: **GKG has no headline field** (`V2EXTRASXML` is blank for news content), so titles must
be joined from the DOC 2.0 API; and **GKG carries no bias or framing labels** — it is unsupervised
signal plus a document backbone.

### 3.5 Models runnable on a free runner

**Budget baseline.** `ubuntu-latest` for a **public** repo is **4 vCPU / 16 GB RAM / 14 GB SSD**
(https://docs.github.com/en/actions/reference/runners/github-hosted-runners). RAM is not the binding
constraint — **disk and cold-start download time are**. A few thousand 12-word headlines is a
trivial compute load; a 1.9 GB model download is not. Rank candidates by megabytes, and cache the
Hugging Face directory with `actions/cache`.

#### Sentence embeddings

| model | params | fp32 on disk | dim | licence |
|---|---|---|---|---|
| paraphrase-multilingual-MiniLM-L12-v2 | 117.7M | 470.6 MB | 384 | Apache-2.0 |
| paraphrase-multilingual-mpnet-base-v2 | 278.0M | 1,112.2 MB | 768 | Apache-2.0 |
| **LaBSE** | **470.9M** | **1,883.7 MB** | 768 | Apache-2.0 |
| distiluse-base-multilingual-cased-v1/v2 | 134.7M | 538.9 MB | 512 | Apache-2.0 |
| **multilingual-e5-small** | 117.7M | 470.6 MB → **118.3 MB int8 ONNX** | 384 | **MIT** |
| multilingual-e5-base | 278.0M | 1,112.2 MB | 768 | **MIT** |

**⚠️ LaBSE is the trap, and it is the obvious-looking pick.** Reimers & Gurevych
(https://arxiv.org/abs/2004.09813) Table 2, cross-lingual STS 2017 average: XLM-R←SBERT-paraphrases
**83.7**, mUSE 81.1, **LaBSE 73.5**. But BUCC bitext mining F1 (Table 3): **LaBSE 93.5**, best.
LaBSE wins at finding *translations* and loses at judging *similarity*, and the SBERT docs say so:
"LaBSE works less well for assessing the similarity of sentence pairs that are not translations of
each other." **Articles about the same event in different languages are not translations of each
other — they are loose paraphrases.** LaBSE is wrong for this task and is also the largest and
slowest. This is the single most decision-relevant fact in the model inventory.

**Recommendation: `multilingual-e5-small`, int8 ONNX, 118 MB, MIT, all corpus languages covered.**
Note it *requires* a `"query: "` prefix on every input — the card is explicit that this is not
optional and applies to "symmetric tasks such as semantic similarity, bitext mining… [and]
clustering". If Arabic quality matters, the base model earns its 1.1 GB: en-ar STS goes 57.4 → 71.3
and Arabic Tatoeba accuracy 77.4 → 85.9.

The model measured in §5 (paraphrase-multilingual-MiniLM-L12-v2, 117.7M params, 33s for 493 titles
fp32 on a laptop) is a reasonable alternative; e5-small is the same parameter count with a
quantised build a quarter the size and a cleaner licence.

#### NER — and a correction to a common assumption

Pulled from per-model `meta.json` in https://github.com/explosion/spacy-models, not the website:

| pipeline | NER F1 | licence | size |
|---|---|---|---|
| `xx_ent_wiki_sm` (currently used) | 0.8314 | MIT | 10 MB |
| `de_core_news_sm` | 0.8210 | MIT | 13 MB |
| `fr_core_news_sm` | 0.8144 | LGPL-LR | 15 MB |
| `it_core_news_sm` | 0.8558 | **CC BY-NC-SA 3.0 (non-commercial)** | 12 MB |
| `es_core_news_sm` | 0.8897 | **GPL-3.0** | 12 MB |
| `ru_core_news_sm` | 0.9436 | MIT | 14 MB |
| `zh_core_web_sm` | **0.6842** | MIT | 46 MB |

**Three corrections.** (1) **spaCy models are not uniformly MIT** — licences are inherited from
training corpora and vary per language; `it_core_news_sm` is *non-commercial* and `es_core_news_sm`
is GPL-3.0. (2) **spaCy has no Arabic pipeline at all** — this is the direct explanation for the
empirical finding in §6.1 that no Arabic entity surfaces from 79 Arabic articles while Arabic
interrogatives do. (3) Chinese NER is the weak link at F1 0.684.

**No single NER tool covers the corpus:**

| | ar | zh | ru | pt | gap |
|---|---|---|---|---|---|
| spaCy `_sm` | ✗ | weak | ✓ | ✓ | **no Arabic** |
| Stanza (Apache-2.0) | ✓ 74.3 | ✓ 79.2 | ✓ 92.9 | ✗ | no Portuguese |
| `Babelscape/wikineural-multilingual-ner` | ✗ | ✗ | ✓ | ✓ | no Arabic/Chinese, **CC BY-NC-SA 4.0** |
| `Davlan/xlm-roberta-base-ner-hrl` | ✓ | ✓ | ✗ | ✓ | no Russian |

Combining tools is unavoidable — realistically Stanza for Arabic plus spaCy elsewhere — with
heterogeneous label sets and F1 spanning 68-94. Note WikiNEuRal's own card warns it was trained on
Wikipedia and "might not generalize well to all textual genres (e.g. news)".

#### Cross-lingual entity linking: no off-the-shelf option fits

This is M1's blocking dependency, and every ready-made option fails the budget:

- **mGENRE** (https://arxiv.org/abs/2103.12528, 106 languages): 2,469 MB of weights plus a 582 MB
  prefix trie — **≥3.05 GB**, and autoregressive generation *per mention* on CPU. Infeasible.
- **DBpedia Spotlight**: 17 languages, **no Arabic, no Chinese** — cannot meet the requirement
  regardless; the English model alone is 2 GB and needs >8 GB RAM.
- **Wikidata full JSON dump**: **~130 GiB compressed** against a 14 GB disk. Content is CC0, so
  licensing is not the obstacle — size is.

**The one workable design** is the alias table, and it works because Wikidata stores every
language's label and alias on the *same* item: `Q52412` carries "Benjamin Netanyahu", "نتنياهو" and
"内塔尼亚胡" together, at CC0. Build a filtered label/alias subset **once, offline, outside CI**,
restricted to human / country / organisation in the corpus languages; commit or cache the few
megabytes; match longest alias at runtime. `wikimapper` and `qwikidata` (both Apache-2.0) handle the
mechanics. A live `wbsearchentities` fallback can cover novel surface forms, which are few once the
table is warm.

**Entity linking must not be a per-run cost.** It is a cached lookup refreshed on its own schedule.

### 3.6 Lexicons — and why the Moral Foundations proxy should be dropped

The ticket lists Moral Foundations lexicons as a candidate proxy. The evidence says no, on three
independent grounds.

**1. They do not exist multilingually.** The eMFD (Hopp et al., *Behavior Research Methods* 53:232-246,
https://doi.org/10.3758/s13428-020-01433-0; https://github.com/medianeuroscience/emfdscore, GPL-3.0)
is the best-constructed of them, 3,270 scored words with continuous foundation probabilities — and
it is **English-only, by its own author's statement in print.** Stecker & Hopp (2025), Hopp being the
eMFD's author: "To our knowledge, no translation has yet been undertaken for the eMFD, meaning we
can only apply it to English-language texts." `emfdscore` depends on `en_core_web_sm`, so it is
English by construction.

Translated *MFD* (not eMFD) versions exist for German/Dutch (Bos & Minihold 2022), Spanish
(Carvalho & Guedes 2022), Chinese (C-MFD 2.0, https://doi.org/10.5117/ccr2023.2.10.chen) and
Japanese — **four of nine corpus languages, from four different groups with four different
construction methods**, so cross-language comparability is not established.

**2. The instruments do not agree with each other.** Stecker & Hopp, *Political Analysis* 34:166-187,
https://doi.org/10.1017/pan.2025.10011 (CC-BY), compared MFD, MFD2, eMFD, DDR, CCR and MoralBERT over
961,455 sentences in four languages:

> "Surprisingly, correlations between the measurement tools are overall very low, to the point where
> **no connection can be said to exist between any**."

Mean Kendall τ *between instruments*: eMFD↔MFD 0.16-0.20, eMFD↔MFD2 0.14-0.21, DDR↔others 0.05-0.23.
Worse for this project's purposes, translated MFD produces **opposite-signed** ideology↔morality
effects across languages — positive Care/GAL-TAN in Dutch and German, negative in English.

**3. Dictionary methods barely track human judgment on exactly this text type.** Rathje et al.,
PNAS 121(34) e2308950121, https://doi.org/10.1073/pnas.2308950121 — 47,925 manually annotated
**tweets and news headlines** across 12 languages, constructs including moral foundations:

> "GPT (r = 0.59–0.77) performed much better than **English-language dictionary analysis
> (r = 0.20–0.30)** at detecting psychological constructs as judged by manual annotators."

And the sparsity problem is decisive at headline length. Stecker & Hopp: "the dictionary word-count
methods show peaks around zero, meaning that **the majority of sentences are not classified**…
because they do not contain words that are also present in the dictionary" — measured on manifesto
*sentences*, which are longer than headlines.

**Conclusion: for 12-word headlines in five languages, lexicon-based moral scoring is not a
measurement but a source of language-dependent noise.** Drop it. This directly matches the empirical
finding in §6.2 that the intensifier lexicon fired on 2% of the corpus.

#### Other lexicons, briefly

- **NRC EmoLex** (14,182 unigrams, 108 languages) and **NRC-VAD** (v2.1, >55,000 terms, 100+
  languages) cover every corpus language — but **you may not ship them**. The terms are explicit:
  "can be used freely for **non-commercial research and educational purposes**"; "**Do not
  redistribute the data.** Direct interested parties to the lexicon home page"; commercial use
  requires contacting the author. http://saifmohammad.com/WebPages/lexicons.html. For a public repo
  with a CI pipeline this means no vendoring, and runtime fetching is fragile and arguably still
  redistribution if cached in a public artifact.
- **LIWC** is commercial (Pennebaker Conglomerates, https://www.liwc.app/). Pricing, the official
  non-English dictionary list and redistribution terms are **not disclosed in fetchable text** —
  treat as paid, not redistributable, language list unconfirmed.
- **Connotation frames**, which would be the principled way to get agency and perspective:
  Rashkin et al., ACL 2016 (https://aclanthology.org/P16-1030/) is **947 verbs × 12 aspect ratings**,
  distributed as a 21 KB Anthology attachment with **no licence file**; Sap et al., EMNLP 2017
  (https://aclanthology.org/D17-1247/) agency/power is **2,149 verbs**, now living in Riveter
  (https://github.com/maartensap/riveter-nlp, GPL-3.0). **Both are English-only with no non-English
  version in existence**, and the verbs are stored as English 3rd-person-singular surface forms, so
  there is not even a lemma layer to port cheaply.
- **Attribution / reported-speech verb lexicons: no standalone public resource exists, in any
  language.** The closest leads (Wilson & Wiebe 2005 on MPQA attributions; Bednarek 2006 on
  evidentiality in English news) are annotation schemes, not downloadable lists. Attribution verbs
  like *say* are already scored inside the Rashkin lexicon, which is the most practical English-only
  substitute. This is why §6 rates the attribution proxy "a feature, not a measure".
- **Multilingual sentiment on CPU**: `cardiffnlp/twitter-xlm-roberta-base-sentiment` covers 8
  languages but **no Russian, no Chinese, and declares no licence at all**;
  `nlptown/bert-base-multilingual-uncased-sentiment` (MIT) covers 6 and misses Arabic, Chinese,
  Russian and Portuguese, and is product-review domain. VADER is **English-only**, confirmed.
  **No multilingual sentiment model trained on news surfaced** — everything available is tweets or
  product reviews.

---

## 4. Why GoEmotions on a headline is not a framing measure

Four independent legs, plus one argument not to make. This section exists so the decision is
recorded as reasoned rather than intuited.

### An argument NOT to make

"GoEmotions is trained on long comments, headlines are too short" is **false**. The corpus is
filtered to comments of **3-30 tokens with a median of 12** (Demszky et al., ACL 2020, §3.1,
https://aclanthology.org/2020.acl-main.372/) — exactly this corpus's title distribution (mean 12.0,
median 11). Length is not the problem, and making that argument would be easy to refute.
The real mismatch is **register and speech act**.

### Leg 1 — Category error, and structural blindness to omission

The construct needed is *selection and salience*. The construct estimated is the affective state of
whoever wrote the string.

The field's own taxonomy makes this concrete: BASIL separates **informational bias** from **lexical
bias** and finds informational bias the **more frequent** of the two
(https://aclanthology.org/D19-1664/); NeuS draws the same line between "which events to cover" and
"how to cover them" (https://arxiv.org/abs/2204.04902).

An emotion classifier reads tokens that are present. **The omission signal — the ticket's own
hypothesis that the strongest evidence is a source not naming someone everyone else names — leaves
no trace in the token stream and is invisible to it by construction.** So the emotion route is at
best a weak proxy for the *less frequent* bias type and structurally blind to the more frequent one.

Two real headlines from this corpus make the point without theory:
"U.S. military says it struck vessel in Caribbean, killing two" (The Hindu) versus
"US military strikes vessel in Caribbean, killing two **alleged narco-terrorists**" (JPost).
Affectively indistinguishable; framed differently on exactly the axis that matters.

### Leg 2 — Register and speech act

GoEmotions comments are first-person expressive speech by a participant. A headline is third-person
referential speech by an institution about someone else's conduct. The target of the label silently
changes: the emotion of the writer, of the event, or of the intended reader? Buechel & Hahn
(EACL 2017, https://aclanthology.org/E17-2092/) find "evidence for the supremacy of the reader's
perspective in terms of IAA and rating intensity" — GoEmotions annotates the **writer's** expressed
emotion, headline tasks annotate the **reader's** perceived emotion. Applying the former to headlines
swaps the construct, for the less reliable of the two.

Cross-corpus transfer is poor (Bostan & Klinger, COLING 2018, https://aclanthology.org/C18-1179/):
"the in-corpus results … show higher F1-scores than the cross-corpus results", and their own framing
is that "Journalists ideally tend to be objective when writing articles … Therefore, the transfer
across emotion recognition models is, presumably, challenging."

*Honest gap:* **no published study runs a GoEmotions checkpoint on news headlines and reports the
degradation.** Leg 4 is this project's own measurement of it, and should be read as such.

### Leg 3 — The instrument is weak, unevenly so, and its labels are contested

- Macro-F1 of the paper's baseline over 27+neutral is **0.46 with a standard deviation across labels
  of 0.19** (Table 4). Not one instrument but 28 of unequal quality: gratitude 0.86, amusement 0.80,
  love 0.78, against **grief 0.00**, relief 0.15, realization 0.21. Collapsing to Ekman-6 raises
  macro-F1 to 0.64, to 4-way sentiment 0.69 — the fine granularity is precisely what fails.
- Chance-corrected agreement among the dataset's own in-domain raters, for the labels a framing
  argument needs: anger κ=0.307, fear 0.394, disgust 0.241, disapproval 0.234, annoyance 0.192,
  disappointment 0.184 (Appendix C, Table 7).
- The taxonomy was **selected for annotator agreement** — boredom, doubt, heartbroken, indifference
  and calmness were removed for low agreement, and the authors state agreement "can be partially
  explained by the fact that we took interpretability into consideration while constructing the
  taxonomy."
- 82 raters, and the paper states "**All raters are native English speakers from India**", over
  Reddit data with, in the authors' words, "a demographic bias leaning towards young male users …
  not reflective of a globally diverse population."
- The deployed checkpoint `SamLowe/roberta-base-go_emotions`
  (https://huggingface.co/SamLowe/roberta-base-go_emotions) reports at the default 0.5 threshold
  **accuracy 0.474, precision 0.575, recall 0.396, F1 0.450** — at the setting this pipeline uses it
  misses ~60% of the emotions present. English-only; the card attributes its ceiling to "ambiguity
  and/or labelling errors visible in the training data".

**Google's own model card is the most quotable source** (`goemotions_model_card.pdf`, in
https://github.com/google-research/google-research/tree/master/goemotions). It lists four canonical
uses — user feedback, social listening, customer support, expressive content — **none of which is
news analysis**, each concerning the emotional state of the text's author. Under Limitations:

> "The data can only be used to determine the **local emotional state of a user**."
> "**Aggregating local emotion predictions does not guarantee a meaningful interpretation over a
> stream of data.**"
> "Context-less emotion prediction means that the input text can often be interpreted in multiple
> fashions. As such, **we expect the prediction to be ambiguous for many input texts**."

and: "the model's predictions are **context-free**, meaning that … **there may be missing factors
for fully evaluating the source of an expressed emotion**."

A framing claim requires exactly the three things ruled out: attributing affect to an editorial
choice rather than a felt state, a *target*, and aggregation over a corpus.

### Leg 4 — Measured on this repository's own output

The literature contains no study of GoEmotions on news headlines. This repository is one. Measured
on the 493 unique titles:

1. **Degenerate output.** 431/493 = 87% `neutral`. Entropy 0.771 bits of a possible 2.585.
   fear = 4 articles, anger = 2.
2. **Inversely ordered by emotional charge.** Mean `manipulation_score`: neutral 85.4, sadness 63.7,
   fear 62.8, anger 50.5, surprise 44.8, positive 25.7. The cause is a code defect —
   `risk_multiplier` initialises to 1.0 and no branch matches `neutral`, so the field returns the
   classifier's *confidence that the headline is bland*. "10 largest man-made lakes in Canada…"
   scores 96/100; so does "Replay: JD Vance addresses US-Iran talks".
3. **Its principal empirical correlate is whether the headline is in English.** The four
   highest-scoring outlets are exactly the four non-English feeds — Spiegel 95.5 (sd 2.2), El País
   95.1 (sd 1.2), Al Jazeera 94.6 (sd 0.9), Le Monde 93.6 — against BBC 69.4 and Japan Times 69.8.
   Non-English mean 89.2 vs English 76.5. An English-only RoBERTa fed Arabic or German collapses
   onto `neutral` with ~0.95 confidence.
4. **27% of its variance is outlet identity** (eta² = 0.270), before any event is considered — the
   same phenomenon Baly et al. document at scale (§2.3).
5. **Its consumer is inert.** `calculate_gti()` uses `fear_anger_count / len(articles)` = 6/500,
   giving 0.36 of a possible 30 points; the 40-point narrative block is a near-constant driven by
   article count.
6. **Two branches are dead code.** The mapping tests for `anxiety` and `frustration`, which are not
   GoEmotions labels. (Separately, `extract_keywords()` filters on `GPE`/`NORP`/`PERSON`, which
   `xx_ent_wiki_sm` never emits — it emits PER/LOC/ORG/MISC.)

*Scope note:* points 3 and 4 measure **this deployment**, not a general claim that GoEmotions
measures outlet style. No published study establishes that, and none refutes it. The defensible
general claim is the one the sources support — absolute affect on a headline is confounded with the
valence of the underlying event and with genre register (NeuS §4.2: "**It is the relative polarity
that is meaningful to indicate the framing bias, not the absolute polarity** … if the news issue
itself is about tragic events … then the polarity of neutral reporting will also be negative").

### Leg 5 — The construct has no reliable human ground truth at the headline level

This closes the question, because it means the route is not merely inaccurate but **unvalidatable**.

- SemEval-2007 Task 14 (https://aclanthology.org/S07-1013/), 1,000 news headlines: inter-annotator
  Pearson, each rater vs the mean of the other five — anger 49.55, disgust 44.51, surprise 36.07
  (valence 78.01). The organisers' own reason for choosing headlines is the house-style argument:
  headlines are "written in a style meant to attract the attention of the readers", "often written
  by creative people with the intention to 'provoke' emotions".
- **GoodNewsEveryone** (https://aclanthology.org/2020.lrec-1.194/): 5,000 English news headlines,
  vetted crowdworkers, five annotators each, and the 5,000 were **pre-selected as the headlines most
  agreed to be emotional at all** — the easy cases. Fleiss **κ on the dominant emotion: 0.09**, with
  1.74 bits of residual entropy. The authors concluded the task has no single ground truth and
  **declined to publish a majority-vote gold label**.

Five vetted humans, on headlines pre-filtered for emotional content, reach κ = 0.09. A classifier
emitting a 28-dimensional point estimate is estimating a quantity humans cannot locate.
**There is no signal against which such a metric could be validated.** By contrast, "which entities
does this headline name" has near-perfect agreement by construction — which is exactly why a
coverage/omission measure can be validated and an emotion measure cannot.

### The decision to record

GoEmotions on a headline is not a weak framing measure to be repaired with a better threshold or a
larger model. It estimates a different construct; it is structurally blind to omission, the more
frequent form of framing bias; it is applied out of domain, out of register and out of language; its
own producers state it cannot attribute a source to the emotion or be meaningfully aggregated; in
this deployment its dominant correlate is whether the headline is English; and the construct has
κ = 0.09 human agreement on headlines. **Remove it from the index rather than reweight it.**

---

## 5. Clustering feasibility, measured

A divergence measure has nothing to compute on without multi-source clusters, so this was measured
before anything else.

### Lexical baseline (tf-idf cosine + union-find, pure Python)

| threshold | clusters >1 | ≥2 domains | ≥3 domains | coverage | containing Arabic |
|---|---|---|---|---|---|
| 0.30 | 33 | 21 | 11 | 80/493 (16%) | 0 |
| 0.40 | 22 | 17 | 6 | 44/493 (9%) | 0 |
| 0.50 | 15 | 11 | 1 | 23/493 (5%) | 0 |

Recall is poor and structurally biased. A keyword probe finds 29 titles from 14 domains on the
Colombia election; lexical clustering at 0.40 recovered 3 of them — ~10% recall on the day's biggest
story, missing every non-English document. **Not one cluster at any threshold contains an Al Jazeera
document**: 16% of the corpus is unreachable because it is in a different script.

### Multilingual embeddings: they work, and they fit the budget

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 117.7M parameters, CPU:

| threshold | clusters >1 | ≥2 domains | ≥3 domains | coverage | cross-language | with Arabic | max cluster |
|---|---|---|---|---|---|---|---|
| 0.60 | 32 | 26 | 15 | 249/493 (51%) | 13 | 5 | 136 |
| 0.65 | 31 | 23 | 16 | 187/493 (38%) | 11 | 6 | 64 |
| **0.70** | 31 | 24 | 14 | 151/493 (31%) | 10 | 5 | 49 |
| 0.75 | 32 | 28 | 14 | 124/493 (25%) | 11 | 6 | 24 |
| 0.80 | 27 | 25 | 9 | 75/493 (15%) | 8 | 2 | 9 |

Roughly double the multi-source clusters, triple the coverage, and — decisively — **the Arabic
documents are recovered.** At 0.70 the Colombia cluster grows from 3 documents to 24 across
14 domains, including Al Jazeera's Arabic headline
"سانده ترمب.. مرشح أقصى اليمين يفوز برئاسة كولومبيا بفارق ضئيل" ("Trump backed him… far-right
candidate wins Colombia's presidency by a narrow margin"), which usefully uses *both* descriptors
that split the Western outlets.

This independently reproduces Reuver et al.'s finding that SBERT + agglomerative clustering
substantially beats TF-IDF for story-chain clustering (https://arxiv.org/abs/2309.06192).

**Cost, measured not estimated.** Import 17.2s, model load 59.8s cold (including download), and
**encoding 493 titles in 33.2 seconds — 14.9 titles/sec.** The Action already budgets
`timeout 600`. And note the comparison: today `analyze_narrative_hf` makes one HTTP call per article
to the Hugging Face router with `time.sleep(0.5)` between them — ~250 seconds of deliberate sleeping
for 500 articles before any latency. **Running a small model locally is cheaper than the remote call
the pipeline already makes**, and removes a rate-limited third-party dependency.
*Caveat:* these timings are from a local machine pinned to torch 2.2.2, not a GitHub runner; cold
load and wheel download are cache-dependent in CI. The order of magnitude is the point.

### Two honest problems the experiment exposed

**1. The clusters are stories, not events.** At 0.70 the 24-document Colombia cluster contains the
result, protests against the result, pre-vote analysis ("Ghost of far-right paramilitaries hovers
over Colombia's presidential runoff vote"), and turnout among Colombians in Spain. The 21-document
Starmer cluster mixes resignation rumours, the resignation, and a feature on failed prime ministers.
Divergence over such a cluster partly measures *that these are different sub-events*. This is
exactly the distinction SemEval-2022 Task 8 factorises out (§2.6) and it must be handled — tighter
threshold, time-windowing, or accepting story-level granularity and saying so.

**2. Threshold choice is doing a lot of work.** At 0.60 the largest cluster is 136 documents, a
blob; at 0.80 coverage falls to 15% and only 2 clusters contain Arabic. The usable band is narrow
and was chosen here by inspection, which is not a method. Threshold selection must be tied to the
validation set.

### The two control cases already exist in the corpus

- **Expected-low divergence:** the Alan Greenspan obituary — three sources, one clean isolated
  cluster of exactly 3, mean pairwise cosine **0.888**. ("architect of the modern American economy" /
  "former US Fed Reserve chair" / "longtime U.S. Federal Reserve chairman", all "dies aged 100".)
- **Expected-high divergence:** the Espriella result — 10 titles, mean pairwise cosine **0.594**.

A crude spread statistic already separates them in the right direction. That is not validation — one
pair of anchors, and part of the gap is language rather than framing, which is precisely why the
residualisation in M2 is mandatory. But it means the hand-labelled ranking set (V4) can be built
from data the project already has.

---

## 6. Proxies, ranked by what this corpus supports

| proxy | in titles? | needs body? | multilingual? | verdict |
|---|---|---|---|---|
| **actor absence** | yes, strongly | no | only with entity linking | **best candidate**, blocked on normalisation |
| **descriptor / word choice** | yes, strongly | no | no (disjoint vocabularies) | **most validatable**, scope to one language |
| **numeric claims** | yes | no | yes (digits are language-neutral) | cheap, narrow, high precision |
| **attribution** (says/reports) | yes | no | poorly (uneven lexicon coverage) | a feature, not a measure |
| entity salience / position | partly | no | needs per-language parsing | weak on 12-word titles |
| actor vs patient roles | in principle | no | needs dependency parsing | promising, unbuilt, costly |
| moral foundations lexicons | barely | **yes** | **no** | **drop it — §3.6** |
| polarity / intensity | yes but | no | model-dependent | **measures house style** |
| emotion (GoEmotions) | no | n/a | no | rejected, §4 |

### What the corpus supports

**Actor absence — real, and the strongest thing here.** On the Colombia cluster, 8 of 20 titles name
Trump and 12 do not: the Guardian, JPost, Straits Times, El País, The Hindu and MercoPress omit him
while the BBC, NYT, Le Monde, Spiegel, RT, SCMP and France24 name him. The ticket's hypothesis,
present in two days of real data, readable from titles alone. It is also the proxy most damaged by
naive implementation — see §6.1.

**Descriptor divergence — real, and the most legible.** Seven descriptors for one person on one day:

| source | descriptor | names Trump |
|---|---|---|
| lemonde.fr | candidat d'ultradroite | yes |
| theguardian.com | Far-right millionaire | **no** |
| rss.nytimes.com | Trump-Backed Rightist | yes |
| jpost.com | Right-wing candidate | **no** |
| feeds.bbci.co.uk | Trump-backed political outsider | yes |
| spiegel.de | Trumps Tiger | yes |
| rt.com | Trump-backed 'Tiger' | yes |
| straitstimes.com | law-and-order newcomer | **no** |
| aljazeera.net | مرشح أقصى اليمين (far-right candidate) | yes |

**Numeric divergence — real, cheap, narrow, and multilingual for free.** The Qatar gas plant
explosion, five sources, one event:

- lemonde.fr: "l'explosion d'un complexe gazier fait **54 blessés et 18 disparus**"
- rss.nytimes.com: "Explosion at Qatar Gas Plant Leaves **at Least 54 Injured**" (no missing)
- straitstimes.com: "**Qatar reports** explosion at factory in Ras Laffan, **several** injured"
- rt.com: "**Massive** explosion **rocks** Qatari gas processing hub (VIDEO)" (no numbers)
- aljazeera.net: "**الداخلية القطرية**: انفجار بمصنع في رأس لفان **نتيجة عطل فني**"
  ("**Qatari Interior Ministry**: explosion at a factory in Ras Laffan **as a result of a technical
  fault**")

One cluster exercises every proxy in the table: numeric divergence, attribution (unattributed
assertion vs "Qatar reports" vs a named ministry as speaker), a causal attribution present in
exactly one source and exculpatory, intensity, and location specificity. Digits are language-neutral,
so this proxy is genuinely multilingual — its weakness is coverage, firing on only 15% of titles.

**Agency divergence — the strongest single example in the corpus.** The same Strait of Hormuz
closure, four sources, four different agents:

- straitstimes.com: "German minister blames **Trump** for Strait of Hormuz closure"
- aljazeera.net: "**طهران** تواصل إغلاق مضيق هرمز…" ("**Tehran** continues closing the Strait…")
- rt.com: "Only **US** could impose Hormuz tolls – Trump"
- scmp.com: "**Iran, US claims conflict** over Hormuz…"

**Attribution — real but confounded.** "U.S. military **says** it struck vessel" (The Hindu) vs
"US military strikes vessel" (JPost) is a genuine framing difference. But per-source attribution
rates range from 0.34 (JPost) to 0.00 (El País, Japan Times, Guardian, China Daily), and the zeros
are partly an artifact of an English-biased cue list. **Any hand-built cue lexicon will have uneven
cross-lingual coverage and will therefore *manufacture* apparent divergence between languages.**

### 6.1 The entity-normalisation problem, measured

`extract_keywords()` runs spaCy `xx_ent_wiki_sm` on titles. The actual `top_keywords` output shows
systematic surface-form fragmentation of the same referent:

trump (19) / donald trump (8) · keir starmer (15) / starmer (12) · abelardo de la espriella (6) /
espriella (3) · britain (5) / u.k. (3) / großbritannien (3) · russia (2) / russie (3) / moscou (2) ·
crimea (4) / crimée (3) · colombia (13) / colombie (2) / colombians (3) · hormuz (3) /
strait of hormuz (3)

And systematic type errors: `hormuz` tagged PER, `jd vance` and `meloni` tagged ORG, `brexit` tagged
LOC, `espriella` tagged LOC while `abelardo de la espriella` is PER, `direct` tagged ORG (from
Le Monde's "EN DIRECT" live-blog prefix), and two Arabic function words as entities — `كيف` ("how")
tagged LOC, `كأس` ("cup") tagged ORG. **No Arabic named entity appears in the top 60 despite 79
Arabic articles** — Al Jazeera's actual actors never surface while Arabic interrogatives do.

The Arabic failure has a simple explanation, recorded in §3.5: **spaCy has no Arabic pipeline at
all**, and `xx_ent_wiki_sm` is trained on WikiNER, which has no Arabic section. The pipeline is not
misconfigured; it is asking for something that does not exist. Fixing it means adding Stanza (the
only surveyed tool with Arabic NER, F1 74.3) or excluding Arabic and declaring the exclusion.

**Consequence.** Without cross-lingual entity normalisation, "source A does not mention Trump" is
indistinguishable from "source A wrote 'Donald Trump' where others wrote 'Trump'", and from "source
A is Arabic and the NER found nothing". **The proxy the ticket calls the strongest signal is
precisely the one most destroyed by raw NER strings.** Entity linking to a shared identifier space
is a prerequisite, not an optimisation.

### 6.2 The decisive negative result: surface features measure house style

Per-source rates of seven crude surface cues over 493 titles:

| source | n | attribution | hedge | quotes | question | numbers | intensifier | colon |
|---|---|---|---|---|---|---|---|---|
| www.spiegel.de | 20 | 0.05 | 0.00 | 0.15 | 0.05 | 0.05 | 0.00 | **0.90** |
| www.lemonde.fr | 36 | 0.03 | 0.00 | **0.72** | 0.00 | 0.08 | 0.00 | 0.44 |
| timesofindia | 41 | 0.17 | 0.02 | 0.63 | 0.10 | 0.24 | 0.10 | 0.51 |
| feeds.elpais.com | 23 | 0.00 | 0.00 | 0.26 | 0.00 | 0.13 | 0.00 | 0.43 |
| www.jpost.com | 32 | **0.34** | 0.06 | 0.31 | 0.03 | 0.06 | 0.06 | 0.09 |
| www.straitstimes.com | 29 | 0.28 | **0.17** | 0.21 | 0.00 | 0.10 | 0.00 | 0.07 |
| feeds.bbci.co.uk | 22 | 0.18 | 0.05 | 0.27 | 0.00 | 0.14 | 0.05 | **0.00** |
| www.theguardian.com | 8 | 0.00 | 0.00 | 0.50 | 0.00 | 0.12 | 0.12 | 0.00 |
| www.aljazeera.net | 79 | 0.01 | 0.00 | 0.13 | 0.00 | 0.20 | 0.00 | 0.10 |
| **CORPUS** | 493 | 0.11 | 0.04 | 0.33 | 0.05 | 0.15 | 0.02 | 0.21 |

Spiegel opens 90% of headlines with a colon; the BBC and Guardian 0%. Le Monde uses quote characters
in 72% of headlines; Al Jazeera in 13%. These are CMS conventions and style guides, and they dwarf
anything event-specific.

Two consequences that constrain every candidate:

1. **A feature rate computed per source over a corpus is dominated by that outlet's headline
   conventions.** Any measure must be computed *within an event cluster* and differenced against the
   source's own baseline. This is the same phenomenon as §2.3 (Baly et al.: outlet identity is 80%
   recoverable, ideology is not) and §4 (eta² = 0.27).
2. **Intensifiers have no signal at this scale** — 0.02 corpus-wide, ~10 of 493 titles. Lexicon-based
   intensity on 12-word titles is too sparse for a per-cluster statistic.

### 6.3 The statistical power problem

On the Colombia cluster, per-source Trump-mention rates are 1/1, 1/1, 2/3, 1/2, 1/2, 1/2, 1/3, and
six 0/1s. Each source contributes 1-3 titles to the day's biggest event. A rate estimated from n=1
carries no information; the difference between 0/1 and 1/1 is a coin flip. And per §2.6, plug-in
divergence estimators are *upward biased* at this sample size — so the measure will not merely be
noisy, it will be **systematically wrong in a specific direction**, reporting more divergence for
lower-volume sources.

Anything reported per source per event is noise. The measure must pool across clusters and days, or
report only cluster-level scalars.

### 6.4 What requires the article body, and what that costs

State it as a budget line, not a footnote. Not available from a ~12-word headline:

- **Frame classification in the MFC sense.** Generic frames are annotated over articles; a headline
  is one sentence and frequently carries no frame cue. §2.4 quantifies the loss.
- **Actor vs patient roles across the narrative, and who is quoted.** A headline names 1-3 entities;
  the sourcing pattern of a story lives in the body.
- **Moral Foundations scoring.** Dictionary methods need enough tokens for a stable rate; 12 words
  yields 0 or 1 hits and the per-document score is noise.
- **Omission of *facts*** as opposed to omission of *actors*.

The cost of adding bodies: an HTTP fetch per article (hundreds of requests inside a ten-minute
Action, against paywalls, consent walls and robots.txt), HTML boilerplate removal, storage growth of
roughly two orders of magnitude over the current 476 KB `news.json`, licensing exposure from storing
full copyrighted text in a public repo, and a new class of pipeline failure. Whether it is worth it
is a real decision — but it must be taken as one, with that list visible.

**The honest position:** the actor-absence and descriptor proxies work on headlines; the framing
literature's own constructs mostly do not. Building on the first two and declaring the third out of
scope is a coherent product. Claiming the third from headlines is not.

---

## 7. The shape of the measure

The three shapes in the ticket — pairwise distance, cluster entropy, source × source matrix — are
posed as alternatives. **They are not alternatives; they are three views of one object.**

Lin's generalized Jensen-Shannon divergence over a weighted family `P = {(w_i, p_i)}`
(J. Lin, IEEE Trans. Inf. Theory 37(1):145-151, 1991,
https://ieeexplore.ieee.org/document/61115, Eq. 5.1) is

```
D_JS[P] = H( Σ_i w_i p_i ) − Σ_i w_i H(p_i)
```

— entropy of the mixture minus the weighted mean of the entropies. As Nielsen's exposition notes
(https://franknielsen.github.io/blog/blogJSD/JensenShannonDiv.pdf), this "is nowadays called the
**Jensen-Shannon diversity index**". Two readings matter:

1. `D_JS[P] = Σ_i w_i · KL(p_i ‖ p̄)` where `p̄` is the mixture. **The cluster scalar is the weighted
   mean divergence of each source from the consensus — so it decomposes into per-source contributions
   for free.** The "which outlet drives this" ranking comes without a second measure.
2. As Sibson's information radius, `min_c Σ_i w_i KL(p_i ‖ c)`, minimised at `c = p̄`:
   "how much do these sources disagree" = "how badly does the best possible single consensus account
   for all of them".

So: **compute the pairwise matrix as the primitive, headline the cluster scalar as the summary, show
the per-source terms as the explanation.** The choice is what to report, not what to compute.

Five technical points, cheap now and expensive later:

- **Use √JSD, not JSD, for anything geometric.** JSD is bounded and symmetric but violates the
  triangle inequality; √JSD is a metric (Endres & Schindelin, IEEE Trans. Inf. Theory 49(7), 2003,
  https://doi.org/10.1109/TIT.2003.813506). Any clustering of sources, MDS layout, centroid, or
  "A is closer to B than to C" claim needs the square root.
- **Normalise by log N.** The two-distribution JSD is bounded by 1 bit; the generalized form over N
  sources is bounded by the entropy of the weights, i.e. `log N` for uniform weights. Without
  normalising, **an apparent rise in divergence over time can be entirely an artifact of more
  outlets covering later events** — a trap this project would walk into, since feed presence is
  randomised per run.
- **JSD tolerates disjoint support; KL does not.** Two outlets' entity distributions routinely share
  no support, making KL infinite and JSD merely maximal. RADio (https://arxiv.org/abs/2209.13520)
  prefers JSD for exactly this reason, and adds smoothing `Q̄ = (1−α)Q + αP` plus rank weighting.
- **Do not use the size-weighted (Gallagher) JSD variant** — its rankings shift with relative corpus
  size (https://aclanthology.org/2020.lrec-1.832/), and outlets here publish 5 to 79 headlines each.
- **Use Lu et al.'s per-item decomposition for the drill-down:**
  `D_JS,i(P‖Q) = −m_i log2 m_i + ½(p_i log2 p_i + q_i log2 q_i)`. This is what turns a scalar into
  the per-token or per-entity table a reader can actually see.

**If framings differ by varying amounts, Rao-Stirling is the only candidate that can say so.**
`Δ = Σ_{i≠j} d_ij p_i p_j` (Stirling, J. R. Soc. Interface 4(15):707-719, 2007,
https://pmc.ncbi.nlm.nih.gov/articles/PMC2373389/) admits a *disparity matrix* — it can express that
swapping "protest" for "riot" is a small difference while omitting the victim entirely is a large
one. JSD-family measures treat categories as exchangeable atoms and cannot. Stirling decomposes
diversity into **variety**, **balance** and **disparity**.

But report the factors separately, not the product: Leydesdorff, Wagner & Bornmann
(https://arxiv.org/abs/1803.09317) show "two factors cannot cover three concepts", and empirically
Rao-Stirling correlates 0.896 with Simpson and 0.893 with Shannon but **−0.078 with Gini** — it does
not actually track balance. A conflated scalar cannot distinguish "many outlets each saying slightly
different things" from "two outlets saying wildly different things", and a reader would want those
told apart.

**Krippendorff's α is the wrong tool**, and worth saying so because it is the obvious thing to reach
for. Its null model treats coders as interchangeable instruments measuring one truth, with
disagreement as error (Artstein & Poesio, CL 34(4), 2008, https://aclanthology.org/J08-4004/). For
news outlets, **disagreement is the signal, not the error**; chance-correcting it away destroys the
quantity being measured. α has exactly one legitimate role here: as the ceiling when validating
against human judgment.

### Recommendation

Primary object: the **cluster-level scalar**, normalised by `log N`, decomposed into per-source
contributions and displayed with them. The index is the average over the day's clusters. The
pairwise √JSD matrix is the drill-down inside a cluster. The pooled source × source matrix is the
right long-run artifact and should shape the **archive schema now** — per-cluster, per-source vectors
must start being written before any of it is possible — but must not be published until the cells
are populated. Reserving the schema is free; publishing an empty matrix is not.

---

## 8. Three candidate measures

All take the same input: a cluster C of headlines grouped by source. All obey the constraint
measured in §6.2 — the source main effect must be removed — and all follow NeuS's calibration
principle: **subtract the cluster consensus before scoring**. In the authors' words
(https://arxiv.org/abs/2204.04902, §5.1.1): "if 'riot' exists in the neutral target, it will not be
counted in bias measurement through calibration."

### M1 — Actor Presence Divergence (recommended)

For cluster C with source set S_C, link entities to a shared identifier space. For each entity e,
let `p_e` = (number of sources whose headlines mention e) / |S_C|. Then

```
APD(C) = (1/|E_C|) · Σ_e H2(p_e),   H2(p) = −p log2 p − (1−p) log2(1−p)
```

An entity every source names contributes 0 bits; one exactly half the sources name contributes 1
bit, the maximum. Bounded [0,1]. Reads as "how contested, on average, is the cast of this story".
Restrict `E_C` to entities mentioned by ≥2 sources to avoid rewarding NER noise.

**Why this one.** (a) It targets *informational* bias, which BASIL finds is the **more frequent**
type. (b) Its vocabulary is small and closed, so it is far less exposed to the finite-sample
divergence bias of §2.6 than any token-based measure. (c) It is the only candidate whose ground
truth — "does this headline name X" — humans agree on, so it can actually be validated.
(d) Its drill-down is the number: "Trump — named by 8 of 13 sources (0.96 bits)".

**Do not use symmetric Jaccard.** "A omits an entity everyone mentions" and "A mentions one nobody
else does" are different editorial acts priced identically by Jaccard. Follow NeuS's asymmetric
coverage-against-reference: report `|E_A ∩ C| / |C|` (coverage of the consensus) and
`|E_A \ C| / |E_A|` (exclusivity) as two numbers.

**Terminology correction, and it matters.** In the Media Bias Taxonomy
(https://arxiv.org/abs/2312.16148), omission is **selection/coverage bias** at the reporting level,
while **framing bias** is a text-level phenomenon, "the use of subjective words or phrases linked
with a particular point of view". If the flagship measure is about who gets mentioned, it measures
selection and coverage, and calling it "framing divergence" invites exactly the objection the project
should want to avoid. **Name it for what it measures.**

**Input required:** headlines + **cross-lingual entity linking**. Not raw NER strings (§6.1). This is
the largest new dependency in this document. §3.5 establishes that no off-the-shelf option fits the
runner (mGENRE ≥3 GB and autoregressive; DBpedia Spotlight has no Arabic or Chinese; the Wikidata
dump is 130 GiB against a 14 GB disk), and that the workable design is a **Wikidata label/alias
table built once offline and cached** — which works precisely because every language's label sits on
the same CC0 item. It is a build-time artifact, not a runtime cost, but it is real work.

Arabic needs two things this project does not have yet: an NER model that exists for it (Stanza, not
spaCy — §3.5) and linking rather than string normalisation. Until both are in place, Arabic must be
excluded from M1 and the exclusion *declared*, not silently absorbed.

### M2 — Residual semantic spread

Embed each headline; residualise out the two nuisance factors measured here before computing spread:

```
e'_d = e_d − mean(e | language(d)) − mean(e | source(d)) + grand_mean
```

then take mean pairwise cosine distance among residualised vectors.

The residualisation is load-bearing. Multilingual encoders place documents partly by language;
outlets have house style. Without removing both, RSS reproduces the exact failure measured in §4,
where the four "most manipulative" outlets are the four non-English feeds. And Hamborg's warning
(§2.6) applies directly: opposing articles on the same topic have *high* TF-IDF/embedding
similarity, so the raw signal is topic, not framing. The measured Greenspan-vs-Espriella contrast
(0.888 vs 0.594) is encouraging but **partly attributable to language**, since one cluster spans five
languages and the other one — residualisation is what separates those explanations.

**Input:** headlines and a CPU encoder. Measured cost: 33 seconds for 493 titles. No annotation, no
lexicon, no entity linking. By far the cheapest.

**Honest risk:** after removing topic, language and source, what remains may be sampling noise.
**M2 should not ship unless it passes V1.** Discarding it on evidence would itself be a result.

### M3 — Descriptor divergence (within-language lexical JSD)

Within a cluster, restrict to one language, build per-source distributions over content lemmas after
removing every token present in the cluster consensus, and take the generalized JSD across sources,
normalised by `log N`, with Lu et al.'s per-item decomposition for the drill-down.

The top-contributing tokens are the output the reader sees: *ultradroite / far-right / rightist /
right-wing / political outsider / Tiger / law-and-order newcomer*. The project's thesis in one
screenshot, **derived from the score** rather than illustrated beside it.

**Input:** headlines, a tokeniser, a stopword list. Nothing else.

**Two hard limits, stated plainly.**
1. **Across languages this measure is degenerate.** French and English headlines share almost no
   vocabulary, so JSD between them is near-maximal by construction and carries no framing
   information. M3 is valid within a language or on translated text. Scoping it to English (68% of
   the corpus, 19 of 23 feeds) is defensible; claiming it works cross-lingually is not.
2. **It is the candidate most exposed to the GST finite-sample bias** (§2.6). With 1-3 twelve-word
   headlines per source against an open vocabulary, a naive plug-in estimator will report divergence
   between outlets saying the same thing. It needs a bias-corrected estimator, a permutation
   baseline, and a minimum-document-count gate — or it should not ship.

---

## 9. How to validate — and what cannot be validated

### V1. Permutation test on source labels

Shuffle which source each headline came from, recompute, repeat. If the observed value does not sit
in the tail of the shuffled distribution, the measure is reading document-level variation, not
source-level structure. Canonical reference: Yeh, COLING 2000
(https://aclanthology.org/C00-2137/), which gives the p-value bound `(n_c + 1)/(n_t + 1)` and the
good practice of re-running the shuffle set to check stability. See also Dror et al., ACL 2018,
https://aclanthology.org/P18-1128/.

This is the test that most directly answers "is this a number or is it noise", **and it doubles as
the control for the finite-sample bias of §2.6** — the shuffled null is subject to the same bias, so
the comparison is bias-free even when the raw estimate is not. Gate all three candidates on it.

Power limit at cluster size 3-5: few distinct label assignments, so the smallest achievable p-value
is bounded away from zero. Report the achievable minimum alongside the p-value, or pool across the
day's clusters. And Artstein & Poesio's caution applies: "a null hypothesis of chance agreement is
not very interesting, and demonstrating that agreement is significantly better than chance is not
enough". Passing V1 is necessary, not sufficient.

### V2. Self-similarity — the within-source null

Kilgarriff, *Comparing Corpora*, IJCL 6(1):97-133, 2001
(https://www.kilgarriff.co.uk/Publications/2001-K-CompCorpIJCL.pdf), on exactly this problem:

> "It can be used for measuring the similarity of a corpus to itself, as well as the similarity of
> one corpus to another, and this feature is valuable as, **without self-similarity as a point of
> reference, a measure of similarity between corpora is uninterpretable.**"

His procedure: split each source's material into slices, randomly allocate half to each of two
subcorpora, measure, iterate, report mean and sd. **The trap to avoid:** measure between-source
distance *the same way*, half against half. Comparing a full-vs-full cross-source distance against a
half-vs-half within-source distance inflates the effect. His Table 6 gives a falsifiability check:
the "high/high/low" cell is marked *impossible* — two corpora cannot be more similar to each other
than either is to itself. A measure producing it is broken.

Consequence for interpretation, and it is not obvious: a wire service with rigid house style and an
opinion-heavy outlet have different internal homogeneity, so **a raw A-B divergence is not
interpretable until it is normalised by each source's self-distance.**

With 1-3 headlines per source per cluster this cannot be run today. That is a reason to collect more
per source, not a reason to skip it.

### V3. Synthetic mixtures — validation with no annotators

Kilgarriff's Known-Similarity Corpora design, and the best value in this document: build clusters by
mixing documents from two outlets in known proportions (100/0, 90/10, 80/20 …) and check the measure
orders them correctly. **Quantitative validation with no human labelling** — for a solo project, the
difference between a test that gets run and one that does not.

⚠️ One finding cuts against the JSD choice: on his KSC evaluation "χ² and Spearman both performed
better than any of three cross-entropy measures … χ² outperformed Spearman". His setting is
500-most-frequent-word lists and his cross-entropy variants are not JSD, so do not over-read it —
but a χ² baseline should be in the comparison rather than assumed away.

### V4. Hand-labelled ranking set, with an agreement ceiling

~40 clusters scored on a 3-point divergence scale by two people independently; report Spearman
against the measure, and inter-annotator agreement as the ceiling. Two anchors already exist in the
corpus (§5): the Greenspan obituary (known low) and the Espriella result (known high).

The register of claim to aim for is NeuS's: they report "Spearman correlation coefficient between
human-based and metric-based annotations is 0.63615 with a p-value < 0.001, and the agreement
percentage 80%", and conclude only that the metric "provides a good approximation". A good
approximation, from ρ = 0.64 — not a measurement.

### V5. External check against BASIL

Run the measure on **BASIL headlines only** and correlate with the annotated bias divergence across
each triplet. A genuine external test, and specifically a test of the headline-only claim, since the
bodies exist and would be deliberately withheld. Caveats: 300 articles is small; English-only, so it
validates M3 and the English half of M1 and says nothing cross-lingual; and the repo carries no
licence file.

### What cannot be validated with the means available

- **Anything called "framing" in Entman's sense.** These estimators measure divergence in actor
  selection and word choice. Under the field's own taxonomy that is selection/coverage bias plus
  lexical bias — components of framing, not framing. Name the metric accordingly.
- **Emotion-based divergence, at all.** Now a formal result, not a preference: with Fleiss κ = 0.09
  for the dominant emotion of a headline (§4, Leg 5), there is no reliable human ground truth to
  validate against. **The emotion route is not merely inaccurate, it is unvalidatable** — the
  strongest available argument for the direction taken here.
- **Cross-lingual divergence on this corpus.** One source per non-English language; language and
  outlet perfectly confounded. No model fixes it.
- **Any source-level claim from a single day**, at 1-3 headlines per source per cluster — and worse
  than noisy, biased in a known direction (§6.3).
- **Retrospective validation on the project's own history.** `data/archive/` holds daily scalars
  only. Validation is forward-built from a schema change, or borrowed from BASIL.

---

## 10. Corrections to the ticket and the map

1. **"~9 lingue" is wrong.** The corpus is 5 languages (English 68%, Arabic 16%, French, Spanish,
   German), and the `language` metadata is factually incorrect for 4 of 18 domains. More importantly
   there is **one source per non-English language**, which is the real blocker.
2. **"l'assenza di un attore (spesso il segnale più forte)" is well-founded** — BASIL finds
   informational bias more frequent than lexical bias — **but it is also the proxy most destroyed by
   naive implementation.** Raw NER strings make omission indistinguishable from spelling variation
   (§6.1). The ticket treats it as the easy win; it is the strongest signal behind the most
   expensive prerequisite.
3. **The three "forms" of the measure are not alternatives.** Pairwise distance, cluster entropy and
   the source × source matrix are three views of the same generalized JSD object (§7). The real
   decision is what to *report*, and when.
4. **Stance detection should be dropped from scope**, not researched further: it requires a stated
   target and falls below the majority baseline when the text is about something adjacent (§2.5).
5. **The ticket does not mention the finite-sample bias problem**, which is the most likely way a
   naive implementation produces confident nonsense (§2.6). It is the single strongest technical
   argument for preferring the entity-based measure.
6. **Moral Foundations lexicons should be dropped, not deferred.** The ticket lists them as a
   candidate proxy. They are English-only in their best form (the eMFD's own author says so in
   print), the available translations cover 4 of 9 languages from 4 different groups and produce
   **opposite-signed results across languages**, the instruments correlate with *each other* at
   τ ≈ 0.05-0.25, and dictionary methods correlate r ≈ 0.20-0.30 with human annotation on tweets and
   news headlines specifically. Plus the sparsity problem at 12 words. §3.6.
7. **`xx_ent_wiki_sm` cannot see Arabic**, because spaCy has no Arabic pipeline and WikiNER has no
   Arabic section (§3.5). The measured Arabic NER failure (§6.1) is structural, not a bug.
8. **LaBSE would be the wrong encoder** despite being the intuitive cross-lingual choice: it is
   optimised for finding translations and underperforms on paraphrase similarity (cross-lingual STS
   73.5 vs 83.7), which is what same-event articles actually are (§3.5).

---

## 11. Recommended next steps, cheapest first

1. **Add a second outlet per non-English language, and raise `feed.entries[:10]`.** A dozen lines.
   Converts an unidentifiable measurement into an identifiable one, and is a precondition for V2.
   Nothing else in this document delivers as much per unit of effort.
2. **Change the archive schema** to store per-cluster, per-source data. Free now, impossible
   retroactively — every day it is not done is a day of validation data lost.
3. **Remove the GoEmotions call and the `manipulation_score` field** (§4), and with it the narrative
   term in `calculate_gti()`, which is a near-constant anyway (§4, Leg 4, point 5).
4. **Replace the remote HF call with a local multilingual encoder** — `multilingual-e5-small`, int8
   ONNX, 118 MB, MIT, with the mandatory `"query: "` prefix (§3.5). Measured faster than the
   round-trips it replaces, and removes a rate-limited dependency (§5). Do not reach for LaBSE.
5. **Build the two-anchor validation set** from the Greenspan and Espriella clusters, then extend to
   ~40 clusters (V4). The anchors already exist.
6. **Implement V1 (permutation) and V3 (synthetic mixtures) before implementing any measure.**
   Both are cheap, neither needs annotators, and together they will kill a bad measure before it
   reaches a dashboard.
7. Only then implement M1, and gate it on V1.

### Open questions this document does not settle

- **Event vs story granularity** (§5). Clusters currently span sub-events. Unresolved whether to
  tighten the threshold, add time-windowing, or accept story-level and say so.
- **Threshold selection** is currently by inspection. It should be tied to the validation set.
- **Whether M2 survives residualisation** — genuinely unknown until V1 is run on it.
- **Whether to fetch article bodies** (§6.4). A real decision with a real cost, to be taken
  explicitly.
- **Two experiments nobody appears to have run**, both relevant: headline-frame vs article-frame
  agreement inside MFC (Card et al. annotated both; no published comparison exists — though MFC's
  text is no longer obtainable), and headline-sentiment vs body-sentiment correlation (the proxy
  assumption is cited to Allan Bell's *The Language of News Media*, 1991, and appears never to have
  been measured in NLP).
