---
id: HW-20260823-009
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: planned
components:
  - X-axis motor cable
  - Y-axis motor cable
  - A-axis motor cable
  - mechanical CAD
tags:
  - cad
  - strain-relief
  - stepper
  - cable-management
related:
  - HW-20260823-008
---

# Plan motor-harness strain-relief CAD

## Summary

Design CAD strain-relief features for all three motor wire harnesses.

## Reason

The motor terminals and the X protective-earth sheath need mechanical protection
from motion, harness weight, and accidental pulls.

## Implementation

The planned CAD features must grip each harness cable's outer jacket, not
individual phase wires; preserve bend radius and service slack; and avoid
transmitting load to TB6600 terminals. The X feature must not disturb the PE
sheath/drain bond or its verified isolation.

## Verification

Planned only. Verify fit, range-of-motion clearance, clamp retention, bend
radius, terminal relief, and X sheath continuity/isolation after fabrication.

## Struggles and rejected approaches

No design has been selected. Directly clamping individual conductors is
rejected because it does not provide reliable cable strain relief.

## Risks and follow-up

The design needs measured harness outside diameters, exit directions, available
mounting geometry, and drag-chain clearance before dimensions are finalized.

## Files

- `docs/project/ROADMAP.md`: adds the CAD task and acceptance criteria.
