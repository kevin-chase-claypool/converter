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
geometry" stalls. A redundant per-edge boundary scan was also removed from the
fill clip.

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
- `geometry.py`: `_point_in_polygons_even_odd` replaces `point_in_region` in the
  fill clip, dropping the per-edge boundary scan that is measure-zero for a
  regular lattice.
- `read_svg` and the Qt `load_contours` pass `settings.scale` through.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- 800-vertex star, triangular fill, spacing 5: scale 0.2 dropped 5.0 s -> 0.21 s.
- The boundary-scan removal was compared against the original on a diagonal
  lattice and produced byte-identical segments.
- A 3003-vertex "C" shape produced zero fill segments outside its boundary.

## Struggles and rejected approaches

The requested "rasterize a downscaled background image" path was considered, but
the existing vector fill already has the exact clipping we need; scaling its
resolution by the scale factor gives the same proportional contour reduction
without introducing a second, precision-lossy raster pipeline or touching
scale-1.0 output. A fill-polygon vertex decimation was also tried to bound the
remaining clip cost, but stride-sampling a concave outline cut across its
notches and leaked fill segments outside the true boundary, so it was reverted.

## Risks and follow-up

Scaled-down artwork intentionally gets a coarser fill relative to its own size
(the on-paper spacing is held constant). Scale 1.0 output is unchanged. The
remaining known cost is that clipping the fill lattice is still
O(segments x polygon_vertices), so an unusually high-vertex filled outline is
slow at scale 1.0; a spatial edge index is the intended follow-up to make that
exact clipping sublinear without distorting the boundary.

## Files

- `software/converter_core/geometry.py`: scale-aware fill resolution and a faster fill clip.
- `software/qt_svg_to_gcode.pyw`: pass the scale into the shared parser.
