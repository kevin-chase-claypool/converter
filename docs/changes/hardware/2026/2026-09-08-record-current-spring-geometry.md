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

Recorded the replacement spring’s 20.37 mm installed/unloaded length and 1.95
mm reported full-compression length. The housing therefore applies 4.63 mm
compression even without external load.

## Reason

T-01A needs real geometry before actuator preload motion. The former spring’s
LIFT dimensions are explicitly superseded.

## Implementation

Added the values to the BOM, T-01A current-state guidance, and a dated lab
note. The 1.95 mm reading is explicitly recorded as the housing's
full-compression endpoint, not the free spring's `L_solid`; it is prohibited
as a working endpoint until separate coil-bind and housing-stop margins exist.

## Verification

Owner-reported power-off measurements: 25.00 mm free, 20.37 mm installed
unloaded, and a 1.95 mm full-compression endpoint within the housing.

## Struggles and rejected approaches

Treating the housing full-compression endpoint as spring solid height or as an
operating endpoint was rejected: it does not establish clearance to coil bind
or to a housing hard stop.

## Risks and follow-up

Measure free-spring `L_solid`, `L_lift`, `L_contact`, selected `L_min`, margins
to both coil bind and the housing endpoint, and retract direction before
powered preload motion.

## Files

- `docs/hardware/BOM.md`: current spring measurement record.
- `docs/testing/TEST_PLAN.md`: T-01A partial geometry state.
- `docs/report/lab-notes/2026-09-08-t-01a-spring-geometry.md`: measurement record.
