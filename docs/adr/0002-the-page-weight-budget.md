# ADR 0002 — The page weight budget, and what it is now

Date: 2026-09-05
Status: accepted, superseding the 250 KB figure carried in `ledger.py`
Context: [#79](https://github.com/exdsgift/tensionr/issues/79),
[#82](https://github.com/exdsgift/tensionr/issues/82)

## Context

The Ledger carried a budget of **250 KB gzipped for the whole page**, enforced in code:
`LEDGER_BUDGET_BYTES` in `ledger.py`, measured on `gzip.compress(page, 9)`, with `_fit()`
dropping evidence tables from the narrowest rows until the page fitted and announcing the
cap to the reader.

That figure was set for a page with nothing under it. The Ledger was a single HTML file
with inlined CSS, one inline script, no webfonts and no network requests, so the whole
budget was content.

The site is now a Next.js static export (#79, decision 2). The generator that enforced
the budget was deleted with the rest of the Python frontend, and nothing has enforced it
since.

## What the page actually weighs

**The page's weight is a property of the run, not of the code.** Two consecutive runs,
seven hours apart, measured on real builds:

| | evidence rows | content | total |
| --- | ---: | ---: | ---: |
| `20260905T044830Z` | 499 | 67.3 KB | 313.9 KB |
| `20260905T115847Z` | 1,227 | 147.2 KB | 486.1 KB |

A single story carried 600 rows in the second. **2.5× between two runs of the same
engine, hours apart** — so a budget set from one measurement is a build that fails on a
Tuesday. This was found the way it should be: the budget check failed on its own first
CI run, against data fresher than the local copy it had been calibrated on.

Decomposed, on the lighter of the two — gzip level 9, counting only what a modern
browser fetches for a first load (the `noModule` legacy bundle is excluded because
module-capable browsers never request it):

| | gzip |
| --- | ---: |
| The page: HTML with `<script>` blocks stripped | 59,330 |
| CSS | 9,350 |
| **Content subtotal** | **68,680** |
| Next's inlined RSC flight payload — the same tree, serialised again | 69,041 |
| Next + React runtime | 154,785 |
| Geist Sans (`next/font`, self-hosted) | 29,288 |
| **Framework subtotal** | **253,114** |
| **Total** | **321,794** |

The framework alone exceeds the old budget before a single story is rendered.

Two reductions were taken and one was measured and rejected:

- Geist Mono dropped for the platform monospace stack: **−23 KB**. The braille glyphs come
  from a fallback face on every platform regardless, so the webfont was paying for a face
  the map never used.
- Native `<details>` instead of shadcn's `Accordion`: **−12 KB**, measured on a full build.
  Not taken. It buys 3.7% of the total while giving up the component library the redesign
  exists to adopt — which is also what establishes that the weight is the framework and
  not the components.
- Geist Sans could go too, for a further −29 KB, at the cost of the typography.

## Decision

**520 KB gzipped for a first load, and 160 KB for the content half** — the latter counted
as HTML with `<script>` blocks stripped, plus CSS.

Both are set from the *heavier* observed run with ~8% headroom, not from a single sample.
An earlier draft of this ADR said 340 and 120, taken from the lighter run alone; those two
numbers were also mutually inconsistent, since the RSC payload tracks the content almost
exactly and `total ≈ 2 × content + 181 KB`, which puts a 120 KB content ceiling at a
420 KB total rather than 340. Corrected here rather than quietly adjusted, because the
first version would have failed on ordinary days.

The content half is the one this project controls, and the only one where growth is
somebody's decision.

The framework half is not budgeted, because it is not a variable — it is what Next costs.
Recording it as its own line is the point: a future reader comparing 520 KB against the
old 250 KB should see immediately that the page did not grow by 270 KB, the platform
under it did.

## Consequences

- **`_fit()` is reimplemented**, in `frontend/src/lib/fit.ts`, as a backstop rather than a
  routine mechanism: at 147 KB against 160 the heavier observed run keeps every table, and
  the fitting only fires on a run beyond anything measured. Its rules are the part that
  matters and are tested: figures are never dropped, only the tables behind them; the hero
  keeps its evidence longest, because leading with an unevidenced claim is the one thing
  this page exists not to do; the narrowest rows go first; and the page says how many it
  gave up and where those rows are. Never truncate silently — a page that hides rows
  without saying so is claiming a completeness it does not have.
- The fitting costs a table by gzipping the text it will print rather than by rendering
  it, because `react-dom/server` is not importable from a server component under
  Turbopack. That proxy is calibrated — `content ≈ 26 KB + 2.03 × proxy`, from the two
  runs above — and `check-weight.mjs` measures the built page and is the real gate.
  Recalibrate by re-solving against a build, not by feel.
- Both figures are gzip, not brotli. Pages serves brotli to browsers that ask for it, so
  the real transfer is smaller. Measuring the larger number is deliberate.
- Revisiting the framework choice would move the framework line, not the content line.
  The measurements above are what such a decision should be argued from — an Astro build
  of the same page was measured at 0 B of baseline JavaScript before this one was chosen,
  and Next was taken with that trade-off stated (#79, decision 2).

## What this does not change

The lightness principle from #1 — *"every dependency must justify itself"* — is not
retired, and the engine still honours it: three runtime dependencies, no webfont for the
map, no external requests from the published page. This ADR records what the framework
costs so that the principle has a number to be applied against, not an excuse to stop
applying it.
