---
id: WSW-20261003-001
date: 2026-10-03
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/shading.py
  - software/converter_core/geometry.py
  - software/converter_core/settings.py
  - software/converter_core/__init__.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_shading.py
  - software/tests/test_raster_import.py
tags:
  - fill
  - shading
  - stipple
  - halftone
  - tsp
  - image-tone
  - plotter-art
related:
  - WSW-20261001-004
  - software/README.md
---

# Stipple, halftone and single-line (TSP) photo shading

## Summary

Three new `Fill pattern` values for imported JPG/PNG artwork:

- `stipple` — blue-noise dots whose density follows tone (the hand-stippled
  portrait look).
- `halftone` — a fixed-pitch grid of dots whose radius follows tone (the
  printed-halftone look).
- `tsp` — the stipple points walked nearest-neighbour into one continuous
  pen-down path (the single-line portrait look).

All three share `Dot spacing mm` as their pitch and are deterministic, so the
same photo produces the same marks on every preview and save.

## Reason

Request: "there are many different means of dealing with shading on
reddit/plotterart ... implement some of the most popular ways ... several means
of doing shading on images i import jpg, png". The converter already had
density hatching (`Shade levels`), concentric tone contours and the
`sine_gradient` SquiggleDraw-style wave, but the three most recognisable photo
styles — stipple, halftone and single-line — were missing.

## Implementation

- `software/converter_core/shading.py` (new) holds the image-agnostic
  generators. Each takes a `bounds` rectangle, an `inside(x, y)` predicate and a
  `darkness(x, y) -> 0..1` callable, so the vector path can pass polygon
  membership with a constant tone while the image-tone path passes sampled
  pixels. Nothing imports Qt, which keeps the behaviour unit-testable.
  - `stipple_points` throws candidates uniformly and accepts them when they are
    in ink, above `INK_FLOOR` (0.04), pass a tone-weighted random draw, and are
    at least `min_dist` from every accepted point. A fixed `seed` makes the
    field reproducible.
    - Each accepted point is plotted as a small closed circle
      (`stipple_mark_radius` / `dot_mark_contours`), sized on paper at half the
      pen tip or 0.25 mm radius, whichever is larger. A dot drawn as a fraction
      of the fill spacing disappears at bed-filling scales, because
      `apply_geometry_settings` drops any contour shorter than 1 mm on paper.
  - `halftone_contours` places a square lattice and sizes each dot
    `spacing / 2 * sqrt(tone)` so ink area tracks tone.
  - `greedy_single_line` orders points with a spatial-grid nearest-neighbour
    search, so a several-thousand-point stipple stays tractable.
- `software/converter_core/geometry.py` imports the module, adds
  `stipple_region_contours`, `halftone_region_contours` and
  `tsp_region_contours`, and dispatches the three patterns in
  `fill_region_pattern_contours` before the `Shade levels` density step. They
  read tone directly, so they ignore `Shade levels` the same way
  `sine_gradient` does.
- `software/converter_core/settings.py` registers the patterns, aliases, labels
  and the shared `dot_spacing_mm` size field, plus a tooltip for that field.
- `software/qt_svg_to_gcode.pyw` handles the three patterns in
  `raster_shade_contours` (the real JPG/PNG image-tone path) and reports them in
  `describe_fill`.

## Verification

- `software/tests/test_shading.py` (new, 14 tests) pins density/radius following
  tone, minimum stipple spacing, reproducibility, the single line visiting every
  point once, and the vector fill path.
- `software/tests/test_raster_import.py` gained a case that builds each pattern
  through the real Qt image-tone path from a saved PNG.
- Regression coverage: `test_shading.py` gained three dot-size cases (radius
  floor, exactly closed circles, and a 300 x 400 unit artwork at `Scale 0.3`
  through `apply_geometry_settings`), and `test_raster_import.py` builds a
  1200 x 900 photo through the full `load_contours` fit-and-scale pipeline,
  asserting every stipple dot is more than 0.3 mm across.
- Full suite: 189 tests pass (`python -m unittest discover -s software/tests
  -p "test_*.py"`).

## Struggles and rejected approaches

The first cut of the nearest-neighbour grid computed its search radius from the
wrong sign, so `tsp` collapsed to a single point; the test caught it and the
radius is now the Chebyshev distance to the grid's bounding box. Weighted
Voronoi relaxation was rejected: it is the canonical stipple algorithm but needs
an iterative centroid solver, while the tone-weighted Poisson-disc sampler here
is simpler, deterministic and already reads as stipple.

The first cut also drew each stipple dot as a short horizontal dash whose length
was a fraction of the fill spacing (5.5 %, with a sampling-step floor). That
survived the unit tests, which build small artworks at `Scale ~1`, but on a
bed-filling photo (`Scale 0.35`) every dot shrank to ~0.44 mm on paper and
`apply_geometry_settings` dropped all of them as sub-pen-width slivers -
selecting `stipple` produced an empty program. Dots are now closed circles with
the radius chosen in paper millimetres and divided by the artwork scale, so the
geometry filter sees a ~1.6 mm circumference and every dot survives. The vector
path needed the same treatment: `clip_polyline_to_region` returns one two-point
contour per circle edge, so the clipped dot edges are re-chained with
`chain_segments_to_paths` before they are filtered - the same fix also keeps
small halftone dots in the vector path.

## Risks and follow-up

- The single-line tour is greedy nearest-neighbour, not an optimal TSP, so it
  is faster but can leave an occasional long bridge. An optional 2-opt or
  real TSP pass would improve it at higher point counts and is left as a
  follow-up.
- A stipple dot never shrinks below ~0.5 mm across (pen tip and 0.25 mm radius
  floors). A user wanting finer marks needs a finer pen, not a smaller
  `Dot spacing mm`; the pitch only sets the minimum gap between dots.
- Stipple/halftone/tsp have not been plotted on paper yet; the on-screen
  geometry is verified, and the physical density reading still needs a test
  sheet.

## Files

- `software/converter_core/shading.py`: new image-shading primitives.
- `software/converter_core/geometry.py`: vector-path dispatch and wrappers.
- `software/converter_core/settings.py`: pattern registry and shared size field.
- `software/converter_core/__init__.py`: export the new module.
- `software/qt_svg_to_gcode.pyw`: image-tone dispatch and fill descriptions.
- `software/tests/test_shading.py`: unit tests for the new generators.
- `software/tests/test_raster_import.py`: integration coverage of the Qt path.
