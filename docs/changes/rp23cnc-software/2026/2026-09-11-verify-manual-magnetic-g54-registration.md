---
id: RP23-20260911-023
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/macros/P112.macro
  - G54 work coordinate system
tags:
  - g54
  - magnetic-registration
  - tmag
  - index-magnet
related:
  - docs/report/lab-notes/2026-09-11-p100-q5-centroid-survey-plan.md
---

# Verify Manual Magnetic G54 Registration

## Summary

The active G54 frame is physically verified: X0/Y0 is the pen at the center
magnet and A0 is the outer index magnet.

## Reason

P112 had already stopped TMAG at the physically verified index, where a manual
G54 A0 write succeeded. The center-magnet and installed pen-offset relationship
needed the corresponding stationary write and physical pen-tip inspection.

## Implementation

After a successful Q5 returned TMAG to the calculated center,
`G10 L20 P1 X0 Y-29.4892` recorded the measured pen-minus-TMAG offset. The
subsequent `G54 G0 X0 Y0` is the controlled park that puts the pen at center.
No macro source was unlocked or altered.

## Verification

- Q5 stopped at `MPos:-232.125,-218.325,A17281.142`.
- `$#` reported `G54:-232.126,-188.835,0.000,17281.142` after the stationary
  XY write.
- `G54 G0 X0 Y0` completed without alarm.
- Operator visually confirmed the pen tip exactly centered on the center
  magnet.

## Struggles and rejected approaches

The existing P100 Q0/Q3/Q4 body was not enabled because it does not yet use the
verified P111/Q5/P112 sequence and still contains stale outer-index geometry.

## Risks and follow-up

Build and supervised-test a new automated registration path that runs P111,
Q5, and P112, performs these two verified G54 writes, and parks at G54 X0/Y0.
Do not invoke the locked P100 Q0/Q3/Q4 modes.

## Files

- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: records the active,
  physically verified G54 semantics.
- `firmware/grblhal/macros/README.md`: updates the macro-operation boundary.
- `docs/integration/INTERFACES.md`: records the controller coordinate contract.
- `docs/report/lab-notes/2026-09-11-p100-q5-centroid-survey-plan.md`: preserves
  the bench evidence.
