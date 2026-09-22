---
id: RPSW-20260922-011
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09f_cs1238_guarded_force_hold
tags:
  - e-09f
  - cs1238
  - pen-clear
  - settling
related:
  - RPSW-20260922-009
  - RPSW-20260922-010
---

# Delay E-09F air-gap telemetry

## Summary

E-09F now waits 500 ms after its 100 ms air-gap UP pulse before it emits its
final CS1238 telemetry and `CLEAR_COMPLETE`.

## Reason

The fresh-tare E-09F sequence measured a valid clear band (`tare_delta=-2728`),
then visibly cleared the pen by about 1.75 mm. The sketch read the CS1238 in
the same millisecond as the motor stopped, obtained `tare_delta=-25545`, and
incorrectly faulted `air_gap_not_clear`.

## Implementation

- Added an explicit `AIR_GAP_SETTLE` state with a 500 ms no-motion wait.
- The final `AIR_GAP_SETTLED` CS1238 record is telemetry only. Clear was
  already proven before the fixed-duration air-gap movement, so this later
  sample cannot retroactively classify the completed movement as failed.
- Kept ULT/GP2 pre-UP protection, pulse limits, timeout, and driver sleep.

## Verification

- Source inspection confirms the final CS1238 read no longer occurs directly
  after `AIR_GAP_PULSE`.
- Firmware compilation and a repeat bench cycle are still required; the
  observed 1.75 mm physical gap is recorded in the E-09F lab note.

## Struggles and rejected approaches

Treating an immediate post-drive ADC reading as an air-gap sensor was rejected:
the ADC measures load-cell strain and needs time to settle, while the test had
already verified the low-force release condition before it applied the known
air-gap motion.

## Risks and follow-up

This remains temporary supervised firmware. Repeat clear cycles and retain the
full serial trace before enabling production M5 or GP27 behavior.

## Files

- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino`: delayed final telemetry state.
- `docs/report/lab-notes/2026-09-22-e-09f-guarded-force-hold.md`: observed false fault and physical-clear evidence.
