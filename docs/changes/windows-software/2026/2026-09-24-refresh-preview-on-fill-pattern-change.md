---
id: WSW-20260924-002
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
---

# Rebuild the preview when the fill pattern or raster shading changes

## Summary

Changing the fill pattern (or toggling raster shading) now rebuilds the preview
automatically after a short settle. The user no longer has to remember to press
**Preview** to see a new pattern.

## Reason

The `hatch_pattern` combo box and the raster-shading checkbox only updated the
visibility of the pattern-size fields; nothing invalidated or regenerated the
preview. A user who changed the pattern and glanced at the preview saw the
previous pattern and concluded the change did nothing. The fill engine itself
was already producing distinct output per pattern (e.g. triangular, diamonds,
and hexagonal each emit a different lattice), so the gap was purely in the UI
refresh path.

## Implementation

- `qt_svg_to_gcode.pyw`: added a single-shot `preview_refresh_timer` and an
  `on_shading_control_changed` handler that calls `update_pattern_settings()`
  and then schedules `preview()` after 400 ms.
- The `hatch_pattern.currentTextChanged` and `raster_shading.toggled` signals now
  route through `on_shading_control_changed` instead of only toggling field
  visibility.
- The refresh is skipped when no SVG is loaded, so changing a dropdown before
  choosing a file does not raise a "Preview needs an SVG" dialog. `preview()`
  still no-ops if a build is already running.

## Verification

- `python -c "import py_compile; py_compile.compile(...)"` passes on
  `software/qt_svg_to_gcode.pyw`.
- Offscreen smoke test: with an SVG loaded, calling `on_shading_control_changed`
  activates `preview_refresh_timer`; with no SVG loaded, it does not.
- Geometry check (offscreen `load_contours`, raster shading on, triangle/diamond/
  hex size 30, spacing 5): triangular 644 contours, diamonds 830, hexagonal 1175,
  confirming the fill engine already changed output per pattern.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

Auto-refreshing on every keystroke of the numeric fill fields was rejected: it
would rebuild repeatedly and, with raster shading on a large SVG, that build is
expensive. The discrete pattern/raster controls get the debounced auto-refresh;
numeric fields still rebuild on the next explicit **Preview**.

## Risks and follow-up

Auto-refresh can still start an expensive raster build immediately when a user
toggles raster shading on for a large file, but the existing **Cancel** path
unwinds it cleanly. If numeric-field live refresh is later wanted, it should be
debounced on `editingFinished` rather than `textChanged`.

## Files

- `software/qt_svg_to_gcode.pyw`: add debounced preview rebuild on pattern/raster changes.
