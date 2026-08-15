---
id: HW-20260803-001
date: 2026-08-03
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - rp23cnc-pro-micro-interface-schematic.svg
  - rp23cnc-pro-micro-interface-schematic.png
  - docs/hardware/WIRING_TABLE.md
tags:
  - wiring
  - interface
  - rp23cnc
  - toolhead
related:
  - HW-20260802-001
---

# RP23CNC To Pro Micro Interface Schematic

## Summary

Added a PNG/SVG schematic for the planned RP23CNC-to-SparkFun Pro Micro RP2350
interface.

## Reason

The interface wiring needs to distinguish the RP23CNC-to-Pro-Micro logic paths
from the Pro-Micro-to-RP23CNC `A_HOME` switch-like path without overlapping
wires or implying that all RP23CNC terminals share the same voltage behavior.

## Implementation

The schematic separates RP23CNC, HiLetgo level shifter, Zopsc optocoupler, and
SparkFun Pro Micro RP2350 blocks. It shows `SPINDLE ENA OUT` and `AUX0
HOME_ARM OUT` passing through the HiLetgo 3.3 V/5 V level shifter to `GP8` and
`GP10`, while `GP9 A_HOME OUT` drives the Zopsc optocoupler input and presents
a switch-like output to the RP23CNC A limit/home input. The wiring table now
lists the image as explanatory only.

## Verification

- Rendered `rp23cnc-pro-micro-interface-schematic.png` from the SVG with Chrome
  headless.
- Visually checked the PNG for separated horizontal wiring lanes and no
  terminal-to-terminal wire overlap.
- Ran documentation index generation and validation after the update.

## Struggles and rejected approaches

An initial PNG render placed the lower optocoupler title too close to the
terminal labels. The schematic was widened and the lower section was given more
vertical space before final rendering.

## Risks and follow-up

The drawing remains explanatory. Exact RP23CNC terminal names, polarity,
voltage, and common/return points still require manual/meter verification
before powered wiring.

## Files

- `rp23cnc-pro-micro-interface-schematic.svg`: editable source schematic.
- `rp23cnc-pro-micro-interface-schematic.png`: viewable PNG schematic.
- `docs/hardware/WIRING_TABLE.md`: recorded the schematic as explanatory only.
