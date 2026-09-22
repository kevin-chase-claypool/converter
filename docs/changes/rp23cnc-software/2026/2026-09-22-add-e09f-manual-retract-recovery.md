---
id: RPSW-20260922-010
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
  - n20
  - retract
  - recovery
  - safety
related:
  - RPSW-20260922-009
---

# Add E-09F manual retract recovery

## Summary

E-09F now has a guarded 5 ms manual UP/retract command that remains available
after an automatic-test fault.

## Reason

The pre-fix release fault left the pen pressing on the scale and the sketch had
no direct recovery motion command. An operator must always be able to retreat
from the fixture without relying on an automatic state transition.

## Implementation

- Added Serial Monitor `u` / `UP`.
- It cancels automatic activity, clears arming, checks ULT and GP2, drives one
  5 ms UP pulse, sleeps the driver, and reports completion.
- It is intentionally available from the FAULT state.

## Verification

- `arduino-cli compile --build-path work\\e09f-manual-up-build --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e09f_cs1238_guarded_force_hold` produced the UF2 artifact.
- No post-flash physical recovery is claimed.

## Struggles and rejected approaches

Requiring a new automatic `c` clear attempt after a fault was rejected because
it can be unavailable by design and leaves the operator without a direct,
bounded retreat action.

## Risks and follow-up

The physical 6 V cutoff remains the emergency action. Reflash E-09F, use `u`
only until clear, then re-tare before any further automatic test.

## Files

- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino`: recovery command.
- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/README.md`: recovery procedure.
