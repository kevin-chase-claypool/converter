---
id: WSW-20261006-003
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/line_draw_tab.py
tags:
  - user-interface
  - generators
  - line-art
related:
  - WSW-20261006-001
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Line Draw generator tab

## Summary

The converter now has a **Line Draw** tab that turns a raster image into
edge-traced contour paths plus luminance-driven hatch lines, previews the
result, and hands the SVG to the Convert tab.

## Reason

The survey identified image-to-line-art as a permissive, non-duplicate gap:
the converter's terrain fill draws tone iso-contours, while this tab draws
edge-detected outlines with hatching, following `LingDong-/linedraw` (MIT).

## Implementation

- `software/generator_tabs/line_draw_tab.py` (`TITLE = "Line Draw"`):
  grayscale resize, Gaussian blur, Sobel gradient, non-maximum suppression,
  8-connected edge tracing with Douglas-Peucker simplification, and hatch
  runs clipped to the dark luminance mask. Modes: contours, hatch, or both.
- Controls: image file, invert, mode, edge threshold, hatch spacing, hatch
  tone, sketch jitter, minimum length, line width, seed, page size and margin.
- Output is SVG through `host.use_svg`; the tab never writes G-code.
- Attribution: `line_draw_NOTICE.md`.

## Verification

- `python -m unittest discover -s software\tests -p "test_line_draw_tab.py" -v`
  -> 4 tests pass on a synthetic disc image: all three modes produce paths,
  same seed is identical, SVG/XML is valid, and the tab hands off to a fake
  host.
- Full suite: `python -m unittest discover -s software\tests` -> 221 tests
  pass.

## Struggles and rejected approaches

None beyond tuning: the edge tracer needed the one-pixel non-maximum
suppression pass before tracing, otherwise the Sobel ridge traced as parallel
double lines.

## Risks and follow-up

- Edge suppression is a pure-Python per-pixel pass; a 900 px image takes
  seconds. The grid cap keeps the working image at 900 px on the long side.
- Single-pen output only; no CMYK separation in this tab.
- Threshold defaults suit high-contrast art; photos need the threshold and
  hatch-tone controls.
- Owner review of the visual output is the next required step.

## Files

- `software/generator_tabs/line_draw_tab.py`: tab and algorithm.
- `software/generator_tabs/line_draw_NOTICE.md`: MIT attribution.
- `software/tests/test_line_draw_tab.py`: algorithm and tab tests.
