---
id: HW-20260823-006
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - X-axis motor cable shield
  - 12 V DC return
tags:
  - protective-earth
  - shielding
  - isolation
  - wiring
  - x-axis
related:
  - HW-20260823-005
---

# Verify X sheath DC-negative isolation

## Summary

The X motor-cable sheath has no continuity to DC `-V`.

## Reason

The protective-earth shield must not become a DC return path.

## Implementation

No wiring changed. This records the owner's power-off isolation measurement.

## Verification

Owner meter verification: no continuity between the X sheath and DC `-V`.

## Struggles and rejected approaches

None reported.

## Risks and follow-up

PE-to-chassis continuity and isolation from every motor-phase conductor remain
open. Do not treat this single isolation result as a completed mains or motor
power test.

## Files

- `docs/hardware/WIRING_TABLE.md`: records the passing `-V` isolation result.
- `docs/report/lab-notes/2026-08-23-mains-terminal-and-x-sheath-verification.md`:
  adds the measurement boundary.
