---
id: WSW-20261006-005
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - generators
  - preview
related:
  - WSW-20261006-001
  - WSW-20261006-002
  - WSW-20261006-003
  - WSW-20261006-004
---

# Keep import, export, and preview static across generator tabs

## Summary

The artwork/G-code file row, the Preview / Cancel / Save G-code actions, and
the OpenGL preview panel now live outside the tab widget. Switching to Flow
Field, Line Draw, or 3D Wireframe no longer hides the converter's import,
export, or preview controls.

## Reason

The first tab shell put the whole existing workspace - file row, actions, and
preview - inside the Convert tab. That made the generator tabs dead ends: a
generated SVG could not be previewed or saved without switching back, and the
playback/preview controls disappeared with the tab. The owner reported exactly
that on 2026-10-06.

## Implementation

- `software/qt_svg_to_gcode.pyw` (`build_ui`): the central widget is now a
  window-level `QVBoxLayout` holding the static file row, the static action
  row (Preview / Cancel / Save G-code), a horizontal splitter of
  **tabs | OpenGL preview panel**, and the log.
- The Convert tab now contains only the settings sidebar and the G-code
  command list; the preview panel, its playback controls, status, estimate,
  fit/clip row, and the preview progress widgets moved out of the tab.
- The visible artwork label was renamed from `SVG` to `Artwork`, matching the
  dialog that already accepts SVG and raster images.
- `software/tests/test_generator_tabs.py` now asserts that the file row,
  Preview/Save buttons, GL preview, and playback slider are not descendants of
  the tab widget, so the regression cannot return silently.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 3 tests pass, including the new static-chrome assertion.
- Full suite: `python -m unittest discover -s software\tests` -> 222 tests
  pass.
- Offscreen render of the 1500x950 window on the Convert tab and on the Flow
  Field tab: the file row, action row, and preview panel are present in both,
  and the tab bar rebuilds only the left workspace.

## Struggles and rejected approaches

- Keeping the preview inside the Convert tab and duplicating a second preview
  in every generator tab was rejected: it would duplicate playback state and
  split the single source of truth for the built program.
- A vertical layout with the preview above the tabs was rejected because it
  squeezed the generator controls and command list at the target window size.

## Risks and follow-up

- The preview panel is now always on screen; on a small window the tab
  workspace gets proportionally less width, but both splitter sides remain
  resizable.
- Owner review on the running converter is still the next gate before the
  next batch of generator tabs.

## Files

- `software/qt_svg_to_gcode.pyw`: static window furniture and tab splitter.
- `software/tests/test_generator_tabs.py`: static-chrome regression test.
- `software/README.md`: user-facing description of the persistent controls.
