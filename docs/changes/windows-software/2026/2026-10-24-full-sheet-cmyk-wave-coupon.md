---
id: WSW-20261024-014
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_cmyk_wave_coupon.py
  - software/tests/test_cmyk_wave_coupon.py
  - samples/gcode/cmyk-wave-coupon.gcode
tags:
  - cmyk
  - wave-screen
  - coupon
  - test-paper
  - parked-control
  - rotating-bed
  - all-angles
related:
  - WSW-20261024-013
  - WSW-20261024-012
---

# Expand the CMYK wave coupon to a full-sheet motion matrix

## Summary

Replaced the two-patch coupon with one sixteen-patch program that fits on an
already-mounted 14-inch round sheet. It tests zero-anchored depth against
equidistant rows at all four CMYK screen angles. The upper half is planned with
A parked as a geometry control; the lower half uses production Xtheta/Ytheta
planning. One Cycle Start completes the entire matrix without retaping,
re-registration, a file swap, or an operator checkpoint.

## Reason

The prior coupon tested only the 75-degree magenta screen angle. A full CMYK
image uses 15, 75, 0, and 45 degrees, and the reported collisions were
distributed throughout the image. Testing one angle on a small scrap did not
use an already-taped sheet efficiently and could miss an angle-specific
regression.

## Implementation

- The program contains sixteen `54 x 28 mm` patches in four columns and four
  rows. Columns are C15, M75, Y0, and K45 from left to right.
- The first row of each two-row set uses **Wave screen - zero-anchored depth**.
  The
  bottom row uses **Wave screen - equidistant rows** with the same tone field.
- The upper parked matrix occupies `y = -72..-10 mm`. The lower two-row
  Xtheta/Ytheta matrix occupies `y = 10..72 mm`.
- The combined field is `234 x 142 mm`, centered on the sheet. Its corners are
  about `137 mm` from the registered center, inside the active compensation
  coverage and gantry reach.
- The program uses the production `3.36 mm` paper pitch, `0.8 mm` pen,
  `F700`, and `0.05 mm` Path tolerance. Bed compensation remains enabled.
- The parked and motion jobs are combined behind one preamble and one `M2`
  using preplanned job lists, so ioSender sees one uninterrupted program.

## Verification

- The coupon tests cover all four CMYK angles, both wave modes, both motion
  modes, one-program emission, layout bounds, spacing behavior, and motion
  limits.
- The file contains 220 wave contours and 18,804 source drawing points.
- The complete program passes `check_gcode_motion.py --strict`: `5.18 deg`
  largest drawing step, `268 motor deg/s` largest A rate, and no pen-up
  rotation.
- All three focused coupon tests pass. Full converter discovery passes `519`
  tests with one expected OpenGL-context skip.
  Four moves exceed the requested `0.05 mm` path target because the bounded
  subdivision cap binds; all controller motion limits pass.

## Physical procedure

1. Keep the current sheet mounted and registered.
2. Load `cmyk-wave-coupon.gcode` and press Cycle Start once.
3. Let the file complete without pausing or swapping programs.
4. Compare each equidistant patch with the zero-anchored patch directly above
   it. Then compare the upper parked pair with the lower bed-driven pair at
   each angle.
5. Do not retape or re-register during the program.

## Risks and follow-up

- Physical results remain unknown until both programs are printed. A
  zero-anchored patch must show tonal frequency/depth without ink-edge contact;
  the equidistant patch is the strict-spacing control.
- The `234 x 142 mm` matrix leaves a substantial outer margin, so a localized
  follow-up can still target the same sheet without automatic retaping.
- If only the lower Xtheta/Ytheta half fails, the result localizes the
  remaining defect to motion following, compensation, or machine dynamics
  rather than the shared generator geometry.

## Files

- `tools/make_cmyk_wave_coupon.py`: generates the combined sixteen-patch
  program.
- `software/tests/test_cmyk_wave_coupon.py`: validates all angles and modes.
- `samples/gcode/cmyk-wave-coupon.gcode`: complete parked and
  Xtheta/Ytheta diagnostic.
