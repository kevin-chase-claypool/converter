---
id: RPSW-20260911-003
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
tags:
  - P100
  - Q3
  - scan-bounds
  - G53
  - safety
related:
  - RPSW-20260911-002
---

# Record P100 Q3 Candidate Scan Rectangle

## Summary

P100 now records a measured, 100 × 100 mm candidate G53 rectangle for the
future Q3 center-magnet raster. Q3 remains error-39 locked.

## Reason

After Q2 homing was verified, the operator jogged the TMAG sensor to four
corners around the center magnet and supplied the G54 DRO coordinates. The
current G54 offset was then read back before conversion, eliminating any
assumption about the active coordinate system.

## Implementation

The source stores X `-280.000..-180.000` and Y `-266.000..-166.000` as the
candidate G53 bounds. The macro validator now verifies numeric assignments,
100 mm dimensions, ordering, and at least 20 mm clearance inside the proven
X `-455..0` and Y `-446..0` machine envelope. It does not release the Q3 lock
or assign a row pitch/feed.

## Verification

- G54 readback: `[G54:-232.900,-191.200,0.000,0.000]`.
- Jogged G54 corners: X `-47.100..52.900`, Y `-74.800..25.200`.
- Conversion: MPos = WPos + WCO, yielding X `-280.000..-180.000`, Y
  `-266.000..-166.000`.
- `python tools\\validate_homing_macro.py`: pending after this source update.

## Struggles and rejected approaches

The DRO coordinate values were not copied directly into P100 because Q3 uses
`G53` machine moves. The G54 offset was explicitly read before conversion.

## Risks and follow-up

The rectangle describes where motion may later be allowed, not a safe raster
program. Q3 remains locked until a row pitch, feed, magnetic corner-baseline
test, and observed first-pass plan are approved.

## Files

- `firmware/grblhal/macros/P100.macro`: candidate G53 rectangle.
- `tools/validate_homing_macro.py`: rectangle range and dimension checks.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: coordinate evidence.
- `docs/report/lab-notes/2026-09-11-p100-q3-candidate-rectangle.md`: bench record.
