---
id: HW-20260615-001
date: 2026-06-15
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/cad
  - tools/cad/generate_tecmojo_14130201.py
  - docs/hardware/BOM.md
tags:
  - electronics-rack
  - sliding-shelf
  - step
  - cad
  - tecmojo-14130201
related:
  - docs/hardware/BOM.md
---

# Tecmojo Sliding Shelf Reference CAD

## Summary

Added parametric reference CAD for the selected Tecmojo `14130201` 1U
adjustable-depth sliding shelf sold as Amazon ASIN `B0BMW9V6MS`.

The generated STEP assemblies cover the published minimum 350 mm and maximum
500 mm rack-post depths. Both preserve the published 482.6 mm mounting width
and 44.45 mm shelf-body height.

## Reason

The shelf will support the plotter electronics, so rack envelope, electronics
placement, cable clearance, and future mounting-plate work need usable 3D
geometry before the physical integration layout is finalized.

## Implementation

`tools/cad/generate_tecmojo_14130201.py` builds a named CadQuery assembly with
the sliding shelf, front supports, telescoping rear supports, drawer-slide
members, front and rear rack ears, and optional anti-slip stops.

The model uses manufacturer-published dimensions for the rack interface and
adjustment range. Unpublished sheet-metal thickness, rail profiles, vent
pattern, cable passages, fastener holes, and stop geometry are isolated as
image-derived constants so received-part measurements can replace them later.

Loose screws, cage nuts, hook-and-loop ties, and the instruction sheet are not
included in the installed assembly models.

## Verification

- Generated `tecmojo-14130201-350mm.step` and
  `tecmojo-14130201-500mm.step`.
- Re-imported each STEP through CadQuery.
- Confirmed 13 valid solids in each assembly.
- Confirmed full imported envelopes of `482.6 x 350 x 62.45 mm` and
  `482.6 x 500 x 62.45 mm`, including optional anti-slip stops.
- Confirmed shelf-body envelopes before stops of
  `482.6 x 350 x 44.45 mm` and `482.6 x 500 x 44.45 mm`.
- Rendered and visually inspected both configurations against the listing
  images and current Tecmojo manual.
- Ran Python bytecode compilation on the generator.

## Struggles and rejected approaches

The Amazon catalog table reports `20.9"D x 3.35"W x 1.73"H`, which does not
describe the installed shelf envelope. An older manual also listed a
350-400 mm adjustment range. These sources were rejected for geometry after
the current Tecmojo manual and specification sheet identified SKU `14130201`
and explicitly gave 482.6 mm width, 350-500 mm mounting depth, and 44 mm
height.

No manufacturer production CAD was available from the product downloads.

## Risks and follow-up

This is a layout-quality reference model, not a production drawing. Measure the
received shelf before manufacturing mating parts or relying on individual vent,
hole, bend, rail, and stop dimensions.

The optional stops rise above the nominal 1U body. Their final use and required
vertical clearance should be decided during electronics placement.

## Files

- `docs/hardware/cad/README.md`: dimensions, scope, sources, and accuracy
  boundary.
- `docs/hardware/cad/tecmojo-14130201-350mm.step`: minimum-depth assembly.
- `docs/hardware/cad/tecmojo-14130201-500mm.step`: maximum-depth assembly.
- `docs/hardware/cad/*-preview.png`: rendered visual checks.
- `tools/cad/generate_tecmojo_14130201.py`: parametric source and exporter.
- `docs/hardware/BOM.md`: selected electronics shelf and verification needs.
- `docs/project/ENGINEERING_LOG.md`: source conflict and modeling result.
