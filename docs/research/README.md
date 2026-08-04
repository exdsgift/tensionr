# Research corpus

Findings that the v2 decisions were made against. Each document was produced to answer one issue and is linked from the decision it supports. Measurements state their window and their gaps; where a figure was later refuted by a further measurement, the refutation is noted here rather than silently corrected in place.

| Document | Answers | Headline result |
|---|---|---|
| [`event-clustering-multilingual-headlines.md`](event-clustering-multilingual-headlines.md) | [#2](https://github.com/exdsgift/tensionr/issues/2) | GDELT's Global Similarity Graph publishes precomputed cross-language same-story edges. LaBSE and multilingual-e5 both ruled out with benchmark evidence. |
| [`framing-divergence-measurement.md`](framing-divergence-measurement.md) | [#3](https://github.com/exdsgift/tensionr/issues/3) | Divergence is measurable from headlines alone. Actor-presence recommended; GoEmotions rejected as unvalidatable (Fleiss κ = 0.09, no gold label). |
| [`pixel-indie-aesthetic-for-data.md`](pixel-indie-aesthetic-for-data.md) | [#4](https://github.com/exdsgift/tensionr/issues/4) | *Look Outside*'s palette is DawnBringer 16 exactly. It uses no grid-locked bitmap font, so the integer-multiple constraint does not apply. Its chrome fails WCAG; its body text does not. |
| [`feed-panel-audit.md`](feed-panel-audit.md) | [#15](https://github.com/exdsgift/tensionr/issues/15) | 8 of 23 feeds inert, 3 of them returning HTTP 200. China Daily frozen since 2017-12-12. Corpus window ~31 hours. |
| [`pipeline-cost-audit.md`](pipeline-cost-audit.md) | [#16](https://github.com/exdsgift/tensionr/issues/16) | `data/` is 93.6% of git history at +9.5 MiB/month. The cron delivers 45% of requested runs. The 98.87% success rate is false: half of green runs publish no GDELT article. |
| [`panel-candidates.md`](panel-candidates.md) | [#17](https://github.com/exdsgift/tensionr/issues/17) | GDELT does not carry Reuters, AP, WSJ, Le Monde, Meduza, TASS or NHK — all 0 records/day. |
| [`polity-availability.md`](polity-availability.md) | [#21](https://github.com/exdsgift/tensionr/issues/21) | 13 languages meet a resilient two-polity quorum, 6 cannot. 68% of top-host volume is not journalism. Perfect liveness is an anti-signal. |
| [`cross-lingual-actors.md`](cross-lingual-actors.md) | [#22](https://github.com/exdsgift/tensionr/issues/22) | GKG joins to our clusters at 95.3% and its name fields are 100% Latin script, but translation is not resolution: raw names carry a 0.501 language artefact against 0.189 for the recommended design. |
| [`language-residual.md`](language-residual.md) | [#23](https://github.com/exdsgift/tensionr/issues/23) | About 70% of the 0.189 residual is editorial difference between polities, not a language artefact. A published figure moves 0.7pp at `M ≥ 50` and 4.9pp below `M = 20`; what does not survive is the ranking, where top-10 overlap is 3/10 at a floor of 10 and the #1 row is never stable. |
| [`mobile-legibility.md`](mobile-legibility.md) | [#51](https://github.com/exdsgift/tensionr/issues/51) | The published homepage scrolled sideways by 6,532px at 320 CSS px, from a measuring probe left at `font-size:100px`, and the map was never being resized at all — a bare `1fr` track took its 571px max-content size at every width. No monospace font covers the braille block, so the advance is 10.6–16.7% wider than `1ch`. 76 columns cannot be legible under 603px of viewport; 38 columns can, and score the same 32 of 34 on the check that guards the projection. |

## Corrections between documents

Later measurement refuted three earlier claims. All three are recorded because the pattern matters more than the individual numbers.

| Claim | Source | Refuted by |
|---|---|---|
| Percolation threshold 0.68–0.70 leaves the largest cluster at 1.7–4.0% of the corpus | `event-clustering` | Measured at 25.3% on a fresh window ([#7](https://github.com/exdsgift/tensionr/issues/7)). Threshold is not a constant: 0.75, then 0.76 in a third window. |
| The `gsg_docembed` archive reaches back to 2020-01-01 | `event-clustering` | `20250801000000` returns 404 ([#12](https://github.com/exdsgift/tensionr/issues/12)). Retention is under a year. |
| Per-outlet GDELT presence is intermittent day to day (Al-Ahram 348 → 0) | `panel-candidates` | Bursty, not dead: 267/day across 17 of 96 census slots ([#21](https://github.com/exdsgift/tensionr/issues/21)). A worse problem than intermittency. |
| Per-language bias can be calibrated away with a per-language offset | assumed while scoping [#23](https://github.com/exdsgift/tensionr/issues/23) | A per-language main effect explains 1.2% of variance, rms deviation falls 11.1pp → 11.0pp, and the fitted offsets do not replicate between windows (r = +0.11). `language-residual` |
| On a phone the braille map hits its 4px floor and becomes a grey smear | assumed while scoping [#51](https://github.com/exdsgift/tensionr/issues/51) | The floor needs a 240px viewport and was never reached. The map ran at its 11px *ceiling* at every phone width, because a `1fr` grid track sized itself to the block's max-content. `mobile-legibility` |
| The evidence tables are the widest thing on the page and the likely cause of sideways scrolling | assumed while scoping [#51](https://github.com/exdsgift/tensionr/issues/51) | They never reached the document — `overflow-x:auto` contained every one. The measuring probe did, at 6,836px. What was wrong with the tables was vertical: automatic layout left the headline column 160 of 620px and the 26 tables came to 403,000px of rows. `mobile-legibility` |
| `ch` is the advance of `0` in the first available font, which is why it is wrong for braille | code comment in `ledger.html`, from [#41](https://github.com/exdsgift/tensionr/issues/41) | `ch` is the advance of `0` in the font that renders it, and the "first available font" wording was removed from CSS Fonts 4 as incorrect. All three engines resolve it from the *primary* font and never consult the fallback. The conclusion held; the reason did not. `mobile-legibility` |

## Open

Two, both from [#51](https://github.com/exdsgift/tensionr/issues/51) and both design decisions rather than unanswered measurements.

- **`body { font-size: 15px }` overrides the reader's default font size**, and with it the `<meta name="text-scale">` route to the OS text-size setting that ~34–37% of mobile users have changed. Deleting the declaration does not fix it — `medium` for a monospace stack is 13px, not 16 — so the fix is to negotiate rather than override, which rescales the whole page. `mobile-legibility` §4.4.
- **`max-height: 26rem` on the evidence tables nests a vertical scroller inside a vertically scrolling page.** Practitioner consensus is against that nesting; it is also what makes the sticky header stick within a screen. `mobile-legibility` §3.3.

[#23](https://github.com/exdsgift/tensionr/issues/23) was the last open *measurement* question and `language-residual.md` answers it: the residual is mostly editorial rather than an artefact, a figure with a large enough denominator survives it, and the ranking does not — which is why the product publishes a band rather than a #1.
