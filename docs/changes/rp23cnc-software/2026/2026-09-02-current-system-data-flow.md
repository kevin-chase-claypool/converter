---
id: RPSW-20260902-001
date: 2026-09-02
category: rp23cnc-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - docs/system_data_flow.html
  - docs/architecture/SYSTEM_ARCHITECTURE.md
  - docs/README.md
tags:
  - data-flow
  - system-architecture
  - plotting
  - p100
  - toolhead
  - safety
related:
  - docs/integration/INTERFACES.md
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
---

# Add Current System Data Flow Chart

## Summary

Added one current-state visual reference for how data moves through the whole
plotter in normal operation, startup registration, toolhead control, fault
handling, and commissioning.

## Reason

The prior standalone homing sheet is archived and describes an earlier
architecture. The project needed an unambiguous visual that separates the
current operational scenarios and makes their start and end points visible.

## Implementation

Created `docs/system_data_flow.html` with five explicit scenario diagrams.
The first SVG-based layout proved too dense on a phone and its return paths
crossed components. Replaced it with responsive top-to-bottom card flows: each
arrow connects only adjacent steps, and the only desktop-only branches stack to
one column on a narrow display. The sheet distinguishes job data, motion
commands, toolhead control, sensor feedback, calculated registration data, and
faults. It states that M3/M5 becomes an isolated pin state, P100 owns magnetic
calculation, the force loop is local to the toolhead, and faults require
deliberate recovery.

Linked the sheet from the documentation map and system architecture.

## Verification

- Documentation-only update.
- Reviewed against `docs/integration/INTERFACES.md`,
  `firmware/pen_pressure/README.md`, and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`.
- Mobile screenshot review identified the original crossing/overlap defect;
  the replacement uses no drawn connector paths.
- `python tools\docs_index.py --write` and `--check` passed after the layout
  correction.

## Struggles and rejected approaches

Extending `docs/homing_data_flow.html` was rejected because it is explicitly
archived and represents a superseded direct A-home workflow. The first new
SVG-based layout was also rejected after mobile review because its connector
paths crossed and ran through components.

## Risks and follow-up

The candidate `GP27` to `PRB` route remains gated by F-08; the chart labels it
as a candidate rather than installed behavior. Toolhead safety and force
thresholds remain commissioning-gated until their named tests pass.

## Files

- `docs/system_data_flow.html`: current, non-overlapping system data-flow chart.
- `docs/architecture/SYSTEM_ARCHITECTURE.md`: link to the visual companion.
- `docs/README.md`: documentation-map link.
