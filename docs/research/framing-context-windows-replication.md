# Replication on an independent day

A pre-registered replication of [`framing-context-windows.md`](framing-context-windows.md),
which measured on 2026-09-06 that the words surrounding an actor's name differ by the
country of publication in 4 of 10 within-language cells, at p between 0.003 and 0.043.
That document's own verdict named replication as the next step and said why: four hits in
ten is roughly what one day of noise plus a real effect looks like from the outside, and
the two are told apart by whether they come back.

They do not come back.

- **Measured on**: 2026-09-06
- **Replication day**: the run `20260903T045246Z`, `index.json` and `capture.json` off
  `origin/history`
- **Replication article window**: `2026-09-01T06:02:05Z` to `2026-09-03T04:02:09Z`
- **Original article window**: `2026-09-04T22:31:28Z` to `2026-09-06T12:47:17Z`
- **Back-check**: the same pipeline was also re-run on the original day, from the original
  run `20260906T133811Z`, because a null on a second day is unreadable without it
- **Everything else**: identical to the original, and section 3 records the two places
  where it could not be, with the size of each difference measured
- Nothing outside `docs/research/` was changed; the scripts were throwaway, under `/tmp`

---

## 0. Verdict first

1. **Not replicated.** Of the four pre-registered cells, **0 of 4** reached p <= 0.05 on
   the new day with every control the original applied. One (`hormuz` ES) was significant
   as measured, p = 0.030, and lost it to near-duplicate removal. The criterion fixed
   before the test called 0 or 1 hits "not replicated", 2 "partially replicated" and 3 or
   more "replicated".

2. **The distinctive tokens do not come back, and this is the stronger result.** Of the
   35 published day-1 tokens whose country still had a panel on the new day, **1 came
   back** where **1.18 were expected by chance**. The same code recovers **43 of 56** of
   those tokens when pointed at the original day, so the instrument is not the reason.

3. **The nulls are only informative in one of the four cells, and there they are
   informative.** Simulated power at the original's 8% effect size is 0.165, 0.94, 0.315
   and 0.10 on the four replication cells. Only `iran` ES is powered, and it is powered
   well: 0.94, with a calibrated length-matched null, and it returns p = 0.079 against
   p = 0.030 for the same cell on the original day at power 0.89. That single comparison
   is the cleanest evidence here, and it is negative.

4. **Three of the four cells could not be rebuilt at day-1 size, and that is a finding
   about the design rather than an accident.** The English Ukraine panel fell from 5
   countries and 68 sources to 3 countries and 31, the Spanish Ukraine panel from 5 and
   56 to 2 and 13. A cell's country panel is a property of which cluster the engine
   happened to produce that hour, not of the method. Any measurement built on this would
   be silent most days and would not be silent in a predictable way.

5. **The back-check reproduces the original day, which is what makes the null readable.**
   Re-run on the original run with the enriched n-gram coverage this replication was
   instructed to use, the four cells give p = 0.018, 0.030, 0.019 and 0.059: 3 of 4 still
   reject. Re-run with the original's own `:01`-only coverage, the cell shapes match to
   within one source (n = 67/53/44/56 against a published 68/53/44/56) and the median
   context lengths to within three tokens.

6. **But the published p-values are fragile at a level the original did not report.** On
   the `:01`-only reproduction the four controlled p-values come out 0.057, 0.064, 0.005
   and 0.014 against a published 0.003, 0.043, 0.021 and 0.025. Two of the four cross
   0.05 on nothing but *which member of each near-duplicate pair is dropped*, a choice the
   original does not specify. Four hits in ten was already a thin result; two of the four
   are decided by an unstated tie-break.

7. **The one place on the new day where a country test fires hard is the failure mode the
   original warned about.** An exploratory cell, the day's best-powered English `ukraine`
   panel, gives pseudo-F 3.01 at p = 0.0005 through every control. Its distinctive tokens
   are `india, jaishankar, visit, minister, external` for India against `german, germany,
   ironclad, invasion, 2022` for the United Kingdom. Those are two different stories in
   one cluster, not two framings of one story. Section 8 keeps it out of the verdict; it
   belongs in the record because it is the third condition of the original's own verdict
   failing in the wild, at more than twice the pseudo-F of anything that passed.

8. **What this means for building.** Nothing should be built on the country-context
   measurement. The original's condition list already required a within-language design,
   an 8% effect floor, and a same-event guarantee. The third condition is the one that
   fails first and it is not a statistical problem, so no amount of more data fixes it.
   The headline naming mark remains the only measurement.

---

## 1. The day, and how it was checked to be independent

`origin/history` carries captures from 2026-08-02 onward, four to seven runs per day. The
requirement was a day whose article window does not overlap the original's
`2026-09-04T22:31Z` to `2026-09-06T12:47Z`.

**2026-09-03 was chosen** as the closest day that clears it. Closeness is the right
direction to err in: the further back the day, the less likely the running stories still
exist, and a cell with no counterpart is untested rather than falsified. The four runs
captured that day are `0452`, `1300`, `1927` and `2246`.

**Which run**, decided on source counts alone before any statistic was computed: the one
whose stories supply the largest within-language, multi-country panels for the
pre-registered actors. That is `20260903T045246Z`. The four candidates, counting sources
per country with at least five in a language:

| run | Iran / Hormuz story | EN countries >= 5 | ES countries >= 5 | Russia-Ukraine story | EN countries >= 5 | ES countries >= 5 |
|---|---|---|---|---|---|---|
| **0452** | `s-351daf9be839`, 512 | **8** (229 sources) | **6** (105) | `s-dd2019f6552b`, 355 | 3 (68) | **2** (23) |
| 1300 | `s-99a083fa7a36`, 623 | 10 (172) | 3 (43) | `s-3220cd669ee5`, 506 | 4 (77) | 1 (29) |
| 1927 | `s-99a083fa7a36`, 354 | 7 (123) | 2 (36) | `s-3220cd669ee5`, 739 | **4** (134) | 1 (38) |
| 2246 | `s-99a083fa7a36`, 459 | 8 (157) | 5 (74) | `s-16837de513c7`, 480 | 2 (82) | 2 (26) |

`0452` wins on three of the four cells and ties on the fourth, and it is the only run that
puts a Spanish panel of two or more countries on both stories at once. Runs `1300` and
`1927` cannot supply the Spanish Ukraine cell at all. The whole table is printed because
the choice was made from it and a reader should be able to see that it was not made from
a p-value.

**Independence, checked three ways.**

- **Article window.** `2026-09-01T06:02:05Z` to `2026-09-03T04:02:09Z`, computed from the
  `seen_at` of the 867 selected URLs joined to nine captures between `2026/09/01/0527`
  and `2026/09/03/2246`. All 867 resolved. The gap to the original window is **42 hours
  29 minutes** and the two do not touch.
- **URLs.** Of the 2,281 URLs in the original run, **one** also appears in the
  replication selection: `hngn.com/articles/272964/...kyiv-area-depot-blast...`, a page
  the clustering picked up on both days. It was dropped, so the two corpora are disjoint
  by construction.
- **Events.** The two days are not the same news. The original's Ukraine story is peace
  emissaries in Moscow; 2026-09-03's is Ukrainian airspace closing to civil aviation. The
  original's Iran story is strikes on tankers and warships; 2026-09-03's is a proposal to
  rename the Strait of Hormuz. Section 2 records what that does to the token test.

The n-gram fetch: 79 distinct quarters, each mapped to quarter+1 and quarter+2 for 158
files. Four returned 404 (`20260901170100`, `20260902183100`, `20260902204600`,
`20260903034700`) and in every case the quarter's other file served, so **no quarter was
lost**. Coverage reached **835 of 866 URLs, 96.4%**, against the original's 84.8% from
`:01` alone. 456,113 word n-gram records were kept.

---

## 2. What was fixed before the test

Written down and timestamped before any p-value was computed on the new day. Reproduced
here as it was fixed, not as it reads with hindsight.

### 2.1 The four cells and their counterparts

Counterpart rule: the chosen run's story with the most sources about the same running
conflict, same actor key, same language. A cell is **untested**, not failed, if the day
carries no story on that conflict, or if the counterpart does not reach the original's own
admission rule of two or more countries each with five or more sources whose context
reaches 8 tokens.

| # | original cell, named as the original names it | original p | counterpart on 2026-09-03 | testable? |
|---|---|---|---|---|
| 1 | `s-98d5802015fa` / `ukraine`, ENGLISH (peace talks) | 0.0030 | `s-dd2019f6552b` / `ukraine`, ENGLISH | yes |
| 2 | `s-c3580bf07787` / `iran`, SPANISH (tanker strikes) | 0.0430 | `s-351daf9be839` / `iran`, SPANISH | yes |
| 3 | `s-c3580bf07787` / `hormuz`, SPANISH | 0.0205 | `s-351daf9be839` / `hormuz`, SPANISH | yes |
| 4 | `s-d138951909f1` / `ukraine`, SPANISH (Putin envoys) | 0.0250 | `s-dd2019f6552b` / `ukraine`, SPANISH | yes, barely |

All four turned out testable, so nothing here is untested for want of a counterpart. Cell
4 is the one that had to be reasoned about: on the original day the Spanish Ukraine cell
was a separate Spanish-headline cluster, and 2026-09-03 has no Spanish-headline Ukraine
cluster in any of its four runs. The counterpart taken was therefore the Spanish sources
*inside* the day's Ukraine story, which is the same object the original's cell was, one
clustering decision earlier. It clears the admission rule at 2 countries and 13 sources
and is reported, at power 0.10.

### 2.2 The success criterion, numeric, fixed before looking

Under the null that all four were day-1 noise, each rejects at 0.05 independently:
expected hits 0.20, P(>= 1) = 0.185, P(>= 2) = 0.0140, P(>= 3) = 0.00048.

- **3 or 4 of 4** at p <= 0.05 with every control: replicated.
- **2 of 4**: partially replicated.
- **0 or 1 of 4**: not replicated, because one hit is the modal outcome under pure noise.

A cell that fails to reject counts against the finding only if its simulated power at
f = 8% is >= 0.5; below that it is unpowered and counted as untested-for-power, following
the original's own rule in its section 5. If fewer than three cells are testable the
verdict can be at most "partially replicated".

### 2.3 The token test

The original's section 7 lists per country, copied before the new day was touched:

`s-98d5802015fa` / `ukraine`, English: US `air, troops, said, purely, had, struggled,
scale`; UK `recent, officials, nato, moscow, ukrainian, peace, continues`; India `people,
talks, civilians, military, vladimir, remains, killed, ready`; Pakistan `kremlin,
breakthrough, territory, calls, push`; Syria `eastern, ushakov, since, pause, both,
efforts, putin`.

`s-c3580bf07787` / `iran`, Spanish: Spain `ha, esta, guardia, revolucionaria, ataque,
militar, informado`; Mexico `estados, unidos, maritimo, buques, armadas, bombardea`;
Argentina `ataques, condeno, confirmo, region`; Chile `fars, segun, agencia, armada,
herido, aeroespacial`; US `golfo, washington, centcom, fuerzas`.

Method on the new day: identical log-odds with an informative Dirichlet prior taken from
the cell itself, minimum 3 occurrences, on the near-duplicate-free sources, top 8 per
country. Reported as raw overlap per country and against a permutation null drawn from the
day-2 vocabulary.

Recorded in advance, and it matters: **the two days are different sub-events of the same
conflicts, so event-specific proper nouns cannot recur and only framing words can.** The
overlap is a lower bound on framing stability. It is also, for the same reason, the test
that separates framing from topic: `ushakov`, `witkoff`, `centcom` and `fars` were never
going to come back, but `civilians`, `talks`, `troops`, `officials`, `nato` and
`bombardea` would if the finding were about how a country writes rather than about what
happened that afternoon.

---

## 3. The instrument, and the back-check that makes a null readable

A failed replication is worth nothing unless the pipeline is known to reproduce the
original result on the original data. It was run on both days, and two differences from
the original had to be found and priced first.

### 3.1 The two differences, and what each is worth

**Coverage was enriched by instruction.** The original fetched only the `:01` file for
each quarter and reached 84.8% of URLs. This replication was instructed to fetch
quarter+1 and quarter+2, which reaches 96.4% on the new day and 93.3% on the original's.
That is a better instrument and it is not the original's instrument, so every result below
is reported on both.

**Alias matching had to be read out of the prose.** The original says a context is built
from "every record whose `ngram` is one of that actor's aliases", and separately that it
kept "substring matching for Arabic and CJK as `AliasTable` does". The second clause only
means something if Latin, Cyrillic and Greek did *not* use substring matching, so the
match is exact equality on the folded single token. Taking `AliasTable`'s own substring
rule instead inflates contexts by 1.7 to 1.9 times, because `ucrania` then also matches
`ucraniano` and `iran` matches `irani`. The two readings are told apart by the original's
own published numbers: with exact matching the median context of `ukraine` EN comes out
**92 tokens against a published 95**, and of `hormuz` ES **28 against a published 28**;
with substring matching they come out 168 and 28. Exact matching is what the original did.
This is recorded because it is invisible in the prose and it changes the answers.

### 3.2 The back-check, `:01` only, against the published numbers

| cell | n (published) | median tokens (published) | n clean (published) | p as measured (published) | p clean + time block (published) |
|---|---|---|---|---|---|
| `ukraine` EN | 67 (68) | 92 (95) | 56 (60) | 0.0055 (0.0020) | **0.0565** (0.0030) |
| `iran` ES | 53 (53) | 81 (80) | 43 (44) | 0.0005 (0.0030) | **0.0635** (0.0430) |
| `hormuz` ES | 44 (44) | 28 (28) | 34 (34) | 0.0065 (0.0075) | 0.0050 (0.0205) |
| `ukraine` ES | 56 (56) | 52 (53) | 47 (49) | 0.0365 (0.0270) | 0.0140 (0.0250) |

Cell construction is reproduced exactly: source counts match to within one, median context
lengths to within three tokens, clean counts to within four. The as-measured p-values
reproduce. **The controlled p-values do not, in two of the four cells**, and the reason is
the near-duplicate step: the original specifies dropping "one of each pair" above cosine
0.9 without saying which one. This implementation drops the later index. On a 50-source
cell that choice moves `ukraine` EN from 0.003 to 0.057 and `iran` ES from 0.043 to 0.064,
across the line in both cases, while leaving the other two below it. Two of the original's
four surviving cells are decided by an unstated tie-break.

### 3.3 The back-check with the instructed coverage

| cell | n | countries | median | p as measured | dup pairs | n clean | p clean | **p clean + time block** | length null | power @ 8% |
|---|---|---|---|---|---|---|---|---|---|---|
| `ukraine` EN | 91 | 7 | 94 | 0.0005 | 30 | 72 | 0.0200 | **0.0175** | 3/100 | **0.975** |
| `iran` ES | 61 | 5 | 80 | 0.0015 | 24 | 50 | 0.0385 | **0.0295** | 7/100 | **0.89** |
| `hormuz` ES | 55 | 5 | 28 | 0.0145 | 24 | 40 | 0.0105 | **0.0190** | 9/100 | 0.20 |
| `ukraine` ES | 66 | 5 | 50 | 0.0235 | 35 | 48 | 0.0545 | 0.0585 | 5/100 | 0.585 |

**3 of 4 reject on the original day under the instrument this replication uses**, and the
fourth misses at 0.0585. Two of the three are adequately powered. That is close enough to
the published 4 of 4 that the instrument can be pointed at a second day and believed.

---

## 4. The four cells on the new day

Every column computed the same way as section 3.3, on `20260903T045246Z`.

| cell | n | countries | median | p as measured | dup pairs | n clean | countries clean | p clean | **p clean + time block** | length null | power @ 8% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ukraine` EN | 31 | 3 | 56 | 0.2074 | 7 | 23 | 2 | 0.3028 | **0.4648** | 2/100 | 0.165 |
| `iran` ES | 67 | 5 | 53 | 0.0985 | 15 | 59 | 5 | 0.0835 | **0.0785** | 5/100 | **0.94** |
| `hormuz` ES | 58 | 5 | 40 | **0.0300** | 20 | 46 | 5 | 0.3108 | **0.3273** | 6/100 | 0.315 |
| `ukraine` ES | 13 | 2 | 34 | 0.2669 | 0 | 13 | 2 | 0.2624 | **0.4093** | 1/100 | 0.10 |

**Nothing reaches 0.05.** `hormuz` ES is significant as measured at 0.030 and loses it
entirely to near-duplicate removal, which is the same thing that happened to `russia` EN
and `indonesia` EN on the original day. `iran` ES lands at 0.079, a near miss on a cell
with power 0.94.

Side by side with the same instrument on the original day:

| cell | day 1 p (power) | day 2 p (power) |
|---|---|---|
| `ukraine` EN | **0.0175** (0.975) | 0.4648 (0.165) |
| `iran` ES | **0.0295** (0.89) | 0.0785 (0.94) |
| `hormuz` ES | **0.0190** (0.20) | 0.3273 (0.315) |
| `ukraine` ES | 0.0585 (0.585) | 0.4093 (0.10) |

The country panels themselves did not survive the day. Under this instrument the original
day's English Ukraine cell reached seven countries, US, India, UK, Pakistan, Syria,
Australia and Canada, and the original's own `:01` build reached five; on the new day it
reaches US 21, Canada 5, UK 5, and after near-duplicate removal only US and UK. The Spanish
Iran cell kept its size but swapped Chile for Colombia. The Spanish Ukraine cell went from
five countries and 66 sources on the original day to two countries and 13.

Publication time behaved differently too. On the original day four-hour publication block
as a factor was significant in the Ukraine EN cell at p = 0.0005, F = 1.66 in this
back-check and F = 2.02 as the original reports it, beating country either way. On the new
day it is significant in none of the four: p = 0.080, 0.207, 0.163, 0.294. Whatever drives
the clock structure is not a constant of the design either.

---

## 5. Power, without which the null means nothing

Simulated exactly as the original's section 5: each round shuffles the country labels
across the cell's real sources, plants 50 marker words per country drawn from the cell's
own vocabulary, replaces a fraction `f` of every source's tokens with draws from its
country's markers, and tests. 200 simulations, 499 permutation rounds each.

The first four columns are simulated on the cell as measured, which is the shape the
original's own table reports. The last column is simulated on the near-duplicate-free
admitted set, which is the shape the decisive p-value is computed on, and it is the one
the verdict uses.

| cell (as measured) | f = 0 | 4% | 8% | 16% | 8% on the clean set |
|---|---|---|---|---|---|
| `iran` ES, n = 67, 5 countries | 0.030 | 0.200 | 0.885 | 1.000 | **0.940** (n = 59, 5) |
| `hormuz` ES, n = 58, 5 | 0.050 | 0.120 | 0.425 | 1.000 | 0.315 (n = 46, 5) |
| `ukraine` EN, n = 31, 3 | 0.045 | 0.085 | 0.160 | 0.975 | 0.165 (n = 23, 2) |
| `ukraine` ES, n = 13, 2 | 0.090 | 0.080 | 0.100 | 0.175 | 0.100 (n = 13, 2) |

**The test is calibrated**: 0.030 to 0.090 at f = 0 against a nominal 0.05, and the
length-matched null rejects 1 to 6 times in 100 on all four cells, so no cell here is the
`argentina` ES case where the statistic was reading context length.

**Only `iran` ES can support a null claim.** At power 0.94 its p = 0.079 is real evidence
that the effect is not there at the size the original day showed. `hormuz` ES at 0.315 and
`ukraine` EN at 0.165 would miss a planted 8% effect two times in three; `ukraine` ES at
0.10 is not a test at all. Following the original's practice and the criterion fixed in
section 2.2, those three are published as **unpowered**, not as "no difference".

This is the honest shape of the result: **one informative null, three uninformative
ones, and zero hits.** The pre-registered criterion returns "not replicated" on the count.
The power table says the count is carried by one cell.

---

## 6. Whether the distinctive tokens are the same tokens

This is the second and stronger test, and it is the one that settles the question.

### 6.1 The method reproduces the original's own token lists

Pointed at the original day with the original's coverage, the same log-odds code recovers
the published lists:

| cell | country | recovered in the top 8 | published list length |
|---|---|---|---|
| `ukraine` EN | Syria | **6** (`both, eastern, efforts, pause, since, ushakov`) | 7 |
| `ukraine` EN | United Kingdom | **6** (`continues, moscow, nato, officials, recent, ukrainian`) | 7 |
| `ukraine` EN | India | 4 (`military, people, remains, talks`) | 8 |
| `ukraine` EN | United States | 3 (`air, purely, troops`) | 7 |
| `iran` ES | Chile | **6** (`aeroespacial, agencia, armada, fars, herido, segun`) | 6 |
| `iran` ES | Spain | **6** (`ataque, esta, guardia, ha, militar, revolucionaria`) | 7 |
| `iran` ES | Mexico | 5 (`armadas, bombardea, buques, estados, maritimo`) | 6 |
| `iran` ES | Argentina | 4 (`ataques, condeno, confirmo, region`) | 4 |
| `iran` ES | United States | 3 (`centcom, golfo, washington`) | 4 |

**43 of 56 published tokens**, across nine of the original's ten country lists. The tenth,
Pakistan in the English Ukraine cell, falls below five sources after near-duplicate removal
in this reproduction and has no list to compare. The instrument works.

### 6.2 On the new day it recovers almost nothing

The original reports ten country lists across these two cells. Four of them no longer
have a panel on the new day: India, Pakistan and Syria fall out of the English Ukraine
cell and Chile out of the Spanish Iran cell. For the six that remain:

| cell | country | day-2 top 8 | overlap with day 1 | expected by chance | p |
|---|---|---|---|---|---|
| `ukraine` EN | United States | `on, attacks, war, and, will, its, long, attack` | **0** | 0.193 | 1.00 |
| `ukraine` EN | United Kingdom | `them, equipment, combat, were, than, which, this, but` | **0** | 0.000 | 1.00 |
| `iran` ES | Spain | `ha, ya, programa, numero, no, propio, negado, eeuu` | **1** (`ha`) | 0.753 | 0.544 |
| `iran` ES | Mexico | `eu, ciberataques, jordania, redes, episodios, fallidos, ultimas, ultimos` | **0** | 0.095 | 1.00 |
| `iran` ES | Argentina | `trafico, ademas, uu, ee, medio, respondio, acuerdo, paises` | **0** | 0.139 | 1.00 |
| `iran` ES | United States | `seguridad, regimen, ofensiva, finales, fin, nueva, martes, teheran` | **0** | 0.000 | 1.00 |

**1 recovered token out of 35, against 1.18 expected by chance.** The single hit is `ha`,
the Spanish perfect auxiliary, which the original itself flagged as peninsular grammar
rather than editorial choice.

A more forgiving test was run because the exact top-8 overlap is a blunt instrument: for
every day-1 (country, token) pair, where does that token rank in day 2's own log-odds z
for the matching country, compared with the other countries of the same cell? If framing
is stable the matching country should rank it higher. In the Spanish Iran cell it does, by
0.077 of a percentile, p = 0.185. In the English Ukraine cell it goes the **wrong way**, by
0.406, p = 0.989: day 1's American markers are more distinctive of the United Kingdom on
day 2 than of the United States.

The tokens are not the same tokens, by any reading.

---

## 7. Controls, and the day's own sanity checks

Everything the original established about the shape of this measurement reproduces on the
new day. It is only the finding that does not.

**The representation is not inert.** Pooling the English sources of the day's two stories
and labelling them by story gives F = 9.86, p = 0.0005 on 261 sources; the Spanish
equivalent gives F = 5.01, p = 0.0005 on 114. The original measured 12.59 and 9.36. Subject
matter is trivially visible in these vectors on both days.

**Language is still the larger effect and would still be reported as country.** On the
all-language sets, with countries of five or more sources:

| cell | n | countries | languages | F country | F language | ratio |
|---|---|---|---|---|---|---|
| `ukraine` | 171 | 15 | 14 | 5.08 | **7.63** | 1.50 |
| `iran` | 280 | 18 | 8 | 5.31 | **14.47** | 2.72 |
| `hormuz` | 238 | 16 | 5 | 5.16 | **21.02** | 4.07 |

Every one at p = 0.0005 both ways, and language larger in every one, by 1.5 to 4.1 times
against the original's 1.4 to 3.9. **The language artefact replicates cleanly and the
country effect does not.** That contrast is the most reliable thing in either document: a
test run without holding language constant measures translation, on both days, at the
same magnitude.

**The length-matched null is calibrated on all four cells** at 1 to 6 rejections in 100,
so unlike the original day no cell here has to be discounted for context length. The
per-country median lengths are unequal (`iran` ES runs Mexico 75, Argentina 65, Spain 53,
US 52, Colombia 27) but not unequal enough to move the statistic.

**Near-duplicate wire copy is worth as much as it was**, 7 to 20 pairs per cell, and it
still decides a cell: `hormuz` ES goes from 0.030 to 0.311.

---

## 8. Exploratory, and not part of the verdict

Two things were looked at beyond the four pre-registered cells. Neither counts toward the
verdict and neither should be read as support for anything.

### 8.1 The day's best-powered English Ukraine panel

The pre-registered counterpart for cell 1 turned out to have power 0.165, which makes its
null uninformative. So the day's best-powered English `ukraine` panel was tested as well:
`s-3220cd669ee5` in run `20260903T192748Z`, 739 sources, article window
`2026-09-01T05:16Z` to `2026-09-03T18:47Z`, still disjoint from the original's. It admits
**68 sources over 4 countries**, which is almost exactly the shape of the original's
strongest cell.

It gives pseudo-F 2.27 at p = 0.0005 as measured. After near-duplicate removal, 24 pairs
and 53 admitted sources over 3 countries, it gives **F = 3.01 at p = 0.0005**, holding at
0.0005 when country is permuted within four-hour publication blocks. Its length-matched
null rejects 4 times in 100. Its power at 8% is 0.76. By every control in the original,
this cell passes, at more than twice the pseudo-F of anything the original found.

It is also not a finding. Its distinctive tokens, on the same 53 sources:

| country | most distinctive context tokens |
|---|---|
| India | `india, jaishankar, visit, minister, indian, affairs, an, external, during, end` |
| United Kingdom | `german, germany, ironclad, invasion, scale, full, 2022, our, supporting, for` |
| United States | `at, ap, hub, providing, has, more, destabilizing, associated, defense, will` |

India's markers are an Indian foreign-minister visit. The United Kingdom's are a
Germany-Russia story. These are different events sharing a cluster, and the statistic is
reporting which event each country covered. It is the exact failure the original recorded
in its section 7 for `argentina` ES, the cell with the largest F in that study, and it is
the third condition of the original's verdict: **the cell has to be one event**.

The lesson is not that this cell is spurious. It is that on a day when the four
pre-registered cells return nothing, the one cell that returns a large, control-surviving
result is a clustering artefact, and no statistic in this family can tell the two apart.
Whatever gets built would have shipped this one.

### 8.2 The English cells of the same stories

`iran` EN (n = 146, 7 countries) and `hormuz` EN (n = 142, 7 countries) were also
available, since they come from the same fetch. They are the original's cells 8 and 10,
both null on the original day. They were not tested here, because the original did not
count them among the four and testing them would only add cells that could go either way
to a verdict already fixed at four. Their shapes are recorded so a later reader can see
what was on the table and not taken.

---

## 9. Verdict

**Not replicated.**

Of four cells fixed before the test, **zero** reached p <= 0.05 on an independent day with
every control the original applied, against a pre-registered threshold of three. One was
significant before near-duplicate removal and did not survive it. Of the 35 published
distinctive tokens whose country still had a panel, **one** came back where 1.18 were
expected by chance, and the same code recovers 43 of 56 of those tokens when pointed at
the original day. The one replication cell with the power for its null to mean anything,
`iran` ES at power 0.94, returned p = 0.079 where the same cell on the original day
returned p = 0.030 at power 0.89.

Two qualifications, both of which cut against reading this as a clean refutation, and
neither of which rescues the finding.

**The replication was weaker than the original.** Three of four cells came back
underpowered, at 0.165, 0.315 and 0.10, because the day's clustering did not produce
comparable country panels. Those three nulls are evidence of nothing. If the effect is
real and of the size the original measured, this design would have missed it in three
cells out of four on this day. But it would not have missed the tokens, and the tokens are
gone.

**The original's own numbers are more fragile than it reported.** Reproduced on the
original day at the original's coverage, two of the four surviving p-values cross 0.05 on
nothing but which member of a near-duplicate pair is dropped. The original's verdict said
four hits in ten is what one day of noise plus a real effect looks like from the outside.
Two of those four were an unstated tie-break, which makes the outside view worse than it
looked.

**What should be built: nothing, on this.** The original attached three conditions to its
signal. The first two, hold language constant and expect an 8% effect floor, both hold up
here and are worth keeping in the project's memory. The third, that the cell has to be one
event, is the one that fails, and section 8.1 shows it failing at more than twice the
pseudo-F of anything that passed. That is not a sample-size problem and more days will not fix
it. Until the clustering can guarantee one event per cell, a country-context measurement
will report cluster heterogeneity as framing whenever the two are available to it, and
will report nothing the rest of the time.

The headline naming mark remains the only measurement this project has.

**What would change the answer.** Not a bigger corpus and not embeddings. A same-event
guarantee, or a unit smaller than the cluster. The original's own next-step-after-this
was to make the published unit a *pair* of countries rather than a set; that is still the
right shape, but it needs a cell whose sources are one event, and providing that is a
clustering problem rather than a statistics problem.

---

## 10. What could not be established

- **Whether the three unpowered cells are flat.** `ukraine` EN, `hormuz` ES and
  `ukraine` ES came back at power 0.165, 0.315 and 0.10 and their p-values carry no
  information in the direction of absence. Only `iran` ES tested the hypothesis. A third
  day would not obviously fix this: the panels are whatever the day's clustering yields.

- **Whether a differently chosen run would have replicated.** One run of four was used,
  chosen on source counts before any statistic. The other three were not tested and the
  window for each is disjoint from the original's, so the experiment could be run again on
  any of them. Doing so after seeing this result would not be a replication.

- **Whether the original's four cells are noise or a real effect that this day could not
  see.** The count says the former, the power says the count rests on one cell, and the
  token test says the former. They point the same way but they are not the same evidence
  and none of them is decisive on its own.

- **What the near-duplicate tie-break should be.** The original does not say which member
  of a pair it drops, and section 3.2 shows the choice moving two of its four published
  p-values across 0.05. Dropping the shorter, the later, or the more central source are
  all defensible and they do not agree. Any future version has to fix this in code and say
  so.

- **Whether the enriched `:01` plus `:02` coverage is better for this question.** It is
  more complete, 96.4% against 84.8%, and it changes the answers: on the original day it
  moves `ukraine` EN from 0.057 to 0.018 and `ukraine` ES from 0.014 to 0.059. More data
  per source is not neutral here, because longer contexts also create more near-duplicate
  pairs, 30 against 22 in the same cell.

- **Whether exact alias matching is what the original did.** It is inferred from the
  original's prose and confirmed by reproducing its published median context lengths to
  within three tokens, which is strong but not the same as reading its code. If it used
  substring matching, section 3.2's reproduction is against the wrong baseline; the day-2
  results were computed both ways and the verdict is the same under either, at 1 of 4
  under substring matching and 0 of 4 under exact.

- **Anything about the six cells the original found null.** They were not rebuilt. A
  replication tests the hypothesis that was fixed, and the six nulls were not part of it.

- **Whether the token test would pass on two days of the same sub-event.** The two days
  carry different sub-events of the same two conflicts, so the token overlap is a lower
  bound. It came in at chance, and framing words like `civilians`, `talks`, `nato` and
  `bombardea` had every opportunity to recur and did not, but a design that compared two
  windows on one continuous event would test this better and was not available here.

- **The 3.6% of sources with no n-gram coverage**, and the four quarters where one of the
  two files 404'd. Whether the missing articles are missing at random with respect to
  country is still untested, as it was in the original.
