---
id: RPSW-20260911-002
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
tags:
  - P100
  - homing
  - safety
  - grblHAL
related:
  - RPSW-20260911-001
---

# Enable Isolated P100 Q2 X/Y Homing

## Summary

`G65 P100 Q2` is now source-enabled as an isolated X/Y homing stage. Q0, Q3,
and Q4 remain hard-locked.

## Reason

The installed controller completed a direct `$H` cycle with X/Y fuses
installed, both home inputs proven individually, and Z/A excluded. The cycle
finished in `IDLE` with no alarm and reported the homed state. This is enough
evidence to expose the same controller operation through the staged macro, but
not enough to authorize magnetic raster or A-index motion.

## Implementation

The early Q2 branch sends `M5`, waits three seconds, executes `$H`, prints its
completion message, and returns before any Aux0, GP27, raster, or coordinate
registration code. The static validator now enforces the separate early Q2
branch and retains the Q0/Q3/Q4 locks.

## Verification

- Manual controller `$H` on 2026-09-11: completed with no alarm; final
  `MPos:-10.000,-436.000,0.000,0.000` and transient `H:1,3`.
- X and Y home inputs each changed from blank to asserted when their own
  switch was pressed.
- `python tools\\validate_homing_macro.py`: passed after this source update.
- Filesystem `G65 P100 Q2`: passed on 2026-09-11. The controller entered
  `Home`, reported `H:1,3`, returned `Idle` at
  `MPos:-10.000,-436.000,0.000,0.000`, then printed
  `P100 Q2 X/Y homing complete` and `ok`.

## Struggles and rejected approaches

The previous all-mode lock prevented Q2 even after direct controller homing
was demonstrated. Enabling the legacy shared body would unnecessarily expose
the Q2 call to later magnetic code, so the released path is an early return.

## Risks and follow-up

Q0, Q3, and Q4 remain unavailable; this change does not establish scan bounds,
G54 registration, A indexing, or production readiness.

## Files

- `firmware/grblhal/macros/P100.macro`: isolated Q2 stage gate.
- `tools/validate_homing_macro.py`: validates Q2 isolation and preserved locks.
- `firmware/README.md`: current commissioning status.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: mode availability.
- `firmware/grblhal/macros/README.md`: macro behavior and test boundary.
- `docs/testing/TEST_PLAN.md`: records direct `$H` evidence and next test.
