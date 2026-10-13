---
id: WSW-20261013-010
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/kinematics.py
  - software/converter_core/settings.py
  - software/tests/test_reversal_parking.py
  - samples/gcode/heraldic-revpark.gcode
tags:
  - a-axis
  - reversal
  - scallop
  - outline
  - parking
related:
  - WSW-20261013-009
  - WSW-20261013-008
---

# Park the bed across reversal-dense stretches

## Summary

New `Theta kinematics` setting **Bed reversal park mm** (default `2.5`).
Stretches whose planned bed direction reverses within that distance of pen
travel are now drawn with the bed parked (gantry X/Y) instead of whipping the
12:1 bed back and forth. Smooth curves keep the bed turning; the artwork is
unchanged because both strategies trace the same bed-frame points.

## Reason

The two-pen A/B overlay (`WSW-20261013-009`) proved the bed-motion copy of the
back-of-head scallop carries a ~0.5 deg net bed-angle error plus ~0.5 mm local
distortion, while the parked copy matches the commanded geometry to a median
of 0.07 mm. That stretch reverses the bed 16 times in 40 mm. This rule removes
exactly those reversals from the machine's budget instead of asking the bed
to survive them.

## Implementation

- `settings.py`: `theta_reversal_park_mm` (0 disables), validation 0-100 mm,
  `FIELD_DOCS` entry, and a row in the Theta kinematics settings group so the
  operator can tune it without a code change.
- `kinematics.py`: `_reversal_park_mask()` finds reversal events (sweep sign
  flips against the previous significant sweep) and marks every segment
  between events closer than the setting, merging each back-and-forth patch
  rather than toggling per spike. `_plan_contour_thetas_rtheta()` now runs the
  existing per-segment planner, computes the mask, and when it is non-empty
  re-plans with the masked segments forced onto the existing
  `_held_segment_plan` (the bed stays where it is; the gantry traces the same
  bed points in X and Y). Smooth contours produce no mask and plan exactly as
  before.

## Verification

- 410 tests pass, including 7 new in `software/tests/test_reversal_parking.py`:
  the mask marks close reversal pairs and ignores wide/smooth ones; a smooth
  circle keeps zero parked segments with all `x_theta`/`y_theta` labels; the
  real 322-point head-area run parks (>=5 holds, longest contiguous run >=4,
  held segments keep a constant theta) while the rule-off baseline never
  parks; out-of-range values are rejected by the settings validator.
- Regenerated `samples/gcode/heraldic-revpark.gcode` with the operator's
  plotting settings (manual 0.5 scale, feed 350, tolerance 0.05): the geometry
  matches the operator's file (only 9 of 6258 points differ, all within 10 mm
  of the bed centre where point sampling dominates the comparison), and
  420 mm of the 4298 mm pen path (9.8%) is parked, concentrated on the
  fur/claw/scallop zigzags including 24 parked moves on the head-back stretch.
- **Bench follow-up (2026-10-13): insufficient coverage.** With the
  operator's 350 mm/min settings the 2.5 mm rule parks only 12 of the 83
  outer-outline moves through the back-of-head zone - the defect cluster's
  reversals sit ~3.6 mm apart - and the outline defect persisted on the
  plot. The rule is the right mechanism but needs a wider default (about
  4-4.5 mm) or a density-based criterion. Parked-mode accuracy itself was
  proven flawless by the bed-fixed full-plot diagnostic (`WSW-20261013-011`).

## Risks and follow-up

- Every park patch adds a clean A stop/start at its boundary. If a boundary
  ever shows a mark, raise or lower **Bed reversal park mm** in the settings
  dialog, or lower **Max bed step deg**.
- If the scallop still shows anything on paper, the next levers are the A
  drivetrain preload (belt tension, pulley grub screws, 12:1 coupling) and the
  A driver current.

## Files

- `software/converter_core/settings.py`: setting, validation, docs, dialog row.
- `software/converter_core/kinematics.py`: mask and two-pass planner.
- `software/tests/test_reversal_parking.py`: mask, planner and validation
  tests with the real stretched-geometry fixture.
- `samples/gcode/heraldic-revpark.gcode`: regenerated bench sample.
