---
id: WSW-20261021-001
date: 2026-10-21
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
  - WSW-20261020-003
---

# Center hold is now a 60 mm diameter

## Summary

The centre hold is specified as a **diameter** and defaults to **60 mm**
(a 30 mm radius). The setting is now `theta_center_hold_diameter_mm`,
labelled **Center hold diameter mm** in the sidebar and **Center hold** on
the CMYK tab (default 60, range 0-200). The planner parks the bed for
drawing points inside the 30 mm radius.

## Reason

The operator asked for a 60 mm diameter ("lets make it 60 instead -
diameter"). The previous field and UI were radius-based at 20 mm, which
invited unit mistakes; the A-rate saturation and the observed wobble extend
beyond that radius anyway, so a 30 mm radius gives margin.

## Implementation

- `settings.py`: `theta_center_hold_diameter_mm` (default 60, validated
  nonnegative); sidebar label **Center hold diameter mm**; tooltip states
  the diameter equals a 30 mm radius at the default.
- `kinematics.py`: `_apply_center_hold` divides the setting by two and
  compares each drawing point's radius; the per-point hold and the
  Max-bed-step sweep gate on leaving are unchanged.
- `cmyk_tab.py`: **Center hold** spin default 60 (0-200) feeds the diameter
  through `apply_tab_settings` for the preview, all four ink programs and the
  calibration sheet.

## Verification

- Real yellow layer (`cmyk-y-1792529836934-71025f.svg`, frame centre 100,100,
  tolerance 0.05): 1,190 segments lie fully inside r = 30. With the hold
  disabled 712 of them rotate the bed; with the 60 mm diameter all 1,190
  hold. Contour count unchanged at 640; total hold segments 13,504 ->
  14,354.
- Tests updated for the diameter semantics; the reversal-parking isolation
  test disables the centre hold explicitly.
- Full suite: 425 tests pass (1 skipped).

## Struggles and rejected approaches

- Keeping the radius field and entering 30: rejected - the operator asked
  in diameter and the labels should match the unit being set.
- A separate diameter control beside the radius one: rejected as duplicated
  state and a new source of mismatch.

## Risks and follow-up

- The 60 mm hold covers a larger area than 20 mm: more gantry travel near the
  centre, slightly slower, and the default changes existing Xθ/Yθ plans. Set
  0 to disable or reduce the value.
- Bench print of the wave screen is the acceptance check; XY only remains
  the whole-print precision mode.

## Files

- `software/converter_core/settings.py`: renamed field, 60 mm default, label, tooltip.
- `software/converter_core/kinematics.py`: diameter-to-radius hold logic.
- `software/generator_tabs/cmyk_tab.py`: Center hold default 60 and wiring.
- `software/tests/test_kinematics_choice.py`, `software/tests/test_cmyk_tab.py`,
  `software/tests/test_reversal_parking.py`: updated coverage.
- `software/README.md`: current-state documentation.
