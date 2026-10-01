---
id: WSW-20261001-006
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_kaleidoscope.pyw
  - software/converter_core/generative.py
tags:
  - kaleidoscope
  - generative
  - interface
related:
  - WSW-20261001-003
  - software/README.md
---

# Ornament spacing: the wallpaper density is a control, not a constant

## Summary

The kaleidoscope app has an `Ornament spacing` control (1.0-8.0, default 2.0,
saved with the rest of the setup) directly under `Region overlay`. It sets how
far apart the wallpaper-like ornaments sit - the bead rows, stud flowers and
dotted rings that fill the bands between the shape rings and run around the
rim - as a multiple of the engraved hatching's pitch. 1.0 is the old, packed
look; 2.0 is the sparse default; 4.0 and up leaves a few ornaments per band.
It rebuilds the preview as you change it, and the shaded leaves, lenses,
separators and rim arcs keep their own spacing.

## Reason

Operator, after the sparse default shipped as a module constant: "i dont know
where or how im supposed to modify the wallpaper-like items". A constant in
`generative.py` is not reachable from the app the operator actually runs
(`kaleidoscope.bat`), so the density has to be a control.

## Implementation

- `converter_core/generative.py`:
  - `random_pattern(ornament_pitch=...)` takes the multiplier, clamped to
    `MIN_ORNAMENT_PITCH` (1.0) and `MAX_ORNAMENT_PITCH` (8.0). `None` keeps the
    module default `ORNAMENT_PITCH` (2.0), so existing callers and the previous
    change's output are unchanged.
  - The pitch is threaded to the ornament layers only: `_studs()`, `_dots()`,
    `_rim()` and `_rosette()` take it as an optional keyword (defaulting to
    `ORNAMENT_PITCH`), and the family dispatch passes it to `_beadrow()`, the
    one shape family built out of beads. The other ten families are untouched.
- `software/qt_kaleidoscope.pyw`: `Ornament spacing` spin box in the Source
  group, wired to `on_design_changed`, passed to `random_pattern` and stored in
  `kaleidoscope_settings.json` next to `region_overlay`.
- `software/README.md`: the random-pattern section describes the control and
  the parameter it maps to.

## Verification

- `OrnamentPitchTests` in `test_generative.py`: an omitted pitch equals
  `ORNAMENT_PITCH`; 1.0/2.0/4.0 draw strictly fewer contours in that order for
  the operator's seed; -3.0 clamps to the minimum and 99.0 to the maximum; and
  the drawing stays inside the design radius at both extremes.
- `SettingsPersistenceTests.test_settings_round_trip_keeps_folder_and_numbers`
  now also round-trips `ornament_pitch` (3.5); the sidebar test
  `test_the_ornament_spacing_control_reaches_the_generator` builds the real
  window and asserts that 1.0 draws more contours than 4.0.
- Contour counts for the operator's seed (83382, intricacy 10, 4 divisions):
  12,064 mirrored contours at 1.0, 7,248 at 2.0 and 5,032 at 4.0, against a
  path length of 150,633 / 133,929 / 126,310 mm - the count moves far more than
  the length, because only the ornaments change.
- Render check: `samples\preview\gen_ornament_pitch_1.png`,
  `_2.png` and `_4.png` are the same seed at the three settings.
- All fourteen `software/tests` modules pass; `docs_index --write/--check`
  pass.

## Struggles and rejected approaches

- Reusing `_density()` for the control was rejected: it is the packing
  multiplier for the whole composition, so the control would also thin the
  hatching inside every shape and change designs the operator did not ask
  about.
- Giving every family a `pitch` argument so the dispatch table stays uniform
  was rejected as noise - ten of the eleven families never use it - so the
  dispatch passes it to `_beadrow()` only.

## Risks and follow-up

- `Ornament spacing` is a taste control, and the operator now owns the value;
  the shipped 2.0 is a default, not a recommendation.
- The control is only meaningful in random-pattern mode. It stays enabled when
  an imported image is loaded, where the generator is not used; the same is
  already true of `Intricacy` and `Region overlay`.

## Files

- `software/converter_core/generative.py`: `ornament_pitch`, the pitch
  parameters, `MIN_ORNAMENT_PITCH`/`MAX_ORNAMENT_PITCH`.
- `software/qt_kaleidoscope.pyw`: the spin box, its persistence and its use in
  the build.
- `software/tests/test_generative.py`, `software/tests/test_preview_view.py`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`.
