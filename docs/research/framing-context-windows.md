# Do the words around an actor's name differ by the country that published them?

A one-day experiment, run to decide whether the project has a *second* measurement or only
one. Today the published figure asks a single question per (story, actor): **did this
source's headline contain the actor's name?** That detects the omission of a proper noun.
It says nothing about how the actor was described once it *was* named, which is what most
people mean by framing. This document asks whether the second question is answerable at
all with the data the pipeline already touches, and answers it before anything is built on
top of it.

- **Measured on**: 2026-09-06
- **Corpus**: the published run `20260906T133811Z` (`data/stories.json` on `origin/data`),
  joined to the captures on `origin/history` for `seen_at`
- **Article window**: `2026-09-04T22:31Z` to `2026-09-06T12:47Z`
- **Text source**: GDELT Web News NGrams 3.0,
  `http://data.gdeltproject.org/gdeltv3/webngrams/{stamp}.webngrams.json.gz`
- **Alias matching**: `data/actors/aliases.json` through `tensionr.stories.actors.AliasTable`,
  the same table and the same evaluability rule the engine uses
- **Permutation convention**: `p = (beaten + 1) / (rounds + 1)`, 2,000 rounds, floor
  0.0005, tie tolerance 1e-12, exactly as `backend/src/tensionr/stories/structure.py`
- Nothing outside `docs/research/` was changed; the scripts were throwaway, under `/tmp`

---

## 0. Verdict first

1. **There is a signal, and it is not language.** Holding language fixed and asking whether
   the words surrounding an actor's name differ by the country of publication, **4 of 10
   testable cells survive every control applied here**, at p between 0.003 and 0.043. The
   strongest is the Ukraine peace-talks story read in English across the United States,
   India, the United Kingdom, Pakistan and Syria: 68 sources, 68 distinct domains,
   pseudo-F 1.574, **p = 0.002**, and p = 0.003 after near-duplicate removal and
   permutation restricted within publication-time blocks.

2. **Language is the larger effect, and it would have been reported as country.** On the
   same source set, with every language in it, country gives pseudo-F 8.93 and language
   gives **15.95**. Across all eleven all-language cells the language statistic is larger
   than the country statistic in every one, by a factor of 1.4 to 3.9. A test run without
   holding language constant measures mostly translation.

3. **Six of ten within-language cells show nothing, and three of those six are
   underpowered.** Simulated on each cell's own shape, the design reaches 0.8 power only
   when roughly 8% of a source's context tokens come from a 50-word country-specific set,
   and only in the larger cells. At half that effect size power is 0.07 to 0.20 everywhere.
   A null cell here has not been shown to be flat.

4. **Two cells were significant for a reason that has nothing to do with framing.** A
   length-matched null, in which each source keeps its token count but draws its content
   at random from the pooled corpus, rejects at 5% in eight cells and at **29% and 18%** in
   the two whose per-country median context lengths are most unequal. Both of those were
   otherwise "significant". Context length is a confound the statistic cannot see past on
   its own.

5. **Near-duplicate wire copy is worth 3 to 12 sources per cell and it decides two of
   them.** Every source in every cell is a distinct domain, so syndication does not show up
   as a repeated outlet; it shows up as two different outlets carrying the same paragraph.
   Removing one of each pair above cosine 0.9 costs 4 to 33 pairs per cell and turns
   p = 0.012 into p = 0.142 in one cell and p = 0.002 into p = 0.078 in another.

6. **Publication time is a stronger predictor of context than country, in the largest
   cell.** Four-hour publication block as a factor gives pseudo-F 2.02 against country's
   1.57 on the same 68 English sources, at p = 0.0005. The country effect survives being
   permuted within time blocks, but any future design that ignores the clock will attribute
   the story's own development to geography.

7. **The measurement is thin by construction.** The median source contributes **28 to 95
   context tokens** for one actor, because an actor is named two to seven times per article
   and each n-gram record carries about fourteen words of window. This is the binding
   constraint, not the number of sources.

8. **The smallest next step is not a model.** It is to re-run this same test on a second,
   independent day and see whether the four surviving cells replicate. Section 8 states it
   precisely and prices it at under an hour of wall clock.

---

## 1. What was measured, on what

### 1.1 The corpus

The published run carries evidence rows for 20 stories. Six were chosen for having the most
sources spread over the most polities:

| story | headline (truncated) | evidence rows | polities | languages |
|---|---|---|---|---|
| `s-98d5802015fa` | Russia and Ukraine Pause Military Strikes as U.S. Peace Emissaries... | 530 | 73 | 23 |
| `s-c3580bf07787` | Iran Targets US Warships With Ballistic Missiles; CENTCOM Destroys... | 391 | 78 | 19 |
| `s-a68d00f85906` | Volcanic ash cloud sparks widespread air travel disruption... | 204 | 52 | 17 |
| `s-439f214700fb` | Nearly 9,000 killed in Israeli attacks on Lebanon since 2023 | 199 | 53 | 27 |
| `s-9cd2a3c658fc` | Maíllo dice que trasladar migrantes a la Península es la "mejor forma"... | 113 | 8 | 1 |
| `s-d138951909f1` | Putin se reúne con los enviados de EU para hablar de la guerra en Ucrania | 94 | 16 | 2 |

That is **1,531 source URLs**. The run's own capture covers only the last two blocks of the
selection window, so `seen_at` was assembled from ten captures on `origin/history` between
`2026/09/05/0448` and `2026/09/06/1338`, which resolves **1,531 of 1,531** URLs.

### 1.2 Fetching the right minute

`bodies.minutes_for()` was not used. It assumes an n-gram file exists for every minute and
fetches the wanted minute plus its two neighbours. That is wrong for this dataset: files
exist only at **:01 and :02 past each quarter hour**, and every other minute is a 404, so
`minutes_for` spends two thirds of its requests on nothing and misses the file it wants
whenever `seen_at` is not already on the grid. Each article's `seen_at` was floored to its
quarter and the `:01` file for that quarter fetched directly.

The 1,531 URLs fall in **79 distinct quarters**. Only the `:01` files were taken, which the
day's earlier measurement puts at about 91% of the articles GDELT stamped in a quarter
against 98% for `:01` plus `:02`; the extra 79 files were not judged worth the bandwidth for
a question this coarse. One file, `20260906011600`, returned a transport error on four
attempts and its quarter was served by `20260906011700` instead.

**Coverage achieved: 1,299 of 1,531 URLs, 84.8%**, close to the 91% ceiling the `:01`-only
choice implies. 575,786 word n-gram records (`type` 1) were kept for those URLs.

### 1.3 From records to a context

`fragments()` was read and not used. It merges `pre`, `ngram` and `post` into one string per
record so that `assemble()` can reconstruct a body. This experiment needs the opposite: the
individual records, keyed by which word sits at the centre. A source's **context for an
actor** is the concatenation of `pre + post` over every record whose `ngram` is one of that
actor's aliases, lowercased, accent-folded and split on word characters, with one-character
tokens dropped. The actor's own name is therefore never in its own context.

A source enters a test only if it passes the engine's own evaluability rule, that the actor
has at least one alias in the source's language (`code_for` plus `AliasTable.languages_for`),
and only if its context reaches 8 tokens.

**One alias class is unreachable and this matters.** A `type` 1 record carries a single
token, so a multi-word alias can never match one. Restricting to single-token aliases in
Latin, Cyrillic and Greek script, and keeping substring matching for Arabic and CJK as
`AliasTable` does, costs:

| actor | usable aliases | multi-word, dropped | single-token needles |
|---|---|---|---|
| `ukraine` | 89 | 3 | 21 |
| `russia` | 136 | 50 | 38 |
| `iran` | 131 | 36 | 25 |
| `israel` | 117 | 35 | 19 |
| `hormuz` | 135 | **90** | 12 |

`hormuz` loses two thirds of its aliases, because in most languages the actor's name *is* a
phrase ("Strait of Hormuz", "estrecho de Ormuz"). Its results below should be read as being
about the bare toponym.

### 1.4 The cells

All 36 actors in the alias table were scanned against all six stories, 216 candidate cells.
**Eighteen reached 20 sources with a context.** Two facts from that scan are worth stating
even though they are not the experiment: `israel` in the volcanic-ash story produced
**0 occurrences across 171 covered articles**, and `ceuta` in the Spanish migration story
produced contexts for 26 of 93 covered articles, all of them Spanish outlets. Body text
answers "was this actor discussed at all", which the headline mark cannot.

---

## 2. The statistic, and why this one

Each source becomes one sublinear TF-IDF vector over the cell's own vocabulary
(`tf = 1 + log(count)`, `idf = log((1+N)/(1+df)) + 1`, terms below 2 documents or present in
all of them dropped, L2 normalised), and the distance between two sources is cosine
distance. Nothing heavier was tried. The brief was to establish whether a bag of words shows
anything before reaching for embeddings, and it does, so it was not necessary.

The statistic is **Anderson's PERMANOVA pseudo-F**, computed from the squared distance
matrix:

```
F = (SS_between / (g - 1)) / (SS_within / (n - g))
```

with `SS_within` the sum of squared distances inside each country divided by that country's
size, and `SS_total` the same over the whole matrix. It was chosen for three reasons.

**It answers the question as asked.** "How much of the between-source variation in context
aligns with country" is a variance-partition question, and pseudo-F is the variance
partition that a distance matrix admits. It needs no assumption that the cloud is Gaussian,
which a 400-dimensional sparse TF-IDF cloud of 50 points certainly is not.

**Its null is the same null `structure.py` already uses.** Country labels are permuted
across sources, holding the country sizes and the source count fixed and destroying only the
correspondence between country and context. The reported p is
`(beaten + 1) / (rounds + 1)` over 2,000 rounds with the same 1e-12 tie tolerance, so the
smallest value it can report is 0.0005 and it never reports zero.

**Its value is not published, for the same reason `structure.py` does not publish mutual
information.** Pseudo-F at n = 50 over 5 groups is mostly a property of the table's shape.
Only the permutation rank of the observed value is used.

A positive control confirms the representation is not inert. Pooling the English sources of
two unrelated stories and labelling them by story gives F = 12.59, p = 0.0005 on 91 sources;
the Spanish equivalent gives F = 9.36, p = 0.0005 on 109. Subject matter is trivially
visible in these vectors. Whatever the country tests find, they find it against a
representation that works.

---

## 3. The result before the language control, which is the wrong result

Eleven cells had two or more countries with at least 5 sources. Every one of them is
"significant", and every one of them is contaminated:

| cell | sources | countries | F country | p country | F language | p language |
|---|---|---|---|---|---|---|
| `s-98d5802015fa` / ukraine | 238 | 18 | 8.93 | 0.0005 | **15.95** | 0.0005 |
| `s-98d5802015fa` / russia | 212 | 18 | 6.76 | 0.0005 | **11.65** | 0.0005 |
| `s-c3580bf07787` / iran | 187 | 12 | 7.47 | 0.0005 | **20.14** | 0.0005 |
| `s-c3580bf07787` / hormuz | 106 | 9 | 5.15 | 0.0005 | **20.14** | 0.0005 |
| `s-439f214700fb` / israel | 66 | 7 | 7.48 | 0.0005 | **11.39** | 0.0005 |
| `s-439f214700fb` / lebanon | 63 | 7 | 8.09 | 0.0005 | **14.16** | 0.0005 |
| `s-439f214700fb` / hezbollah | 69 | 8 | 11.04 | 0.0005 | **15.75** | 0.0005 |
| `s-a68d00f85906` / indonesia | 56 | 6 | 7.89 | 0.0005 | **12.98** | 0.0005 |
| `s-9cd2a3c658fc` / argentina | 51 | 4 | 2.64 | 0.0005 | single language | |
| `s-d138951909f1` / ukraine | 57 | 5 | 1.38 | 0.0150 | single language | |
| `s-d138951909f1` / russia | 58 | 5 | 1.23 | 0.0725 | single language | |

**In every multilingual cell the language statistic is the larger one**, between 1.4 and 3.9
times the country statistic. Sources in the same country mostly share a language, so a
country test run on a multilingual set is measuring vocabulary, not editorial choice. This
is the same trap `cross-lingual-actors` found on `V2.1ALLNAMES` and `language-residual` had
to separate for the naming mark, arriving one layer further in. If this experiment had
stopped here it would have reported eleven strong findings and every one would have been
an artefact of translation.

Two cells that are single-language by construction are the exception, and they are also the
two weakest: F 1.38 and 1.23 against 5 to 11 for the multilingual ones. That gap is the size
of the language artefact, read off the same table.

---

## 4. Holding language constant

The honest test uses one language at a time, across countries that publish in it.
The corpus supports this in two languages:

- **English** across the United States, India, the United Kingdom, Pakistan and Syria
- **Spanish** across Spain, Mexico, Argentina, Chile, Venezuela and the United States

Australia and Ireland were reachable in the all-language set but never with 5 English
sources in a single cell, so the English panel is US / IN / GB / PK / SY rather than the
US / UK / India / Australia / Ireland the brief suggested.

Ten cells reached at least two countries with 5 sources within one language. Reading the
whole table at once, with every control applied:

| cell | lang | n | countries | median tokens | p as measured | dup pairs | n clean | p clean, permuted within time block | length-null rejects at .05 | power at 8% |
|---|---|---|---|---|---|---|---|---|---|---|
| `s-98d5802015fa` / ukraine | EN | 68 | 5 | 95 | **0.0020** | 16 | 60 | **0.0030** | 6/100 | **0.93** |
| `s-c3580bf07787` / iran | ES | 53 | 5 | 80 | **0.0030** | 17 | 44 | **0.0430** | 5/100 | 0.82 |
| `s-c3580bf07787` / hormuz | ES | 44 | 4 | 28 | **0.0075** | 23 | 34 | **0.0205** | 6/100 | 0.15 |
| `s-d138951909f1` / ukraine | ES | 56 | 5 | 53 | **0.0270** | 9 | 49 | **0.0250** | 3/100 | 0.42 |
| `s-9cd2a3c658fc` / argentina | ES | 51 | 4 | 77 | 0.0005 | 6 | 46 | 0.0005 | **18/100** | 0.73 |
| `s-98d5802015fa` / russia | EN | 55 | 3 | 69 | 0.0120 | 33 | 43 | 0.0975 | **29/100** | 0.27 |
| `s-a68d00f85906` / indonesia | EN | 23 | 3 | 51 | 0.0020 | 12 | 17 | 0.0860 | 10/100 | 0.09 |
| `s-c3580bf07787` / hormuz | EN | 38 | 2 | 28 | 0.0535 | 20 | 29 | 0.1584 | 7/100 | 0.17 |
| `s-d138951909f1` / russia | ES | 57 | 5 | 42 | 0.0975 | 4 | 54 | 0.1654 | 7/100 | 0.41 |
| `s-c3580bf07787` / iran | EN | 54 | 3 | 78 | 0.1819 | 9 | 47 | 0.4293 | 8/100 | 0.60 |

The four bold rows are the finding. They are two stories in each of two languages, they
survive every control in sections 5 and 6, and their length-matched null rejects at the
nominal rate. Everything below them fails at least one control or was never null to begin
with.

**The effect does not vanish when language is held constant. It shrinks.** Country pseudo-F
falls from 5.2 to 11.0 in the contaminated multilingual cells to 1.35 to 1.58 in the clean
within-language ones, while staying beyond the permutation null. That is the shape of a real
but modest effect sitting underneath a much larger artefact, which is what
`language-residual` found for the naming mark and is presumably the same phenomenon seen
through a different instrument.

An intermediate design was also run, permuting country labels within language strata on the
full multilingual set. It agrees with the within-language subsets on the direction but not
reliably on the individual cells: `ukraine` survives at p = 0.0015 and `iran` at p = 0.0005,
while `russia` moves to p = 0.1064 and `hezbollah` to p = 0.1024. It is reported here and
not relied on, because permuting within strata does not preserve each country's total size
across strata, so its null distribution is not the same shape as the observed statistic's.
The single-language subsets hold size fixed exactly and are the ones the verdict rests on.

---

## 5. Power, which decides what a null means

Power was simulated on each cell's own shape. Each round shuffles the country labels across
that cell's real sources, which destroys whatever association the cell actually carries while
holding the country sizes and the bags fixed, then plants an effect on the shuffled labels
and tests for it. Each country gets 50 marker words drawn from the cell's own vocabulary,
and a fraction `f` of every source's tokens is replaced by draws from its country's markers.
200 simulations per point, 499 permutation rounds each.

| cell | f = 0 | 1% | 2% | 4% | 8% | 16% |
|---|---|---|---|---|---|---|
| `ukraine` EN, n=68, 5 countries | 0.060 | 0.070 | 0.040 | 0.195 | **0.930** | 1.000 |
| `iran` ES, n=53, 5 | 0.060 | 0.055 | 0.050 | 0.165 | **0.815** | 1.000 |
| `argentina` ES, n=51, 4 | 0.050 | 0.070 | 0.075 | 0.110 | 0.725 | 1.000 |
| `iran` EN, n=54, 3 | 0.050 | 0.080 | 0.055 | 0.130 | 0.600 | 1.000 |
| `ukraine` ES, n=56, 5 | 0.055 | 0.045 | 0.080 | 0.155 | 0.415 | 1.000 |
| `russia` ES, n=57, 5 | 0.085 | 0.075 | 0.060 | 0.090 | 0.405 | 1.000 |
| `russia` EN, n=55, 3 | 0.035 | 0.065 | 0.095 | 0.105 | 0.265 | 1.000 |
| `hormuz` EN, n=38, 2 | 0.060 | 0.055 | 0.020 | 0.075 | 0.165 | 0.885 |
| `hormuz` ES, n=44, 4 | 0.040 | 0.055 | 0.065 | 0.070 | 0.150 | 0.925 |
| `indonesia` EN, n=23, 3 | 0.040 | 0.025 | 0.040 | 0.065 | 0.090 | 0.345 |

Three things to take from this.

**The test is calibrated.** At f = 0 the rejection rate is 0.035 to 0.085 against a nominal
0.05, across ten different table shapes. The permutation machinery is doing what it claims.

**Detection needs a large effect.** 8% of a 95-token context is about eight words per source
drawn from a country-specific list. Below 4% nothing is visible anywhere, at any n available
here. This is a floor set by the 28 to 95 tokens a source contributes, not by the source
count: `indonesia` EN has 23 sources and 0.09 power at 8%, while `ukraine` EN has 68 sources
and 0.93.

**Three of the six null cells cannot support a null claim.** `hormuz` EN (0.17), `hormuz` ES
(0.15) and `indonesia` EN (0.09) would miss a planted 8% effect four times out of five. Their
p-values are uninformative in the direction of absence. `iran` EN, at 0.60, is the only null
cell with enough power that its p = 0.18 is mild evidence of flatness, and `russia` ES at
0.41 is borderline. Following `structure.py`'s practice, a cell like this must be published
as unpowered rather than as "not significant".

Note that the planted effect is idealised: disjoint marker sets per country make the
signature cleaner than real framing, where the same words appear everywhere at different
rates. The power figures are therefore an **upper bound**.

---

## 6. Three confounds that are not language

### 6.1 Duplication

Every source in every within-language cell is a **distinct domain**, so no cell is inflated
by one outlet appearing repeatedly. That is not the same as no duplication: two different
outlets can run the same wire paragraph. Cosine similarity at or above 0.9 between two
sources in a cell was taken as a near-duplicate and one of each pair dropped.

The pair counts are not small: 4 to 33 per cell, up to **33 pairs among 55 sources** in
`russia` EN. Two cells lose their result to this alone, `russia` EN from p = 0.012 to
p = 0.142 and `indonesia` EN from p = 0.002 to p = 0.078, and one gets stronger,
`ukraine` ES from p = 0.027 to p = 0.010. The four surviving cells hold.

### 6.2 Context length

Cosine distance between sparse vectors is not neutral to how many tokens went into them. A
20-token bag is further from everything than a 200-token bag, so if context length varies by
country the statistic can find country structure in nothing but article length.

The control: keep each source's exact token count, replace its content with draws from the
pooled token distribution of the cell, and run the identical test. 100 simulations per cell.
A calibrated cell should reject at 5%.

Eight of ten do, at 3 to 10 rejections in 100. Two do not:

| cell | rejects at .05 | median p under the null | per-country median context tokens |
|---|---|---|---|
| `russia` EN | **29/100** | 0.162 | US 69, India 42, UK 42 |
| `argentina` ES | **18/100** | 0.214 | Chile 104, Argentina 77, Mexico 50, **Spain 13** |

These are exactly the two cells with the most unequal per-country lengths, and both were
otherwise significant. `argentina` ES held p = 0.0005 through every other control and must
still be discounted, because a test that rejects 18% of the time on content-free data is not
entitled to a p of 0.0005 on real data. This control is cheap and it changed the answer;
any future version of this measurement must carry it.

### 6.3 Publication time

Sources arrive over 38 hours and a story develops within that. Outlets in one country
cluster in that country's working day, so time of publication and country of publication are
correlated by construction, and later articles carry words earlier ones could not.

Four-hour publication blocks as a factor are **significant in six of ten cells**, and in the
largest cell they beat country outright: on the same 68 English sources, time block gives
F = 2.02 at p = 0.0005 while country gives F = 1.57 at p = 0.002. In the Spanish
Putin-envoys story time is significant (p = 0.0015) where country for the same actor is not
(p = 0.098).

Permuting country labels only within time blocks leaves the four surviving cells intact
(0.003, 0.043, 0.021, 0.025) and removes `russia` EN and `indonesia` EN, which had already
failed the duplication control. So the country effect is not merely the clock. But the clock
is a real and in one case *larger* structure in this data, and a design that does not
condition on it will read the news cycle as geography.

---

## 7. What the words actually are

A p-value is not a finding. These are the tokens that most distinguish each country's
context, by log-odds with an informative Dirichlet prior taken from the cell itself, on the
near-duplicate-free sources, minimum 3 occurrences.

**`s-98d5802015fa` / ukraine, English** (peace talks, Witkoff and Kushner in Moscow):

| country | most distinctive context tokens |
|---|---|
| United States | air, troops, said, purely, had, struggled, scale |
| United Kingdom | recent, officials, nato, moscow, ukrainian, peace, continues |
| India | people, talks, civilians, military, vladimir, remains, killed, ready |
| Pakistan | kremlin, breakthrough, territory, calls, push |
| Syria | eastern, ushakov, since, pause, both, efforts, putin |

This reads like framing rather than like different subjects: the same event, with the US
sources on military detail, the UK sources on institutions and NATO, the Indian and Pakistani
sources on civilians, talks and the prospect of a breakthrough.

**`s-c3580bf07787` / iran, Spanish** (US strikes on Iranian tankers):

| country | most distinctive context tokens |
|---|---|
| Spain | ha, está, guardia, revolucionaria, ataque, militar, informado |
| Mexico | estados, unidos, marítimo, buques, armadas, bombardea |
| Argentina | ataques, condenó, confirmó, región |
| Chile | fars, según, agencia, armada, herido, aeroespacial |
| United States | golfo, washington, centcom, fuerzas |

Two of these are checkable as framing: Mexican outlets foreground *estados unidos* as the
agent, Chilean outlets foreground *fars*, *según*, *agencia*, that is, attribution to the
Iranian news agency. Spanish outlets' markers are partly grammatical (`ha`, `está`), which
is peninsular Spanish rather than editorial choice, and is a reminder that "one language"
is not one dialect.

**The counter-example is instructive.** `s-9cd2a3c658fc` / argentina, Spanish, the cell with
the largest F of all and the miscalibrated length null, separates on *república, baker,
hughes, halliburton, empresas* for Argentina against *chile, quirno, magallanes, bioceánico,
bicontinental* for Chile and *malvinas, islas* for Spain. Those are not three framings of one
event; they are three different events that happen to name Argentina. The cluster is
heterogeneous and the statistic reported the heterogeneity. This is the failure mode a
future version has to guard against, and the guard is not statistical.

A last check: removing the 50 most frequent tokens in each cell, a data-driven stopword list,
leaves all five surviving p-values essentially unchanged (0.003, 0.0075, 0.002, 0.0375,
0.0005). The effect is not a function-word artefact.

---

## 8. Verdict, and the smallest next step

**There is a signal worth building on, with three conditions attached.**

The signal: in two languages and two stories each, the words around an actor's name differ
by the country of publication more than a permutation of the country labels produces, and
the difference survives near-duplicate removal, a length-matched null, and restriction to
within publication-time blocks. The distinctive tokens in the strongest cell read like
editorial emphasis rather than like different subjects. That is a second measurement, and it
is measuring something the headline mark cannot see.

The conditions:

1. **It is a within-language measurement or it is nothing.** Run across languages it reports
   translation, at three to four times the apparent strength.
2. **It needs about 8% of context tokens to move before it can see anything**, so it will be
   silent on most cells and must say "unpowered" rather than "no difference", the way
   `structure.py` already does.
3. **The cell has to be one event.** The one cell that behaved like a heterogeneous cluster
   produced the largest statistic in the study.

**The smallest next step is replication, not modelling.** Take a second, independent day,
rebuild the same four cells from the same run artefacts, and ask whether they are significant
again and whether their distinctive tokens are the same tokens. Four cells at p between 0.003
and 0.043 out of ten tested is roughly what one day of noise plus a real effect looks like
from the outside, and the two are told apart by whether they come back. The cost is 79 n-gram
files, about 3 GB and 15 minutes of wall clock, plus the scripts already written. Nothing in
the pipeline needs to change to find out.

If it replicates, the second step is to make the unit the project publishes a *pair* of
countries rather than a set, because pseudo-F over 5 groups says "somebody differs" and the
page needs to say who. If it does not replicate, this is a day spent, and the headline mark
remains the only measurement.

Do **not** reach for embeddings first. A bag of words found the effect, found the language
artefact, found the length artefact and found the heterogeneous cluster. A sentence encoder
would have found all four too and made none of them visible.

---

## 9. What could not be established

- **Whether it replicates.** Everything here is one run and one 38-hour window. Four
  significant cells out of ten is a result, not a finding, until a second window agrees.
  This is the single largest gap and section 8 exists because of it.

- **How much of the variation country explains.** Only the permutation rank of pseudo-F is
  reported. Its value at n around 50 over 4 or 5 groups is dominated by the table's shape,
  the same objection `structure.py` records against publishing mutual information. No effect
  size in this document should be read as a share of variance.

- **Whether the effect is editorial or is different sub-events.** Section 7 shows one cell
  that was plainly the latter and one that plainly reads as the former, judged by eye. No
  test here separates them, and no test in this family can. It needs either a same-event
  guarantee stronger than the clustering currently provides, or human reading.

- **Anything about languages other than English and Spanish.** The corpus contained 34
  languages, but only these two put 5 or more sources in each of 4 or more countries inside
  a single cell. Arabic, Greek, Turkish, German and Russian were present in quantity and each
  is effectively one polity in this window. Whether the effect exists in them is untested,
  and `polity-availability` already predicted this shape.

- **Whether "one language" is one comparison.** Peninsular Spanish grammar showed up in the
  Spanish distinctive tokens (`ha`, `está`) and Indian English has its own register. Dialect
  is a confound nested inside the language control and nothing here separates it.

- **The 15% of sources with no n-gram coverage.** Only the `:01` files were fetched, and one
  quarter failed outright. 232 of 1,531 URLs contributed nothing. Whether they are missing at
  random with respect to country is untested; GDELT's own processing order is not documented.

- **Multi-word actor names.** A unigram record cannot match "Strait of Hormuz", so `hormuz`
  was tested on a third of its aliases and any actor whose name is a phrase in most languages
  is currently unmeasurable this way. GDELT does publish longer n-grams; they were not fetched.

- **Whether context length is a nuisance or a signal.** It was treated as a confound here
  because it drives the statistic under a content-free null. It is also plausibly editorial:
  how much an outlet says about an actor is a choice. Nothing here can tell the two apart,
  and the length-matched null deliberately throws the second away.

- **Any comparison against a supervised framing benchmark.** There is no gold label for
  framing in this corpus, which is the same wall `framing-divergence-measurement` hit when it
  rejected GoEmotions. Everything above is internal consistency and permutation, not accuracy.
