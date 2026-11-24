---
id: WSW-20261123-015
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_sheet.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
  - docs/testing/CMYK_CALIBRATION.md
tags:
  - cmyk
  - color-management
  - process-inks
  - tombow
  - calibration
  - ink-simulation
  - preview
related:
  - WSW-20261123-012
  - WSW-20261008-008
  - WSW-20261123-011
---

# Match CMYK separation to the process-ink response

## Summary

CMYK separation now uses the known full-ink transmittances instead of relying
only on complementary RGB channel values. It refines cyan, magenta, and yellow
coverage through the same multiply model used by the preview, accepts the
refinement only where predicted colour improves, and uses a loaded measured
ink profile for both separation and preview.

## Reason

The nominal Tombow process colours were already available, but they only
affected preview blending. Separation still set C/M/Y from `1 - R/G/B`, so the
software knew how the inks should combine but did not use that knowledge when
choosing how much ink to draw. This left avoidable colour shifts in skin,
foliage, neutrals, and dark overprints.

## Implementation

- `ink_transmittance_matrix()` converts nominal hex colours or measured
  profile values into full-coverage RGB multipliers.
- `predict_cmyk_rgb()` evaluates the same
  `product(1 - coverage * (1 - ink))` response used by the calibration
  validator and OpenGL multiply preview.
- `rgb_to_cmyk_tone()` retains the channel-complement result as a baseline,
  applies the requested GCR to Black, and refines C/M/Y with a damped
  Gauss-Newton solve. The refined value is selected per pixel only when its
  predicted RGB error is lower.
- Refinement runs in bounded chunks so full-size source images retain a
  predictable memory ceiling. Nearly neutral pixels remain K-led at high GCR
  instead of becoming maximum-density four-pen stacks.
- A loaded `cmyk-ink-profile` now reaches image-tone preparation, Auto's
  screen model, the CMYK layer-cache key, and the saved set manifest. Both
  separation and preview therefore use one ink response.
- Ink weights and gamma remain deliberate post-match adjustments. Their
  tooltips now state that 100 percent and gamma 1.0 preserve the closest
  predicted colour.
- The calibration sheet keeps its raw GCR ladder because its purpose is to
  measure each requested ink split, not to pre-correct itself through the
  nominal process model.

## Verification

- The focused CMYK suite passes `136` tests.
- The tool-shell suite passes `42` tests with one expected OpenGL-context
  skip.
- The calibration-sheet suite passes `16` tests.
- Complete converter discovery passes `661` tests with one expected
  OpenGL-context skip.
- A synthetic neutral target improves from RGB prediction RMS `0.041` with the
  plain complement to `0.001` after process matching.
- A representative skin target `(0.75, 0.20, 0.18)` improves from
  approximately `0.060` to below `0.001`.
- The measured-profile regression verifies that custom transmittances drive
  both predicted colour and the CMYK layer-cache key.

## Struggles and rejected approaches

An optical-density-only inversion was tested first. It predicted neutral and
skin colours much worse because it treated partial screen coverage as a
continuous Beer-Lambert layer rather than an area mix of paper and full ink.
The accepted model uses the same coverage blend as the preview.

Replacing the complement estimate outright was rejected because process CMY
cannot reproduce some saturated sRGB colours. Keeping the baseline and
accepting model-refined pixels only when their predicted error drops avoids
making out-of-gamut areas worse.

## Risks and follow-up

The nominal Tombow RGB transmittances are a baseline, not a spectral
measurement of the actual pen batch, pressure, paper, or drying behaviour.
Load a calibration profile for the installed pen set. Four process inks also
cannot reproduce every sRGB colour; the model minimizes error but cannot
expand the physical gamut. Physical four-pass colour checks remain required.

## Files

- `software/converter_core/cmyk.py`: process response, prediction, refinement,
  profile plumbing, and Auto model.
- `software/generator_tabs/cmyk_tab.py`: active profile, controls, cache key,
  and manifest.
- `software/generator_tabs/cmyk_sheet.py`: keeps the measurement ladder in raw
  complement/GCR coordinates.
- `software/qt_svg_to_gcode.pyw`: profile-to-separation handoff and status.
- `software/tests/test_cmyk_tab.py` and `software/tests/test_generator_tabs.py`:
  model, profile, and cache regressions.
- `software/README.md` and `docs/testing/CMYK_CALIBRATION.md`: operator
  behavior and calibration guidance.
