---
id: HW-20260823-004
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - X-axis motor cable shield
  - MEISHILE S-120-12 protective-earth terminal
tags:
  - protective-earth
  - mains
  - shielding
  - wiring
  - x-axis
related:
  - HW-20260823-002
  - HW-20260823-003
---

# Record X sheath protective-earth bond

## Summary

The green X motor-cable sheath/drain is reported connected to the MEISHILE
power supply's protective-earth terminal, alongside the wall-earth conductor.

## Reason

The shield needs a single protective-earth reference without being tied to a
DC or signal return.

## Implementation

The owner reports red on `L`, blue on `N`, and green on the protective-earth
symbol. The X sheath/drain is green and lands at that PE terminal. It does not
connect to DC `-V`, live, or neutral.

## Verification

Owner report only. Terminal-label inspection, PE/chassis continuity, and
isolation of the shield from `-V` and signal ground remain open.

## Struggles and rejected approaches

Color alone is not accepted as terminal identification; the printed `L`, `N`,
and protective-earth markings remain authoritative.

## Risks and follow-up

Before mains power, verify the terminal labels with power removed and measure
low-resistance PE-to-chassis continuity. Confirm no continuity from the X
shield to DC `-V` or any motor phase.

## Files

- `docs/hardware/WIRING_TABLE.md`: records color convention and X PE bond.
- `docs/hardware/POWER_DISTRIBUTION.md`: adds the mains-color safety note.
