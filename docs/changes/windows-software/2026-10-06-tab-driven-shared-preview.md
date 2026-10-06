---
id: WSW-20261006-007
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs
tags:
  - user-interface
  - generators
  - preview
related:
  - WSW-20261006-001
  - WSW-20261006-002
  - WSW-20261006-003
  - WSW-20261006-004
  - WSW-20261006-005
  - WSW-20261006-006
---

# Tab-driven preview in the shared preview panel

## Summary

Preview and Save now act on the **active tab**. Convert previews the Artwork
row; Flow Field, Line Draw, and 3D Wireframe each build their own SVG from
their controls when the static Preview button is pressed. Every result runs
through the same converter pipeline and appears in the one shared preview
panel with the existing status, command count, timing estimate, and progress
bar. The per-tab previews, per-tab Generate buttons, and **Use in Convert**
hand-off are removed.

## Reason

The owner's model: switching tabs selects which feature set Preview should
use, and the preview result must change only when Preview is pressed. The
earlier layout kept the OpenGL panel locked to the Convert tab and gave each
generator its own small preview, so the shared panel showed the wrong thing
after a tab switch and the real result never reached the shared status.

## Implementation

- `MainWindow.resolve_active_source()` returns the Convert artwork path when
  the Convert tab is active and calls `build_svg()` on a generator tab
  otherwise. Tabs raise `ValueError` with a user-facing message when input is
  missing; the window shows that message.
- `preview()` and `convert()` (Save G-code) both use the resolver, so the
  shared preview and the exported program always describe the active tab.
- `on_tab_changed()` never rebuilds. It marks the visible preview as belonging
  to another tab and the stale label reads "Preview is from another tab -
  press Preview to rebuild." until Preview is pressed again on that tab.
- Generator tabs now implement `build_svg()` and own no preview, no file
  picker, and no hand-off button; `host.use_svg()` and the per-tab
  `PreviewCanvas` were removed. The tab contract and `software/README.md`
  describe the new model.

## Verification

- `software/tests/test_generator_tabs.py` -> 5 tests pass: Convert is the
  first tab, static import/export/preview stay outside the tabs, the Convert
  resolver returns the Artwork row's file, a tab switch marks the preview
  stale without rebuilding, and the active generator's SVG reaches the
  converter's contour pipeline.
- `test_flow_field_tab.py` -> 4 pass; `test_line_draw_tab.py` -> 4 pass;
  `test_three_d_tab.py` -> 6 pass; all three tab tests build through
  `build_svg()` and parse the returned SVG.
- End-to-end offscreen check: with Flow Field active,
  `resolve_active_source()` returned a parsed `flow-field-*.svg` and the tab
  identity.
- Full suite: `python -m unittest discover -s software\tests` -> 224 tests
  pass.

## Struggles and rejected approaches

- Keeping the per-tab preview as a "mini preview" was rejected: it duplicates
  the shared panel and leaves the Preview button ambiguous.
- Disabling Save until a re-preview was considered, but the resolver makes
  Save rebuild the active tab's result, so exporting a stale other-tab result
  is impossible without freezing the button.

## Risks and follow-up

- `build_svg()` runs on the UI thread before the threaded converter pipeline
  starts, so a heavy generator (dense flow field, large mesh) briefly blocks
  the window. Moving generation into the worker is a follow-up if it becomes
  noticeable.
- Owner review of the per-tab preview results is the next gate.

## Files

- `software/qt_svg_to_gcode.pyw`: active-tab resolver, stale-tab tracking,
  preview/Save wiring.
- `software/generator_tabs/_tab_common.py`: control-column tab base, no
  preview canvas.
- `software/generator_tabs/flow_field_tab.py`,
  `line_draw_tab.py`, `three_d_tab.py`: `build_svg()` implementations.
- `software/generator_tabs/README.md` and `__init__.py`: contract.
- `software/tests/test_generator_tabs.py`, `test_flow_field_tab.py`,
  `test_line_draw_tab.py`, `test_three_d_tab.py`: coverage.
- `software/README.md`: user-facing model.
