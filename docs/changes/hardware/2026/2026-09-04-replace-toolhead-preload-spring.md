---
id: HW-20260904-007
date: 2026-09-04
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - toolhead
  - N20/1024GA20 actuator
  - preload spring
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - spring
  - preload
  - lift
  - testing
related:
  - HW-20260830-004
  - HW-20260904-005
---

# Replace Toolhead Preload Spring

## Summary

The rigid spring in the toolhead was replaced with an owner-reported
compression spring measuring 0.4 mm wire diameter x 7 mm outside diameter x
25 mm free length. It was installed on 2026-09-04.

## Reason

The toolhead needs a compliant preload element. The prior spring-dependent LIFT
compression, pen clearance, force, and motor-hold observations must not be
assumed to describe the replacement spring.

## Implementation

The current candidate is recorded in the hardware inventory and test plan. The
previous 0.535 in LIFT compression and 0.1885 in pen-tip clearance are marked
historical and superseded for the current assembly. T-01A must establish the
new free length, solid height, safe compression range, and LIFT reference before
powered motion into preload.

## Verification

- Owner reported the replacement spring installed.
- Owner-reported dimensions: 0.4 mm wire x 7 mm outside diameter x 25 mm free
  length.
- No force, solid-height, clearance, or loaded-current measurement has yet been
  made for this spring.

## Struggles and rejected approaches

None reported. Reusing the prior spring's compression and force data is
explicitly rejected because the spring geometry changed.

## Risks and follow-up

Repeat T-01A before powered preload motion. Then repeat the loaded actuator
check and T-01B/T-01C/T-01D as needed. The prior E-06 result remains evidence
only for the removed spring candidate until the replacement passes its own
bounded test.

## Files

- `docs/hardware/BOM.md`: records the installed replacement spring.
- `docs/testing/TEST_PLAN.md`: supersedes the old LIFT datum and spring-dependent
  acceptance evidence.
- `docs/report/lab-notes/2026-09-04-t-01a-new-spring-installation.md`: records
  the installation observation and open measurements.
- `docs/project/ENGINEERING_LOG.md`: records the hardware change.
