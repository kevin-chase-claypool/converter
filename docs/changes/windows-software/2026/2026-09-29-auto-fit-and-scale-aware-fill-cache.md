---
id: WSW-20260929-002
date: 2026-09-29
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - usability
  - scale
  - reach
  - fill
  - cache
related:
  - WSW-20260929-001
  - WSW-20260928-002
---

# Auto-fit to the bed, and fill that follows the final scale

## Summary

Scale no longer has to be computed by hand. A new **Fit** setting next to
`Scale` chooses how the scale is set:

| Fit | Behaviour |
|---|---|
| `Fill bed (auto)` (default) | Sizes the artwork's bounds to the drawable circle on every build, so the drawing fills the bed |
| `Fit inside (auto)` | Sizes the artwork so every point stays inside the drawable circle |
| `Manual (use Scale)` | Uses the `Scale` field exactly as before |

While an auto fit is selected, `Scale` is read-only and shows the value the last
build used, so the number is visible but not something to type. The `Fill bed`
and `Fit inside` buttons beside the preview now also *select* that fit, so a
button press becomes the standing behaviour instead of a one-off.

Building this exposed a second defect, fixed here: **the parsed geometry was
cached without the scale**, so changing only `Scale` reused fill generated for
the previous scale. On `samples/svg/kindergarten-house-sun.svg`, a build at
`Scale 0.25` following a build at `Scale 1.0` produced 122 contours instead of
the correct 48 - a fill roughly four times denser on paper than
`Fill spacing mm` asked for. Every fit action changes only the scale, so this
was the normal path.

## Reason

The owner asked for "an auto-fit option ... to scale the image to exactly within
the bounds of the printable area". The two fit buttons already produced that
size, but only when pressed, and only until the next settings change: settings
are not persisted between launches, so a manual scale has to be re-derived every
session.

The cache defect then made the buttons produce the wrong fill. `parse_svg_geometry` is
called with `scale=` and uses it to coarsen fill spacing and tolerance so the
final on-paper density stays constant. `raw_geometry_key()` did not include the
scale, so the cached contours - generated at the old scale's coarsening - were
reused and simply multiplied by the new scale.

## Implementation

`software/converter_core/settings.py`:

- `fit_mode: str = "fill"`, validated against `fill`, `inside`, and `manual`,
  with `FIT_MODE_CHOICES` supplying the labels and a tooltip for both the mode
  and the now-conditional `Scale` field.

`software/converter_core/geometry.py`:

- `fit_scale_to_radius()` now sizes exactly instead of being shrink-only, so
  "fit inside" means the same thing in both auto and manual use: the artwork
  ends up at `reach x 0.98` whether it started larger or smaller.

`software/qt_svg_to_gcode.pyw`:

- `raw_geometry_key()` includes `scale` and `fit_mode`, so a scale change
  regenerates the fill at the right on-paper density.
- `fitted_settings()` returns settings whose scale satisfies the configured
  auto fit, or the same object when the fit is manual or already satisfied.
  `PreviewWorker.run()` re-reads the geometry once when it returns a changed
  object, because the fill is generated during that read. A second build starts
  from the scale the field now holds, so the extra read happens once per file.
- `install_preview()` writes the scale the build used back into the read-only
  `Scale` field with signals blocked, so the field cannot mark its own build
  stale.
- `update_fit_fields()` switches the `Scale` field between editable and
  read-only with the `Fit` mode, and `select_fit_mode()` lets the two buttons
  adopt their behaviour as the standing fit.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 72 tests
  pass, including the updated `fit_scale_to_radius()` cases that now pin exact
  sizing in both directions.
- Cache probe on `samples/svg/kindergarten-house-sun.svg`, `Fill spacing 4`:

| build | before fix | after fix |
|---|---|---|
| fresh at `Scale 1.0` | 127 contours | 127 contours |
| `Scale 0.25` reusing the cache | 122 contours (wrong density) | 48 contours |
| fresh at `Scale 0.25` | 48 contours | 48 contours |

- Offscreen `MainWindow` probe: `fill` fit sizes a 400 mm artwork to a 375.1 mm
  span with a 265.3 mm corner radius (corners clipped), `inside` fit sizes it to
  a 187.6 mm radius (nothing clipped), `manual` returns the same settings
  object, and a second fitting pass is a no-op so repeat builds parse once.
  The `Scale` field is read-only under an auto fit, editable under `Manual`, and
  showed `1.8757` after a build that used that scale.
- End-to-end `PreviewWorker` run on `samples/svg/kindergarten-house-sun.svg`
  with the default fit: log reports
  `Auto-fit (Fill bed): Scale 1 -> 1.9672`, the rebuild reads its geometry at
  the new scale (215 hatch passes for the same 4 mm spacing), and the program
  ends with 229 clipped contours and 7085 G-code lines.

## Struggles and rejected approaches

- Defaulting `Fit` to `Manual` was rejected. Settings are not persisted, so the
  owner would have to re-select the fit every launch; the whole point of the
  request is that the artwork lands on the bed without being asked.
- Re-fitting after planning was rejected: the fill is generated while reading
  the geometry, so a late change would have to throw away and rebuild the fill
  anyway.
- Keeping `fit_scale_to_radius()` shrink-only while the auto fit sized exactly
  was rejected as two meanings for one action.

## Risks and follow-up

- **Auto-fit resizes artwork that was authored at a physical size.** A 200 mm
  drawing opens at `Fill bed` size rather than 200 mm. `Fit = Manual` restores
  literal document sizes; the README says so.
- `Fill bed` still clips the four corners by design, and the reach guide stays
  red while it does.
- The extra geometry read happens once per file per scale change. On a very
  large trace that is one more parse than strictly necessary, which the roadmap's
  "resolve the fill once per build" work would remove.

## Files

- `software/converter_core/settings.py`: `fit_mode`, labels, tooltips, validation.
- `software/converter_core/geometry.py`: exact `fit_scale_to_radius`.
- `software/qt_svg_to_gcode.pyw`: auto-fit pass, scale-aware cache key, field
  read-only handling, sticky fit buttons.
- `software/tests/test_fit_to_bed.py`: updated fit semantics.
- `software/README.md`, `docs/HANDOFF.md`: current behaviour.
- `docs/changes/windows-software/2026/2026-09-29-fill-bed-and-recenter-fits.md`:
  records that its `Fit inside` sizing is superseded here.
