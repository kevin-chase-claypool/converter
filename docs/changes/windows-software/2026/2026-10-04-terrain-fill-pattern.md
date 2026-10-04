---
id: WSW-20261004-002
date: 2026-10-04
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/shading.py
  - software/converter_core/geometry.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_shading.py
  - software/tests/test_raster_import.py
tags:
  - fill
  - shading
  - terrain
  - topographic
  - image-tone
  - plotter-art
related:
  - WSW-20261003-001
  - software/README.md
---

# Terrain fill: topographic contour shading

## Summary

A new `Fill pattern` value, `terrain`, fills a region with the contour lines of
a deterministic fractal height field - a topographic map of hills - instead of
the `concentric` pattern's insets of the region's own outline. Tone is drawn as
contour density: darker fills and darker photo areas tighten the contour
interval on the same terrain, so the pattern shades with the pen the way
`stipple` shades with dots or `sine_gradient` with wave amplitude.

## Reason

Request: "i want to use a propper terrain pattern for shading instead of the
concentric fill." `concentric` insets each region's outline, so its lines echo
the shape they fill and read as mechanical rings; a terrain pattern's lines
belong to the landform, not the region, and its density is what carries tone.

## Implementation

- `software/converter_core/shading.py` gains a terrain section:
  - `terrain_height(x, y, feature_scale, seed, octaves)` sums three octaves of
    deterministic gradient noise (a hash-indexed 16-direction gradient table,
    so a corner costs a hash and a dot product). The field is not clipped, so a
    peak is a peak instead of a plateau at 1.0.
  - `terrain_contours(bounds, spacing, feature_scale, phase, seed, octaves,
    min_step, max_cells)` extracts the level sets with marching squares on a
    grid sampled at half the contour pitch, then chains the segments into
    continuous polylines (`_stitch_contour_segments`), so one contour line is
    one pen-down stroke. Shared cell edges are interpolated from the same two
    samples in the same order, which makes the shared endpoints bit-identical
    and the raw tuples usable as chain keys.
  - The level ladder is calibrated: `TERRAIN_PITCH_CALIBRATION = 0.55` makes
    the average on-paper contour pitch equal the requested spacing (the
    three-octave sum has a gentler typical slope than `pitch / feature`
    assumes). A `feature / 4` clamp keeps at least a few ladder rungs when a
    caller asks for a spacing wider than the hill, and `TERRAIN_MAX_CELLS` /
    `TERRAIN_MAX_LEVELS` bound the work a pathological spacing can request.
- `software/converter_core/geometry.py` adds `terrain_region_contours`, which
  clips the level sets to the region with the existing `_PolygonGrid` /
  `clip_segment_to_region` path (even-odd, with the standard fill pull-back),
  and dispatches `terrain` between the line families and the lattices.
- `software/converter_core/settings.py` registers the pattern, its label
  (`terrain (topographic contours)`), aliases, the `terrain_size_mm` field
  ("Terrain size mm", 0 = `Fill spacing mm x 8`), and the tooltip.
  `TERRAIN_FEATURE_SCALE` lives beside `CELL_SPACING_SCALE`.
- `software/qt_svg_to_gcode.pyw` draws terrain in the real image-tone path:
  one contour interval per shade layer, phase-shifted so the extra levels of
  the same field interleave instead of redrawing a line, masked through the
  existing `append_active_polyline` runs. `describe_fill` reports the contour
  count and says that `Shade levels` darkens this pattern.
- `GEOMETRY_VERSION` is now `2.5-terrain-fill`.

## Verification

- `software/tests/test_shading.py` gains seven `TerrainTests` cases: registry
  and aliases, deterministic field, contours stay inside the bounds and chain
  into long polylines, tighter spacing draws more contour length (2 mm vs
  6 mm on a 120 mm field), vector fill darkens with `Shade levels`, vector fill
  is clipped to the region (checked against all three triangle edges), and the
  grid cap bounds a pathological 0.05 mm spacing on a 1000 mm field.
- `software/tests/test_raster_import.py` gains
  `test_terrain_contours_follow_tone`: the ramp photo's dark half carries more
  than 1.5x the contour length of its light half through the real Qt
  image-tone path.
- Full suite: 198 tests pass (`python -m unittest discover -s software/tests
  -p "test_*.py"`).
- End-to-end on `samples/svg/kindergarten-house-sun.svg` (`Fill spacing 4`,
  `Shade levels 3`, `Fill source = SVG shapes`): 154 contours / 6,088 points /
  7,071 G-code lines in 0.33 s, clipped to the house and sun shapes.
- A 900 x 700 photo at `Fill spacing 4`, `Shade levels 4`: 710 contours /
  30,532 points / 3.0 s; at 2 mm: 2,367 contours / 91,936 points / 5.5 s.

## Struggles and rejected approaches

- The first ladder used `interval = pitch / feature` directly and drew lines
  about 1.8x farther apart than the requested pitch. Measuring the mean pitch
  (area / total contour length) over hill sizes from 4x to 16x the spacing gave
  a consistent 0.55 calibration factor, which is now a named constant.
- Per-layer phase shifts were kept rather than a power-of-two nested ladder:
  nesting doubles the density per shade level, so a four-level photo fill would
  reach `Fill spacing / 8` and paint solid black over the dark half of a photo.
  The layered intervals stay at `spacing / sqrt(levels)` on the darkest tone,
  matching how the other density patterns darken.
- Profiling the 2 mm photo case (13.6 s under `cProfile`) showed the nested
  `corner()` closure in the noise function dominating; inlining it and using
  shared per-axis coordinate lists for bit-identical chaining keys cut the real
  time from 6.9 s to 5.5 s.

## Risks and follow-up

- The pattern is verified on-screen; it has not been plotted on paper yet. The
  dark end of the tone range is the thing to check - at `Shade levels 4` a
  fully dark region draws at `Fill spacing / 2`, and the plotter's actual ink
  spread at that pitch is unmeasured.
- Level sets of the same field never cross, but with `Shade levels > 1` the
  different ladder intervals do bunch where their spacings beat together; that
  is inherent to contour maps and reads as steeper ground, not as a defect.
- A future `terrain` variant could use the image tone itself as the elevation
  (a contour portrait, dense lines at edges) instead of tone as density. That
  is a different drawing and is not implemented here.

## Files

- `software/converter_core/shading.py`: terrain field, marching squares,
  contour chaining and the pitch calibration constants.
- `software/converter_core/geometry.py`: region clipping, dispatch, aliases,
  version bump.
- `software/converter_core/settings.py`: pattern registry, size field, tooltip.
- `software/qt_svg_to_gcode.pyw`: image-tone terrain and the fill log line.
- `software/tests/test_shading.py`, `software/tests/test_raster_import.py`:
  coverage for the new pattern.
- `software/README.md`, `docs/HANDOFF.md`: current-state documentation.
