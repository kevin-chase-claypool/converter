---
id: WSW-20261024-012
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_cmyk_wave_coupon.py
  - samples/gcode/cmyk-wave-coupon.gcode
  - software/tests/test_cmyk_wave_coupon.py
tags:
  - cmyk
  - wave-screen
  - coupon
  - test-paper
  - ink-consumption
related:
  - WSW-20261024-011
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Add a compact CMYK wave comparison coupon

## Summary

Added a 56 x 20 mm black-pen coupon that prints the original variable-depth
Wave screen beside the new equidistant-row mode. It uses ordinary paper and a
few dozen strokes instead of a full CMYK sheet.

## Reason

Full-image CMYK prints consume scarce 14-inch stock and a substantial amount of
yellow ink. Repeated algorithm comparisons need a cheap feedback loop that
still uses the production wave generator, paper pitch, feed, compensation, and
motion planner.

## Implementation

- `tools/make_cmyk_wave_coupon.py` generates
  `samples/gcode/cmyk-wave-coupon.gcode`.
- The left patch uses the original variable-depth Wave screen.
- The right patch uses Wave screen - equidistant rows with the same luminance
  field and `75 deg` screen angle.
- Both use `3.36 mm` on-paper pitch, `0.8 mm` pen width, `F700`, `0.05 mm` Path
  tolerance, the accepted bed-compensation profile, and a parked A axis.
- The complete coupon has 20 short wave runs and 640 drawing points.

## Verification

- The original patch's adjacent gaps span approximately `3.177-3.515 mm`.
- The equidistant patch holds exactly `3.360 mm` spacing within floating-point
  precision.
- The generated 783-line program contains 639 motion moves and passes
  `tools\check_gcode_motion.py --strict` with no bed rotation, no rotated
  pen-up rapid, and no path-bow warning.
- Three coupon tests cover bounds, both mode labels, exact mode behavior, motion
  limits, and black-pen use.
- Full converter discovery passes 514 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Repeating full CMYK layers is too expensive and obscures the geometry result.
- A synthetic diagram would not exercise the actual wave generator and planner.
- Rotating the bed in the first coupon adds a variable unrelated to choosing
  the wave style.

## Risks and follow-up

- The fixed-A coupon isolates the generator and short-path planner. It does not
  replace a final Xtheta/Ytheta production print.
- Once the equidistant patch looks correct on ordinary paper, use it for the
  next full yellow or magenta layer.

## Files

- `tools/make_cmyk_wave_coupon.py`: deterministic coupon generator.
- `samples/gcode/cmyk-wave-coupon.gcode`: generated black-pen coupon.
- `software/tests/test_cmyk_wave_coupon.py`: geometry and motion checks.
- `software/README.md`: usage.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  next bench step.
