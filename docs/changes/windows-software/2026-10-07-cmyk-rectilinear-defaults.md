---
id: WSW-20261007-024
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - defaults
  - rectilinear
related:
  - WSW-20261007-020
  - WSW-20261007-022
  - WSW-20261007-023
---

# Tune the CMYK defaults for the rectilinear fill

## Summary

The CMYK tab now opens with the settings that give the rectilinear fill its
best result: **Rectilinear fill (joined rows)** style, **Dot pitch
0.20 mm**, **Black (GCR) 75 %**, artwork scale 100 %, auto levels on,
pen 0.30 mm, overdraw 1, 40000 marks/ink, 6000 px resolution, weights
100 %.

Why those values: the effective row spacing is pitch x artwork scale x the
tone-adaptive factor (1-3x), and mid tones - the bulk of a photo - sit at
2x the set pitch. At 0.20 mm the mid tones land near 0.4 mm, about one pen
width, so adjacent rows (and the four inks) genuinely overlap and the
multiply simulation shows mixed colours; dark tones fuse solid, light tones
stay sparse by design. At GCR 75 % no CMY channel is forced to zero, so
cyan no longer collapses into patches on warm content the way 100 % GCR
does.

## Reason

Owner: "change the settings to provide the best result for rectilinear,"
after the preview inspection showed 200 % artwork scale had doubled the
effective pitch and GCR 100 % had flattened the colour mix.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: default style `crosshatch` ->
  `rectilinear`; pitch 1.2 -> 0.20 mm; GCR 100 -> 75 %. Everything else
  (auto levels, scale 100 %, pen 0.30, overdraw 1, resolution 6000) stays.
- `software/README.md`: shipped-defaults sentence and recommended-settings
  row updated.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 386
  tests (1 skipped: the pre-existing headless shader compile); the
  shipped-defaults test asserts the rectilinear style, 0.20 mm pitch, and
  75 % GCR.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- 0.15 mm (fully fused mid tones) was rejected as the default: it roughly
  quadruples the draw length of the owner's last run for a modest gain over
  0.20 mm; it remains available as a manual choice.

## Risks and follow-up

- The denser default roughly triples the draw length of the previous
  200 %-scale/0.30 mm setup; expect multi-hour per-pen plans. Raise the
  pitch (0.30 mm halves it) if time matters more than density.
- Heavy overlapping ink can cockle large fills; check paper wetness. Once a
  calibration sheet is plotted and scanned, the measured profile replaces
  the display ink colours in the simulation.

## Files

- `software/generator_tabs/cmyk_tab.py`: default style, pitch, GCR.
- `software/tests/test_cmyk_tab.py`: shipped-defaults assertions.
- `software/README.md`: current-state defaults.
