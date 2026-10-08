---
id: WSW-20261008-001
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - tone
  - contrast
  - defaults
  - rectilinear
related:
  - WSW-20261007-025
  - WSW-20261007-024
  - WSW-20261007-022
---

# Soften the CMYK tone curve and rebalance the defaults

## Summary

Two changes to bring the plotted result closer to the source image:

1. **Soft contrast.** Contrast above 100 % now blends toward a soft S-curve
   instead of the hard linear clamp. The old math mapped everything outside
   0.25-0.75 tone to pure white or black at 200 %, which posterized the
   preview into flat fields and blown highlights; the S-curve keeps strong
   contrast with smooth, un-clipped ends (contrast 100 % is unchanged, and
   values below 100 % keep the old softening).
2. **Source-matched defaults.** Saturation 130 -> 105 %, contrast
   200 -> 110 %, black (GCR) 99 -> 80 %, weights C/M/Y 120 -> 100 % and
   K 150 -> 120 %. Everything else stays: rectilinear fill, 0.10 mm pitch,
   artwork scale 280 %, resolution 10000 px, auto levels on, hatch levels 8,
   40000 marks/ink, pen 0.30 mm, overdraw 1.

## Reason

Owner: the tuned defaults "made it look like this" (a posterized,
over-saturated ink simulation of momandbennett.jpg), then "make changes that
would make the drawing look better." The three overdriven values -
contrast 200 %, GCR 99 % with K 150 %, saturation 130 % - were the cause.

## Implementation

- `software/converter_core/cmyk.py`: for contrast > 1.0, blend the image
  toward `0.5 + 0.5*tanh(3(x-0.5))/tanh(1.5)` by the amount over 1.0 (capped
  at 1.0, i.e. contrast 2.0 = full curve). Contrast <= 1.0 is unchanged.
- `software/generator_tabs/cmyk_tab.py`: default saturation 105, contrast
  110, GCR 80, weights 100/100/100/120.
- `software/README.md`: shipped-defaults sentence and recommended-settings
  row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 387
  tests (1 skipped: the pre-existing headless shader compile). New test: a
  gray ramp at contrast 2.0 keeps its K tones strictly inside 0.05-0.95,
  where the old hard clip hit 0 and 1; the shipped-defaults test asserts the
  new values.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Keeping contrast 200 % and only lowering the default was rejected: the
  control itself posterized, so any strong setting damaged the tone map.

## Risks and follow-up

- Artwork tuned against the old hard-clip contrast renders softer at the
  same number; raise contrast or K weight for punch, and use the ink
  simulation to compare against the source.
- The definitive hue/saturation match remains the measured calibration
  profile once the test sheet is plotted and scanned.

## Files

- `software/converter_core/cmyk.py`: soft S-curve contrast.
- `software/generator_tabs/cmyk_tab.py`: rebalanced defaults.
- `software/tests/test_cmyk_tab.py`: clip regression test and defaults.
- `software/README.md`: current-state defaults.
