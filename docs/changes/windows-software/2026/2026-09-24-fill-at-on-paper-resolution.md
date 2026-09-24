---
id: WSW-20260924-005
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - performance
  - fill
  - scale
  - shading
---

# Generate fill at on-paper resolution when the artwork is scaled down

## Summary

When the SVG is scaled below 1.0, the fill (hatch/lattice), curve flattening,
and pattern sizes are now generated at the coarser SVG-space resolution that
matches the final on-paper density, instead of at full source resolution and
shrinking afterward. A scaled-down drawing now produces proportionally fewer
contours (roughly scale^2), which removes the multi-minute "Parsing SVG
geometry" stalls. Fill-clipping polygons are also capped at 512 vertices and a
redundant per-edge boundary scan was removed from the fill clip.

## Reason

`parse_svg_geometry` built the fill lattice in SVG-space at the configured
spacing and only afterward did `apply_geometry_settings` scale it. The cost of
that fill is therefore independent of the scale, and `clip_segment_to_region`
is O(segments x polygon_vertices), so a high-vertex filled outline with a fine
lattice blew up to minutes even when the drawing was tiny on paper.

## Implementation

- `geometry.py`: `parse_svg_geometry` accepts a `scale` argument. For `0 <
  scale < 1` it multiplies `tolerance`, `hatch_spacing`, `triangle_size`, and
  the pattern sizes by `1/scale`, keeping the on-paper fill density constant
  and emitting `scale^2` fewer SVG-space segments.
- `geometry.py`: `_simplify_fill_polygon` decimates fill-clipping polygons to
  at most `FILL_MAX_POLYGON_VERTICES = 512`; the full-resolution outline is
  still drawn as the stroke.
- `geometry.py`: `_point_in_polygons_even_odd` replaces `point_in_region` in the
  fill clip, dropping the per-edge boundary scan that is measure-zero for a
  regular lattice.
- `read_svg` and the Qt `load_contours` pass `settings.scale` through.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- 800-vertex star, triangular fill, spacing 5: scale 0.2 dropped 5.0 s -> 0.21 s.
- 3000-vertex filled outline: scale 0.2 read in 0.39 s vs 5.2 s at scale 1.0.
- The boundary-scan removal was compared against the original on a diagonal
  lattice and produced byte-identical segments.

## Struggles and rejected approaches

The requested "rasterize a downscaled background image" path was considered, but
the existing vector fill already has the exact clipping we need; scaling its
resolution by the scale factor gives the same proportional contour reduction
without introducing a second, precision-lossy raster pipeline or touching
scale-1.0 output.

## Risks and follow-up

Scaled-down artwork intentionally gets a coarser fill relative to its own size
(the on-paper spacing is held constant). Fill-only shapes with no stroke will
show the 512-vertex simplification at their boundary only when the source
outline exceeds 512 vertices. Scale 1.0 output is unchanged apart from that
decimation threshold.

## Files

- `software/converter_core/geometry.py`: scale-aware fill resolution, fill-polygon decimation, faster fill clip.
- `software/qt_svg_to_gcode.pyw`: pass the scale into the shared parser.
