---
id: WSW-20261007-006
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - user-interface
  - opengl
related:
  - WSW-20261007-003
---

# Add a Red motion lines toggle to the preview panel

## Summary

The preview panel now has a **Red motion lines** checkbox next to **Fill bed**
and **Fit inside**. It turns the generated X/Y pen-down machine path overlay
(the red lines) on and off directly from the preview, and stays in sync with
the existing **Preview settings > Show X/Y pen-down path** checkbox and the
**View > Pen-down Path** menu action.

## Reason

Project-owner request: "in the preview area i need an option to turn the red
lines on and off." The toggle existed only in the sidebar's Preview settings
group and the View menu, away from the preview where the clutter matters.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `preview_motion_check` is added to the
  bottom preview row and two-way connected to `show_pen_down_path`, which
  already drives `GLPreview.set_show_pen_down_path`, the sidebar checkbox and
  the View menu action. The tooltip names the View-menu equivalent.

## Verification

- New tool-shell test: the checkbox lives inside `preview_panel`, defaults on,
  turning it off clears `GLPreview.show_pen_down_path` and the sidebar
  checkbox, and turning the sidebar checkbox back on restores the panel
  checkbox and the GL flag.
- Full suite and `tools\docs_index.py --write` / `--check` re-run before
  commit.

## Struggles and rejected approaches

None: the state already existed; this only surfaces it in the preview panel.

## Risks and follow-up

None. The default remains on, matching the previous behavior.

## Files

- `software/qt_svg_to_gcode.pyw`: preview-panel checkbox and sync.
- `software/tests/test_generator_tabs.py`: coverage.
- `software/README.md`: preview controls documentation.
