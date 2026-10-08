---
id: WSW-20261007-023
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - preview
  - ink-simulation
related:
  - WSW-20261007-022
  - WSW-20261007-017
---

# Ink simulation draws at the real pen width and explains the pitch chain

## Summary

The ink-simulation preview now draws its strokes at the real pen width
(`pen_diameter_mm` x current zoom) instead of a fixed 1 px, so on-screen
overlap - and therefore ink mixing - matches what the pens will actually
cover. The Artwork scale and Ink simulation tooltips now spell out the
effective-pitch chain: effective spacing = Dot pitch x Artwork scale x the
tone-adaptive factor (1-3x), and full coverage needs the effective spacing
at or below the pen width.

## Reason

Owner: "colors are still not combining well in the preview." Inspection:
mixing only occurs where strokes overlap; the owner's 200 % Artwork scale
had doubled the 0.3 mm pitch to 0.6 mm+ (5-9x the pen's width in lighter
tones), so most of the sheet stayed paper-white between rows and different
inks met only at crossings. The 1 px simulation strokes also
under-represented overlap at zoomed-out views.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the simulation pass computes
  pixels-per-millimetre from the current bounds and draws at
  `max(1, pen_diameter_mm x px_per_mm)`; the Ink simulation tooltip states
  the overlap rule.
- `software/generator_tabs/cmyk_tab.py`: Artwork scale tooltip warns that
  the effective pitch scales with it.
- `software/README.md`: the same note in the preview-panel section.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 386
  tests (1 skipped: the pre-existing headless shader compile). The paint
  path itself cannot be unit-tested headless (no GL context); the change is
  a draw-call parameter derived from `Settings.pen_diameter_mm` and the
  current bounds.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Zooming a fixed 1 px stroke was rejected: overlap density must reflect the
  physical nib, otherwise the simulation misleads exactly when the pitch is
  near the pen width.

## Risks and follow-up

- Very small pen widths can render thinner than one pixel at zoomed-out
  views (clamped to 1 px); zoom in for exact overlap judgement.
- The pitch chain still includes the tone-adaptive factor by design, so
  light areas intentionally stay sparse.

## Files

- `software/qt_svg_to_gcode.pyw`: pen-width stroke in simulation mode.
- `software/generator_tabs/cmyk_tab.py`: scale tooltip.
- `software/README.md`: effective-pitch documentation.
