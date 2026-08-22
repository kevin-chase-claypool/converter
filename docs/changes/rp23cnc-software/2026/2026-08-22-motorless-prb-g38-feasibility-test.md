---
id: RPSW-20260822-001
date: 2026-08-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: planned
components:
  - RP23CNC PRB input
  - grblHAL G38 probing
  - GP27/PC817C U3 return path
tags:
  - probing
  - magnetic-calibration
  - motorless-test
  - g38
related:
  - F-08
  - E-18
---

# Motorless PRB/G38 Feasibility Test

## Summary

Added F-08 as a motorless feasibility gate for using the RP23CNC `PRB` input
to capture TMAG5273 magnetic transitions during X/Y raster and A-index moves.
The current GP27/U3 -> `LIMA` assignment remains authoritative until the test
passes and a later change deliberately approves retermination.

## Reason

The RP23CNC manual documents the isolated electrical probe input, and grblHAL
documents or implements G38 probing and coordinate reporting. Neither source
explicitly certifies this project's complete Hall-sensor raster, area-centroid,
and rotary-A use case. A source-level indication that enabled axes share the
probe target vector is useful evidence but is not a substitute for testing the
installed firmware build.

## Implementation

F-08 disconnects all TB6600 signal leads and motors, then uses a dry contact or
validated isolated sink to test `PRB` state reporting, X `G38.3`/`G38.5`
trigger and release capture, probe-coordinate output, and A-axis command/report
behavior. Only after the direct-input stage passes is the actual GP27/PC817C U3
path tested.

## Verification

Documentation index generation and validation are required for this planned
test note. No electrical or firmware behavior is claimed yet; F-08 remains
unperformed.

## Struggles and rejected approaches

Rejected treating the existence of an RP23CNC probe terminal or generic
grblHAL source behavior as end-to-end proof of the proposed magnetic workflow.
Also rejected wiring motors merely to test parser, input-state, and internal
probe-coordinate behavior.

## Risks and follow-up

The installed build may reject A-axis G38 targets or omit A from the returned
probe record. Probe polarity may differ from the proposed active state. A
failed result keeps `LIMA` in service and requires a different architecture;
do not tune around or omit that result.

## Files

- `docs/testing/TEST_PLAN.md`: defines F-08 and its pass conditions.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: places F-08 before toolhead and
  motion integration.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: records the evidence
  boundary and preserves the current `LIMA` design.
- `docs/hardware/WIRING_TABLE.md`: marks `PRB` as a candidate, not an assigned
  endpoint.
- `docs/integration/INTERFACES.md`: preserves the current interface contract.
