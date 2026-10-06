---
id: WSW-20261006-008
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
  - WSW-20261006-005
  - WSW-20261006-007
---

# Move Preview and Cancel into the preview panel

## Summary

**Preview** and **Cancel** now sit inside the shared preview panel, directly
under the playback controls. **Save G-code** moved up beside the G-code path,
and the separate top action row was removed.

## Reason

The Preview button builds and stops the preview shown in that panel, so the
owner asked for the action to live with the thing it controls instead of in a
full-width row above the tabs. With Preview and Cancel gone, the old action
row held only Save G-code and wasted vertical space.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the playback controls row is followed by an
  equal-width Preview / Cancel row inside the preview panel; the buttons are
  created there instead of in the removed top row.
- **Save G-code** is created in the artwork/G-code file row, after the G-code
  Browse button, so export stays static and visible on every tab.
- `software/tests/test_generator_tabs.py` pins the new placement: Preview and
  Cancel are descendants of `preview_panel`, Save G-code is not, and all of
  them remain outside the tab widget.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 6 tests pass, including the new placement test.
- Full suite: `python -m unittest discover -s software\tests` -> 225 tests
  pass.
- Offscreen render of the 1500x950 window: the file row ends with Save
  G-code, the tab workspace starts directly below it, and the preview panel
  shows playback controls followed by the Preview / Cancel row, status,
  estimate, and progress.

## Struggles and rejected approaches

- Leaving a top row that held only Save G-code was rejected as wasted chrome;
  moving Save next to the G-code path keeps export static without a second
  row.

## Risks and follow-up

- None functional: the buttons keep their existing handlers, enabled states,
  and building/cancelling behavior.

## Files

- `software/qt_svg_to_gcode.pyw`: button placement and row removal.
- `software/tests/test_generator_tabs.py`: placement regression test.
- `software/README.md`: user-facing description.
