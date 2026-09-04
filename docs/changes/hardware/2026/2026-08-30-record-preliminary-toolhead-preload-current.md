---
id: HW-20260830-003
date: 2026-08-30
category: hardware
affected_categories:
  - hardware
status: partial
components:
  - toolhead
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - n20
  - preload
  - current
  - testing
related:
  - HW-20260830-001
---

# Record Preliminary Toolhead Preload Current

## Summary

Recorded the first reported N20 retract-current observation with the spring
installed: approximately 0.019-0.050 A in motion and 0.18 A at the reported
endpoint. The owner later clarified that 0.18 A is the observed N20 stall
current and that the motor holds the selected spring preload.

## Reason

The observation informs whether the selected spring may overload the N20, and
the follow-up clarification provides qualitative preload-hold evidence. It
must not be mistaken for a complete electrical, thermal, or force-envelope
qualification without the missing test conditions and dwell measurements.

## Implementation

Added a dated raw lab note, a clearly bounded observation in the authoritative
test plan, and an engineering-log event. The next test is directed to use a
guarded working endpoint and controlled measurement setup.

## Verification

- Owner-reported current values recorded in the lab note.
- The test-plan interpretation was updated to record the owner-reported stall
  current and preload hold while leaving formal E-06/T-01C acceptance open.

## Struggles and rejected approaches

Treating the 0.18 A reading as a complete E-06 pass was rejected because the
measurement method, spring compression, force, supply limit, peak behavior,
stall duration, and thermal duration were not recorded. The owner's statement
that the motor holds preload is retained as qualitative T-01C evidence, not a
formal dwell/temperature pass.

## Risks and follow-up

Avoid full spring compression in normal operation. Complete T-01A, the
controlled portion of E-06, and the measured T-01C/T-01D evidence before
setting a controller limit or claiming a qualified continuous preload hold.

## Files

- `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`:
  preliminary bench evidence and limitations.
- `docs/testing/TEST_PLAN.md`: links the observation to the T-01 gate.
- `docs/project/ENGINEERING_LOG.md`: records the partial milestone.
