---
id: HW-20260904-002
date: 2026-09-04
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - plotter-top-down-wiring-schematic.svg
  - plotter-top-down-wiring-schematic.png
  - docs/hardware/WIRING_TABLE.md
tags:
  - wiring
  - schematic
  - routing
  - tb6600
  - signal-lanes
related:
  - HW-20260904-001
---

# Reroute top-down wiring schematic into clean lanes

## Summary

Rebuilt the top-down wiring schematic with separate orthogonal lanes so that
signal, motor, and power routes are readable without wire crossings or
overlapping cable paths.

## Reason

The previous explanatory layout used diagonal power branches and repeated
fan-outs from the RP23CNC. Those paths crossed and overlaid one another, making
it difficult to follow an individual axis from controller to motor.

## Implementation

- Added one four-wire source lane set for each RP23CNC axis.
- Added an explicit X, Y, and A signal-common block that shows how each axis
  `G` is distributed to `PUL-`, `DIR-`, and `ENA-`.
- Routed the six TB6600 control lanes directly into each driver and routed all
  four motor leads horizontally to the corresponding motor block.
- Moved the six DIN power branches into separate top lanes and a far-right
  vertical corridor before dropping to the driver power terminals.
- Kept the axis-specific motor cable documentation: X uses white cable-side
  `B-` continuing to the motor blue lead; Y and A use stock blue `B-` leads.

## Verification

- Parsed `plotter-top-down-wiring-schematic.svg` with the PowerShell XML parser.
- Rendered `plotter-top-down-wiring-schematic.png` with Chrome headless.
- Visually inspected the rendered preview: signal lanes, motor leads, and
  power branches are separated and no longer cross or share a route.

## Struggles and rejected approaches

The first clean-lane draft still overlaid the PSU-to-DIN `+V` and `0V` lines
and placed the X motor's white terminal on the opposite side of its motor
block. Both issues were corrected before the final render. No physical
wiring or terminal assignment changed.

## Risks and follow-up

This remains an explanatory schematic; the exact terminal order and physical
wire lengths must still be checked against the installed RP23CNC, TB6600s,
DIN distribution, and motor harnesses before power is applied.

## Files

- `plotter-top-down-wiring-schematic.svg`: rebuilt with non-overlapping
  orthogonal routes.
- `plotter-top-down-wiring-schematic.png`: regenerated visual preview.
- `docs/hardware/WIRING_TABLE.md`: recorded the schematic-routing revision.
