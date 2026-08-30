---
id: HW-20260830-004
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
  - spring
  - preload
  - lift
  - pen-stop
related:
  - HW-20260830-001
---

# Set Proposed Toolhead Lift Datum

## Summary

Recorded a proposed LIFT datum of 0.535 in spring compression, producing a
0.655 in installed spring length and 0.1885 in pen-tip-to-bed clearance. An
integrated pen-mount stop is planned to make the pen insertion datum repeatable.

## Reason

The pressure-control system needs a repeatable relationship between pen tip,
carriage position, and spring compression before it can use safe travel limits
or force calibration.

## Implementation

Recorded the dimensions in T-01A and a dated lab note. The result remains a
proposed LIFT setting rather than a firmware constant until the spring solid
height and the new pen stop are verified.

## Verification

- Owner caliper measurement: `L_free = 1.190 in`.
- Owner measured proposed LIFT compression: `0.535 in`.
- Derived installed length: `0.655 in`.
- Owner measured pen-tip clearance: `0.1885 in`.

## Struggles and rejected approaches

Using pen insertion by eye was rejected because it changes the pen-contact
carriage position and therefore spring compression. The planned integrated stop
establishes a mechanical datum instead.

## Risks and follow-up

Measure the spring solid height and retain a documented margin before using the
selected position. Build the pen stop and verify repeated insertion and
clearance measurements before completing T-01A.

## Files

- `docs/testing/TEST_PLAN.md`: records the proposed T-01A LIFT datum.
- `docs/report/lab-notes/2026-08-30-t-01a-toolhead-lift-datum.md`: raw
  measurement and remaining gate.
- `docs/project/ENGINEERING_LOG.md`: records the partial hardware milestone.
