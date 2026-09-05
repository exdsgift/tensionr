# ADR 0001 — The visual constraints that outlive the palette

Date: 2026-09-05
Status: accepted
Context: [#79](https://github.com/exdsgift/tensionr/issues/79), superseding the visual system of
[#1](https://github.com/exdsgift/tensionr/issues/1)

## Context

The v2 map decided a visual system — pixel-indie aesthetics, the DawnBringer 16 palette, three
themes — and backed it with a measured study of a reference work
(`docs/research/pixel-indie-aesthetic-for-data.md`) and a measured mobile audit
(`docs/research/mobile-legibility.md`).

On 2026-09-05 the project owner retired that direction and moved the site to shadcn/ui with its
standard palette.

Retiring an aesthetic is cheap. The risk is that the constraints discovered *while* building it
are thrown out with it, because they arrived wearing its clothes. They were not preferences. Each
one below is the result of a measurement, and each is independent of which colours the site uses.

This ADR exists so that a redesign cannot silently undo them.

## Decision

The following hold under any palette, any component library, any framework.

### 1. Contrast applies to chrome, not only to body text

Borders, rules, meter fills, disabled states and decorative frames must meet WCAG's 3:1 for
non-text contrast.

This is stated because it is the failure that was actually observed rather than a generic
reminder. The study measured the reference work's own borders at **2.65:1 and 2.96:1**, and its
meter fills at **1.72:1 and 2.83:1** — while its body text was mostly AAA. The most decorative
element was the least accessible one. All three of tensionr's retired themes shared the same
defect, so this was already a thing to fix rather than a thing to copy.

A component library's defaults do not discharge this. Check the values.

### 2. Colour is never the only encoding

Every state carries a second, non-colour signal: a glyph, a shape, a fill, a word.

The Ledger's marks are the concrete case. `●` present, `○` absent, `–` unresolved, `—` unplaced
polity — each is a character *and* a class, and the character alone is sufficient. The redundancy
is load-bearing: the study measured the reference's four semantic text colours as near-isoluminant
with one another, worst pair **1.20:1**, so colour was doing none of the work it appeared to do.

### 3. The reader's text size gets through

Do not set `font-size` on `body`. Do not disable text size adjustment. `-webkit-text-size-adjust:
100%` stays.

### 4. Wide content scrolls inside its own container, accessibly

The evidence tables are wider than a phone. They must sit in a container with `overflow-x: auto`,
`overscroll-behavior-x: contain`, `tabindex="0"`, `role="region"` and `aria-labelledby` pointing
at the table's caption — the `tabindex` is what makes the scroller reachable by keyboard
(WCAG SC 2.1.1), and without it the content is unreachable without a pointer.

Use fixed table layout with declared column widths. The mobile audit measured what automatic
layout does here: two `white-space: nowrap` columns took **375 of 620 px**, leaving the headline
160, headlines wrapped to five lines, and 26 tables came to **402,792 px of rows**.

### 5. A hidden measuring element must be clipped and reset

The braille map measures the rendered advance of `⠿` at runtime, because no monospace font on any
platform covers the Braille Patterns block and the fallback face's advance is not `1ch` (measured:
**+10.6%** Safari, **+13.5%** Chrome).

The probe that does this must be inside a clipping ancestor and must not be left at its measuring
size. `visibility: hidden` does not remove a box from layout. An earlier version held 100
characters at `font-size: 100px`, `position: absolute`, with every ancestor at `overflow: visible`
— it was **6,835.9 px wide** and made the published homepage scroll sideways by **6,532 px at a
320 px viewport**, identically in WebKit and Chromium. It dwarfed every other layout problem on
the page.

### 6. Motion respects `prefers-reduced-motion`

The map's sonar pulse, and anything like it, is disabled under
`@media (prefers-reduced-motion: reduce)`.

### 7. The page is readable before JavaScript runs

The stories, their evidence tables and the footer are present in the delivered HTML. Scripting may
enhance the page; it may not be the thing that produces it.

This is what makes the site citable, indexable, previewable in a chat client and readable in
reader mode — and it is why the site is pre-rendered at build time rather than assembled in the
browser. It has a specific consequence for component choice: a disclosure widget whose collapsed
content is absent from the exported HTML does not satisfy this, however it is styled.

## Consequences

- A palette swap does not revisit any of the above. A component library that violates one of them
  is configured until it complies, or is not used for that element.
- Constraints 4 and 5 are specific to elements this project actually ships. If the evidence tables
  or the braille map are ever removed, those two lapse with them — the others do not.
- `docs/research/pixel-indie-aesthetic-for-data.md` and `docs/research/mobile-legibility.md` stay
  in the tree. Their aesthetic conclusions are superseded; their measurements are the evidence for
  this ADR and are not superseded by anything.

## What this ADR does not decide

Colours, typography, spacing, component library, or any question of taste. Those now follow
shadcn/ui defaults per #79, and are free to change without touching this file.
