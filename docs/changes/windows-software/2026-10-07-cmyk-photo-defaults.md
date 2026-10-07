---
id: WSW-20261007-005
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - defaults
  - auto-levels
  - halftone
  - photo
related:
  - WSW-20261007-001
  - WSW-20261007-002
---

# Photo-ready CMYK defaults: auto levels, solid dots, 1.2 mm pitch

## Summary

The CMYK tool now opens an ordinary photo and produces a recognizable screen
without touching a control: **auto levels on** (stretch the 1st-99th
luminance percentiles before separation), **halftone with solid spiral dots**,
**1.2 mm pitch**, **75 % dot size**, **15000 marks per ink**, **1200 px
resolution**, and **100 % C/M/Y/K weights** (K was 80 %). Two explicit
controls were added: **Auto levels** and **Solid dots**. A test photo that
previously screened into a flat field now shows both faces.

## Reason

Project-owner report: "none of these are working. i imported
PXL_20211205_011351426.PORTRAIT.jpg but i cant get any of these to show enough
resolution as to show the faces." Reproducing the render on that exact photo
found three compounding causes:

1. **Spatial resolution.** The 3 mm pitch is only ~62 dots across a 200 mm
   page, and the 5000-mark cap forced an effective ~2.3 mm pitch; eyes and
   glasses (about 5-12 mm on paper) survived as 2-3 dots.
2. **Compressed tonality.** The night photo's luminance sits between 0.015 and
   0.79 with most content low in that band, so the K screen became an almost
   uniform mid-dark field; dot radius barely varied across the faces.
3. **Ring dots.** Halftone dots were drawn as circle outlines; at 1 mm scale
   they read as open rings, not printed dots, washing out mid-tone faces.

## Implementation

- `software/converter_core/cmyk.py`:
  - `prepare_image_tones(..., auto_levels=True, level_clip_pct=1.0)` stretches
    RGB by the luminance percentiles before saturation/contrast and the CMYK
    split, so low-key or hazy images use the whole tonal range.
  - `solid_dots(contours)` converts each halftone circle into a two-turn
    Archimedean spiral that reads as a filled dot at pen width; one continuous
    pen-down stroke per dot, no extra pen cycles. `screen_channel(..., solid=True)`
    applies it to the halftone style.
- `software/generator_tabs/cmyk_tab.py`: new **Auto levels** and **Solid
  dots** checkboxes (both on by default), pitch default 3.0 -> 1.2 mm (range
  now 0.6-8), dot size 100 -> 75 %, max marks 5000 -> 15000 (range to 40000),
  resolution 700 -> 1200 px (range to 2000), K weight 80 -> 100 %. Both new
  controls are in the layer cache key and passed through the pipeline.

## Verification

- Rendered the owner's photo through the shipped tab defaults (1400 px page
  render): 1647 C / 13109 M / 13137 Y / 13572 K marks, both faces visible.
  Before the change the same pipeline produced 319/2621/2614/2937 marks on a
  3 mm effective ~2.3 mm pitch with no legible faces.
- Screening the default page takes ~1.25 s; planning one dense ink measured
  8.7 s at 10635 contours and 14.7 s at 13572 contours, so the automatic
  background planning takes roughly a minute for all four inks and stays
  cancellable.
- 349 tests pass (1 skipped: shader compile on the headless platform),
  including a new auto-levels range test, a solid-vs-ring dot test, and a
  shipped-defaults test.

## Struggles and rejected approaches

- Boosting contrast and gamma first was rejected: it clipped the highlights
  (the shirt went blank) and crushed the shadows, making the faces harder to
  read than the auto-level stretch.
- Reducing CMY weights and raising K to carry detail was tried and rejected as
  the default: the screens turned into a heavy dark mass.
- Keeping ring dots and only changing pitch was rejected: even at 1.2 mm the
  ring outlines kept the mid-tones mushy; the spiral option keeps the
  halftone-area law while reading as solid ink.

## Risks and follow-up

- A dense photo screen is tens of thousands of pen cycles: at the shipped
  defaults a full-page CMYK plot is many hours of dwell time, consistent with
  the multi-hour CMYK plots reported in r/PlotterArt. Raise Dot pitch or lower
  Max marks/ink for a faster pass, or use the line/TSP/contour styles.
- Auto levels clips the top and bottom 1 % of tones; turn it off for images
  that are already well exposed.
- Not yet plotted on paper; the render is a screen-space simulation.

## Files

- `software/converter_core/cmyk.py`: auto levels, solid dots.
- `software/generator_tabs/cmyk_tab.py`: controls and defaults.
- `software/tests/test_cmyk_tab.py`: coverage.
- `software/README.md`: defaults table and tool text.
