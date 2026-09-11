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
- Static macro validation: pending after the early-gate correction.
- Hardware execution: pending; required command sequence is Q2 then Q5.

## Risks and follow-up

Q5 commands automatic X/Y motion. Run it only with X/Y clear, slow rates, and
observation. It supplies no G54/A registration result.
