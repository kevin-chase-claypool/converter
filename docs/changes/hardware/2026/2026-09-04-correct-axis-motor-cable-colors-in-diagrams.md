---
id: HW-20260904-001
date: 2026-09-04
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - plotter-wiring-schematic.svg
  - plotter-photo-style-wiring.svg
  - plotter-top-down-wiring-schematic.svg
  - docs/full_wiring_diagram.html
  - docs/hardware/WIRING_TABLE.md
tags:
  - stepper
  - tb6600
  - motor-cable
  - wiring
  - x-axis
  - y-axis
  - a-axis
related:
  - HW-20260823-003
  - HW-20260823-002
---

# Correct axis-specific motor cable colors in diagrams

## Summary

Updated the visual wiring diagrams and rendered previews to distinguish the X
axis's shielded motor cable from the stock Y and A motor leads.

## Reason

The diagrams previously repeated the stock `black/green/red/blue` labels for
all three axes. That was misleading for X, whose replacement shielded cable
uses a white conductor for cable-side `B-`; the white conductor is spliced to
the motor's blue lead.

## Implementation

- X is labeled `A+ black`, `A- green`, `B+ red`, and `B- white`, with the
  white-to-blue motor splice called out.
- Y and A remain `A+ black`, `A- green`, `B+ red`, and `B- blue` using the
  stock motor leads.
- The full HTML diagram uses compact axis-specific labels, while the SVG
  diagrams include the distinction in their motor blocks and notes.

## Verification

- Rendered `plotter-wiring-schematic.png`, `plotter-photo-style-wiring.png`,
  and `plotter-top-down-wiring-schematic.png` from their updated SVG sources
  with Chrome headless.
- Visually inspected all three PNG previews for the X white label, the Y/A
  blue labels, and the explanatory splice notes.
- Rendered `docs/full_wiring_diagram.html` with Chrome headless and confirmed
  the X/Y/A labels and updated callout text.
- Parsed all three SVG sources as XML with the Python standard-library parser.

## Struggles and rejected approaches

The prior generic labels were retained only as a temporary conceptual view;
they are not an acceptable representation of the installed X harness. No
physical wiring was changed in this update, and no new cable colors were
inferred beyond the project-owner clarification and the existing master-table
record.

## Risks and follow-up

The diagrams remain explanatory; the master wiring table controls if a visual
copy becomes stale. Final X phase continuity and motor-direction checks remain
required before powered operation.

## Files

- `plotter-wiring-schematic.svg`: corrected X motor block and accessibility note.
- `plotter-wiring-schematic.png`: regenerated preview.
- `plotter-photo-style-wiring.svg`: added axis-specific color notes.
- `plotter-photo-style-wiring.png`: regenerated preview.
- `plotter-top-down-wiring-schematic.svg`: corrected X motor-lead block and caution note.
- `plotter-top-down-wiring-schematic.png`: regenerated preview.
- `docs/full_wiring_diagram.html`: corrected axis-specific labels and callout.
- `docs/hardware/WIRING_TABLE.md`: recorded the diagram correction in the revision log.
