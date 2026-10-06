---
id: WSW-20261006-015
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
  - scale
related:
  - WSW-20261006-002
  - WSW-20261006-003
  - WSW-20261006-004
---

# Artwork scale control on every generator tab

## Summary

Every generator tab now has an **Artwork scale** control (10-200%, default
100%) that scales the generated result about the page centre. Flow Field,
Line Draw, and 3D Wireframe gained the control; the new Harmonograph,
Snowflake, and Truchet tabs ship with it.

## Reason

The owner asked for each feature to be able to scale its image, matching the
Convert tab's Scale field. Without it a generated result was locked to the
full page.

## Implementation

- `software/generator_tabs/_tab_common.py`: `scale_polylines(polylines,
  factor, width_mm, height_mm)` scales every point about the page centre and
  returns the input unchanged at 1.0.
- `flow_field_tab.py`, `line_draw_tab.py`, `three_d_tab.py`: Page group gained
  `Artwork scale %`, applied after the generator runs and before the SVG is
  written.
- `software/tests/test_generator_tabs.py` asserts every generator page has a
  `scale_pct` control that defaults to 100; the Truchet and new-tab algorithm
  tests verify that 50% halves the drawn extent about the centre.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 12 tests pass, including the per-tab scale check.
- New tab tests cover scale in their algorithms (Harmonograph, Snowflake) and
  the shared helper (Truchet).
- Full suite: `python -m unittest discover -s software\tests` -> 244 tests
  pass.

## Struggles and rejected approaches

- Regenerating each tool at a smaller size was rejected; scaling the finished
  geometry keeps the scale control independent of every generator's density
  and spacing parameters.

## Risks and follow-up

- Scale above 100% enlarges the artwork past the page and the SVG clips at the
  viewBox edge; 200% is the documented maximum.

## Files

- `software/generator_tabs/_tab_common.py`: scale helper.
- `software/generator_tabs/*_tab.py`: scale controls and application.
- `software/tests/test_generator_tabs.py`, `test_*_tab.py`: scale coverage.
- `software/README.md`: control lists.
