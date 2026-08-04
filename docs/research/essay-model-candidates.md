# Which model on Hugging Face can write the essays, and by which route

Research for [#74](https://github.com/exdsgift/tensionr/issues/74), under the map in
[#59](https://github.com/exdsgift/tensionr/issues/59). Written 2026-08-04.

**Question.** [#63](https://github.com/exdsgift/tensionr/issues/63) fixed the shape — a hosted model
over the network, one call per essay, generated once per story and kept — and left *which* model
open, to be settled against real output rather than asserted. This document establishes what is true
about the candidates and the routes. The choice is the owner's.

**A constraint arrived after the ticket was written**, and it is the reason this document is not
shaped like the one #74 asked for:

- **The model must be free.** No per-token cost, no paid endpoint. That reverses the part of #63 that
  chose a hosted paid API.
- **Everything runs under GitHub Actions.** Running a model on the owner's own machine is out. Models
  come from Hugging Face.

So the dedicated-endpoint route is excluded on its face — Hugging Face requires *"an active
subscription and credit card on file"* for it ([Inference Endpoints
pricing](https://huggingface.co/docs/inference-endpoints/pricing)) — and two routes remain: the free
inference credit, and weights in the runner.

**Measured on.** The published corpus at `origin/data:data/stories.json`, run **20260804T194757Z**,
a 48-slot (12-hour) window carrying 217,396 articles, 2,464 stories, 23 with a band. Tokenizer
measurements were made locally against each candidate's own `tokenizer.json`, downloaded from the
Hub. The live route inventory is `https://router.huggingface.co/v1/models`, fetched unauthenticated
(HTTP 200, 131 models) on 2026-08-04. §9 records what could not be determined.

**No money was spent.** No inference call was made, on any route, free or paid. Every cost figure
below is arithmetic over published prices and measured token counts. §10 gives the script that would
settle the remaining questions and states what it would cost.

---

## 0. Verdict first

1. **The ticket's central measurement is wrong by three to seven times, and not because anybody
   miscounted.** #74 requires *"context of at least ~80k tokens"* on the basis that the largest story
   is ~74,250 input tokens. Measured on the current corpus that figure is **411,000 to 511,000
   tokens** for the largest featured story, depending on whose tokenizer counts it. Three independent
   causes compound (§2): the window doubled from 6 hours to 12 on 2026-08-03 for a reason unrelated
   to the essay, so the largest featured story went from 297 sources to **592**; #63 costed a
   reconstructed article at 1 KB when the measured median is **2,288 characters**; and #63 used one
   flat rate of 250 tokens per KB for all 36 languages when measured fertility on this corpus's own
   text is **1.7× to 3.8× the English rate** for Greek, Cyrillic and Arabic script.

2. **Nothing servable reads the full bodies of the largest featured story in one call.** The widest
   window any provider offers today is 1,048,576 tokens, and at the *mean* reconstruction length the
   largest story needs 548,000–681,000 tokens — which fits, but only just, and only at 2026's widest
   commercial offer. At the p90 length it needs 1.09–1.35M and fits nothing. **The input has to be
   cut**, and §3 measures exactly how much survives each cut.

3. **The free route works, and the arithmetic is tighter than it is comfortable.** Hugging Face gives
   every free account **$0.10 of inference credit a month** ([pricing
   page](https://huggingface.co/docs/inference-providers/pricing), quoted in §4.1). At the cheapest
   route wide enough to be useful — `Qwen/Qwen3-4B-Instruct-2507` served by nscale at **$0.01 per
   million input tokens, 262,144-token window, structured output supported, 582 ms to first token**
   — reading the **first 500 characters** of each source's body costs $0.00069 an essay, which is
   **145 essays a month on the free credit**. Five new featured stories a day is 150 a month. The
   free tier covers the requirement with no margin at all.

4. **There is one genuinely zero-priced route, and the provider says in its own words that it is
   free.** `prism-ml/Ternary-Bonsai-27B-gguf` — a ternary (1.71 bits/weight) quantisation of
   Qwen3.6-27B, Apache-2.0, 761,269 downloads — is listed by Together at `pricing.input: 0`,
   `pricing.output: 0`, 262,144 context, 312 ms to first token, and Together's own model page states
   three times *"Available free on Together AI serverless infrastructure"* with a *"99.9% SLA"*. It
   would make the whole question free at 27B-class quality. Three cautions: HF's own router record
   says `is_free: false` alongside the zero price, which is a contradiction; Together's pricing table
   gives the input price as 0.00 with the **output** field unset rather than zero, so output may not
   be free (immaterial here — the essay generates ~400 tokens); and **it has no multilingual
   evaluation of any kind** (§5.6). §9.1 says what would settle it.

5. **Route 3 — weights in the runner — fails on two grounds, and #63's stated reason was the weakest
   of the three available.** #63 rejected local weights because *"nothing that fits in a runner with
   4 vCPU, 16 GB and no GPU reads that set at a level worth publishing"*. That reasoning is about
   quality. The second objection is arithmetic: prefill costs `2·N·T` FLOPs plus a quadratic attention
   term, and the quadratic term is what bites — at 450,000 tokens it is **16× the weight term** for a
   4B model, so parameter count stops being the binding variable (§4.3). The third objection is
   contractual and does not depend on any measurement: 100+ CPU-hours a day of model inference fits
   every documented GitHub quota and fails the Actions terms' *"burden … disproportionate to the
   benefits"* clause, whose remedies reach the account that also publishes the site (§4.3). The
   low-bit 27B build in finding 4 weakens the second objection — a **7.15 GB resident footprint** and
   a **~75% linear-attention backbone** put a 27B-class model inside 16 GB at the full 262K window —
   but not the third, and whether it prefills fast enough is the one number nobody has published
   (§9.2).

6. **This does not reopen #63, and I want to be exact about why.** #63's decision — hosted, over the
   network, one call per essay, generated once and kept — survives, and finding 3 vindicates it: the
   hosted route is free at the required volume and the local route is not clearly feasible at any
   volume. What #63's *arithmetic* cannot support is the premise that 74k tokens is the size of the
   job, and what its *stated reasoning* cannot support is the rejection of local weights on quality
   grounds when the decisive objection is compute. Both are corrections to a decision that holds, not
   grounds to retake it. §11 sets out the one finding that would reopen it if it were confirmed.

7. **The quality evidence is thin, old, and it points one way.** On **GreekMMLU** — 21,805 natively
   authored Greek questions, published February 2026, independent of every vendor — a 27B model
   scores **79.41**, a 4B model **62.24**, and a 1.7B model **29.68 against a random baseline of
   30.42**. Greek is this corpus's third language by volume. The model class the free budget affords
   is the 4B class, and 4B in Greek is 17 points below 27B and 31 below a frontier model (§5.2).

8. **Licences are not the constraint.** The models that matter here are Apache-2.0 or MIT with no
   output obligation, no attribution duty and no gate: Qwen3/3.5/3.6 (Apache-2.0), Gemma 4
   (Apache-2.0 — Gemma 4 left the Gemma Terms of Use), DeepSeek V4 (MIT), GLM-5.x (MIT), gpt-oss
   (Apache-2.0), Nemotron-3 (OpenMDW-1.1, the only licence that *expressly* disclaims output
   obligations). Avoid Cohere's CC-BY-NC — not because a free site fails the NonCommercial test, but
   because whether the licence reaches model output at all is unresolved (§6.4). One duty applies
   whatever is chosen: **label the essays as machine-written** (§6.6).

---

## 1. The corpus, as it stands today

| | Run 20260804T194757Z |
| --- | --- |
| Window | 48 slots, 12 hours, 0 missing, parse fidelity 1.0 |
| Articles in window | 217,396 |
| Stories | 2,464, of which **23 publish a band** |
| Featured (top five by peak division over the span) | **1,837 sources across 37 languages** |

The five that would carry an essay, ranked as `_feature()` in `src/tensionr/stories/run.py:160`
ranks them:

| | id | band | span division | sources | collapsed | languages |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `s-26595bfbd379` | russia | 0.9995 | 497 | 697 | 33 |
| 2 | `s-5cba1c7c130f` | iran | 0.9969 | 146 | 205 | 13 |
| 3 | `s-0d8b33c7cb87` | spain | 0.9918 | 338 | 297 | 24 |
| 4 | `s-9b833d8db991` | israel | 0.9850 | 264 | 424 | 23 |
| 5 | `s-034a3c362b8d` | hormuz | 0.9660 | **592** | 885 | 30 |

Language mix over those five — 37 languages, and the top eight are close to #74's measurement with
Greek and Russian trading places:

| | sources | share | | sources | share |
| --- | --- | --- | --- | --- | --- |
| English | 581 | 31.6% | Portuguese | 43 | 2.3% |
| Spanish | 210 | 11.4% | Italian | 43 | 2.3% |
| **Greek** | 125 | 6.8% | Romanian | 40 | 2.2% |
| **Russian** | 124 | 6.8% | Chinese | 37 | 2.0% |
| **Arabic** | 106 | 5.8% | Bulgarian | 31 | 1.7% |
| French | 88 | 4.8% | Albanian | 27 | 1.5% |
| **Turkish** | 62 | 3.4% | Slovak | 26 | 1.4% |
| **Ukrainian** | 61 | 3.3% | *29 more* | 133 | 7.2% |
| German | 47 | 2.6% | | | |

The tail matters more than its share suggests. Armenian (5), Hebrew (11), Georgian (1) and Korean
(11) are the languages where a tokenizer's coverage collapses (§2.3), and Greek — the third language
by volume — is the worst case for the tokenizer family that is otherwise cheapest.

---

## 2. What the essay actually has to read, and why the ticket's number is wrong

#74 states the requirement as *"a usable context window is **at least ~80k tokens**"*, from a table
whose largest row is 297 sources at ~74,250 tokens. Three things moved that number, and none of them
is an error by anybody.

### 2.1 The window doubled, for a reason that has nothing to do with the essay

`WINDOW_SLOTS` went from 24 to 48 in `5595673` on 2026-08-03 — *"feat: ask for a run every four
hours, with a twelve-hour window (#48)"*. The commit's own reasoning is about coverage, not essays:
*"Twelve hours covers two consecutive misses."* The consequence for the essay is that the largest
featured story went from **297 sources to 592**.

That is the first thing to notice about this requirement: **it is not a property of the essay, it is
a property of a constant that was changed for an unrelated reason, and it can change again.** #74's
~74,250 becomes ~148,000 on #63's own method with no other change.

### 2.2 A reconstructed article is 2.3× the size #63 costed it at

#63 costs the input at *"roughly 250 tokens per KB of reconstructed text"* and arrives at 250 tokens
per source. The rate is right; the size is not.
[`reconstructed-text-rights.md` §8.1](reconstructed-text-rights.md) measured the reconstruction on a
real GDELT minute file:

| | median | mean | p90 | max |
| --- | --- | --- | --- | --- |
| reconstruction, characters | **2,288** | 3,051 | 6,067 | 32,714 |
| reconstruction, gzipped bytes | 1,048 | 1,208 | 2,075 | — |

The 1 KB figure #63 used is the **gzipped** size. The text is 2,288 characters at the median. English
at the measured 0.231 tokens/character is ~529 tokens per source, not 250.

### 2.3 The flat rate is wrong per language by 1.7× to 3.8×, and this is measurable on our own text

A tokenizer's fertility is not a constant across scripts. Measured on **3,073 real headlines from
this corpus**, grouped by GDELT's language field, with each candidate's own `tokenizer.json`:

**Tokens per character** (lower is better):

| tokenizer | vocab | en | es | **el** | **ru** | **ar** | fr | **tr** | **uk** | de | he | hy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-235B-A22B-Instruct-2507 | 151,669 | 0.232 | 0.307 | **0.877** | 0.392 | 0.387 | 0.311 | 0.364 | 0.510 | 0.320 | 0.432 | 0.992 |
| DeepSeek-V3.1 | 128,815 | 0.231 | 0.291 | 0.493 | 0.356 | 0.405 | 0.298 | 0.437 | 0.451 | 0.308 | 0.521 | 0.586 |
| gpt-oss-120b | 200,019 | 0.226 | 0.253 | 0.419 | 0.309 | 0.333 | 0.266 | 0.326 | 0.373 | 0.266 | 0.416 | 0.334 |
| Llama-3.3-70B-Instruct | 128,256 | 0.227 | 0.294 | 0.433 | 0.355 | 0.406 | 0.308 | 0.328 | 0.359 | 0.320 | **0.992** | **1.607** |
| Llama-4-Scout | 201,135 | 0.230 | 0.245 | 0.397 | 0.255 | 0.374 | 0.260 | 0.297 | 0.321 | 0.264 | 0.499 | 0.878 |
| Mistral-Small-3.2-24B | 131,072 | 0.246 | 0.269 | 0.427 | 0.339 | 0.315 | 0.262 | 0.355 | 0.378 | 0.279 | 0.474 | 0.347 |
| gemma-3-27b-it | 262,145 | 0.228 | 0.263 | 0.433 | 0.302 | 0.361 | 0.277 | 0.320 | 0.346 | 0.270 | 0.496 | 0.520 |
| GLM-4.6 | 151,365 | 0.227 | 0.279 | 0.460 | 0.310 | 0.431 | 0.296 | 0.376 | 0.382 | 0.293 | **0.992** | **1.844** |

**The same, as a multiple of that tokenizer's own English rate:**

| tokenizer | **el** | **ru** | **ar** | **tr** | **uk** | zh | he | hy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-235B-A22B-Instruct-2507 | **3.78×** | 1.69× | 1.67× | 1.57× | 2.19× | 3.17× | 1.86× | 4.27× |
| DeepSeek-V3.1 | 2.13× | 1.54× | 1.75× | 1.90× | 1.95× | 3.00× | 2.26× | 2.54× |
| gpt-oss-120b | 1.86× | 1.37× | 1.48× | 1.44× | 1.65× | 3.79× | 1.84× | 1.48× |
| Llama-3.3-70B-Instruct | 1.91× | 1.57× | 1.79× | 1.45× | 1.58× | 4.08× | **4.37×** | **7.08×** |
| Llama-4-Scout | 1.73× | 1.11× | 1.63× | 1.29× | 1.40× | 3.54× | 2.17× | 3.83× |
| gemma-3-27b-it | 1.90× | 1.32× | 1.58× | 1.40× | 1.52× | 3.53× | 2.17× | 2.28× |
| GLM-4.6 | 2.02× | 1.37× | 1.89× | 1.65× | 1.68× | 3.07× | **4.36×** | **8.11×** |

Two things worth stating separately.

**Greek is the expensive language, and it is expensive precisely where the price is lowest.** Qwen3's
tokenizer spends 0.877 tokens per Greek character — nearly one token per character — which is 3.78×
its English rate and more than twice what DeepSeek, Llama 4 or Gemma spend. Greek is 6.8% of the
featured five's sources. The Qwen family is the cheapest route on the router; it is also the worst
tokenizer for the project's third language.

**A rate of ≥1 token per character means the tokenizer has no vocabulary for that script and is
falling back to bytes.** Llama-3.3 and GLM-4.6 both hit exactly 0.992 on Hebrew and 1.6–1.84 on
Armenian. That is a diagnostic, not a cost: it is independent evidence, derived from the artefact
rather than from a claim, that those models' training data contained little of those scripts. It is
the one capability signal in this document that does not depend on anybody's benchmark or anybody's
model card.

**Method and its limits.** Headlines are a proxy for bodies. Fertility is mostly a property of the
script and the language's morphology, so it should transfer, but headlines are short, capitalised
and carry masthead suffixes, so the absolute rates are approximate. 1,828 of the 1,837 featured
sources (99.5%) fall in a language with enough material to measure a rate; the remaining nine
(Azerbaijani, Finnish, Georgian, Latvian, Persian, Slovenian) fall back to the model's English rate,
which understates them.

### 2.4 The input budget, restated

Combining the three: sources per story from the corpus, 2,288 characters per source from
`reconstructed-text-rights` §8.1, and tokens per character per language from §2.3.

**Input tokens for one essay call, at the median reconstruction:**

| | s1 (497) | s2 (146) | s3 (338) | s4 (264) | s5 (592) | largest | run total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.x | 442,816 | 109,827 | 302,313 | 212,878 | 510,989 | **510,989** | 1,578,823 |
| DeepSeek V3.1/V4 | 392,436 | 107,972 | 256,629 | 202,636 | 464,757 | 464,757 | 1,424,430 |
| Llama-3.3-70B | 386,231 | 117,312 | 255,293 | 202,764 | 468,446 | 468,446 | 1,430,046 |
| Mistral-Small-3.2 | 364,821 | 124,260 | 240,325 | 183,199 | 447,445 | 447,445 | 1,360,050 |
| GLM-4.6 | 377,444 | 108,637 | 249,268 | 207,261 | 465,090 | 465,090 | 1,407,701 |
| gemma-3-27b | 347,880 | 109,224 | 234,105 | 182,150 | 424,503 | 424,503 | 1,297,862 |
| Llama-4-Scout | 328,413 | 108,714 | 221,547 | 178,655 | **411,095** | **411,095** | 1,248,425 |
| **#63's method** (250/source, flat) | 124,250 | 36,500 | 84,500 | 66,000 | 148,000 | *148,000* | *459,250* |

At the **mean** length the largest story is 548,187–681,393 tokens; at **p90**, 1,090,086–1,354,970.

So the requirement is not ~80k. It is **~411k–511k at the median, per essay, for the largest of the
five** — 2.8× to 3.5× #63's figure for the same run, and 5.5× to 6.9× the figure #74 records.

---

## 3. What fits, and what is lost by cutting

Since nothing reads the whole thing reliably, the design question becomes *which* cut. There are two
shapes, and they cost the essay different things.

**Cut A — truncate every body.** All 592 sources are read, but only the first *n* characters of each.
Characters per source that fit a given window, on the largest featured story:

| tokenizer | 128k | 200k | 262k | 1M |
| --- | --- | --- | --- | --- |
| Qwen3.x | 573 | 896 | 1,174 | 2,288 (all) |
| DeepSeek | 630 | 985 | 1,291 | 2,288 |
| gemma-3 | 690 | 1,078 | 1,413 | 2,288 |
| Llama-4-Scout | 712 | 1,113 | 1,459 | 2,288 |

**Cut B — sample the sources.** Full 2,288-character bodies, but only the first *k* sources:

| tokenizer | 128k | 200k | 262k | 1M |
| --- | --- | --- | --- | --- |
| Qwen3.x | 104 | 194 | 263 | 592 (all) |
| Llama-4-Scout | 175 | 279 | 336 | 592 |

**Cut A is the better fit for the decisions already taken, and the reason is #60.** The gate requires
that an asserted relation be found in *that source's own text*, so the essay may only attribute to
sources it has read. Under Cut B it can attribute to 104–336 of 592 publishers and is structurally
blind to the rest — and the measure the essay is describing is computed over all 592. Under Cut A it
can attribute to every one of them, at the price of only having seen each one's opening. News prose
is written to put the framing first, and [#70](https://github.com/exdsgift/tensionr/issues/70)
already observed that on the story it was reasoned about *"the attributed relations were all in the
headlines"*. A 500–1,200 character lede is where the framing lives.

**Cut A at ~500 characters is not the same thing as the option #63 rejected.** #63 rejected *reading
only headlines*, on the ground that *"a model reading only headlines makes the reconstruction
pipeline pointless and returns the essay to being a paraphrase of headlines"*. Measured on this
corpus, an English headline averages 77 characters. 500 characters is 6.5× that and is body text —
the reconstruction pipeline is still doing work. It is a real reduction and it should be recorded as
one, but it is a different reduction from the one that was declined.

---

## 4. The routes

### 4.1 Route 1 — the free inference credit

The old serverless API is gone. `api-inference.huggingface.co` no longer resolves;
`https://huggingface.co/docs/api-inference/index` 302s to the Inference Providers docs. The current
surface is `https://router.huggingface.co/v1`, OpenAI-compatible, and the docs state
that *"This service used to be called "Inference API (serverless)" prior to Inference Providers."*

**The credit**, quoted verbatim from
[the pricing page](https://huggingface.co/docs/inference-providers/pricing):

> Every Hugging Face user receives monthly credits to experiment with Inference Providers:
>
> | Account Type | Monthly Credits | Extra usage (pay-as-you-go) |
> | --- | --- | --- |
> | Free Users | $0.10, subject to change | yes (credits purchase required) |
> | PRO Users | $2.00 | yes |
> | Team or Enterprise Organizations | $2.00 per seat | yes |

And on exhaustion:

> **All users** can continue using the API after exhausting their monthly credits by purchasing
> additional credits. This ensures uninterrupted access to models for production workloads.

Two things follow that bear on this decision. The word is **"experiment"**, and the sentence about
production workloads is about *paying*. And the overage is **pre-purchase, not overage billing** —
"credits purchase required" — so the free tier is a hard stop, which is the failure mode a public
repository wants. There is no path by which a looping bug spends money on a free account.

**Billing is pass-through**: *"Hugging Face charges you the same rates as the provider, with no
additional fees. We just pass through the provider costs directly."*

**The route decides the window, not the model.** This is the single most operationally important
thing in the router data, and it is invisible from a model card. Fetched from
`https://router.huggingface.co/v1/models`:

| model | provider | context offered | $/M in | structured output |
| --- | --- | --- | --- | --- |
| `Qwen/Qwen3-235B-A22B` | novita | **40,960** | 0.20 | yes |
| `Qwen/Qwen3-235B-A22B` | nscale | **32,000** | 0.20 | yes |
| `meta-llama/Llama-3.3-70B-Instruct` | novita | **6,000** | 0.135 | — |
| `meta-llama/Llama-3.3-70B-Instruct` | groq | 131,072 | 0.59 | — |

`Qwen3-235B-A22B`'s own config declares 262,144. Novita serves it at 40,960 and nscale at 32,000.
Llama-3.3-70B is offered by one provider at **6,000 tokens**. A job that lets the router pick on
price can land on a 6,000-token window and fail hard on a 500,000-token prompt. **The provider must
be pinned**, and pinning disables the automatic failover the docs describe.

**The offers that matter.** Every route at ≥128k, cheapest input price first, from the same fetch:

| $/M in | context | model | provider | struct | ttft ms |
| --- | --- | --- | --- | --- | --- |
| **0** | 262,144 | `prism-ml/Ternary-Bonsai-27B-gguf` | together | no | 312 |
| **0** | 262,144 | `prism-ml/Ternary-Bonsai-27B-AWQ-4bit` | together | no | 282 |
| **0.01** | **262,144** | **`Qwen/Qwen3-4B-Instruct-2507`** | **nscale** | **yes** | **582** |
| 0.01 | 262,144 | `Qwen/Qwen3-4B-Thinking-2507` | nscale | yes | 650 |
| 0.02 | 131,072 | `meta-llama/Llama-3.1-8B-Instruct` | deepinfra | no | 362 |
| 0.037 | 131,072 | `openai/gpt-oss-120b` | deepinfra | yes | 441 |
| 0.05 | 131,072 | `google/gemma-3-4b-it` | deepinfra | yes | 394 |
| 0.05 | 131,072 | `google/gemma-3-12b-it` | deepinfra | yes | 332 |
| 0.06 | 202,752 | `zai-org/GLM-4.7-Flash` | deepinfra | no | 390 |
| **0.07** | **262,144** | **`google/gemma-4-26B-A4B-it`** | **deepinfra** | **yes** | 580 |
| 0.08 | 131,072 | `google/gemma-3-27b-it` | deepinfra | yes | 752 |
| 0.09 | 262,144 | `Qwen/Qwen3-235B-A22B-Instruct-2507` | deepinfra | yes | 477 |
| 0.09 | 262,144 | `Qwen/Qwen3-Next-80B-A3B-Instruct` | deepinfra | yes | 504 |
| 0.09 | **890,000** | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | nscale | yes | 641 |
| 0.09 | **1,048,576** | `deepseek-ai/DeepSeek-V4-Flash` | deepinfra | yes | 598 |
| 0.10 | 262,144 | `Qwen/Qwen3.5-9B` | deepinfra | yes | 2266 |

**What the free $0.10 buys.** Priced on the mean of the five featured stories, since #63 generates
once per story; a story that exceeds the window is charged at the window, because it must be cut to
fit:

| route | headline only | first 500 chars | first 1,000 chars | full body |
| --- | --- | --- | --- | --- |
| `Ternary-Bonsai-27B` @ together, $0 | free | free | free | free, but 2 of 5 exceed the window |
| **`Qwen3-4B-Instruct-2507` @ nscale, $0.01** | 941/mo | **145/mo** | 72/mo | 45/mo (3 of 5 cut) |
| `gemma-4-26B-A4B-it` @ deepinfra, $0.07 | 167/mo | **25/mo** | 13/mo | 7/mo (2 of 5 cut) |
| `Qwen3-235B-A22B-2507` @ deepinfra, $0.09 | 105/mo | 16/mo | 8/mo | 5/mo (3 of 5 cut) |
| `DeepSeek-V4-Flash` @ deepinfra, $0.09 | 117/mo | 18/mo | 9/mo | 4/mo |
| `Llama-4-Scout` @ nscale, $0.09 | 136/mo | 20/mo | 10/mo | 4/mo |

Against a requirement of roughly **150 essays a month** — five featured stories a day, each written
once and kept — the free credit affords exactly one combination with any margin at all: the **4B
model at 500 characters a source**. Everything else needs either PRO at $9/month, or a smaller cut,
or fewer new stories per day than five.

**How many essays a month is actually needed is not measurable from what is published.** Story
identity survives between runs ([#10](https://github.com/exdsgift/tensionr/issues/10)), so a story
featured today is often featured tomorrow, and only new entrants need an essay. The `data` ref is a
single force-pushed commit and the per-run records on `history` do not carry per-story source counts,
so the turnover of the featured five cannot be measured today. 150/month is the pessimistic bound —
every story new every day. §9.5 says what would settle it.

**Credential and failure.** A fine-grained HF token with the *Make calls to Inference Providers*
permission, in Actions secrets. Fork pull requests never receive it — GitHub's docs: *"With the
exception of `GITHUB_TOKEN`, secrets are not passed to the runner when a workflow is triggered from a
forked repository"* — and `stories.yml` runs on `schedule` and `workflow_dispatch` only, so no pull
request path reaches it, exactly as #63 recorded. Unauthenticated calls return **401 with an HTML
body**, not JSON, so a naive `response.json()` in error handling raises a parse error rather than
surfacing the status.

**Exhaustion returns HTTP 402, and the provenance of that needs stating.** There is **no
error-handling page in the Inference Providers docs** — `.../inference-providers/errors` is a 404, and
enumerating the whole doc set confirms one has never been published. The status code and message come
from Hugging Face's own forum, corroborated by a Hugging Face staff reply in the same thread
confirming the trigger condition:

> 402 Client Error: Payment Required for url: https://router.huggingface.co/…

> You have exceeded your monthly included credits for Inference Providers. Subscribe to PRO to get
> 20x more monthly included credits.

— [discuss.huggingface.co/t/148414](https://discuss.huggingface.co/t/148414) and
[/t/148551](https://discuss.huggingface.co/t/148551). Reported in 2025, so the wording may have
moved; the 20× ratio is consistent with $0.10 → $2.00. **This is the answer to what happens when the
model is unavailable mid-run**, and it is the right failure for this project: a distinct status code,
on a hard stop, with no silent billing.

**Automated scheduled use is permitted, and it is more than "not prohibited".** The Terms of Service
(effective 2022-09-15) contain no clause on automation, bots, scraping, rate limits, resale or fair
use — no prohibited-conduct section at all. The [Inference Services Supplemental Terms](https://cdn-media.huggingface.co/landing/assets/Supplemental+Terms+-+Inference+Services.pdf)
(effective 2025-04-28, which prevail over the ToS on conflict) define the service affirmatively as
programmatic: *"a machine learning model inference service **allowing to run inference
programmatically**"*. And Hugging Face publishes a first-party guide,
[*Automating Code Review with GitHub Actions*](https://huggingface.co/docs/inference-providers/guides/github-actions-code-review),
which walks through storing an `HF_TOKEN` as a repository secret and calling the router from a
workflow — and whose only warning about public repositories is about **cost control and who may
trigger the job**, not about permission.

Two smaller things worth recording. The credit is framed as being *"to experiment"*, but that is the
only appearance of the framing and the same page endorses *"production workloads"* in the next
paragraph, so the allowance is a **quantity**, not a **purpose** — nothing conditions it on the use
being evaluation. And the Supplemental Terms say access *"is available to Users for personal use and
to Organization accounts"*; that reads as naming which account types may access the service rather
than imposing a non-commercial limit, and nothing elsewhere develops it into a restriction — but it
is the only string in the corpus a scope objection could hang on, and **owning the token under an
Organization account removes the ambiguity at zero cost**.

**There is no other free route on Hugging Face.** Free CPU Spaces are no longer free to create:
*"CPU Basic has no hourly cost, but creating a new Space that runs on compute (Gradio or Docker)
requires a paid plan. Static Spaces are free for everyone."* ZeroGPU is genuinely free (2 Spaces for
free accounts in good standing) but capped at **5 GPU-minutes a day** for a free account, Gradio-only,
60 s default per call — enough for a handful of essays and nothing more. HF Jobs requires *"a positive
credit balance"*. And GitHub's own hosted inference is not an alternative either:
**GitHub Models was fully retired on 2026-07-30** and `models.github.ai` now returns HTTP 410.

### 4.2 Route 2 — dedicated inference endpoints

Excluded by the constraint, and the exclusion is on the face of the pricing page: Inference Endpoints
are *"accessible to Hugging Face accounts with an active subscription and credit card on file"*.
Recorded for completeness: they bill by the minute including the cold start, scale to zero after a
fixed non-configurable 15 minutes of idleness, return **502** while a replica initialises with no
request queue, and the cheapest GPU is $0.50/hour. Serving a 235B-class MoE with a 150k KV cache
needs on the order of 4×A100 80GB at $10/hour — about $7,300 a month if left running, against
fractions of a cent per call on Route 1. For a scheduled job that makes a handful of calls a day this
route is roughly three orders of magnitude the wrong answer even before the constraint.

### 4.3 Route 3 — weights in the runner

**The runner**, quoted from
[GitHub's docs](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), public
repositories:

> | Linux | 4 | 16 GB | 14 GB | x64 | `ubuntu-latest`, `ubuntu-24.04`, `ubuntu-22.04`, `ubuntu-26.04` |

and *"Use of the standard GitHub-hosted runners is free and unlimited on public repositories."*
The per-job limit is **6 hours**; concurrency on the free plan is 20 jobs, so the five essays can run
as a parallel matrix and the wall clock is one essay, not five.

**Correcting the framing this route is usually costed under.** The engine's 2400 s ceiling is the
engine's own timeout, not a platform limit. An essay job is a separate job and gets the full 6 hours,
and because #63 generates once per story and keeps the result, that job may lag the measurement
without breaking anything. Six hours per essay is available.

**Prefill is the whole cost, and its second term is the one that decides.** The essay generates
~400 tokens and reads hundreds of thousands, so decode throughput is irrelevant. Prefill costs

```
2·N·T                    weight matmuls
+ 2·L·T²·d_attn          causal attention
```

The second term is quadratic. For a 4B model at 450,000 tokens it is **16× the first**, which is why
choosing a smaller model does not rescue this route: below about 4B the attention term dominates and
parameter count stops mattering. Sanity check against published `llama-bench` internals: at T=512 the
formula puts attention at 0.84% of the matmul term for an 8B model, and the measured `SOFT_MAX` share
in an upstream llama.cpp profile of that configuration is 0.84%.

**Throughput on the runner is unpublished, and the band is 5× wide.** Nobody has published a
`llama-bench` prompt-processing figure at 4 threads on x86, let alone on a GitHub runner. Deriving an
effective FLOP/s from two upstream measurements whose hardware is stated:

| measured | derived |
| --- | --- |
| Llama-3.1-8B Q4_K_S, Ryzen 7950X, 16 threads, `pp512` 108.4 t/s | ~1,745 GFLOP/s over 8 cores = **218 GFLOP/s/core** |
| Qwen3-32B Q6_K, 2× Xeon 6238R, 56 threads, `pp512` 20.99 t/s | ~1,343 GFLOP/s over 28 cores = **48 GFLOP/s/core** |

A 4-vCPU runner is ~2 physical cores with SMT, at a lower clock than a desktop Zen 4 part, so the
plausible band is **100–500 GFLOP/s**, central estimate ~250. Two further measured facts make long
prompts worse than a `pp512` headline: on the same 7950X box `pp512` 108 t/s falls to `pp2048`
93 t/s, and at 32k tokens `MUL_MAT` drops from 93.3% to 80.2% of time while `SOFT_MAX` rises to
17.8%.

**Conventional models: RAM kills it before throughput does.** KV cache per token, from each model's
own `config.json`:

| model | KV KiB/tok | f16 @128k | q8 @128k | q4 @450k | native window |
| --- | --- | --- | --- | --- | --- |
| Qwen3-1.7B | 112 | 14.7 GB | 7.3 GB | 12.9 GB | 40,960 |
| Qwen3-4B-Instruct-2507 | 144 | 18.9 GB | 9.4 GB | 16.6 GB | 262,144 |
| Qwen3.5-4B | 128 | 16.8 GB | 8.4 GB | 14.7 GB | 262,144 |
| Qwen3.5-9B | 128 | 16.8 GB | 8.4 GB | 14.7 GB | 262,144 |
| EuroLLM-22B-Instruct-2512 | 216 | 28.3 GB | 14.2 GB | 24.9 GB | **32,768** |

Weights at Q4 cost about 0.4 GB per billion parameters, so the KV budget is ~16 GB minus that minus
~1 GB of runtime. Solving jointly for the 6-hour job at 250 GFLOP/s **and** 12 GB of q8 cache:

| model | largest input that fits | = chars per source, largest story | share of a median body |
| --- | --- | --- | --- |
| Qwen3-0.6B / 1.7B | 40,960 (its native window) | 183 | 8% |
| Qwen3-4B-Instruct-2507 | 122,431 | **548** | 24% |
| Qwen3.5-4B | 129,074 | 578 | 25% |
| Qwen3.5-9B | 113,241 | 507 | 22% |
| EuroLLM-22B-2512 | 32,768 (its native window) | 147 | 6% |

At the **pessimistic** end of the throughput band those numbers fall to ~40,000 tokens — 183
characters a source, barely more than a headline. At the optimistic end they roughly double.

**The low-bit 27B build changes the shape of this route.** `prism-ml/Ternary-Bonsai-27B-gguf`
reports, on its model card and therefore as a **vendor claim**: 7.15 GB of weights at 1.71 bits per
weight; *"the 100K peak drops to ~10.1 GB, and the full 262K window fits in ~12.8 GB peak"* with a
4-bit KV cache; and a backbone that is *"~75% linear attention"*, which removes most of the
quadratic term. Those three together put a 27B-class model inside a 16 GB runner at 262k context —
something no conventional build comes close to. Its published `llama-bench` table has Metal and CUDA
rows only (M4 Pro `pp512` 125 t/s, M5 Max 830, H100 2596) and **no x86 CPU row**. Extrapolating on
`2·N·T` alone across the throughput band:

| tokens | 100 GFLOP/s | 250 GFLOP/s | 500 GFLOP/s |
| --- | --- | --- | --- |
| 17,000 (headlines) | 2.6 h | 1.0 h | 0.5 h |
| 40,000 | 6.1 h ✗ | 2.4 h | 1.2 h |
| 100,000 | 15.2 h ✗ | 6.1 h ✗ | 3.0 h |
| 262,144 | 39.8 h ✗ | 15.9 h ✗ | 8.0 h ✗ |

✗ exceeds the 6-hour job limit. So Route 3 with this build reads somewhere between 40,000 and
100,000 tokens per essay depending on a number nobody has measured — which is 180 to 450 characters
per source. **It is worse than Route 1 at every point in the band, and Route 1 is free too.**

**Route 3 fits every documented quota and fails the terms.** This is the finding that decides it
independently of any throughput number, so it is worth setting out in full. Five parallel jobs is
inside the 20-concurrent limit on the Free plan, minutes are *"free and unlimited on public
repositories"*, and there is no documented monthly cap for public repositories at all. But the
billing docs themselves route the permission question elsewhere — *"In addition to the usage limits,
you must ensure that you use GitHub Actions within the GitHub Terms of Service"* — and the
[Terms for Additional Products and Features](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)
say Actions **should not be used for**, among five disjunctive items:

> Any activity that places a burden on our servers, where that burden is disproportionate to the
> benefits provided to users (for example, don't use Actions as a content delivery network **or as
> part of a serverless application**, but a low benefit Action could be ok if it's also low burden)

and, separately and without any public-repository qualification:

> *Use for Development and Testing* — You may only access and use GitHub Actions to develop and test
> your application(s).

The clause's own test is a **ratio**, and 100+ CPU-hours a day of neural inference for a handful of
300-word essays is about the worst ratio this workload could present; the escape hatch it offers —
*"a low benefit Action could be ok if it's also low burden"* — is forfeited by the premise. The
fifth item, *"any other activity unrelated to the production, testing, deployment, or publication of
the software project associated with the repository"*, is genuinely arguable when the repository *is*
the site, but the burden clause does not need it. **This is a reading, not a settled answer** — GitHub
has published nothing on model inference on runners specifically, and its documented enforcement
writing is about cryptomining. §9.4 says how to settle it.

**The failure modes are not symmetric, and this is the strongest reason to prefer Route 1.** Route 1's
worst case is a 402 and no essay that month. Route 3's stated remedies are *"termination of jobs,
restrictions in your ability to use GitHub Actions, disabling of repositories created to run Actions
in a way that violates these Terms, or in some cases, suspension or termination of your GitHub
account."* The same account publishes the site through Pages. **Route 1 risks the essays; Route 3
risks the website.**

**One more operational fact.** Gated repositories need a token from an account that has individually
accepted each model's terms — `meta-llama/*` and `google/gemma-3-*` are `gated=manual`, meaning a
human reviews the request, which can block a pipeline for days.

---

## 5. What can actually be established about multilingual reading

This is where the evidence is thinnest, and the thinness is the finding.

### 5.1 What the benchmarks cover

| benchmark | el | ar | tr | uk | ru | task | authored how |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Belebele](https://arxiv.org/abs/2308.16884) (122 variants) | ✅ | ✅ | ✅ | ✅ | ✅ | machine reading comprehension, 4-option | questions human-written on FLORES-200 *translated* passages |
| [Global-MMLU](https://arxiv.org/abs/2412.03304) (42) | ✅ | ✅ | ✅ | ✅ | ✅ | knowledge MCQ | translated; **Greek is fully machine-translated** |
| Global-MMLU-**Lite** (23) | ❌ | ✅ | ❌ | ❌ | ❌ | knowledge MCQ | — |
| [INCLUDE-44](https://arxiv.org/html/2411.19799v1) | ✅ | ✅ | ✅ | ✅ | ✅ | knowledge MCQ from real local exams | **natively authored** |
| [MMLU-ProX](https://arxiv.org/abs/2503.10497) (29) | ❌ | ✅ | ❌ | ✅ | ✅ | knowledge MCQ, 5-shot CoT | LLM-translated, expert-reviewed |
| MMMLU (OpenAI, 14) | ❌ | ✅ | ❌ | ❌ | ❌ | knowledge MCQ | professional human translation |
| [GreekMMLU](https://arxiv.org/abs/2602.05150) | ✅ | — | — | — | — | knowledge MCQ, 45 subjects | **natively authored**, 21,805 questions |
| [TurkishMMLU](https://arxiv.org/abs/2407.12402) | — | — | ✅ | — | — | knowledge MCQ | **natively authored** |
| [Marco-Bench-MIF](https://arxiv.org/html/2507.11882v1) (30) | ✅ | ✅ | ✅ | ✅ | ✅ | **instruction following**, IFEval-style | **localised**, not merely translated |
| [ONERULER](https://arxiv.org/abs/2503.01996) (26) | ❌ | ❌ | ❌ | ✅ | ✅ | **long context**, retrieval + aggregation | instructions translated into 25 languages |
| [NoLiMa](https://arxiv.org/html/2502.05167v3) | ❌ | ❌ | ❌ | ❌ | ❌ | long context, low lexical overlap | English only |

Three structural facts follow.

**Global-MMLU-Lite covers none of Greek, Turkish, Ukrainian or Russian.** Any model whose headline
multilingual number is a Global-MMLU-*Lite* score has no evidence for four of the five languages that
matter here. This is worth flagging because it is the number several vendors report.

**Greek's only high-quality evaluation is GreekMMLU and Belebele.** It is excluded from MMLU-ProX,
MMMLU, Okapi and Global-MMLU-Lite, and machine-translated in Global-MMLU.

**Turkish is the worst-covered.** Excluded from MMLU-ProX, MMMLU and Global-MMLU-Lite; INCLUDE's
Turkish subset is 2,710 items, and Ukrainian's is 1,482.

### 5.2 GreekMMLU: the size-versus-quality curve, on native text, independent of every vendor

The single most useful table in this document, because it measures the size class the free budget
affords, in the project's third language, on questions written in Greek rather than translated into
it. *GreekMMLU: A Native-Sourced Multitask Benchmark for Evaluating Language Models in Greek*, Zhang
et al., [arXiv:2602.05150](https://arxiv.org/abs/2602.05150), submitted 2026-02-05. Zero-shot
accuracy, Table 3, extracted from the PDF locally:

| model | Average | Greek-specific |
| --- | --- | --- |
| Gemini 3 Flash *(closed)* | 93.16 | 95.44 |
| GPT-5.2 *(closed)* | 87.75 | 92.92 |
| Qwen2.5-72B-Instruct | 79.70 | 84.67 |
| Llama-3.3-70B-Instruct | 79.65 | 86.94 |
| **Gemma-3-27B-it** | **79.41** | 85.33 |
| Qwen3-30B-Instruct | 78.39 | 81.80 |
| Gemma-3-12B-it | 75.31 | 82.21 |
| EuroLLM-22B-Instruct-2512 | 72.18 | 78.99 |
| EuroLLM-9B-Instruct | 68.48 | 76.86 |
| Qwen2.5-14B-Instruct | 66.61 | 73.06 |
| Llama-Krikri-8B-Instruct *(Greek-adapted)* | 66.47 | 74.73 |
| GLM-4-9b-chat | 64.68 | 69.29 |
| **Gemma-3-4B-it** | **62.24** | 68.58 |
| Meltemi-7B-Instruct-v1.5 *(Greek-adapted)* | 60.93 | 66.42 |
| Qwen2.5-7B-Instruct | 60.25 | 64.02 |
| Llama-3.1-8B-Instruct | 59.56 | 64.75 |
| Aya-101 | 56.73 | 59.86 |
| Llama-3.2-3B-Instruct | 44.52 | 46.15 |
| Llama-3.2-1B-Instruct | 37.29 | 35.46 |
| **EuroLLM-1.7B-Instruct** | **29.68** | 30.16 |
| **Random baseline** | **30.42** | 31.59 |

The paper's own reading: *"substantial performance gaps between frontier and open-weight models, as
well as between Greek-adapted models and general multilingual ones."*

**Read against §4.3, this is the most decision-relevant number in the document.** The pessimistic end
of Route 3's throughput band forces a model of about 1.7B. **A 1.7B model is at chance in Greek** —
EuroLLM-1.7B-Instruct scores 29.68 against a 30.42 random baseline. A 4B model scores 62.24, which is
real but is 17 points below a 27B and 31 below a frontier model. There is no size at which this curve
is flat, and the free budget sits on its steep part.

Two caveats. GreekMMLU is knowledge MCQ, not reading comprehension of supplied text, so it does not
directly measure the essay's task — Belebele would, and nobody has published current-model Belebele
numbers (§5.5). And `Qwen3-4B-Instruct-2507`, the model the arithmetic points at, **is not in this
table**; the nearest 4B row is Gemma-3-4B-it.

### 5.3 INCLUDE-44: the only per-language table covering all five

From Cohere's *Command A* report, [arXiv:2504.00698](https://arxiv.org/abs/2504.00698), Table 25.
Vendor-run — Cohere evaluating competitors — but on an independent, natively authored benchmark, and
it is the only source found with el+ar+tr+uk+ru side by side:

| model | avg | ar | **el** | **tr** | **uk** | ru |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V3 | 76.9 | 73.9 | 66.5 | 66.8 | 77.8 | 72.8 |
| Llama 3.1 405B Instruct | 75.3 | 70.7 | 62.2 | 71.9 | 76.5 | 72.0 |
| Llama 3.3 70B Instruct | 75.0 | 71.7 | 64.7 | 73.0 | 74.5 | 69.6 |
| Command A | 74.3 | 73.2 | 68.0 | 67.7 | 76.5 | 69.2 |
| Qwen 2.5 72B Instruct | 72.6 | 70.5 | 57.1 | 64.8 | 71.3 | 69.4 |
| Gemma 2 9B Instruct | 61.7 | 57.1 | 55.3 | 59.3 | 66.0 | 57.8 |
| Qwen 2.5 7B Instruct | 59.9 | 57.1 | 49.3 | 52.6 | 57.1 | 52.5 |
| Llama 3.1 8B Instruct | 54.9 | 55.1 | **33.5** | 56.0 | 54.7 | 49.1 |
| Ministral 8B | 50.2 | 43.8 | 41.6 | 46.7 | 54.0 | 51.1 |

Greek is the column that separates the classes: 33.5 for Llama-3.1-8B against 66.5 for DeepSeek V3.
The same pattern as §5.2, on a different benchmark, from a different author.

### 5.4 Steerability: Marco-Bench-MIF is the only benchmark that covers Greek, Turkish and Ukrainian

This is the requirement #60 imposes, and it is the one where a benchmark exists.
*Marco-Bench-MIF: On Multilingual Instruction-Following Capability of Large Language Models*, Zeng et
al., [arXiv:2507.11882](https://arxiv.org/html/2507.11882v1) — **30 languages including el, tr, uk,
ar, ru**, IFEval-style verifiable output constraints, **localised rather than machine-translated**.
Verified directly: the language list and both quotations below are in the fetched paper.

Instruction-level accuracy, strict:

| model | ar | **el** | en | ru | **tr** | **uk** |
| --- | --- | --- | --- | --- | --- | --- |
| Claude 3.5 Sonnet | 82.4 | 79.3 | **90.3** | 80.9 | 83.3 | 78.0 |
| GPT-4o | 81.2 | 79.0 | 87.8 | 78.6 | 79.2 | 78.1 |
| Gemini 1.5 Flash | 84.9 | 77.8 | 89.5 | 80.4 | 78.8 | 78.8 |
| Qwen2.5-7B | 55.4 | **49.4** | 73.7 | 60.6 | 50.9 | 56.2 |
| Ministral-8B | 21.8 | 32.4 | 53.0 | 49.0 | 32.0 | 33.5 |

The paper: *"High-resource European (de, fr) and East Asian languages (zh, ja) achieve 75-85%
accuracy across top models, while low-resource languages (yo, ne, kk) performance is at 50-60% even
for Claude3.5-sonnet. This 25-35 point gap persists across difference LLM scales"* [sic].

**Read against #60, this is the number to design the gate around.** A frontier model loses 8–12
points of instruction-level accuracy going from English to Greek, Turkish or Ukrainian. A 7B model
loses **24 points in Greek** — 73.7 → 49.4. #29 d5 makes the output mechanically gated, so a
sentence that fails attribution is discarded; a model at 49% instruction-level accuracy in Greek is
not merely worse, it produces an essay that is gutted in exactly the languages the product exists to
compare.

A methodological warning from the same paper that applies to any evaluation this project builds:
*"machine-translated data underestimates accuracy by 7-22% versus localized data."* Machine-
translating English prompts into 36 languages to build a gate-calibration set would produce numbers
that are pessimistic by up to 22 points and mis-ranked.

One further finding worth carrying into #64: [IFBench](https://arxiv.org/abs/2507.02833) (AI2) finds
*"most models strongly overfit on a small set of verifiable constraints from the benchmarks that test
these abilities … and are not able to generalize well to unseen output constraints."* #60's rule —
attribute the relation to a named source and anchor it in that source's text — is precisely an unseen
out-of-domain constraint, so the Marco-Bench numbers are an upper bound on what the gate will see.

### 5.5 Long context in the languages that matter: almost nothing measures it

**ONERULER** — *One ruler to measure them all: Benchmarking multilingual long-context language
models*, Kim, Russell, Karpinska, Iyyer, [arXiv:2503.01996](https://arxiv.org/abs/2503.01996) —
covers 26 languages, and its abstract states: *"Experiments with both open-weight and closed LLMs
reveal a widening performance gap between low- and high-resource languages as context length
increases from 8K to 128K tokens."* Its 26 languages **include Ukrainian and Russian and exclude
Greek, Arabic and Turkish**. The paper reports the gap between the top five and bottom five languages
by resource growing *"from 11% with a context length of 8K to 34% with context length of 128K"*, and
the counter-intuitive result that English ranks 6th of 26.

**NoLiMa** ([arXiv:2502.05167](https://arxiv.org/html/2502.05167v3)) is the most relevant negative
result and it is English-only: needle-in-haystack with *minimal lexical overlap* between question and
answer, where *"At 32K, for instance, 11 models drop below 50% of their strong short-length
baselines."* Attributing a causal claim to a named source across hundreds of thousands of tokens of
news in 37 languages is a low-lexical-overlap association task, not a string match. It collapses at
32K in English.

**The intersection nobody measures.** This system needs long-context comprehension *and* instruction
following *and* 37 languages, simultaneously. No benchmark measures long context and instruction
following together in any language. **No long-context benchmark covers Greek, Arabic or Turkish at
all.** And nothing measures multilingual comprehension beyond 128K, which is a quarter of what §2.4
says one essay needs.

### 5.6 The current generation has no per-language evaluation, and that includes the recommendation

Searching arXiv systematically for per-language multilingual results on the models the router
actually serves today produced nothing for `Qwen3.5`/`Qwen3.6`, `gemma-4`, `GLM-5.x`,
`DeepSeek-V4`, `Kimi-K3`, `MiniMax-M3`, `Nemotron-3`, `Inkling`, `MiMo-V2.5`, `Hy3`, `Step-3.7` or
`Ling-2.6` in any of the five languages. Every relevant leaderboard is stale or unreadable: the Open
Multilingual LLM Evaluation Leaderboard returns a runtime error; the European LLM Leaderboard Space
was last modified 2025-04-28; MMLU-ProX's leaderboard has eight rows and says "coming soon".

**This applies to my own recommendation.** `Qwen/Qwen3-4B-Instruct-2507` has no independent
per-language evaluation in Greek, Arabic, Turkish, Ukrainian or Russian that I could find or open.
Neither does `prism-ml/Ternary-Bonsai-27B-gguf`, whose card reports 15 benchmarks — MMLU-Redux, MuSR,
HumanEval+, MBPP+, LiveCodeBench, IFEval, IFBench, AIME26 among them — **all English or code**, and
does not state which languages it supports. The recommendation in §8 rests on architecture, price,
window and a size-versus-quality curve measured on *neighbouring* models, not on a measurement of the
model itself. §10 is how to fix that.

---

## 6. Licences

Read on the actual licence text, not on the `license:` tag. Gating status and licence ids were
confirmed live via `https://huggingface.co/api/models/<repo>` on 2026-08-04.

### 6.1 Permits, unconditionally, no gate

| model | licence | notes |
| --- | --- | --- |
| `Qwen/Qwen3-4B-Instruct-2507` | **Apache-2.0** | I fetched the LICENSE (201 lines, HTTP 200): stock Apache, zero occurrences of "non-commercial". Same for Qwen3.5-*, Qwen3.6-*, Qwen3-Next |
| `google/gemma-4-*` | **Apache-2.0** | Gemma 4 left the Gemma Terms of Use; the Terms page itself says *"For Gemma 4 terms, see the Gemma 4 license"*, which resolves to plain Apache-2.0. `gated=False` |
| `deepseek-ai/DeepSeek-V4-*` | **MIT** | plain MIT, no use restriction, no output clause |
| `zai-org/GLM-5.x`, `GLM-4.7` | **MIT** | weights MIT; note the GitHub *code* repo is Apache-2.0 — don't cite one for the other |
| `openai/gpt-oss-120b` / `-20b` | **Apache-2.0** | no usage policy referenced anywhere in the licence or the card |
| `nvidia/NVIDIA-Nemotron-3-Ultra-*` | **OpenMDW-1.1** | the only licence that expressly disclaims output duties: *"This agreement does not impose any restrictions or obligations with respect to any use, modification, or sharing of any outputs generated by using the Model Materials."* |
| `prism-ml/Ternary-Bonsai-27B-gguf` | **Apache-2.0** | a derivative of Qwen3.6-27B, which is itself Apache-2.0, so the chain is clean |
| `tencent/Hy3`, `XiaomiMiMo/MiMo-V2.5`, `stepfun-ai/Step-3.7-Flash`, `inclusionAI/Ling-2.6-1T` | Apache-2.0 / MIT | no MAU clause, no output clause |

### 6.2 Permits with a cheap condition

- **Llama 3.3** — commercial use permitted outright; the 700M-MAU clause is irrelevant at this scale.
  The condition is §1.b.i: *"prominently display "Built with Llama" on a related website, user
  interface, blogpost, about page, or product documentation."* Whether a static site "contains" the
  Llama Materials is an unlitigated reading; displaying the notice costs nothing and ends the
  question. `gated=manual`.
- **Kimi K2.x / K3** — a modified MIT with a display duty that triggers only above 100M MAU or $20M
  monthly revenue. Nothing triggers.
- **MiniMax-M3** — a community licence granting rights *"for non-commercial purposes"*, with
  Commercial Use defined by intent (*"primarily intended for commercial advantage or monetary
  compensation"*). A free ad-free site falls outside it; §2.1 imposes a *"Built with MiniMax M3"*
  notice the moment it does not.
- **`thinkingmachines/Inkling`** — Apache-2.0, but the card links a self-executing Model AUP that
  imposes an affirmative duty on the published page: to disclose *"that they are interacting with an
  AI system wherever required by law or where that fact would be material to their understanding of
  the interaction."* It is the only licence-adjacent document that obliges something of the site.

### 6.3 Does not permit

- **Mistral Research Licence** (Mistral Large, Ministral 8B) — §3.2: *"You shall only use the Mistral
  Models, Derivatives … **and Outputs** for Research Purposes"*, where Research Purposes expressly
  excludes *"any Distribution by a commercial entity of the Mistral Model, Derivative or Output
  whether in return for payment or **free of charge**"*. The "free of charge" wording forecloses the
  zero-revenue argument. Note `Mistral-Small-3.2-24B-Instruct-2506` is Apache-2.0 and unaffected —
  but no `mistral*` model appears on the router at all.
- **Mistral Non-Production Licence** (Codestral) — non-production environments only; a live public
  site is production.
- **`Qwen/Qwen2.5-3B-Instruct`** — the Qwen *Research* Licence, where *"'Non-Commercial' shall mean
  for research or evaluation purposes only."* Purpose-based, not revenue-based, so a free site does
  not rescue it. A trap worth naming, because sibling Qwen2.5 sizes are Apache-2.0.
- **Llama 4, for an EU-domiciled operator** — the AUP withholds the §1(a) grant for the multimodal
  models from *"an individual domiciled in, or a company with a principal place of business in, the
  European Union"*, exempting only *"end users of a product or service that incorporates any such
  multimodal models"*. Scout and Maverick are natively multimodal. Downloading the weights is
  therefore unlicensed for an EU operator; whether calling a third-party API makes one an "end user"
  is unlitigated. The cost of avoiding Llama 4 is near zero, so avoid it.

### 6.4 Cannot determine: Cohere's CC-BY-NC

Command A, Command R+, Aya Expanse: `cc-by-nc-4.0` plus Cohere's Acceptable Use Policy. Two
questions, two different answers.

**Does NonCommercial permit a free public site? Almost certainly yes.** CC BY-NC 4.0 §1(i): *"not
primarily intended for or directed towards commercial advantage or monetary compensation."* CC's own
FAQ: *"Whether a use is commercial will depend on the specifics of the situation and the intentions
of the user"*, and its interpretation guide: *"it is only the primary purpose of the reuse that needs
to be considered."* A no-ads, no-subscription, no-revenue site is not primarily commercial.

**Does publishing model output count as sharing Adapted Material? Cannot be determined from the
text.** CC BY-NC 4.0 is a content licence with no clause about models, weights, inference or output.
An essay is not plausibly material *"in which the Licensed Material is translated, altered, arranged,
transformed, or otherwise modified"* — the weights are not in the essay. On that reading output is
outside the licence's subject matter, so the NC limit never reaches it and neither does the
attribution duty. But that also means the licence grants no positive permission for it, and Cohere's
AUP does treat outputs as within its reach (it separately restricts *"generating synthetic data
outputs for commercial purposes"*), which cuts against the reading. Unlitigated worldwide.

**Verdict: avoid.** Not because it fails, but because a dozen Apache/MIT alternatives of equal or
better capability make this an unnecessary use of the project's risk budget.

### 6.5 Does a hosted API move the obligation off us?

No licence read says the obligation binds only whoever runs the weights. Where they address it they
reach the caller.

- **Gemma** binds the API caller explicitly, in its preamble: *"By using … any portion or element of
  Gemma, Model Derivatives **including via any Hosted Service** … you agree to be bound by this
  Agreement"*, with Distribution defined to include *"providing or making Gemma or its functionality
  available as a hosted service via API."*
- **Llama** contemplates it and exempts exactly one clause: §1.b.ii disapplies **only** the 700M-MAU
  section for someone receiving the materials as part of an integrated end-user product. By
  implication the rest still reaches you.
- **Mistral MRL** §1.1: *"This Agreement applies to any use, modification, or Distribution of any
  Mistral Model by You, **regardless of the source** You obtained a copy of such Mistral Model."*
- **Apache-2.0, MIT, OpenMDW-1.1** have no use restriction to bind. **CC BY-NC 4.0 is genuinely
  silent** on models and APIs.
- **Hugging Face is silent.** The Inference Providers docs contain zero occurrences of "licen"; the
  ToS says only *"Nothing in these Terms limit your rights under, or grants you rights that supersede,
  the terms and conditions of any applicable Open Source license."*

### 6.6 One duty applies whatever is chosen

Llama, Gemma, Cohere and Thinking Machines each independently forbid presenting model output as
human-written — Llama's AUP: *"Representing that the use of Llama 3.3 or outputs are
human-generated"*; Gemma's Prohibited Use Policy §3(a): *"Misrepresentation of the provenance of
generated content by claiming content was created by a human."* **Label the essays as machine-written
on the page.** It is the cheapest possible compliance step, it is required by four of the candidate
families, and it is consistent with what this product already does everywhere else — say what was
computed and how.

No licence or acceptable-use policy read here restricts news, journalism or political subject matter
as such. Five restrict *intentional* disinformation, which a good-faith attributed measurement is
not.

---

## 7. The candidates, against the three requirements

Requirements as #74 states them, with the context figure corrected per §2.4. "Free" means: runs
inside the $0.10/month credit at 150 essays a month, or costs nothing at all.

| candidate | route | reads 37 languages? | context | steerable? | free? | licence |
| --- | --- | --- | --- | --- | --- | --- |
| **`Qwen/Qwen3-4B-Instruct-2507`** | nscale, $0.01/M | **no direct evidence.** Neighbouring 4B (Gemma-3-4B-it) scores 62.24 on native GreekMMLU vs 79.41 at 27B | **262,144** — 1,174 chars/source, or 500 with room to spare | no direct evidence; the 7B class scores 49.4 instruction-level in Greek (§5.4) | **yes — 145 essays/mo at 500 chars/source** | Apache-2.0, ungated |
| **`google/gemma-4-26B-A4B-it`** | deepinfra, $0.07/M | no direct evidence; Gemma-3-27B-it scores **79.41** on GreekMMLU, the best open-weight row | **262,144** | no direct evidence; a 27B is 17 pts above a 4B in Greek | **25 essays/mo** — a fifth of the requirement | Apache-2.0, ungated |
| **`prism-ml/Ternary-Bonsai-27B-gguf`** | together, **$0/M**; also runnable in the runner | **none at all** — 15 benchmarks, all English/code; card does not state its languages. 1.71-bit quantisation of Qwen3.6-27B | **262,144**, and 12.8 GB peak locally | no multilingual evidence; provider advertises **no** structured output | **yes, apparently free** — but `is_free: false` contradicts the $0 price | Apache-2.0, ungated |
| `Qwen/Qwen3-235B-A22B-Instruct-2507` | deepinfra, $0.09/M | Qwen3-30B-Instruct 78.39 GreekMMLU; **Qwen3's tokenizer is the worst for Greek at 3.78× English** | 262,144 | INCLUDE-44 aggregate 73.46 (vendor) | 16 essays/mo | Apache-2.0 |
| `deepseek-ai/DeepSeek-V4-Flash` | deepinfra, $0.09/M | DeepSeek V3 leads INCLUDE-44 on 4 of our 5 languages (§5.3); V4 unmeasured | **1,048,576** — the only route that fits a full-body call | no per-language evidence for V4 | 18 essays/mo | MIT |
| `meta-llama/Llama-4-Scout` | nscale, $0.09/M | Llama-3.3-70B: GreekMMLU 79.65, INCLUDE-44 el 64.7 | 890,000 | Multi-IF covers ru but not el/tr/uk | 20 essays/mo | **Llama 4: grant withheld from EU-domiciled operators for local use** |
| `utter-project/EuroLLM-22B-Instruct-2512` | publicai, $0.10/M | **the only model purpose-built for this language set.** GreekMMLU 72.18 | **32,768 — disqualifying.** 147 chars/source | no Turkish evaluation exists in its own report | ~13 essays/mo | Apache-2.0 |
| `CohereLabs/aya-expanse-32b` | cohere, price unpublished | Aya covers el/tr/uk/ar/ru by design; Aya-101 GreekMMLU 56.73 | unpublished | Marco-Bench 62.96 avg (Aya-expanse-32B) | unknown — Cohere publishes no price | **CC-BY-NC: cannot determine whether it reaches output** |
| Qwen3-1.7B / 0.6B in the runner | Route 3 | **at chance in Greek** — EuroLLM-1.7B-Instruct 29.68 vs a 30.42 baseline | 40,960 native → 183 chars/source | worse than any measured row | free | Apache-2.0 |

---

## 8. My recommendation

The choice is the owner's; this is what I would choose and why.

**`Qwen/Qwen3-4B-Instruct-2507`, pinned to nscale, reading the first ~500 characters of each source's
reconstructed body, one call per essay, generated once per story.**

The reasoning, in the order it decided me:

1. **It is the only candidate that meets the volume requirement inside the free credit.** 145 essays
   a month against a pessimistic requirement of 150, at 262,144 tokens of window — 12× the margin the
   next-cheapest wide route has. Every other route on the table delivers between 4 and 25 essays a
   month and then stops.
2. **Its window is the second-widest thing available at any price under $0.09**, and at 500
   characters a source it has room to grow: the largest featured story costs 111,667 of its 262,144
   tokens, so the window absorbs a doubling of the corpus or of `WINDOW_SLOTS` without a redesign.
   Given that §2.1 shows this requirement moved 2× in one day for an unrelated reason, headroom is
   worth more here than it usually is.
3. **The provider advertises structured output and 582 ms to first token.** The output is mechanically
   gated (#29 d5), so constrained decoding matters; and sub-second latency means the essay job is a
   few seconds, not the hours Route 3 needs.
4. **Apache-2.0, ungated, no output obligation, no attribution duty.** Nothing to negotiate and
   nothing to display beyond the machine-written label that §6.6 recommends regardless.
5. **Route 3 is dominated on every axis, including the one that is not about capability.** The same 4B
   class, run locally, reads *fewer* characters per source (548 at the central throughput estimate,
   183 at the pessimistic one), takes hours instead of seconds, and is free in exactly the same sense
   Route 1 is. And it fits every documented GitHub quota while failing the Actions terms on a reading
   I would not want to test (§4.3) — where the stated remedies reach the account that also publishes
   the site. **Route 1 risks the essays; Route 3 risks the website.** There is no axis on which it
   wins.

**What I am recommending against, and it should be said plainly.** This is a 4B model doing a job
that the evidence says a 27B model does 17 points better in Greek, and a frontier model 31 points
better. #63's own recommendation was *"the most capable model available for multilingual reading
rather than the cheapest that seems to cope, because the failure mode is a confidently wrong essay in
a language nobody on the project reads"*. **The free constraint forces exactly the choice #63 argued
against.** If the owner will spend $9 a month on PRO, the $2.00 credit buys 2,898 essays a month at
the 4B model or **504 at `gemma-4-26B-A4B-it`** — comfortably above the requirement at the size class
GreekMMLU says scores 79 rather than 62. That is the honest form of "what the cheapest achievable
option costs": **$9/month buys the 27B class; free buys the 4B class; nothing buys the frontier
class.**

**Two things I would do before writing the first essay, both cheap.**

- **Settle the Ternary Bonsai question first** (§9.1). If the $0 price is real, it is a 27B-class
  model at 262k context for nothing, and it dominates my recommendation outright — subject to it
  having any multilingual ability at all, which nobody has measured. One authenticated call and a
  look at the billing page answers the price question; the evaluation in §10 answers the other.
- **Run the evaluation in §10 on this corpus before choosing.** #63 said the choice should be made
  against real output rather than a benchmark on someone else's data, and I have not been able to do
  that — every number in §5 is somebody else's data. The evaluation costs about **$0.01** and
  produces the only evidence that would actually settle this.

---

## 9. What could not be determined

**9.1 Whether `prism-ml/Ternary-Bonsai-27B-gguf` is free *through the Hugging Face router*.** Together
says it is free on Together — three times, on its own model page, with a 99.9% SLA — and HF charges
*"the same rates as the provider, with no additional fees"*, so pass-through of $0.00 should be $0.00.
Against that: HF's router record says `is_free: false` beside the zero price, and if the router gates
on that flag rather than on computed cost, calls could be refused once the $0.10 is spent elsewhere.
This is the most consequential open question in the document — it is the difference between 145
essays a month and an unbounded number, at 27B rather than 4B. *Settled by:* one authenticated call,
then `https://huggingface.co/settings/billing` before and after to see whether the balance moves; then
deliberately exhausting the $0.10 on a priced model and calling again. **That last step is the actual
answer.** Cost if it is not free: at 262,144 tokens and the most expensive plausible rate on the board
($0.09/M), one call is $0.024.

**9.2 Prefill throughput on a GitHub runner.** No `llama-bench` prompt-processing figure exists at 4
threads on x86, and none on an Actions runner. My 100–500 GFLOP/s band is an extrapolation from
16-thread and 56-thread runs, and it is 5× wide — wide enough to change Route 3's answer from "183
characters a source" to "548". *Settled by:* one `workflow_dispatch` job running
`llama-bench -t 4 -p 512,2048 -d 100000` on `ubuntu-latest`. Free.

**9.3 Whether the Hub's published rate limits govern the router at all.** `https://huggingface.co/docs/hub/rate-limits`
defines exactly three buckets — Hub APIs, Resolvers, Pages — and never mentions
`router.huggingface.co`. For a job making five calls a day the credit balance is almost certainly the
binding limit, not a request rate, but this is an assumption. *Settled by:* one authenticated router
call, inspecting the response for `RateLimit` and `RateLimit-Policy` headers.

**9.4 Whether GitHub would actually enforce its Actions terms against model inference.** The clause is
established and quoted in §4.3, and on my reading Route 3 fails it — but that is inference from the
text. GitHub has published nothing addressing LLM inference on runners; its documented enforcement
writing concerns cryptomining, where it says it has *"spent thousands of hours combating abuse"* and
that *"GitHub may monitor your use of GitHub Actions"*. *Settled by:* a GitHub Support ticket
describing the workload, which the terms themselves invite — *"If you have questions about whether
your use or intended use falls into these categories, please contact us through the GitHub Support
portal"*. Cheap and definitive, and it bears only on Route 3, which I recommend against anyway.

**9.5 How many essays a month are actually needed.** #63 generates once per story and keeps it, so
the requirement is the *turnover* of the featured five, not five a day. The `data` ref is a single
force-pushed commit and the per-run records on `history` carry no per-story source counts, so
turnover is not measurable from what is published. Everything in §4.1 uses 150/month, the pessimistic
bound. *Settled by:* adding the featured story ids to the per-run record on `history` and waiting a
week — which is work #62 will do anyway when it gives the essay a home.

**9.6 Whether the maximum request body size on the router accepts a 262,144-token prompt.** The
chat-completion reference documents every payload field and states no body-size cap, no per-request
token cap and no timeout. A 262k-token prompt is roughly 1–1.5 MB of JSON. *Settled by:* one call at
full size.

**9.7 The multilingual ability of the two models I am recommending between.** Neither
`Qwen3-4B-Instruct-2507` nor `Ternary-Bonsai-27B` has any published per-language evaluation in Greek,
Arabic, Turkish, Ukrainian or Russian. Nor does any other model the router serves today (§5.6). The
size-versus-quality curve in §5.2 is measured on *neighbouring* models of the same scale, which is
inference, not measurement. *Settled by:* §10.

**9.8 Three leads I could not open.** The GreekMMLU leaderboard Space, the Open Arabic LLM
Leaderboard Space and the MERA Russian leaderboard are all JavaScript-rendered and returned no data.
They are the three places where 2026-generation per-language numbers are most likely to exist.
*Settled by:* a browser that executes JavaScript.

**9.9 Cohere's prices and context windows.** Cohere publishes neither `context_length` nor `pricing`
for any of its 12 router models, and featherless-ai publishes neither for any of its 67. So the Aya
and Command rows in §7 cannot be costed at all.

---

## 10. The evaluation that would settle it, on this corpus

#63 said the choice should be made against real output on this corpus rather than a benchmark on
someone else's data, and that is what §5 could not supply. The evaluation is cheap and it is worth
running before the choice is made.

**Material.** The banded stories on the `data` ref already carry per-source headlines, languages,
domains and URLs. The bodies do not exist yet — #62 builds the reconstruction — so until it does the
evaluation runs on headlines, which is a weaker test but a real one: 3,073 headlines in 41 languages,
of which 125 Greek, 124 Russian, 106 Arabic, 62 Turkish, 61 Ukrainian.

**The test that matters is not fluency, it is whether #60's gate passes.** For each candidate, on the
five featured stories:

1. prompt for one essay under #60's rule — every causal or evaluative sentence must name a source of
   that story and the relation must be findable in that source's text;
2. run the gate: does the named source belong to the story, and does the asserted relation appear in
   that source's own text?
3. report **the share of generated sentences the gate keeps, broken down by the language of the
   source attributed to.**

That last breakdown is the number nobody's benchmark gives and this corpus can. #29 d5 makes a
sentence that fails the gate a sentence that is discarded, so a model that attributes reliably in
English and unreliably in Greek does not produce a worse essay — it produces an essay with Greece
missing, on a product whose subject is exactly that comparison.

**Cost.** Five calls per candidate. At headline scale the five stories are 53,152 tokens in total, so
one candidate costs **$0.0005 at `Qwen3-4B-Instruct-2507`** and **$0.005 at `Qwen3-235B-A22B-2507`**.
Eight candidates at both scales is under **$0.05**, well inside the free $0.10. At full 500-character
bodies once #62 exists, one candidate over five stories is 345,023 tokens — $0.0035 at the 4B model,
$0.031 at the 235B.

**A caution on how to build it**, from §5.4: machine-translating an English prompt into 36 languages
would make the results pessimistic by up to 22 points and mis-ranked. The prompt should be one
English instruction over multilingual source text — which is also what production will do.

---

## 11. Does this reopen #63?

**No, and I want to separate three claims that could be mistaken for each other.**

**#63's decision holds.** A hosted model over the network, one call per essay, generated once per
story and kept. §4 confirms it on grounds #63 did not have: the hosted route is free at the required
volume, and the local route is not clearly feasible at any volume and is dominated at every point of
its uncertainty band.

**#63's arithmetic needs correcting on the record, and #64 inherits the correction.** The input is
411,000–511,000 tokens per essay at the median reconstruction, not 74,250 — 2.8× to 3.5× on the same
run, from three compounding causes in §2. The consequence is real: **the essay cannot read the full
bodies of all its sources, and a cut has to be chosen.** #63 rejected reading only headlines; it did
not consider truncating every body to its lede, which §3 argues is the cut that fits #60's
per-source anchoring gate. That is a decision the owner has not taken and this document does not take
for them.

**#63's stated reason for rejecting local weights is the weakest of the three available.** #63 said
nothing that fits the runner *reads the language set well enough to publish*. §5.2 supports that at
the sizes the runner forces — a 1.7B model is at chance in Greek. But two harder objections need no
benchmark at all: quadratic attention prefill on a GPU-less 4-vCPU runner puts every conventional
model outside a 6-hour job before quality enters the argument, and 100+ CPU-hours a day of model
inference fails the Actions terms' disproportionate-burden clause, whose remedies reach the account
that publishes the site. Substituting stronger reasons for a weaker one is a correction, not a
reopening.

**The one finding that would reopen it.** If `prism-ml/Ternary-Bonsai-27B-gguf` prefills fast enough
on a 4-vCPU runner (§9.2) *and* retains its base model's multilingual ability through a 1.71-bit
quantisation (§9.7), then a 27B-class model runs in the runner at 262k context for nothing, and #63's
*"nothing that fits in a runner with 4 vCPU, 16 GB and no GPU reads that set at a level worth
publishing"* would be false as a matter of fact. One of those two is cheap to test; the other — whether
a ternary quantisation preserves Greek and Ukrainian — is the one I would bet against, because low-bit
quantisation damages the least-represented parts of a model's training distribution first and that is
precisely what these languages are. **It should be tested rather than assumed, and it is #74's
business to test it, not to decide it.**

Note that even both resolving favourably would not make Route 3 *advisable*, because the Actions-terms
objection in §4.3 is untouched by either. The same finding would, however, make the model itself the
strongest candidate on **Route 1**, where it is served at $0/M with a 262k window and no compute
question at all — which is why §9.1 is the first thing to settle and §9.2 the second.

---

## 12. The numbers that constrain the decision

1. **One essay call needs 411,000–511,000 input tokens at the median reconstruction, not the ~80,000
   the ticket states** — 592 sources on the largest featured story, 2,288 characters each, at a
   per-language tokenizer fertility of 1.7×–3.8× the English rate. Nothing servable reads that
   reliably, so the input must be cut, and the cut is an open design decision.

2. **Hugging Face's free inference credit is $0.10 a month, and it buys 145 essays at
   `Qwen3-4B-Instruct-2507` reading 500 characters a source, against a pessimistic requirement of
   150.** The next size class up, `gemma-4-26B-A4B-it`, buys 25. PRO at $9/month buys 504 at that
   size class. The free tier is a hard stop, not overage billing, which is the failure mode a public
   repository wants.

3. **The provider decides the usable window, not the model.** `Qwen3-235B-A22B` declares 262,144 and
   is served at 40,960 by one provider and 32,000 by another; `Llama-3.3-70B-Instruct` is served at
   **6,000** by one and 131,072 by three. The provider must be pinned, and pinning disables failover.

4. **Route 3 fits every documented GitHub quota and fails the Actions terms.** Five parallel jobs is
   inside the 20-concurrent limit, minutes are *"free and unlimited on public repositories"*, and
   there is no monthly cap for public repositories — but the terms forbid *"activity that places a
   burden on our servers, where that burden is disproportionate to the benefits provided to users"*,
   and separately *"You may only access and use GitHub Actions to develop and test your
   application(s)."* The stated remedies include suspension of the account, which also publishes the
   site. **Route 1's worst case is a 402 and no essay; Route 3's worst case is the website going
   down.** This is a reading, not a settled answer, and §9.4 says how to settle it.

5. **On native Greek, an open-weight model scores 79.41 at 27B, 62.24 at 4B, and 29.68 at 1.7B
   against a 30.42 random baseline.** Greek is 6.8% of the featured five's sources. The free budget
   affords the 4B row.

6. **A 7B model's instruction-level accuracy falls from 73.7 in English to 49.4 in Greek, and a
   frontier model's from 90.3 to 79.3.** Output is mechanically gated, so this is not a quality
   gradient but a rate at which sentences are discarded — and they are discarded in the languages the
   product exists to compare.

7. **No long-context benchmark covers Greek, Arabic or Turkish; none measures multilingual
   comprehension past 128K; and none measures long context and instruction following together in any
   language.** The system needs all three at once, at 3–4× the furthest anything has been measured.

8. **No model the router serves today has an independent per-language evaluation in any of the five
   languages that matter** — not Qwen3.5/3.6, not gemma-4, not GLM-5.x, not DeepSeek-V4, not Kimi-K3,
   and not either model this document recommends between. The evaluation in §10 costs about $0.01 on
   this project's own corpus and is the only thing that would change that.
