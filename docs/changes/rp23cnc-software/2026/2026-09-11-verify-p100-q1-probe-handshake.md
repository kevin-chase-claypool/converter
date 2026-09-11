---
id: RPSW-20260911-001
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - P100 Q1
  - GP27/U3 probe return
tags:
  - p100
  - q1
  - probe
  - gp27
  - safety
related:
  - RPSW-20260910-001
---

# Verify P100 Q1 probe handshake

## Summary

The motor-inert P100 Q1 macro automatically verified both the GP27/U3 PRB
assertion and release at the installed RP23CNC PROBE SIG endpoint.

## Reason

Manual U3/output testing had to distinguish a released pull-up voltage from an
actual GP27/U3 low-side assertion before any physical rework was considered.

## Implementation

No firmware or wiring was changed. P105 provided a long asserted interval for
meter observation; P100 Q1 then exercised the same command path and tested the
controller-visible PRB state.

## Verification

- P105 READY_ACK measured 173.4 mV from PROBE SIG to PROBE GND.
- P105 release returned P to blank.
- G65 P100 Q1 reported P100 Q1 readiness handshake passed and ok.
- The output state changed Pn:ZA -> Pn:ZAP -> Pn:ZA.

## Struggles and rejected approaches

An attempted voltage reading while telemetry was DISARMED baseline=0 arm=1
could not assert GP27 because the diagnostic intentionally requires its
far-field baseline before arming. That state was corrected by releasing Aux0
and waiting for baseline=1; resoldering was not performed.

## Risks and follow-up

Q2–Q4 remain locked. Their homing, magnetic-motion, and coordinate behavior
must be commissioned independently with the existing safety limits.

## Files

- docs/report/lab-notes/2026-09-11-p100-q1-prb-handshake.md: bench evidence.
- firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md: Q1 availability.
- docs/hardware/WIRING_TABLE.md: installed probe-return status.
