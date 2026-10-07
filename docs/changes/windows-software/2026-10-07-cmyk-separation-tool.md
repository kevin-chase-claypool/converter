---
id: WSW-20261007-001
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/converter_core/cmyk.py
  - software/converter_core/gcode.py
  - software/converter_core/shading.py
  - software/qt_svg_to_gcode.pyw
tags:
  - cmyk
  - color-separation
  - generator-tabs
  - gcode
  - cost-analysis
  - x-theta
  - y-theta
related:
  - docs/research/2026-10-07-cmyk-separation-prior-art.md
  - WSW-20261006-028
---

# Add the CMYK separation tool with one G-code file per ink

## Summary

A new **CMYK** tool page splits a PNG/JPG into cyan, magenta, yellow and black
ink layers, screens each layer as halftone or stipple dots, and produces one
complete G-code program per ink. The page's checkboxes choose which layers the
shared OpenGL preview draws, **Analyze cost (4 files)** reports each file's
x_theta/y_theta draw split and calibrated time, and **Save 4 G-code files**
writes `<base>-cyan.gcode`, `-magenta`, `-yellow` and `-black` from one save
dialog. Every file goes through the normal converter pipeline, so the r-theta
axis-cost solver, M3/M5 pen contract and dwell behavior are inherited
unchanged.

## Reason

The project owner asked for per-ink G-code from a color image, with the same
XY-theta cost-efficiency requirement as existing programs. The r/plotterart
survey (`docs/research/2026-10-07-cmyk-separation-prior-art.md`) found that the
community standard, DrawingBotV3, gates CMYK behind its closed premium tier,
while `ohnorobo/cmyk-splitter` (MIT) provides the RGB->CMYK + GCR math in
Pillow/NumPy - the same dependencies this converter already uses.

## Implementation

- `software/converter_core/cmyk.py`: pure separation/screening module.
  `rgb_to_cmyk_tone` extracts K as the gray component and rescales CMY (GCR),
  then applies GCR strength, per-ink weights, and gamma. Screen angles are the
  classic C 15 / M 75 / Y 0 / K 45 degrees; the default K weight is 0.8
  because r/PlotterArt threads consistently report black overpowering CMYK
  plots. `screen_channel` reuses the repository's own
  `halftone_contours`/`stipple_points` primitives, caps marks per ink by
  growing the pitch, and drops sub-floor coverage so paper stays clean.
  `svg_document` writes one colour-stroked `data-ink` group per channel.
- `software/generator_tabs/cmyk_tab.py`: the tool page (`ORDER 25`,
  Photo-based). Controls: saturation, contrast, ink gamma, black (GCR),
  resolution, per-ink weights, screen style, dot pitch, dot size, pen width,
  max marks per ink, seed, per-layer preview/write checkboxes, page size,
  margin, artwork scale. Preview checkboxes rebuild the shared preview SVG
  with only the checked inks. A QThread worker plans the checked inks through
  the host and fills a monospace cost table; saving reuses the analyzed
  programs unless a control changed.
- `software/qt_svg_to_gcode.pyw`: `settings_for_source` now honours
  `SELF_SCREENED = True` (fill spacing 0) so the Convert Fill patterns do not
  hatch every dot outline twice. New host APIs: `analyze_program` builds the
  exact program a Preview would headlessly (moves, G-code, stats), and
  `export_program_set` owns the single dialog and the per-layer file writes.
- `software/converter_core/gcode.py`: `move_strategy_length` and
  `estimate_program_time` moved out of the main window so the same
  x_theta/y_theta and time math serves both the estimate line and multi-layer
  tools; `strategy_mm` joins `strategy_counts` in the return.
- `software/converter_core/shading.py`: `halftone_contours` accepts a
  `steps` parameter (default 20, unchanged) so CMYK dots can use 8 segments.
- Attribution: `software/generator_tabs/cmyk_NOTICE.md` carries the
  cmyk-splitter MIT license and copyright (Sarah Laplante, 2025); the
  `generator_tabs/README.md` contract documents the new host APIs.

## Verification

- `python -m unittest discover -s software\tests` -> 334 tests pass,
  including the new `test_cmyk_tab.py` (separation/GCR, weights/gamma,
  screening, mark cap, SVG group order, cost table, layer preview, worker
  strategy split, four-file save) and the updated tool-shell tests
  (CMYK in the dashboard order/groups, self-screened fill off,
  `export_program_set` naming/contents).
- Headless end-to-end run through the real window: a 48 px image on a 60 mm
  page with a 4 mm pitch screened 41 K marks and planned 494 moves
  (x_theta 147 / y_theta 168, 632 G-code lines) in 0.02 s; the preview SVG
  built in 0.08 s; `export_program_set` wrote the two test files.
- `python tools\check_gcode_motion.py --strict` on a generated K-ink file:
  PASS - 328 drawing moves, largest bed rotation 14.75 deg (cap 15), A rate
  at the 250 motor deg/s limit, no pen-up move carrying un-fed rotation, and
  the strategy split x_theta 147 / y_theta 168.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Vendoring the whole DrawingBotV3 workflow was rejected: its CMYK separation
  is premium/closed, and the free build is a Java desktop app, not a library.
  Vendoring `svenhb/plotterfun-color` (MIT web app) is a valid artistic
  alternative but would only add another embedded web page, not per-ink
  G-code.
- The first screening attempt emitted closed dot circles into the normal Fill
  pipeline, which would have hatched every dot outline a second time. Fixed
  with the explicit `SELF_SCREENED` contract rather than per-tab settings
  hacks.
- A large page at a small pitch can generate tens of thousands of dot
  contours; the mark cap grows the pitch instead of dropping marks, and the
  default pitch is 3 mm with 5000 marks per ink.

## Risks and follow-up

- Not yet plotted on paper. Inter-ink registration (all four programs sharing
  one origin, consistent pen mounting) is mechanical and is the community's
  most reported failure mode; run a small registration test before a long
  plot.
- The OpenGL preview draws all visible inks in the single preview colour, so
  the layer checkboxes are the way to identify an ink; per-ink tinting would
  need a GL colour change.
- Analyze/Save snapshot the current Motion/Machine settings when the analysis
  starts; changing those fields marks the tab's own key stale only through
  `settings_for_source`, so re-run Analyze after retuning feeds.
- Dot marks are drawn as 8-segment circles, so plot time scales with mark
  count; raise the pitch or lower Max marks/ink for large pages.

## Files

- `software/converter_core/cmyk.py`: separation, screening, layer SVG.
- `software/generator_tabs/cmyk_tab.py`: CMYK tool page and analysis worker.
- `software/generator_tabs/cmyk_NOTICE.md`: MIT attribution.
- `software/converter_core/gcode.py`: shared move/time estimate helpers.
- `software/converter_core/shading.py`: halftone step count.
- `software/converter_core/__init__.py`: export the cmyk module.
- `software/qt_svg_to_gcode.pyw`: `SELF_SCREENED`, `analyze_program`,
  `export_program_set`, estimate delegation.
- `software/generator_tabs/README.md`, `software/generator_tabs/__init__.py`:
  host contract.
- `software/tests/test_cmyk_tab.py`, `software/tests/test_generator_tabs.py`:
  coverage.
- `software/README.md`: tool documentation and defaults table.
