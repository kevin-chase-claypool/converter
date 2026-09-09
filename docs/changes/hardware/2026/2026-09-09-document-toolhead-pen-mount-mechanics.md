---
id: HW-20260909-003
date: 2026-09-09
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - toolhead pen mount
  - spring housing
  - N20 lead screw
tags:
  - toolhead
  - pen-mount
  - spring
  - mechanics
  - t-01
related:
  - HW-20260909-001
  - HW-20260909-002
---

# Document toolhead pen-mount mechanics

## Summary

Added the authoritative physical model for the fixed spring housing, sliding
pen housing, paper-driven spring compression, and separate lead-screw position.

## Reason

Bench discussion exposed an unsafe ambiguity: lead-screw/heat-set-nut gap was
mistakenly treated as spring length. The physical mechanism makes the pen
housing compress the spring only under upward paper reaction.

## Implementation

`TOOLHEAD_MECHANICS.md` defines each component, the force path, measurement
vocabulary, known values, and test boundaries. It explicitly keeps GP2 and
lead-screw position distinct from pen force and spring compression.

## Verification

Project-owner side-view inspection: with upward pen force, the sliding pen
housing rises inside the fixed spring housing and compresses the spring; with
no upward force, the spring is expanded. Force-rate measurements remain open.

## Struggles and rejected approaches

Inferring spring compression from actuator/lead-screw position was rejected.

## Risks and follow-up

Re-measure any historical spring endpoint whose physical datum is unclear.
Complete scale-force T-01B work only after the selected replacement motor is
installed and requalified.

## Files

- `docs/hardware/TOOLHEAD_MECHANICS.md`: authoritative mechanical model.
- `docs/README.md`: task-oriented documentation route.
