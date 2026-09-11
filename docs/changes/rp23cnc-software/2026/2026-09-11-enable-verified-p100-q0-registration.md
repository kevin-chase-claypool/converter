---
id: RP23-20260911-024
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/macros/P111.macro
  - G54 work coordinate system
tags:
  - p100
  - g54
  - magnetic-registration
  - safety
related:
  - RP23-20260911-023
---

# Enable Verified P100 Q0 Registration

## Summary

P100 Q0 now uses the physically verified center and index survey workflow and
parks the pen at G54 X0/Y0 with the index magnet at G54 A0.

## Reason

The prior Q0 body had stale outer-index geometry, prematurely wrote XY G54,
and could not safely contain `$H`. Separate P111, Q5, and P112 runs provided
the required measured replacement behavior.

## Implementation

The ioSender routine is `G65 P111` followed by `G65 P100 Q0`. Q0 starts from a
released magnetic baseline, performs the Q5 center raster, defers all G54
writes, travels to the P112-proven G53 X-10.5 inboard index line, repeats the
two READY/scan-arm phases, captures two A footprints at 10,000 motor-degrees
per minute, applies the 4320 +/- 15 spacing gate, and trims to the second
observed center. Only then does it write A0, return TMAG to the center,
write X0/Y-29.4892, and park at X0/Y0/A0. Q3 and Q4 remain locked.

## Verification

- `python tools\validate_homing_macro.py` passes static flow, coordinate,
  lock, probe, and measured-parameter checks.
- No `$H` exists in P100; P111 remains the only homing macro.
- The first full Q0 run remains supervised hardware verification.

## Struggles and rejected approaches

The old Q0 path was not enabled: it used a stale work-coordinate outer radius
and nominal extrapolation, and it wrote XY G54 before the A survey had passed.

## Risks and follow-up

Copy P100 to SD, run P111, then run Q0 under supervision. Stop on any alarm,
unexpected homing, missing acknowledgement, or failed spacing check; do not
retry automatically. Verify the final pen-center and index references with
`$#` and physical inspection.

## Files

- `firmware/grblhal/macros/P100.macro`: verified Q0 implementation.
- `tools/validate_homing_macro.py`: static contract for Q0 geometry and order.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: operating procedure.
