---
id: WSW-20260925-004
date: 2026-09-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - tools/generate_hershey_text_svg.py
  - samples/svg/us-constitution-preamble-single-line.svg
tags:
  - converter
  - svg
  - hershey
  - single-line
  - text
  - sample
---

# Add a single-centerline text SVG generator and Constitution preamble sample

## Summary

Added `tools/generate_hershey_text_svg.py`, which renders text as single-stroke
SVG paths using the public-domain Hershey vector fonts, and used it to produce a
single-centerline SVG of the U.S. Constitution Preamble for the plotter.

## Reason

Outline fonts re-trace each letter edge, doubling (or tripling) the pen work.
The plotter needs stroke-based text so each letter is drawn as a single pass,
matching the handwriting look the operator wants while keeping centerline
geometry the converter can plan directly.

## Implementation

- `tools/generate_hershey_text_svg.py` loads a Hershey font (default
  `scripts`), word-wraps to a maximum width, and emits one `<path>` per stroke
  with `fill="none"` and a visible stroke, so the converter treats each stroke
  as an independent pen-down contour. Requires the `Hershey-Fonts` package.
- `samples/svg/us-constitution-preamble-single-line.svg` renders the 52-word
  Preamble in cursive single-line at 12 mm cap height (6 lines,
  357 x 96 mm, 455 strokes).

## Verification

- The generated SVG parses through `converter_core.read_svg` and converts to a
  self-contained program (455 `M3`/`M5` pen cycles plus the final full-retract
  and park).

## Struggles and rejected approaches

Outline/TTF text was rejected because it re-traces letter outlines. A G54
off-bed park was already established earlier; this change only adds the text
rendering path.

## Risks and follow-up

- Each Hershey stroke is a separate pen lift, so 455 strokes is expected for a
  52-word cursive paragraph; it is inherent to single-stroke text, not a defect.
- The full Constitution (Articles I-VII) is roughly 4,500 words and would span
  multiple beds, so it should be generated as one file per section rather than
  a single drawing.

## Files

- `tools/generate_hershey_text_svg.py`
- `samples/svg/us-constitution-preamble-single-line.svg`
