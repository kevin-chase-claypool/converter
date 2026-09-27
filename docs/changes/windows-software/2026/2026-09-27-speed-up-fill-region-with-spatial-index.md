---
id: WSW-20260927-002
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - converter
  - performance
  - fill
  - hatch
  - spatial-index
  - svg
related:
  - WSW-20260927-001
---

# Accelerate fill generation with a polygon spatial index

## Summary

Fill generation no longer tests every subpath against every hatch row and every
inset query. A bounding-box grid narrows each query to the polygons that can
actually reach it, and the exact predicates are run over that smaller set.
Generated geometry is unchanged.

## Reason

Converting `F15_cutaway_black_white_clean_vector.svg` (one compound path with
4,875 subpaths) took 134 s in the geometry stage while motion planning took 2 s.
Two costs dominated, both quadratic in the subpath count:

- `_inset_fill_region` classified outer boundaries from holes by testing each
  contour centroid against every other contour: 4,875 squared = 23.8 M
  containment tests, measured at 17 s.
- `line_region_contours` clipped each hatch row against every polygon edge:
  ~230 rows against 31,817 edges, measured at 31 s per shade level.

`samples/svg/spirit-logo-purple-rgb.svg` hit the same code for 79.6 s.

## Implementation

`software/converter_core/geometry.py`:

- `_PolygonGrid` indexes polygon bounding boxes into a uniform grid sized from
  `sqrt(polygon count)`, and stores each polygon's closed edge list once instead
  of rebuilding it per clip call.
- `candidates_for_point()` returns the polygons whose bounding box can contain a
  point, or nothing when the point is outside the overall bounding box.
  `candidates_for_segment()` returns the polygons whose bounding box can overlap
  a segment. Both are supersets, so callers still run the real predicates.
- `_inset_fill_region` and `line_region_contours` build one grid per region and
  per angle family.
- `clip_segment_to_region` and `_point_in_polygons_even_odd` take an optional
  index. With no index they run exactly the previous code path, so other call
  sites are untouched.
- Below `_FILL_INDEX_MIN_POLYGONS` (8) the grid is not built, leaving
  single-polygon and small-region call sites as cheap as before.

## Verification

Output identity was proved before and after on every `samples/svg/*.svg` plus
the F15 cutaway, using the same settings, by comparing the full contour lists:

- aggregate SHA-256 of the serialised contours: `b8f6a5d8...b603e9e3`, identical
  before and after.
- per-file comparison with normalised coordinate types: **ALL MATCH**.

Measured geometry-stage timing:

| file | before | after |
|---|---|---|
| `F15_cutaway_black_white_clean_vector.svg` | 134.19 s | **1.83 s** |
| `spirit-logo-purple-rgb.svg` | 79.60 s | 45.10 s |

- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 36
  tests. The 5 new cases are in `software/tests/test_fill_spatial_index.py` and
  drive the indexed and unindexed paths with identical inputs.
- `python -m py_compile software\qt_svg_to_gcode.pyw` passes.

## Struggles and rejected approaches

The first reproduction used a small filled square, which was fast and hid the
problem entirely; the cost only appears with thousands of subpaths in one
element. Profiling per stage (parse vs inset vs lattice vs planning) was what
located it, after an initial guess that raster shading was responsible - raster
shading measured 0.61 s.

Replacing the predicates with a faster but approximate containment test was
rejected. The grid keeps the existing exact tests and only reduces how many run,
which is what makes the identity check possible.

## Risks and follow-up

- The grid does not help regions built from a few very large polygons. The
  spirit logo is 105 polygons but 83,233 points, the largest 14,685 points, so
  the candidate polygon is itself the expensive one and the ray-cast still walks
  every edge. It remains 45 s. An edge-level index (y-band buckets for the
  ray-cast, an edge bounding-box grid for segment clipping) is the next step and
  is recorded on the roadmap.
- `_point_in_polygons_even_odd` and `clip_segment_to_region` keep the unindexed
  path for compatibility, so the two implementations must stay in step. The new
  tests compare them directly.

## Files

- `software/converter_core/geometry.py`: grid index and wiring.
- `software/tests/test_fill_spatial_index.py`: identity coverage.
- `software/README.md`: raster-versus-vector shading guidance.
