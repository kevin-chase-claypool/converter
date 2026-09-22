---
id: RPSW-20260922-015
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - DRV8833 GP4/GP5 phase selection
tags:
  - motor-direction
  - gp2
  - supervised-bench
related:
  - RPSW-20260922-014
  - E-09E
---

# Correct integrated motor-direction polarity

## Summary

Corrected the integrated controller's lift/seek phase selection after its first
supervised boot timed out before reaching the GP2 lift-home switch.

## Reason

The standalone E-09E direction check established IN1 HIGH/IN2 LOW as DOWN and
IN1 LOW/IN2 HIGH as UP. The integrated configuration selected the opposite
phase for `motorLift()` and `motorSeek()`.

## Implementation

`LIFT_USES_IN1_PWM` is now `false` and `SEEK_USES_IN1_PWM` is now `true`,
matching the installed motor wiring and E-09E evidence. The bounded timeout
fault remains in place.

## Verification

The corrected integrated sketch compiled successfully for
`rp2040:rp2040:sparkfun_promicrorp2350`. The pre-correction fault is recorded
in the linked lab note; the corrected binary must be flashed before retrying.

## Struggles and rejected approaches

The first integrated boot was initially interpreted as a possible GP2 or
mechanical issue. Comparing the phase constants with the already validated
E-09E sketch identified the polarity mismatch, so no hardware rewiring was
performed.

## Risks and follow-up

Do not clear or retry the old binary. Flash the corrected sketch and perform
one boot plus one supervised M3/M5 cycle with the physical cutoff reachable.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: corrected
  DRV8833 phase selection.
- `docs/report/lab-notes/2026-09-22-integrated-direction-polarity-fault.md`:
  failed boot and corrective evidence.
