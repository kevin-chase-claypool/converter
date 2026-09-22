---
id: RPSW-20260922-008
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
  - force-hold
  - pen-clear
  - safety
related:
  - RPSW-20260922-007
  - docs/report/lab-notes/2026-09-22-e-09e-installed-pen-scale-direction.md
---

# Add E-09F guarded force-hold test

## Summary

Added a separate supervised automatic force-hold/clearance test that uses the
accepted precision-weight CS1238 profile without unlocking production M3/M5
behavior.

## Reason

Precision masses calibrate the CS1238 raw scale. E-09E verified the installed
pen's force sign and practical range, but it required manual pulses. The next
test must exercise bounded automatic correction and the staged air-gap motion
before production code can be authorized.

## Implementation

- E-09F seeks/holds the calibrated 40–60 g raw band using only 5 ms pulses,
  500 ms settling, per-direction 30-pulse budgets, a 30 s timeout, and a raw
  70 g hard limit.
- Its explicit clear command releases to the 3 g raw band before one 100 ms
  candidate air-gap pulse.
- It uses service UART1, ULT fault sensing, GP2 pre-UP check, and sleeps the
  driver after every pulse.
- It does not configure GP29/M3/M5, GP27, magnetic logic, or drawing behavior.

## Verification

- `arduino-cli compile --build-path work\\e09f-guarded-force-hold-build --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e09f_cs1238_guarded_force_hold` produced its UF2 artifact.
- No powered E-09F run is claimed.

## Struggles and rejected approaches

Enabling the integrated controller directly was rejected: its continuous PWM
hold behavior has not been characterized with this mechanism. E-09F limits
each automatic correction to the measured 5 ms resolution instead.

## Risks and follow-up

The 40–60 g band and 100 ms air-gap value remain bench candidates. Run E-09F
with the physical cutoff reachable, then record its scale range, raw telemetry,
correction count, clearance gap, and any fault before considering production
gate changes.

## Files

- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/`: bounded test firmware and procedure.
- `firmware/pen_pressure/README.md`: sketch inventory.
- `docs/integration/INTERFACES.md`: temporary UART/test contract.
- `docs/testing/TEST_PLAN.md`: E-09F pass criteria.
