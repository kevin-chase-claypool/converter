---
id: WSW-20261004-004
date: 2026-10-04
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/shading.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_shading.py
tags:
  - fill
  - shading
  - terrain
  - topographic
  - image-tone
  - plotter-art
related:
  - WSW-20261004-003
  - software/README.md
---

# Terrain: stop stacking contours on hard outlines

## Summary

The image-tone terrain used to draw every level of a hard tone edge, so an
outline, silhouette or thin stroke collected a band of near-coincident
contours - the operator's "seems like its doing too much on outlines". The
generator now (a) spreads its level ladder across the ink's own tone range with
at least six bands, so no stroke is lost between rungs, and (b) skips any line
that would come closer than half the requested `Fill spacing` to a line already
placed, longest line first. A hard edge is traced once or twice; a soft
gradient is left alone.

## Reason

Operator feedback with a CAD-style drawing preview: "seems like its doing too
much on outlines" - the blue draw path was a chain of thick bands along every
outline. The tone-as-elevation model makes every edge a cliff, and a cliff is
where all the levels meet.

## Implementation

- `software/converter_core/shading.py`, `tone_terrain_contours`:
  - The level count is `round(span / interval)` where `span` is the inked
    area's own tone range and `interval` is the coarea-calibrated gap, with
    `TERRAIN_TONE_MIN_LEVELS = 6` as a floor. A line drawing's ink is a thin
    slice of the tone range whose mean slope can exceed the whole slice: without
    the floor (and the span-relative ladder) a scanned line could fall between
    two rungs and vanish.
  - `_thin_contour_segments` walks the extracted level buckets longest-first
    and drops any segment whose endpoints come closer than
    `TERRAIN_LINE_SEPARATION x Fill spacing` (0.5) to a line already placed.
    Segments from one contour are judged together so a line is never compared
    with itself (which chopped contours into dashes in the first cut), and the
    longest-first order stops a tiny noise speck from knocking out a
    structure-defining line.
  - `_marching_squares` gained a `by_level` bucket mode so the thinning needs
    no second grid pass.
- `software/qt_svg_to_gcode.pyw`: the fill log no longer claims the drawn
  average equals `Fill spacing`; it says lines closer than half the spacing are
  skipped so hard outlines are traced once.

## Verification

- `software/tests/test_shading.py`:
  `test_a_hard_edge_is_thinned_to_a_few_lines` (a dark disc keeps <= 3 lines
  where the unthinned extraction draws 6) and
  `test_thin_strokes_are_drawn_once_each` (four 2 px strokes on white each keep
  1-2 lines and are never lost).
- Full suite: 205 tests pass.
- On `momandbennett.jpg` at `Fill spacing 4`: 825 contours / 22,475 points
  (whole-image average gap 5.7 mm against 4.2 mm unthinned), loading in 0.38 s;
  the 4 mm program (22,834 lines) still passes
  `tools\check_gcode_motion.py --strict` (largest bed step 13.50 deg against
  the 15.0 cap, A rate at its 250 limit, no bare `G0` rotation).
- A synthetic CAD-style drawing (900 x 700 px, rectangle outlines plus
  hairline hatching) is now traced with one contour per stroke instead of a
  band per stroke; the earlier version drew 5-14 fragments with the strokes
  missing entirely.

## Struggles and rejected approaches

- Comparing every segment with every already-kept point chopped a continuous
  contour into 8 mm dashes; the thinning now judges one level's segments as a
  unit against the other levels.
- Ordering the levels darkest-first let the tiny specks at the top of a noisy
  photo's range suppress the real lines; longest-first fixed it.
- A self-calibrating separation (half the drawing's own achieved gap) was
  tried and rejected: the achieved gap is measured from the undecimated length,
  so a line drawing's stacked duplicates made the estimate too small and the
  strokes stacked again. A fixed half-spacing is predictable and passes both
  the cliff and the thin-stroke cases.
- The ladder originally ran over the full 0..1 tone range; on the drawing that
  produced a single rung in the middle of the ink and lost the strokes. Spanning
  the ink's own range with a six-level floor is what made every stroke appear.

## Risks and follow-up

- Thinning removes ink, so a photo's coverage drops (4.2 mm to 5.7 mm average
  gap at a 4 mm setting) and an outline-heavy drawing drops more. Lower
  `Fill spacing` to compensate; the thinning is what keeps outlines from
  turning into bands.
- Each thin stroke is traced as a narrow closed loop (two almost-parallel pen
  passes about a millimetre apart), not as a single centreline. Skeletonizing
  thin contours to centre lines would be a further refinement.
- Still not plotted on paper: the ink behaviour at cliffs is the thing to watch
  on the first test sheet.

## Files

- `software/converter_core/shading.py`: span-relative ladder, level floor,
  separation pass, by-level marching squares.
- `software/qt_svg_to_gcode.pyw`: honest fill log line.
- `software/tests/test_shading.py`: cliff and thin-stroke regressions.
- `software/README.md`, `docs/HANDOFF.md`: current-state documentation.
