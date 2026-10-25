---
id: RPSW-20261025-005
date: 2026-10-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: superseded
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
  - RPSW-20261025-003
  - RPSW-20261025-004
  - 2026-10-25-p100-center-magnet-y-1-3-deployed
---

# Set and deploy the final P100 Y correction to 1.30

> Superseded by `RPSW-20261025-006`: after Y `1.30` tested almost centered,
> a final 0.29 mm south adjustment produced Y `1.01`.

## Summary

After P100 Y was set to `0.30`, the center-magnet check showed that the pen
still needed another 1 mm northward movement. The final deployed correction is
X `1.45 mm`, Y `1.30 mm`.

## Reason

A positive P100 Y correction moves the registered origin north. Adding the
next 1 mm movement to Y `0.30` gives Y `1.30`. X was already correct at `1.45`
and remains unchanged.

## Implementation

- `P100.macro` sets:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = 1.3`
- Final registration write:

```text
G10 L20 P1 X-1.45 Y-30.7892
```

- `tools/validate_homing_macro.py` pins both final values.

## Verification

- `python tools\check_macros.py`: all 17 macros parse-safe.
- `python tools\validate_homing_macro.py`: P100/P115 validation passed.
- Binary FTP upload returned `226 Closing data connection`.
- Controller listing reports `P100.macro` at 15,228 bytes, matching the local
  source size.
- Local source SHA-256:
  `C3AE0A5B6E8112A93CE09855437A423834618578663C4D34D2B61849CC7AECEB`.

## Struggles and rejected approaches

- Y `0.30` was close but still about 1 mm south.
- Y `-0.70` was the earlier interim source and is discarded.
- X and artwork offsets were not changed for this final Y correction.

## Risks and follow-up

- The upload is verified by FTP status and matching remote/local file size.
- Run `G65 P113` and verify the parked pen is centered over the embedded
  magnet.
- Rotate the bed with the magnet under the lifted pen and require it to remain
  centered. If it does not, the remaining error is angle-dependent.

## Files

- `firmware/grblhal/macros/P100.macro`: final center-correction constants.
- `tools/validate_homing_macro.py`: pinned final values.
- `firmware/grblhal/macros/controller-manifest-2026-10-25.txt`: deployed size.
- Current-state firmware and homing documentation.
- `docs/report/lab-notes/2026-10-25-p100-center-magnet-y-1-3-deployed.md`.
