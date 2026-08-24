---
id: HW-20260823-007
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - MEISHILE S-120-12 protective-earth terminal
  - X-axis motor cable shield
tags:
  - protective-earth
  - chassis
  - shielding
  - mains
  - wiring
related:
  - HW-20260823-006
---

# Verify supply protective-earth chassis path

## Summary

The protective-earth terminal-to-supply-chassis path passes; the powder-coated
machine structure is not used as the protective-earth reference.

## Reason

Powder coating cannot be assumed to provide a reliable electrical bond.

## Implementation

No wiring changed. The green X sheath remains landed at the supply PE terminal.

## Verification

Owner meter verification: the PE terminal-to-supply-chassis path passes.

## Struggles and rejected approaches

Using the powder-coated structure as the PE path was rejected because the
coating may electrically isolate mounting points.

## Risks and follow-up

The X sheath still needs isolation verification from all motor-phase conductors.
Enclosure, strain-relief, and powered E-11 checks remain open.

## Files

- `docs/hardware/WIRING_TABLE.md`: records the PE/chassis pass.
- `docs/hardware/POWER_DISTRIBUTION.md`: records the non-reliance on coating.
- `docs/report/lab-notes/2026-08-23-mains-terminal-and-x-sheath-verification.md`:
  records the evidence boundary.
