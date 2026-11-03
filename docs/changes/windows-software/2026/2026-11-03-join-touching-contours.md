---
id: WSW-20261103-002
date: 2026-11-03
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/path_join.py
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_path_join.py
tags:
  - svg
  - path-planning
  - pen-cycle
  - contour-join
  - continuous-pen
  - performance
related:
  - WSW-20261024-011
---

# Join endpoint-touching contours to remove unnecessary pen lifts

## Summary

Added an opt-in **Join touching contours (keep pen down)** transform to the
Convert workflow. It merges ordinary open paths when their endpoints already
touch within a configurable tolerance, reducing M3/M5 cycles without linking
visibly separate areas.

## Reason

The converter's current cubic-space-division artwork contains `53,693` parsed
open contours before the planner. Many of these are consecutive pieces of the
same physical line, but each currently receives its own pen-down/up cycle.
Keeping the pen down across arbitrary disjoint contours would add unwanted
connectors across white paper, so a conservative endpoint merge is needed.

## Implementation

- Added `join_touching_contours()` in `path_join.py`.
- The join runs after clipping and artwork placement but before motion planning,
  so every merged chain becomes one drawable contour and one M3/M5 cycle.
- It matches both normal and reversed endpoints, preferring the smallest turn
  angle when several contours meet at one node.
- Closed contours remain independent loops.
- Tagged Wave and Fill contours bypass the generic join so their dedicated
  row-order, spacing, and bridge rules are not broken.
- The Convert Geometry group exposes:
  - `Join touching contours (keep pen down)`, default off.
  - `Path join tolerance mm`, default `0.02`.
- G-code records the contour-count reduction and tolerance when the pass joins
  anything.

## Verification

- The current cubic-space-division SVG contains `78,249` source polylines and
  parses into `53,693` open contours under the loaded artwork settings.
- Exact endpoint joining reduces that parsed set to `38,389` contours.
- The default `0.02 mm` tolerance reduces it to `38,001` contours, removing
  `15,692` potential pen cycles before clipping and motion planning.
- Regressions cover exact joins, reversed endpoints, tolerance boundaries,
  closed loops, tagged Wave rows, G-code cycle reduction, header recording, and
  UI availability.
- The complete converter suite passes 616 tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

A general "always pen down" painter was rejected because it would draw every
travel connector across the artwork. Merging all nearest endpoints regardless
of distance would drastically change the image. Enabling the existing fill
bridge flag was not applicable because the current artwork has no generated
fill trails.

## Risks and follow-up

The default tolerance can connect gaps up to `0.02 mm`; those joins are below
the physical pen width but remain configurable. The greedy path continuation
may not produce the mathematical minimum number of trails at dense junctions,
but it never invents a connection beyond the requested tolerance. Profile a
complete preview on the current large SVG before estimating the final print-time
reduction.

## Files

- `software/converter_core/path_join.py`: conservative endpoint-chain builder.
- `software/converter_core/gcode.py`: integration before planning, header, and
  plan metadata.
- `software/converter_core/settings.py`: option defaults, validation, and UI
  tooltips.
- `software/qt_svg_to_gcode.pyw`: sidebar state and preview logging.
- `software/tests/test_path_join.py`: path and G-code regressions.
- `software/README.md`: current behavior and safety boundary.
