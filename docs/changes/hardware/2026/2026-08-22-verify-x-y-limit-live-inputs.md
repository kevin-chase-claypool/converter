---
id: HW-20260822-001
date: 2026-08-22
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/testing/TEST_PLAN.md
  - RP23CNC X/Y limit inputs
tags:
  - limits
  - homing
  - safety
  - iosender
related:
  - docs/report/lab-notes/2026-08-22-f-04-x-y-limit-live-input-test.md
---

# Verify X/Y limit live inputs

## Summary

The installed X and Y NC limit switches now report correctly in the RP23CNC
ioSender Signals display: each axis is inactive released and active only while
its own switch is pressed.

## Reason

The project needed live controller evidence before any motion, homing, or
hard-limit protection depends on these inputs.

## Implementation

X and Y use `COM` to their respective `SIG` terminal and `NC` to `GND`.
The controller's limit inversion remains `$5=0`. Hard limits remain disabled
with `$21=0` because unused limit inputs have not yet been resolved.

## Verification

The owner meter-checked COM–NC contact behavior and individually operated both
switches while observing ioSender 2.0.47. X and Y each changed only with its
own pressed switch. The detailed procedure and limitations are in the F-04 lab
note.

## Struggles and rejected approaches

The compact ioSender Signals indicators were initially misread during the
interactive check. No inversion was applied; the verified final setting is
`$5=0`.

## Risks and follow-up

Do not enable hard limits yet. A deliberate alarm, open-circuit/broken-wire
behavior, homing, permanent moving-cable routing, and deterministic states for
unused Z/A inputs remain open.

## Files

- `docs/hardware/WIRING_TABLE.md`: records final X/Y endpoints and live-input
  evidence.
- `docs/testing/TEST_PLAN.md`: records F-04 as partial.
- `docs/report/lab-notes/2026-08-22-f-04-x-y-limit-live-input-test.md`:
  preserves bench procedure and result.
