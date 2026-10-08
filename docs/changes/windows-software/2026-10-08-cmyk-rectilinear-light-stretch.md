---
id: WSW-20261008-002
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - rectilinear
  - tone
  - screening
related:
  - WSW-20261008-001
  - WSW-20261007-020
---

# Open rectilinear light tones instead of hatching them

## Summary

The rectilinear fill was structurally dark: its adaptive pitch capped at 3x
the base spacing, so with the shipped 0.10 mm pitch at 280 % artwork scale
the *lightest* possible coverage for one ink was ~36 % (a 0.3 mm pen over a
0.84 mm row gap). Every inked area therefore laid down at least a
third-coverage of all four films, and the multiply overprint crushed mid
tones and shadows to black. Rectilinear now opens the row pitch up to 7x in
the lightest tones (`light_stretch = 6`; the plain line screen keeps 3x).
Per-ink coverage now spans roughly 15 %-100 % at the shipped density instead
of 36 %-100 %, so highlights stay paper, mid tones keep roughly half their
former ink, and full tones still fuse solid.

## Reason

Owner: the previous result "made it look like this" - a night photo whose
simulation was almost entirely black with a few light streaks. The cause was
structural (coverage floor), not only the image options.

## Implementation

- `software/converter_core/cmyk.py`: `_line_runs` gains `light_stretch`
  (default 2.0, the historic behaviour); the rectilinear dispatch passes
  6.0, so its pitch factor is `1 + 6*(1 - tone)`.
- `software/README.md`: the shipped-defaults sentence notes the 7x
  light-tone stretch.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 388
  tests (1 skipped: the pre-existing headless shader compile). New test: a
  20 % tone field produces fewer than 70 % of the line screen's rows; the
  chain, blank-band, sheet-ladder, and page-bounds tests still pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Raising the artwork scale or lowering the pitch was rejected: it keeps the
  36 % coverage floor and only trades which tones block up.
- Changing the shared line screen was rejected: the wide stretch is a
  rectilinear-fill choice, and the plain line screen keeps its established
  look.

## Risks and follow-up

- Light areas are now sparse parallel strokes; chains fragment more where
  the pitch opens, so M3 savings are largest in the mid and dark tones.
- The measured calibration profile is still the final step for matching the
  pens' hue and saturation.

## Files

- `software/converter_core/cmyk.py`: `light_stretch`, rectilinear value.
- `software/tests/test_cmyk_tab.py`: light-tone spacing regression test.
- `software/README.md`: current-state notes.
