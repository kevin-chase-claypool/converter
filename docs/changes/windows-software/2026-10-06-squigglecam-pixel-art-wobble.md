---
id: WSW-20261006-024
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - user-interface
  - generators
related:
  - WSW-20261006-021
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Add SquiggleCam, Pixel Art, and Wobble tools

## Summary

The next three permissive tools from the r/plotterart list are integrated:
**SquiggleCam** (msurguy, MIT), **Pixel Art** (vpype-pixelart, MIT), and
**Wobble** (cadin/line-wobbler, Unlicense). The dashboard's **Line art** group
now holds Flow Field, Line Draw, SquiggleCam, Pixel Art, and Wobble; the Tools
menu follows the same order (Ctrl+2...Ctrl+0 tail).

## Reason

The list batches were paused for the menu/navigation work; this resumes them
with the next non-duplicate tools. Plotterfun is queued for its own batch
because it is a 22-algorithm suite, not a single tool.

## Implementation

- `squigglecam_tab.py`: complete port of the upstream settings and row loop
  (line count, frequency, amplitude, brightness, contrast, min/max
  brightness, pixel spacing, black-background inversion).
- `pixel_art_tab.py`: all three vpype-pixelart modes (`big` 5x5 spiral,
  `line` runs with overdraw, `snake` connected walk), pixel pitch, max grid,
  alpha threshold, ignore-white. Colour layers are fused for the single pen.
- `wobble_tab.py`: line-wobbler's frequency/amplitude/frequency-jitter and
  endpoint toggles applied to the current preview contours; the host gained
  `current_contours()`.

## Verification

- New tests: `test_squigglecam_tab.py` (3), `test_pixel_art_tab.py` (5),
  `test_wobble_tab.py` (4); the dashboard order test now expects the three
  new tools.
- Full suite: `python -m unittest discover -s software\tests` -> 281 tests
  pass.

## Struggles and rejected approaches

- Porting Plotterfun alongside these was rejected: it is a suite of 22
  algorithms, and a partial port would repeat the simplification the owner
  flagged; it gets its own batch.

## Risks and follow-up

- SquiggleCam and Pixel Art read the static Artwork file (File > Open
  Artwork); Wobble needs an existing preview because it processes contours.
- Pixel Art fuses colours into one pen path; per-colour layers remain a
  multi-pen roadmap item.

## Files

- `software/generator_tabs/squigglecam_tab.py`, `pixel_art_tab.py`,
  `wobble_tab.py`: tools.
- `software/generator_tabs/*_NOTICE.md`: attribution.
- `software/tests/test_squigglecam_tab.py`, `test_pixel_art_tab.py`,
  `test_wobble_tab.py`: coverage.
- `software/qt_svg_to_gcode.pyw`: `current_contours()` host accessor.
- `software/README.md`: tool list.
