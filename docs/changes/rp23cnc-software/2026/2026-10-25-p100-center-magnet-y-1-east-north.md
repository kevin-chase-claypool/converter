---
id: RPSW-20261025-002
date: 2026-10-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: superseded
components:
  - firmware/grblhal/macros/P100.macro
  - tools/validate_homing_macro.py
tags:
  - grblhal
  - p100
  - registration
  - center-magnet
  - pen-center
  - offset
related:
  - RPSW-20261014-001
  - RPSW-20261014-002
  - 2026-10-25-p100-center-magnet-y-1-east-north
---

# Correct P100 center registration by −1 mm X/Y

> Superseded by `RPSW-20261025-003`: the operator clarified that the pen must
> move 1 mm north in Y, so the previously deployed Y `+0.30` correction becomes
> `+1.30`. X remains `+1.45`. This note records the temporary wrong-sign
> interpretation and was not deployed.

## Summary

The P100 registration constants now target the measured center-magnet
placement: X `1.45 mm` and Y `-0.70 mm`, reduced from `2.45 mm` and `0.30 mm`.
After a fresh `G65 P113`, the pen had parked `1.000 mm` east and `1.000 mm`
north of the embedded center magnet.

## Reason

The center-magnet check directly tests the intended P100 contract: `G54 X0 Y0`
must place the pen tip, not the TMAG sensor, at the center of the bed. A
positive X correction moves the registered origin east and a positive Y
correction moves it north. Because the observed origin was already 1 mm too far
in each positive direction, both corrections decrease by 1 mm.

This is separate from the artwork placement values. Those only place an image
inside the registered bed frame and cannot correct a physical registration
error.

## Implementation

- `P100.macro` now sets:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = -0.7`
- The dated P100 comment records the direction, delta, and subtraction rule.
- The homing-macro validator pins both new values so they cannot be dropped
  silently.

## Verification

- `python tools\check_macros.py`: all 17 macros parse-safe.
- `python tools\validate_homing_macro.py`: P100/P115 validation passed.
- Repository P100 source: 15,218 bytes, SHA-256
  `11DBE7A25408496B0A77B79EA0B7FAB76DF836B05A0783C32DBB515544E964A2`.
- Controller deployment is not yet complete. The FTP endpoint at
  `10.10.10.2:21` timed out from the workstation, so no remote file was
  changed.

## Struggles and rejected approaches

- Artwork offset X/Y was considered explicitly and rejected because it shifts
  the drawing inside the already-registered bed frame; it cannot correct the
  pen-center reference.
- Increasing both axis-center corrections by 1 mm would move the pen farther
  east and north, the wrong direction.
- Changing `sensor_to_pen` would produce the same G54 translation but would
  label a registration-frame error as pen/TMAG geometry. The center-magnet
  test is a registration-frame measurement, so the axis-center constants remain
  the correct owner.

## Risks and follow-up

- Upload `P100.macro` to the controller and rerun `G65 P113`.
- Require the parked pen tip to land centered on the embedded magnet.
- Confirm the magnet stays centered while rotating the bed. If the error
  changes with angle, a constant correction is insufficient and the off-axis
  magnet/runout attribution test is still required.

## Files

- `firmware/grblhal/macros/P100.macro`: corrected constants and dated comment.
- `tools/validate_homing_macro.py`: pinned regression values.
- `firmware/README.md`, `firmware/grblhal/macros/README.md`, and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: current-state values
  and deployment status.
- `docs/report/lab-notes/2026-10-25-p100-center-magnet-y-1-east-north.md`:
  measurement and pending physical verification.
