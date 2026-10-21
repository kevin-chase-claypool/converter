---
id: WSW-20261020-003
date: 2026-10-20
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/kinematics.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - theta
  - kinematics
  - cmyk
  - center
  - precision
related:
  - WSW-20261020-001
  - WSW-20261015-001
---

# Center hold radius: park the bed for fine strokes near the bed centre

## Summary

New `theta_center_hold_mm` setting (default 20 mm), exposed as **Center hold
radius mm** in the sidebar and **Center hold** on the CMYK tab. Drawing
points inside that radius are traced with the bed parked; the gantry draws
the same bed-frame geometry in X/Y. The per-move rotation gate still limits
how the bed is brought back to the planned angle after leaving the hold
region.

## Reason

CMYK wave-screen rows wobbled near the bed centre even with Path tolerance
at 0.05 mm. The saved yellow program shows the tolerance is honoured: the
largest residual bed-path bow of any emitted move is 0.043 mm (r < 10 mm)
and 0.032 mm (10-20 mm). The actual problem is the A axis: at r = 10 mm and
700 mm/min a straight paper move would need about 48,000 motor deg/min,
above the controller's 30,000 limit, so the centre is A-rate-limited with
frequent reversals and scrubbing. The same file had 455 of 730 segments
fully inside r = 20 mm rotating the bed, with up to 12.1 bed degrees in a
single move inside r = 10 mm. Tolerance cannot fix a mechanical/A-rate
following error.

## Implementation

- `settings.py`: `theta_center_hold_mm` (default 20, validated nonnegative),
  sidebar row and tooltip.
- `kinematics.py`: `plan_contour_thetas` applies a resolver-independent
  centre-hold pass: every point inside the radius uses the entry bed angle,
  then a sweep limiter re-applies `Max bed step deg` when the contour leaves
  the region. Strategy labels become `hold` (or the dominant gantry axis)
  for the changed segments; the bed-frame artwork is unchanged.
- `cmyk_tab.py`: **Center hold** spin (default 20 mm) feeds
  `theta_center_hold_mm` through `apply_tab_settings`, so the preview, the
  four ink programs and the calibration sheet share it.

## Verification

- On the real yellow layer (`cmyk-y-1792529836934-71025f.svg`, frame centre
  100,100, tolerance 0.05): with the default 20 mm hold all 730 segments
  fully inside r = 20 now hold the bed (0 rotating, was 455); contour count
  unchanged at 640; total hold segments rise 13,504 -> 14,078.
- New `test_kinematics_choice.py` cases: centre segments inside the radius
  have zero theta change and `hold` labels while outer segments still
  rotate; enabling the hold adds hold segments versus 0.
- `test_cmyk_tab.py`: the tab's Centre hold value reaches
  `apply_tab_settings` (20 default, 35 when set).
- Full suite: 425 tests pass (1 skipped).

## Struggles and rejected approaches

- Lowering Path tolerance further: rejected - 0.05 residual is 0.043 mm and
  is already at the setting; the wobble is A-dominated motion, not
  subdivision error.
- Lowering Max bed step deg only: helps near the centre but also parks the
  bed across the whole plot; the radius-limited hold targets the actual
  region.

## Risks and follow-up

- The default changes existing Xθ/Yθ plans: points inside 20 mm now add
  gantry travel and can be slightly slower. Set 0 to restore the old
  behavior.
- Center hold removes the A-dominated regime but does not correct other
  mechanical errors; **Bed motion = XY only** remains the precision mode for
  the whole print. A bench print of the wave screen is the acceptance check.

## Files

- `software/converter_core/settings.py`: field, row, tooltip, validation.
- `software/converter_core/kinematics.py`: centre-hold planner pass.
- `software/generator_tabs/cmyk_tab.py`: Center hold control and wiring.
- `software/tests/test_kinematics_choice.py`, `software/tests/test_cmyk_tab.py`: tests.
- `software/README.md`: current-state documentation.
