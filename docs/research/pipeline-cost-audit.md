# Pipeline cost audit

Fact-gathering for [#16](https://github.com/exdsgift/tensionr/issues/16). Measurements only — no
proposal for a branch model, a CI design, or a storage backend. Those belong to
[#10](https://github.com/exdsgift/tensionr/issues/10) and
[#6](https://github.com/exdsgift/tensionr/issues/6), and to a human.

- **Measured on**: 2026-08-02
- **Repository**: `exdsgift/tensionr`, public, default branch `master`, created 2026-05-05
- **Sources**: `gh run list` / `gh run view --log-failed` / `gh api`, and local `git` on `origin/master`
  at `b45b57b`
- **Run history window**: 2026-05-05T21:56Z → 2026-08-02T12:49Z (88.5 days)

## 0. Three premises in the ticket that no longer hold

The ticket was written against an earlier shape of the repository. Correcting it first, because the
rest of the numbers only make sense against the current layout.

| Ticket says | Actually |
| --- | --- |
| `timeout 600` on `src/fetch_gdelt.py` | The step is `timeout 600 uv run tensionr`. `src/fetch_gdelt.py` does not exist; the pipeline is the package `src/tensionr/` with entry point `tensionr = tensionr.pipeline:main`. |
| `requirements.txt` pins | `requirements.txt` was deleted on 2026-07-21 (`94ba01f`). Dependencies now live in `pyproject.toml` and are locked in `uv.lock`. |
| "zero tests" (map #1) | `tests/` holds 4 files, 363 lines, **23 test functions**, and `pytest>=8` is declared in the `dev` dependency group. What is true is that **CI never runs them**: `pytest` appears nowhere under `.github/`. |

The workflow has been rewritten three times. This matters for reading the duration series:

| Date | Commit | Change |
| --- | --- | --- |
| 2026-05-05 | `c3ac6d6` | Initial: `actions/setup-python`, `pip install -r requirements.txt`, step `Fetch data from GDELT`, no timeout |
| 2026-05-27 | `9135539` | Migrated to `uv`; added the missing `click` dependency |
| 2026-05-28 | `cc305e3` | **Added `timeout 600`** and the JSON validation step |
| 2026-07-21 | `4a5c426` | Package refactor; step renamed `Run data pipeline` |

## 1. Run history — `Tensionr Data Synchronizer`

993 runs have existed (run numbers 2–993 visible; #1 has aged out of the API). **975 are still
queryable**, 974 of them completed with a `success`/`failure` conclusion.

### Outcomes

| | Count | Share |
| --- | --- | --- |
| success | 964 | 98.87% |
| failure | 10 | 1.03% |
| cancelled | 1 | 0.10% |
| **total queryable** | **975** | |

Triggers: 965 `schedule`, 10 `workflow_dispatch`. No run was ever retried (`attempt` = 1 everywhere).

### Wall-clock duration per run, by workflow era

Seconds, from `startedAt` to `updatedAt`.

| Era | n | min | p25 | median | mean | p75 | p90 | p95 | max | >300s | ≥600s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All (05-05 → 08-02) | 974 | 28 | 96 | **115** | 134.6 | 141 | 177 | 289 | 903 | 48 | 8 |
| Pre-timeout (05-05 → 05-27) | 255 | 28 | 105 | 123 | 139.4 | 146 | 169 | 212 | 804 | 7 | 4 |
| Timeout era (05-28 → 07-20) | 560 | 56 | 88 | 106 | 128.4 | 129 | 180 | 343 | 616 | 35 | 2 |
| Current package (07-21 → 08-02) | 159 | 69 | 115 | **134** | 148.8 | 149 | 186 | 249 | 903 | 6 | 2 |

Failure rate per era: pre-timeout 1.96%, timeout era 0.54%, current package 1.26%.

### The fetch/pipeline step specifically

Step timings sampled from 55 successful runs (every 24th run across the window, **plus every run
over 480s** — so the tail is deliberately over-represented and the mean below is inflated; use the
run-level table above for the distribution).

| Step | n | min | median | mean | p90 | max |
| --- | --- | --- | --- | --- | --- | --- |
| `Fetch data from GDELT` (pre-07-21) | 47 | 21 | 106 | 224.5 | 542 | **757** |
| `Run data pipeline` (post-07-21) | 8 | 101 | 123 | 167.9 | 510 | 510 |
| `Install dependencies` | 55 | 2 | 6 | 12.4 | 29 | 35 |
| `Set up uv` | 37 | 1 | 2 | 2.4 | 3 | 4 |
| `Commit and push changes` | 55 | 0 | 2 | 1.8 | 2 | 14 |
| `Checkout repository` | 55 | 0 | 1 | 0.9 | 1 | 2 |
| `Validate output data` | 37 | 0 | 0 | 0.0 | 0 | 0 |

Everything except the pipeline step is noise: setup + install + commit + checkout is ~10–20s.
Run duration is the pipeline step plus roughly 15s.

The 757s maximum is from before 2026-05-28, when the step had no timeout.

### Is `timeout 600` being hit? Yes — three times, confirmed from step timings

| Run | Date | Step that failed | Step duration | Exit |
| --- | --- | --- | --- | --- |
| #355 | 2026-06-06 | `Fetch data from GDELT` | 09:15:28 → 09:25:28 = **600s exactly** | — |
| #367 | 2026-06-07 | `Fetch data from GDELT` | 06:55:04 → 07:05:04 = **600s exactly** | — |
| #984 | 2026-08-01 | `Run data pipeline` | 20:02:35 → 20:12:35 = **600s exactly** | **124** (`timeout` kill) |

Exit code 124 is the signature. In all three the subsequent `Validate output data` and
`Commit and push changes` steps were `skipped`, so **the run produced no commit** — the hour's data
was lost.

The log of #984 shows where the 600s went:

```
[timing] nlp enrichment: 560.5s (total 586.4s)
[timing] fetch intel/markets/flights: 3.4s (total 589.9s)
WARNING deadline reached (590s): skipping LLM stages
[timing] llm synthesis: 0.0s (total 589.9s)
##[error]Process completed with exit code 124
```

The NLP enrichment stage alone consumed 560.5s of the 600s budget. `TENSIONR_DEADLINE` defaults to
480s (`src/tensionr/config.py:22`), but it is only checked at `src/tensionr/pipeline.py:121` —
**after** `enrich_new_articles()` at line 92, which is itself unbounded. So the soft deadline cannot
protect against the stage that actually overruns; by the time it is evaluated, 590s are gone and the
hard `timeout` kills the process during the write phase.

The NLP stage is bimodal. Across the 20 most recent successful runs it took 2.5–9.0s in 18 of them,
251.8s in one, and 560.5s in the run that died. It calls a remote inference API
(`src/tensionr/processing/hf.py`), so the tail is not local compute.

### The other seven failures — read from the logs, not the status

| Runs | Date | Cause (from log) |
| --- | --- | --- |
| #262–#265 (4 consecutive) | 2026-05-26/27 | `ModuleNotFoundError: No module named 'click'` — spaCy's CLI imports `click` at import time, and unpinned `typer` stopped pulling it in. A loose-pin failure. Fixed by `9135539` (explicit `click>=8` + migration to `uv`). |
| #88 | 2026-05-11 | Push failed: `remote: Internal Server Error` / `error: 500`. GitHub-side. |
| #741 | 2026-07-14 | Push failed: `remote: fatal error in commit_refs`, `! [remote rejected] master -> master (failure)`. GitHub-side. |
| #879 | 2026-07-24 | Job `cancelled` after 903s with **no steps recorded** — never got past runner assignment. Infrastructure, not the project. |

Attribution: **3 timeouts** (project), **4 dependency-resolution failures** (project, since fixed),
**3 GitHub-side** (2 push errors, 1 runner failure). Of the 10 failures, 7 predate the current
package layout.

### The cron says hourly. GitHub does not run it hourly.

`cron: '0 * * * *'` requests 24 runs/day. Measured:

| Era | Scheduled runs | Span | **Runs/day** | Median gap | Mean gap | Max gap |
| --- | --- | --- | --- | --- | --- | --- |
| All | 965 | 88.5 d | **10.90** | 112 min | 132 min | **1727 min (28.8 h)** |
| Pre-timeout | 248 | 21.2 d | 11.68 | 107 min | 124 min | 603 min |
| Timeout era | 559 | 53.6 d | 10.43 | 118 min | 138 min | 386 min |
| Current package | 158 | 12.5 d | 12.66 | 103 min | 114 min | 247 min |

**GitHub delivers about 45% of the requested schedule** — roughly one run every 1h50m, not every
hour. 438 of 964 intervals exceeded 120 minutes. The worst observed gap was 28.8 hours. Daily counts
range 2–17 with a median of 11.

Corroborating evidence in the data itself: `data/archive/` holds 73 daily snapshots covering the
74-day span 2026-05-21 → 2026-08-02. The one missing day is **2026-05-27** — the day of the four
`click` failures.

### Actions minutes

| | Value |
| --- | --- |
| Sync workflow, total wall time over 88.5 d | 2,186 min (36.4 h) |
| Sync workflow, per month | ~751 min wall / ~913 min billable-equivalent (per-run ceiling) |
| Pages builds, 994 builds over 88.5 d, median 36.6s | 714 min total, ~245 min/month |
| **Combined** | **~1,160 billable-equivalent min/month** |

The repository is **public**, so Actions minutes are not billed. The number is recorded because it
becomes a real cost the moment the repository goes private or the job moves to a paid runner.

## 2. Repository cost of the committed data

### Total size

| Measure | Value |
| --- | --- |
| GitHub-reported repository size | 30,016 KB = **29.3 MiB** |
| Local `size-pack` (11 packs, not fully repacked) | 40.35 MiB |
| Loose objects | 1,319 objects, 14.01 MiB |
| Reachable objects, sum of on-disk size | 9,095 objects, **31.55 MiB** |
| Reachable objects, sum of uncompressed size | **421.73 MiB** |

The 31.55 MiB figure is the one to reason with — it is what a clone pays. GitHub's 29.3 MiB is the
same quantity after a better repack.

### How much of that is `data/*.json`

Every reachable object, bucketed by path, sized with `git cat-file --batch-check %(objectsize:disk)`:

| Bucket | Objects | Uncompressed MiB | On-disk MiB | % of history |
| --- | --- | --- | --- | --- |
| `data/*.json` (top level) | 4,316 | 412.11 | **29.09** | **92.2%** |
| `images/` | 2 | 0.68 | 0.65 | 2.1% |
| commits / trees / tags | 3,840 | 2.44 | 0.56 | 1.8% |
| `data/archive/*.json` | 779 | 4.09 | 0.44 | 1.4% |
| other root files | 66 | 0.85 | 0.30 | 1.0% |
| `*.js` | 54 | 0.87 | 0.29 | 0.9% |
| `src/` (Python) | 29 | 0.31 | 0.11 | 0.3% |
| `uv.lock` | 1 | 0.28 | 0.09 | 0.3% |
| `*.css` | 4 | 0.08 | 0.02 | 0.1% |
| `tests/` | 4 | 0.01 | 0.00 | 0.0% |
| **Total** | **9,095** | **421.73** | **31.55** | |

**`data/` accounts for 29.53 MiB of 31.55 MiB — 93.6% of the repository's history on disk, and
98.7% of it uncompressed (416.2 of 421.7 MiB).** All hand-written code — Python, JS, CSS, HTML,
tests, config — is 0.51 MiB, about 1.6%.

### Commit rate of the automated job

| | Value |
| --- | --- |
| Total commits on `origin/master` | 1,013 |
| Commits with message `Automated update of GDELT data` | **959 (94.7%)** |
| Human commits | 54 (5.3%) |
| First / last automated commit | 2026-05-05T21:57Z / 2026-08-02T12:50Z |

| Month | Automated | All | Automated share |
| --- | --- | --- | --- |
| 2026-05 | 287 | 338 | 84.9% |
| 2026-06 | 259 | 259 | **100%** |
| 2026-07 | 393 | 396 | 99.2% |
| 2026-08 (2 days) | 20 | 20 | 100% |

Recent daily rate: 10–17 automated commits/day, typically 12.

### Growth per month

Each `data/` blob attributed to the month it first entered history:

| Month | New `data/` blobs | Uncompressed MiB | On-disk MiB |
| --- | --- | --- | --- |
| 2026-05 (27 d) | 1,365 | 112.89 | 10.25 |
| 2026-06 (full) | 1,433 | 120.19 | 7.17 |
| 2026-07 (full) | 2,178 | 174.59 | 11.83 |
| 2026-08 (2 d) | 118 | 8.25 | 0.23 |
| **Total** | **5,094** | **415.92** | **29.48** |

**Mean over the two full calendar months: 9.50 MiB/month of packed history, ~147 MiB/month
uncompressed.** (Per-month on-disk attribution is approximate — delta chains cross month
boundaries — but the total reconciles with the 29.53 MiB measured independently above.)

Straight-line projection at the current rate, on top of today's 31.55 MiB:

| Horizon | Projected clone size |
| --- | --- |
| +6 months | ~89 MiB |
| +12 months | ~146 MiB |
| +24 months | ~259 MiB |

### Why it is expensive: the payload is rewritten whole every run

| File | Current size |
| --- | --- |
| `data/news.json` | 370,929 B (**362 KiB**) |
| `data/telemetry.json` | 29,555 B |
| `data/status.json` | 6,101 B |
| `data/intelligence.json` | 3,550 B |
| `data/markets.json` | 1,287 B |
| **Total top-level** | **411,422 B (402 KiB)** |
| `data/archive/` | 73 files, 584 KiB |

`news.json` is a rolling window of 500 articles (`ARTICLE_CAP = 500`) written from scratch each run.
A representative automated commit is `5 files changed, 3,973 insertions(+), 4,058 deletions(-)`.
Because `git add data/*.json` uses a git pathspec (whose `*` crosses `/`), the daily
`data/archive/<date>.json` snapshot is committed too, so the archive is overwritten several times a
day, not once.

Every one of those 959 commits landed on `master`, and `master` is what Pages serves — hence 994
Pages rebuilds in 88.5 days.

## 3. Publication setup

`gh api repos/exdsgift/tensionr/pages`:

| Field | Value |
| --- | --- |
| `html_url` | `https://exdsgift.github.io/tensionr/` |
| `build_type` | **`legacy`** (branch-served, not the Actions-based `workflow` builder) |
| `source.branch` | **`master`** |
| `source.path` | **`/`** (repository root) |
| `status` | `built` |
| `cname` | `null` |
| `https_enforced` | `true` |
| `public` | `true` |

There is no Pages workflow file in `.github/workflows/`; deployment is GitHub's implicit legacy
builder. Pages build history: **994 builds**, 981 `built` / **13 `errored`** (1.3%), median 36.6s,
mean 43.1s, max 578s.

The consequence for any branch model: the site is served from the root of `master`, so the
production artefact and the branch that receives ~12 automated data commits a day are the same ref.

## 4. Existing tooling surface

### Python dependencies — `pyproject.toml` (no `requirements.txt`)

| Package | Constraint | Tightness |
| --- | --- | --- |
| `requests` | `>=2.32` | lower bound only |
| `feedparser` | `>=6.0` | lower bound only |
| `pandas` | `>=2.2` | lower bound only |
| `numpy` | `>=2.0` | lower bound only |
| `scikit-learn` | `>=1.5` | lower bound only |
| `spacy` | `>=3.8,<3.9` | **bounded** |
| `click` | `>=8` | lower bound only (added to fix #262–#265) |
| `yfinance` | `>=0.2.50` | lower bound only |
| `python-dotenv` | `>=1.0` | lower bound only |
| `xx-ent-wiki-sm` | direct wheel URL, **`3.8.0` exact** | **pinned** |
| `pytest` (dev group) | `>=8` | lower bound only |

**9 of 11 declarations are open-ended lower bounds.** What makes CI reproducible is not the
constraints but `uv.lock` (290,736 B) combined with `uv sync --frozen` in the workflow — an exact,
hash-locked resolution. The `requirements.txt` that was deleted on 2026-07-21 had **no version
constraints at all** (`requests`, `pandas`, `python-dotenv`, `spacy`, `click`, `feedparser`,
`yfinance`, `scikit-learn`, `scipy`), which is what produced the four `click` failures.

Note: `scipy` was dropped in the migration and `pandas`/`numpy`/`scikit-learn` remain declared.

### Python version

| Where | Value |
| --- | --- |
| `pyproject.toml` `requires-python` | `>=3.12` (open-ended upper) |
| `astral-sh/setup-uv@v5` `python-version` | `"3.12"` |
| Observed on the runner | 3.12.13 |

No `.python-version` file.

### Lint / type / test configuration

| Tool | Present |
| --- | --- |
| `ruff` / `flake8` / `black` / `isort` | none |
| `mypy` / `pyright` | none |
| `pre-commit` | none |
| `[tool.*]` sections in `pyproject.toml` | **none** (only `project`, `dependency-groups`, `project.scripts`, `build-system`) |
| `.editorconfig`, `tox.ini`, `setup.cfg` | none |
| `pytest` | declared as a dev dependency, **never invoked in CI** |

### JS tooling

There is none. No `package.json`, no `node_modules`, no lockfile, no `.nvmrc`, no ESLint/Prettier
config, no bundler, no test runner. The 9 `.js` files are loaded as plain `<script>` tags from
`index.html`. Everything third-party comes from a CDN at runtime:

| External runtime dependency | Version |
| --- | --- |
| Google Fonts — Fira Code | — |
| Leaflet CSS + JS (`unpkg`) | 1.9.4 |
| flatpickr CSS + JS (`jsdelivr`) | 4.6.13 |
| Chart.js (`jsdelivr`) | 4.4.9 |

**4 distinct CDN origins, 7 external requests, zero version locking on the JS side.** This is the
"5 CDN libraries plus Google Fonts" noted in map #1.

### Workflows

One workflow file: `.github/workflows/update_data.yml`, 46 lines. Actions used:
`actions/checkout@v4`, `astral-sh/setup-uv@v5`, `stefanzweifel/git-auto-commit-action@v5` — all
major-tag pinned, none SHA-pinned. All three emit the Node 20 deprecation warning and are forced to
Node 24 via `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`.

## 5. Line counts and file inventory

| Language / area | Files | Lines |
| --- | --- | --- |
| Python — `src/tensionr/` | 17 (3 empty `__init__.py`) | **1,249** |
| Python — `tests/` | 4 | **363** (23 test functions) |
| **Python total** | **21** | **1,612** |
| JavaScript (root) | 9 | **1,319** |
| CSS — `styles.css` | 1 | 752 |
| HTML — `index.html` | 1 | 186 |
| YAML — workflow | 1 | 46 |
| TOML — `pyproject.toml` | 1 | 30 |
| **Total hand-written** | **34** | **3,945** |

Python modules, largest first:

| File | Lines |
| --- | --- |
| `src/tensionr/pipeline.py` | 203 |
| `src/tensionr/processing/hf.py` | 182 |
| `src/tensionr/config.py` | 165 |
| `src/tensionr/fetchers/news.py` | 112 |
| `src/tensionr/fetchers/flights.py` | 97 |
| `src/tensionr/processing/analytics.py` | 97 |
| `src/tensionr/scoring.py` | 89 |
| `src/tensionr/output.py` | 67 |
| `src/tensionr/http_client.py` | 57 |
| `src/tensionr/fetchers/markets.py` | 47 |
| `src/tensionr/processing/articles.py` | 47 |
| `src/tensionr/fetchers/intel.py` | 46 |
| `src/tensionr/processing/keywords.py` | 36 |
| `src/tensionr/__main__.py` | 4 |

JS files: `app.js` 407, `charts.js` 258, `api.js` 166, `ui.js` 148, `tactical_map.js` 105,
`map.js` 98, `utils.js` 75, `worker.js` 43, `state.js` 19.

A lint/type/test step would therefore have to cover **1,612 lines of Python across 21 files** and
**1,319 lines of JS across 9 files** — and on the JS side would have to establish a toolchain from
nothing.

## 6. Observation: the 98.87% success rate does not mean the data is good

Not part of the requested measurements, recorded because it bears on the data-gate question and on
how any future CI signal should be read. **No fix is proposed here.**

Scan of the 20 most recent `success` runs, from their logs:

| Symptom | Runs affected |
| --- | --- |
| `GDELT article fetch degraded (no data this run)` | **10 / 20 (50%)** |
| `GDELT timeline fetch degraded` | **6 / 20 (30%)** |
| At least one `RSS feed degraded: <domain>` | **20 / 20 (100%)** — typically 3–5 of the 15 feeds sampled from 23 |
| `feeds.reuters.com` failing | frequent; the domain does not resolve (`NameResolutionError` in the 2026-07-14 log) |

All 20 were marked `success` and all 20 committed. `src/tensionr/fetchers/news.py` guards only on
`status_code != 200` (lines 43 and 60) and then does `.get("articles", [])` / `.get("timeline", [])`,
so a 200 whose body lacks the expected key degrades to an empty list, logs a `WARNING`, and the run
completes green. Half the "successful" hours are shipping no GDELT articles at all.

The `Validate output data` step is `jq empty` over five files. It catches a malformed or missing
file, but it is a syntax check: a structurally valid document containing zero new records passes.

Context from a parallel investigation (not verified here): GDELT's **Global Frontpage Graph** has
been returning **HTTP 200 with a 45-byte empty gzip payload** since around October 2025. That
endpoint is not the one this pipeline calls — it uses GDELT DOC 2.0 `mode=ArtList` and
`mode=TimelineVol` at `api.gdeltproject.org/api/v2/doc/doc` — but it is the same failure class:
a success status code over an empty body. Neither the `status_code != 200` guard in the fetcher nor
the `jq empty` check in the workflow distinguishes that from a good run.

## The numbers that constrain the decisions

1. **`data/` is 93.6% of the repository's git history on disk — 29.53 MiB of 31.55 MiB — and grows
   9.50 MiB/month packed (~147 MiB/month uncompressed), from 959 automated commits in 88.5 days
   (94.7% of all commits).** Straight-line, a clone is ~146 MiB in a year and ~259 MiB in two. This
   is the price tag on "where does the data live".

2. **GitHub honours about 45% of the hourly cron: 10.9 runs/day, median gap 112 minutes, worst
   observed gap 28.8 hours.** Any claim of hourly freshness is not what the platform delivers, and
   any accumulation plan must be budgeted at ~11 samples/day, not 24.

3. **Pages is a `legacy` branch build serving `master` at path `/`.** The production artefact and
   the branch receiving ~12 automated data commits a day are the same ref. Every branch model has to
   resolve that collision, and 994 Pages rebuilds in 88.5 days is what it currently costs.

4. **The hard `timeout 600` has been hit 3 times in 974 runs (0.31%), each time losing that hour's
   data entirely; the median run is 115s, so the budget is ~5× the typical need.** The overrun is
   one unbounded stage — remote NLP inference, 560.5s of a 600s budget in the failing run — sitting
   ahead of the 480s soft deadline that is supposed to guard it.

5. **A lint/type/test gate would cover 1,612 lines of Python (21 files, 23 existing tests that CI
   never runs) and 1,319 lines of JS (9 files) with no JS toolchain whatsoever** — no
   `package.json`, no lockfile, 4 CDN origins unversioned at runtime. Python reproducibility today
   rests entirely on `uv.lock` + `uv sync --frozen`, since 9 of 11 dependency declarations are
   open-ended lower bounds.
