---
id: RPSW-20260912-001
date: 2026-09-12
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P113.macro
  - firmware/README.md
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
  - firmware/grblhal/macros/README.md
  - docs/integration/INTERFACES.md
  - docs/project/ROADMAP.md
tags:
  - P113
  - P100
  - P111
  - homing
  - magnetic-registration
  - G54
related:
  - RPSW-20260911-013
---

# Record P113 unified registration command

## Summary

Corrected current-state documentation to identify P113 as the verified unified
`HOME + REGISTER` command, rather than presenting P111 followed by P100 Q0 as
the production ioSender routine.

## Reason

P113 is the current verified wrapper: it performs M5, the fixed dwell, the one
physical X/Y `$H`, and then P100 Q0. Earlier documentation retained staging
language from before this wrapper was verified, which made the operational
entry point ambiguous.

## Implementation

The firmware, macro, interface, and roadmap documents now consistently state
that ioSender uses `G65 P113` for normal supervised home and registration.
P111 remains the isolated physical-home macro used by diagnostic and survey
stages; P100 remains free of `$H` and owns the registration portion.

## Verification

- Confirmed `P113.macro` contains `M5`, `G4 P3.0`, `$H`, and `G65 P100 Q0` in
  that order.
- Ran `python tools\validate_homing_macro.py`: passed.
- The existing 2026-09-11 engineering-log evidence records the motor-inert
  P114 nested-macro check and the successful P113 hardware run with the pen
  centered at the final park.

## Struggles and rejected approaches

The stale two-command wording was retained in several current-state documents
after P113 verification. It is now reserved only for isolated commissioning
instructions where P111 or P100 stages are intentionally run independently.

## Risks and follow-up

P113 verifies pen-free home and magnetic registration. It does not authorize
direct printing: the toolhead M3/M5 electrical path, force/clearance tests, and
commissioning gates remain required.

## Files

- `firmware/README.md`: current motion-controller status and entry point.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: P113 ownership and Q0 status.
- `firmware/grblhal/macros/README.md`: macro operation instructions.
- `firmware/grblhal/macros/P100.macro`: identifies P113 as the production caller.
- `docs/integration/INTERFACES.md`: startup command contract.
- `docs/project/ROADMAP.md`: completed Phase 6 macro milestone.
- `docs/testing/TEST_PLAN.md`: M-10 production-command contract.
- `docs/p100-data-movement.html`: visual start-command contract.
