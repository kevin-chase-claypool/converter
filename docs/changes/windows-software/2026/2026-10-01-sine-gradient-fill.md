---
id: WSW-20261001-004
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - samples/svg/gradient-sine-demo.svg
tags:
  - fill
  - gradient
  - tone
  - plotter-art
related:
  - WSW-20261001-003
  - software/README.md
---

# Sine gradient: gradient tone plotted as continuous adjacent sinusoids

## Summary

New `Fill pattern` value `sine_gradient`. It fills a gradient with rows of sine
curves whose amplitude is the rendered darkness at that row, so a gradient reads
as curvature instead of as line density: dark areas swell the waves until
neighbouring rows just touch, light areas flatten them out. Rows are emitted in
antiphase and, with the new `Connect sine rows` option on (default), joined end
to end into a single pen-down serpentine. Two new controls ship with it:
`Gradient wave amplitude %` (default 50 of the row spacing) and
`Connect sine rows (one continuous stroke)`.

## Reason

Request: "in converter, for svg files with gradients, i need an option that
deals with gradients by using continuous adjacent sinusoids much like in
reddit/r/plotterart". Gradient artwork already routed to the rendered-image fill
source, but every tone pattern there encodes tone as hatch *density*, which is
the slicer look rather than the plotter-art look.

## Implementation

- `converter_core/geometry.py`
  - New `sine_gradient_region_contours(bounds, darkness, spacing, angle_deg,
    amplitude_pct, ink_floor, connect_rows, cancel_check)`. It is pure geometry:
    it takes a `darkness(x, y) -> 0..1` callable, so the Qt renderer supplies
    the tone and the behaviour is testable without Qt. Rows run along the
    rotated x axis; the amplitude at each sample is the tone at that sample's
    *row baseline*, which keeps the envelope from feeding back on itself along
    a vertical gradient. Rows alternate phase by pi, so at full darkness the
    crest of one row meets the trough of its neighbour instead of crossing it.
  - `SINE_GRADIENT_INK_FLOOR = 0.04`: below this tone a row carries no ink, so
    white space stays white and a gradient fades out instead of leaving a flat
    line drawn across its white end. `connect_rows` joins the end of one row to
    the start of the next only when the join does not cross blank paper, which
    is what keeps a holed gradient from being stitched across the hole.
  - `normalized_hatch_pattern` accepts `sine_gradient` and the aliases
    `gradient`, `gradient_wave(s)`, `sine_wave_gradient`, `continuous_sine`.
  - Vector fallback: with `Fill source = SVG shapes` there is no rendered tone,
    so `fill_region_pattern_contours` routes `sine_gradient` to the existing
    uniform `wave_region_contours` family rather than to a straight hatch.
  - `waves` and `sine_gradient` rows in the vector path are now passed through
    `chain_segments_to_paths`. `wave_region_contours` clips one segment at a
    time, so a row used to arrive as ~120 per row two-point contours; the
    chained form is 19 contours for a 40 mm square (one per row) with the same
    point set, i.e. the same drawing for a fraction of the pen cycles.
- `converter_core/settings.py`: `gradient_wave_amplitude_pct` (>= 0, <= 100),
  `sine_rows_connected`, the `sine_gradient` pattern value, its reuse of
  `wave_size_mm` as the row spacing, and tooltips.
- `qt_svg_to_gcode.pyw`: the pattern dispatches to the new generator with the
  renderer's `darkness_at`, both new settings are in the preview/geometry cache
  key, `Gradient wave amplitude %` is shown only for this pattern,
  `describe_fill` reports what the pattern will do, and selecting gradient
  artwork logs a one-line pointer to the new pattern.
- Follow-up in the same session, after the option was hard to find in the
  sidebar: the pattern combo now shows readable labels over the stored values
  (`gradient waves (sine_gradient)`, `waves (uniform sine rows)`,
  `cubic (isometric)`, `concentric (inset loops)`, `linear (parallel lines)`).
  `settings.HATCH_PATTERN_LABELS`/`VALUE_CHOICE_LABELS` hold them,
  `normalized_hatch_pattern` accepts either the label or the value, the panel
  reads the combo's stored value rather than its text, and the resolver's
  supported-pattern set is now taken from `HATCH_PATTERNS` so the offered list
  and the accepted list cannot drift apart.
- Second follow-up, after the option still could not be found in a running
  window: `sine_gradient` now sits third in `HATCH_PATTERNS`, so the combo shows
  `gradient waves (sine_gradient)` without scrolling, a test keeps it in the top
  three, and the log pane and `qt_debug.log` print the converter core version at
  startup (`2.3-sine-gradient`) so an open window from before a change is easy
  to recognise.
- Third follow-up, after the shape path was reported as "just equally sized sine
  waves that ignore the gradient": the vector (SVG shapes) path now scales the
  crest by the element's own fill or stroke darkness too, and refuses to let
  `Shade levels` tighten the pitch at the same time, so tone is counted once.
  On top of that, tone now drives the wiggle *rate* as well, matching
  SquiggleDraw's `phase += z/xsmooth` rule: the phase accumulates per sample
  with an increment proportional to the local darkness. `Gradient wave density
  %` (default 100 = the darkest areas wiggle twice as fast as the lightest,
  0 = the previous constant-wavelength behaviour, 400 = five times) is the gain.
  Both are threaded through `parse_svg_geometry`/`element_contours`/
  `fill_region_pattern_contours` so the shapes path and the image-tone path use
  the same settings.
- `samples/svg/gradient-sine-demo.svg`: a linear fade, a radial orb and a
  vertical band for trying the pattern.

## Verification

- `python -m unittest discover -s software/tests -t software/tests`: 143 tests
  pass (133 before this change) including the new `test_sine_gradient.py`:
  dark-end swing is > 5x the light-end swing, amplitude respects the configured
  percentage, rows sit exactly one spacing apart, a solid region becomes one
  stroke, white paper receives no ink, a blank band breaks the serpentine, and
  the vector fallback is a chained uniform wave inside the polygon.
- Offscreen Qt run of the real path (`QSvgRenderer` -> `raster_shade_contours`
  with `Fill source = Auto`) on `samples/svg/gradient-sine-demo.svg` at
  `Fill spacing 3`: 65 wave passes, 18,016 points, one continuous stroke per
  gradient region, all ink inside the three gradient shapes and none in the
  white area between them. Render check `samples/preview/_sine_gradient_demo.png`
  (scratch, not committed) shows the linear fade and the radial orb swelling at
  their dark ends and flattening at their light ends.
- Offscreen Qt run with every combo entry selected in turn: each label stores
  and re-reads its canonical value, and `gradient waves (sine_gradient)` selects
  `sine_gradient` and reveals `Gradient wave amplitude %`.
- `svg_fill_sources` on the sample reports `gradient: 3`, and
  `resolve_fill_source` returns `tone` under `Auto`, which is what sends the
  artwork to the new generator. The headless core has no `QSvgRenderer`, so
  `converter_core.convert_file` stays on the SVG-shapes fallback and converts
  the sample to 102 contours / 11,993 G-code lines without error.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- First implementation read the tone at the *wave* point rather than at the row
  baseline. On a vertical gradient that makes the amplitude depend on the
  amplitude (the wave climbs into lighter or darker tone and pulls itself
  around); sampling the baseline removes the feedback and makes the envelope a
  clean read of the gradient.
- Considered scaling the vector-path amplitude by the element's fill darkness
  too. Rejected: `density_spacing` already encodes darkness as spacing there, so
  the pattern would double-count tone. Vector mode stays a uniform sine hatch.
- Considered a separate `Fill source` mode for gradients. Rejected: `Auto`
  already routes gradient paint to the tone source, so a pattern value is enough
  and it does not touch the source resolution contract.
- Considered forcing the serpentine. It is the plotter-art look, but a user
  wanting separate wave rows has no other way to get them, so it is a checkbox.
- The end-of-row join is bounded by `2 x spacing` rather than by one spacing:
  where the two rows meet in antiphase, one endpoint can be a full-amplitude
  crest and the other the matching trough. Joining at the row baseline would
  look tidier but does not shorten the stroke, because the travel is entirely
  vertical either way.

## Risks and follow-up

- Render-checked only; no gradient has been plotted on paper yet. The amplitude
  curve (linear in tone), the default 50 %, and whether the row-end joins read
  as deliberate seams or as defects all need a plot before they are called good.
- A light gradient fades to flat hairlines, not to nothing, because the ink
  floor is a tone threshold and every sample above it gets a mark. If that reads
  as banding on paper, the floor and the amplitude curve are the two knobs.
- Wavelength is fixed at twice the row spacing; there is no separate length
  control. `Wave size mm` moves the row spacing and the wavelength together.
- `gyroid` still returns one contour per clipped segment in the vector path, the
  defect fixed here for `waves`. Recorded in the roadmap with the sine-gradient
  follow-ups.

## Files

- `software/converter_core/geometry.py`: the sine-gradient generator, the
  pattern name, the vector fallback, and wave-row chaining.
- `software/converter_core/settings.py`: the two new settings and the pattern
  registration.
- `software/qt_svg_to_gcode.pyw`: tone-path dispatch, cache key, field
  visibility, log text.
- `software/tests/test_sine_gradient.py`: the new test module.
- `samples/svg/gradient-sine-demo.svg`: gradient sample for manual checks.
- `software/README.md`: fill documentation.
