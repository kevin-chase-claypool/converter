---
id: WSW-20261024-005
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_wave_rotation_isolation_test.py
  - samples/gcode/wave-rotation-isolation-base.gcode
  - samples/gcode/wave-rotation-isolation-low-a-accel.gcode
  - software/tests/test_wave_rotation_isolation.py
tags:
  - cmyk
  - wave-screen
  - a-axis
  - rotation
  - diagnostic
  - acceleration
  - test-sheet
related:
  - WSW-20261024-004
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Add a one-sheet CMYK wave-rotation isolation test

## Summary

Added a compact two-run test sheet that compares identical wave patches under
parked motion, increasing bed rotation, reduced drawing feed, and reduced A
acceleration. The paper remains mounted for both files, and registration is
performed only once.

## Reason

The 16:30 post-fix print still showed the spacing pattern. Its generated source
and compensated G-code paths are regular, while the operator localizes the
remaining distortion to large bed rotations during pen-down drawing. Printing
a fresh sheet for every hypothesis is slow and risks changing paper mounting
between runs.

## Implementation

- `tools/make_wave_rotation_isolation_test.py` generates four identical wave
  rows for each case using the active compensation profile and converter feed
  planner.
- `wave-rotation-isolation-base.gcode` draws six patches:
  - case 1, top-left: parked A0 control at `F700`;
  - case 2, top-centre: `+5 deg` rotation at `F700`;
  - case 3, top-right: `+10 deg` rotation at `F700`;
  - case 4, middle-left: `+14.5 deg` baseline at `F700`;
  - case 5, middle-centre: `+14.5 deg` at reduced `F350`;
  - case 6, middle-right: `-14.5 deg` at `F700`.
- `wave-rotation-isolation-low-a-accel.gcode` draws a second parked control
  (case 7) and case 8 below it after the operator changes `$123` from `6000`
  to `3000`.
- Both files use the normal pen contract, compensation, center coordinates,
  and end park. The second file must be run without re-registering or moving
  the paper.

## Verification

- Added `software/tests/test_wave_rotation_isolation.py`, which runs the
  generator through its CLI, checks both outputs and all eight case markers,
  rejects malformed comments, checks every case reconstructs the same
  bed-space wave, and checks the bed-step/A-rate/rapid guards.
- `python -m unittest -v software.tests.test_wave_rotation_isolation`: both
  tests pass.
- Full converter discovery passes 502 tests with one OpenGL-context skip.

### Physical result

- The base pass ran at `$123=6000`; the second pass ran at `$123=600`.
- The operator reports that all eight patches look the same and none
  reproduces the full-image spacing pattern.
- Large pen-down A rotation is not sufficient to reproduce the defect, and a
  10x reduction in A acceleration produces no visible improvement.
- Both generated files pass `tools/check_gcode_motion.py --strict`.
- The largest per-block drawing rotation is `0.40 bed deg`; the largest
  commanded A rate is `108 motor deg/s`, inside the installed `15 deg` and
  `500 deg/s` limits. Both files use fed travel for any bed rotation.

## Struggles and rejected approaches

- Reusing the full yellow image in parked and rotating copies would require two
  large prints and makes patch-to-patch comparison harder.
- Overdrawing several configurations at the same coordinates would make the
  lines difficult to separate on one pen colour.
- Changing `$123` inside a paused program was rejected because grblHAL setting
  writes are not guaranteed while a program is paused. The reduced-acceleration
  case is a second file with no paper or registration change.

## Risks and follow-up

- The second file is valid only after `$$` confirms `$123=3000`; restore
  `$123=6000` afterward.
- This is a diagnostic, not a production pattern or controller calibration.
- Results must be recorded before changing either A acceleration or the wave
  generator again.

## Files

- `tools/make_wave_rotation_isolation_test.py`: deterministic generator.
- `samples/gcode/wave-rotation-isolation-base.gcode`: cases 1-6.
- `samples/gcode/wave-rotation-isolation-low-a-accel.gcode`: cases 7-8.
- `software/tests/test_wave_rotation_isolation.py`: generator/CLI guards.
- `docs/testing/TEST_PLAN.md`: M-13 procedure and current status.
- `docs/project/ROADMAP.md` and `docs/project/ENGINEERING_LOG.md`: current
  diagnosis and next hardware step.
