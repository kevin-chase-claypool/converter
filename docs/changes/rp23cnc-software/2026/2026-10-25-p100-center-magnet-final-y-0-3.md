---
id: RPSW-20261025-004
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
  - RPSW-20261025-002
  - RPSW-20261025-003
  - 2026-10-25-p100-center-magnet-final-y-0-3
---

# Set the final P100 center correction to X 1.45 / Y 0.30

> Superseded by `RPSW-20261025-005`: after Y `0.30` was tested, the pen still
> needed another 1 mm north. The deployed final value is Y `1.30`.

## Summary

The final P100 axis-center correction is X `1.45 mm`, Y `0.30 mm`. The
controller was running the interim X `1.45`, Y `-0.70` source when the pen was
observed to need a further 1 mm north move.

## Reason

A positive P100 Y correction moves the registered origin north because the
`G10 L20` write subtracts the correction from `sensor_to_pen_y`. Starting from
the deployed Y `-0.70` and adding the required 1 mm north movement gives:

```text
Y = -0.70 + 1.00 = +0.30
```

X remains `1.45` from the measured 1 mm west correction. This supersedes the
incorrect Y `1.30` source calculation, which assumed the older Y `0.30` macro
was still deployed.

## Implementation

- `P100.macro` now sets:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = 0.3`
- The G10 registration write is:

```text
G10 L20 P1 X-1.45 Y-29.7892
```

- The homing-macro validator pins both final values.

## Verification

- `python tools\check_macros.py`: all 17 macros parse-safe.
- `python tools\validate_homing_macro.py`: P100/P115 contract passes.
- The controller listing showed deployed P100 at 15,218 bytes, matching the
  superseded X `1.45`, Y `-0.70` source before this final correction.
- Controller upload and physical registration remain pending.

## Struggles and rejected approaches

- Updating Y from `0.30` to `1.30` assumed the original controller file was
  still active. The FTP listing disproved that assumption.
- Decreasing Y moved the pen farther south and was rejected.
- Artwork offsets remain unrelated to P100 registration.

## Risks and follow-up

- Upload the final `P100.macro` and run `G65 P113`.
- Verify the pen parks centered over the embedded magnet.
- Rotate the bed with the magnet under the lifted pen. If the center changes
  with angle, a constant correction cannot remove the residual.

## Files

- `firmware/grblhal/macros/P100.macro`: final registration constants.
- `tools/validate_homing_macro.py`: pinned final regression values.
- `firmware/README.md`, `firmware/grblhal/macros/README.md`, and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: current-state values.
- `docs/report/lab-notes/2026-10-25-p100-center-magnet-final-y-0-3.md`:
  final measurement arithmetic and acceptance.
