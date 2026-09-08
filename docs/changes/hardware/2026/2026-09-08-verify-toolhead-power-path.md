---
id: HW-20260908-002
date: 2026-09-08
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - docs/hardware/WIRING_TABLE.md
  - firmware/pen_pressure
tags:
  - toolhead
  - power
  - d36v50f6
  - drv8833
  - e-14
related:
  - docs/testing/TEST_PLAN.md
---

# Verify toolhead power-path gates

## Summary

E-14, E-14B, E-14C, and E-15A passed. The D36V50F6 output measured a constant
6.05 V; the perfboard/DRV8833 inspection gates and the previously run
TMAG-related 5 V path test were reported passed.

## Reason

These gates are prerequisites for guarded actuator commissioning and establish
the powered toolhead path before testing force-control behavior.

## Implementation

Promoted the D36V50F6 input/output and toolhead power rows to verified where
the reported E-14 result applies. Updated the test plan and roadmap to reflect
the four passed gates.

## Verification

- Owner report, 2026-09-08: E-14 output constant at 6.05 V.
- Owner report: E-14B, E-14C, and prior TMAG-associated E-15A test passed.
- Existing supporting E-14B/E-14C evidence remains linked in the test plan.

## Struggles and rejected approaches

No new failure reported. E-15 is deliberately not inferred from the no-load
voltage result: loaded current, ripple, and temperature remain separate work.

## Risks and follow-up

Complete E-15 before loaded force-control work, then proceed through guarded
T-01 mechanical direction/travel checks.

## Files

- `docs/hardware/WIRING_TABLE.md`: current power-path status.
- `docs/testing/TEST_PLAN.md`: E-14/E-14B/E-14C/E-15A outcomes.
- `docs/project/ROADMAP.md`: passed phase-one gates.
- `docs/report/lab-notes/2026-09-08-e-14-toolhead-power-path.md`: evidence scope.
