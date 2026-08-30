---
id: HW-20260830-003
date: 2026-08-30
category: hardware
affected_categories:
  - hardware
status: planned
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
fully compressed end condition.

## Reason

The observation informs whether the selected spring may overload the N20, but
must not be mistaken for a controlled stall, thermal, or force-capability test.

## Implementation

Added a dated raw lab note, a clearly bounded observation in the authoritative
test plan, and an engineering-log event. The next test is directed to use a
guarded working endpoint and controlled measurement setup.

## Verification

- Owner-reported current values recorded in the lab note.
- No component capability, pass condition, or firmware setting changed.

## Struggles and rejected approaches

Treating the 0.18 A reading as verified stall current or proof of motor margin
was rejected because the measurement method, spring compression, force, supply
limit, peak behavior, and thermal duration were not recorded.

## Risks and follow-up

Avoid full spring compression in normal operation. Complete T-01A, E-06,
T-01C, and T-01D before setting a controller limit or claiming reliable
retraction against preload.

## Files

- `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`:
  preliminary bench evidence and limitations.
- `docs/testing/TEST_PLAN.md`: links the observation to the T-01 gate.
- `docs/project/ENGINEERING_LOG.md`: records the partial milestone.
