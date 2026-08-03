# The Ledger on a phone: braille at small sizes, wide tables, and how to scale text

Research for [issue #51](https://github.com/exdsgift/tensionr/issues/51), against the Ledger as it
was published at `b45b57b`.
Date: 2026-08-04.

Everything in §1–§4 was measured. Claims are marked **[measured]** when they come from a number this
document can reproduce, **[cited]** when they come from a specification, a browser source tree or a
bug tracker, and **[derived]** when they are arithmetic over measured inputs. Where a claim rests on
a platform this document could not run, it says so and is marked **[derived]**.

**Measurement conditions.**

| | |
| --- | --- |
| Host | macOS, Darwin 24.6.0, x86_64 |
| Engines | Playwright WebKit and Chrome Headless Shell 151.0.7922.34, `device_scale_factor: 3`, viewport height 844 |
| Page under test | rendered by `uv run python -m tensionr.ledger` from `origin/data:data/stories.json` at `137ead0` — 26 banded stories, 2,700 source rows, 177 KB gzipped |
| Font binaries | `fontTools` 4.63.0 over all of `/System/Library/Fonts{,/Supplemental}`, plus Noto Sans Symbols 2 v2.008 and DejaVu 2.37 downloaded from their releases |
| Widths exercised | 320, 390, 430, 620, 621, 1200 CSS px |

---

## 0. Bottom line

Five findings, and the first two are not what the ticket expected.

1. **The published homepage scrolled sideways by 6,532 px at a 320 px viewport**, and by 6,462 and
   6,422 px at 390 and 430 — identically in WebKit and Chromium (§1.1). The cause is the measuring
   probe: `#probe` holds 100 braille characters at `font-size: 100px`, is `position: absolute` with
   no clipping ancestor, and was left at that size after measuring. `visibility: hidden` does not
   remove a box from layout. It is 6,835.9 px wide and every ancestor up to the viewport had
   `overflow: visible`. This is one line of CSS, and it dwarfed everything else on the page.

2. **The map was never being resized on a phone at all.** The ticket predicted the 4 px floor in
   `Math.max(4, …)` being reached. The opposite happened: `.hook { grid-template-columns: 1fr }`
   means `minmax(auto, 1fr)`, whose automatic minimum is content-based, and the map is a `<pre>` at
   `width: max-content`. So the track took the block's 571 px max-content size, `.earth.clientWidth`
   was **571 px at a 320 px viewport**, and `fit()` returned 10.99 px — its 11 px ceiling — at every
   phone width (§1.2). The floor is unreachable: it needs a 208 px box, i.e. a 240 px viewport.

3. **The evidence tables were already contained.** The ticket flagged them as the widest thing on
   the page and asked for verification; they never reached the document. The widest measured 740.8 px
   inside a 272 px scrollport, clipped by `.ev-scroll`'s `overflow-x: auto` (§1.3, §3.2). What was
   wrong with them is different and was not in the ticket: automatic table layout gave the two
   `white-space: nowrap` columns 375 of 620 px and left the headline 160, so headlines wrapped to
   five lines and the 26 tables came to **402,792 px of rows** (§3.3).

4. **No monospace font on any platform covers the Braille Patterns block**, so the glyphs always
   come from a fallback whose advance is not `1ch`: **+10.6%** in Safari, **+13.5%** in Chrome on
   macOS, **+16.7%** on Android (§2.1, §2.2). Measuring a probe rather than using `ch` was correct.
   The advance is, however, **perfectly uniform across all 256 code points** in every font that
   covers the block, so the `<pre>` grid does not break internally — only its scale was wrong.

5. **A 76-column map cannot be legible at 320–430 CSS px, and 38 columns can.** 76 characters need
   52 times the font size in pixels, so a 358 px column buys 6.89 px type and **0.83 CSS px of ink
   per dot** — 1.67 device pixels on the 2× displays that iPhone SE and iPhone 11 still ship. 38
   columns in the same box run at 13.78 px, 1.67 CSS px of ink, 3.34 device pixels (§2.4, §2.5). And
   halving the grid costs nothing where it matters: the coastal-capital check that guards the
   projection scores **32 of 34 on both maps** (§2.6).

One thing the ticket did not ask about turned out to matter more than any of these: a font size
computed by measuring a probe against a viewport-derived box is **zoom-resistant in exactly the way
`vw` is**, which is the live objection to the CSS WG's own `text-fit` proposal. Measured, it does not
bite here — the dot ink grows ×2.0 at 200% zoom and ×4.0 at 400%, because the 11 px and 14 px
ceilings mean the measured size is not what governs over most of the range, and because zooming past
250% crosses the breakpoint into the narrow map (§4.1). **Those ceilings are load-bearing.** Remove
them and the map stops responding to zoom.

Two things this document could not settle: no measurement was taken on a real iOS or Android device
(§5, item 1), and no public bug report of braille art failing on a mobile browser exists to
corroborate the geometry (§5, item 4).

---

## 1. What the published page actually did at 320, 390 and 430 CSS px

Measured by loading the rendered page in both engines and reading `document.documentElement`,
`getBoundingClientRect()` on every element, and the nearest ancestor of each overflowing element
whose computed `overflow-x` was not `visible`.

### 1.1 The document scrolled sideways, everywhere, by about 6,500 px

**[measured]**

| Engine | Viewport | `scrollWidth` | `clientWidth` | Overflow | Widest element | Its width | Nearest clipping ancestor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WebKit | 320 | 6,852 | 320 | **6,532** | `pre#probe` | 6,835.9 | none |
| WebKit | 390 | 6,852 | 390 | **6,462** | `pre#probe` | 6,835.9 | none |
| WebKit | 430 | 6,852 | 430 | **6,422** | `pre#probe` | 6,835.9 | none |
| Chromium | 320 | 6,852 | 320 | **6,532** | `pre#probe` | 6,835.9 | none |
| Chromium | 390 | 6,852 | 390 | **6,462** | `pre#probe` | 6,835.9 | none |
| Chromium | 430 | 6,852 | 430 | **6,422** | `pre#probe` | 6,835.9 | none |

`6,835.9 = 100 characters × 0.68359 em × 100 px`, which is the probe exactly. Removing it from
layout dropped `scrollWidth` to 731 (WebKit) and 728 (Chromium) — the residue is the map block,
§1.2. Both numbers are still over the viewport, so the page had **two** independent causes of
horizontal scroll and the probe hid the other one.

Worth stating plainly because it generalises: an absolutely positioned box contributes to the
scrollable overflow region of its containing block's scroll container, and `visibility: hidden`
leaves it in layout. CSS Overflow 3 defines the scrollable overflow region over "the box's own
content and padding areas … and the scrollable overflow regions of all of [its] descendant boxes"
without excluding hidden or absolutely positioned ones —
<https://drafts.csswg.org/css-overflow-3/#scrollable> **[cited]**. `content-visibility` and
`contain: size` do not help: `contain: size` sizes the box as empty but does not clip, and the page
still measured 6,852 with it applied **[measured]**.

### 1.2 The map track never narrowed, so `fit()` was fed a constant

**[measured]** With the probe removed from layout, `.earth.clientWidth` and the resulting font size:

| Viewport | `.earth` box | `<pre>` block | `fit()` result | 76-column natural size for that box |
| --- | --- | --- | --- | --- |
| 320 | **571** | 571.0 | 10.99 px | 5.54 px |
| 390 | **571** | 571.0 | 10.99 px | 6.89 px |
| 430 | **571** | 571.0 | 10.99 px | 7.66 px |
| 1200 | 704 | 571.0 | 10.99 px | 13.55 px |

Forcing `.hook { grid-template-columns: minmax(0, 1fr) }` dropped the box to 288 px at a 320 px
viewport **[measured]**, confirming the track was the cause.

The mechanism is normative in two places. CSS Grid 1 §7.2.1: "`<flex>` … When appearing outside a
`minmax()` notation, implies an automatic minimum (i.e. `minmax(auto, <flex>)`)", and `auto` "as a
minimum: represents the largest minimum size … of the grid items occupying the grid track" —
<https://drafts.csswg.org/css-grid-1/#track-sizes>. CSS Grid 1 §6.6 then makes the item's automatic
minimum content-based unless "its computed `overflow` is not a scrollable overflow value" fails —
<https://drafts.csswg.org/css-grid-1/#min-size-auto> **[cited]**. The `--cols` definition in `:root`
already used `minmax(0, 1fr)` correctly; the `@media (max-width: 980px)` override on `.hook` did
not.

Two consequences of that one keyword: the map stuck out of the viewport, **and** the whole `.hook`
grid — including the paragraph beside the map — was laid out at 571 px inside a 390 px viewport,
which is why the lede text was clipped mid-word in the before screenshots.

### 1.3 Where the horizontal overflow was, and was not

**[measured]** Every element whose right edge exceeded the viewport, at 320 CSS px, with the
ancestor that clipped it:

| Element | Width | Clipped by |
| --- | --- | --- |
| `pre#probe` | 6,835.9 | **nothing** |
| `pre#globe` | 571.0 | **nothing** |
| `table.src` (widest) | 740.8 (WebKit) / 724.1 (Chromium) | `div.ev-scroll` `[auto]` |
| `thead`, `tr`, `th`, `tbody`, `td.hl` inside it | up to 740.8 | `div.ev-scroll` `[auto]` |

So the tables were fine and the map was not, which is the reverse of the ticket's expectation. The
`.ev-scroll` wrapper is also the pattern W3C illustrates as a **Pass** for SC 1.4.10 Reflow —
"An element that contains a table with a minimum height, width or both, can be styled to provide
bidirectional scrollbars allowing a user to scroll the table's content and mitigating bidirectional
scrollbars appearing at the page level" —
<https://www.w3.org/WAI/WCAG22/Understanding/reflow.html> **[cited]**.

### 1.4 Column heads and row cells

**[measured]** `getComputedStyle().gridTemplateColumns` and the left edge of each child, for
`.colhead` and the first `.row .grid`:

| Viewport | `.colhead` tracks | `.row .grid` tracks | Head lefts | Row lefts |
| --- | --- | --- | --- | --- |
| 1200 | `584px 96px 120px 304px` | `584px 96px 120px 304px` | 24, 624, 736, 872 | 24, 624, 736, 872 |
| 430 | `1fr` (flex) | `398px` | 16, 101.7, 202.2, 310.1 | 16, 16, 16, 16 |
| 320 | `1fr` (flex) | `288px` | 16, 101.7, 202.2, **16** | 16, 16, 16, 16 |

Above the 760 px breakpoint the two grids resolve to identical track lists, because both read one
`--cols`, and the heads sit exactly over their cells. Below it there is one track and there are no
columns to align with: each row cell carries its own label through `.cell::before { content:
attr(data-l) }`. The defect at 320 is narrower than "they do not line up": the fourth head wraps
onto a second line under the first, so a strip that still reads as four column headings is laid out
as a broken two-row table over cells that are stacked. The fix is presentational — make the strip
read as the list of definitions it has become.

---

## 2. Braille at small sizes

### 2.1 No monospace font covers U+2800–U+28FF

**[measured]** `fontTools` over 580 font files in the four macOS font directories, checking the best
`cmap` for each of the 256 code points and reading `hmtx`:

| Face | upem | Braille coverage | Braille advance | Advance of `0` |
| --- | --- | --- | --- | --- |
| Apple Symbols | 2048 | **256/256** | 1400 = **0.68359 em** | 969 = 0.47314 em |
| Apple Braille | 2048 | **256/256** | 1400 = **0.68359 em** | — |
| Apple Braille Outline / Pinpoint, 6 and 8 Dot | 2048 | 256/256 | 1400 = 0.68359 em | — |
| Menlo — all four faces | 2048 | **0/256** | — | 1233 = 0.60205 em |
| `.SF NS Mono` (`SFNSMono.ttf`) | 2048 | **0/256** | — | — |
| DejaVu Sans Mono 2.37 | 2048 | **0/256** | — | — |
| DejaVu Sans 2.37 | 2048 | 256/256 | 1500 = 0.73242 em | 1303 = 0.63623 em |
| Noto Sans Symbols 2 v2.008 | 1000 | 256/256 | 700 = **0.70000 em** | 1102 |

Nothing else in the 1,004 faces read carries the block. Independent corroboration for Android: the
face that serves braille there is `NotoSansSymbols-Regular-Subsetted.ttf`, whose braille advance is
1434/2048 = **0.70020 em**, and the block is listed in AOSP's own subsetting script at
`2800..28FF; Braille Patterns` —
<https://android.googlesource.com/platform/external/noto-fonts/+/refs/heads/main/scripts/subset_noto_sans_symbols.py>
**[cited]**. It is placed before the CJK families in the fallback list on purpose —
<https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/data/fonts/fallback_order.json>
**[cited]**.

**Which font the browser actually used.** Chromium's `CSS.getPlatformFontsForNode` over the rendered
`<pre>` reports `Apple Braille`, `glyphCount: 1672` for the 76 × 22 map and `418` for the 38 × 11
one — exactly the character counts, so every glyph came from that one face **[measured]**. Apple
Braille and Apple Symbols have identical braille metrics, which matters because Apple's system-font
table lists Apple Symbols as a system font on iOS and Apple Braille as *downloadable* only —
<https://developer.apple.com/fonts/system-fonts/> **[cited]**. So iOS almost certainly resolves to
Apple Symbols instead, at the same 0.68359 em **[derived]** — see §5.1.

### 2.2 The advance is not `1ch`, and by how much

**[measured]** in-page, with a hidden span at `font-size: 100px` carrying the same `font-family` as
`body`:

| Engine | Braille advance | `1ch` (advance of `0`) | Ratio |
| --- | --- | --- | --- |
| WebKit | 0.68359 em | 0.61816 em | **1.1058** |
| Chromium | 0.68359 em | 0.60205 em (Menlo) | **1.1354** |
| Android Chrome | 0.70020 em | 0.60010 em (DroidSansMono) | **1.1668** [derived] |

`U+2800` (blank) measured the same advance as `U+28FF` in both engines, so the block is uniform in
layout as well as in `hmtx` **[measured]**.

**[derived]** What sizing 76 columns as `76ch` would have produced:

| Engine | Viewport | Font size from `76ch` | Real block width | Box | Overshoot |
| --- | --- | --- | --- | --- | --- |
| WebKit | 390 | 7.62 px | 395.9 px | 358 | +37.9 px |
| Chromium | 390 | 7.82 px | 406.5 px | 358 | +48.5 px |
| Android Chrome | 390 | 7.85 px | 417.7 px | 358 | +59.7 px |

A correction to the premise the code comment states. `ch` is **not** resolved from the first
available font; CSS Values 4 defines it as "the used advance measure of the '0' … glyph **in the
font used to render it**", and the "first available font" wording was removed from CSS Fonts 4 as
incorrect — <https://drafts.csswg.org/css-values-4/#ch>, and PR
[csswg-drafts#3129](https://github.com/w3c/csswg-drafts/pull/3129), "[css-fonts-4] Stop claiming
that 'ch' uses the first available font, since it doesn't", merged **[cited]**. In practice all
three engines resolve it from the *primary* font and never consult the fallback that draws the
braille, which is conforming. The conclusion — measure a probe — is unchanged; the reason is that
`ch` describes a different font, not that it describes the fallback badly.

### 2.3 Dot geometry, measured from the outlines

**[measured]** glyph bounding boxes via `fontTools`' `BoundsPen`. Dot diameter from `U+2801`
(one dot), vertical pitch from the `ymin` difference between `U+2801` and `U+2803` (dots 1 and 1+2),
horizontal pitch from the `xmax` difference between `U+2801` and `U+2809` (dots 1 and 1+4):

| Font | Advance | Dot diameter | Horizontal pitch | Vertical pitch |
| --- | --- | --- | --- | --- |
| Apple Braille / Apple Symbols | 0.68359 em | **0.12109 em** | 0.23633 em | 0.23975 em |
| Noto Sans Symbols 2 | 0.70000 em | 0.12900 em | 0.26700 em | 0.25000 em |
| DejaVu Sans | 0.73242 em | 0.14648 em | 0.29297 em | 0.27686 em |

Two structural facts fall out, and both are properties of the block rather than of this page.

**There is always a horizontal gap between character cells.** Two dot columns span `2 × pitch`,
which is less than the advance:

| Font | `2 ×` pitch | Advance | Gap | As a share of the advance |
| --- | --- | --- | --- | --- |
| Apple Braille / Symbols | 0.47266 em | 0.68359 em | 0.21094 em | **30.9%** |
| Noto Sans Symbols 2 | 0.53400 em | 0.70000 em | 0.16600 em | 23.7% |
| DejaVu Sans | 0.58594 em | 0.73242 em | 0.14648 em | 20.0% |

So the dot lattice is not uniform horizontally and cannot be made so without negative
`letter-spacing` tuned per font. Nothing in this change attempts that.

**The line height that makes the lattice uniform vertically is `4 × pitch`, and it differs per
platform.** **[derived]** The published `line-height: 1.15em` against the gap it leaves between the
fourth dot row of one line and the first of the next:

| Font | Seamless line-height | Cross-row gap at `1.15em` | Ratio to within-glyph pitch | At `1.0em` | Ratio |
| --- | --- | --- | --- | --- | --- |
| Apple Braille / Symbols | 0.9590 em | 0.4308 em | **1.80×** | 0.2808 em | **1.17×** |
| Noto Sans Symbols 2 | 1.0000 em | 0.4000 em | 1.60× | 0.2500 em | **1.00×** |
| DejaVu Sans | 1.1074 em | 0.3194 em | 1.15× | 0.1694 em | 0.61× |

At `1.15em` the vertical dot spacing jumps by 80% at each of the 21 line boundaries on iOS and
macOS, which is why the published map reads as horizontal bands. `1.0em` is exact for Android,
4.3% loose for Apple, and 39% tight for DejaVu — no single value tiles on all three, so `1.0em` is
the best available compromise and is what this change adopts. It also brings the map closer to a
true equirectangular: with 2.368° of longitude per dot over 0.34180 em and 1.477° of latitude per
dot over `line-height/4`, the vertical exaggeration falls from **1.35× to 1.17×** **[derived]**.

### 2.4 Where the dots stop being separable

Two independent estimates, which agree on the order of magnitude and not on the criterion. Both are
stated because neither is authoritative — **there is no standard for a minimum legible dot size on a
screen**, braille-specific or otherwise (§5.3).

**Estimate A — ink per dot [derived].** At font size `F`, one dot carries `0.12109 F` CSS px of ink
in Apple Braille, and `0.11523 F` px of background separates it from its neighbour. For the ink to
survive greyscale antialiasing at all it needs to be at least one device pixel, and to read as a
dot rather than a smudge, two.

**Estimate B — glyph rasterisation [measured, by a separate pass; FreeType greyscale].** Requiring
five ink pixels across the two dot columns and eleven down the four rows puts the floor at **12–13
device pixels of font size**: Apple Symbols 12, Apple Braille 13, AOSP Noto Symbols 12, Cascadia
Mono 13. That pass also found the result **non-monotonic** in size — Apple Braille separated at 10
and 14 device px but not at 12 — because separation depends on the subpixel phase and the hinting,
so it is not a clean threshold. Treat 12–13 as an order of magnitude.

**[derived]** Both estimates against the sizes the two maps actually run at, on Apple Braille:

| Map | Viewport | Box | Font size | Dot ink, CSS px | Device px at DPR 2 | at DPR 3 | Font size in device px, DPR 2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 76 × 22 | 320 | 288 | 5.54 | 0.67 | **1.34** | 2.01 | **11.1** — below estimate B |
| 76 × 22 | 390 | 358 | 6.89 | 0.83 | **1.67** | 2.50 | 13.8 — marginal |
| 76 × 22 | 430 | 398 | 7.66 | 0.93 | 1.86 | 2.78 | 15.3 |
| 38 × 11 | 320 | 288 | 11.09 | 1.34 | 2.69 | 4.03 | 22.2 |
| 38 × 11 | 390 | 358 | 13.78 | 1.67 | 3.34 | 5.01 | 27.6 |
| 38 × 11 | 430 | 398 | 14.00 (cap) | 1.70 | 3.39 | 5.09 | 28.0 |
| 76 × 22 | 1200 | 704 | 11.00 (cap) | 1.33 | 2.66 | 4.00 | 22.0 |

The DPR-2 column is the one that decides it. iPhone SE (2nd and 3rd generation) is 375 × 667 at
2×, and iPhone 11 and XR are 414 × 896 at 2× — these are not edge cases. On them the 76-column map
gives each dot 1.3–1.7 device pixels; the 38-column map gives 2.7–3.4.

**And the ink is faint to begin with.** The published coastline is `--slate` `#4e4a4e` on `--ink`
`#140c1c`, which is **2.20:1** by the WCAG 2 relative-luminance formula **[derived]** — below the
3:1 that SC 1.4.11 Non-text Contrast asks of graphical objects needed to understand content,
<https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html> **[cited]**. A 1.3-device-pixel
mark at 2.20:1 is not a thin line, it is nothing. `--grey` `#757161` on the same background is
**3.90:1**, which clears it, and is already in the palette. Whether the coastline counts as
"required to understand the content" is arguable — the markers carry the measurement — but a map
nobody can see is not decorative either.

**Text inflation is not a factor, on either platform.** Chromium's text autosizer was disabled by
default in Chrome 143 and deleted in 149; before that it suppressed autosizing for any block whose
line does not wrap, which `<pre>` does not — `BlockSuppressesAutosizing`, "Don't autosize
block-level text that can't wrap" **[cited]**. Blink's `minimumFontSize` and
`minimumLogicalFontSize` both initialise to 0, and Chromium explicitly allows a smaller explicit
pixel size: "we always allow the page to set an explicit pixel size that is smaller, since sites
will mis-render otherwise" — so `font-size: 4px` stays 4px on Android **[cited]**. WebKit's
autosizer *is* live on iOS and does **not** exempt `<pre>` or monospace, but returns the specified
size unchanged when `pageScale >= 1` — `AutosizeStatus::idempotentTextSize`, `if (pageScale >= 1)
return specifiedSize;` — which the page's `initial-scale=1` guarantees **[cited]**. Keeping that
viewport meta is therefore load-bearing, not boilerplate.

### 2.5 So: is a 76-column map right at 380 CSS pixels?

No, and the arithmetic is not close. **[derived]** 76 columns occupy `76 × 0.68359 = 51.95` em, so
reaching the 11 px the desktop uses needs a **571 px** block — 603 px of viewport once the page's
own padding is counted, which is wider than any phone. Every width in the ticket forces the map to
5.5–7.7 px, where a dot is under one CSS pixel of ink at 2.20:1 contrast. There is no CSS that
fixes this, because the constraint is the number of characters.

**38 × 11 is the size chosen**, on five measured grounds:

1. It is **exactly half the shipped map on both axes**, at the same crop, so the two are one
   projection at two resolutions rather than two different worlds — and every marker's column and
   row is exactly half its counterpart, which a test asserts.
2. It fills a phone column at a legible size: 11.09 px at 320, 13.78 px at 390, capped at 14 at 430.
3. **It loses nothing on the check that guards the projection** (§2.6).
4. It costs 1.8 KB raw and ~0.3 KB gzipped. Page weight went from 172 to 177 KB gzipped against the
   250 KB budget, and most of that is the table `scope` and caption attributes, not the map.
5. Wider candidates were measured and rejected: 40 × 14 drops the coastal-capital score to 30 of 34,
   and 44 × 13 and 48 × 14 keep the score but run at 9.57 and 8.78 px at a 320 px viewport, giving
   2.3 and 2.1 device pixels of ink at DPR 2 against 2.7 for 38 columns.

**[measured]** Candidates, all rasterised from the same Natural Earth source at the same crop:

| Grid | Dots | Coastal capitals hit | Ink cells | Raw bytes | Font size at a 288 px box | at 358 |
| --- | --- | --- | --- | --- | --- | --- |
| 76 × 22 (shipped) | 152 × 88 | **32/34** | 415 | 5,552 | 5.54 | 6.89 |
| **38 × 11 (chosen)** | 76 × 44 | **32/34** | 157 | 1,413 | **11.09** | **13.78** |
| 40 × 14 | 80 × 56 | 30/34 | 188 | 1,851 | 10.53 | 13.09 |
| 44 × 13 | 88 × 52 | 32/34 | 194 | 1,883 | 9.57 | 11.90 |
| 48 × 14 | 96 × 56 | 31/34 | 227 | 2,187 | 8.78 | 10.91 |
| 52 × 15 | 104 × 60 | 32/34 | 257 | 2,515 | 8.10 | 10.07 |

The switch belongs in a media query rather than in the script, because the page has to be readable
with scripting off. It sits at **620 px**, which is where the wide map stops being able to reach its
own 11 px ceiling — so the wide map is only ever shown at the size it was designed for, and the
narrow one covers everything below **[derived, verified at 620 and 621 — §4]**.

### 2.6 The narrow map is a weaker guard against a projection error, and that is worth writing down

**[measured]** The check that caught #41 asks how many of 34 coastal capitals land on a cell that
carries ink. Run against the correct crop and against the prototype's wrong 82N/58S crop:

| Grid | Correct crop | Prototype's crop |
| --- | --- | --- |
| 76 × 22 | 32/34 | **25/34** |
| 38 × 11 | 32/34 | **30/34** |

At half the resolution each cell covers four times the area, so it swallows the displacement. The
narrow map is worth checking — a mismatch would still show — but it cannot be the guard. The
negative control therefore stays on the full-resolution map, and `tests/test_map_data.py` now
asserts this asymmetry explicitly so that nobody deletes the wide check as redundant.

### 2.7 Reproducing the coastline, and what that licenses

`data/map/coastline.json` referenced a rasteriser on a prototype branch. The version there rasterises
a *filled* map at an 82N/58S crop, which is neither the crop nor the drawing the shipped file
contains, so the shipped map could not be regenerated from anything in the repository.

`tools/build_map.py` now reproduces it **bit for bit**: all 1,672 cells identical, from
`ne_110m_land.geojson` at `nvkelso/natural-earth-vector@master`
(<https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson>,
138,160 bytes) **[measured]**. Getting there pinned down three choices the file's comment does not
record:

- Sample at **dot centres**, `(index + 0.5)`, not at dot corners.
- **Four-connected** edge trace: keep a land dot that has a non-land dot directly above, below, left
  or right. Eight-connected agrees on only 85.3% of cells; the filled map agrees on 68.1%.
- Test rings until one **contains** the sample, rather than accumulating crossings across all of
  them. Even-odd parity across rings — which would carve out lakes — moves 245 of the 1,672 cells.
  Natural Earth's land layer has no lake rings, so "first containing ring wins" is the correct read.

Because the tool reproduces the shipped artefact exactly, the narrow map it emits is trustworthy in
the same way. Both files carry their own projection fields and neither is restated in code.

---

## 3. Wide data tables at 320–430 CSS px, without a framework

### 3.1 What was considered, and what each costs

| Approach | Keeps row/column alignment | Cost |
| --- | --- | --- |
| **Horizontal scroll container** | Yes | Needs `tabindex`/role/name to be keyboard-operable; verbose for screen readers; the scrollbar affordance is hidden on touch |
| Stacked cards (`display:block` + `::before{content:attr(…)}`) | No | Deletes the header row from the accessibility tree; re-invents labels as unselectable generated content; ~4× the vertical length |
| Sticky first column | Yes | Surrenders a large share of a 288 px scrollport permanently; collapsed borders on sticky cells scroll away in every engine |
| `table-layout: fixed` + wrapping | Yes | Column widths must be declared; content can no longer negotiate |
| Hiding low-priority columns | Yes, for what is left | Removes data from the accessibility tree as a normative MUST NOT, with no scriptless way to reveal it |

The scroll container is the one to keep. It is the pattern W3C illustrates as a Reflow **Pass**
(§1.3), and the practitioner who built and user-tested both reports the scrolling version "performs
better for all users" than the reflowed one — Adrian Roselli, *Under-Engineered Responsive Tables*,
<https://adrianroselli.com/2020/11/under-engineered-responsive-tables.html> **[cited]**.

The stacked pattern's old objection — that changing `display` on table elements dropped the table
semantics — is **no longer true**: Chrome 80 (with a regression in 113 fixed in 115), Firefox 113 for
`<th>` under flex/grid, and Safari 17 —
<https://adrianroselli.com/2018/02/tables-css-display-properties-and-aria.html> **[cited]**. It
fails on the other two grounds instead: the recipe hides the header row, and ARIA §7.1 makes that
irreversible — "user agents **MUST NOT** include them in the accessibility tree: elements … that
have host language semantics specifying that the element is not displayed, such as CSS
`display:none`" — <https://www.w3.org/TR/wai-aria-1.2/#tree_exclusion> **[cited]**. And with three
mark columns whose entire meaning is positional, stacking turns each glyph into a `Label: ●` line.

Hiding columns is out for the same reason plus one more: SC 1.4.10's permission to rearrange is
conditional — "so long as users are still able to access the content" — and its only sanctioned
pattern for space-constrained content is a reveal mechanism, which a page that must work with
scripting off cannot offer for a table column **[cited]**.

### 3.2 What the scroller needed

`tabindex="0"`, a role and a name. The keyboard requirement is SC 2.1.1 —
<https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html> — and it is not obsolete. Firefox has
made scroll containers tab stops since Firefox 4; Chrome landed it in **132** (January 2025) after
five roll-backs; **Safari has not shipped it** — WebKit bug 277290 is still `NEW`, and PR
[WebKit#66624](https://github.com/WebKit/WebKit/pull/66624) is a draft
(<https://bugs.webkit.org/show_bug.cgi?id=277290>) **[cited]**. axe-core acknowledged the narrowing
by renaming its rule to "…accessible by keyboard **in Safari**"
([dequelabs/axe-core#4995](https://github.com/dequelabs/axe-core/pull/4995)) **[cited]**.

And Chrome's automatic focusability "only happens if the scroller has no focusable children" —
<https://developer.chrome.com/blog/keyboard-focusable-scrollers> **[cited]** — so the moment a
`Source` cell becomes a link, the attribute is required in Chrome too. It is cheaper to write it than
to remember the exception.

The name points at the table's own `<caption>` via `aria-labelledby` rather than restating the string
in `aria-label`, so the scroller and the table it holds announce one name. The caption is clipped
rather than `display:none`, both because a hidden caption still names the table and because a
caption's min-content contributes to the table's used minimum width (CAPMIN) unless it is out of
flow — CSS Tables 3 §3.9.1, "The used min-width of a table is the greater of the resolved
`min-width`, CAPMIN, and GRIDMIN" — <https://drafts.csswg.org/css-tables-3/#computing-the-table-width>
**[cited]**. Measured: the caption's box is 1 px wide and the table's width did not move
**[measured]**.

`overscroll-behavior-x: contain` stops a swipe that reaches the table's edge from becoming a browser
back-navigation. Safari 16+, everything else long since — <https://caniuse.com/css-overscroll-behavior>
**[cited]**.

The affordance is the Verou/Chen Hui Jing `background-attachment: local` pair: a `local` cover that
scrolls with the content over a fixed shadow, so a shadow appears exactly when there is more table
in that direction. Necessary because "scrollbars are often hidden by default on mobile devices …
so the visual affordance that the user needs to scroll is often gone" **[cited]**, and NN/g agrees
that "arrows or cut-off elements convey this information best" —
<https://www.nngroup.com/articles/mobile-tables/> **[cited]**. The shadow had to be drawn in a
*light* colour: `#000000` at 45% over a `#140c1c` background is invisible.

### 3.3 The change that mattered most was `table-layout: fixed`

**[measured]** at a 320 px viewport, across all 26 tables on the page:

| | Automatic layout | Fixed layout, widths on the header row |
| --- | --- | --- |
| Table width, 1 mark column | 620 px | 620 px |
| Table width, 2 mark columns | 678.8 px | **620 px** |
| Columns, 1 mark column | 216.9 / 158.4 / 85 / **159.7** | 144 / 104 / 80 / **292** |
| Median row height | 84.5 px | **47.9 px** |
| Median row height, 2 mark columns | 194.5 px | **66.2 px** |
| Total height of all 26 table bodies | **402,792 px** | **206,938 px** |
| Cells whose content overflowed their column | 0 | 0 |

Automatic layout distributes a table's surplus width in proportion to each column's own content, so
the two `white-space: nowrap` columns took 375 of 620 px for content that needs a third of that, and
the headline — the only column with something long in it — got 160. Fixed layout hands it the
remainder. That is **49% less to scroll vertically** and, for the three-mark tables, 9% less
horizontally, at no cost in overflow. CSS 2.2 §17.5.2.1 is the normative statement: "the horizontal
layout of the table does not depend on the contents of the cells" —
<https://www.w3.org/TR/CSS22/tables.html#fixed-table-layout> **[cited]**.

Fixed columns cannot be widened by their content, so everything that used to hold a column open has
to be allowed to wrap. `overflow-wrap: anywhere`, not `break-word`: CSS Text 3 is explicit that
"soft wrap opportunities introduced by `anywhere` are considered when calculating min-content
intrinsic sizes", and that those introduced by `break-word` are **not** —
<https://drafts.csswg.org/css-text-3/#overflow-wrap-property> **[cited]**. Nothing is clipped or
ellipsised: a domain is which publisher said it, and an ellipsis there deletes the evidence.

Sticky moved from each `<th>` to the `<thead>`, which every engine has supported since Chrome 91
(TablesNG, <https://developer.chrome.com/blog/tablesng>) and Safari 14, and which avoids Safari
leaving a caption-sized gap above the header row **[cited]**. Its hairline became an inset
`box-shadow`, because a collapsed border on a sticky cell scrolls away in every engine —
Bugzilla [1727594](https://bugzilla.mozilla.org/show_bug.cgi?id=1727594), where a Mozilla developer
notes "all browsers behave the same on the testcase" **[cited]**.

`hyphens: auto` was considered and dropped. It ships no dictionary for Arabic, Hebrew, Chinese,
Japanese or Korean in any engine, and unprefixed `hyphens` only arrived in Safari 17 — MDN
browser-compat-data **[cited]**. For the RTL headlines this page carries it would do nothing;
`dir="auto"` on the cell, which the generator already writes, is the mechanism that matters.

**One recommendation deliberately not taken.** `max-height: 26rem` with `overflow-y: auto` nests a
vertical scroller inside a vertically scrolling page, and both Roselli and Sheri Byrne-Haber argue
against exactly that nesting for magnification, switch and screen-reader users
(<https://sheribyrnehaber.com/nested-scroll-bars-are-the-one-of-the-biggest-accessibility-evils-ever/>)
**[cited]**. Dropping it below ~640 px would leave a single-axis scroller. But it is also what makes
the sticky header stick within a screen, which NN/g calls out as the thing that "help[s] users know
what they are looking at" on a table taller than one screen. That is a design trade-off with sourced
arguments both ways rather than a defect, so it is recorded here and left to the owner.

---

## 4. Viewport units, container queries, or `clamp()`

The question is what should set the size of text that has to work from 320 to 1200+ px, and what each
answer costs a user who zooms or who has raised their OS or browser text size. Anything that defeats
either is unacceptable.

### 4.1 The map: the unit has to be the braille advance, which no CSS unit expresses

§2.2 shows `ch` is out by 10.6–16.7%, and by a *platform-dependent* amount, so no constant factor
rescues it. `em` and `rem` describe the primary font, not the fallback that draws the braille. `vw`,
`cqi` and `cqw` describe the box — the numerator, not the denominator. The quantity needed is "the
advance of `⠿` in whichever face this browser chose", and the only way to get it is to render one and
measure it. The CSS WG has declined to add a way to constrain a glyph's advance for twelve years —
John Daggett, 2014: "Rather than using new CSS features to solve your problem, I think the simplest
and best approach here is simply to use a font that's designed for the set of characters you intend
to use" (<https://lists.w3.org/Archives/Public/www-style/2014Oct/0354.html>) **[cited]**. The
alternative to measuring is shipping a webfont, and #14 forbids the request.

**But a size measured that way is, in principle, zoom-resistant in exactly the way `vw` is**, and
this needs stating because it is the one accessibility trap in the design. Page zoom shrinks the
viewport *measured in CSS pixels* while making each CSS pixel render larger — CSSOM View 1: "page
zoom which affects the size of the initial viewport", against "the visual viewport scale factor which
acts like a magnifying glass and does not affect the initial viewport"
(<https://drafts.csswg.org/cssom-view-1/>) **[cited]**. So a font size computed as `box ÷ (columns ×
advance)` falls by the zoom factor, and the rendered physical size does not change. This is the same
mechanism that makes `vw` fail SC 1.4.4, and it is the live objection to the `text-fit` proposal the
CSS WG began incubating in April 2025: the Chrome team's own explainer says "changing the page zoom
level might not alter the physical text size in that container … We currently do not have a solution
for this issue" ([csswg-drafts#12886](https://github.com/w3c/csswg-drafts/issues/12886)) **[cited]**,
and Patrick Lauke demonstrated the same code making text *shrink* under zoom
([csswg-drafts#2528](https://github.com/w3c/csswg-drafts/issues/2528#issuecomment-2770261671))
**[cited]**.

**Measured, it does not happen here, and the reason is the ceiling.** Emulating page zoom on a
1280 px window as the equivalent narrower viewport, and reporting physical size as CSS px × zoom:

| Zoom | Viewport | Map shown | Font size | Dot ink, CSS px | Physical dot ink, relative to 100% |
| --- | --- | --- | --- | --- | --- |
| 100% | 1280 | wide | 11.00 (cap) | 1.33 | ×1.00 |
| 150% | 853 | wide | 11.00 (cap) | 1.33 | **×1.50** |
| 200% | 640 | wide | 11.00 (cap) | 1.33 | **×2.00** |
| 250% | 512 | **narrow** | 14.00 (cap) | 1.70 | **×3.18** |
| 300% | 427 | narrow | 14.00 (cap) | 1.70 | ×3.82 |
| 400% | 320 | narrow | 11.09 | 1.34 | **×4.03** |
| 500% | 256 | narrow | 8.62 | 1.04 | ×3.92 |

**[measured]** The dot ink grows monotonically to 400% and plateaus at 500%; it never shrinks. Two
things make that true. First, the measured size is capped at 11 px for the wide map and 14 for the
narrow one, and over most of the range the cap is what governs — so the size is effectively a fixed
`px` value, which zoom scales normally. That is precisely the exception the CSS WG co-chair
identified: "if the container width is a simple length like `500px` then you *could* use zoom to
enlarge fit-to-width text" ([csswg-drafts#2528](https://github.com/w3c/csswg-drafts/issues/2528#issuecomment-2784612744))
**[cited]**. Second, zooming past 250% crosses the 620 px breakpoint and the map is replaced by one
with half the columns, which doubles the dot pitch outright.

So the breakpoint is not only a legibility device, it is the zoom accommodation — which is the case
F94, the canonical failure technique for viewport-unit text, explicitly contemplates: "Note If media
queries were used to adjust the size of text or unit of measure at different screen sizes, **it may
not be a failure of Resize Text**" (<https://www.w3.org/WAI/WCAG21/Techniques/failures/F94.html>,
updated 9 March 2026) **[cited]**. Between 200% and 250% the map more than doubles, so the 200%
threshold of SC 1.4.4 is met with room. The residual risk is narrow and worth writing down: if the
caps were ever removed, or a viewport appeared where the box is small enough for `fit()` to bind
across the whole zoom range, the map would stop responding to zoom entirely. The caps are load
bearing, not cosmetic.

### 4.2 Display type: `clamp()` with relative bounds, and it passes

`.fig b { font-size: clamp(3rem, 6vw, 4.4rem) }` is the page's one fluid size. Both bounds are in
`rem`, which is the shape a fluid size has to have — a bare `vw` is the documented failure, F94:
"As these units are relative to the viewport, it means they cannot be resized by zooming or adjusting
text-size" **[cited]**.

The quantitative rule for whether a clamped size still reaches 200% is Maxwell Barvian's, derived by
solving for the zoom at which the fluid curve doubles: "**If the maximum font size is less than or
equal to 2.5 times the minimum font size, then the text will always pass WCAG SC 1.4.4**, at least on
all modern browsers" (<https://www.smashingmagazine.com/2023/11/addressing-accessibility-concerns-fluid-type/>)
**[cited]**. Here the bounds are 48 px and 70.4 px against a 16 px root — a ratio of **1.47**, well
inside 2.5 **[derived]**. The 2.5 comes from browsers reaching 500% zoom, which they all now do:
Firefox raised its ceiling from 300% in **Firefox 85**, January 2021
([Bugzilla 1681213](https://bugzilla.mozilla.org/show_bug.cgi?id=1681213)) **[cited]**, so the
often-repeated 300% caveat is obsolete.

### 4.3 Container queries were not adopted, and support is not why

`container-type: inline-size` and the `cq*` units are Baseline since 14 February 2023 (Chrome/Edge
105, Safari 16, Firefox 110) **[cited]**, and letting the map size itself against its own column
rather than the viewport is architecturally the right dependency. Three reasons not to, here:

1. **It does not solve the actual problem.** The size is still `box ÷ (columns × advance)` and `cqi`
   cannot supply the advance any more than `vw` can. It would replace a media query the page honours
   with scripting off by a mechanism that still needs the script to do the arithmetic.
2. **`cqi` inherits the zoom problem from whatever sizes the container**, so it is not a fix for
   §4.1 either. The normative rule is that a container query length resolves against the nearest
   eligible ancestor container, and "if no eligible query container is available, then use the small
   viewport size for that axis" — so on the root `1cqi` *is* `1svi`
   (<https://drafts.csswg.org/css-conditional-5/>) **[cited]**. A container sized in `%` of a
   viewport-derived ancestor is as zoom-resistant as `vw`; one sized in `px` or `rem` is not. The
   dependency is on the chain, not on the unit.
3. **It imposes containment.** `container-type: inline-size` "applies style containment and
   inline-size containment to the principal box, and establishes an independent formatting context",
   and inline-size containment determines the inline intrinsic size "as if the element had no
   content" **[cited]** — which is what makes content-sized elements collapse. Worth recording that
   the commonly cited *layout* containment is no longer part of it: the CSS WG resolved on
   2024-07-24 that `container-type` does not force layout containment
   ([csswg-drafts#10544](https://github.com/w3c/csswg-drafts/issues/10544)) **[cited]**, and MDN's
   own container-queries guide is still stale on this. Also note the `cq*` units now live in CSS
   Conditional Rules 5; `css-contain-3` has been emptied out.

### 4.4 The OS and browser text-size settings — and the one thing this page gets wrong

`-webkit-text-size-adjust: 100%` is often described as defeating the OS text size. It does not. It
governs *inflation* of a page laid out at a width other than the device's, and nothing else. In Blink
`none` and `100%` are literally one value — `// An adjustment of 'none' is equivalent to 100%.` in
`text_size_adjust.h` **[cited]** — and Chromium's autosizer was deleted outright in April 2026, so on
Chrome the declaration now gates nothing. The spec is explicit that the property is about the mobile
inflation algorithm and suppresses it for `white-space: pre` anyway
(<https://drafts.csswg.org/css-size-adjust-1/>) **[cited]**. In WebKit it still matters, and there
`100%` is *not* equivalent to `none`: `none` short-circuits, while `100%` enters a narrower set of
heuristics **[cited]**. Either way it does not touch iOS Dynamic Type, which resolves through a
different code path entirely. The declaration is harmless.

**`body { font-size: 15px }` is the real cost, and it is larger than it looks.** Three things follow
from it, each independently sourced:

1. **The browser's default font-size preference is overridden** for everything inheriting from
   `body`. The preference does not arrive as a user-origin declaration; it changes what the initial
   value `medium` computes to, and an author declaration replaces it by ordinary cascade precedence.
   15 px is also *below* the 16 px default, so a user starts smaller than they asked for.
2. **`rem` still tracks the root, so the page scales incoherently.** `.fig b`'s `3rem`/`4.4rem`
   resolve against `html`, which still honours the preference, while body copy is frozen. A user with
   a 20 px default gets a display number that grows from 48 to 60 px over body text that does not
   move at all.
3. **It disables `<meta name="text-scale" content="scale">`**, which shipped in **Chrome 146 on
   10 March 2026** and is the mechanism by which a page opts into the OS text-size setting. CSS Fonts
   5: "User agents must calculate the computed value of `medium` by multiplying `16px` by the text
   scale factor" (<https://drafts.csswg.org/css-fonts-5/#text-scale-meta>) **[cited]**; the
   feature's proposer states the consequence directly — "if you override the default font size, the
   `<meta name=text-scale>` tag will have no effect" **[cited]**. It equally blocks the
   `font: -apple-system-body` route to iOS Dynamic Type, which requires the root's size to be left
   alone. Roughly 37% of Android and 34% of iOS users have changed their OS text scale, against about
   3% who change a desktop browser's default font size **[cited, via the CSS WG explainer; the
   underlying survey's sample size is not published — see §5, item 9]**.

**This was deliberately not changed here**, for a reason worth recording rather than a shrug. The
obvious fix — deleting the declaration — does not give 16 px on this page: the page's font stack is
monospace, and `medium` for monospace is the *default fixed* font size, which is **13 px** in both
Blink and WebKit **[cited]**. So dropping it makes the body text smaller, not larger. The correct fix
is to negotiate rather than override, e.g. `html { font-size: max(1em, 15px) }`, which keeps the
design's floor while letting a raised preference win — the pattern Miriam Suzanne argues for in
<https://www.oddbird.net/2025/07/22/size-preferences/> **[cited]**. That rescales every size on the
page at once and is a design decision for the owner, not a mobile-legibility defect, so it is
recorded here and left.

### 4.5 After the change: measured at every width, both engines

**[measured]**

| Engine | Viewport | Document overflow | Map shown | Box | Block | Font size | Dot pitch, CSS px |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WebKit | 320 | **0** | narrow 38×11 | 288 | 288.02 × 121.95 | 11.09 | 3.79 × 2.77 |
| WebKit | 390 | **0** | narrow | 358 | 358.00 × 151.59 | 13.78 | 4.71 × 3.45 |
| WebKit | 430 | **0** | narrow | 398 | 363.67 × 154.00 | 14.00 | 4.79 × 3.50 |
| WebKit | 620 | **0** | narrow | 588 | 363.67 × 154.00 | 14.00 | 4.79 × 3.50 |
| WebKit | 621 | **0** | **wide 76×22** | 589 | 571.48 × 242.00 | 11.00 | 3.76 × 2.75 |
| WebKit | 1200 | **0** | wide | 704 | 571.48 × 242.00 | 11.00 | 3.76 × 2.75 |
| Chromium | 320 | **0** | narrow | 288 | 287.83 × 122.03 | 11.09 | 3.79 × 2.77 |
| Chromium | 390 | **0** | narrow | 358 | 358.00 × 151.60 | 13.78 | 4.71 × 3.45 |
| Chromium | 430 | **0** | narrow | 398 | 363.67 × 154.00 | 14.00 | 4.79 × 3.50 |
| Chromium | 1200 | **0** | wide | 704 | 571.48 × 242.00 | 11.00 | 3.76 × 2.75 |

The switch behaves exactly as designed at the boundary: 620 shows the narrow map, 621 shows the wide
one at precisely its 11 px ceiling in a 589 px box.

**Markers, checked against the text layout rather than against the script's own arithmetic.** For
each of the 31 markers, a `Range` over the character at the projection's `(row, col)` gives that
cell's pixel box from the browser's own text layout; the marker's centre is then located by scanning
the grid for the cell that contains it. **[measured]**

| Engine | Viewport | Map | In the exact cell | Within one cell | Centre offset from the cell centre | Over an inked cell |
| --- | --- | --- | --- | --- | --- | --- |
| WebKit | 320 | narrow | 27/31 | **31/31** | dx ±3.98, dy ±5.47 px (cell is 7.6 × 11.1) | 28/31 |
| WebKit | 390 | narrow | 27/31 | **31/31** | dx ±4.92, dy ±6.82 | 28/31 |
| WebKit | 430 | narrow | 27/31 | **31/31** | dx ±4.83, dy ±6.87 | 28/31 |
| WebKit | 1200 | wide | 27/31 | **31/31** | dx ±3.58, dy ±5.49 | 22/31 |
| Chromium | 390 | narrow | **31/31** | 31/31 | dx ±4.63, dy ±7.64 | 27/31 |
| Chromium | 1200 | wide | 28/31 | **31/31** | dx ±3.69, dy ±5.50 | 22/31 |

The residual off-by-ones are markers whose *fractional* row or column is within a fraction of a
pixel of a cell boundary — Czechia is at row 2.02 of the narrow map, so its centre sits 0.3 px inside
the cell and the `Range` box's leading puts it on the other side. The offset never exceeds half a
cell in either axis, which is the statement that matters: the marker is drawn at the fractional
position the projection gives, not at a rounded one. More markers sit over drawn coast on the
narrow map (28) than on the wide one (22), because a coarser cell covers more coastline.

---

## 5. What could not be determined

1. **No measurement on a real iOS or Android device.** Everything is Playwright WebKit and Chromium
   on macOS. The iOS conclusion — Apple Symbols at 0.68359 em, because Apple's own table lists Apple
   Braille as downloadable-only on iOS while Apple Symbols is a system font — is **derived**, and
   rests on the two faces having identical braille metrics on macOS. It was not possible to inspect
   an iOS copy of Apple Symbols and confirm it carries all 256 glyphs at 1400/2048. The Android
   numbers come from the AOSP font binary and its subsetting script, not from a device.
2. **Which face `monospace` and `ui-monospace` resolve to on iOS.** WebKit's
   `SystemFontDatabaseCoreText.cpp` contains a branch mapping `courier new` → `Courier` for iOS, but
   it is behind a build flag that is off outside watchOS and tvOS, so it is dead code that only
   *suggests* the answer. It does not change any conclusion: every candidate has 0/256 coverage.
3. **There is no standard for a minimum legible dot size on a screen.** WCAG sets no minimum font
   size at all. The 12–13-device-pixel figure in §2.4 is one measurement against one stated
   criterion, and it was non-monotonic in size. The ink-per-dot estimate is arithmetic. Neither is
   authoritative and the document does not pretend otherwise.
4. **No public bug report of braille art failing specifically on iOS Safari or Android Chrome
   exists.** WebKit's Bugzilla returns ten hits for "braille" and all ten are about screen readers
   and refreshable braille displays. The browser-side reports that do exist and that corroborate the
   advance arithmetic to 0.01 px are from Electron and browser terminals —
   [vercel-labs/wterm#87](https://github.com/vercel-labs/wterm/issues/87),
   [warpdotdev/warp#9696](https://github.com/warpdotdev/warp/issues/9696),
   [jupyter/notebook#4354](https://github.com/jupyter/notebook/issues/4354) — not from mobile
   browsers. The mobile case is undocumented in public primary sources and had to be measured rather
   than cited.
5. **Whether any shipping browser implements Unicode 17's change to U+2800.** Its `Line_Break`
   changed from `AL` to `BA` for Unicode 17.0 (UTC #184 consensus 184-C29;
   <https://www.unicode.org/Public/UCD/latest/ucd/LineBreak.txt> now reads
   `2800 ; BA # So BRAILLE PATTERN BLANK`) **[cited]**, which makes every blank-to-dot transition a
   line-break opportunity. This is inert here because `<pre>` does not wrap, but it means the map
   must never be given `pre-wrap` or `overflow-wrap`. No browser bug, WPT test or csswg issue on the
   change was found, so no engine's behaviour is known.
6. **The visual result was not reviewed by a human on a phone.** The screenshots in this pass are
   Playwright renders at `device_scale_factor: 3`. Nothing here substitutes for looking at the page
   on a 2× device, which is exactly the case §2.4 says is marginal.
7. **Whether the coastline is "required to understand the content"** under SC 1.4.11, and therefore
   whether the 2.20:1 it was published at is a conformance failure or only a legibility one. The
   markers carry the measurement; the coastline places them. This document raises the contrast to
   3.90:1 and does not attempt to settle the classification.
8. **The vertical dot lattice cannot be made uniform on all platforms at once.** `line-height: 1em`
   is exact for Android's Noto face, 4.3% loose for Apple's, and 39% tight for DejaVu (§2.3). Making
   it exact everywhere means measuring the glyph's ink extents at runtime — `TextMetrics`'
   `actualBoundingBoxAscent` on a canvas would do it — or drawing the dots directly instead of
   relying on font glyphs, which is what Ghostty and xterm.js do. Neither was attempted.
9. **The 37% / 34% OS-text-scale figures in §4.4 could not be traced to their survey.** They are
   quoted by the CSS WG's own `meta-text-scale` explainer from `appt.org`, whose page is
   Netherlands-only, last updated January 2023, and publishes no sample size. The desktop
   counterpart — about 3% of visitors changing a browser's default font size — is Evan Minto's 2018
   measurement over Internet Archive traffic, and only the headline figure could be verified. Treat
   both as orders of magnitude. The one properly measured dataset found, WebAIM's 2018 survey of 248
   low-vision users, shows the honest gap between what people report and what a browser reports:
   36.7% said they use browser text-sizing settings, and **7.9% measurably had**, while 17.9%
   magnify to 400% or more.
10. **Page zoom was emulated, not driven.** §4.1's table narrows the viewport by the zoom factor,
    which is the standard equivalence — "there's very little difference between making the window
    smaller or making the pixels bigger" — but it is not the same as pressing Cmd-+ in a real
    browser, and it does not exercise `devicePixelRatio` changes. Pinch zoom, which magnifies without
    changing the layout viewport, was not tested at all; on that path the map is magnified normally
    and there is nothing to measure.
11. **Whether Safari's Option-Cmd-+ scales author `px` font sizes.** One source calls it text-only
    zoom, which in Gecko does scale `px`; the CSS WG explainer describes Safari's per-site control as
    changing the initial font size, which would not. No test was run and the two accounts were not
    reconciled. It matters only for §4.4's conclusion about `body { font-size: 15px }`, which holds
    either way.
