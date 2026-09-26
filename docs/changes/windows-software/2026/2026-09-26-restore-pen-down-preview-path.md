---
id: WSW-20260926-001
date: 2026-09-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/README.md
tags:
  - converter
  - preview
  - gcode
  - pen-down
related:
  - WSW-20260924-015
---

# Restore the generated pen-down path in the preview

## Summary

The converter preview again shows the generated X/Y coordinates for every
pen-down `G1` segment in the selected Motion color (red by default). A checked
**Show X/Y pen-down path** control makes that visibility explicit and lets the
operator hide it when they want to inspect the upright artwork alone.

## Reason

The 2026-09-24 artwork-only cleanup removed all machine-frame paths. That
removed the cluttering pen-up travel path, but it also removed the operator's
required inspection of the generated X/Y drawing path.

## Implementation

- Reused the existing `motion` vertex buffer, which contains draw moves only.
- Rendered that buffer after the artwork and playback-progress layers when the
  new control is checked.
- Kept pen-up travel, crosshairs, and tool markers hidden.

## Verification

- `python -m py_compile software/qt_svg_to_gcode.pyw`
- `python -m unittest discover -s software/tests`
- `QT_QPA_PLATFORM=offscreen` construction of `MainWindow` passes. This runs
  the same `qt_svg_to_gcode.pyw` entry point used by `converter.bat` and
  catches widget-order startup failures before a user launches the app.

## Struggles and rejected approaches

Restoring every removed machine-frame layer would reintroduce pen-up travel,
crosshairs, and markers that obscure the drawing. Rendering only `motion`
preserves the requested G-code inspection layer.

The first implementation connected the new checkbox before `GLPreview` was
constructed, causing `converter.bat` to exit during `MainWindow` construction.
The connection now occurs immediately after `GLPreview` is created.

## Risks and follow-up

On highly rotational jobs the generated X/Y path can still be visually dense;
the operator can uncheck the control to return to the clean artwork view.

## Files

- `software/qt_svg_to_gcode.pyw`: restores the selectable red G1 X/Y overlay.
- `software/README.md`: documents the preview control and its scope.
