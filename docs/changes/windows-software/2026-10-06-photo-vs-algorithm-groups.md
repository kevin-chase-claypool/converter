---
id: WSW-20261006-027
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - navigation
  - generators
related:
  - WSW-20261006-021
  - WSW-20261006-026
---

# Group tools by input type: Photo-based and Algorithm only

## Summary

The dashboard and the Tools menu now divide the generators by what they need:
**Photo-based** (Line Draw, SquiggleCam, Pixel Art) require an image from
File > Open Artwork, and **Algorithm only** (Flow Field, 3D Wireframe,
Harmonograph, Snowflake, Truchet, Text, Substitution, Postcard, Wobble)
generate from parameters. Convert stays in a **Core** group on the dashboard.

## Reason

The owner asked for the tool list to be divided between photo-based tools and
algorithm-only tools, so the starting point for each tool is obvious.

## Implementation

- Each tab's `GROUP` constant is now **Photo-based** or **Algorithm only**.
  Flow Field (optional image-edge source), 3D (optional mesh file), and
  Wobble (uses the current preview contours) are algorithm-only with the
  optional input noted in the README.
- `build_dashboard()` renders the groups in the order Core, Photo-based,
  Algorithm only; `build_menus()` creates the same two submenus under Tools
  in the same order.
- `software/README.md` lists the tools under the two headings and notes the
  optional inputs.
- `software/tests/test_generator_tabs.py` asserts the exact membership of
  both groups and the two Tools submenus.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 19 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 288 tests
  pass.

## Struggles and rejected approaches

- A third "hybrid" group was rejected: Flow Field, 3D, and Wobble all work
  without a photo, so algorithm-only with a noted optional input keeps the
  split to the two categories the owner asked for.

## Risks and follow-up

- The old Line art / Patterns / 3D / Text & layout groups are gone; the Tools
  menu shortcuts are unchanged because the tool order is unchanged.

## Files

- `software/generator_tabs/*_tab.py`: GROUP constants.
- `software/qt_svg_to_gcode.pyw`: dashboard and menu group ordering.
- `software/tests/test_generator_tabs.py`: grouping tests.
- `software/README.md`: tool list by input type.
