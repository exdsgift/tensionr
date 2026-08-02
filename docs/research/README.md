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

## Corrections between documents

Later measurement refuted three earlier claims. All three are recorded because the pattern matters more than the individual numbers.

| Claim | Source | Refuted by |
|---|---|---|
| Percolation threshold 0.68–0.70 leaves the largest cluster at 1.7–4.0% of the corpus | `event-clustering` | Measured at 25.3% on a fresh window ([#7](https://github.com/exdsgift/tensionr/issues/7)). Threshold is not a constant: 0.75, then 0.76 in a third window. |
| The `gsg_docembed` archive reaches back to 2020-01-01 | `event-clustering` | `20250801000000` returns 404 ([#12](https://github.com/exdsgift/tensionr/issues/12)). Retention is under a year. |
| Per-outlet GDELT presence is intermittent day to day (Al-Ahram 348 → 0) | `panel-candidates` | Bursty, not dead: 267/day across 17 of 96 census slots ([#21](https://github.com/exdsgift/tensionr/issues/21)). A worse problem than intermittency. |

## Open

[#23](https://github.com/exdsgift/tensionr/issues/23) decomposes the 0.189 residual and establishes whether a published per-(story, actor) figure survives it. Until it lands, every figure the product publishes carries an artefact of unstated size.
