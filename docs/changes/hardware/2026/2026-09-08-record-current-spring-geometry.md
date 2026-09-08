---
id: HW-20260908-003
date: 2026-09-08
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - toolhead compression spring
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - spring
  - t-01a
  - safety
related:
  - HW-20260908-002
---

# Record current spring geometry

## Summary

Recorded the assembled spring-seat separation as 20.37 mm unloaded and 1.95
mm at the lower housing endpoint, establishing an 18.42 mm motor-controlled
compression span. The housing applies 4.63 mm compression even without
external load.

## Reason

T-01A needs real geometry before actuator preload motion. The former spring’s
LIFT dimensions are explicitly superseded.

## Implementation

Added the values to the BOM, T-01A current-state guidance, and a dated lab
note. The 1.95 mm reading is explicitly recorded as the housing's
full-compression endpoint, not the free spring's `L_solid`; it is prohibited
as a working endpoint until separate coil-bind and housing-stop margins exist.

## Verification

Power-off measurements and annotated photographs: 25.00 mm free length outside
the housing, 20.37 mm assembled/unloaded spring-seat separation, and 1.95 mm
at the lower in-housing endpoint; `20.37 - 1.95 = 18.42 mm` available
compression span.

## Struggles and rejected approaches

Treating the housing full-compression endpoint as spring solid height or as an
operating endpoint was rejected: it does not establish clearance to coil bind
or to a housing hard stop.

## Risks and follow-up

Measure `L_lift`, `L_contact`, selected `L_min`, margin to the housing
endpoint, and retract direction before powered preload motion. Obtain
free-spring `L_solid` or its specification before final coil-bind margin or
force limits are assigned.

## Files

- `docs/hardware/BOM.md`: current spring measurement record.
- `docs/testing/TEST_PLAN.md`: T-01A partial geometry state.
- `docs/report/lab-notes/2026-09-08-t-01a-spring-geometry.md`: measurement record.
