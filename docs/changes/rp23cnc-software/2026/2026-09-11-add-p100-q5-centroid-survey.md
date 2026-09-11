---
id: RPSW-20260911-006
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
tags:
  - P100
  - Q5
  - centroid
  - raster
  - safety
related:
  - RPSW-20260911-005
---

# Add P100 Q5 Centroid Survey

## Summary

Added Q5 as the first automatic, non-registering center-magnet raster stage.
It stops with the TMAG at its calculated centroid and leaves G54/A unchanged.

## Reason

The operator authorized automatic motion inside the measured safe rectangle,
but the first raster must provide evidence before coordinate registration or
index-magnet motion.

## Implementation

Q5 shares the established P100 chord-validation raster but returns immediately
after its G53 centroid approach. Its return occurs before `G10`, G54 use, or
the A-index branch. Q2 remains a separate required prior home stage; Q0/Q3/Q4
remain locked.

## Verification

- The first controller Q5 attempt correctly returned error 39 with the old
  early-lock message and made no move. It revealed that the early gate still
  rejected Q5 before it could reach the new survey body.
- The next Q5 attempt reached `MPos:-280.000,-266.000` inside the candidate
  rectangle, then safely aborted before a raster row because READY was absent.
  Q5 now performs Q1's forced-release baseline and uses a two-second READY wait.
- The following attempt reached a real magnetic entry at
  `MPos:-232.863,-236.000`, then soft-limit protection rejected the next move.
  The cause is confirmed: grblHAL exposes `#5061` in G54 work coordinates
  while the raster uses G53. Entry/exit values now convert with `+ #5221`.
- Static macro validation: pending after the baseline correction.
- Hardware execution: pending; required command sequence is Q2 then Q5.

## Risks and follow-up

Q5 commands automatic X/Y motion. Run it only with X/Y clear, slow rates, and
observation. It supplies no G54/A registration result.

The first valid chord measured 36.687 mm at Y `-226.000`; the provisional
25 mm ceiling rejected it safely. The candidate ceiling is now 50 mm for the
next observed pass.
