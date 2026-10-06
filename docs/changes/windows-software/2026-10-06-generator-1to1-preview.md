---
id: WSW-20261006-017
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - generators
  - scale
related:
  - WSW-20261006-015
  - WSW-20261006-007
---

# Plot generator pages 1:1 so Artwork scale works

## Summary

Generator tabs are now previewed and saved at 1:1: their page millimetres map
directly onto the bed, with the auto fit skipped. The tab's **Artwork scale**
control now visibly changes the drawing size instead of being renormalized
away by the Convert tab's Fill-bed auto fit.

## Reason

The owner reported that Artwork scale had no effect on any generator tab. The
tabs were scaling their SVG correctly, but the preview pipeline ran the result
through `fit_mode = "fill"`, which resized the artwork bounds back to the
reach circle on every build - so 50% and 100% previewed identically.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `settings_for_source(source_tab)` returns
  the Convert tab's settings unchanged, but for a generator tab returns
  `fit_mode="manual"` and `scale=1.0`. `preview()` and `convert()` both use it
  and log "Generator page plotted 1:1; Artwork scale sets its size."
- `software/tests/test_generator_tabs.py` pins the manual/1.0 settings for
  generator sources and measures the drawing through `load_contours`: 50%
  Artwork scale produces half the width of 100%.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 14 tests pass, including the 1:1 settings test and the
  `half / full == 0.5` pipeline measurement.
- Full suite: `python -m unittest discover -s software\tests` -> 246 tests
  pass.

## Struggles and rejected approaches

- Scaling the contours after auto-fit was rejected: auto-fit has already
  destroyed the requested size, and the correct meaning of a generator page is
  that its millimetres are physical.
- Changing the Convert tab's Fit field was rejected; the override is local to
  the generator build so the imported-artwork workflow is untouched.

## Risks and follow-up

- Generator pages larger than the reach circle are clipped by the bed, with
  the existing clip warning; 200 mm pages fit the 185 mm-radius reach.

## Files

- `software/qt_svg_to_gcode.pyw`: `settings_for_source`, preview/save wiring.
- `software/tests/test_generator_tabs.py`: 1:1 and scale-survival tests.
- `software/README.md`: user-facing description.
