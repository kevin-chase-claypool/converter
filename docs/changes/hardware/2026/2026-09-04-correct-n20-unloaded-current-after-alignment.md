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

# Correct N20 Unloaded Current After Lead-Screw Alignment

## Summary

The owner corrected the unloaded N20 motion-current result to **0.009 A**.
The earlier 0.043 A toolhead reading included extra load from a lead screw
that was not nearly straight against the heat-set insert. The alignment has
since been corrected.

## Reason

The previous value was not a valid normal unloaded baseline because it mixed
motor motion with avoidable lateral heat-set friction. The corrected value is
needed for interpreting the N20's actual no-load behavior and power margin.

## Implementation

Updated the E-05 record and toolhead lab notes to distinguish the corrected
aligned unloaded current from the earlier misalignment-loaded measurement.
The spring-installed preload observation remains a separate result.

## Verification

- Owner reports corrected aligned unloaded N20 motion current: `0.009 A`.
- E-05 remains passed for stable unloaded motion at 6 V.
- The earlier 0.043 A reading is retained as historical evidence of an
  accidental alignment load, not the normal unloaded baseline.

## Struggles and rejected approaches

Using the earlier 0.043 A value as the normal unloaded motor current was
rejected after the owner identified lead-screw misalignment at the heat-set
insert as the source of the additional load.

## Risks and follow-up

The corrected unloaded value does not qualify the spring-loaded stall or hold
condition. Retain the separate 0.18 A stall/preload observation and complete
the controlled E-06 and T-01C/T-01D measurements with documented dwell, rail,
force, and temperature evidence.

## Files

- `docs/testing/TEST_PLAN.md`: corrected E-05 current interpretation.
- `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`: records the
  alignment correction and preserves the earlier historical result.
- `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`:
  distinguishes unloaded current from spring-installed preload current.
- `docs/hardware/BOM.md`: records the current N20 baseline and remaining gates.
