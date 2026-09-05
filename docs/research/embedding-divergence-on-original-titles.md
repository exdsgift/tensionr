# Distance between headlines: does it carry political division?

Research for the question raised on 2026-09-05: instead of generating a report with a
generative model, encode the grouped headlines and score how far apart they are.

Everything here was measured on the run `20260905T115847Z` as published to the `data`
branch. The script is `tools/embedding_divergence.py` and is run by hand.

---

## 0. Bottom line

Four findings, and two of them contradict what the person running the experiment
predicted beforehand, including the one who wrote this document.

1. **There is a real effect, and it is about a third of what it first appears to be.**
   Crossing a polity boundary with the language held constant moves the mean cosine
   distance to 0.6415 against 0.4665 for two outlets inside one polity. But shuffling
   the polity labels at random *still* produces a gap of +0.0678. Read against that null
   rather than against zero, the observed +0.1020 leaves an excess of roughly **+0.034**,
   at about 3.4 standard deviations of the shuffled distribution (p = 0.007, 1 of 300
   rounds as extreme).

2. **The ranking is not what a reader would call political division.** The most
   "divergent" story is a stock-market piece, the second is Serena and Venus Williams
   being knocked out of a doubles tournament. The Falklands story, where UK and
   Argentine framing is about as predictable as journalism gets, ranks sixth of twelve.

3. **This is not the small-sample bias.** That was the prediction on record, and it is
   wrong: the rank correlation between story size and gap is **+0.105**, near zero and
   the wrong sign. Small stories are not what is being rewarded here.

4. **The polity term is larger than the language term, which was also predicted wrongly.**
   The expectation on record was that the polity term would come out near zero because
   the vectors could not carry framing. It does not. What follows is an argument that
   this is the wrong reading of the same numbers.

The verdict in §5 is that this should not become a published figure, but the reason is
not the one anybody expected going in.

---

## 1. What was measured, and how it differs from what was already refused

Issue #8 measured semantic spread over GDELT's own `gsg_docembed` vectors, grouped by
language, and refused it: multilingual wire-identical wildfire coverage ranked first at
0.2654, the visibly divergent Trump/Iran story fourteenth at 0.1401, and a story carried
by Russian *and* Ukrainian outlets nineteenth at 0.0700.

Two things are different here.

**The text.** `gsg_docembed` vectors are Universal Sentence Encoder v4 applied to
GDELT's machine translation into English. Framing is the first thing translation
flattens: *neutralised* and *killed* become one English word before any vector exists.
This run ignores those vectors and re-encodes the `title` field, which is the
publisher's own headline in its own language.

**The contrast.** Grouping by language made language and polity indistinguishable. Here
the comparison is *within a language*: same story, same language, different polity,
against same story, same language, same polity. This is the design
`language-residual.md` used on the actor channel, where it separated a genuine polity
term (+0.086, P(≤0) = 0.001) from a language term indistinguishable from zero (+0.037).

**Model.** `paraphrase-multilingual-mpnet-base-v2`, hosted at Hugging Face and called
over HTTP. Nothing runs locally and the engine's three runtime dependencies are
untouched. LaBSE was excluded on measurement (cross-lingual STS 73.5 against 83.7 for
the XLM-R/SBERT family: it wins at finding translations and loses at judging
similarity). The multilingual-e5 family was excluded because it compresses pairwise
similarity into 0.76–0.92.

**Corpus.** The 20 banded stories of the run: 2,578 evidence rows, 2,577 after
collapsing syndication, of which **1,195 are dropped for having no polity** and 1,382
are usable. That 46% loss is the polity-placement rate showing up as a direct cost, and
it is the single biggest limitation on this measurement.

---

## 2. Results

### Pooled

| cell | pairs | mean cosine distance | 95% CI |
| --- | ---: | ---: | --- |
| same language, same polity | 7,361 | 0.4665 | [0.4617, 0.4713] |
| same language, different polity | 9,994 | 0.6415 | [0.6372, 0.6461] |
| different language | 111,826 | 0.5078 | [0.5068, 0.5088] |

Pooled polity gap **+0.1750**. Mean of per-story gaps **+0.1020**; the two differ
because story sizes differ by a factor of twenty, and only the second is comparable to
the permutation null.

### Permutation

Polity labels shuffled *within* each (story, language) block, 300 rounds. Shuffling
within language is what makes it a test of political structure rather than of language
composition.

    shuffled gap   mean +0.0678   sd 0.0101
    observed       +0.1020
    rounds at least as extreme   1/300   (p = 0.007)

**The shuffled gap is not zero.** With polity assigned at random the measure still
reports +0.0678. Any figure from this measure has to be read against that, and reporting
+0.1020 as "the political divergence" would be reporting two thirds estimator artefact.

### Per story

Twelve of twenty stories have at least 30 pairs in both cells.

| gap | naive | n | pairs (same/diff polity) | story |
| ---: | ---: | ---: | ---: | --- |
| +0.3150 | 0.6730 | 58 | 327/143 | The stock market just did something for the first time |
| +0.2661 | 0.5793 | 19 | 48/123 | Serena and Venus Williams out of the doubles |
| +0.2263 | 0.4795 | 66 | 38/218 | Israel and Hezbollah battle over a hill in Lebanon |
| +0.2061 | 0.5820 | 176 | 744/750 | Trump calls the Iran conflict "small potatoes" |
| +0.1405 | 0.4100 | 124 | 202/431 | Nepal rescuers find two alive after 10 days |
| +0.1267 | 0.7240 | 164 | 1290/5629 | The UK-controlled Falkland Islands |
| +0.1000 | 0.4282 | 57 | 314/41 | Saxony-Anhalt: what will AfD do |
| +0.0460 | 0.2621 | 95 | 93/269 | Bolivia military base explosion |
| +0.0273 | 0.4038 | 23 | 190/63 | Trump disparages Mexico over tamales |
| +0.0162 | 0.4946 | 400 | 3452/1653 | Witkoff and Kushner travel to end the war in Ukraine |
| +0.0042 | 0.4573 | 34 | 159/402 | Pachuca beat Juárez |
| −0.0092 | 0.6598 | 19 | 48/123 | Colombia's president announces a capture |

Prediction on record before the run: most divergent Falklands, Israel/Hezbollah,
Trump/Iran; least divergent Pachuca, Williams, Musk's taxi.

Scored: two of the three predicted-most are in the top four. One of the predicted-least
is second to bottom. **Williams is second from the top.** Musk fell below the pair
threshold and is not ranked.

### Size

Rank correlation between story size and gap: **+0.105**. The hypothesis that the
ranking is driven by the upward small-sample bias, which this project has been warned
about three times, is not supported.

---

## 3. What the numbers actually say

The measure detects something above chance. What it detects is not political division.

The evidence is the ranking, not the effect size. A stock-market story and a tennis
result are the two most "divergent" stories in the window, above a shooting war in
Lebanon and an active sovereignty dispute. There is no reading of *political division*
under which that ordering is correct.

There is a reading under which it is perfectly sensible, and it is the one to take
seriously: **the measure is detecting how differently a story is angled from one country
to another, which is mostly a function of local relevance rather than of politics.**
Argentine, Mexican and Spanish coverage of a doubles match at a tournament each lead with
their own player, their own bracket, their own stakes. That is a real difference between
headlines and the model is right to see it. It is simply not disagreement.

The Falklands result is the sharpest form of this. It ranks **first** on the naive
all-pairs figure (0.7240, the highest in the window) and **sixth** once the same-polity
baseline is subtracted. The subtraction is doing exactly what it was designed to do:
UK and Argentine outlets differ, but UK outlets also differ from each other about as
much, because the story is a background explainer that every desk writes its own way.
The political boundary adds little on top of the editorial one.

### A caution about the third cell

The cross-language mean (0.5078) is **lower** than the same-language cross-polity mean
(0.6415). Two headlines in different languages are, on this model, closer together than
two headlines in one language from different countries. That is not a fact about the
news: a multilingual paraphrase model is trained to place translations near each other,
so it pulls cross-language pairs together by construction. The third cell is therefore
useless as a scale reference and should not be quoted as "the language effect is small".

---

## 4. Two errors made while doing this, recorded

**The permutation initially compared the wrong two quantities.** The observed statistic
was pooled over all pairs (+0.1750) while the null was a mean of per-story gaps
(+0.0678). Those differ whenever story sizes differ, and comparing them produced an
apparently decisive result out of an arithmetic mismatch. This is the same class of
defect that made issue #8's permutation z-scores untrustworthy, reproduced here by
someone who had just finished reading about it. Fixed by computing the observed
statistic the same way the null is computed.

**The size-bias hypothesis was asserted before it was tested.** The per-story table was
read as showing small stories on top, and it was announced as such. The rank correlation
is +0.105. The two stories at the top happen to be small; the correlation across all
twelve is not there.

---

## 5. Verdict

**Do not publish this as a divergence figure.** Not because it measures nothing, but
because what it measures does not match the name it would be given. A number on the page
called "political divergence" that puts a tennis result above a war would be worse than
having no number, and this project already removed one index for ranking noise first.

**What survives.**

- The finding itself is worth keeping: country-of-publication accounts for a measurable
  part of how a story is worded, above an editorial baseline, at about +0.034 after the
  null is subtracted. That is a fact about the corpus, and it is publishable as a fact.
- The script is worth keeping as a diagnostic. A story whose same-polity baseline is
  unusually high is a story whose cluster may be loose, and that is a cheaper check on
  clustering quality than anything currently in the engine.
- The method is worth keeping. Within-language, cross-polity, against a within-language
  permutation null is the right shape for this question, and it is now implemented.

**What would change the verdict.** A measure that separates *how* a thing is said from
*what* is being said. Every attempt in this project so far, including this one, has
found that general-purpose sentence embeddings encode the second and not the first.
That is a property of the training objective, not of the corpus, and no amount of
residualising recovers information the vector never carried. The actor-naming channel
remains the only measure here that survives contact with a hand-labelled expectation,
and the reason is that it asks a question a human can answer from the headline: *did
this publisher use this name?*

The next thing worth trying in that family is not another embedding. It is another
discrete, checkable property of the surface text: which verb is attached to an actor,
or whether a casualty figure is attributed to a named agent or left agentless.
