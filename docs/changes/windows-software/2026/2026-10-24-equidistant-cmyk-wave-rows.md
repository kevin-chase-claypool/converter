---
id: WSW-20261024-011
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - equidistant
  - row-spacing
  - clearance
related:
  - WSW-20261024-010
  - WSW-20261024-007
---

# Add an equidistant Wave-screen mode

## Summary

Added **Wave screen - equidistant rows** to the CMYK Screen style list. Every
row is an exact vertical translation of one shared waveform, so adjacent row
centre spacing is exactly the configured pitch and cannot converge.

## Reason

The variable-depth Wave screen necessarily changes spacing when individual row
amplitudes differ. Repeated prints showed that the same nearby pair could
remain tight even after changing the tone source. Equidistance and per-row
vertical wave depth are geometrically incompatible.

The existing **Wave screen** remains available for comparison. The new mode
makes the stricter no-contact geometry an explicit choice.

## Implementation

- Added stored style value `waves_even`, displayed as
  **Wave screen - equidistant rows**.
- It calculates one luminance-derived amplitude at each horizontal position
  and applies that same vertical displacement to every row.
- The channel tone remains the ink-presence mask, so blank image regions and
  each CMYK separation still control where marks exist.
- Every row baseline is separated by exactly `Dot pitch × Artwork scale`.
- The original `waves` mode and its bounded variable-depth behavior remain
  unchanged.

## Verification

- A new regression applies row-varying tone plus a horizontal luminance
  gradient. At four sampled waveform phases, every adjacent row gap is exactly
  `4.000 mm` for a `4 mm` test pitch, with no overlap.
- A second regression repeats the exact-gap check at all four CMYK screen
  angles (`15`, `75`, `0`, and `45` degrees).
- The same test confirms the shared waveform still changes amplitude across
  the page, but never between rows at the same horizontal position.
- A real Ben1 rendering at `280 %` Artwork scale gives exactly `3.360000 mm`
  center-to-center row spacing for every sampled adjacent gap in all four
  layers, with zero measured residual.
- A complete headless yellow program generated from the real image has 583
  wave runs and 35,765 lines; `tools/check_gcode_motion.py --strict` passes with
  a largest step of `3.93 deg`, A rate `268 motor deg/s`, and worst bounded bed
  path bow `0.053 mm`.
- All existing variable-depth, smooth-chord, blank-region, and CMYK style
  integration tests pass.
- `python -m unittest -v software.tests.test_cmyk_tab`: 76 tests pass.
- Full converter discovery passes 511 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Continuing to tune per-row amplitude cannot guarantee equidistance.
- Dropping luminance entirely would make the pattern uniformly flat.
- Replacing the existing Wave screen would prevent an A/B comparison against
  the variable-depth version.

## Risks and follow-up

- Vertical tone cannot be encoded as independent changes in wave height in this
  mode. Image depth is limited to the shared horizontal waveform and ink mask.
- Regenerate all four CMYK files and select **Wave screen - equidistant rows**
  explicitly. The old `waves` style is still the variable-spacing mode.
- Print on a small test area or with a non-yellow pen first; full CMYK results
  remain pending.

## Files

- `software/converter_core/cmyk.py`: exact-spacing wave construction.
- `software/generator_tabs/cmyk_tab.py`: new style option and tooltip.
- `software/tests/test_cmyk_tab.py`: spacing and style regressions.
- `software/README.md`: current Wave-screen modes.
- `docs/project/ENGINEERING_LOG.md`: design and verification record.
