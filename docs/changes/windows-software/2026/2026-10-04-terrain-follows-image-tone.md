---
id: WSW-20261004-003
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
  - WSW-20261004-002
  - software/README.md
---

# Terrain on image tone follows the photo's shading

## Summary

On image tone (photos, gradients, embedded images) the `terrain` fill no longer
draws a synthetic noise field: the picture's own darkness **is** the elevation,
so the contour lines trace the photo's features - a topographic portrait.
Darker pixels are higher ground, so hair and shadows fill with contours and a
blown-out sky stays blank paper. Flat SVG shapes keep the synthetic height
field, because a flat fill has no tone gradient inside it to trace.

## Reason

Operator feedback on a real photo (`momandbennett.jpg`): "compared to
momandbennett.jpg it seems that the terrain mapping is very random based on the
shading" - the noise field's swirls had no relationship to the faces. A terrain
pattern that is used for shading should be a map *of the shading*, not a
texture modulated by it.

## Implementation

- `software/converter_core/shading.py`:
  - `tone_terrain_contours(bounds, spacing, darkness, blur, ...)` samples the
    caller's `darkness(x, y)` on a grid, box-blurs it, and extracts the level
    sets. Elevation is the tone itself.
  - The grid pitch follows `Fill spacing / 2`, but the Qt caller caps it at two
    source pixels so thin features (a scan's linework) cannot fall between
    grid lines.
  - The level interval comes from the image's mean tone gradient magnitude over
    its inked area (cells whose average tone is above `INK_FLOOR`). By the
    coarea identity the average gap between level sets is
    `area x interval / total variation`, so sizing the interval this way makes
    `Fill spacing mm` mean the average gap on paper whatever the photo
    contains. Blank paper is excluded from the average so it does not tighten
    the inked area's pitch. `TERRAIN_TONE_CALIBRATION` is 1.0 and recorded as a
    measured constant.
  - The marching-squares extractor, the shared grid geometry and the
    segment chaining are now helpers (`_marching_squares`,
    `_contour_grid_geometry`, `_stitch_contour_segments`, `_box_blur`) shared
    with the synthetic-field `terrain_contours`, which is unchanged in
    behaviour.
- `software/qt_svg_to_gcode.pyw`: the image-tone `terrain` branch calls
  `tone_terrain_contours` with `Fill spacing` as the average gap and
  `Terrain size mm` as the smoothing radius (0 follows half the spacing).
  `Shade levels` deliberately does not apply here. The sampling bounds are
  inset by half a source pixel so the outermost grid line lands on a pixel
  centre; without it the tone cliff at the image border drew a rectangle of
  contours around the artwork.
- `software/converter_core/settings.py`: the `terrain_size_mm` tooltip explains
  both meanings (smoothing radius on image tone, hill width on flat shapes).
  `describe_fill` reports the new behaviour, and `GEOMETRY_VERSION` is
  `2.6-tone-terrain`.

## Verification

- On `momandbennett.jpg` (532 x 563 px, fitted to the bed): a 4 mm request
  measures a 4.07 mm mean gap and a 2 mm request 2.05 mm, extracted in 0.27 s
  and 0.60 s. The render shows the faces, hair and glasses as contour
  structures.
- End-to-end G-code for the 4 mm portrait: 402 contours / 30,456 points /
  27,410 lines, planned and emitted in 0.42 s;
  `python tools\check_gcode_motion.py tmp\...gcode --strict` passes (largest
  bed step 13.70 deg against the 15.0 cap, largest A rate 250 against 250, no
  bare `G0` rotation).
- `software/tests/test_shading.py` gains a `ToneTerrainTests` class: a linear
  ramp draws vertical lines exactly `Fill spacing` apart (5.0 mm gaps for a
  5.0 mm request), a dark disc's contours stay on the disc edge, a flat field
  draws nothing, smoothing turns a cliff into a slope, and output is
  deterministic.
- `software/tests/test_raster_import.py`'s terrain case now builds a ramp-only
  photo and asserts the contour lines are near-vertical columns about 4 mm
  apart through the real Qt image-tone path.
- A 900 x 700 px photo: 4 mm gives 65 contours / 37,657 points in 0.45 s, 2 mm
  gives 127 contours / 73,573 points in 0.57 s.
- Full suite: 204 tests pass.

## Struggles and rejected approaches

- The first calibration used `0.5 * (mean|dx| + mean|dy|)` as the gradient
  magnitude and absorbed its ~1.57x underestimate in a fitted factor. A pure
  ramp exposed it (3.95 mm gaps for a 5 mm request); using the true
  `hypot(dx, dy)` mean and a calibration of 1.0 makes a linear ramp exact. The
  earlier 1.58 factor was removed with it.
- Normalising the mean gradient over *sloped* cells was tried next: it fixed
  the ramp but made hard-edged art degenerate (a step edge's only sloped cells
  are enormous, so the interval exceeded the tone range and nothing was drawn).
  The average is now over the inked area, which is well behaved for both soft
  photos and hard-edged scans.
- The noise field was kept for flat SVG shapes rather than replaced: a
  constant-tone element has no level sets to trace, and the synthetic field is
  what makes a flat silhouette fill read as terrain.
- Sampling the full view rectangle instead of the pixel centres drew a
  rectangle of contours around the whole photo, because `darkness_at` returns
  0 outside the image and every level crossed that cliff.

## Risks and follow-up

- Flat plateaus (a plain wall, a flat shirt) produce no contours by
  construction - that is what a contour map does. `Terrain size mm` trades
  detail for broader landforms, but a density-based style (stipple, halftone)
  remains the tool for flat tone.
- A hard tone edge stacks every level in one cell, so the drawn band at a
  silhouette is dense (the map's cliff). If that reads as a heavy halo on
  paper, the next step is a minimum-gap decimation that drops a level where it
  would fall within some distance of an already emitted line.
- Not plotted on paper yet; the ink behaviour at cliff bands is the thing to
  watch on the first test sheet.

## Files

- `software/converter_core/shading.py`: tone-terrain generator, shared
  marching-squares/blur/chaining helpers.
- `software/converter_core/geometry.py`: version bump.
- `software/converter_core/settings.py`: tooltip.
- `software/qt_svg_to_gcode.pyw`: image-tone terrain branch and fill log line.
- `software/tests/test_shading.py`, `software/tests/test_raster_import.py`:
  tone-terrain coverage.
- `software/README.md`, `docs/HANDOFF.md`: current-state documentation.
