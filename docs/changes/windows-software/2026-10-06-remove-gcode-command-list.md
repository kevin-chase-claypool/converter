---
id: WSW-20261006-010
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - preview
related:
  - WSW-20261006-009
---

# Remove the G-code command list and let the preview fill the workspace

## Summary

The G-code command list pane was removed from the UI. The preview panel now
fills the entire area to the right of the feature settings (the tab pane), so
the window is a two-column workspace under the static file row.

## Reason

The owner decided an in-app G-code listing is unnecessary; the saved `.gcode`
file is the artifact to inspect. Removing the pane gives the preview the
remaining width instead of splitting it with a read-only list.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the window splitter is now
  **tabs | preview** with the tabs pane fixed to its content and the preview
  taking the stretch. `command_list`, `command_selected`, the program-row
  mapping, and the `set_index(..., sync_command_list=...)` parameter were
  deleted; playback still drives the preview index and status line.
- The unused `QListWidget`, `QListWidgetItem`, and `QFont` imports were
  removed.
- `software/tests/test_generator_tabs.py` now asserts that `command_list` no
  longer exists and that the splitter holds exactly the tab pane and the
  preview panel.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 7 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 226 tests
  pass.
- Offscreen render of the 1500x950 window: settings pane on the left and the
  preview panel filling all remaining width, with playback controls, Preview /
  Cancel, status, estimate, and progress at its bottom.

## Struggles and rejected approaches

- Keeping the list hidden or collapsible was rejected: the owner wants it gone
  from the UI, and the saved file already carries the complete program.

## Risks and follow-up

- Inspecting individual commands now requires opening the saved G-code file.
  The preview still reports command count, reach, and timing in its status.

## Files

- `software/qt_svg_to_gcode.pyw`: splitter layout and removal of the list,
  its selection sync, and the program-row mapping.
- `software/tests/test_generator_tabs.py`: layout regression test.
- `software/README.md`: user-facing description.
