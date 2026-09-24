---
id: WSW-20260924-011
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - shading
  - fill-pattern
  - ux
related:
  - WSW-20260924-002
---

# Restore manual-only preview refresh

## Summary

The preview is now rebuilt only when the user presses **Preview**. Changing the
fill pattern or toggling raster shading no longer triggers an automatic
preview rebuild.

## Reason

The automatic refresh added earlier (`WSW-20260924-002`) rebuilt the preview on
every pattern/raster change, which the user did not want. They prefer explicit
control over when the (sometimes expensive) preview build runs.

## Implementation

- `qt_svg_to_gcode.pyw`: removed the single-shot `preview_refresh_timer`, the
  `on_shading_control_changed` handler, and reverted the `hatch_pattern` and
  `raster_shading` signals to only call `update_pattern_settings`.

## Verification

- `python -c "import py_compile; py_compile.compile(...)"` passes.
- No remaining references to `preview_refresh_timer` or
  `on_shading_control_changed`.

## Struggles and rejected approaches

None.

## Risks and follow-up

None; this is a direct revert to explicit-preview behavior.

## Files

- `software/qt_svg_to_gcode.pyw`: remove auto-refresh of the preview.
