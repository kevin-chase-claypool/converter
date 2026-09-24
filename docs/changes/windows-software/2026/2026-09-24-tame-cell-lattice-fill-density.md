---
id: WSW-20260924-003
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - shading
  - fill-pattern
  - performance
  - lattice
---

# Tame cell-lattice fill density and fix triangular lattice over-generation

## Summary

The cell-based fill patterns (`triangular`, `diamonds`, `hexagonal`, `circles`)
no longer fall back to the raw `Fill spacing` when their dedicated size field is
left at zero. They instead fall back to `Fill spacing × 6`, and the triangular
lattice generator no longer over-generates columns for tall regions.

## Reason

A user reported that previewing `crosshatch` was fast but `triangular` was
extremely slow, and that `triangular` appeared to raster-shade the entire image
even with raster shading unchecked. Two independent problems were behind this:

1. A cell pattern's size field defaults to `0`, which previously fell back to
   `Fill spacing` (commonly 5 mm). A 5 mm triangular cell is roughly 36x denser
   than a 30 mm cell, so an unset `Triangle size` produced a huge, slow mesh
   that looked like full-image raster shading.
2. `tile_shape_contours` and the Qt app's `lattice_from_closed_contours` computed
   the triangular lattice column range with a mixed X/Y bound
   (`min_x - max_y`, `max_x - min_y`), generating more columns than the lattice
   actually needs.

## Implementation

- `settings.py`: added `CELL_PATTERNS` and `CELL_SPACING_SCALE = 6.0`;
  `pattern_size_override` now scales the fallback for cell patterns.
- `geometry.py`: `_pattern_spacing` applies the same scale, and
  `tile_shape_contours` bounds the triangular `i` range from the row range so the
  j-dependent horizontal offset is accounted for correctly.
- `qt_svg_to_gcode.pyw`: `lattice_from_closed_contours` uses the corrected
  triangular `i` range.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- `raster-shading-math.svg`, raster off, fill spacing 5, shade levels 4:
  crosshatch 58 ms; triangular (size 0) 649 ms; triangular (size 30) 525 ms.
  Before the change, triangular at size 0 resolved to a 2.5-5 mm lattice.
- A 100×100 mm square with side 30 tiles exactly to its 0-100 mm bounds with
  11 chained contours and no coverage gap.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The lattice fill is still heavier than line hatch because it emits short mesh
segments and chains them, while line patterns emit a few long lines. Scaling the
unset cell size removes the pathological dense case; a full rewrite of the
lattice generator into long zigzag polylines is left as a possible follow-up
for very large artwork.

## Risks and follow-up

Users who relied on `0` meaning "inherit `Fill spacing` exactly" will now get a
6x larger cell. An explicit non-zero size still wins and is unchanged. If a
per-cell scale other than 6 is wanted, `CELL_SPACING_SCALE` is the single
constant to adjust.

## Files

- `software/converter_core/settings.py`: cell-pattern fallback scale.
- `software/converter_core/geometry.py`: spacing fallback + triangular lattice bounds.
- `software/qt_svg_to_gcode.pyw`: triangular lattice bounds in the raster/lattice path.
