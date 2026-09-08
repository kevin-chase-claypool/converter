---
id: HW-20260907-002
date: 2026-09-07
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
  - windows-software
status: verified
components:
  - RP23CNC/RP23U5XBB grblHAL settings
  - X/Y/A motion system
  - temporary G54 work reference
  - converter house-and-sun sample
tags:
  - m-03
  - m-06
  - m-07
  - soft-limits
  - g54
  - xya
related:
  - HW-20260906-004
  - HW-20260906-005
  - HW-20260906-006
---

# Verify converter motion and guarded X/Y envelope

## Summary

The operator revalidated `$100=80.00000` by caliper, enabled a conservative
X/Y software envelope, refreshed the temporary G54 reference after the Y
coordinate-frame change, and completed a pen-free converter-generated
house-and-sun X/Y/A run that returned exactly to both its XY center and A
reference.

## Reason

The earlier X calibration value and obsolete 508 mm travel entries did not
reflect the operator's final measured/caliper-selected X scale or conservative
safe travel distances. A converter-generated test was needed after establishing
the guarded working envelope and the temporary G54 reference.

## Implementation

The active settings are `$100=$101=80.00000`, `$130=455.000`, `$131=446.000`,
`$20=1`, and `$40=1`; hard limits remain disabled (`$21=0`). The new Y maximum
changed machine coordinates after `$H`, so the temporary pen-axis center was
re-established at machine position `(-232.900,-191.200)` and assigned G54
`X0 Y0`. The manually chosen A reference remains G54 `A0` only for pen-free
work.

## Verification

- `$H` completed with `H:1,3` at `MPos:-10.000,-436.000,0.000,0.000`.
- The pen-free `kindergarten-house-sun.gcode` completed with no reported
  motion or skipped-step symptom.
- `G90`, `G54`, `G0 X0 Y0 A0` returned the pen axis and bed exactly to their
  manually established references.
- On 2026-09-08, the pen-free `m06-radius-sweep.svg` converter run reportedly
  completed every path perfectly; the same explicit G54 return landed X, Y,
  and A exactly on their reference marks. No elapsed times were captured.

## Struggles and rejected approaches

The previous `$100=79.71303` result came from an earlier calibration
interpretation. It is superseded by the owner's later caliper verification of
`$100=80.00000`; no unmeasured interpolation is retained as the active setting.

## Risks and follow-up

The finite X/Y values are conservative software-envelope values, not verified
hard-stop coordinates. Test controller rejection/recovery near each X/Y
boundary and compare converter preview time with measured runtime for the
completed inner/middle/outer-radius M-06 sample. P100 magnetic
registration must replace the temporary G54 reference before production.

## Files

- `docs/report/lab-notes/2026-09-07-converter-house-sun-and-soft-limits.md`:
  bench evidence and exact observed scope.
- `docs/testing/TEST_PLAN.md`: current M-03, M-06, and M-07 status.
- `firmware/README.md`, `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`,
  `firmware/grblhal/config/build-record.md`, and `docs/integration/INTERFACES.md`:
  current machine-reference and configuration record.
- `docs/project/ENGINEERING_LOG.md`: chronological milestone.
