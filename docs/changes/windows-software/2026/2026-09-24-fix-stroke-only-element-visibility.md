---
id: WSW-20260924-012
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - visibility
  - stroke
  - regression
---

# Fix stroke-only elements being treated as invisible

## Summary

Elements that are stroke-only with no explicit `stroke-width` are visible again.
They were being skipped, so SVGs like `sample.svg` produced zero contours.

## Reason

`_element_is_visible` relied on `has_visible_stroke`, which checks
`stroke_width(element) > 0`. `stroke_width` returns 0.0 when the SVG omits
`stroke-width`, even though the SVG default is 1, so a plain
`stroke="black"` shape was treated as invisible and dropped.

## Implementation

- `geometry.py`: `_element_is_visible` now checks the stroke color directly
  (present, not `none`, not white) instead of going through the width check.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- `sample.svg` (stroke-only rect/circle/path) now yields 3 contours and 545
  G-code lines instead of 0 contours and 10 lines.

## Struggles and rejected approaches

Fixing `stroke_width` to return the SVG default of 1 was considered but would
change `expand_strokes` outlining; the targeted visibility check avoids that
blast radius.

## Risks and follow-up

`stroke="black" stroke-width="0"` is now treated as visible (the width is
ignored), which is acceptable for this plotter. `stroke_width` still returns 0
for omitted width; that pre-existing behavior is unchanged.

## Files

- `software/converter_core/geometry.py`: element-visibility fix.
