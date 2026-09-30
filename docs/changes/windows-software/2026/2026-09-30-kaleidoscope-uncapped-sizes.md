---
id: WSW-20260930-013
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
  - WSW-20260930-012
  - software/README.md
---

# Kaleidoscope: no cap on source size or typed bounds

## Summary

`Source size` was capped at 400 mm and the typed bounds at 300-1000 mm. Those
were arbitrary guards, not limits of the machine, so they are gone: source size
now accepts 0.1-1,000,000 mm, the image offsets +/-100,000 mm, bed diameter
10-100,000 mm, reach radius and fit radius up to 100,000 mm. Auto-fit no longer
clamps its result to 400 mm either.

## Reason

The operator asked "why is 400 mm the max for source size. let me go as high as
i want". The cap came from the main converter's assumption that artwork larger
than the 457 mm bed is pointless; in the kaleidoscope the source is scaled to
the `Fit radius` before it is clipped and planned, so the source size is a
drawing scale, not a machine limit.

## Implementation

- `qt_kaleidoscope.pyw`:
  - `Source size` range 10-400 becomes 0.1-1,000,000 and the two auto-fit paths
    in `rebuild` and `fit_to_bounds` clamp to the spin box minimum instead of a
    hard 400.
  - `Image offset X/Y` range +/-500 becomes +/-100,000 so a large source can
    still be positioned.
  - `Bed diameter` 100-1000 becomes 10-100,000, `Bed margin` 0-100 becomes
    0-10,000, and `Gantry reach radius` / `Fit radius` 10-300 / 5-300 become
    1-100,000 / 0.5-100,000.
  - The `Source size` tooltip now says what the number means and that the fit
    radius is what keeps the plot on the bed.
- Nothing in the core changed: `normalize_source`, `random_pattern` and the
  planner already take any size, and the planner still clips the saved program
  at the real printable limit with its existing log warning.

## Verification

- New `SourceSizeTests` in `software/tests/test_preview_view.py`: the spin box
  maximum is at least 100,000 mm, and a random pattern built with
  `Source size` 250,000 mm and auto-fit lands at the fit radius to within 1 %
  (measured 181.3 mm).
- All eleven test modules pass.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Leaving the caps but adding a warning was rejected: the operator asked for the
  cap to go, and the fit radius plus the planner's own clipping already make a
  large source safe.
- Removing the spin-box limits entirely was rejected because `QDoubleSpinBox`
  needs a finite maximum; 1,000,000 mm is a metre-class number that no plot will
  reach while keeping the widget's stepping and formatting sane.

## Risks and follow-up

- A very large source with auto-fit off still gets clipped by the fit radius, so
  the preview can look empty if the design is scaled far beyond the frame; the
  log reports the outer radius against the bound, as before.
- The preview's bed circle is drawn from the typed bed diameter, so a nonsense
  bed entry makes the design look tiny; that is the operator's own number.

## Files

- `software/qt_kaleidoscope.pyw`: spin-box ranges, auto-fit clamps, tooltip.
- `software/tests/test_preview_view.py`: source-size tests.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
