---
id: WSW-20261006-029
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - generators
  - quality
related:
  - WSW-20261006-028
  - WSW-20261006-026
---

# High-quality tier: Stipple/TSP, Reaction-Diffusion, and Vector Trace

## Summary

Three deeper tools join the existing set: **Stipple / TSP** (density
stippling plus route-optimized single-line art), **Reaction-Diffusion**
(Gray-Scott patterns drawn as contours), and **Vector Trace** (clean
outline/hatch tracing). **Path Prep** also gained global 2-opt route
optimization, so every tool's pen-up travel can be shortened.

## Reason

The owner asked for much higher-quality features beyond the earlier
single-algorithm batch, while keeping the existing tools.

## Implementation

- `_raster.py`: shared marching squares, segment stitching, Douglas-Peucker,
  Chaikin smoothing, and Otsu thresholding.
- `stipple_tsp_tab.py`: weighted sampling plus chunked k-means/Lloyd
  relaxation for the stipple, and greedy nearest-neighbour + open-path 2-opt
  for the TSP line; dots, line, or both.
- `reaction_diffusion_tab.py`: Gray-Scott with a nine-point Laplacian,
  centre/random seeding, and one to five contour levels.
- `vector_trace_tab.py`: Otsu/manual threshold, marching-squares outlines,
  simplify/smooth/min-area filters, and angled hatch fill scanned through the
  mask.
- `path_prep_tab.py`: `_two_opt()` reorders and flips polylines to reduce
  pen-up travel (0-100 passes, control added).

## Verification

- New suites: `test_stipple_tsp_tab.py` (5), `test_reaction_diffusion_tab.py`
  (4), `test_vector_trace_tab.py` (5); `test_path_prep_tab.py` gained the
  travel-reduction test. Shell tests cover the new tool order and groups.
- Full suite: `python -m unittest discover -s software\tests` -> 318 tests
  pass.

## Struggles and rejected approaches

- scipy is not installed, so stippling uses a numpy weighted k-means instead
  of scipy.spatial.Voronoi; the visual result is equivalent for stipple art.
- Full 2-opt is O(n^2) per pass; passes default to 5 and are capped at 100.

## Risks and follow-up

- Reaction-Diffusion cost grows with grid area times steps; the defaults
  (128 x 128, 4000 steps) keep a build in the low seconds.
- TSP 2-opt on 3000 points is the slowest path; reduce points or passes.

## Files

- `software/generator_tabs/_raster.py`, `stipple_tsp_tab.py`,
  `reaction_diffusion_tab.py`, `vector_trace_tab.py`, `path_prep_tab.py`.
- `software/generator_tabs/*_NOTICE.md`: attribution.
- `software/tests/test_stipple_tsp_tab.py`,
  `test_reaction_diffusion_tab.py`, `test_vector_trace_tab.py`,
  `test_path_prep_tab.py`, `test_generator_tabs.py`: coverage.
- `software/README.md`, `software/qt_svg_to_gcode.pyw`: docs and help.
