# tensionr

> tensionr does not measure the world's tension. It measures the **disagreement between
> those who narrate it**.

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](https://opensource.org/licenses/MIT)

Every few hours the engine takes a window of the world's news, groups articles that are
telling the **same story** across different sources and languages, and measures how
differently those sources name the people and places in it. It publishes the five most
divided stories, the evidence behind each one — every source, and who each one named —
and a statement of what it did *not* see.

## What it is not

There is no tension score. Two independent attempts at aggregating divergence into a
single number both ranked noise first and the visibly divergent story near the bottom,
for a structural reason rather than a tunable one, so the index was removed. What
survives is the per-(story, actor) count, which is checkable row by row.

The unit is the **story**, never the event. A ten-word headline does not distinguish
*"Starmer will resign"* from *"Starmer has resigned"*, and human annotators do not
either. Measured on a hand-built gold set: precision **0.86 at story granularity**,
**0.23 at event granularity**. That is a property of the input, not a tuning problem.

Every figure carries its unit, its procedure, and its uncertainty, or it is not
published.

## Layout

```
backend/     the engine. Python, reads GDELT, writes JSON. Self-contained.
frontend/    the site. Next.js + shadcn/ui, exported as static files.
data/        the contract between them, and published as-is.
docs/adr/    decisions that constrain the code.
docs/research/  what was measured, and how.
tools/       things run by hand.
```

`data/` sits between the two on purpose. The engine writes it, the frontend build reads
it, and readers can fetch it: the footer points at `data/stories.json`, which needs
nothing from this site to be useful.

## Running the engine

From the repository root, so that `data/` resolves — `--project` rather than
`--directory`, because the engine's paths are relative to the root and `--directory`
would move there along with the project:

```bash
uv sync --project backend
uv run --project backend python -m tensionr.stories --out out
```

Three runtime dependencies — `requests`, `numpy`, `python-dotenv`. Set `HF_TOKEN` in
`.env` at the repository root to enable the Hugging Face stages.

Tests:

```bash
cd backend && uv run pytest
```

## Running the site

```bash
tools/serve-site.sh          # build the static export and serve it at :8123
```

This builds the site the way it is actually published, then serves the files. For
writing components, `cd frontend && npm run dev` is faster.

The pipeline's output is not in this repository — it is on the `data` branch, so the
production ref stays protectable. For a page with real stories on it:

```bash
git fetch origin data && git show origin/data:data/stories.json > data/stories.json
```

## How it is published

GitHub Pages, assembled by `.github/scripts/assemble-site.sh` on every deploy:
production at the site root, plus one preview per open pull request under
`preview/<branch>/`. The whole tree is rebuilt from git refs every time — Pages
publishes a single artifact as the entire site, so anything less would take production
down.

Two scheduled workflows and one publishing workflow, none of which run on a pull
request.

---

*MIT. Built by [exdsgift](https://github.com/exdsgift).*
