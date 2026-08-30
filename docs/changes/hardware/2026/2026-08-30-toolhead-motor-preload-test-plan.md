---
id: HW-20260830-001
date: 2026-08-30
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - docs/testing/TEST_PLAN.md
  - docs/testing/RECOMMENDED_TEST_SEQUENCE.md
  - firmware/pen_pressure/README.md
tags:
  - toolhead
  - preload
  - spring
  - n20
  - force-control
  - test-plan
related:
  - RPSW-20260825-001
---

# Plan Toolhead Motor/Preload Physical-Envelope Test

## Summary

Added a T-01 sub-test sequence that proves the installed spring, N20 actuator,
and force path can operate within a measured pressure-control envelope before
contact seeking or force-loop tuning.

## Reason

The nominal spring dimensions do not establish installed preload, coil-bind
margin, force at the pen, friction, backlash, motor holding capability, or
retract performance. Those unknowns must be measured before they become
firmware limits or control-loop assumptions.

## Implementation

`T-01A` through `T-01F` establish geometry/preload, the installed force curve
and hysteresis, static motor hold, retract reserve, pulse response, and a
single control-envelope record. The recommended sequence places the unpowered
geometry check before motor motion and gates loaded conclusions on E-06, E-15,
and E-07.

## Verification

- `python tools/docs_index.py --write` — pending.
- `python tools/docs_index.py --check` — pending.
- Physical tests are planned; no component capability is verified by this
  documentation update.

## Struggles and rejected approaches

Treating the nominal 0.027 in x 0.295 in x 1.19 in spring dimensions or the
unloaded N20 current result as proof of loaded retract/hold capability was
rejected. The installed mechanism's preload, friction, and force-path
hysteresis are material variables.

## Risks and follow-up

The actual spring rate, solid height, force direction, motor thermal margin,
and force-transfer ratio remain unknown until T-01 is run. Record every test
attempt in a dated lab note and leave control constants gated until T-01F is
complete.

## Files

- `docs/testing/TEST_PLAN.md`: authoritative T-01 motor/preload sub-tests and
  pass conditions.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: dependency order for the new
  sub-tests.
- `firmware/pen_pressure/README.md`: points force-control commissioning to the
  physical-envelope gate.
- `docs/project/ROADMAP.md`: tracks the new Phase 5 test work.
- `docs/project/ENGINEERING_LOG.md`: records the planned milestone and safety
  boundary.
