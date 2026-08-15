---
id: HW-20260803-002
date: 2026-08-03
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/POWER_DISTRIBUTION.md
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/BOM.md
  - power-distribution-schematic.svg
  - power-distribution-schematic.png
tags:
  - power-distribution
  - buck-regulator
  - wiring
  - toolhead
related:
  - HW-20260802-001
  - docs/hardware/WIRING_TABLE.md
  - docs/testing/TEST_PLAN.md
---

# Power Distribution Document And Schematic

## Summary

Added a dedicated power-distribution current-state document and a viewable
power-only schematic for the plotter. The document and schematic identify the
active buck/regulator path: MEISHILE 12 V supply, fused 12 V distribution,
Pololu D36V50F6 fixed 6 V regulator, one 6 V + GND toolhead drag-chain pair,
toolhead-mounted Pololu S7V8F5 5 V regulator, and Pro Micro 3.3 V sensor power.

## Reason

The buck regulators had already been added to the BOM and wiring table, but the
power path did not have one organized page that separated power distribution
from signal wiring. The roadmap also still referenced the superseded
B085T73CSD adjustable buck as the active 6 V verification task.

## Implementation

Created `docs/hardware/POWER_DISTRIBUTION.md` as the power-distribution entry
point and linked it from the documentation map, BOM, and wiring table. Added
`power-distribution-schematic.svg` and rendered `power-distribution-schematic.png`
with straight branch lanes and a single toolhead 6 V terminal block so the
local DRV8833 and S7V8F5 feeds are visually separated.

Updated the Phase 1 roadmap tasks to verify and characterize the Pololu
D36V50F6 and toolhead-mounted S7V8F5 instead of the superseded adjustable buck.

## Verification

- Parsed `power-distribution-schematic.svg` as XML.
- Rendered `power-distribution-schematic.png` with Chrome headless.
- Visually inspected the PNG for branch layout and terminal labels.
- `python tools\docs_index.py --write` updated five generated change indexes.
- `python tools\docs_index.py --check` passed for 22 change notes.

## Struggles and rejected approaches

An initial schematic render still bundled several conductors near the drag-chain
boundary and allowed the 6 V path to visually interfere with unrelated content.
The schematic was redrawn so 12 V loads use straight paired lanes and the
toolhead 6 V split occurs only at a labeled terminal block.

## Risks and follow-up

The schematic is still explanatory. Final fuse sizes, terminal allocation, wire
gauge, ferrules, strain relief, and branch protection remain TBD until the
power budget and bench tests `E-11`, `E-14`, `E-15`, and `E-15A` are complete.

## Files

- `docs/hardware/POWER_DISTRIBUTION.md`: new current-state power distribution document.
- `power-distribution-schematic.svg`: editable power-only schematic source.
- `power-distribution-schematic.png`: rendered viewable schematic image.
- `docs/README.md`: linked the power-distribution entry point.
- `docs/hardware/BOM.md`: linked the power-distribution document from the inventory.
- `docs/hardware/WIRING_TABLE.md`: linked the schematic and added a revision entry.
- `docs/project/ROADMAP.md`: updated the active regulator verification tasks.
