---
id: HW-20260904-005
date: 2026-09-04
category: hardware
affected_categories:
  - hardware
components:
  - toolhead
  - N20/1024GA20 actuator
  - docs/testing/TEST_PLAN.md
status: partial
tags:
  - toolhead
  - n20
  - current
  - alignment
  - testing
related:
  - HW-20260830-003
---

# Correct N20 Current After Lead-Screw Alignment and Preload Test

## Summary

The owner corrected the unloaded N20 motion-current result to **0.009 A** and
reported a bounded endpoint-stall test. At 6.0 V with a 0.20 A supply limit,
the motor retracted until it could travel no farther and pressed the LIFT_HOME
switch; the supply read 0.18 A for about 30 seconds, repeated 10 times. This
is not a measurement of current required to hold a selected spring preload.
The earlier 0.043 A toolhead reading included extra load from a lead screw that
was not nearly straight against the heat-set insert. The alignment has since
been corrected.

## Reason

The previous value was not a valid normal unloaded baseline because it mixed
motor motion with avoidable lateral heat-set friction. The corrected value is
needed for interpreting the N20's actual no-load behavior and power margin.
The controlled endpoint-stall result bounds the current observed at the switch-
pressed travel endpoint. It does not establish practical actuator capability at
a selected operating preload.

## Implementation

Updated the E-05/E-06 records and toolhead lab notes to distinguish the
corrected aligned unloaded current from the earlier misalignment-loaded
measurement, and to separate the switch-pressed endpoint stall from the still
open T-01C preload-hold test.

## Verification

- Owner reports corrected aligned unloaded N20 motion current: `0.009 A`.
- E-05 remains passed for stable unloaded motion at 6 V.
- The earlier 0.043 A reading is retained as historical evidence of an
  accidental alignment load, not the normal unloaded baseline.
- Bounded E-06 endpoint observation passed at 6.0 V / 0.20 A supply limit /
  0.18 A switch-pressed stall current, approximately 30 s dwell, and 10
  successful repeats.
- No known-compression operating-preload hold was measured; T-01C remains open.

## Struggles and rejected approaches

Using the earlier 0.043 A value as the normal unloaded motor current was
rejected after the owner identified lead-screw misalignment at the heat-set
insert as the source of the additional load.

## Risks and follow-up

The bounded result does not characterize operating-preload capability,
temperature, rail droop, driver-fault behavior, or long-duration endurance.
Retain the separate spring geometry and force-path gates, repeat T-01C at a
known safe compression, and complete T-01D/T-01E before setting production
travel or force-loop limits.

## Files

- `docs/testing/TEST_PLAN.md`: corrected E-05 current interpretation.
- `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`: records the
  alignment correction and preserves the earlier historical result.
- `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`:
  distinguishes unloaded current from spring-installed preload current.
- `docs/hardware/BOM.md`: records the current N20 baseline and remaining gates.
- `docs/report/lab-notes/2026-09-04-e-06-t-01c-n20-stall-preload-hold.md`:
  records the controlled stall/preload-hold test.
