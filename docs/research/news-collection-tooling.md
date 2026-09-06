# News collection tooling: article extraction libraries, and free feeds to ingest alongside GDELT

Fact-finding for two questions asked together, because they turn out to be the same question seen
from two ends: **what can be extracted from a news URL**, and **where the URLs come from**. Written
2026-09-06.

**This document does not decide anything.** It measures, attributes, and ranks. Where a published
figure exists it is quoted with the URL that owns it. Where no published figure exists that is said
plainly rather than filled in with an estimate.

**Method note.** Two prior research tasks in this project were burned by second-hand summaries, one
of them producing fabricated references. So the rule here was: open the repository, read the licence
file, probe the endpoint. Every number in §4 and §7 is my own measurement on this project's own
corpus, taken today, and the script that produced it is described well enough to re-run. Every
number in §3 and §8 that I did not take myself is attributed to whoever did take it, and §11 lists
what I could not verify at all.

- **Measured on**: 2026-09-06
- **Machine for the extraction benchmark**: Intel Core i5-8257U at 1.40 GHz, macOS 15.7.9,
  CPython 3.12.8, single process, single thread. This is a slow 2019 laptop CPU. A GitHub-hosted
  `ubuntu-latest` runner on a public repository is **4 cores, 16 GB RAM, 14 GB SSD**
  ([docs.github.com](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)),
  so the per-core figures below are conservative and the per-job figures should be multiplied by
  four, not by eight.
- **Corpus for the extraction benchmark**: one real `gsg_docembed` heartbeat, the same feed
  `backend/src/tensionr/stories/window.py` reads.

---

## 0. What is settled, and what is not

| | Status |
| --- | --- |
| **Trafilatura is the best-maintained, best-licensed and most accurate general extractor available**, and it is the only one that returns title, body, date and author from a single call. Measured here at 96.3% body coverage across 18 languages and body F1 0.816 against an independent reference. | **Settled.** §2, §4 |
| **No benchmark in existence measures multilingual article extraction on the modern web.** The three benchmarks with real numbers are 71% German-TLD, 89% English and 98% English. The one genuinely multilingual evaluation uses pages collected in 2011 and 2012 and does not contain a single tool released after 2020. | **Settled, and it is the most important finding in Part A.** §3.4 |
| **`newspaper3k` is dead.** Its last commit touching the package directory is 2020-06-22. Every commit since is README edits selling proxy-vendor advertising slots. | **Settled, verified from the commit log.** §2.1 |
| **A headless browser buys almost nothing on this corpus.** 105 of 107 fetched pages yielded a body from at least one extractor without any JavaScript execution. | **Measured, on a small sample.** §4.5 |
| **The bottleneck is not extraction, it is fetching.** Trafilatura extracts 100,000 articles in about 2 hours of 4-core runner time. Fetching those 100,000 pages is 21 GB of HTML and a robots.txt question against several thousand publishers. | **Measured for the extraction half, argued for the fetching half.** §4.4, §9.4 |
| **Media Cloud publishes an unauthenticated nightly dump of every URL its 180,000 feeds discovered that day**, 486,092 items for 2026-09-05 in a single 47 MB request, across 15,080 hosts and 170 country-code TLDs. It is the only candidate that clears the 100k-200k/day bar for free. | **Measured myself today.** §8.1 |
| **That dump is undocumented.** It appears nowhere on mediacloud.org. It was found by reading their open-source repository. There is no SLA and the same codebase carries basic-auth credentials for a sibling API. | **Settled, and it is the reason this is a spike and not a decision.** §8.1, §10 |
| **GDELT publishes a 5.6 MB static domain-to-country lookup that resolves 98.7% of a live heartbeat to 70 countries in a single 15-minute slot.** The project already ingests the heartbeat and does not use the lookup. | **Measured myself today.** §7.6 |
| **GDELT's Global Frontpage Graph and Global Entity Graph are both dead.** GFG has served a 45-byte empty gzip since roughly mid-October 2025. GEG stopped on 2026-06-18 at 22:31 UTC. | **Verified by probe.** §7.4, §7.5 |
| Whether an unattended GitHub Actions job may lawfully fetch 100,000 publisher pages a day | **Not established.** Out of scope here, and it is the question that decides whether Part A matters at all. §11 |

---

# Part A. Extracting title, body, date, author and language from a news URL

## 1. What was measured, and what could not be

### 1.1 The sample

One `gsg_docembed` heartbeat was downloaded: `20260905231500`, 4,328,972 bytes gzipped,
**1,502 records in 36 languages**. From it, a stratified sample was drawn across the 18 largest
languages, **at most one URL per domain**, giving **109 URLs across 109 distinct domains and 18
languages**. The one-URL-per-domain rule matters: without it, English collapses onto a handful of
syndication hosts and the benchmark measures Yahoo rather than the web.

Each URL was fetched once with `curl`, following redirects, with a desktop Chrome user-agent and a
25-second timeout:

| Outcome | Count |
| --- | --- |
| HTTP 200 | 106 |
| HTTP 302 to a body of 112 and 138 bytes | 2 |
| HTTP 403 with a 54,611-byte challenge page | 1 |

Two of the 200s were bot walls returning a body under 500 bytes. Dropping every response under 500
bytes leaves **107 documents, 23,023,176 bytes of HTML, mean 215 KB per page**. That is the corpus
every number in §4 is computed over.

Language mix of the 107: English 8, Spanish 8, Italian 8, Portuguese 8, Russian 8, French 8,
Arabic 8, German 7, Chinese 6, Japanese 6, Korean 5, Turkish 5, Serbian 5, Indonesian 5,
Vietnamese 3, Greek 3, Polish 3, Ukrainian 3.

### 1.2 The three references, and what each is worth

There is no gold-standard body text for these 107 pages, and hand-annotating them was out of scope.
Three imperfect references were used instead, and their imperfections are stated because they bound
what the numbers mean.

**Reference 1: GDELT's own title.** The `title` field in the heartbeat is the **original-language**
headline, not the machine-translated one (verified by inspection: the Greek record carries
`Μητσοτάκης: Η ΔΕΗ είναι υγιής...`, the Japanese record carries Japanese). It is GDELT's own
extraction of the same page at roughly the same time, so agreement with it is a real signal about
title extraction, from an independent third party. It is not gold: GDELT can be wrong too.

**Reference 2: the project's own n-gram reconstruction.** `backend/src/tensionr/stories/bodies.py`
rebuilds article bodies from GDELT's Web News NGrams. All 109 sampled records carry the same
`seen_at` minute, `202609052301`, so `minutes_for` resolves to three files, of which
`20260905230100` (23,658,257 bytes) and `20260905230200` (36,085 bytes) exist and `20260905230000`
is a 404. Running the project's own `fragments`/`assemble` over those two files reconstructed
**108 of 109 URLs, median 1,800 characters**. Restricting to reconstructions of at least 400
characters leaves **92 documents** usable as a body reference. Collodon and Vestrelli validate the
algorithm at 0.75 similarity unfiltered and 0.96 at high token overlap
([doi.org/10.3390/bdcc10020045](https://doi.org/10.3390/bdcc10020045)), so this reference is noisy
by construction, and it is whitespace-tokenised, which makes it near-useless for Chinese and
Japanese. It is nonetheless the most project-relevant reference available, because it is exactly the
text the pipeline already works with.

**Reference 3: the full page text.** `inscriptis` with no boilerplate removal gives the total
extractable text of the page. The ratio of an extractor's output to that is a boilerplate-retention
measure, not an accuracy measure, but it separates "extracted the article" from "extracted the
article plus the nav bar".

**What none of these can do** is tell you whether an extractor silently truncated a long article, or
reordered paragraphs, or included the comment thread. Token-level F1 against a noisy reference does
not catch ordering errors. For accuracy in the strict sense, §3 relies on the published benchmarks,
with their conflicts of interest stated.

---

## 2. Maintenance and licence, read from the repositories

Every licence below was read via the GitHub licence API, which returns the file itself, not a guess.
Release dates come from the PyPI JSON API. Commit counts are on the default branch, counted with
`gh api`, over the 12 and 3 months to 2026-09-06.

| Library | Repo | Licence (from the file) | Latest release | Commits, 12mo | Commits, 3mo | Verdict |
| --- | --- | --- | --- | ---: | ---: | --- |
| **trafilatura 2.2.0** | `adbar/trafilatura` | **Apache-2.0** | 2026-07-31 | 52 | 41 | **Healthy, accelerating** |
| **resiliparse 1.0.9** | `chatnoir-eu/chatnoir-resiliparse` | **Apache-2.0** | 2026-07-20 | 605 | 89 | **Healthy, very active** |
| **inscriptis 2.7.4** | `weblyzard/inscriptis` | **Apache-2.0** | 2026-08-10 | 108 | 78 | Healthy (not an article extractor) |
| **newspaper4k 0.9.6** | `AndyTheFactory/newspaper4k` | **MIT** | 2026-07-19 | 169 | 26 | Healthy; 135 open issues |
| **readability-lxml 0.9** | `buriy/python-readability` | **Apache-2.0** | 2026-08-27 | 11 | 9 | Alive, low-volume, just released after 15 months |
| **goose3 3.1.22** | `goose3/goose3` | **Apache-2.0** | 2026-07-23 | 25 | 4 | Alive, slow |
| **htmldate 1.10.0** | `adbar/htmldate` | **Apache-2.0** | 2026-06-01 | 8 | 3 | Alive (dates only) |
| **news-please 1.6.16** | `fhamborg/news-please` | **Apache-2.0** | 2025-09-21 | 5 | 0 | **Coasting.** No commit since 2026-04-14 |
| **jusText 3.0.2** | `miso-belica/jusText` | **BSD-2-Clause** | 2025-02-25 | 1 | 1 | **Effectively frozen.** One commit in a year |
| **GNE 0.4.3** | `kingname/GeneralNewsExtractor` | **GPL-3.0** | 2026-03-08 | 13 | 0 | Alive, but see the licence |
| **magic-html 0.1.8** | `opendatalab/magic-html` | **Apache-2.0** | 2026-06-28 | 3 | 0 | Barely maintained |
| **boilerpy3 1.0.7** | `jmriebold/BoilerPy3` | Apache-2.0 (file text; GitHub reports `NOASSERTION`) | 2023-11-01 | **0** | 0 | **Frozen since 2023-11-01** |
| **newspaper3k 0.2.8** | `codelucas/newspaper` | MIT | **2018-09-28** | 14 | 4 | **Dead.** See §2.1 |
| **go-readability** | `go-shiori/go-readability` | MIT | none | 1 | 0 | **Archived and deprecated.** See §2.2 |
| **ReadabiliPy 0.3.0** | `alan-turing-institute/ReadabiliPy` | MIT | 2024-12-02 | 0 | 0 | Dormant |
| **extractnet 2.0.7** | `currentslab/extractnet` | MIT | 2022-11-06 | 0 | 0 | Dead |
| **dragnet 2.0.4** | `dragnet-org/dragnet` | MIT | 2019-04-16 | 0 | 0 | **Dead.** Last commit 2021-05-09 |

Three licences deserve a note. **GNE is GPL-3.0**, which is a real constraint on a project that
ships its own source: linking it into `backend/` would put the pipeline under GPL. Every other live
option is Apache-2.0, MIT or BSD-2-Clause. **BoilerPy3's licence file is not a bare Apache-2.0
text**, which is why GitHub classifies it `NOASSERTION`; the file opens "The author licenses this
file to You under the Apache License, Version 2.0", inherited from Kohlschütter's boilerpipe.

### 2.1 newspaper3k is dead, and the commit graph hides it

`codelucas/newspaper` shows 14 commits in the last 12 months and a `pushed_at` of 2026-08-31, which
on a dashboard reads as alive. It is not. Reading the log:

```
2026-08-31  adjust github ad ordering, add new one
2026-08-09  add Novada proxy
2026-07-21  remove webshare
2026-05-13  add swiftproxy
2026-04-16  webshare proxy
2025-11-24  remove thordata advert from readme
```

Every one is a README edit rotating paid proxy-vendor advertising. Restricting the log to the
`newspaper/` package directory, **the last commit is 2020-06-22, "Dropping python 3.4 support"**, and
the three before it are 2019 stopword-list contributions. The last PyPI release is **2018-09-28**.
The maintained successor is `newspaper4k`, a fork carrying the same MIT text and the same
`Copyright (c) 2013 Lucas Ou-Yang`.

### 2.2 go-readability is archived and points somewhere else

`go-shiori/go-readability` is `archived: true`, and its README carries the notice verbatim:

> This package is deprecated in favor of
> [codeberg.org/readeck/go-readability/v2](https://codeberg.org/readeck/go-readability/src/branch/v2).

The Codeberg fork is live (last commits 2026-06, MIT, 17 stars) and tracks Readability.js v0.6 where
the archived package tracks v0.5.0. Anything citing `go-shiori/go-readability` as a current option is
citing a dead repository. Note also that the Go route costs this project a second toolchain in CI
for no measured accuracy gain, so it is listed for completeness rather than as a candidate.

---

## 3. The published accuracy numbers, and who ran them

There are exactly three benchmarks with reproducible numbers over a non-trivial corpus. **Two of the
three were run by the author of a tool that appears in the table.** All three are effectively
monolingual.

### 3.1 Trafilatura's own evaluation

Source: [trafilatura.readthedocs.io/en/latest/evaluation.html](https://trafilatura.readthedocs.io/en/latest/evaluation.html),
results block dated **2026-08-04**, 990 documents, 2,951 text and 2,966 boilerplate segments,
Python 3.13. **Run by Adrien Barbaresi, the author of trafilatura, on a corpus he assembled, with a
metric he designed.**

| Package | Precision | Recall | Accuracy | F-score | Time vs baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| html2text 2025.4.15 | 0.525 | 0.900 | 0.544 | 0.663 | 2.8x |
| raw HTML | 0.528 | 0.906 | 0.549 | 0.667 | 0.03x |
| beautifulsoup4 4.15.0 | 0.532 | 0.980 | 0.561 | 0.690 | 2.1x |
| html_text 0.7.1 | 0.531 | 0.988 | 0.559 | 0.691 | 0.7x |
| inscriptis 2.7.4 | 0.534 | 0.991 | 0.564 | 0.694 | 1.1x |
| newspaper4k 0.9.6 | 0.878 | 0.736 | 0.817 | 0.801 | 6.6x |
| boilerpy3 1.0.7 (article) | 0.818 | 0.796 | 0.810 | 0.807 | 1.6x |
| goose3 3.1.22 | **0.936** | 0.714 | 0.833 | 0.810 | 10.2x |
| resiliparse 1.0.9 | 0.705 | 0.955 | 0.778 | 0.811 | **0.3x** |
| baseline (text markup) | 0.767 | 0.869 | 0.803 | 0.815 | 1x |
| readability-lxml 0.8.4.1 | 0.898 | 0.764 | 0.839 | 0.826 | 2.6x |
| news-please 1.6.16 | 0.932 | 0.758 | 0.852 | 0.836 | **20.5x** |
| justext 3.0.2 (custom) | 0.864 | 0.859 | 0.862 | 0.862 | 2.3x |
| magic-html 0.1.8 | 0.887 | 0.891 | 0.889 | 0.889 | 3.5x |
| trafilatura 2.2.0 (recall) | 0.899 | 0.939 | 0.917 | 0.918 | 2.1x |
| trafilatura 2.2.0 (precision) | 0.925 | 0.915 | 0.921 | 0.920 | 3.2x |
| **trafilatura 2.2.0 (standard)** | 0.906 | **0.943** | **0.923** | **0.924** | 3.2x |

Three things about this table that a citation usually drops.

**It is a German corpus.** The docs say documents are "selected from large collections of web pages
in German" with 20-30% other languages added. I downloaded `tests/evaldata.json` myself
(883,683 bytes, **990 entries, 934 distinct hosts**) and counted TLDs: **`.de` 438, `.com` 240,
`.org` 55, `.ch` 43, `.at` 37, `.pl` 18, `.fr` 13, `.it` 5**. That is 518 German-speaking TLDs, 52%
of the corpus, before counting the German-language `.com` and `.org` hosts.

**It is not full-text comparison.** Each entry is a handful of hand-picked strings that must and must
not appear. A real entry, read from the file:

```json
{"file": "die-partei.net.luebeck.html",
 "with": ["Die GEMA dreht völlig am Zeiger!", "http://www.openpetition.de"],
 "without": ["31. Mai", "Impressum", "Steuerdarling"]}
```

Roughly three `with` and three `without` segments per page, deliberately placed where errors happen.
The repository's own `tests/README.rst` says the evaluation "does not probe for duplicate segments"
and does not check "whether the extracted segments are in the right order". These numbers are
therefore not comparable to §3.2's n-gram F1 or §3.3's ROUGE.

**The "Diff." column is a ratio, not a time.** Trafilatura publishes no absolute milliseconds
anywhere. §4.4 supplies them.

### 3.2 The Zyte / Scrapinghub benchmark

Source: [github.com/scrapinghub/article-extraction-benchmark](https://github.com/scrapinghub/article-extraction-benchmark).
**The repository is archived** (`archived: true`, last push 2026-05-29). The original 2019 paper was
written by Konstantin Lopukhin at Scrapinghub, a company that sells the commercial extractor that
tops its own table.

I downloaded `ground-truth.json` myself: **181 pages, 126 distinct hosts, 11 TLDs**, distributed
`.com` 149, `.org` 8, `.br` 6, `.uk` 6, `.ru` 3, `.ca`/`.kr`/`.it` 2 each, `.in`/`.info`/`.net` 1
each. It is an English corpus, and the paper says so: the Google News seeds were pulled with
"Language and region" set to English (United States).

Current README figures, F1 with bootstrap standard deviation over the 181 pages:

| Library | Version | F1 | Precision | Recall |
| --- | --- | ---: | ---: | ---: |
| rs_trafilatura (Rust) | 9261e08 | **0.970 ± 0.004** | 0.951 | 0.990 |
| go_trafilatura | ae7ea06 | 0.960 ± 0.007 | 0.940 | 0.980 |
| **trafilatura** | 2.0.0 | **0.958 ± 0.006** | 0.938 | 0.978 |
| newspaper4k | 0.9.3.1 | 0.949 ± 0.008 | 0.964 | 0.934 |
| news_please | 1.6.16 | 0.948 ± 0.008 | 0.964 | 0.933 |
| readability_js | 0.6.0 | 0.947 ± 0.005 | 0.914 | 0.982 |
| readability-lxml | 0.8.4.1 | 0.922 ± 0.013 | 0.913 | 0.931 |
| goose3 | 3.1.20 | 0.896 ± 0.015 | 0.940 | 0.856 |
| justext | 3.0.2 | 0.804 ± 0.018 | 0.858 | 0.756 |
| boilerpipe_rs | 0.6.0 | 0.739 ± 0.022 | 0.761 | 0.717 |
| inscriptis | 2.6.0 | 0.679 ± 0.015 | 0.517 | 0.992 |
| beautifulsoup | 4.13.5 | 0.665 ± 0.015 | 0.499 | 0.994 |

The 2019 commercial numbers survive in a separate historical block, labelled `Nov 2019`:
**AutoExtract 0.970 ± 0.005, Diffbot 0.951 ± 0.010, newspaper3k 0.912, dragnet 0.907**. Two
disclosures matter. The 2019 paper states that the commercial services were given the
browser-rendered page while the open-source libraries got bare HTML, which is not a like-for-like
comparison. And **trafilatura's entry was contributed by trafilatura's own author** (PR #4, `adbar`,
2020-07-15), which the README says out loud. The practical consequence today is that the open-source
top of the table has caught up with the 2019 commercial number on the same corpus.

The benchmark has **no timing code at all**. It measures quality only.

### 3.3 Bevendorff et al., SIGIR 2023

"An Empirical Comparison of Web Content Extraction Algorithms", DOI
[10.1145/3539618.3591920](https://doi.org/10.1145/3539618.3591920), code and data at
[github.com/chatnoir-eu/web-content-extraction-benchmark](https://github.com/chatnoir-eu/web-content-extraction-benchmark).
3,985 pages assembled by merging eight pre-existing datasets (Dragnet 1,379, CleanEval 738, CETD 700,
L3S-GN1 621, Scrapinghub 181, Google-Trends-2017 180, Readability 115, CleanPortalEval 71).

Macro mean ROUGE-LSum F1, ranked: ensembles 0.885-0.899, **Trafilatura 0.883, Readability 0.861,
Resiliparse 0.859, DOM Distiller 0.858**, Web2Text 0.841, Boilerpipe 0.834, Dragnet 0.823,
Newspaper3k 0.816, news-please 0.815, Goose3 0.810, BoilerNet 0.798, ExtractNet 0.791,
jusText 0.759, and the naive baselines (lxml Cleaner, html_text, BS4, inscriptis) 0.664-0.717.

Three caveats the paper itself supplies. The corpus is **English-centric by the authors' own
description**, and the Chinese CleanEval set was deliberately omitted. The pages are old: CleanEval
dates from 2007, and the paper concedes "the majority of the web pages contained are rather old and
the web has changed quite a bit". And the versions tested are 2023 versions: trafilatura ~1.4.1
against 2.2.0 today.

**The conflict of interest here runs the other way, which is worth saying.** Resiliparse is written
by the paper's first author, disclosed once in §4.1 body text and nowhere in the abstract or
conclusion. But the declared winners are Readability and Trafilatura, not Resiliparse, which
substantially defuses it.

The paper's own conclusion is the useful one: on **low-complexity pages the naive baselines beat
every real extractor** (html_text 0.928, BS4 0.922, against Trafilatura 0.865), and on
**high-complexity pages everything degrades together** (Readability 0.780, Trafilatura 0.777,
Resiliparse 0.746, jusText 0.605). There is no one-size-fits-all extractor.

The paper has **no runtime table, no pages-per-second figure and no hardware spec**. Any claim that
it shows Resiliparse is fast is unsupported by it.

### 3.4 The only multilingual evaluation, and it is from 2011

Barbaresi and Lejeune, "Out-of-the-Box and Into the Ditch? Multilingual Evaluation of Generic Text
Extraction Tools", 12th Web as Corpus Workshop at LREC 2020,
[aclanthology.org/2020.wac-1.2.pdf](https://aclanthology.org/2020.wac-1.2.pdf). Corpus: the DAnIEL
corpus, **1,694 documents in Chinese, English, Greek, Polish and Russian**, collected in 2011 and
2012, available on request rather than openly released.

F1 by language, from the paper's Tables 10-14:

| Tool | English | Greek | Polish | Russian | Chinese |
| --- | ---: | ---: | ---: | ---: | ---: |
| Newspaper3k | **91.32** | **5.58** | 73.86 | **5.14** | 19.17 |
| Goose3 | 90.69 | **2.98** | 74.84 | 40.24 | 20.60 |
| news-please | 88.91 | 65.07 | 83.13 | 42.64 | 13.31 |
| Dragnet | 88.78 | 43.82 | 79.79 | 50.94 | 44.53 |
| Readability | 87.16 | 86.62 | 79.23 | 74.27 | 42.36 |
| BoilerPy3 (article) | 87.00 | 74.63 | **84.20** | 69.31 | **63.30** |
| jusText | 84.86 | **88.80** | 82.47 | **76.29** | 19.19 |
| Inscriptis | 45.84 | 50.66 | 43.28 | 32.53 | 12.97 |

**Newspaper3k scores 91.3 on English and 5.6 on Greek. Goose3 scores 90.7 on English and 2.98 on
Greek.** The paper's own conclusion: "one cannot rely on results evaluated solely on English to draw
conclusions on the efficiency of a tool in real-world multilingual settings."

Trafilatura is **absent** from this paper, which makes it the cleanest of the set on the
conflict-of-interest axis. It appears in the companion four-page demo paper, Lejeune and Barbaresi,
"Bien choisir son outil d'extraction de contenu à partir du Web", JEP/TALN/RÉCITAL 2020,
[hal.archives-ouvertes.fr/hal-02768510v3](https://hal.archives-ouvertes.fr/hal-02768510v3/document),
on the same corpus. That is the paper trafilatura's docs cite as "best overall tool", and the margin
is thinner than the citation suggests: **Trafilatura 75.69 macro against Readability 74.62, while
losing to Readability on Greek, English, Polish and Russian individually.** Its entire margin comes
from Chinese (69.22 against 55.20), where BoilerPy3 beats them both at 74.91.

That paper is also one of the only sources in the field with a real wall-clock table: 1,694
documents on a laptop, Inscriptis 19.7 s, Dragnet 24.0 s, BoilerPy3 39.8 s, Readability 56.8 s,
Newspaper3k 105.5 s, Trafilatura 109.9 s, Goose3 191.3 s, jusText 322.0 s, **news-please 3,755.6 s**.

### 3.5 The conflict-of-interest ledger

| Benchmark | Run by | Their tool in it | Did it win | Read it as |
| --- | --- | --- | --- | --- |
| trafilatura evaluation page | Barbaresi, trafilatura's author | Yes, 4 configurations | **Yes, top 4 rows** | A self-evaluation on a self-built German corpus with a self-designed segment metric. The single least independent number set in the field, and the most cited. |
| Zyte 2019 paper | Lopukhin, Scrapinghub, which sold AutoExtract | Yes | **Yes, F1 0.970** | A vendor benchmark. Mitigated by releasing corpus, ground truth and scripts, and by disclosing that only the commercial services got rendered pages. |
| Zyte repo, current table | Outside contributors; repo archived | Commercial rows moved to a dated historical block | n/a | More independent now, but trafilatura's row was contributed by trafilatura's author. |
| Bevendorff et al. 2023 | Bevendorff, Resiliparse's author | Yes | **No.** Readability and Trafilatura declared winners | Disclosed once in body text. Anti-self-serving, which largely defuses it. |
| Barbaresi and Lejeune, WAC-XII 2020 | Barbaresi and Lejeune | **No, trafilatura is absent** | n/a | Cleanest on COI. Corpus is Lejeune's own, and it is from 2011-2012. |
| Lejeune and Barbaresi, TALN 2020 | Same two | **Yes** | Yes, by 1.07 macro points while losing 4 of 5 languages | A self-evaluation in a 4-page demo format that hides how thin the win is. |

---

## 4. What I measured on this project's own corpus

Everything in this section is my own measurement over the 107 documents of §1.1, one pass, one
process, one thread, on the machine named at the top.

### 4.1 Coverage: did anything come out at all

"Body" means at least 200 characters of extracted text.

| Library | Body, of 107 | Median chars | Title | Date | Author | Language |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **trafilatura 2.2.0** (single call, `output_format="json", with_metadata=True`) | **103 (96.3%)** | 2,351 | **104** | **103** | 69 | no |
| trafilatura 2.2.0 (`favor_recall=True`, body only) | 104 | 2,463 | n/a | n/a | n/a | no |
| **resiliparse 1.0.9** (`main_content=True`) | **104** | 2,989 | no | no | no | no |
| **readability-lxml 0.9** | 98 | 2,103 | **107** | no | no | no |
| **boilerpy3 1.0.7** (article) | 101 | 2,294 | no | no | no | no |
| **newspaper4k 0.9.6**, default install | 79 | 1,833 | 86 | 72 | 62 | no |
| **newspaper4k 0.9.6** + `nltk`, `tinysegmenter`, `jieba` | **96** | 1,907 | **105** | 88 | **77** | no |
| **news-please 1.6.16**, default install | 79 | 1,823 | 86 | 77 | 62 | **87** |
| **jusText 3.0.2** | 86 | 2,100 | no | no | no | no |
| **goose3 3.1.22** | 80 | 1,430 | **107** | 81 | 74 | no |
| htmldate 1.10.0 (dates only) | n/a | n/a | no | 104 | no | no |
| inscriptis 2.7.4 (control, no boilerplate removal) | 104 | 9,104 | no | no | no | no |

**The single largest effect in this table is an installation default.** `newspaper4k` and
`news-please` both raise `ImportError` on **20 of 107 documents (18.7%)** out of the box:

```
7  ImportError: nltk is required for Arabic text processing
6  ImportError: You must install tinysegmenter before using the Japanese tokenizer
5  ImportError: nltk is required for Korean text processing
2  ImportError: You must install jieba before using the Chinese tokenizer
```

That is Arabic, Japanese, Korean and Chinese failing hard, not degrading. Installing
`newspaper4k[nlp]`, `tinysegmenter` and `jieba` and downloading the NLTK `punkt` data lifts
newspaper4k from 79 to 96 bodies. `news-please` was tested at its default and was not re-tested with
the extras, so its 79 is a default-install number, not a ceiling.

### 4.2 Coverage per language

Body count, of the documents sampled for that language.

| Language | n | trafilatura | newspaper4k+extras | readability | boilerpy3 | resiliparse | jusText | goose3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| English | 8 | 7 | 7 | 7 | 7 | 6 | 6 | 6 |
| Spanish | 8 | 8 | 8 | 6 | 8 | 8 | 8 | 8 |
| Italian | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 7 |
| Portuguese | 8 | 7 | 7 | 8 | 8 | 8 | 8 | 7 |
| Russian | 8 | 8 | 8 | 7 | 8 | 8 | 8 | 8 |
| French | 8 | 7 | 7 | 7 | 7 | 8 | 7 | 7 |
| **Arabic** | 8 | **8** | 6 | 7 | 8 | 8 | 7 | 7 |
| German | 7 | 7 | 7 | 6 | 7 | 7 | 7 | 6 |
| **Chinese** | 6 | **5** | 2 | 5 | 3 | 5 | **0** | **0** |
| **Japanese** | 6 | **6** | 6 | 5 | 6 | 6 | **0** | **0** |
| **Korean** | 5 | **5** | 4 | 5 | 4 | 5 | **1** | **0** |
| Turkish | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 5 |
| Serbian | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 2 |
| Indonesian | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| Vietnamese | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| Greek | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 3 |
| Polish | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| Ukrainian | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |

**jusText and goose3 return nothing on CJK: 1 body out of 17 for jusText, 0 out of 17 for goose3.**
For jusText this is structural rather than a bug: it is a stopword-density algorithm, it ships no
Chinese stoplist, and CJK text has no whitespace-delimited stopwords to count. Six of the 107
documents were passed an empty stoplist for exactly that reason. Goose3's failure has no such
excuse, and it is the same failure the 2020 DAnIEL evaluation recorded at F1 3.06 on Chinese.

Note that the CJK gap in §3's benchmarks is not visible at all: the trafilatura corpus contains
about five Chinese documents and the Bevendorff corpus deliberately excludes the Chinese set.

### 4.3 Body agreement against the n-gram reconstruction

92 documents with at least 400 characters reconstructed. Recall is the share of the reconstruction's
tokens present in the extractor's output; F1 additionally penalises retained boilerplate. The
reference is noisy and CJK-hostile, so read the ordering, not the absolute values.

| Library | Mean recall | Median recall | Recall ≥ 0.9 | **Mean F1** | Boilerplate ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| **trafilatura (standard)** | 0.897 | 0.972 | 74 | **0.816** | 0.276 |
| trafilatura (`favor_recall`) | 0.908 | 0.972 | 76 | **0.816** | n/a |
| boilerpy3 | 0.873 | 0.975 | 74 | 0.792 | 0.270 |
| readability-lxml | 0.839 | 0.965 | 71 | 0.787 | 0.294 |
| newspaper4k + extras | 0.808 | 0.942 | 61 | 0.776 | 0.236 |
| goose3 | 0.706 | 0.913 | 48 | 0.715 | **0.214** |
| **resiliparse** | **0.896** | **0.980** | **80** | 0.707 | **0.388** |
| jusText | 0.771 | 0.949 | 57 | 0.702 | 0.257 |
| inscriptis (control) | 0.946 | 0.989 | 87 | 0.495 | 1.000 |

"Boilerplate ratio" is median extracted characters divided by full-page text characters. It explains
the resiliparse row: **resiliparse has the second-highest recall in the table and the second-lowest
F1**, because its `main_content` heuristic keeps 38.8% of the page against trafilatura's 27.6%. It is
finding the article and bringing the furniture. That is exactly the shape trafilatura's own
evaluation reports for it (precision 0.705, recall 0.955), measured here independently on a
different corpus with a different metric, which is a useful corroboration of both.

Pairwise token-F1 between extractors on the same 107 documents, for orientation: trafilatura agrees
with readability at 0.89 and with newspaper4k at 0.87; resiliparse is the outlier, agreeing with
everything else at 0.72 to 0.82.

Per-language mean recall shows the same CJK cliff as §4.2, and adds one thing: **on Korean,
trafilatura 0.93, readability 0.96 and resiliparse 0.97 all work, while jusText scores 0.03 and
goose3 scores 0.00.**

### 4.4 Field recovery: title, date, author, language

**Title**, scored as token F1 against GDELT's own extraction of the same headline:

| Library | Titles returned | Mean F1 | F1 ≥ 0.8 | Exact |
| --- | ---: | ---: | ---: | ---: |
| goose3 | 107 | **0.934** | **98** | **82** |
| readability-lxml | 107 | 0.913 | 91 | 76 |
| trafilatura (`extract_metadata`) | 107 | 0.913 | 95 | 68 |
| trafilatura (single call) | 104 | 0.894 | 93 | 66 |
| newspaper4k + extras | 105 | 0.897 | 89 | **79** |
| newspaper4k, default install | 86 | 0.731 | 72 | 64 |

Titles are the easy field. Everything that tries gets roughly nine tenths of it, because everything
falls back to `<title>` and `og:title`.

**Publication date.** There is no gold date, so the test is plausibility: does the extracted date
land within one day of the moment GDELT observed the article. For same-day news this is a weak but
real check.

| Library | Dates returned | Within 1 day | Share of documents |
| --- | ---: | ---: | ---: |
| **trafilatura** | 103 | 95 | **88.8%** |
| **htmldate 1.10.0** alone | 104 | 96 | **89.7%** |
| newspaper4k + extras | 88 | 84 | 78.5% |
| goose3 | 76 | 72 | 67.3% |
| readability-lxml | 0 | n/a | 0% |
| jusText, boilerpy3, resiliparse | 0 | n/a | 0% |

Trafilatura's date figures are htmldate's, because trafilatura calls htmldate. That is the honest
reading: **the state of the art in publication-date extraction is one 156-star Apache-2.0 library by
the same author**, and it is the only component here with no competitor at all. If trafilatura is
rejected, htmldate still has to be adopted separately.

**Author** is the weakest field everywhere: newspaper4k 77 of 107 (72%), goose3 74, trafilatura 69,
news-please 62. Nothing was verified against a reference, so these are recovery rates and not
accuracy rates. Author names are also the field most likely to be a byline template ("Redazione",
"Di Giorgio E Caterina Calabrese") rather than a person.

**Language.** Only `news-please` returns a language field at all (87 of 107). Trafilatura can filter
by `target_language` but does not report a detected language without an optional `py3langid`
install. This barely matters for this project: **the GDELT record already carries `lang`**, and it
carried 36 distinct values in the single heartbeat sampled. Detecting language from the extracted
body is a redundant step here.

### 4.5 Throughput per core

Wall clock, single thread, over the 107 documents totalling 23.0 MB of HTML.

| Library | ms/doc | docs/s/core | MB/s/core | Core-hours per 100k docs |
| --- | ---: | ---: | ---: | ---: |
| **resiliparse** (body only) | **17.6** | **56.8** | **12.21** | **0.49** |
| inscriptis (control) | 72.4 | 13.8 | 2.97 | 2.0 |
| jusText | 101.5 | 9.9 | 2.12 | 2.8 |
| htmldate (dates only) | 144.3 | 6.9 | 1.49 | 4.0 |
| boilerpy3 | 146.5 | 6.8 | 1.47 | 4.1 |
| trafilatura (`favor_recall`, body only) | 164.2 | 6.1 | 1.31 | 4.6 |
| readability-lxml | 198.5 | 5.0 | 1.08 | 5.5 |
| **trafilatura (body + title + date + author, single call)** | **289.8** | **3.45** | **0.74** | **8.1** |
| goose3 | 608.8 | 1.6 | 0.35 | 17 |
| newspaper4k + extras | 628.0 | 1.6 | 0.34 | 18 |
| news-please | 652.8 | 1.5 | 0.33 | 19 |

Two notes. **Calling `extract()` and `extract_metadata()` separately costs 531 ms/doc; the single
`extract(output_format="json", with_metadata=True)` call costs 290 ms** for the same fields. That
2x is free and easy to miss.

And the 20.5x that trafilatura's evaluation reports for news-please, and the 190x that the DAnIEL
paper reports, do not reproduce here: I measure news-please at **2.3x trafilatura's single-call
path**, not 20x. The difference is almost certainly that this benchmark feeds pre-fetched HTML to
`NewsPlease.from_html()` rather than letting news-please run its own Scrapy crawler. **news-please's
reputation for slowness is a property of its crawler, not of its extractor.**

Translating to the runner: a 4-core `ubuntu-latest` job extracting **100,000 articles with
trafilatura's full-metadata path needs about 2.0 hours of wall clock**, inside the 6-hour job limit
with room to spare. Resiliparse would need 7 minutes. On this axis the choice is not close to
binding.

### 4.6 Does any of this need a headless browser

**No, on this corpus.** Of the 107 fetched documents, **exactly 2 yielded no body from any
extractor**: a Canadian local paper serving a 1,118-byte bot wall, and a `baijiahao.baidu.com` page
serving 1,488 bytes. Both were 200 responses with almost no HTML, which is a fetch-layer problem, not
a rendering problem. A third and fourth page (a phpBB forum thread and a `leral.net` article) defeated
trafilatura specifically but were extracted by others.

**So the ceiling a headless browser could buy on this sample is 2 pages of 107, 1.9%,** and at least
one of those two is a bot challenge that a browser would also have to solve. That is a strong result
against adding Playwright to this pipeline, and it is worth stating that it contradicts the usual
folk claim about modern news sites. The reason is structural: news publishers want to be in Google
News, Google News requires server-rendered HTML or a sitemap, so the article body is in the initial
response.

The caveat is that the sample is 109 URLs fetched from an Italian domestic IP, not from an Azure
GitHub Actions egress IP, which is a materially more blocked address space. §11 records this.

---

## 5. Ranked shortlist for Question 1

**1. trafilatura 2.2.0, Apache-2.0.** Best measured body F1 here (0.816), highest coverage
(96.3%, and the only library at 5 of 6 Chinese and 5 of 5 Korean), best date recovery (88.8%),
second-best title, and the only library that returns body, title, date and author from one call.
Actively developed (41 commits in 3 months). The trade-off is honest: **it is 3.45 docs/s/core with
metadata, about 17x slower than resiliparse**, and the benchmark most often cited in its favour is
its author's own. Every independent benchmark also puts it first or second, which is why it still
ranks first.

**2. resiliparse 1.0.9, Apache-2.0.** The speed option, and it is not a small margin: **17.6 ms/doc,
12.2 MB/s, 56.8 docs/s/core**. Highest raw recall of the article body (0.896, median 0.980), CJK-safe,
and the healthiest repository in the set. The trade-off is precision: it keeps 38.8% of the page
against trafilatura's 27.6%, giving the second-lowest F1 in §4.3, and it returns **no title, no
date, no author**. Choose it when the downstream consumer tolerates furniture, or pair it with
htmldate and an `og:title` read.

**3. readability-lxml 0.9, Apache-2.0.** The dependable middle. F1 0.787, coverage 91.6%, titles on
107 of 107, 5.0 docs/s/core, CJK-safe, and a fresh release after a 15-month gap. Its real
recommendation is external: it is the tool Bevendorff et al. rank best on median and robustness, and
the only one that beat trafilatura on four of five languages in the DAnIEL evaluation. It gives no
date and no author, so htmldate is mandatory alongside it.

**4. newspaper4k 0.9.6, MIT.** The best author recovery measured here (77 of 107) and good titles,
and the only maintained descendant of newspaper3k. Two trade-offs, both real. **Out of the box it
throws `ImportError` on 18.7% of this corpus** and needs `newspaper4k[nlp]`, `tinysegmenter`, `jieba`
and an NLTK data download to reach 96 bodies. And it is 1.6 docs/s/core, the slowest tier. 135 open
issues.

**5. boilerpy3 1.0.7.** A genuine surprise: F1 0.792, second only to trafilatura, at 6.8 docs/s/core,
and it was the strongest tool on Chinese in the 2020 multilingual evaluation (63.30 where everything
else scored under 45). Against that, **zero commits since 2023-11-01**, no metadata of any kind, and
a licence file GitHub cannot classify. Usable, unmaintained.

**6. news-please 1.6.16, Apache-2.0.** Returns the most fields of anything here, including a language
field nothing else provides, and its extractor is **not** the 20x-slow monster the published tables
suggest when you feed it HTML directly (measured 2.3x trafilatura). But it has 5 commits in 12 months
and none since April 2026, it inherits newspaper's CJK `ImportError` at the default install, and it
drags Scrapy, Elasticsearch clients and a Hadoop-era dependency tree into the lockfile for an
extractor that trafilatura beats.

**7. jusText 3.0.2, BSD-2-Clause.** One commit in 12 months. F1 0.702. **1 body out of 17 CJK
documents.** Its stopword-density design cannot work on languages without whitespace-delimited
stopwords, and there is no version of this project where that is acceptable.

**8. goose3 3.1.22, Apache-2.0.** Best titles in the sample (mean F1 0.934), and nothing else.
**0 of 17 CJK bodies**, lowest recall (0.706), 1.6 docs/s/core, median body 1,430 characters against
trafilatura's 2,351, which is the truncation the 2020 evaluation measured as 2.98 F1 on Greek.

**Not options.** `newspaper3k` (dead since 2020, README-only commits), `dragnet` (dead 2021),
`extractnet` (dead 2022), `ReadabiliPy` (dormant, and 248x baseline time in the one benchmark that
timed it), `go-shiori/go-readability` (archived and self-deprecated; the live fork is at
`codeberg.org/readeck/go-readability/v2`), and `GNE`, which is alive and well-regarded on Chinese
news but is **GPL-3.0** and publishes no benchmark, only a README claiming "nearly 100% accuracy"
with no corpus and no metric.

**The recommendation for Part A is trafilatura plus htmldate, both Apache-2.0, one call, 290 ms/doc.**
It is also worth recording what the shortlist does *not* say: on the evidence in §3.4, the ranking
between the top four is smaller than the between-language variance, and no benchmark anywhere covers
Arabic, Turkish, Serbian, Indonesian or Vietnamese, which are five of the eighteen languages in this
project's own corpus.

---

# Part B. Free feeds to ingest alongside GDELT

## 6. The constraints, restated as tests

Every candidate below is tested against four things, and failing any one is disqualifying:

1. **Free at 100k-200k articles/day.** No credit card, no expiring trial, no "free credits".
2. **Reachable from a GitHub Actions runner over plain HTTPS.** No fixed IP allowlist, no
   browser-based OAuth.
3. **No external storage.** The runner has **14 GB of SSD** and the repository is pruning itself to a
   20-day window. Anything requiring tens of GB retained is unusable, and anything requiring tens of
   GB *transited per day* is close to it.
4. **Breadth of country-of-publication beats English depth.**

---

## 7. GDELT's other tables

Sizes below were measured with `curl` today. Note that `http://data.gdeltproject.org` 301-redirects
to HTTPS, so `-L` is required.

### 7.1 What the project already reads

`gsg_docembed`, 15-minute grid, 96 files/day. My sample slot `20260905231500` was
**4,328,972 bytes gzipped, 1,502 records, 36 languages**. A slot measured at 18:00 the same day was
7,186,212 bytes and 2,481 records. **Volume is strongly diurnal**: those two slots extrapolate to
144,000 and 238,000 articles/day respectively. Either way the feed alone is already inside the
100k-200k target.

### 7.2 GKG 2.1, and why it is a projection problem

`http://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip` plus a parallel
`.translation.gkg.csv.zip`, both 15-minute. 27 columns including `V2SOURCECOMMONNAME` (the publisher
domain), `V2ENHANCEDPERSONS`, `V2ENHANCEDORGANIZATIONS`, `V1.5TONE`, `V2.1TRANSLATIONINFO` and
`V2GCAM`. One translation file measured today carried **961 rows, 201 unique domains and 34 distinct
source languages**.

Measured daily volume: **English 0.26 GB/day compressed, translation 0.53 GB/day**, so
**15.8 GB over a 20-day window**. That fails constraint 3 outright. The size is almost entirely
`V2GCAM`, which is 2,300-plus emotional and thematic dimensions per document. Retaining a projection
(record id, date, domain, url, tone, translation info) would cut it by roughly 90%. This project has
already established that GKG joins to its clusters at 95.3% (`cross-lingual-actors.md`), so GKG is not
a new source here so much as an already-known one whose storage cost is now quantified.

### 7.3 Web News NGrams 3.0

`http://data.gdeltproject.org/gdeltv3/webngrams/{stamp}.webngrams.json.gz`. GDELT's announcement
([blog.gdeltproject.org](https://blog.gdeltproject.org/announcing-the-new-web-news-ngrams-3-0-dataset/))
says the file is "downloaded directly every minute" and covers "152 languages". **The every-minute
claim is not what is published.** Files exist only at minutes `:01, :02, :16, :17, :31, :32, :46, :47`,
which is 7 to 8 files/hour, roughly 180/day, and that pattern holds in 2024 as well as 2026, so it is
structural. My own probe is consistent: `20260905230000` is a 404 while `...230100` is 23,658,257
bytes and `...230200` is 36,085 bytes.

**3.37 GB/day compressed, 43 GB/day raw.** Retention is out of the question; fetch-on-demand and
discard, which is exactly what `bodies.py` already does, is the only viable pattern.

### 7.4 Global Frontpage Graph: dead, and confirmed

The correct path has an `alpha/` segment:
`http://data.gdeltproject.org/gdeltv3/gfg/alpha/{stamp}.LINKS.TXT.gz`. My own probe:

```
20250201120000  http=200  bytes=234789550
20260101120000  http=200  bytes=45
20260905120000  http=200  bytes=45
```

The 45 bytes are a well-formed, empty gzip carrying the correct embedded filename. Independent
probing across the decline gives the shape: 234 MB/hour in February 2025, 101 MB in March, 34 MB in
April, 8.8 MB in June, 2.3 MB in September, flapping in early October 2025 and flat at 45 bytes from
2025-10-15 onward. The gzip MTIME field on today's file decodes to 2026-09-05 12:19:41 UTC, so
**GDELT's hourly job is still running on schedule and shipping zero rows**. This will not self-heal.

This corroborates and refines the note in `pipeline-cost-audit.md` §6: the "since around October 2025"
date is right for the empty payload, but the collapse had been underway since March 2025.

### 7.5 Global Entity Graph: stopped 2026-06-18

`http://data.gdeltproject.org/gdeltv3/geg_gcnlapi/`. The master file list ends at
`20260618223100.geg-gcnlapi.json.gz`, and its `last-modified` is 2026-06-18 22:33:08 GMT. My probe:

```
20260618223100  http=200  bytes=3901
20260905120000  http=404
```

Daily file counts were healthy right to the last day (401, 421, 428, 410 for 15 to 18 June), so this
is an abrupt stop, not a wind-down. Consistent with a Google Cloud NL API credential ending. The
1.14 M-file historical archive remains fetchable. **Not a forward-looking option.**

### 7.6 The domain-to-country lookup, which is the best thing in this section

`http://data.gdeltproject.org/blog/2018-news-outlets-by-country-may2018-update/MASTER-GDELTDOMAINSBYCOUNTRY-MAY2018.TXT`
(the `-update` suffix is required; without it the URL 404s). Measured myself: **HTTP 200,
5,625,484 bytes, 189,545 lines, 3 tab-separated columns, 241 distinct countries.**

```
0-100.it	IT	Italy
0-50.ru	RS	Russia
```

I joined it against the 1,502 records of my own heartbeat slot:

| Match strategy | Records resolved | Share |
| --- | ---: | ---: |
| Exact host, after stripping `www.` | 1,414 | **94.1%** |
| Plus a parent-domain suffix walk | **1,482** | **98.7%** |

**70 distinct countries in a single 15-minute slot**: United States 469, India 96, Spain 82,
Canada 75, United Kingdom 52, Mexico 52, Argentina 51, China 50, Italy 48, Russia 35, Australia 34,
Brazil 31, Japan 24, South Korea 22, Germany 21, Turkey 21, Austria 20, Vietnam 19, Serbia 16,
Greece 14, Peru 13, and a long tail down to Malawi and New Zealand at 9.

This is a **5.6 MB file fetched once**, with zero recurring storage cost, and it converts the feed the
project already ingests into a country-attributed feed. Given that this project's whole measurement
is whether outlets in different countries name the same actor, and given that `polity-availability.md`
had to establish polity membership by hand, this is the single highest-value item in Part B. It is
also stale: the file is from May 2018, and `2020-news-outlets-by-country/` and
`2021-news-outlets-by-country/` both 404, so the 1.3% that fails to resolve is mostly outlets founded
or renamed since.

### 7.7 The Global Similarity Graph edge files, which are separate and cheap

`http://data.gdeltproject.org/gdeltv3/gsg/{stamp}.gsg.json.gz` is a **different product** from the
`gsg_docembed` files the project reads. It carries `simScore`, `simWords`, and `fromUrl`/`fromLang`/
`toUrl`/`toLang` pairs: precomputed cross-language same-story edges. Live today, measured at
177,502 / 101,580 / 112,233 bytes for three slots. It follows the ngrams cadence, not the docembed
one, at roughly 192 files/day, giving **about 25 MB/day compressed and 500 MB over a 20-day window**.

`event-clustering-multilingual-headlines.md` already identified this product as the answer to #2, so
this is a re-confirmation rather than a discovery. What is new is the storage number: **it is the only
GDELT product surveyed here that fits a 20-day GitHub-hosted window in full.**

### 7.8 Terms of use, verbatim, and one correction

From [gdeltproject.org/about.html#termsofuse](https://www.gdeltproject.org/about.html):

> The GDELT Project is an open platform for research and analysis of global society and thus all
> datasets released by the GDELT Project are available for unlimited and unrestricted use for any
> academic, commercial, or governmental use of any kind without fee.

> You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form. However,
> any use or redistribution of the data must include a citation to the GDELT Project and a link to
> this website (https://www.gdeltproject.org/).

**There is no CC BY 4.0 statement.** `gdeltproject.org/terms.html` is a 404, and the phrase "Creative
Commons" does not appear on `about.html`, `index.html`, `data.html`, or in the Data Format,
Event or GKG codebook PDFs. The licence is a bespoke two-paragraph statement that is CC-BY-like in
effect but is not a standard licence, carries no warranty or patent language, and can be revised
unilaterally. `reconstructed-text-rights.md` §6 already reads these terms correctly as covering
GDELT's datasets and being silent on the underlying articles' copyright; the correction here is only
to any description of them as CC BY 4.0.

**DOC 2.0 API rate limits are published nowhere except in the 429 body**, which reads "Please limit
requests to one every 5 seconds", and which explicitly redirects high-traffic users to the ngrams
dataset. This project measured 429 on 5 of 5 attempts; an independent probe today got 429 on 3 of 5.
Same mechanism. **1 request per 5 seconds is 17,280 requests/day**, and with a 250-record cap and no
cursor it is an enrichment endpoint, not an ingestion path. For country attribution the static file in
§7.6 is strictly better: no rate limit, no network dependency at selection time, higher coverage.

---

## 8. Everything else

### 8.1 Media Cloud's nightly URL dump

This is the only candidate in the whole survey that clears 100k-200k articles/day for free, and it is
not documented anywhere on mediacloud.org. It was found by reading the README of their open-source
`rss-fetcher` repository, which says the service "keeps a database of approximately 180K RSS and
Google news sitemap feeds" and that "Every night it generates a synthetic RSS feed with unique new
URLs".

The live host, verified by me today, needs **no key, no account and no card**:

```
https://rss-fetcher.tarbell.mediacloud.org/rss/mc-2026-09-05.rss.gz
  → HTTP 200, application/x-rss+xml, 46,983,241 bytes, 5.3 s
https://rss-fetcher.tarbell.mediacloud.org/rss/mc-2026-09-04.rss.gz  → 200, 63,578,963 bytes
https://rss-fetcher.tarbell.mediacloud.org/rss/mc-2025-09-05.rss.gz  → 200, 43,532,945 bytes
https://rss-fetcher.tarbell.mediacloud.org/rss/mc-2023-01-01.rss.gz  → 200, 18,931,898 bytes
/robots.txt → 404
```

Contents of the 2026-09-05 file, parsed by me:

| | |
| --- | ---: |
| Items | **486,092** |
| Uncompressed | 195,112,416 characters |
| Distinct hosts | **15,080** |
| Distinct TLDs | **226** |
| Two-letter country-code TLDs | **170** |
| Share of links on a ccTLD | **41.5%** |

Top TLDs after `.com` (253,715): `.de` 18,277, `.net` 17,561, `.br` 12,516, `.it` 11,291,
`.ru` 9,901, `.es` 8,636, `.fr` 8,032, `.ar` 6,459, `.uk` 6,223, `.mx` 5,959, `.ir` 5,001,
`.nl` 4,949, `.jp` 4,905, `.ua` 4,803, `.gr` 4,783, `.se` 3,944, `.tr` 3,768, `.in` 3,681,
`.rs` 3,415, `.vn` 3,348, `.az` 2,895.

Per item: `link`, `pubDate`, `domain`, `title`, and a `source` element with the originating feed URL
and Media Cloud's own feed and source ids. **No body. No language field.** Titles are real headlines:
in a random sample of 4,000, 2 were empty and 19 (0.5%) were URL-slug noise rather than a headline.

**One request per day, 47 MB, 486,000 URLs. It is one two-hundredth the bandwidth of CC-NEWS for
twice the article count.**

The trade-offs are all governance, not engineering. It is **undocumented**: `mediacloud.org/documentation/daily-rss`
is a 404 and the host is named nowhere in their public docs. There is **no SLA**, and the same
repository carries `RSS_FETCHER_USER`/`RSS_FETCHER_PASS` variables for an authenticated sibling API,
so this could be closed at any time. And their terms
([mediacloud.org/legal/media-cloud-terms-of-use](https://www.mediacloud.org/legal/media-cloud-terms-of-use),
effective 2023-05-16) say the platform "is designed for and is best fitted to academic, nonprofit, and
journalistic research and not designed for use as a commercial tool", while granting, in §2.2, that
"You may use, reproduce, distribute, and/or display any Platform Outputs, including directly copying
them" and warning in §2.3 that they cannot license third-party content. For a free, ad-free research
site that reading is favourable, but it should be confirmed with them rather than assumed.

Media Cloud's documented REST API is a different and much worse proposition for this purpose: free
and keyed without a card, but capped at **4,000 requests/week** with some endpoints at 2/minute
([mediacloud.org FAQs](https://www.mediacloud.org/documentation/faqs)), and it never returns article
text: "Due to copyright restrictions we cannot release the actual text of a story."

### 8.2 Common Crawl CC-NEWS

Live and current. `https://data.commoncrawl.org/crawl-data/CC-NEWS/2026/09/warc.paths.gz` returns 200
with a `last-modified` of 2026-09-05. My own counts: **61 files listed for 1 to 5 September 2026,
13 per day**, and **490 files for August 2026, 15.8 per day**. Each WARC is fixed at about 1.07 GB
(`content-length: 1072703705` on the file I HEADed).

**That is 13.9 to 16.9 GB/day.** The runner has 14 GB of disk. Stream-and-discard is the only option,
and there is a second, worse problem: **there is no index for CC-NEWS.** I verified this three ways.
`https://index.commoncrawl.org/collinfo.json` lists **127 collections, every one of them `CC-MAIN-*`**.
`crawl-data/CC-NEWS/2026/08/cc-index.paths.gz`, `cc-index/table/cc-news/warc/` and
`crawl-data/CC-NEWS/cc-index-table.paths.gz` all return 404. Range requests work, but with no index
there are no offsets, so you can only stream from byte zero.

Its one real advantage is breadth. A sampled 100 MiB slice yielded 34 languages with **English at
only 26%**, and hosts across Russia, Turkey, Iran, Kazakhstan, Benin, Palestine and Cuba. That is the
best multilingual profile in this survey. But it is bought at 200 times Media Cloud's bandwidth for
fewer articles, and Common Crawl's terms
([commoncrawl.org/terms-of-use](https://commoncrawl.org/terms-of-use)) are **not an open licence**:
they grant "a limited, non-assignable, non-transferable, non-sublicensable, non-exclusive, limited
license to access and use the Service", and state that by using the crawled content "YOU AGREE TO
RESPECT THE COPYRIGHTS AND OTHER APPLICABLE RIGHTS OF THIRD PARTIES". Automated bulk download is the
intended use and there is no rate limit; redistribution of article content is not granted.

### 8.3 Internet Archive

**The Wayback CDX API cannot answer a "what was published today" query**, and this is architectural,
not a quota problem. `url` is a required parameter: omitting it returns HTTP 400 with
`x-archive-wayback-runtime-error: url must be specified`. Worse, `from`/`to` do not prune the scan,
because the index is sorted by SURT key rather than time: `url=bbc.co.uk&matchType=domain` reports
92,726 pages with a 3-day date filter and 92,726 pages without one. The endpoint is also slow and
flaky (503s and 60-second timeouts observed) while `archive.org` itself answers in under a second.

The TV News Archive is genuinely international (98 stations sampled, including Polish, Russian,
German, Persian, Indonesian, Brazilian, Moroccan, Serbian and North Korean channels) but runs at about
3,660 items/day of caption text, which is 30x short and the wrong medium.

Terms: `archive.org/about/terms.php` is now a JavaScript shell, so the last readable text is a 2019
capture. It grants access "for scholarship and research purposes only" and grants no redistribution
right over archived third-party content. Their bot policy
([archive.org/developers/bots.html](https://archive.org/developers/bots.html)) requires a descriptive
User-Agent, delays between bulk requests, and honouring 429 and `Retry-After`. No numeric quota is
published.

### 8.4 Europe Media Monitor / JRC: the best coverage claim, and no usable output

EMM has moved. `https://emm.newsbrief.eu/` 301-redirects to `https://media-monitor.europa.eu/`, and
**every legacy RSS shape returns 403**, with or without a browser user-agent. `emm.newsexplorer.eu`
returns 503. `press.jrc.it` no longer resolves. And `https://medisys.newsbrief.eu/robots.txt` is
`User-agent: * / Disallow: /`, so the legacy estate is both blocked and explicitly disallowed.

The JRC's own published statistic is the largest in this document
([knowledge4policy.ec.europa.eu](https://knowledge4policy.ec.europa.eu/europe-media-monitor-emm_en)):

> The Europe Media Monitor (EMM) is a research project that continuously tracks 20,000 news websites
> and processes approximately 500,000 publicly available pages in 80 languages across 150 countries
> every day.

The new site is an Angular application whose unauthenticated API returns exactly **five story
clusters** per domain, with no article URLs anywhere in the payload and `sourceLanguage` null. The gap
between 500,000 pages ingested and 5 aggregate clusters published is total. Licence is the
Commission-wide reuse decision 2011/833/EU with CC BY 4.0 for EU-owned content, which does not extend
to the news articles themselves.

**80 languages and 150 countries, and nothing to ingest.**

### 8.5 Wikimedia

**EventStreams** is live and, contrary to expectation, workable from a short job: Wikimedia enforces
a 15-minute connection timeout but supports timestamp replay via `?since=`, with 7 to 31 days of
history, and a 6-hour backfill was measured at about 3.5 minutes of streaming. But the payload is page
edits, not news: 2.9 M events/day, 61% bot-generated, 4.7 GB/day of JSON, and the docs say the service
is "intended for use by small scale external tool developers" and "should not be used to build
production services".

**Wikimedia Enterprise** has a real free tier with no credit card, but it is 50,000 on-demand requests
per month (about 1,650/day, sixty times short), snapshots are tens of GB, and the Realtime API is
paid-only.

The **In The News** feed is English-only and returns about 6 stories a day, and the block is absent
from historical dates. There is **no machine-readable news-citation dataset**: `/citationusage/` under
`analytics.wikimedia.org/published/datasets/` is a 404, and the nearest artefact
(`one-off/html-dump-scraper-refs/`) contains reference *counts* for two wikis and no external URLs.

Practical note if any Wikimedia API is used at all: the documented rate limit is **10 requests/minute
with no User-Agent and 200/minute with a compliant one**
([mediawiki.org](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits)), a 20x difference for a
header.

**Verdict: a signal, not a source.**

### 8.6 RSS at scale

Four published registries, with their own data counted:

| Registry | Feeds | Countries | Licence | Data last changed |
| --- | ---: | ---: | --- | --- |
| `yavuz/news-feed-list-of-countries` | 1,197 raw, 992 active | **152 / 140** | **none at all** | 2026-05-29 |
| `mhus/hrafnagud-catalog-rss` | 828 | **196** | Apache-2.0 | 2026-08-29 |
| `plenaryapp/awesome-rss-feeds` | 259 country, 582 topic | 25 | CC0-1.0 | 2026-06-18 |
| `kotartemiy/newscatcher` | 4,505 | 53 | MIT | **frozen 2020-10-28** |

Probing 200 random `yavuz` feeds: **92% live**, median 24 items per poll, **median 10 items dated in
the last 24 hours**, median age of the newest item 2.3 hours. So **1,000 feeds polled hourly yields
about 20,000 articles/day**, and the deduplicated union of all four registries (6,192 feeds, 4,779
domains) yields **about 50,000/day**: roughly half the floor, before cross-source deduplication. Feed
lists decay: only 50% of the 2020 Newscatcher list is still alive.

Two flags. The best country-tagged list, `yavuz`, **has no LICENSE file**, so there is no
redistribution right in it at all. And **Google News RSS is out**: `news.google.com/robots.txt` is
`Disallow: /` with an allow-list that does not include `/rss`, and Google's terms prohibit automated
access "in violation of the machine-readable instructions on our web pages". The links are useless
anyway, being 294-character `CBMi...` redirects that bounce through `consent.google.com` and never
reach the publisher. **Bing News RSS is dead**: it returns HTTP 200 with `Content-Type:
application/xml` and an HTML body containing zero `<item>` elements.

### 8.7 Search-engine APIs: all fail

| Source | Status | Free quota | Card | Free articles/day |
| --- | --- | --- | --- | ---: |
| Brave Search API | live | $5 credit at $5/1,000 requests | **yes** | ~1,650 |
| Bing Search API | **retired 2025-08-11** | none | n/a | 0 |
| Marginalia | live | shared throttled key | no | ~0 |
| Mojeek | live | "get in touch", no published number | n/a | 0 |
| SearXNG self-hosted | runnable | n/a | no | ~0, CAPTCHA |

**Brave fails on licence before it fails on volume.** Its terms forbid you to "store, cache, or create
a database of Search Results... other than transient storage", which is precisely what this project
does. **Bing is retired**: Microsoft's own page states "Public Bing Search and Bing Custom Search APIs
were retired on 11th August 2025", and the successor returns an LLM answer rather than the tool output.
**Marginalia says it is the wrong tool** in its own words: "If you are looking for facts you can trust,
this is almost certainly the wrong tool", and it is CC-BY-NC-SA. **SearXNG in Actions would be
scraping Google and Bing from a shared Azure IP against `Disallow: /search` in both robots files.**

### 8.8 Commercial free tiers: all fail by one to three orders of magnitude

| Provider | Free ceiling | Shortfall vs 100k/day | Card | Disqualifying term |
| --- | --- | ---: | --- | --- |
| Event Registry / newsapi.ai | 200,000 articles **once, ever** | infinite after day 1 | no | tokens "don't renew"; free use may not produce value "even indirectly" |
| NewsAPI.org | 10,000/day, 24h delayed | 10-20x | no | "cannot be used in a staging or production environment (including internally)" |
| Currents API | 5,000/day | 20-40x | no | may not "create permanent copies of, scrape, build databases of such data" |
| GNews | 1,000/day, 12h delayed | 100-200x | no | free tier not for commercial projects |
| Webz.io free datasets | ~143/day | ~700x | no | no redistribution right; `"license": null` |
| Aylien / Quantexa | **NXDOMAIN** | total | n/a | the service no longer exists |

### 8.9 Hugging Face

**No dataset on the Hub is a daily multilingual news feed.** The most live one found,
`oitnews/rss`, commits daily and carries a country field, but averages **619 articles/day**, 0.4% of
the floor, and declares no licence. `RealTimeData/bbc_news_alltime` and its 26 sibling datasets all
stopped on 2025-06-28. The licences are worse than the tags suggest: **XL-Sum is CC BY-NC-SA 4.0**
and its "44 languages" are 45 BBC World Service services rather than 45 countries' domestic press;
**MLSUM is 5 languages, non-commercial**; **WikiLingua is WikiHow guides, not news**;
**MassiveSumm is gated**, which is fatal for unattended CI; `stanford-oval/ccnews` is **967 GB** and
stops in June 2024.

One item is worth knowing about even though it fails the tests: `ruggsea/infini-news-corpus`,
1.36 B articles across 1,172 languages and 133,565 hostnames, with a keyless public lookup API at
`infini-news.uni-graz.at`. It is 1.8 TB, lags about five months, and its `cc-by-4.0` badge applies
only to derived metadata columns under an academic-research commitment. **Historical enrichment,
not a feed.**

Operational note if the Hub is used for anything: anonymous rate limits are **per IP**, and GitHub
runners share Azure egress, so a free `HF_TOKEN` moves you to a per-account bucket and should be set
even for public datasets ([huggingface.co/docs/hub/en/rate-limits](https://huggingface.co/docs/hub/en/rate-limits)).

---

## 9. Ranked shortlist for Question 2

**1. GDELT's `MASTER-GDELTDOMAINSBYCOUNTRY-MAY2018.TXT`.** Not a feed, which is why it wins: it is a
5.6 MB one-off fetch that resolves **98.7% of a live heartbeat to 70 countries in a single 15-minute
slot**, on the feed the project already ingests. Zero recurring storage, zero rate limit, zero new
dependency, and it attacks the constraint the brief says matters most. Trade-off: it is from May 2018
and there is no newer edition, so outlets founded since then are the 1.3% that fails, and the
suffix-walk fallback is required to get from 94.1% to 98.7%.

**2. Media Cloud's nightly URL dump.** **486,092 URLs/day, 15,080 hosts, 170 country-code TLDs, one
47 MB unauthenticated request.** The only candidate that clears the volume bar for free, and the only
one where breadth of country-of-publication is a property of the data rather than a hope. Trade-offs,
all governance: undocumented and unannounced, no SLA, no language field, no article bodies, and terms
that describe the platform as not designed for commercial use. This is why it is a spike and not a
decision.

**3. GDELT's Global Similarity Graph edge files (`gdeltv3/gsg/`).** About 25 MB/day, **500 MB over a
20-day window, the only GDELT product surveyed that fits a GitHub-hosted window in full**, carrying
precomputed cross-language same-story edges with `fromLang`/`toLang`. Already identified as the answer
to #2 in `event-clustering-multilingual-headlines.md`; what is new here is the storage figure and the
confirmation it is live. Trade-off: it is a different cadence from the docembed feed
(`:01/:02/:16/:17`, not the quarter-hour grid), so it needs its own slot arithmetic.

**4. The RSS registry union.** 6,192 deduplicated feeds across 4,779 domains and roughly 196
countries, yielding about **50,000 articles/day** at roughly 11 minutes of polling per cycle. The
country tagging is explicit rather than inferred, which is its real value. Trade-offs: half the volume
floor, 8.3 GB/day transited, ~8% of feeds dead on any given day with 50% decay over five years, and
the best country-tagged list carries **no licence at all**.

**5. Common Crawl CC-NEWS.** The best multilingual profile measured anywhere in this survey, English
at only 26%, and the only source that ships article bodies. Disqualified on operations rather than
data: **13.9 to 16.9 GB/day against a 14 GB runner disk, and no index of any kind**, verified three
ways. Its terms are not an open licence.

**6. GKG 2.1.** Rich, already joined to this project's clusters at 95.3%, and 15.8 GB over 20 days,
so usable only as a projection with `V2GCAM` dropped. A known quantity rather than a new source.

**Not options, and the reasons are worth keeping.** GDELT's **Global Frontpage Graph** (45-byte empty
gzip since October 2025, job still running) and **Global Entity Graph** (stopped 2026-06-18 22:31 UTC).
**Europe Media Monitor**, which processes 500,000 pages a day in 80 languages across 150 countries and
publishes five story clusters, with its legacy RSS at 403 behind `Disallow: /`. **Internet Archive's
CDX API**, which cannot express the query. **Wikimedia**, which is a signal at 6 stories/day, not a
source. **Google News RSS**, which is robots-disallowed and whose links never reach the publisher.
**Bing**, retired. **Brave**, whose terms forbid building a database of results. And every commercial
free tier, which fail by 10x to 700x.

---

## 10. What is worth a spike

Two things, and they are cheap and independent.

**Spike 1: join the country lookup to the existing heartbeat. Half a day.** Fetch
`MASTER-GDELTDOMAINSBYCOUNTRY-MAY2018.TXT` once, cache it in the repository (5.6 MB is 18% of the
current total history, so cache it compressed or fetch it per run), implement the suffix walk, and
report country alongside `language` on every record `window.py` parses. Expected result, already
measured: 98.7% attribution and 70 countries per slot. This does not change what is ingested; it
changes what can be *said* about what is ingested, and it is the axis the project's whole measurement
rests on. It also gives `polity-availability.md`'s hand-assembled polity list a mechanical basis.

**Spike 2: pull three days of the Media Cloud dump and measure the overlap with GDELT. One day.**
Three GETs, 150 MB, no key. The questions to answer are: what fraction of Media Cloud's 486,000 daily
URLs are *not* in GDELT's docembed heartbeats for the same day; what the country distribution of the
non-overlap looks like once the §7.6 lookup is joined to it; and whether the non-overlap is
concentrated in countries GDELT under-serves. If the answer is "Media Cloud adds tens of thousands of
articles from countries GDELT misses", it is worth writing to `support@mediacloud.org` and asking
whether the host is stable enough to depend on. If the answer is "it is 90% the same URLs", the
project has learned that its existing feed is not the bottleneck and can stop looking.

**For Part A, no spike is needed to pick the library: trafilatura plus htmldate, both Apache-2.0, one
`extract(output_format="json", with_metadata=True)` call at 290 ms/doc.** What *is* worth a spike, if
Part A is ever actually built, is the fetching layer rather than the parsing layer: §4.6 shows a 1.9%
JavaScript floor from a residential IP, and the number that matters is the block rate from an Azure
GitHub Actions egress address against a few thousand publishers who have all read their robots.txt
recently. That is the measurement this document could not make.

---

## 11. What could not be verified

Listed because the gaps bear on the decision, not to pad the document.

### 11.1 Part A

- **There is no gold-standard body text for the 107 documents.** Everything in §4.3 is scored against
  a noisy reconstruction validated by its own authors at 0.75 similarity unfiltered. Token F1 against
  a bag of tokens **cannot detect paragraph reordering or silent truncation**, which are two of the
  three failure modes that matter. A hand-annotated gold set for even 30 of these pages would change
  what §4.3 can claim, and it was not built.
- **The sample is 107 documents from one 15-minute slot on one day.** Per-language cells are 3 to 8
  documents. Statements like "trafilatura got 5 of 6 Chinese" are counts, not rates, and should not
  be quoted as percentages. `polity-availability.md` §2.4 already established that the day matters by
  about 70% for this feed.
- **Every page was fetched from an Italian residential IP, not from a GitHub Actions runner.** The
  1.9% JavaScript floor in §4.6 and the 106/109 fetch success rate are therefore optimistic by an
  unknown margin. Azure egress ranges are aggressively blocked by Cloudflare and Akamai, and this is
  the single measurement most likely to invalidate Part A's conclusion.
- **`news-please` was tested at its default install only.** Its 79 bodies include the same 20
  `ImportError`s newspaper4k had, and the extras were not installed for it. Its true ceiling is
  probably close to newspaper4k's 96.
- **Author accuracy was not measured, only recovery.** No reference for bylines exists in the GDELT
  record, so §4.4's author column says how often a string came back, not whether it was right.
- **Throughput was measured once, single-pass, on one slow CPU.** Run-to-run variance on trafilatura's
  body-only path was 164 to 214 ms/doc across two passes, so treat the throughput column as accurate
  to about ±25%, and treat the *ordering* as the reliable part.
- **The DAnIEL corpus was not obtained.** All per-language numbers in §3.4 are read from the two
  papers; the corpus is available on request and I did not request it. I also did not obtain the
  Bevendorff benchmark data (git-LFS tarballs, no Zenodo DOI), so §3.3's table is the paper's, not a
  reproduction.
- **magic-html, GNE, resiliparse's own claimed throughput and the Rust ports were not run here.**
  magic-html's F1 0.889 exists only in trafilatura's own table. GNE publishes no benchmark at all.
  There is **no throughput figure for resiliparse's content extractor published by its own authors**;
  the 1,149 docs/s figure on their documentation is `<title>` extraction with the Lexbor DOM parser,
  a different operation.
- **Whether an unattended job may lawfully fetch 100,000 publisher pages a day** was not researched.
  `reconstructed-text-rights.md` §1.3 established that `repubblica.it` and `corriere.it` both carry
  TDM reservations in `robots.txt`; whether that generalises, and what it means for a fetch-and-parse
  pipeline as opposed to an n-gram derivative, is open and is the question that decides whether Part A
  is ever built.

### 11.2 Part B

- **The Media Cloud host's stability is unknown and unknowable from outside.** It is undocumented,
  carries no SLA, returns 404 for `robots.txt`, and the sibling API in the same codebase is
  password-protected. The four dates I probed all returned 200, back to 2023-01-01, which is evidence
  of a long-running service and not a commitment. **Nobody at Media Cloud has been asked.**
- **Whether Media Cloud's terms permit this project's use.** §2.1 of their terms says the platform is
  "not designed for use as a commercial tool" while §2.2 grants redistribution of Platform Outputs.
  A free, ad-free research site is plainly closer to the permitted case, but this is a reading, not
  an answer, and it echoes the unresolved question in `reconstructed-text-rights.md` §4.1 about
  whether such a site is an information society service at all.
- **The 486,092 figure is one day.** The 2026-09-04 file is 35% larger. Daily volume was not
  characterised over a week, and the overlap with GDELT was not measured at all, which is exactly what
  Spike 2 exists to fix.
- **The Media Cloud dump has no language field**, and I did not test whether language is inferrable
  cheaply from the URL and title alone. If it is not, every article from it needs either a fetch or a
  language-ID pass that the GDELT feed gives away for free.
- **The domain-to-country lookup's accuracy was not audited, only its coverage.** 98.7% of records
  matched a row; whether the row is *right* for a given outlet was spot-checked by eye and not
  verified. The file also uses FIPS-style codes (`RS` for Russia), which will bite anyone assuming
  ISO 3166.
- **GKG, CC-NEWS, EventStreams and the RSS registry probes in §8 are second-hand.** They were produced
  by delegated research under the same open-every-source instruction, and I independently re-verified
  the highest-impact ones myself: the Media Cloud dump (downloaded and parsed), the domain-to-country
  file (downloaded, counted and joined), CC-NEWS's daily file count and the absence of its index (all
  three 404s reproduced), GFG's 45 bytes, GEG's 404, the GSG edge files, the trafilatura evaluation
  table and its corpus composition, and the Zyte ground-truth composition. **Not re-verified by me:**
  the GKG row counts and language distribution, the CC-NEWS language sample (34 languages, English at
  26%), the EventStreams replay measurement, the 200-feed RSS liveness probe and its 20,000/day
  extrapolation, the EMM API surface, the Brave and Bing terms quotations, and the Hugging Face
  licence readings.
- **Common Crawl's own language statistics for CC-NEWS do not exist.** Their published crawl
  statistics cover CC-MAIN only. The 34-language figure is a 100 MiB sample, not a published number.
- **No source in this survey publishes a per-article country field.** GDELT's is derived from a 2018
  domain file, Media Cloud's from the TLD, Common Crawl's from nothing. Country of publication remains
  something this project infers, and every inference route surveyed here is a join it has to maintain
  itself.
