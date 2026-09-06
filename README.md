<div align="center">

# tensionr

**Measuring the disagreement between those who narrate the world, not the world itself.**

[![License](https://img.shields.io/badge/License-MIT-black.svg)](https://opensource.org/licenses/MIT)
[![Site](https://img.shields.io/badge/site-live-black.svg)](https://exdsgift.github.io/tensionr/)
[![Engine](https://img.shields.io/badge/engine-Python%203.12-black.svg)](backend/)
[![Site build](https://img.shields.io/badge/site-Next.js%2016-black.svg)](frontend/)
[![Tests](https://img.shields.io/badge/tests-229-black.svg)](#testing)

[Live site](https://exdsgift.github.io/tensionr/) &nbsp;|&nbsp;
[Quick start](#quick-start) &nbsp;|&nbsp;
[How it works](#how-it-works) &nbsp;|&nbsp;
[Architecture](#architecture) &nbsp;|&nbsp;
[Decisions](docs/adr/) &nbsp;|&nbsp;
[Research](docs/research/)

</div>

---

## Overview

Every few hours the engine takes a window of the world's news, groups articles that are
telling the **same story** across different sources and languages, and measures how
differently those sources name the people and places in it.

It publishes the five most divided stories, the evidence behind each one (every source,
and who each one named), and a statement of what it did *not* see.

The last published run, in full:

| | |
| --- | --- |
| Articles read | **90,467** from 47 of 48 slots |
| Publishers placed in a country | **96.3%** of 7,913 domains |
| Grouped into | 758 themes, 961 stories |
| Stories clearing both floors | 14 |
| Wall clock | 3 minutes |

The window has since moved from 12 hours to 16. Measured on the wider window before it
shipped: **170,427 articles**, peaking at **1.1 GB** of the runner's 16 GB.

---

## Key features

- **Story granularity, deliberately.** The unit is the story, never the event. A ten-word
  headline does not distinguish *"Starmer will resign"* from *"Starmer has resigned"*, and
  human annotators do not either. Measured on a hand-built gold set: precision **0.86 at
  story granularity, 0.23 at event granularity**. That is a property of the input, not a
  tuning problem.

- **Cross-lingual by construction.** Grouping runs on 512-dimensional document embeddings,
  so *Иран*, *إيران* and *Iran* resolve to one actor and one story without translation.

- **Per-window thresholds, not constants.** The percolation point moves between windows.
  It is found per run by walking thresholds down until the largest component would exceed
  a stated share of the corpus, and the threshold chosen is published.

- **A country test, not just an entropy score.** Binary entropy peaks at one half, which is
  also what a coin gives, so it cannot tell a story that splits *by country* from one that
  splits at random. A permutation test answers the second question and the page prints the
  table it rests on, row by checkable row.

- **Every figure carries its unit, its procedure and its uncertainty**, or it is not
  published. Underpowered tests say so instead of printing a bare "not significant".

- **No tension score.** Two independent attempts at aggregating divergence into a single
  number both ranked noise first and the visibly divergent story near the bottom, for a
  structural reason rather than a tunable one. The index was removed.

- **Static output.** The site is a static export with no client-side data fetching; the
  whole page survives with JavaScript off, and the weight is enforced in CI.

---

## Quick start

### Requirements

- Python 3.12 and [`uv`](https://docs.astral.sh/uv/)
- Node 24 (site only)

### Run the engine

From the repository root, so `data/` resolves. Use `--project` rather than `--directory`:
the engine's paths are relative to the root, and `--directory` would move there with it.

```bash
uv sync --project backend
uv run --project backend python -m tensionr.stories --out out
```

Three runtime dependencies: `requests`, `numpy`, `python-dotenv`. Set `HF_TOKEN` in `.env`
at the repository root to enable the Hugging Face stages.

### Run the site

```bash
tools/serve-site.sh          # build the static export and serve it at :8123
```

This builds the site the way it is actually published, then serves the files. For writing
components, `cd frontend && npm run dev` is faster.

The engine's output is not in this repository. It lives on the `data` branch so the
production ref stays protectable. For a page with real stories on it:

```bash
git fetch origin data && git show origin/data:data/stories.json > data/stories.json
```

### Testing

```bash
uv run --project backend pytest        # 188 tests
cd frontend && npm test                # 41 tests
```

---

## How it works

```
GDELT docembed          one gzipped JSONL per 15 minutes, 512-dim per article
      |
      v
  window              64 slots = 16 hours, sized against the worst delivered gap
      |
      v
  themes              cosine edges above a per-window threshold, connected components
      |
      v
  stories             a second pass inside each theme, so one theme is not one story
      |
      v
  identity            joined to the previous run by shared article URLs, not similarity
      |
      v
  measure             per (story, actor): named / evaluable / unresolved, by country
      |
      v
  data/               stories.json, state.json, and an append-only per-run record
```

<details>
<summary><b>Why the window is 16 hours and not 4</b></summary>

GDELT is not an archive. It publishes a quarter hour of the world and then drops it, so a
slot nobody fetches in time is gone for everyone. The engine covers that by reaching back
much further than its own cadence, and the overlap is the safety net.

GitHub's scheduler is best effort. Measured over 57 delivered runs across 13.5 days it
honours about **70%** of what the cron asks for, every run arriving 13 to 225 minutes late,
and twice the gap between two delivered runs exceeded a 12-hour window. About 1.5 hours of
the corpus was lost, silently: both runs succeeded and nothing was logged.

| Window | Gaps covered | Worst uncovered |
| ---: | --- | --- |
| 12 h | 54 of 56, 96.4% | 13.12 h |
| 14 h | 56 of 56, 100% | none |
| **16 h** | 56 of 56, 100% | none |

Fourteen hours would clear the worst gap ever seen by four minutes, which is not a margin.

</details>

<details>
<summary><b>Why three states and not two</b></summary>

A source that did not name an actor is not the same as a source that could not have. If no
alias exists in the row's own language, the question cannot be answered and the row is
`unresolved` rather than `absent`. Before this distinction existed, a Bulgarian headline
found the Russian aliases, was judged answerable, matched none of them, and its author was
recorded as having omitted an actor they had in fact named.

Evaluability is decided by **language**, matching by **script**. They are not the same
question: Cyrillic is shared by five languages.

</details>

<details>
<summary><b>Why publishers are placed by three sources in order</b></summary>

A hand-written table first, then the country TLD, then a bulk lookup built from GDELT's own
domain table. The order makes the join purely additive: the bulk table can place a publisher
that was previously unplaced and can never overrule a placement already being made.

That matters, because the bulk table is wrong about the cases that matter most. It calls
`aljazeera.com` United States and `aljazeera.net` Israel. Across the domains where both
tables answer they agree 95.2% of the time, but the 4.8% is concentrated in exactly the
outlets somebody had already found worth correcting.

Coverage went from **41.4% to 96.3%** without one existing placement moving.

</details>

---

## Architecture

```
backend/          the engine. Python, reads GDELT, writes JSON. Self-contained.
frontend/         the site. Next.js + shadcn/ui, exported as static files.
data/             the contract between them, published as-is.
docs/adr/         decisions that constrain the code.
docs/research/    what was measured, and how.
tools/            things run by hand.
.github/          the workflows, and the scripts they call.
```

`data/` sits between the two on purpose. The engine writes it, the frontend build reads it,
and readers can fetch it: the footer points at `data/stories.json`, which needs nothing from
this site to be useful.

### Branches

| Ref | Publishes to | Role |
| --- | --- | --- |
| `master` | the site root | Production. Reached by pull request only. |
| `staging` | `staging/` | A sandbox. Push to it, force-push it, break it. |
| any branch with an open PR | `preview/<branch>/` | Appears when the PR opens, goes when it closes. |
| `data` | not a site | The engine's current output. |
| `history` | not a site | Append-only per-run records, on a 20-day rolling window. |

`staging` and the previews answer different questions. Staging is where changes live
together on real data at a real URL; a preview is where one change is judged on its own.
Neither is indexed.

**Staging cannot take production down.** The site is reassembled from git refs on every
deploy, so whichever branch triggers a run, the production half of the artifact always comes
from `master`. A staging tree that will not build is reported and skipped; a production tree
that will not build aborts the deployment and Pages keeps serving the last good build.

### Workflows

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `Story engine` | every 4 hours | Fetches a window, groups it, measures it, publishes to `data` and `history`. |
| `Publish the site` | push, pull request | Reassembles the whole site from refs and deploys it. |
| `Checks` | pull request | `Backend · pytest`, `Backend · ruff`, `Frontend · build, markup, weight`, `Scripts · publish.sh`. |
| `Prune captures` | daily | Reports what the rolling window would remove. Applying is a manual dispatch. |

---

## Budgets enforced in CI

The site is graded on every pull request, not reviewed by eye:

| | Measured | Budget |
| --- | ---: | ---: |
| Content, gzipped | 109.4 KB | 160 KB |
| First load, total | 403.2 KB | 520 KB |
| Page readable with scripts stripped | 17,676 words | must be non-empty |

The markup check strips `<script>` blocks before grading, because Next serialises the whole
tree into the RSC payload and a naive grep for the page's text passes even when the page is
empty without JavaScript.

---

## Documentation

| | |
| --- | --- |
| [`docs/adr/`](docs/adr/) | Decisions that constrain the code, with the measurements behind them. |
| [`docs/research/`](docs/research/) | What was measured and how, including the negative results. |
| [`CLAUDE.md`](CLAUDE.md) | Conventions for agents working in this repository. |

---

## License

MIT. Built by [exdsgift](https://github.com/exdsgift).

GDELT data is used under its own terms; see [`docs/research/`](docs/research/) for what was
verified about them.
