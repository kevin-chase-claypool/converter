---
id: HW-20260819-003
date: 2026-08-19
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/BOM.md
  - docs/hardware/POWER_DISTRIBUTION.md
tags:
  - stepper
  - cable
  - shielding
  - y-axis
  - protective-earth
related:
  - HW-20260819-001
---

# Correct Installed Stepper Cable Shielding

## Summary

Corrected the physical motor-cable record: only the Y motor has a shielded
cable and drain wire. X and A retain their supplied unshielded 24 AWG motor
leads.

## Reason

Earlier records generalized a purchased shielded cable as installed on every
axis. The project owner clarified that this is not the actual machine wiring.

## Implementation

The master wiring table now records X/A as unshielded and removes their
nonexistent shield-bond rows. Y remains the sole drain-to-PE/chassis connection
at the driver end. The KWANGIL 20 AWG shielded cable remains purchased but is
not currently installed.

## Verification

Project-owner physical-wiring correction. This changes documentation only; no
powered motor, PE-continuity, or shielding-performance test has occurred.

## Struggles and rejected approaches

Treating the cable purchase as proof of installation incorrectly created X/A
shield-drain connections that do not physically exist. Those rows were removed
rather than leaving a misleading future wiring instruction.

## Risks and follow-up

Before mains power, verify the Y drain's continuity to PE/chassis and isolation
from every DC return. If X or A is later replaced with shielded cable, add its
physical conductor and shield-bond rows before wiring it.

## Files

- `docs/hardware/WIRING_TABLE.md`: actual X/Y/A cable and shield connections.
- `docs/hardware/BOM.md`: separates purchased cable from installed cable.
- `docs/hardware/POWER_DISTRIBUTION.md`: limits PE shield-bond narrative to Y.
