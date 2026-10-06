---
id: WSW-20261006-006
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - user-interface
  - generators
  - import
related:
  - WSW-20261006-005
  - WSW-20261006-002
  - WSW-20261006-003
---

# Remove redundant per-tab image pickers

## Summary

Flow Field and Line Draw no longer carry their own image file pickers. Both
tabs read the file loaded in the static **Artwork** row and show its filename;
if nothing is loaded they point at that row and refuse to generate.

## Reason

After import and export became static window chrome, the per-tab image Browse
buttons were a second import path for the same job. The owner flagged the Flow
Field tab as redundant on 2026-10-06.

## Implementation

- `MainWindow.artwork_path()` returns the static Artwork row's current path.
- `software/generator_tabs/README.md` makes this a contract rule: a tab must
  not add an artwork picker; it reads `host.artwork_path()`.
- `flow_field_tab.py` and `line_draw_tab.py` replace their file row and Browse
  button with a read-only filename label that refreshes when the tab is shown
  or generated, and they report an error when no artwork is loaded.
- The 3D Wireframe tab keeps its model picker on purpose: OBJ/STL files are not
  an Artwork type the static row accepts.

## Verification

- `python -m unittest discover -s software\tests -p "test_flow_field_tab.py" -v`
  -> 4 tests pass.
- `... -p "test_line_draw_tab.py" -v` -> 4 tests pass, including the tab
  hand-off with the fake host supplying the artwork path.
- `... -p "test_generator_tabs.py" -v` -> 3 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 222 tests
  pass.

## Struggles and rejected approaches

- Keeping a per-tab picker "just in case" was rejected; it recreates the same
  two-source-of-truth problem the static row was added to remove.
- Adding OBJ/STL to the static Artwork filter was rejected for now because the
  Convert tab cannot import a mesh, but the model picker remains local to the
  3D tab.

## Risks and follow-up

- A generator tab shows the artwork filename only when it is shown or when
  Generate is pressed, not live while another tab is active.

## Files

- `software/qt_svg_to_gcode.pyw`: `artwork_path()` host accessor.
- `software/generator_tabs/README.md`: no-second-import contract rule.
- `software/generator_tabs/flow_field_tab.py`: static artwork input.
- `software/generator_tabs/line_draw_tab.py`: static artwork input.
- `software/tests/test_flow_field_tab.py`, `test_line_draw_tab.py`: fake host
  artwork path.
- `software/README.md`: user-facing control list.
