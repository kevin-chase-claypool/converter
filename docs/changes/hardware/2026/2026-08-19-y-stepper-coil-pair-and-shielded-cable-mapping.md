---
id: HW-20260819-001
date: 2026-08-19
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/BOM.md
  - docs/testing/TEST_PLAN.md
tags:
  - y-axis
  - stepper
  - coil-pair
  - shielded-cable
  - wiring
related:
  - docs/report/lab-notes/2026-08-19-e-01-y-stepper-coil-pair-test.md
---

# Record Y Stepper Coil Pair and Shielded Cable Mapping

## Summary

Recorded the coil pairs for all three 17HS15 motors and the Y special
shielded-cable splice: every motor has black/green and red/blue coil pairs;
the Y cable continues them as black/green and red/white respectively.

## Reason

The Y motor has an already-installed shielded cable whose white conductor
replaces the motor-side blue color. The generic selected-cable entry was not a
sufficient physical wiring record for this axis; the other two motors also now
have direct coil-grouping evidence rather than manufacturer colors alone.

## Implementation

The master wiring table now records black-to-black, green-to-green,
red-to-red, and white-to-blue at the Y cable splice. The BOM identifies the
separate installed Y cable as Amazon ASIN B0DL9QCH1B. E-01 is partial: it now
has Y coil-grouping evidence but still requires resistance readings and X/A
confirmation.

## Verification

An unpowered hand-turn generated-voltage test performed by the project owner
identified the Y coil pairs. The result is recorded in the E-01 lab note.

## Struggles and rejected approaches

The prior generic cable record would have implied a blue cable conductor on
Y. It was not used for the installed harness; the recorded white-to-blue splice
prevents an incorrect color-for-color assumption during driver wiring.

## Risks and follow-up

The meter model, generated voltages, and winding resistances were not recorded.
Measure resistance before final driver connection and verify each axis's actual
motion direction during M-01/M-03. Do not treat this test as a powered motor or
driver test.

## Files

- `docs/hardware/WIRING_TABLE.md`: authoritative Y phase and splice mapping.
- `docs/hardware/BOM.md`: identifies the separate installed Y cable.
- `docs/testing/TEST_PLAN.md`: records E-01 partial completion.
- `docs/report/lab-notes/2026-08-19-e-01-y-stepper-coil-pair-test.md`: raw
  bench evidence.
