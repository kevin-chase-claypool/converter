---
id: WSW-20261015-001
date: 2026-10-15
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/generator_tabs/_tab_common.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
tags:
  - kinematics
  - theta
  - xy
  - cmyk
  - ui
related:
  - WSW-20261014-003
  - HW-20261011-001
---

# Bed motion bullets: Xθ/Yθ or XY only, in the sidebar and on the CMYK tab

## Summary

The converter now presents its kinematics as an explicit either/or: a
two-bullet **Bed motion** choice in the main sidebar ("Xθ/Yθ (rotating bed,
fast)" / "XY only (bed parked, precise)") and the same two bullets on the
CMYK tab, where they apply to all four ink programs and the calibration
sheet. XY only holds the bed at the Theta offset angle for the whole
program, so every move is drawn by the gantry and no bed-angle error can
reach the paper.

## Reason

After the 2026-10-11..15 bed-tilt investigation (quadrant pairs, gap maps,
rotation gap map), the operator decided that precision prints should avoid
bed rotation entirely while speed-first prints keep the x_theta/y_theta
solver: "for precision prints, I want to be able to print XY only, and for
prints where I need speed but less precision... the xtheta/ytheta". The
core already supported `theta_mode = "fixed"` (one constant A), but it was
buried as a raw combo id, and the CMYK tab had no control for it at all.

## Implementation

- `converter_core/settings.py`: `THETA_MODE_CHOICES` carries the two human
  bullets over the stable ids (`optimized` / `fixed`); the sidebar row is
  renamed **Bed motion**, and the tooltip spells out the trade. `tangent`
  stays a valid settings-file/API value but is no longer offered.
- `generator_tabs/_tab_common.py`: `ChoiceBullets`, the shared vertical
  radio widget (label + stable value per bullet) used by both places.
- `qt_svg_to_gcode.pyw`: the sidebar renders `theta_mode` as the two
  bullets; the dirty-marking and settings-collection loops read the widget.
- `generator_tabs/cmyk_tab.py`: a **Kinematics** group with the same two
  bullets; `apply_tab_settings` feeds `theta_mode` to the preview, the four
  per-ink programs and the calibration sheet, and the cost line plus the
  per-ink log report `XY only` instead of `x0/y0`.

## Verification

- New `software/tests/test_kinematics_choice.py`: XY-only programs emit a
  single A value (0, or `theta_offset x ratio`), every planned theta equals
  the offset, the first drawn point equals the planned bed point (no
  rotation), Xθ/Yθ still sweeps many angles, `ChoiceBullets` round-trips
  its values, and the sidebar offers exactly the two bullets and reports
  them through `MainWindow.settings()`.
- `software/tests/test_cmyk_tab.py`: the tab offers the two bullets,
  `apply_tab_settings`/`_effective_settings` carry the choice, a real layer
  program planned through the tab with XY only holds A at 0 with `fixed`
  strategies, and the cost summary says `XY only`.
- Full suite: 421 tests pass (1 skipped, unchanged).
- A generated XY-only program passes
  `python tools\check_gcode_motion.py <file> --strict`: 0 deg bed rotation
  in every move, 0 A rate, no pen-up rotation, strategies `fixed`.

## Cost at a glance (estimator, motion scale 1.0)

Same settings (`fit_mode = inside`), outline artwork, numbers from
`estimate_program_time` plus the emitted file:

| sample | mode | lines | XY path | bed turns | estimate |
|---|---|---:|---:|---:|---:|
| kindergarten-house-sun.svg | Xθ/Yθ | 294 | 2515 mm | 0.93 | 241 s |
| kindergarten-house-sun.svg | XY only | 236 | 3180 mm | 0.00 | 249 s |
| spirit-logo-purple-rgb.svg | Xθ/Yθ | 13247 | 5254 mm | 2.33 | 488 s |
| spirit-logo-purple-rgb.svg | XY only | 13247 | 6682 mm | 0.00 | 512 s |

XY only costs roughly 25-30 % more gantry path and a few percent of estimated
time on these samples - the feed model binds both modes at the same draw
feed, and bed rotation is itself tangential-speed-limited. What the switch
actually removes is the entire bed-rotation error budget (tilt, runout,
reversal drag), not just some of it.

## Struggles and rejected approaches

- Rejected omitting the A words from XY-only output: one program shape for
  the controller and the preview is simpler, and a constant-A word is a
  no-op. "XY only" is about motion, not file syntax; the README now says so
  because the older text ("no XY-only export mode") read the other way.
- Rejected a third bullet for `tangent`: the operator asked for
  one-or-the-other; the value stays accepted for settings files and tests.
- Rejected making the CMYK bullets follow the sidebar dynamically: the tab
  already owns local overrides (Pen width, Path tolerance), and a hidden
  follow-until-touched interaction is harder to reason about.

## Risks and follow-up

- The clip stays the reach circle (gantry reach radius) in both modes. That
  is correct for XY only - the +Y soft-limit edge is the binding direction -
  but conservative; using the full XY envelope rectangle could be a later
  roadmap item, not needed for this feature.
- First XY-only production print should be watched like any new mode: bed
  parked (A constant), pen-up moves carry no rotation, GP27 trailer
  unchanged.

## Files

- `software/converter_core/settings.py`: choice bullets, tooltip, row label.
- `software/generator_tabs/_tab_common.py`: `ChoiceBullets` widget.
- `software/qt_svg_to_gcode.pyw`: sidebar bullets and settings plumbing.
- `software/generator_tabs/cmyk_tab.py`: Kinematics bullets, summary, plan.
- `software/tests/test_kinematics_choice.py`, `software/tests/test_cmyk_tab.py`: tests.
- `software/README.md`, `docs/HANDOFF.md`: current-state descriptions.
