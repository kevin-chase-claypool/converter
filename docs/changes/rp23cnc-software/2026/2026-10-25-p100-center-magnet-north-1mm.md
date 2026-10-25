---
id: RPSW-20261025-003
date: 2026-10-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
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
  - RPSW-20261025-002
  - 2026-10-25-p100-center-magnet-north-1mm
---

# Move the P100 registered pen 1 mm north

## Summary

The P100 axis-center correction now uses X `1.45 mm` and Y `1.30 mm`. This
encodes a center-magnet check requiring the registered pen position to move
1 mm west in X and 1 mm north in Y from the previously deployed correction of
X `2.45`, Y `0.30`.

## Reason

The earlier 2026-10-25 interpretation incorrectly treated “pen is 1 mm north”
as a requirement to move the pen south. The operator clarified that the pen
must move **north** by 1 mm. A positive P100 Y correction moves the registered
origin north because `G10 L20` subtracts the correction from
`sensor_to_pen_y`.

This correction belongs to the center-registration frame, not the artwork
placement offsets.

## Implementation

- `P100.macro` now sets:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = 1.3`
- The dated comment records that X moves the origin 1 mm west and Y moves it
  1 mm north from the prior deployed constants.
- The homing-macro validator pins both new values.
- The earlier Y `-0.70` source change is marked superseded; it was never
  deployed to the controller.

## Verification

- `python tools\check_macros.py`: all 17 macros parse-safe.
- `python tools\validate_homing_macro.py`: P100/P115 contract passes with the
  new pinned constants.
- Controller deployment remains pending because FTP to `10.10.10.2:21` timed
  out from the workstation.
- Physical acceptance remains pending: upload the macro, run `G65 P113`, verify
  the pen is centered over the embedded magnet, then rotate the bed and confirm
  the magnet remains centered.

## Struggles and rejected approaches

- Subtracting 1 mm from Y moved the origin south, opposite the corrected
  requirement.
- Returning Y to `0.30` would preserve the old registered position rather than
  moving the pen north.
- Artwork offset changes were rejected because they do not affect P100
  registration.

## Risks and follow-up

- If the pen remains off-center after deployment, record the exact ioSender DRO
  difference between the parked position and magnet-centered position.
- If centering changes with bed angle, a constant P100 correction cannot remove
  the residual and the magnet-versus-axis attribution remains required.

## Files

- `firmware/grblhal/macros/P100.macro`: corrected center-registration values.
- `tools/validate_homing_macro.py`: pinned regression values.
- `firmware/README.md`, `firmware/grblhal/macros/README.md`, and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: current-state values.
- `docs/report/lab-notes/2026-10-25-p100-center-magnet-north-1mm.md`:
  measurement and deployment status.
