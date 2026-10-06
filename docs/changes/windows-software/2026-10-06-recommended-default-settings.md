---
id: WSW-20261006-026
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
  - defaults
related:
  - docs/research/2026-10-06-generated-tools-accuracy-audit.md
---

# Recommended default settings for every tool

## Summary

Every tool now ships defaults that produce a plottable result, and the
recommended starting settings are documented in `software/README.md` and
available in the app under **Help > Recommended Settings**.

## Reason

The owner asked for the settings that work best as a default for each feature.

## Implementation

- `three_d_tab.py`: the default Source is **Cube** and the default projection
  is **Perspective**, so 3D Wireframe previews immediately instead of asking
  for a file.
- `pixel_art_tab.py`: the generated paths now auto-fit the page (with a
  margin control), so a large `big`-mode grid cannot overflow a 200 mm page.
- `postcard_tab.py`: default text size raised to 6 mm for a readable card.
- `software/qt_svg_to_gcode.pyw`: Help menu gained **Recommended Settings**,
  listing the per-tool starting values.
- `software/README.md`: a Recommended starting settings table for Convert and
  all twelve generators (200 x 200 mm page, 0.3 mm pen, 1:1 preview).
- `software/tests/test_generator_tabs.py`: a new test builds every tool with
  its shipped defaults (page sizes reduced to 80 mm for suite speed) and
  parses the SVG, so a broken default fails the suite.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 18 tests pass, including `test_every_tool_builds_with_shipped_defaults`.
- Full suite: `python -m unittest discover -s software\tests` -> 287 tests
  pass.

## Struggles and rejected approaches

- Changing Pixel Art's default pitch away from the upstream 0.6 mm was
  rejected; auto-fitting the page keeps the upstream default while making it
  usable on any page size.

## Risks and follow-up

- The recommended table assumes a 200 x 200 mm page and a 0.3 mm pen; other
  paper sizes need the spacing/line-count values scaled, which the table
  notes per tool.

## Files

- `software/generator_tabs/three_d_tab.py`, `pixel_art_tab.py`,
  `postcard_tab.py`: default fixes.
- `software/qt_svg_to_gcode.pyw`: Help > Recommended Settings.
- `software/README.md`: settings table.
- `software/tests/test_generator_tabs.py`: defaults test.
