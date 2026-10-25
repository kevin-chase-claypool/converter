---
id: RPSW-20261025-006
date: 2026-10-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - tools/validate_homing_macro.py
  - firmware/grblhal/macros/controller-manifest-2026-10-25.txt
tags:
  - grblhal
  - p100
  - registration
  - center-magnet
  - pen-center
  - ftp
related:
  - RPSW-20261025-005
  - 2026-10-25-p100-center-magnet-y-1-01-deployed
---

# Deploy the final P100 Y correction at 1.01 mm

## Summary

The P100 center correction is now X `1.45 mm`, Y `1.01 mm`. After Y `1.30`
tested almost centered, the pen required a final 0.29 mm move south.

## Reason

A positive P100 Y correction moves the registered origin north. The requested
southward adjustment subtracts 0.29 mm:

```text
1.30 - 0.29 = 1.01 mm
```

X remains `1.45` because no additional east/west correction was requested.

## Implementation

- `P100.macro` sets:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = 1.01`
- Final registration write:

```text
G10 L20 P1 X-1.45 Y-30.4992
```

- The homing-macro validator pins both values.

## Verification

- `python tools\check_macros.py`: all 17 macros parse-safe.
- `python tools\validate_homing_macro.py`: P100/P115 validation passed.
- Binary FTP upload returned `226 Closing data connection`.
- Controller listing reports `P100.macro` at 15,244 bytes, matching local.
- Local SHA-256:
  `05C52C0C335D2F322B5699D793182DB1F967879EC811E9732845C576C13A73EF`.

## Risks and follow-up

- Run `G65 P113` and verify the parked pen is centered over the embedded
  magnet.
- Rotate the bed with the magnet under the lifted pen. If centering changes
  with angle, record the A0/A180 behavior instead of adding another constant.

## Files

- `firmware/grblhal/macros/P100.macro`: final registration constants.
- `tools/validate_homing_macro.py`: pinned final values.
- `firmware/grblhal/macros/controller-manifest-2026-10-25.txt`: deployed size.
- Current-state firmware and homing documentation.
- `docs/report/lab-notes/2026-10-25-p100-center-magnet-y-1-01-deployed.md`.
