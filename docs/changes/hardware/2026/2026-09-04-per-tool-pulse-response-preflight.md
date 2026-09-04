---
id: HW-20260904-006
date: 2026-09-04
category: hardware
affected_categories:
  - rp23cnc-software
components:
  - toolhead
  - N20/1024GA20 actuator
  - interchangeable pens and pencils
status: implemented
tags:
  - toolhead
  - n20
  - force-control
  - interchangeable-tools
  - preflight
related:
  - HW-20260904-005
---

# Make Pulse Response Tool-Specific During Preflight

## Summary

The toolhead test plan now separates global N20 actuator pulse limits from
per-tool force response. The load cell remains the force-control authority,
while each installed pen or pencil receives a short bounded response check
during preflight.

## Reason

Tip compliance, clamp height, mass, friction, and contact geometry make the
force produced by a given pulse different for different tools. A single
pulse-to-force curve must not be applied to every pen or pencil.

## Implementation

T-01E now establishes global pulse, backlash, and settling bounds with a
representative tool or guarded fixture. T-01J records per-tool target and
contact/release settings plus an optional bounded pulse override. ADR-005
records the resulting control architecture.

## Verification

- Updated `docs/testing/TEST_PLAN.md` to define global T-01E bounds and
  per-tool T-01J checks.
- Updated `firmware/pen_pressure/README.md` and the roadmap.
- Added ADR-005 for the lasting per-tool preflight decision.

## Struggles and rejected approaches

Using one measured force-per-pulse curve as a universal setting for all
interchangeable pens and pencils was rejected because their compliance,
mounting height, and contact mechanics differ.

## Risks and follow-up

The load cell must remain functional and calibrated; a per-tool pulse override
must stay within the global safe actuator bounds. Complete T-01J for each tool
type before allowing it to plot.

## Files

- `docs/testing/TEST_PLAN.md`: global versus per-tool T-01E/T-01J definition.
- `firmware/pen_pressure/README.md`: control and tuning guidance.
- `docs/decisions/ADR-005-per-tool-pulse-response-preflight.md`: accepted
  architecture decision.
- `docs/project/ROADMAP.md`: expanded physical-envelope gate.
