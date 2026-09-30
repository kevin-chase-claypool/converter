---
id: WSW-20260930-015
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - interface
  - bounds
related:
  - WSW-20260930-013
  - software/README.md
---

# Kaleidoscope: auto-fit no longer overwrites typed numbers

## Summary

Changing the seed, the intricacy or the divisions used to rewrite `Source size`
on every rebuild, because auto-fit wrote the fitted size straight back into the
spin box. Auto-fit now scales the drawing internally: the typed `Source size`
stays exactly as entered, the fit factor is reported in the log and in the
bounds note, and only the explicit `Fit design to bounds` button writes a fitted
number into the field.

## Reason

The operator reported that "every time i make a change, for example new seed or
intricacy or divisions the numbers all go back to defaults ... i want to be able
to change those but keep the number changes that i made". Reviewing the code,
`rebuild(refit=True)` called `self.source_size.setValue(size)`: with auto-fit on
by default, every design change silently replaced a hand-typed source size (740
mm, say) with the fitted value (~181 mm).

## Implementation

- `qt_kaleidoscope.pyw`:
  - `rebuild` keeps a `fit_scale` for the current build and multiplies the
    source size by it when building, instead of writing to the spin box. It is
    reset to 1.0 at the start of every rebuild, including `refit=False` builds.
  - The `Auto-fit after a division or rotation change` tooltip explains that it
    scales the design without touching the numbers, and that
    `Fit design to bounds` is the button that changes `Source size`.
  - The build log and the bounds note report the active scale, for example
    `Auto-fit is scaling the drawing by 0.234; Source size stays at 777.0 mm`.
  - `on_bounds_changed` now refits when auto-fit is on, so following the fit
    radius scales the design instead of cropping it - still without touching
    the typed numbers.
- `Fit design to bounds` keeps its old meaning: it measures the natural radius
  and writes the fitted size into `Source size`, then rebuilds with
  `fit_scale = 1.0`.

## Verification

- New `TypedNumberTests` in `software/tests/test_preview_view.py`:
  - rolling the seed keeps Source size, feed rate, theta speed, tolerance, fill
    spacing, threshold, trace detail, bed diameter, bed margin, reach radius and
    fit radius;
  - changing intricacy and divisions keeps the same set;
  - auto-fit on a 777 mm source does not write the size back, and the design
    still lands on the 120 mm fit radius;
  - `Fit design to bounds` is the one path that rewrites `Source size`, and it
    leaves the scale at 1.0.
- All eleven test modules pass; `python tools\docs_index.py --write` /
  `--check` pass.

## Struggles and rejected approaches

- Making auto-fit "only run when the user has not typed a size" was rejected:
  tracking touched-versus-untouched values is invisible behaviour, and the
  operator asked for their numbers to survive *always*.
- Baking the fit into the size and then restoring the old number afterwards was
  rejected as well: it produces a flash of the wrong value and breaks any
  signal connected to the spin box.

## Risks and follow-up

- A design is now described by two numbers (Source size and the current fit
  scale), so two sessions with the same seed can look different if one of them
  had a different fit radius. The scale is printed in the log and the bounds
  note to keep that visible.
- `Fit radius` still clips whatever the scaled design reaches; auto-fit matches
  the *natural* radius to it, which is the behaviour the button always had.

## Files

- `software/qt_kaleidoscope.pyw`: `fit_scale`, non-destructive rebuild,
  tooltip, log line, bounds note, bounds-change refit.
- `software/tests/test_preview_view.py`: `TypedNumberTests`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
