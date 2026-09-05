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

Measured on the first real run rendered by the new frontend — 5 featured stories, 499
evidence rows, gzip level 9, counting only what a modern browser fetches for a first
load (the `noModule` legacy bundle is excluded because module-capable browsers never
request it):

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

**The budget is 340 KB gzipped for a first load, and it is a reader-facing number, not a
content-facing one.**

340 rather than 322 so the ceiling is a ceiling rather than a tripwire: the page's weight
moves with the run, since a window with a 233-source story is heavier than one without.
Roughly 5% of headroom over the measured figure.

**The content half keeps a budget of its own: 120 KB gzipped**, counted as HTML with
`<script>` blocks stripped, plus CSS. That is the half this project controls, it is 68,680
today, and it is the number that says whether the page is getting fatter for reasons that
are anybody's fault.

The framework half is not budgeted, because it is not a variable — it is what Next costs.
Recording it as its own line is the point: a future reader comparing 340 KB against the
old 250 KB should see immediately that the page did not grow by 90 KB, the platform under
it did.

## Consequences

- The old `_fit()` behaviour — dropping evidence tables under pressure and saying so — is
  **not** reimplemented. It existed to keep a hard cap that a static HTML file could
  actually hit; at 68,680 against 120,000 the content half has room, and dropping evidence
  is the most expensive thing this page can give up, since the evidence is what makes the
  figures checkable.
- If the content half is ever exceeded, drop evidence tables from the narrowest rows
  first and announce the cap on the page, as `ledger.py` did. Do not silently truncate;
  a page that hides rows without saying so is claiming a completeness it does not have.
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
