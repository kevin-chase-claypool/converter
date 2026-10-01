---
id: RPSW-20261001-002
date: 2026-10-01
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/macros/P103.macro
  - tools/validate_homing_macro.py
  - tools/check_macros.py
  - samples/gcode/center-registration-check.gcode
tags:
  - grblhal
  - macro
  - p100
  - registration
  - calibration
  - drift
related:
  - RPSW-20260924-001
  - RPSW-20261001-001
  - docs/hardware/WIRING_TABLE.md
---

# Axis-centre correction in P100: the registered origin moves +1.25 mm in X

## Summary

`P100.macro` gains two named constants, `#<axis_center_correction_x> = 1.25` and
`#<axis_center_correction_y> = 0.0`, applied at the `G10 L20 P1` registration
write. They state how far, in machine X/Y, the registered origin must move to sit
on the bed's true rotation axis; the write subtracts them because the registered
origin is the centroid minus the written value.

The correction is reported, not measured: the operator observed the registered
origin landing 1.25 mm on the minus-X side of the axis. It is now **verified on
the machine**: with the correction in place, a magnet held directly under the
lifted pen stayed centred while the bed rotated, so the registered origin is on
the rotation axis. The test that attributes the error to an off-axis centre
magnet or a wrong pen/TMAG offset was deliberately skipped and remains open.

## Reason

"my magnetic homing was off by 1.25mm too far to the -x, how do i fix this in
perpetuity", then "we need to add -1.25mm in the x direction for the offset",
corrected to "POSITIVE X not negative".

Everything that registers is in P100: the survey finds the centre magnet's
centroid, and `G10 L20 P1 X[..] Y[..]` writes the work offset from
`#<sensor_to_pen_x>`/`y`. A constant 1.25 mm error cannot come from the survey -
the calibration record shows the X centroid reproducing to 0.013 mm - so it is a
constant in that chain.

## Implementation

- `P100.macro`: the two constants next to the other commissioning values, with
  the measurement date, the direction, and the pending attribution test in the
  comment block; the registration write is now
  `G10 L20 P1 X[[#<sensor_to_pen_x> - #<axis_center_correction_x>]] Y[[#<sensor_to_pen_y> - #<axis_center_correction_y>]]`.
- `P103.macro`: the whole-initialization diagnostic mirrors P100's assignments,
  so it carries the two new constants with dummy values like the rest.
- `tools/validate_homing_macro.py`: requires the correction constants and the new
  write form, so a future edit cannot drop the correction silently.
- `tools/check_macros.py` (new): parse-safety for every macro - a comment must
  open and close on one line and must not nest parentheses, expressions must
  balance, and every `if`/`while`/`sub` must close. It caught the author's own
  nested-parenthesis comment in this change before the file was committed, the
  same class of defect that made ioSender refuse the repeatability test.
- `samples/gcode/center-registration-check.gcode` plus
  `tools/make_center_check.py`: the acceptance test - a cross at `G54 X0 Y0`,
  half a bed revolution, the same cross again. Coincident crosses mean the
  origin is on the axis; a gap is twice the residual off-axis error.

## Verification

- `python tools\\check_macros.py` - all 17 macros parse-safe.
- `python tools\\validate_homing_macro.py` - P100/P115 validation passed,
  including the new required tokens.
- Two stale expectations in the validator were found and corrected while doing
  this, both left over from before the 2026-09-30 ratio work: it still expected
  P112's `a_expected_spacing` to be 4320 (the macro and the documented gate say
  4332) and `a_spacing_tolerance` to be 15 (documented and installed: 10). The
  validator had evidently not been re-run since that change.
- **Pending:** the physical acceptance test, and the two-survey attribution test.
- **Passed 2026-10-01:** the physical acceptance condition, by the operator's
  quicker equivalent - a magnet directly under the lifted pen stays centred while
  the bed rotates, which is what `center-registration-check.gcode` tests on
  paper. The two-survey attribution test was not run, at the operator's choice:
  the correction works either way, and the residue is recorded as an open item.

## Struggles and rejected approaches

- First attempt wrote the correction as `+ #<axis_center_correction_x>` and
  documented +1.25 as "add that back". Deriving the sign from the validator's own
  model (`origin = centroid - written`) and from the 2026-09-11 registration
  evidence showed that adding would move the origin the *wrong way*; the write
  subtracts, and the constant is stated as the distance the origin must move.
- Considered folding 1.25 into `#<sensor_to_pen_x>`. Rejected: that value is the
  measured pen/TMAG geometry, and the cause of this error is not yet known. Two
  different physical quantities in one constant is how the next calibration gets
  entered wrong.
- Considered having P100 survey at A0 and A180 and average them, which
  self-corrects an off-axis magnet with no constant at all. Deferred as a
  follow-up: it adds a second 100 mm raster to every registration.

## Risks and follow-up

- The direction and sign have been reasoned rather than measured on paper. The
  under-pen magnet check settles it: with the wrong sign the magnet would swing
  away from the pen as the bed turns, and it did not.
- A constant correction is valid only while the bed's registration attitude is
  repeatable (P100 registers A0 first, so it is) - re-seating the magnet would
  invalidate it.
- The `sensor_to_pen` comment in P100 describes the opposite sign to what the
  verified frame uses. That is now recorded in the macros README; a future
  calibration must keep the sign that lands the pen on `G54 X0 Y0`.
- `HOMING_AND_MAGNETIC_CALIBRATION.md` quotes `(0.000, -30.100)` while the macro
  carries `-29.4892`. The 0.61 mm difference is unresolved and is exactly the
  kind of drift that produces this class of error; it needs a fresh measurement.

## Files

- `firmware/grblhal/macros/P100.macro`: correction constants and write.
- `firmware/grblhal/macros/P103.macro`: mirror of the initialization.
- `firmware/grblhal/macros/README.md`: the correction, the pending attribution
  test, and the sign discrepancy.
- `tools/validate_homing_macro.py`, `tools/check_macros.py`: the guards.
- `tools/make_center_check.py`, `samples/gcode/center-registration-check.gcode`:
  the acceptance test.
