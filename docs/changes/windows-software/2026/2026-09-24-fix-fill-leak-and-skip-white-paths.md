---
id: WSW-20260924-006
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - fill
  - correctness
  - point-in-polygon
  - invisibility
---

# Fix fill leak and skip invisible white paths

## Summary

Two correctness fixes for traced/vector artwork: a ray-cast bug that could
classify points far outside a polygon as inside (which leaked fill lattice
segments "outside the drawing"), and skipping fully invisible (white/transparent
fill and stroke) elements so a white knockout/background path is not traced as
pen strokes.

## Reason

On a large traced logo (`spirit-logo-purple-rgb.svg`, ~163k vertices across a
white background, a purple logo, and a lavender highlight), the triangular fill
produced lines well outside the logo, and the preview/parse was very slow.

`point_in_polygon` used `max(y2 - y1, 1e-12)` as a division guard. For a
downward edge `y2 - y1` is negative, so `max(..., 1e-12)` returned `1e-12`,
inflating the computed intersection and flipping the containment test for
points to the right of the polygon. Separately, the white full-canvas background
path had white fill and white stroke, which a single-pen plot cannot show, but
its outline was still emitted and its ~80k vertices were still parsed/planned.

## Implementation

- `geometry.py`: `point_in_polygon` divides by `(y2 - y1)` directly; the
  straddle guard already guarantees `y1 != y2` and a well-behaved ratio.
- `geometry.py`: added `stroke_darkness` and `_element_is_visible`;
  `element_contours` returns `[]` for elements whose fill and stroke are both
  white/transparent.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- `spirit-logo-purple-rgb.svg` at scale 0.2: fill bounds went from
  `(-218,-6)-(465,221)` (leaking) to `(4,5)-(221,210)` (the true logo bounds).
- A far-outside point `(1781, 128)` that previously tested inside subpath 3 now
  correctly tests outside.

## Struggles and rejected approaches

The earlier fill-polygon vertex decimation was removed for a similar leak and is
not reintroduced here; the actual cause was the ray-cast denominator clamp.

## Risks and follow-up

Fill clipping is still O(segments x polygon_vertices), so a high-vertex traced
file remains slow at full scale (~12 s at 0.2 for the logo). A spatial edge
index to make clipping sublinear is the intended follow-up.

## Files

- `software/converter_core/geometry.py`: ray-cast fix and invisible-element skip.
