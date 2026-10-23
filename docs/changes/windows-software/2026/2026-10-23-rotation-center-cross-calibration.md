---
id: WSW-20261023-002
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/rotation_calibration.py
  - software/tests/test_rotation_calibration.py
  - tools/make_rotation_center_calibration.py
  - tools/fit_rotation_center.py
  - samples/gcode/rotation-center-calibration.gcode
tags:
  - theta
  - center
  - registration
  - precision
  - calibration
---

# Rotation-centre cross calibration and P100 correction fit

## Summary

Added a pen test that measures the rotating bed's residual X/Y centre offset
with two orthogonal cross arms, plus a least-squares fitter that converts the
90/180/270-degree readings into replacement P100
`axis_center_correction_x/y` constants. The correction remains in P100; the
converter does not apply a second artwork-space offset.

## Reason

The operator observed that portions of a print drawn in opposite bed quadrants
separate even though they belong to the same artwork. That matches the known
returned-bed error `e(theta) = C - R(-theta)C` from a registered origin that is
a small vector `C` away from the true rotation axis. A half-turn makes the
displacement `2C`, while 90 and 270 degrees expose the two perpendicular
components with opposite X signs. A single line replay could measure only one
component at a time and did not provide a repeatable way to calculate both
P100 constants.

## Implementation

- `tools/make_rotation_center_calibration.py` and
  `samples/gcode/rotation-center-calibration.gcode` draw a 330.2 mm reference
  cross at A=0, a control, and 310.2/300.2/290.2 mm cross replays at
  90/180/270 degrees, followed by a 280.2 mm closing A=0 pass. The layout is
  13 inches (330.2 mm) across on 14-inch (355.6 mm) round stock, leaving
  12.7 mm to the stock edge. The reference arrows point machine +X/+Y; every
  other cross is shorter so its angle remains identifiable where the crosses
  overlap.
- The replays use the same bed-frame cross transformed about G54 zero. The bed
  returns to A=0 before the sheet is read. A replay cross minus the reference
  cross is the measured `DX,DY` shift for that angle.
- Pen-up indexing uses fed `G1 (travel)` moves with both the configured XY
  travel rate and A-rate cap applied, so the diagnostic introduces no bare
  `G0` bed rotation.
- `tools/fit_rotation_center.py` reads the current constants from
  `P100.macro`, fits the two-component centre offset, reports model residual,
  and prints replacement constants. It does not edit or flash the macro.
- `software/converter_core/rotation_calibration.py` owns the reusable geometry,
  fitting, P100 parsing, and G-code construction.

## Verification

- New tests cover the half-turn doubling `e(180)=2C`, exact recovery from
  synthetic 90/180/270 measurements, a two-axis half-turn measurement,
  non-centre residual detection, P100 parsing, sign-preserving correction,
  pass ordering, arm-length checks, indexed A values, and malformed input.
- `python -m unittest discover -s software\tests -p test_rotation_calibration.py -v`
  passes 15 tests with Python 3.13.13.
- `python tools\make_rotation_center_calibration.py` generated the committed
  116-line sample with six length-coded crosses.
- `python tools\check_gcode_motion.py
  samples\gcode\rotation-center-calibration.gcode --strict` passes: 0 degrees
  of A motion in every drawing move, 0 A rate, and no bare `G0` rotation.
- A synthetic reading of `90,0.6,-0.6`, `180,0,-1.2`, `270,-0.6,-0.6`
  recovers `C=(0,-0.6)` mm with zero model residual and changes the current
  P100 Y correction from 0.3 to -0.3 mm as expected.

## Struggles and rejected approaches

- The first fit equations used the wrong sign for the sine term and recovered
  only half of the Y centre component. A synthetic round-trip test caught it;
  the encoded equation and least-squares coefficients now agree.
- A one-line replay cannot give both X and Y offsets without a second run. The
  cross test gives both components in one stable pattern.
- Rejected adding a second correction stage to the converter. P100 owns the
  G54 registration and already contains the two centre constants; duplicating
  them would double-compensate every rotated drawing.
- Rejected applying a fitted correction when the centre model leaves a large
  residual. That signature belongs to bed-plane or bearing-runout error, where
  two constants cannot improve every angle.

## Risks and follow-up

- The pattern is implemented but not yet bench-read. The next milestone is to
  run it after `G65 P113`, measure the three replay crosses against the
  reference, and record the fitted constants in a lab note.
- Photograph or scan the sheet straight down; line-width and pen choice limit
  the readable offset more than the model does. Use the finest pen available.
- If model residual exceeds 0.20 mm, investigate bed plane/runout before
  changing P100. Re-register and repeat after every centre-magnet, pen/TMAG,
  rotation-axis, or bed-plane change.

## Files

- `software/converter_core/rotation_calibration.py`: geometry, fit, P100 parsing,
  and cross-program construction.
- `software/tests/test_rotation_calibration.py`: unit and program-generation
  coverage.
- `tools/make_rotation_center_calibration.py`: generator CLI.
- `tools/fit_rotation_center.py`: measurement-to-P100 fitter CLI.
- `samples/gcode/rotation-center-calibration.gcode`: ready-to-run pen test.
- `software/README.md`, `firmware/README.md`,
  `firmware/grblhal/macros/README.md`, `docs/testing/TEST_PLAN.md`:
  current-state workflow and acceptance criteria.
