---
id: WSW-20261024-001
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/bed_calibration.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_bed_photo_measurement.py
  - tools/make_bed_error_calibration.py
  - samples/gcode/bed-error-map.gcode
  - samples/gcode/bed-error-map.csv
tags:
  - bed
  - compensation
  - calibration
  - angle
  - cmyk
  - striation
---

# Expand full-field bed calibration to eight angles

## Summary

The one-sheet full-field calibration now measures the same 37 whole-bed
stations at **0/45/90/135/180/225/270/315 degrees**, plus the A=0 reference
and post-rotation control. The sheet contains 333 station marks and still fits
inside the 13-inch test field.

## Reason

The previous analyzer measured only 0/90/180/270 and filled every intermediate
angle by linear interpolation. The failing CMYK wave screens use 45- and
75-degree layouts, while center-hold contours can park at arbitrary bed
angles. Operators observed black and magenta adjacent-row spacing defects near
bed center even after reducing feed. A four-angle calibration could not
measure the missing angular behavior.

Adding another small patch would require another paper setup. Expanding the
existing whole-bed sheet keeps the spatial coverage while gathering the
intermediate-angle data before the paper is removed.

## Implementation

- Added 45/135/225/315 calibration passes to `PASS_SPECS`, each in a unique
  diagonal lane around every station.
- Retained 37 stations on 50/95/150 mm rings, four fiducials, the A=0
  reference, and an A=0 control after the complete rotation sweep.
- Generalized profile construction and verification comparison to use every
  measured angle instead of hard-coded quadrant angles.
- Bumped the generated calibration program to v3. It performs nine passes with
  eight drying pauses and one pen.
- Regenerated `bed-error-map.gcode` and its 337-row measurement CSV.

## Verification

- `py -m unittest discover -s software\tests -p "test_bed_*.py" -v` passes all
  32 bed calibration, photo, compensation, and planner tests.
- Generated sheet: 3,136 G-code lines, 333 station L marks plus four
  fiducials, eight `M0` pauses, and a `163.754 mm` maximum ink radius inside
  the `165.100 mm` test radius.
- `py tools\check_gcode_motion.py --strict samples\gcode\bed-error-map.gcode`
  passes the step, A-rate, and rapid-rotation guards.

## Struggles and rejected approaches

- Replacing the whole-bed sheet with a small center-only test was rejected
  because it would improve only a narrow region and require another paper
  change to regain outer-field coverage.
- Keeping the four cardinal angles and lowering numerical acceptance limits
  was rejected because 45/135/225/315 errors would still be unobserved.
- Interpolating missing angular fields was rejected as the exact limitation
  that produced the current complaint.

## Risks and follow-up

- The photo now contains 333 station components instead of 185. Marker
  extraction must be run on a sharp, flat overhead image; retaping or moving
  the sheet still invalidates the calibration.
- The sheet takes longer to plot because it has nine passes and eight drying
  pauses, but it remains one paper setup.
- The current default profile is unchanged. The eight-angle profile becomes
  usable only after the measured sheet passes leave-one-station-out gates and
  an independently compensated verification sheet passes every angle stage.
- Direct adjacent-wave-row pitch remains a separate acceptance check (M-13);
  the expanded map improves angular sampling but does not itself prove screen
  spacing on paper.

## Files

- `software/converter_core/bed_calibration.py`: eight-angle passes and generic
  profile/comparison construction.
- `tools/make_bed_error_calibration.py`: v3 one-sheet generator and dynamic
  pass reporting.
- `samples/gcode/bed-error-map.gcode` and `bed-error-map.csv`: regenerated
  calibration program and measurement template.
- `software/tests/test_bed_compensation.py` and
  `software/tests/test_bed_photo_measurement.py`: angle coverage and expanded
  mark-count regressions.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: current procedure, acceptance gates, and status.
