---
id: HW-20260704-001
date: 2026-07-04
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/electronics_layout_and_wiring.html
  - docs/full_wiring_diagram.html
  - docs/hardware/WIRING_TABLE.md
tags:
  - wiring
  - layout
  - electronics
  - rp23cnc
  - tmag5273
  - toolhead
related:
  - RPSW-20260704-001
---

# Electronics Layout Wiring HTML

## Summary

Added a standalone dark-mode HTML planning view for the current electronics
layout and wiring concept.

## Reason

The project needed a readable visual summary of the current electronics plan:
RP23CNC with Ethernet, 12 V distribution, X/Y/A TB6600 drivers, toolhead
electronics, and the TMAG5273/RP2040 magnetic homing adapter.

## Implementation

Created `docs/electronics_layout_and_wiring.html` with a static dark-mode SVG
system diagram, color-coded wire classes, open connection gates, and notes for
current control flow, power, and magnetic homing/calibration.

Updated the layout after the homing data-flow work to clarify that the
TMAG5273/RP2040 path is the magnetic adapter that produces the validated
`A_HOME` switch-like output, the TMAG5273 is a fixed-height installed sensor
mounted with the toolhead/gantry, the grblHAL `M5` behavior is a spindle/tool
output pin state used for toolhead lift, and the Z axis slot is unused even
though the four-axis grblHAL build is needed to expose A with X/Y.

Updated `docs/hardware/WIRING_TABLE.md` to state that the new HTML, like the
existing wiring diagram, is explanatory only. The master wiring table remains
authoritative for terminal labels, conductor status, and evidence.

Aligned the older `docs/full_wiring_diagram.html` pen-command labels with the
current homing plan by changing the RP23CNC-to-toolhead wording from generic
`M3/M5` command text to the spindle/LIFT output state. No new A_HOME wiring path
was added there because that diagram does not yet model the magnetic adapter.

## Verification

Documentation-only update. The HTML is intended for browser viewing and does
not promote any wiring status or assign new terminals.

`python tools\docs_index.py --write` and `python tools\docs_index.py --check`
must pass before this session is complete.

## Struggles and rejected approaches

None.

## Risks and follow-up

The diagram is deliberately conceptual. It must be updated after RP23CNC input
circuits, TB6600 input topology, fusing, E-stop architecture, and toolhead
controller placement are verified.

## Files

- `docs/electronics_layout_and_wiring.html`: new visual electronics layout and
  wiring concept, styled for nighttime reading.
- `docs/full_wiring_diagram.html`: updates the legacy pen-control labels to
  match the spindle/LIFT output-state wording.
- `docs/hardware/WIRING_TABLE.md`: references the new diagram and records the
  revision while preserving the table as the wiring authority.
