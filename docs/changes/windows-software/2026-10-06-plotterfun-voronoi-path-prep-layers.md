---
id: WSW-20261006-028
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
  - software/plotterfun_vendor
tags:
  - user-interface
  - generators
related:
  - WSW-20261006-027
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Add Plotterfun, Voronoi, Path Prep, and Layers tools

## Summary

The next list batch plus the requested Voronoi generator are integrated:
**Plotterfun** (the full 22-algorithm web app, vendored and embedded),
**Voronoi** (bounded cells with Lloyd relaxation), **Path Prep**
(vpype-style merge/dedupe/reloop/sort on the preview contours), and
**Layers** (split an imported SVG by pen colour).

## Reason

Plotterfun was too large to port algorithm-by-algorithm and would have
duplicated existing fills, so the upstream static site is vendored instead.
Voronoi was requested directly; Path Prep and Layers complete the
permissive-list tools that fit the current pipeline.

## Implementation

- `software/plotterfun_vendor/`: 28 upstream files (~86 KB, MIT), unmodified.
- `generator_tabs/plotterfun_tab.py`: guarded `QWebEngineView` page with an
  **Export SVG to plot** bridge (`XMLSerializer` capture → temp SVG →
  `host.adopt_artwork`). Falls back to an explanatory label without
  QtWebEngine, like the Kaleidoscope Maps tab.
- `generator_tabs/voronoi_tab.py`: half-plane cell clipping with optional
  Lloyd relaxation and deduplicated boundaries; sites/dots/both styles.
- `generator_tabs/path_prep_tab.py`: linemerge, deduplicate, reloop, and
  linesort over `host.current_contours()`.
- `generator_tabs/layers_tab.py`: XML paint grouping; per-layer SVGs preserve
  document structure; the combo selects a layer or All colours.
- `qt_svg_to_gcode.pyw`: `adopt_artwork()` host method; Help text updated.

## Verification

- New suites: `test_plotterfun_tab.py` (vendor assets, MIT, fallback),
  `test_voronoi_tab.py` (5), `test_path_prep_tab.py` (5),
  `test_layers_tab.py` (3); shell tests updated for the new tools and groups.
- Full suite: `python -m unittest discover -s software\tests` -> 303 tests
  pass.

## Struggles and rejected approaches

- Porting Plotterfun's 22 algorithms was rejected (duplication plus weeks of
  work); vendoring preserves exact upstream behaviour.
- Voronoi's first clipping implementation used a cross product for the
  segment/bisector intersection, which produced unbounded coordinates; the
  dot-product form fixed it.

## Risks and follow-up

- Plotterfun requires QtWebEngine (PySide6-Addons); without it the tab shows
  an explanatory fallback.
- Path Prep and Layers do not replace the full vpype CLI or Inkscape layer
  workflows for complex documents.

## Files

- `software/plotterfun_vendor/`: vendored app and LICENSE.
- `software/generator_tabs/plotterfun_tab.py`, `voronoi_tab.py`,
  `path_prep_tab.py`, `layers_tab.py`: tools.
- `software/generator_tabs/*_NOTICE.md`: attribution.
- `software/tests/test_plotterfun_tab.py`, `test_voronoi_tab.py`,
  `test_path_prep_tab.py`, `test_layers_tab.py`: coverage.
- `software/qt_svg_to_gcode.pyw`, `software/README.md`: host bridge, help,
  and docs.
