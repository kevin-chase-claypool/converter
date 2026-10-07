---
id: WSW-20261007-002
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - color-separation
  - screening
  - line-screen
  - tsp
  - contours
  - gcode
related:
  - WSW-20261007-001
  - docs/research/2026-10-07-cmyk-separation-prior-art.md
---

# Add six CMYK mark styles and an overdraw control

## Summary

The CMYK tool's Screen style dropdown now offers eight marks instead of two:
**halftone dots**, **stipple dots**, **line screen** (line pitch follows tone),
**crosshatch levels** (2-4 line families stacked by tone threshold),
**wave screen** (sine rows whose amplitude follows tone), **interference
(gyroid)** (a tone-scaled gyroid field contoured into loops that flatten into
blank paper), **single line (TSP)** (one greedy route through tone stipple
points) and **topographic contours** (contour lines of the tone itself). A new
**Overdraw** control redraws every mark 1-3 times with a sub-pen offset so
ballpoint ink reads darker; **Hatch levels** sets the crosshatch depth.

## Reason

After the first CMYK release the project owner asked what marks could replace
dots and stipple. The dot styles draw each mark as a small closed contour, so
a page can carry tens of thousands of pen-lift cycles; line, wave, TSP and
contour styles are continuous marks that plot far faster and give distinct
print, engraving, map and scribble looks. The XY-theta axis-cost solver is
unchanged - these are drawing primitives, not motion changes.

## Implementation

- `software/converter_core/cmyk.py`
  - `_line_runs`: rotated line family sampled along each line; runs break
    where tone falls below the ink floor and short runs are dropped. With
    `adaptive=True` (the **line screen** style) the next line's pitch grows in
    light areas (up to 3x) and stays at the requested spacing in dark ones, so
    one family covers a continuous tonal range. Crosshatch reuses the same
    helper with fixed pitch, 1-4 passes at +45 degrees, and thresholds
    `i / levels`.
  - `_wave_rows`: sine rows at the requested pitch whose local amplitude is
    `pitch/2 * dot_size% * tone` (the `sine_gradient` convention: wavelength =
    2 x pitch); rows vanish where the tone is blank.
  - `_field_contours`: **topographic contours** call the existing
    `tone_terrain_contours` with the channel's tone sampler; **gyroid** passes
    a tone-scaled interference field (`0.5 + 0.25 * tone * (sin kx cos ky +
    sin ky cos kx)`) so a flat white channel has no relief and draws nothing.
  - **TSP** reuses `stipple_points` + `greedy_single_line` and emits one
    continuous path.
  - `_apply_overdraw`: deterministic sub-pen offsets (<= 0.25 mm) replicating
    each mark up to three times.
- `software/generator_tabs/cmyk_tab.py`: the style combo lists all eight
  marks; Hatch levels (2-5) and Overdraw (1-3) controls are wired into the
  layer cache key and the `screen_channel` call; the screen group tooltips
  explain which styles use pitch/size/levels.

## Verification

- `test_cmyk_tab.py` grows to 19 tests: line runs break in white and stay
  open, crosshatch adds a family per level, overdraw doubles the marks, wave /
  gyroid / TSP produce marks (TSP exactly one path), contours trace a tone
  ramp and draw nothing on a flat tile, and every style builds all four layer
  groups through the real tab.
- Style smoke on an 80 mm page: lines 11 marks / 891 points, crosshatch 48 /
  3216, waves 20 / 2020, gyroid 289 / 1826, TSP 1 / 258, contours 19 runs on a
  ramp; every style draws 0 marks on blank white.
- A line-screen K-ink program through the real window passes
  `tools\check_gcode_motion.py --strict` (317 drawing moves, x_theta 80 /
  y_theta 236, largest bed step 14.43 deg under the 15 deg cap).
- Full suite and `tools\docs_index.py --write` / `--check` re-run before
  commit.

## Struggles and rejected approaches

- `tsp_region_contours` cannot be reused directly: its `darkness` parameter is
  a scalar for vector-art fills (the image-tone path builds callbacks
  elsewhere), so TSP reuses the same two primitives it wraps -
  `stipple_points` + `greedy_single_line`.
- Topographic contours draw nothing on a flat dark tile. That is correct
  behavior (a flat elevation has no level sets), and the tests use a tone ramp
  so the style is checked against real shading rather than a solid fill.
- A first idea to rasterize tone masks and clip the Fill line patterns to them
  was rejected: it would have duplicated the fill clipping machinery for a
  callable tone field.

## Risks and follow-up

- None of the new marks have been plotted on paper; choose one per ink
  experimentally. Line/wave/TSP/contour styles are the fast alternatives to
  dots on large pages.
- Gyroid and contour styles sample a grid (capped at 60000 cells per channel),
  so they cost more compute than a dot screen but far fewer pen cycles.
- The greedy TSP route can self-cross, the same behavior as the existing
  Stipple / TSP tool.

## Files

- `software/converter_core/cmyk.py`: style helpers and dispatch.
- `software/generator_tabs/cmyk_tab.py`: style list, Hatch levels, Overdraw.
- `software/tests/test_cmyk_tab.py`: style coverage.
- `software/README.md`: tool documentation and defaults row.
