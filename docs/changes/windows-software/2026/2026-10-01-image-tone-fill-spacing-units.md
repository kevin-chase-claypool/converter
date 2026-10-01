---
id: WSW-20261001-007
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/converter_core/settings.py
tags:
  - fill
  - tone
  - performance
  - units
related:
  - WSW-20261001-004
  - software/README.md
---

# Image-tone fill spacing is millimetres on paper

## Summary

The image-tone fill path now converts `Fill spacing mm` and the pattern size
fields into SVG user units before building the lattice
(`view_spacing = mm_spacing / settings.scale`). A 4 mm fill is 4 mm on paper
whatever the artwork's viewBox says, which is what the vector path already did.

On the artwork that prompted this - a 1000 x 700 user-unit gradient - `Fill
spacing 4` used to generate 411,060 points in 2.25 s at the fitted scale. It now
generates 55,974 points in 0.30 s, and the planner, preview and G-code listing
that follow all scale with that point count.

## Reason

"what settings do i need to use to provide a time-reasonable render", sent while
a preview sat at `Parsing SVG geometry | 49.8 s` with `Fill spacing 2`,
`Wave size 2`, `Fill pattern gradient waves (sine_gradient)`.

The tone path rasterises the SVG and generates its lattice in *view units*, then
`apply_geometry_settings` scales the result by `settings.scale`. It read
`Fill spacing mm` as if a user unit were a millimetre, so an exported design
whose viewBox is a thousand units wide was filled at roughly a fifth of the
requested pitch and then shrunk. The sine gradient's point count is
`12 x width x height / spacing^2` in view units, so the error was quadratic:
that artwork asked for 2 mm rows and built 1.64 million points.

## Implementation

- `qt_svg_to_gcode.pyw`, `raster_shade_contours`: one conversion at the top of
  the function, `active_spacing = self.pattern_spacing(...) / artwork_scale`,
  with `artwork_scale = settings.scale` (falling back to `1.0` when it is
  missing, non-finite or not positive). Every tone pattern inherits it -
  `dots`, `circles`, `diamonds`, `hexagonal`, `triangular`, `waves`,
  `sine_gradient`, `gyroid`, `concentric` and the line families - because they
  all derive their spacing from that one value, as do `sample_step` and
  `min_segment`.
- The cache key already includes `scale`, so a changed auto-fit still re-reads
  the geometry, and `describe_fill` keeps reporting the spacing in millimetres.
- No change to `Raster px/unit`: it remains pixels per SVG user unit. That is
  the same units mistake in a second setting, but it affects sampling accuracy
  and render cost rather than output density, so it is recorded as follow-up
  instead of being changed under an active plotting session.

## Verification

- 154 tests pass, including the new `software/tests/test_tone_fill_scale.py`:
  a 1000 x 700 user-unit gradient at `Scale 0.5` puts its rows 4.0 mm apart on
  paper (8 user units) for `Fill spacing 4`, halving the scale quarters the
  point count, and halving the requested spacing roughly quarters it again.
- Measured on the reported case (1000 x 700 user units, gradient rect, angle 0,
  `Fill source Auto`):

  | Fill spacing | Scale | Before | After |
  |---|---|---|---|
  | 4 mm | 1.00 | 411,060 points / 2.25 s | 411,060 points / 2.25 s |
  | 4 mm | 0.37 | 411,060 points / 2.25 s | 55,974 points / 0.30 s |
  | 2 mm | 0.37 | 1,644,240 points / 7.73 s | 225,860 points / 1.30 s |

  At scale 1.0 the conversion is the identity, which is why the first row is
  unchanged: an artwork already authored in millimetres behaves exactly as
  before.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Considered generating the tone lattice directly in paper millimetres. Rejected:
  the raster, `darkness_at` and every helper work in view coordinates, and the
  rest of the pipeline expects view-space contours that it scales itself.
- Considered leaving the other tone patterns alone and converting only in the
  sine gradient. Rejected: it would give two patterns different meanings for the
  same field.
- Considered skipping the fill on the pre-fit geometry pass in the preview
  worker (the auto fit discards it and re-reads). Not needed once the spacing is
  correct - that pass now costs the same as any other build - and it would have
  needed a second cache entry to avoid returning an unfilled preview when the
  fit turns out to be a no-op.

## Risks and follow-up

- Any tone fill on an artwork whose viewBox is not in millimetres gets *coarser*
  on paper than before. A user who had tuned a spacing against the old, denser
  behaviour needs to lower `Fill spacing mm` to match the previous look.
- The first build after a scale change still uses the scale shown in the Scale
  box, which for an auto fit is last build's value until the fit runs again; the
  fitted re-read that follows is correct. `Fit = Manual` avoids the second pass.
- `Raster px/unit` is still per user unit while its tooltip says per mm.
  Recorded in the roadmap.

## Files

- `software/qt_svg_to_gcode.pyw`: the mm-to-view-unit conversion.
- `software/tests/test_tone_fill_scale.py`: the regression tests above.
- `software/README.md`: fill documentation.
