---
id: HW-20260823-008
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - X-axis motor cable shield
  - X/Y/A motor phase conductors
tags:
  - protective-earth
  - shielding
  - isolation
  - wiring
  - stepper
related:
  - HW-20260823-007
---

# Verify X sheath motor-phase isolation

## Summary

The X motor-cable sheath has no continuity to any motor-phase conductor.

## Reason

The PE-referenced sheath must remain isolated from all motor windings.

## Implementation

No wiring changed. This records the completed power-off isolation measurement.

## Verification

Owner meter verification: no continuity between the X sheath and any motor
phase conductor. Together with the previously recorded checks, the sheath has
a verified PE path and is isolated from DC `-V` and motor phases.

## Struggles and rejected approaches

None reported.

## Risks and follow-up

Enclosure/strain-relief work and powered E-11/motor commissioning remain open.

## Files

- `docs/hardware/WIRING_TABLE.md`: marks the completed X-sheath isolation.
- `docs/report/lab-notes/2026-08-23-mains-terminal-and-x-sheath-verification.md`:
  records the measurement scope.
