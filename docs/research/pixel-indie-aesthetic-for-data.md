# Look Outside: a study of the game's UI, and what transfers to reading data

Research for [issue #4](https://github.com/exdsgift/tensionr/issues/4), under the v2 map in
[issue #1](https://github.com/exdsgift/tensionr/issues/1).
Date: 2026-08-02.

Everything in the main body was measured from screenshots downloaded from official sources and
inspected pixel by pixel. Sources are listed in §1. Claims are marked **[seen]** when visible in an
image, **[measured]** when computed from pixel values, and **[inference]** when neither.

---

## 0. Bottom line

Four things came out of looking at the actual pixels, and three of them were surprises.

1. **The palette is DawnBringer 16.** Not "inspired by" — the exact hex values. One
   native-resolution screenshot contains just 23 distinct colours, and all 16 DB16 values are among
   them. This is the single most useful finding, because DawnBringer documented his design reasoning
   publicly, so the palette tensionr would be borrowing comes with its rationale attached (§4).

2. **The game does not use a pixel-grid-locked bitmap font.** Its text has 3px stems and a 19px cap
   height at one size, and 2px stems with a 15px cap at another — ratios no integer-scaled bitmap
   font can produce. It is an outline font rasterised at whatever size the layout wants (§5). This
   matters enormously: the "crisp only at integer multiples" trap in Appendix A is a constraint the
   reference game *never accepted in the first place*.

3. **The game's own borders fail WCAG contrast**, at 2.65:1 and 2.96:1 against a 3:1 requirement —
   the identical defect present in all three of tensionr's current themes (§9, §B.3). The decorative
   frame is the least accessible thing in the game, and it is exactly the element a "pixel box"
   redesign would copy most eagerly.

4. **The game never relies on colour alone**, and it is worth being precise about how it avoids it.
   Item names are cyan *and* wrapped in literal `{braces}`. Shouting is red *and* in capitals. The
   selected menu row has a filled background, not just different text colour. Its four semantic text
   colours are near-isoluminant with each other — worst pair 1.20:1 — so the redundancy is not
   stylistic, it is load-bearing (§9.1).

The transfer verdict (§10): take the palette, the box construction, the two-tier type scale, the
right-aligned numeral-plus-bar pattern, and the redundant encoding. Leave the darkness, the
vignette, the letterboxing, and the frame's contrast values.

---

## 1. Sources, and what could not be obtained

**Authorship — confirmed.** Fetched from Steam's structured metadata endpoint
`store.steampowered.com/api/appdetails?appids=3373660`:
`"developers": ["Francis Coulombe"]`, `"publishers": ["Devolver Digital"]`, released 21 March 2025.
The ticket's assumption is correct. App ID 3373660 is unambiguous.

- Steam store page: <https://store.steampowered.com/app/3373660/Look_Outside/>
- Developer's own itch.io storefront (`FrankieSmileShow`):
  <https://frankiesmileshow.itch.io/look-outside>
- Engine, from the developer's own itch.io listing: tagged **RPG Maker MZ**, credited "Made with:
  RPG Maker, Aseprite, Audacity"

**Screenshots used.** Two sets, and the difference between them matters.

| Set | Count | Size | Format | Source |
| --- | --- | --- | --- | --- |
| Steam store screenshots | 13 | 1920×1080 (one 1920×1062) | JPEG | `shared.akamai.steamstatic.com/store_item_assets/steam/apps/3373660/…`, listed by the appdetails API |
| itch.io page images | 5 | 818×626, 818×626, 603×461, 497×393, 739×505 | **PNG, lossless** | `img.itch.zone/…/original/…` from the itch.io page |

The itch.io PNGs are the valuable ones. Two are **818×626**, which is 816×624 plus a 1px frame — the
RPG Maker MZ default canvas, captured at native resolution with no resampling. Exact colour values
survive in them, which is what made the palette identification possible. The Steam JPEGs are upscaled
1.73× and lossily compressed, so they are used here only for layout and for UI states the itch.io set
does not cover.

Images are referred to below as `steam01`…`steam13` and `itch1`…`itch5`.

**What could not be obtained.** All 18 images were opened and inspected. None shows a **title screen
or logotype**, an **inventory**, a **save/load or settings menu**, or a **map screen**. `itch1` is key
art — the man at the window — and carries no type at all, so it says nothing about the logo. Those
parts of the ticket cannot be answered from official material, and this document does not guess at
them. Press-kit material was not located; Devolver's own game page returned HTTP 403. The battle
command box (`itch5`) is the only menu of any kind in either set.

**A correction.** An earlier pass through this research recorded that the demo build used a
monospaced font and the release switched to proportional. Measuring glyph advances properly shows
**both are proportional** — the demo's advances just cluster tightly (11–15 canvas px, mode 13),
which reads as monospace by eye. The release mode is ~13.9 canvas px. The dialogue *wording* did
change between builds ("He is brandishing a knife!" → "He's brandishing a knife!"), which is what
drew attention in the first place. The earlier claim was wrong and is retracted.

---

## 2. Rendering

**Nominal resolution: 816 × 624** — RPG Maker MZ's default project resolution. **[measured]**, three
independent ways that agree:

1. Two itch.io PNGs are 818×626 = 816×624 plus a 1px frame.
2. On the 1080p Steam screenshots the active (non-pillarboxed) width measures 1412–1413 px.
   816 × (1080/624) = **1412.3**.
3. Glyph stems on the 1080p screenshots measure exactly 7 screen px; 4 canvas px × (1080/624) =
   **6.92**. The dialogue-box dither period measures 10–11 screen px; 6 canvas px × 1.7308 =
   **10.38**.

**The art sits on a 2px grid inside that canvas** **[measured]**. In `itch2`, 82% of horizontal
constant-colour runs have even length, with the histogram dominated by 2, 4, 6, 8, 10, 12. So the
scene art is authored at roughly **408 × 312** and drawn at 2× into the 816×624 canvas. The *text*
does not follow this grid (§5) — only the art does.

**Upscaling is non-integer, and the game accepts that.** At 1080p the canvas is scaled by
1080/624 = **1.7308**. Not an integer, so the game's own pixels are resampled and softened on a
standard monitor. **This is worth dwelling on**: the reference title for this aesthetic does not
preserve crisp pixel edges at the resolution most players use. Whatever "pixel-perfect" means here,
it is not what the game itself delivers.

**Pillarboxing** **[seen]** — the 4:3-ish canvas is centred in 16:9 with black bars either side. In
several screenshots the bars are indistinguishable from the scene, because the scene is nearly black
at the edges anyway.

**Dithering** **[measured, seen]** — used in two distinct roles:

- *Surface texture on scene art*: coarse checkerboard patterns on walls and floors, visible in
  `steam01`, `steam04`, `steam09`, `steam12`. This is how a 16-colour palette gets intermediate tones.
- *UI panel fill*: the dialogue box interior is a two-value ordered dither alternating `#1C1A29` and
  `#080708` on roughly a 3-art-pixel period. It reads as a dark screen-door texture, not a flat fill.

Both are applied to *surfaces*. **Dithering is never applied to glyphs.**

**Lighting is a separate layer, and it is what breaks the strict palette.** **[measured]** In `itch2`,
23 colours account for the entire image: 16 DB16 values, 5 DB32 values, and two off-palette tones
(`#221E3F` at 13.6% and `#211B20` at 6.9%) used as large-area background fills. But `itch5` has 2,167
distinct colours and `itch1` has 988. The extra values come from translucent overlays — the darkness
gradient, a vignette, the semi-transparent menu cursor — composited over palette colours.
**[inference]** The art is palette-locked; the lighting pass is not.

`itch4` makes the point starkly: a dim corridor scene with **only 201 distinct colours**, of which
just **5.8% are exact DB16 or DB32 values**. The palette is still underneath, but almost every pixel
has been multiplied down by the darkness layer into an off-palette tone. Compare `itch2`, a lit
interior, at 79.3%. **The lighting layer, not the palette, is what makes the game look the way it
does** — and it is the one part of the look that works by destroying information.

**Grain and scanlines** **[seen]** — `steam13` and `steam06` show pronounced horizontal banding inside
the circular "peephole" view, reading as a scanline or interlace effect. There is no visible uniform
grain layer across the whole frame. The heavy horizontal striping on floors in `steam03` and `steam08`
is drawn into the tile art, not a post-process.

**What animates** — cannot be determined from stills, and is not guessed at here.

### 2.1 What transfers from rendering

| Choice | Serves legibility? | For tensionr |
| --- | --- | --- |
| Fixed low canvas + integer art grid | Neutral | **Take the grid, not the canvas.** An 8px spacing unit gives the same discipline; a web page has no canvas to fix. |
| Non-integer upscale | **Hurts** | Unavoidable on the web too (§A.5) — and the reference game shows it is survivable. Stop optimising for it. |
| Dithered surface texture | Neutral to helpful | **Take it.** Texture without adding a hue, and it gives a second visual channel for source identity (§9.1). |
| Dithered UI panel fill | Helpful | **Take it**, lightly. Separates a card from the page without needing a border colour. |
| Pillarboxing | Hurts | **Leave it.** Wastes horizontal space, which is what dense comparison needs most. |
| Darkness / vignette / near-black scenes | **Hurts badly** | **Leave it.** It is the game's entire mood and it is achieved by hiding information. |
| Scanline banding | Hurts | **Leave it.** Interferes with 1px rules and small text. |

---

## 3. Colour: the palette is DawnBringer 16

### 3.1 The evidence

**[measured]** `itch2.png` (497×393, lossless PNG) contains **23 distinct RGB values in the entire
image**, and **all 16 DawnBringer 16 colours are present**:

| hex | share | membership |
| --- | --- | --- |
| `#000000` | 36.35% | DB32 |
| `#140C1C` | 25.66% | DB16 0 |
| `#442434` | 13.86% | DB16 1 |
| `#221E3F` | 13.64% | **off-palette** |
| `#211B20` | 6.91% | **off-palette** |
| `#30346D` | 2.01% | DB16 2 |
| `#8595A1` | 0.28% | DB16 10 |
| `#854C30` | 0.28% | DB16 4 |
| `#DAD45E` | 0.16% | DB16 14 |
| `#FFFFFF` | 0.12% | DB32 |
| `#4E4A4E` | 0.12% | DB16 3 |
| `#D2AA99` | 0.12% | DB16 12 |
| `#D27D2C` | 0.11% | DB16 9 |
| `#346524` | 0.10% | DB16 5 |
| `#757161` | 0.09% | DB16 7 |
| `#DEEED6` | 0.08% | DB16 15 |
| `#597DCE` | 0.03% | DB16 8 |
| `#323C39` | 0.02% | DB32 |
| `#696A6A` | 0.02% | DB32 |
| `#6DC2CA` | 0.01% | DB16 13 |
| `#D04648` | 0.01% | DB16 6 |
| `#595652` | 0.01% | DB32 |
| `#6DAA2C` | 0.01% | DB16 11 |

Across all five itch.io PNGs, **every one of the 16 DB16 colours appears**, and 14 of the 32 DB32
colours do. In the two native-resolution captures, 66–72% of all pixels are exactly a DB16 or DB32
value; the remainder is the lighting layer (§2).

So the palette is: **DawnBringer 16, plus black and white, plus a handful of DB32 greys, plus two
custom dark background tints (`#221E3F` navy and `#211B20` warm near-black).**

### 3.2 Why this is the most useful finding in the document

DawnBringer published his reasoning for DB16 on the Pixel Joint forum
([thread 12795](https://pixeljoint.com/forum/forum_posts.asp?TID=12795)). He designed for "good
coverage of the spectrum" and "great coverage of the brightness range (a must for any useful
palette)", weighted the dark register toward the blue/violet "commonly found in shadows/dark waters",
the lower-mid toward greens and browns "found in vegetation, wood", and chose "a red that's slightly
violet... to contrast the other colors rather than being another shade of brown/orange". He also
names its weaknesses: "very weak in magentas... also lacks much in turquoise".

DB16 for reference: `#140c1c #442434 #30346d #4e4a4e #854c30 #346524 #d04648 #757161 #597dce #d27d2c
#8595a1 #6daa2c #d2aa99 #6dc2ca #dad45e #deeed6`

The structure to copy is not the hues. It is that **the palette is a luminance ladder first and a hue
set second** — the same principle behind Solarized and Base16 (§B.2), and what lets 16 slots express
a full hierarchy.

### 3.3 What each colour actually does in the UI

**[measured]** from the native captures, cross-checked against the 1080p screenshots:

| Role | hex | Notes |
| --- | --- | --- |
| Page/scene ground | `#000000`, `#140C1C` | 62% of `itch2` between them |
| Background tint fills | `#221E3F`, `#211B20` | the two off-palette additions |
| Panel/box body | `#222034` (DB32) | the frame's inner band |
| Box frame accent | `#45283C` (DB32) | the mauve bevel |
| Box interior dither | `#1C1A29` / `#080708` | two-value ordered dither |
| **Body text** | **`#DEEED6`** | DB16 15, the lightest slot — a slightly green off-white |
| Emphasis / keyword | `~#E0C090` | tan-amber; DB16's `#D2AA99`/`#D27D2C` neighbourhood |
| Item reference | `~#60C0E0` | cyan; DB16 has `#6DC2CA` |
| Danger / shouting | `~#C04040` | red; DB16 has `#D04648` |
| Selection fill | `~#3D4F7E` | translucent blue over the dither; DB16 has `#30346D` |
| HUD stat labels | `~#70C0C0` | teal |
| HP bar | `~#D0A040` | amber |
| STM bar | `~#5080D0` | blue |
| Bar trough | `~#805030` | brown |

Values marked `~` were sampled from the lossily-compressed Steam JPEGs, because the itch.io set does
not contain those UI states at native resolution; treat them as approximate hues, not exact palette
slots. Unprefixed values come from the lossless PNGs and are exact.

**Is the palette global or per-scene?** **[measured]** Global. The same DB16 values recur across all
five native captures in unrelated scenes. What changes per scene is the *lighting multiplier* and
which background tint dominates — a bedroom reads mauve (`#442434`), a corridor reads navy
(`#221E3F`). **The mood comes from lighting and dithering, not from swapping palettes.**

That is worth holding against tensionr's three themes (§B.3), which are three *hue* variations of one
structure — green phosphor, blue tactical, black-on-white ghost. Their text contrast is genuinely
good, so this is not a criticism of their execution. But the game gets far more range out of *one*
palette by varying luminance and texture than three repaints of the same hierarchy can.

### 3.4 What transfers from colour

| Choice | Serves legibility? | For tensionr |
| --- | --- | --- |
| A single fixed 16-slot palette | **Helps** | **Take it.** One system with named roles, replacing three hue variants. |
| Luminance ladder first, hues second | **Helps** | **Take it.** The rule from §B.2, independently confirmed in a shipped product. |
| Lightest slot for body text | **Helps** | **Take it** — `#DEEED6` on `#140C1C` measures 13.9:1. |
| Hue reserved for semantic roles | **Helps** | **Take it**: emphasis, reference, danger — never decoration. |
| Per-scene lighting multiplier | Hurts | **Leave it.** Dimming a card to set mood means dimming its text. |
| Mauve/navy decorative frame accent | **Hurts** | **Leave the value** — it fails 3:1 (§9). Keep the *construction*, raise the contrast. |

---

## 4. Typography

### 4.1 What was measured

Glyph grids were dumped pixel by pixel from the native-resolution PNGs. **[measured]**, in canvas
pixels (816×624 space):

| Context | Source | Stem | Cap height | x-height | Descender | Advance (mode) |
| --- | --- | --- | --- | --- | --- | --- |
| Dialogue body | `itch3` | **3px** | 19px | **14px** | 6px | ~13px |
| Menu item ("Fight") | `itch5` | 3px | 19px | 14px | 6px | — |
| Character name ("Reid") | `itch5` | 3px | 19px | 14px | — | — |
| HUD stat label ("HP") | `itch5` | **2px** | **15px** | — | — | — |

Two sizes: a **primary size** (3px stem, 19px cap, 14px x-height) for dialogue, menu items and
character names, and a **smaller secondary size** (2px stem, 15px cap) for stat labels.

The actual `H` and `e` from the dialogue line, as measured:

```
 472 ..###.....###.................
 476 ..###.....###.................
 477 ..###.....###.....#####.......
 478 ..###.....###....#######......
 480 ..###########...##.....##.....
 483 ..###.....###..###########....
 485 ..###.....###..###............
 489 ..###.....###....########.....
 490 ..###.....###.....#######.....
```

### 4.2 The finding that matters: this is not a bitmap font

**[measured]** A bitmap pixel font scaled by an integer keeps the same stem-to-cap ratio at every
size. This font does not:

- primary size: 3px stem, 19px cap → 6.33
- secondary size: 2px stem, 15px cap → 7.5

19 and 15 are both odd, and neither is a multiple of the other. **[inference, but strongly
constrained]** This is an **outline (vector) font rasterised at two different pixel sizes**, in the
ordinary way RPG Maker MZ renders text — not a bitmap strike placed on a pixel grid.

The consequence for tensionr is large, and it cuts against the conclusion the earlier draft of this
research reached. §A.4 establishes that web pixel fonts are crisp only at integer multiples of their
design size, and that this traps you between "too small to read" and "too wide to be dense".
**Look Outside sidesteps that trap entirely by not using a grid-locked font.** It picks whatever size
the layout needs and lets the rasteriser deal with it. The chunky *look* comes from the letterforms —
thick uniform stems, high x-height, generous counters — not from grid alignment.

So the reference game licenses a much less restrictive approach than the appendix implies: **choose a
face whose letterforms read as pixel-adjacent, then size it freely for legibility.**

### 4.3 Proportions

x-height / cap height = **14/19 = 0.737**. Very high — the measured ratios in §A.3 are 0.750 for
Press Start 2P, 0.545 for Departure Mono, 0.525 for Fira Code. A high x-height is exactly what you
want for small text, because x-height is what the eye actually reads (§A.4).

Descender depth is 6px against a 14px x-height, and descenders are genuinely present — visible on
`g`, `y`, `p` in the dumped grids. This rules out faces that lack them (Press Start 2P has none).

Spacing is **proportional**, in both builds, with advances clustering 11–15 canvas px around a mode
of 13 (§1).

### 4.4 Identification

**Not identified.** I could not name the face from official material, and no developer statement about
typography was found on Steam, itch.io, or in the one substantial interview.

What can be said with confidence from the metrics:

- It is **not Press Start 2P** — that has no descenders and a 1.000em advance; this has 6px
  descenders and proportional spacing.
- It is **not** RPG Maker MZ's stock font (M PLUS), which is not a pixel-style face at all.
- It is a **proportional, pixel-styled outline face** with uniform ~3px stems at its primary size, an
  unusually high x-height ratio (0.737), real descenders, rounded terminals, a single-storey `g`, and
  a dotted `i` with a separate 3px dot.

Emphasis is achieved **entirely by recolouring words**, never by weight or italic **[seen]** —
`FRIENDS!` in tan (`steam02`), `that painting` in tan (`steam04`), `knife!` in tan (`steam12`),
`{Baseball Bat}` in cyan (`steam03`), `CLOSE!` in red (`steam09`). There is no second weight of the
font anywhere in the screenshot set.

### 4.5 What transfers from typography

| Choice | Serves legibility? | For tensionr |
| --- | --- | --- |
| Outline font sized freely, not grid-locked | **Helps** | **Take it.** The key licence: pixel-*looking* letterforms, sized for reading. |
| High x-height (0.737) | **Helps** | **Take it** — prioritise x-height over nominal size when choosing a face. |
| Real descenders | **Helps** | **Require it.** Rules out Press Start 2P, Silkscreen, Tiny5 (§A.3). |
| Exactly two sizes | **Helps** | **Take it.** Body plus a smaller label size is enough. |
| Proportional spacing | **Helps** | **Take it** — and note it argues against an all-monospace stack (§A.6). |
| Emphasis by colour only | **Hurts** | **Modify.** Fails WCAG 1.4.1. Keep the colour, add weight or a marker. |
| Single weight throughout | Hurts | **Leave it.** A second weight is the cheapest emphasis channel there is. |

---

## 5. Text boxes and dialogue

### 5.1 Frame construction — [measured]

The frame is a **nine-slice bevel, 6 art pixels (12 canvas px) thick**, identical in the dialogue box
and the menu box. Cross-section, scanning inward:

| Band | Canvas px | Art px | Colour |
| --- | --- | --- | --- |
| outer keyline | 2 | 1 | `#000000` |
| outer bevel | 2 | 1 | `#45283C` mauve |
| frame body | 4 | 2 | `#222034` navy |
| inner bevel | 2 | 1 | `#45283C` mauve |
| inner keyline | 2 | 1 | `#000000` |
| interior | — | — | `#1C1A29`/`#080708` two-value dither |

So it is not a 1px or 2px line. It is a **five-band bevel**: black, mauve, navy, mauve, black. The
double keyline is what makes it read as raised regardless of what sits behind it — the black bands
isolate the frame from both the scene and the interior.

Corners are **[seen]** slightly rounded — a single pixel notched off each corner rather than a radius.

### 5.2 Layout — [seen]

- The dialogue box is **bottom-anchored, full-width**, with a small margin to the canvas edge.
- The **speaker name sits in its own separate box** above and to the left of the main box, in the same
  bevel construction, sized to its content. In `itch3` this box is present but **empty** — narration
  keeps the plate and leaves it blank. In `steam12` the plate is absent entirely for narration. Both
  patterns occur.
- Text is left-aligned with generous padding, roughly one line-height in from the frame.
- **Line spacing is loose** — in `steam04`, three wrapped lines occupy a box tall enough for four.
- A **continue indicator** — a small downward triangle in the off-white — sits centred at the bottom
  edge **[seen]** in `steam02`, `steam03`, `steam09`, `steam12`, `itch3`.
- The box is a **fixed height** regardless of content: one line of text in `steam02` and `steam12`
  leaves most of the box empty. The box does not shrink to content.

### 5.3 Choices — [seen], `steam04` and `itch5`

Choices appear in a **separate bevelled box**, above the dialogue box and right-aligned in `steam04`,
bottom-right in `itch5`. Within it:

- one row per option, stacked, no separators
- the **selected row has a filled background** spanning the full row width — a translucent blue over
  the dithered fill
- the unselected row keeps the plain dithered fill
- **text colour is identical in both states** (`#DEEED6`-family off-white, measured in `itch5`)

That last point is the important one. **Selection is signalled by fill, not by text colour.** So it
survives greyscale, and the text never loses contrast against its own background.

### 5.4 What transfers — the event card

The concrete translation the ticket asks for: **what a dialogue box becomes when it is an event card
showing diverging sources.**

| Game element | Becomes |
| --- | --- |
| Bevelled box | The event card. Keep the five-band construction; raise the accent colour to clear 3:1 (§9). |
| Separate speaker-name plate | The **source name plate** — one per framing, above its text block. A genuinely good fit: the plate is already designed to label a block of text with an attributed voice. |
| Empty name plate for narration | The card's state when the event has no attributed source yet. |
| Full-width bottom anchor | **Drop.** A comparison needs two or more blocks side by side, not one bottom-anchored box. |
| Fixed box height | **Drop.** Cards must size to content; a half-empty card wastes the scarcest resource on the page. |
| Loose line spacing | **Keep.** It is doing real work for readability. |
| Continue triangle | Becomes a "more sources" / expand affordance where a card truncates. |
| Selected row = filled background | **Keep exactly.** The right way to mark a selected source or event. |
| Identical text colour in both states | **Keep exactly.** Never dim the unselected option's text. |

---

## 6. HUD, stats and bars

This is the part of the game closest to what tensionr needs, so it gets the most attention.

### 6.1 Construction — [measured, seen] from `itch5`, `steam01`, `steam05`, `steam07`

The HUD occupies the bottom-left corner. Top to bottom:

1. A **portrait** — a face in a bordered box, roughly square.
2. The **character name**, at the primary type size, left-aligned under the portrait.
3. Three **stat rows**, one per line: `HP`, `STM`, `Ammo`.

Each stat row is a strict three-column grid:

```
LABEL      [=====bar=====]   NUM
```

- **Label**, left-aligned, at the *smaller* type size (2px stem, 15px cap), in teal
- **Bar**, fixed width, immediately right of the label
- **Numeral**, **right-aligned** against the bar's right edge, at the primary size, in off-white

**[measured]** The bar is a two-part construction: a filled portion in the stat's own hue
(`~#D0A040` amber for HP, `~#5080D0` blue for STM) over a **trough in brown `~#805030`**. No gradient,
no rounded cap, no border on the bar itself. Fill length encodes the value.

**The HUD panel has no frame.** **[seen]** Unlike the dialogue and menu boxes, the HUD sits on a
translucent dark dithered panel with no bevel — it fades into the scene at its right edge. In
`steam05` and `steam07` the panel is clearly semi-transparent, with scene art visible through it.

**Numerals are the same face as body text** **[measured]** — no separate tabular or display face.
They are right-aligned, which is what makes columns of them scannable.

### 6.2 The bar is the weak part

**[measured]**, and this is the one genuine design failure in the HUD:

- HP fill `#D0A040` against trough `#805030`: **2.83:1**
- STM fill `#5080D0` against trough `#805030`: **1.72:1**
- Trough `#805030` against panel `#202030`: **2.37:1**

All three fail the 3:1 that WCAG 1.4.11 requires of a meaningful graphical object. The bars are
legible in practice only because **length** carries the information and the **numeral repeats it
exactly**. Remove the numeral and the meters would be genuinely hard to read.

That redundancy is the lesson, not the colour choice: **the number is not decoration next to the bar,
it is the accessible encoding of the bar.**

### 6.3 What transfers — the index and its history

The concrete translation: **what the HUD becomes when it is an index with its history.**

| Game element | Becomes |
| --- | --- |
| Three stat rows on a fixed grid | The index and its components, one row each, on the same three-column grid: `LABEL · bar · NUMBER`. |
| Label at the smaller size, value at the primary size | **Keep exactly.** The number is the content; the label is furniture. |
| Right-aligned numerals | **Keep exactly.** Non-negotiable for a column of values compared down the page. |
| Bar length as the primary encoding | **Keep.** But raise fill-vs-trough contrast to ≥3:1, which the game fails. |
| Numeral repeating the bar's value | **Keep, and treat it as required.** Never show a bar without its number. |
| Stat hue per row (amber/blue/teal) | **Use sparingly.** At most 4 hues, never as the only difference (§9.1, §B.5). |
| Portrait | Becomes nothing. There is no per-source avatar worth the space. |
| Frameless translucent panel | **Take it** for the index block — it distinguishes persistent readout from bordered content cards. |
| Fading into the scene at the edge | **Drop.** Fine over game art, wrong over a data page. |
| Fixed corner placement | **Take the idea**: the index is persistent furniture, not a card in the flow. |

For the **history**, the game offers nothing directly — there is no graph anywhere in the screenshot
set. The transferable piece is the bar itself: a row of small bars, one per day, on the same fixed
grid with the current value right-aligned, is a sparkline that inherits the HUD's construction
honestly. **[inference]** — a design suggestion, not something observed in the game.

### 6.4 The empty state

The ticket asks what the empty state looks like when there is nothing to report. The game answers
this, in a small way: **`itch3` shows an empty speaker-name plate** — the frame drawn, correctly
sized, containing nothing. The box does not disappear, and it does not apologise.

That is the right pattern. An event card with no diverging sources keeps its frame and its source
plate, and states plainly that the sources agree — which for tensionr is not an absence of data but a
*finding*, and arguably the more interesting one. The structure holds its shape; the content says what
it knows.

---

## 7. Menus and hierarchy without colour

Only one menu exists in the official set: the battle command box in `itch5`, containing `Fight` and
`Escape`.

**[measured, seen]:**

- Items are stacked, one per row, left-aligned with padding, **no separators**
- Row height is generous — a 19px cap band within a ~44px row
- Selection is a **filled row background**, full width
- **Text colour is identical** in selected and unselected rows
- No icons, no bullets, no chevrons, no numbering

**How hierarchy works without colour** — the answer to that part of the ticket: through **fill,
position, and size**, not hue.

1. **Fill** marks state. It survives greyscale, because the fill differs in luminance from the
   unfilled row: `~#3D4F7E` vs `#101010` measures **3.08:1** (§9) — barely clearing 3:1, but clearing
   it.
2. **Position** marks grouping. The name plate sits above its dialogue box; the choice box above the
   dialogue box; the HUD in a fixed corner. Nothing needs a colour to say what it belongs to.
3. **Size** marks importance. Two type sizes, used consistently: content at the primary size, labels
   at the smaller one.

Hue is spent only on *semantics* — emphasis, item reference, danger — never on structure. This is the
same luminance-for-structure / hue-for-meaning rule that §3.2 found in the palette and that §B.2 finds
in Solarized and Base16. **The game applies it consistently across three independent subsystems.**
That consistency is the single most transferable thing in its design.

### 7.1 What transfers from menus

| Choice | Serves legibility? | For tensionr |
| --- | --- | --- |
| Selection = filled row | **Helps** | **Take it.** Raise fill-vs-ground contrast above 3.08:1. |
| Identical text colour across states | **Helps** | **Take it.** |
| Generous row height | **Helps** | **Take it** for scannable lists. |
| No separators between rows | Neutral | **Reconsider.** Fine for two items, poor for a long event list; a 1px rule at ≥3:1 helps. |
| Hierarchy via fill/position/size | **Helps** | **Take it wholesale.** |
| Hue only for semantics | **Helps** | **Take it wholesale.** |

---

## 8. Grid and alignment

**[measured]** Pulling the geometry together, everything in the UI lands on the 2px art grid:

- frame bands: 2 / 2 / 4 / 2 / 2 canvas px — all even
- box interior dither period: 6 canvas px (3 art px)
- stat rows: label, bar and numeral each align to the same left/right edges across all three rows
- the name plate's left edge aligns with the dialogue box's left edge

The underlying unit is **2 canvas px = 1 art px**, and larger elements are multiples of it. For
tensionr the equivalent is a single spacing unit — 8px is the natural web choice — with every padding,
gap, border and row height a multiple of it. This is the cheapest part of the aesthetic to adopt and
the one that most reliably makes a layout look deliberate.

---

## 9. The game's UI scored against WCAG

**[measured]** The game is not a website and was never required to meet WCAG. Scoring it anyway is the
fastest way to see which of its choices are safe to copy. Ratios computed with the WCAG relative
luminance formula (<https://www.w3.org/TR/WCAG21/relative-luminance.html>); method in Appendix C.

| Element | fg | on | ratio | verdict |
| --- | --- | --- | --- | --- |
| Body text | `#D0E0D0` | `#101020` | **13.66** | AAA |
| Body text on dark dither | `#D0E0D0` | `#000000` | 15.26 | AAA |
| Emphasis / keyword | `#E0C090` | `#101020` | 10.84 | AAA |
| Item reference (cyan) | `#60C0E0` | `#101020` | 9.05 | AAA |
| HUD numerals | `#D0E0D0` | `#202030` | 11.64 | AAA |
| HUD label (teal) | `#70C0C0` | `#202030` | 7.62 | AAA |
| Unselected choice text | `#D0E0D0` | `#101010` | 13.82 | AAA |
| HP bar fill | `#D0A040` | `#202030` | 6.70 | AA |
| Selected choice text | `#D0E0D0` | `#4060A0` | 4.49 | large/UI only |
| STM bar fill | `#5080D0` | `#202030` | 4.07 | large/UI only |
| Danger / shout (red) | `#C04040` | `#101020` | 3.62 | large/UI only |
| Selected fill vs unselected | `#4060A0` | `#101010` | 3.08 | just clears 1.4.11 |
| **Box border vs scene** | `#A03030` | `#000000` | **2.96** | **FAILS 3:1** |
| **HP fill vs trough** | `#D0A040` | `#805030` | **2.83** | **FAILS 3:1** |
| **Box border vs box fill** | `#A03030` | `#101020` | **2.65** | **FAILS 3:1** |
| **Bar trough vs panel** | `#805030` | `#202030` | **2.37** | **FAILS 3:1** |
| **STM fill vs trough** | `#5080D0` | `#805030` | **1.72** | **FAILS 3:1** |

**Text is exemplary. Chrome is not.** Every text colour clears AA and most clear AAA — the off-white
on near-black is genuinely excellent. Everything that fails is decorative or graphical: the frame
accent, and the meters.

**The border failure is the one to internalise.** tensionr's three current themes fail on borders at
**1.36–1.59** (§B.3). The reference game fails at **2.65–2.96**. Both chase the same look — a subtle
frame that sits back — and both land under 3:1, because a border that *looks* right against its
background is almost always too close to it to qualify. Copy the construction, not the value.

### 9.1 The colour-alone problem, and how the game avoids it

**[measured]** The four semantic text colours, measured against each other:

| | | ratio |
| --- | --- | --- |
| body `#D0E0D0` | emphasis `#E0C090` | **1.26** |
| body `#D0E0D0` | item `#60C0E0` | 1.51 |
| emphasis `#E0C090` | item `#60C0E0` | **1.20** |
| item `#60C0E0` | danger `#C04040` | 2.50 |
| emphasis `#E0C090` | danger `#C04040` | 2.99 |
| body `#D0E0D0` | danger `#C04040` | 3.77 |

Worst pair **1.20:1**. Body, emphasis and item text are effectively **isoluminant** — they differ by
hue almost exclusively. To a deuteranope, amber emphasis and cyan item references against off-white
body text are close to indistinguishable. This is not a flaw in the colour picks; it is forced. Any
set of colours that all clear ~9:1 against one dark background must sit in a narrow luminance band,
and therefore must be near-isoluminant with each other.

**The game compensates, deliberately and in nearly every case** **[seen]**:

| Semantic | Colour | Redundant channel |
| --- | --- | --- |
| Item reference | cyan | wrapped in literal `{braces}` — `{Baseball Bat}`, `steam03` |
| Shouting / danger | red | ALL CAPS — `CLOSE!`, `steam09` |
| Emphasis | tan | **none** — colour only (`steam02`, `steam04`, `steam12`) |
| Menu selection | blue | filled background, not text colour |
| Stat value | hue per row | numeral repeats the value exactly |

Four of five semantics carry a second channel. The exception is plain emphasis, and that is the one
place the game would fail
[WCAG 1.4.1](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html) as a web page.

For tensionr this settles the source-colour question: **at most 4 source colours, each with a text
label and a second non-colour channel.** The game's own answer — brackets, capitals, fills, repeated
numerals — is a menu of options. The dither patterns from §2 are a fifth: different 1-bit fills at the
same luminance are distinguishable to everyone, including in monochrome.

---

## 10. Transfer summary

**Take:**

- **DawnBringer 16** as the palette, with its documented rationale (§3)
- One palette varied by **luminance**, rather than hue-variant themes (§3.3)
- The lightest slot for body text; hue reserved for semantics (§3.4)
- The **five-band bevel** box construction, accent raised to ≥3:1 (§5.1)
- The **separate name plate** above a text block — it maps directly onto source attribution (§5.4)
- The **empty-but-drawn** plate as the empty-state pattern (§6.4)
- **Two type sizes**, no more: content at the primary, labels at the smaller (§4, §6)
- An **outline font sized freely** for legibility, with pixel-adjacent letterforms, high x-height and
  real descenders (§4.2)
- The stat row grid: **`LABEL · bar · right-aligned NUMBER`** (§6.1)
- **Numeral always accompanies bar**, as an accessibility requirement (§6.2)
- **Selection by filled background**, text colour unchanged (§5.3, §7)
- Hierarchy from **fill, position and size**; hue only for meaning (§7)
- A single **spacing unit** with everything a multiple of it (§8)
- **Dithered surface texture**, including as a source-identity channel (§2, §9.1)
- **Redundant encoding** of every semantic (§9.1)

**Leave:**

- Darkness, vignette, per-scene lighting multipliers (§2.1)
- Pillarboxing and the fixed canvas (§2.1)
- Scanline banding (§2.1)
- The specific frame accent value, at 2.65:1 (§9)
- The bar fill/trough values, at 1.72–2.83:1 (§6.2)
- Fixed-height boxes that don't shrink to content (§5.4)
- Emphasis by colour alone (§9.1)
- A single font weight (§4.5)
- The portrait (§6.3)

**The one-line version:** the game's *structure* is worth copying almost wholesale and its *palette
logic* exactly; its *contrast values* and its *atmosphere* are not.

---

## 11. What could not be determined

1. **Title screen, logo, inventory, save/load, settings, map.** No official screenshot shows any of
   them. Not inferred.
2. **The typeface.** Not identified. Described in metrics in §4.1 and ruled out against specific
   candidates in §4.4. No developer statement on typography was found.
3. **Exact palette slots for UI accent colours.** Dialogue emphasis, item, danger, selection and HUD
   colours appear only in the lossy Steam JPEGs, so the values marked `~` in §3.3 are approximate. A
   native-resolution capture of a dialogue-with-emphasis state would fix them.
4. **Animation.** Cannot be determined from stills.
5. **Whether the two off-palette background tints** (`#221E3F`, `#211B20`) are deliberate palette
   extensions or the product of a lighting multiply. **[inference]** favours the former, since they
   appear as large flat fills, but this is not settled.
6. **The internal art resolution** is stated as ~408×312 from run-length evidence. The canvas
   (816×624) is solid; the 2× art grid is well-supported but is an inference, not a developer
   statement.
7. **Developer intent generally.** No devlog or interview discussing UI, palette or typography was
   located. The one substantial interview covers influences only (§12).

---

## 12. Declared influences

From the one substantial interview located — Francis Coulombe interviewed by Makson Lima:
<https://medium.com/@MaksonLima/look-outside-or-do-not-since-the-consequences-will-be-post-apocalyptic-one-way-or-another-f84a1c2a8570>
(also the source Wikipedia cites for the game's development history). Verified as Coulombe's own words
rather than the interviewer's framing:

- "A big inspiration for me is the famicom game *Sweet Home*."
- "Survival horror games of course like the *Resident Evil* and *Silent Hill* series, *Clock Tower*,
  *Lone Survivor*."
- "Pixel art wise, *Castlevania 3* for the NES and the fleshy monster-planet scrolling shooter
  *Abadox* are some of my fondest early gaming memories for being immersed in a colorful pixel world."
- "I think the kind of horror that gets to me the most is when something terrifying and horrible is
  just out of sight."

Every reference is a console game. None is an information-design reference — worth remembering when
deciding how far to follow the model.

---
---

# Appendix A — Pixel fonts on the web: licences, coverage, limits

Supporting material. This constrains which parts of the game's look can be reproduced in a browser.

## A.1 Licences — verified from primary sources

Verified from Google Fonts' own `METADATA.pb` files in
[google/fonts](https://github.com/google/fonts) and from each project's own LICENSE file, not from
aggregator badges.

| Font | Author | Licence | GF category | Script subsets |
| --- | --- | --- | --- | --- |
| Press Start 2P | CodeMan38 | OFL | **DISPLAY** | latin, latin-ext, cyrillic, cyrillic-ext, greek |
| Silkscreen | Jason Kottke | OFL | **DISPLAY** | latin, latin-ext only |
| VT323 | Peter Hull | OFL | MONOSPACE | latin, latin-ext, vietnamese |
| Pixelify Sans | Stefie Justprince | OFL | **DISPLAY** | latin, latin-ext, cyrillic |
| Micro 5 | Sarah Cadigan-Fried | OFL | **DISPLAY** | latin, latin-ext, math, symbols |
| Jersey 10 | Sarah Cadigan-Fried | OFL | **DISPLAY** | latin, latin-ext |
| Workbench | Jens Kutílek | OFL | MONOSPACE | latin, math, symbols |
| Tiny5 | Stefan Schmidt | OFL | SANS_SERIF | latin, latin-ext, cyrillic, cyrillic-ext, greek |
| Handjet | Rosetta / David Březina | OFL | **DISPLAY** | arabic, armenian, cyrillic, greek, hebrew, latin, korean |
| DotGothic16 | Fontworks Inc. | OFL | SANS_SERIF | latin, latin-ext, cyrillic, japanese |
| Departure Mono | Helena Zhang & Tobias Fried | **SIL OFL** (font) | not on GF | latin, latin-ext, cyrillic, greek |
| Pixeloid Sans | GGBotNet | **SIL OFL 1.1** | not on GF | latin-ext, cyrillic, greek (135-language claim) |
| Monocraft | Idrees Hassan | OFL | not on GF | latin-ext, cyrillic, greek |
| Terminus | Dimitar Zhekov | OFL | not on GF | broadest legacy script coverage of any bitmap font |
| Spleen | Frederic Cambus | **BSD-2-Clause** | not on GF | latin only — but ships pre-built WOFF/WOFF2 |
| Ark Pixel | TakWolf | **SIL OFL 1.1** | not on GF | latin + pan-CJK (zh/ja/ko) |

Notes:

- **Departure Mono** — the repo's `LICENSE` is **MIT** (that covers the *website code*); the README
  states the *font* is SIL OFL. <https://github.com/rektdeckard/departure-mono>,
  <https://departuremono.com/>. Designed at **11px increments**, per the authors.
- **Pixeloid Sans** — SIL OFL 1.1, name-your-price on itch.io, real lowercase descenders, **9px
  native** so crisp at 9/18/36.
- **Ark Pixel** — <https://github.com/TakWolf/ark-pixel-font>, built at 10/12/16px; its README warns
  it "is in active development and still lacks many Chinese characters".
- **Spleen** — most web-ready bitmap-native font (ships WOFF2), but no Cyrillic or Greek.
- **Terminus** — broadest legacy coverage, but no officially blessed web build (see §A.5).

SIL OFL 1.1 permits web self-hosting and `@font-face` embedding provided the font is not sold alone
and modified versions are renamed. All the above can be self-hosted, which also satisfies the map's
"leggerezza" goal of dropping the Google Fonts request.

**Google Fonts' own taxonomy is evidence**: six of these are classified `DISPLAY` — the vendor's own
judgement that they are for headlines and short strings, not continuous text.

## A.2 Licence landmines

Checked against each font's own distribution, because aggregator badges are frequently wrong.

| Font | Actual status |
| --- | --- |
| **Minecraftia** | **Personal use only**; commercial requires purchase. Aggregators wrongly list CC-BY-SA. |
| **04b03 / the 04b family** | Terms **unverifiable** — original site dead, only a bare copyright string in the binary. Do not treat as free. |
| **Nokia Cellphone FC**, **Perfect DOS VGA 437** | Unverifiable from any primary source. |
| **Chicago / Charcoal clones** | Apple **trademark risk on the name**, regardless of code licence. Avoid. |
| **BitPotion** | CC BY-**ND** — the no-derivatives clause forbids modifying the font, so missing accents cannot be added. A real problem for a nine-language corpus. |
| **Determination Mono** | Personal use only, plus derivative-IP risk from a copyrighted game. |
| **Cozette** | **MIT**, not OFL (aggregator error). Usable. |
| **Tamzen** | Informal permissive wording; web use never addressed. |
| **Berkeley Mono** | Paid from $75, and **web/`@font-face` rights are not bundled at every tier**. |
| **GNU Unifont** | OFL / GPL-with-font-exception, near-complete BMP coverage, but its stated purpose is glyph *fallback*, not display. Tens of MB; subsetting mandatory. |
| **Pixel Operator**, **m5x7** | **CC0** — safest available. Note **m3x6 is not CC0** (attribution requested). |

Drop from any candidate list: "Ohno Blex"/"IBM Blex" is not a product (community Plex forks only);
"Retro Gaming" unconfirmed in `google/fonts`; "Fivo Sans" appears to be a mislabel.

## A.3 Measured metrics

Measured from the binaries with `fontTools`, reading the `x` and `H` glyph bounding boxes against
`unitsPerEm`.

| Font | units/em | x-height | cap | **x/em** | cmap | Cyrillic | Greek |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Press Start 2P | 1000 | 750 | 1000 | **0.750** | 656 | yes | yes |
| Silkscreen | 1000 | 625 | 625 | **0.625** | 226 | – | – |
| Workbench | 1024 | 626 | 882 | 0.611 | 217 | – | – |
| JetBrains Mono | 1000 | 550 | 730 | 0.550 | 976 | yes | yes |
| **Departure Mono** | 550 | 300 | 400 | **0.545** | 1079 | yes | yes |
| DotGothic16 | 1000 | 540 | 787 | 0.540 | 8231 | yes | yes |
| **Fira Code** (current site) | 2000 | 1050 | 1374 | 0.525 | 1551 | yes | yes |
| IBM Plex Mono | 1000 | 516 | 698 | 0.516 | 930 | yes | – |
| Tiny5 | 1024 | 512 | 640 | 0.500 | 1154 | yes | yes |
| Handjet | 8160 | 3840 | 5280 | 0.471 | 1339 | yes | yes |
| Pixelify Sans | 1000 | 450 | 631 | 0.450 | 574 | yes | yes |
| VT323 | 1000 | 400 | 560 | 0.400 | 568 | – | – |
| Micro 5 | 1650 | 600 | 750 | 0.364 | 331 | – | – |

**Silkscreen has no real lowercase** — x-height equals cap height exactly (625/625). With 226 glyphs
and no Cyrillic or Greek it is disqualified on coverage alone. **Departure Mono is not metrically
small** — 0.545 x/em beats the current Fira Code (0.525). **Press Start 2P's 0.750 is misleading**:
its lowercase is nearly cap-height, and its advance is a full 1.000 em.

**Descenders — hard disqualifiers** (glyph-verified):

- **Press Start 2P has no true descenders at all** — `y p q g j` all bottom at the baseline.
- **Silkscreen** has none beyond a 1px dip on `q`; cap height = x-height, effectively unicase.
- **Tiny5's descender is ~0.6px** — present in outline, absent once rasterised.

Every true pixel font examined has an x-height of only 5–8 design px. Departure Mono is best of the
set: 6px x-height, 8px cap, real −2px descender. **For comparison, *Look Outside*'s own face has a
0.737 x-height ratio and a real 6px descender (§4.3)** — better than any grid-locked candidate here,
which is exactly why it is not grid-locked.

*Discrepancy recorded:* a parallel check reported Tiny5 as lacking Cyrillic and Greek; my own `cmap`
inspection and `METADATA.pb` both show it has them. The coverage figures above are what I measured.
The descender defect rules Tiny5 out either way.

**Multilingual filter** (~9 languages): disqualified on coverage — Silkscreen (226), Workbench (217),
Micro 5 (331), VT323 (no Cyrillic/Greek). Adequate for Latin + Cyrillic + Greek — Press Start 2P,
Departure Mono, Pixeloid Sans, Tiny5, Handjet, Monocraft. CJK — only DotGothic16 (8231) or Ark Pixel.

Corroboration from a project solving this for real: Tidbyt's `pixlet` renderer, driving a 64×32 LED
display of live data, documents that its bitmap fonts need "at least one additional pixel in the
ascent... for characters with diacritics to be legible"
(<https://github.com/tidbyt/pixlet/blob/main/docs/fonts.md>). Accented characters fail first, and
nine-language headlines are full of them.

## A.4 The critical print size, and the grid trap

The governing result is Legge & Bigelow (2011), *Does print size matter for reading?*, Journal of
Vision 11(5):8, [doi:10.1167/11.5.8](https://doi.org/10.1167/11.5.8)
([abstract](https://pubmed.ncbi.nlm.nih.gov/21828237/)):

> The fluent range extends over a factor of 10 in angular print size (x-height) from approximately
> 0.2° to 2°. Assuming a standard reading distance of 40 cm (16 inches), the corresponding physical
> x-heights are 1.4 mm (4 points) and 14 mm (40 points).

Reading speed is flat across that range and falls off sharply below it. **[measured]** converting 0.2°
of angular x-height to CSS px (`s = 2·d·tan(a/2)`; 1 CSS px = 1/96 in = 0.2646 mm). The method
reproduces the paper's own 1.40 mm at 400 mm exactly:

| Viewing distance | x-height (mm) | x-height (CSS px) |
| --- | --- | --- |
| 400 mm | 1.40 | 5.28 |
| 500 mm | 1.75 | 6.60 |
| 600 mm | 2.09 | 7.92 |
| 700 mm | 2.44 | 9.24 |

A screen is normally 500–700 mm away, so **6.6–9.2 CSS px of x-height** is the realistic floor.

Pixel fonts are crisp only at integer multiples of their design size — Departure Mono's own docs say
"For pixel-perfect results, set the font size to increments of 11px." Combining the two constraints at
600 mm:

| Font | x/em | min size needed | crisp sizes | first crisp size that works |
| --- | --- | --- | --- | --- |
| Press Start 2P | 0.750 | 10.6px | 8/16/24 | 16px |
| Silkscreen | 0.625 | 12.7px | 8/16/24 | 16px |
| **Departure Mono** | 0.545 | **14.5px** | **11/22/33** | **22px** |
| DotGothic16 | 0.540 | 14.7px | 16/32 | 16px |
| Tiny5 | 0.500 | 15.8px | 10/20/30 | 20px |
| VT323 | 0.400 | 19.8px | 16/32 | 32px |
| Micro 5 | 0.364 | 21.7px | 16/32 | 32px |
| *JetBrains Mono* | 0.550 | 14.4px | *any (outline)* | *14.4px* |
| *Fira Code* | 0.525 | 15.1px | *any (outline)* | *15.1px* |

**The cost in line length.** 65–75 characters per line is the standard comfortable measure.
**[measured]** at the minimum size that clears critical print size at 600 mm:

| Font | advance/em | size | char width | 70-char line | chars in 680px |
| --- | --- | --- | --- | --- | --- |
| Handjet | 0.412 | 16.8px | 6.92px | 484px | 98 |
| DotGothic16 | 0.500 | 16px | 8.00px | 560px | 85 |
| *JetBrains Mono* | 0.600 | 14.4px | 8.64px | 605px | 79 |
| *Fira Code* | 0.600 | 15.1px | 9.06px | 634px | **75** |
| Tiny5 | 0.500 | 20px | 10.00px | 700px | 68 |
| Micro 5 | 0.364 | 32px | 11.64px | 815px | 58 |
| VT323 | 0.400 | 32px | 12.80px | 896px | 53 |
| **Departure Mono** | 0.636 | 22px | 14.00px | **980px** | **49** |
| Silkscreen | 0.875 | 16px | 14.00px | 980px | 49 |
| Press Start 2P | 1.000 | 16px | 16.00px | 1120px | 42 |

Fira Code at its critical size fits exactly 75 characters. Departure Mono at its first workable crisp
size fits 49 — a **35% loss of characters per line** for the same legibility.

**But see §4.2**: *Look Outside* escapes this entirely by not using a grid-locked font. The trap is
real for anyone insisting on pixel-perfect crispness; it is optional if you accept, as the reference
game does, that the letterforms carry the style and the rasteriser handles the size.

**The site's current body text already fails this.** **[measured]** On `origin/master`, `body` is
Fira Code at `var(--fs-base)` = 0.875rem = 14px → a 7.35px x-height. At 500 mm that clears 6.60; at
600 mm it is under 7.92 — **below critical print size**. The smaller tokens are worse. Full breakdown
in §B.3.1. Body text wants 15–16px regardless of aesthetic direction.

## A.5 Browser rendering — the hard constraint

> **There is no CSS property that makes live, selectable `@font-face` text render
> nearest-neighbour / pixelated in any browser.**

- **`font-smooth`** — MDN: non-standard, "not part of any standard", may be removed; "We do not
  recommend using non-standard features in production"
  (<https://developer.mozilla.org/en-US/docs/Web/CSS/font-smooth>).
- **`-webkit-font-smoothing` / `-moz-osx-font-smoothing`** — **macOS-only**, and they switch the
  antialiasing *algorithm* rather than disabling AA. No effect on Windows, Linux or Android.
- **`image-rendering: pixelated / crisp-edges`** — images, canvas and background images only; no
  defined interaction with glyph outlines.
- **Embedded bitmap strikes** (TTF `EBDT`/`EBLC`, BDF, PCF) are **bypassed** — browsers rasterise from
  outlines. This is why Terminus lacking a web build matters.

**Every pixel font that works on the web is a vector font whose outlines trace pixel squares.** That
is why crispness requires an integer size multiple *and* an integer device-pixel-ratio.

**Fractional DPR breaks it with no fix.** Windows scaling at 125/150/175% is common, as are many
Android densities. An 11px font at DPR 1.5 lands on 16.5 device px and is resampled. **[inference]** —
reasoned from how pixel-grid outlines rasterise plus one corroborating Ghostty terminal bug report;
not documented by MDN or W3C for fonts specifically.

**The only robust workaround is a bad trade**: pre-rendering to `<canvas>` at integer scale with
`image-rendering: pixelated` gives true nearest-neighbour text and forfeits selectable, searchable,
screen-reader-accessible text.

Telling detail: NES.css, the best-known pixel CSS library, sets `-webkit-font-smoothing: antialiased`
on `body` — it deliberately smooths its own pixel font.

And the strongest evidence of all is in §2: *Look Outside* itself is resampled at 1080p, by a factor
of 1.7308, and looks fine.

## A.6 Non-pixel companions

For anything read in sentences. All OFL, self-hostable.

| Font | x/em | cmap | Notes |
| --- | --- | --- | --- |
| **JetBrains Mono** | 0.550 | 976 | Broadest verified coverage: Cyrillic + ext, Greek, Latin + ext, Vietnamese |
| **iA Writer Mono** | — | — | Purpose-built by iA for long-form reading; inherits IBM Plex's script base |
| Fira Code | 0.525 | 1551 | Already in use |
| IBM Plex Mono | 0.516 | 930 | Cyrillic confirmed; **Greek not confirmed in the Mono subfamily** |
| Martian Mono | — | — | Closest hybrid: designed to sit on the pixel grid while staying a real hinted font — but **no Greek** |

Ruled out on coverage: **Commit Mono** (Cyrillic "coming soon"), **DM Mono**, **Space Mono**,
**Chivo Mono** (Latin only).

**An open question, now with evidence.** The above assumes body text stays monospaced. §4.3 measured
*Look Outside*'s dialogue face as **proportional** — the reference product does not use monospace for
its running text. Monospacing costs character density and reading speed in continuous prose, which is
exactly what tensionr's event summaries are. A proportional body face paired with pixel-styled labels
is very likely the better choice, and the game is evidence for it. To be settled at prototype stage.

## A.7 Other legibility limits

- **Thin stems and contrast.** W3C's own WCAG 3 exploratory methods page states that "some fonts such
  as Courier New have an unusually thin weight, and thus need much higher contrast", warns that
  disabling font smoothing "can drastically reduce contrast for small or thin fonts", and advises that
  "decorative, unusual, and very thin fonts should be avoided for columns of body text"
  (<https://www.w3.org/WAI/GL/WCAG3/2020/methods/font-characteristics-contrast/>). WCAG 2's formula
  measures only colour difference, not stroke coverage — **a font can pass contrast and still be hard
  to read**. No quantitative standard exists; the W3C text is qualitative. Note that *Look Outside*'s
  3px stems put it at the opposite extreme, which is part of why its text scores so well (§9).
- **Homoglyphs.** Low-resolution type collapses `1/l/I`, `0/O`, `5/S`, `8/B`, `rn/m`. tensionr shows
  an index value and source names, so any face chosen for numerals must be checked for a
  disambiguated zero and a distinguishable `1`/`l`. A concrete acceptance test, not theory.
- **Legibility ≠ readability.** Legibility is identifying a character; readability is sustained
  reading without fatigue. A specimen page tests the former. tensionr needs the latter.

---

# Appendix B — Limited palettes: the logic, and candidates

## B.1 Why historical palettes look as they do

**CGA** (16 colours) is 4 bits: R, G, B plus a shared intensity bit. Off is 0, on is 170 (`0xAA`);
intensity adds 85 to every channel. The one deliberate exception is colour 6, which should be dark
yellow `#AAAA00` but which IBM's 5153 circuitry attenuates to **brown** `#AA5500`, because dark yellow
is useless and brown is needed for skin, wood and dirt.
([Wikipedia](https://en.wikipedia.org/wiki/Color_Graphics_Adapter); measured hardware values at
[int10h.org](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/).) Even a
hardware-derived palette gets hand-corrected where the arithmetic produces something unusable.

**EGA** extends the same idea to 2 bits per channel — four levels (0/85/170/255), 64 colours.
([ModdingWiki](https://moddingwiki.shikadi.net/wiki/EGA_Palette).)

**Commodore 64** differs in kind: the VIC-II generates colour as a TV signal in YUV — a luma value
plus a phase-shifted chroma carrier, not arbitrary RGB. That is *why* it uniquely contains several
greys and hue-pairs at two brightness levels each. The palette has a built-in luminance ladder because
the hardware was built that way.
([unusedino.de](http://unusedino.de/ec64/technical/misc/vic656x/colors/index.html),
[pepto.de](https://www.pepto.de/projects/colorvic/).)

**Game Boy DMG** had no fixed RGB at all — a reflective LCD with four opacity levels of one olive dye,
so every "Game Boy palette" is an emulator approximation
([Pan Docs](https://gbdev.io/pandocs/Palettes.html)). Four luminance steps sufficed for complete
hierarchy: ground, shadow, mid-tone, highlight. No hue required.

**DawnBringer 16** — see §3.2, since it turned out to be the palette the game actually uses.

**Solarized** (Ethan Schoonover, <https://ethanschoonover.com/solarized/>) is the only widely-used
limited palette designed explicitly *for reading text*, in CIELAB rather than RGB. Its eight-step mono
ramp has symmetric L\* spacing so light and dark modes are perceptual mirrors, and its accents sit in
a narrow L\* band (mostly 50–60) so none shouts louder than another.

| slot | hex | L\* | | slot | hex | L\* |
| --- | --- | --- | --- | --- | --- | --- |
| base03 | `#002b36` | 15 | | yellow | `#b58900` | 60 |
| base02 | `#073642` | 20 | | orange | `#cb4b16` | 50 |
| base01 | `#586e75` | 45 | | red | `#dc322f` | 50 |
| base00 | `#657b83` | 50 | | magenta | `#d33682` | 50 |
| base0 | `#839496` | 60 | | violet | `#6c71c4` | 50 |
| base1 | `#93a1a1` | 65 | | blue | `#268bd2` | 55 |
| base2 | `#eee8d5` | 92 | | cyan | `#2aa198` | 60 |
| base3 | `#fdf6e3` | 97 | | green | `#859900` | 60 |

**Base16** (Chris Kempson,
[styling.md](https://github.com/chriskempson/base16/blob/main/styling.md)) formalises the structure:
base00–base07 a monochrome ramp, base08–base0F eight accents each bound to a *fixed semantic role*.

## B.2 The one rule

> **Luminance carries structure and depth. Hue carries category and meaning.**

The grey ramp does all the work of background / surface / border / muted text / body text / emphasis,
with no hue decisions. Accents are spent only on *what something is*, never on *how important it is*.
This is why 16 slots is enough — and §3 and §7 found *Look Outside* applying exactly this rule across
three independent subsystems.

It also means hue-variant themes solve the wrong problem: three or eight hue variations give one
hierarchy repainted three or eight times.

## B.3 Audit of the current themes — [measured]

Measured against **`origin/master`** (`git show origin/master:styles.css`), which defines **three**
themes — phosphor (default), tactical, ghost — with a documented tonal ramp
(`--theme-bright > --theme-mid > --theme-dim > --theme-faint`) and semantic text roles.

| theme | text/bg | text/surface | dim/bg | dim/surface | **border/bg** | bright/bg | mid/bg | **dim-accent/bg** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phosphor | 17.08 ✅ | 16.28 ✅ | 9.25 ✅ | 8.82 ✅ | **1.59 ❌** | 14.36 ✅ | 7.13 ✅ | **2.51 ❌** |
| tactical | 13.76 ✅ | 12.89 ✅ | 6.54 ✅ | 6.12 ✅ | **1.36 ❌** | 8.39 ✅ | 5.37 ✅ | **1.92 ❌** |
| ghost | 21.00 ✅ | 18.43 ✅ | 7.00 ✅ | 6.15 ✅ | **1.43 ❌** | 21.00 ✅ | 9.74 ✅ | **2.85 ❌** |

**Credit where it is due: the text roles are correct.** The stylesheet's own comment claims
"Text roles (`--text-main` / `--text-dim`) are WCAG AA+ on `--bg` and `--surface`" — measured, that
claim is **true in all three themes**, with most values clearing AAA. This is real work already done,
and the visual system this research proposes should build on it rather than replace it.

**Two things still fail
[WCAG 1.4.11](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html), which requires 3:1
for UI components and meaningful graphical objects:**

1. **`--border`**, at **1.36–1.59** in all three themes. For a redesign whose visual language is
   boxes and 1px rules, this is the defect that matters most — and §9 shows the reference game makes
   exactly the same mistake, at 2.65–2.96.
2. **`--theme-dim`**, at **1.92–2.85** in all three. The stylesheet documents it as "muted accents,
   dividers" — dividers are graphical objects, so 3:1 applies. `--theme-faint` is fainter still and
   is presumably fill-only, which is fine, but `--theme-dim` is doing structural work at
   sub-threshold contrast.

### B.3.1 The type scale is the other gap — [measured]

`origin/master` defines a four-step scale with an explicit comment that "0.7rem is the readability
floor — nothing renders smaller". Measured against the critical print size from §A.4, with Fira Code's
x/em of 0.525 and a 16px root:

| token | rem | px | x-height | at 500 mm | at 600 mm |
| --- | --- | --- | --- | --- | --- |
| `--fs-xs` | 0.700 | 11.2px | 5.88px | ❌ below | ❌ below |
| `--fs-sm` | 0.750 | 12.0px | 6.30px | ❌ below | ❌ below |
| `--fs-md` | 0.800 | 12.8px | 6.72px | ✅ | ❌ below |
| `--fs-base` | 0.875 | 14.0px | 7.35px | ✅ | ❌ below |

Critical x-height is 6.60px at 500 mm and 7.92px at 600 mm. **Fira Code needs ≥12.6px (0.785rem) to
clear the floor at 500 mm, and ≥15.1px (0.942rem) at 600 mm.** So:

- the declared floor of 0.7rem is **set about 12% too small even at the most generous viewing
  distance**, and 35% too small at a normal desktop distance
- `--fs-base` itself, at 0.875rem, is **below critical print size at 600 mm**

The instinct behind the comment is right — there *should* be a declared floor. The number is just
low. Raising `--fs-base` to **1rem (16px)** and the floor to **0.875rem** would put the whole scale
inside the fluent-reading range at normal desktop distance, and would cost less horizontal space than
any pixel font does (§A.4).

This is worth stating plainly because it is independent of the aesthetic question: **the type scale
should be raised whether or not anything else in this document is adopted.**

### B.3.2 What else still holds

- The page still loads **Chart.js and flatpickr from jsDelivr, plus Google Fonts** — three external
  requests, against the map's "leggerezza" goal. Every font recommended in §A.1 is self-hostable
  under OFL, so the Google Fonts request is removable at no cost.
- There is still **no visual system** in the sense this document means: the themes define colour
  variables and a type scale, but there is no defined role vocabulary for surfaces and borders, no
  spacing unit (§8), and no semantic accent set (§9.1).

## B.4 Candidate palettes — [measured]

Given §3, the primary recommendation is now **DawnBringer 16 itself**, with the roles of §3.3. These
two remain as tuned alternatives, both Base16-shaped.

**Candidate A — "Phosphor" (dark)**

| role | hex | vs bg | vs surface |
| --- | --- | --- | --- |
| bg | `#0B0F0D` | — | — |
| surface | `#131A16` | — | — |
| border | `#5E766A` | **3.93** ✅ | **3.60** ✅ |
| text-dim | `#8FA79A` | 7.50 AAA | 6.88 AA |
| text | `#CFE3D8` | 14.36 AAA | 13.17 AAA |
| text-hi | `#F0F7F3` | 17.74 AAA | 16.26 AAA |
| accent | `#5FD68A` | 10.54 AAA | 9.66 AAA |
| warn | `#E8B84B` | 10.46 AAA | 9.59 AAA |
| alert | `#F2705E` | 6.67 AA | 6.11 AA |

Note the border. The instinctive "subtle dark border" `#2A3831` measures **1.57** — the same failure
as the current themes and as the game's own frame. Reaching 3:1 on near-black forces a border that
looks lighter than instinct suggests.

**Candidate C — "Paper" (light, 1-bit feel)**

| role | hex | vs bg | vs surface |
| --- | --- | --- | --- |
| bg | `#F4F1E8` | — | — |
| surface | `#E8E4D6` | — | — |
| border | `#7E7869` | **3.89** ✅ | **3.45** ✅ |
| text-dim | `#5F5A4E` | 6.08 AA | 5.39 AA |
| text | `#2B2A26` | 12.72 AAA | 11.29 AAA |
| text-hi | `#12110F` | 16.71 AAA | 14.83 AAA |
| accent | `#1A5C99` | 6.13 AA | 5.44 AA |
| warn | `#7A5E0E` | 5.41 AA | 4.80 AA |
| alert | `#A83246` | 5.79 AA | 5.14 AA |

**Solarized as reference and warning.** Measured against `base03`: yellow 4.68, cyan 4.75, green 4.69
pass AA body; blue 4.08, violet 3.43, magenta 3.30, orange 3.26, red 3.25 **fail**; `base01` at
**2.79** fails even 3:1. Solarized Light is worse. It was designed for syntax highlighting, where
accents mark short tokens. Take its *method* — CIELAB, symmetric L\* ramp, matched accent lightness —
not its values.

## B.5 Distinguishing sources

Paul Tol's schemes (<https://sronpersonalpages.nl/~pault/>, values verified from his own page),
designed to be "distinct for all people, including colour-blind readers; distinct from black and
white; distinct on screen and paper":

- **bright** (7): `#4477AA` `#EE6677` `#228833` `#CCBB44` `#66CCEE` `#AA3377` `#BBBBBB`
- **high-contrast** (3): `#004488` `#DDAA33` `#BB5566`
- **vibrant** (7): `#EE7733` `#0077BB` `#33BBEE` `#EE3377` `#CC3311` `#009988` `#BBBBBB`
- **muted** (9): `#CC6677` `#332288` `#DDCC77` `#117733` `#88CCEE` `#882255` `#44AA99` `#999933` `#AA4499`

Okabe & Ito's Color Universal Design set (<https://jfly.uni-koeln.de/color/>) is the other standard
reference; their reasoning is instructive — vermillion replaces red "since it is recognizable also to
protanopes"; bluish green "is chosen so that it won't be confused with red or brown"; "since violet is
close to blue and appear the same to colorblinds, reddish purple is chosen". **Caveat:** the exact
values appear on that page only inside an image, so no hex values are quoted for it here; Tol's
verifiable values are used instead.

**Trap 1 — [measured].** These palettes are designed for *marks* (3:1 under 1.4.11), not *text*
(4.5:1 under 1.4.3). On the Paper background `#F4F1E8`, Tol's bright scheme measures: purple 5.39 ✅,
blue 4.16 ⚠️, green 4.01 ⚠️, red 2.73 ❌, yellow 1.73 ❌, cyan 1.63 ❌, grey 1.70 ❌. **A CVD-safe
chart palette is not automatically usable as text colour.** Source *labels* need darkened variants;
source *swatches* can use the originals.

**Trap 2, and it is unavoidable — [measured].** Any set of accents each clearing 7:1 against one dark
background:

| source | hex | vs `#0B0F0D` | rel. luminance |
| --- | --- | --- | --- |
| S1 cyan | `#7FD8E8` | 11.84 AAA | 0.5945 |
| S2 amber | `#E8C547` | 11.49 AAA | 0.5754 |
| S3 rose | `#F0908A` | 8.33 AAA | 0.4031 |
| S4 violet | `#B49BE0` | 8.00 AAA | 0.3853 |

Pairwise between them: 1.03, 1.42, 1.48, 1.38, 1.44, 1.04 — **worst 1.03**. Forcing every accent above
a high threshold against one background forces them into a narrow luminance band, making them
near-isoluminant *with each other*, so they differ by hue alone — the channel a deuteranope cannot
use. About 1 in 12 men has a red-green deficiency
(<https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness>).

**§9.1 confirms this empirically in the reference game**: its four semantic text colours measure a
worst pair of **1.20**, and it compensates with brackets, capitals, fills and repeated numerals.

**Conclusion, forced not stylistic:** colour cannot be the only channel
([WCAG 1.4.1](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html)). Maximum **4 source
colours**, each with a text label and a second channel — and a limited palette has a native one: the
**dither pattern**. Different 1-bit fills at the same luminance are distinguishable to everyone,
monochrome included.

---

# Appendix C — Reproducing the measurements

- **Contrast ratios** — WCAG relative luminance
  (<https://www.w3.org/TR/WCAG21/relative-luminance.html>): linearise each sRGB channel
  (`c/12.92` if `c ≤ 0.03928`, else `((c+0.055)/1.055)^2.4`), then
  `L = 0.2126·R + 0.7152·G + 0.0722·B`; `ratio = (L_light + 0.05)/(L_dark + 0.05)`.
- **Screenshot analysis** — Pillow. Colour census by exact RGB over the whole image; run-length
  histograms of constant-colour spans along rows to detect the art grid; glyph grids by thresholding
  luma and printing per pixel; UI colours by most-common quantised value within a hand-picked region,
  filtered by luma to separate glyphs from fill.
- **Font metrics** — `fontTools.ttLib`: bounding boxes of `x` and `H` against `head.unitsPerEm`,
  advances from `hmtx`, coverage from `getBestCmap()`.
- **Critical print size** — `s = 2·d·tan(a/2)` with `a = 0.2°`, at 1 CSS px = 1/96 in = 0.2646 mm.
  Validated against Legge & Bigelow's stated 1.4 mm at 400 mm.
- **APCA** — not normative. Removed from the WCAG 3 working draft in July 2023 for lack of Working
  Group consensus; WCAG 3 is not expected to reach Recommendation before roughly 2030
  ([Adrian Roselli](https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html)). All
  figures here use WCAG 2.x, noting (§A.7) that it measures colour difference only.
