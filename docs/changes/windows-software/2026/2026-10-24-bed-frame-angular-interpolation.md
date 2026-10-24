---
id: WSW-20261024-002
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/bed_compensation.py
  - software/converter_core/gcode.py
  - software/tests/test_bed_compensation.py
tags:
  - bed
  - compensation
  - angle
  - interpolation
  - frame
  - striation
related:
  - WSW-20261024-001
  - WSW-20261023-004
  - ADR-009
---

# Interpolate bed compensation in the rotating bed frame

## Summary

Compensation between measured bed angles is now blended in **bed coordinates**
and then rotated into machine XY at the requested angle. Previously, the
already-rotated machine-XY correction vectors were blended directly.

## Reason

The operator reported that striations worsened after bed compensation was
enabled, especially between the four cardinal calibration angles. The old
interpolation shortened and misdirected corrections whenever the bed angle was
between samples.

A synthetic one-millimetre bed-frame error sampled at 0 and 90 degrees
reproduced the defect: interpolation at 45 degrees returned a correction of
`0.500/0.500 mm` instead of `0.707/0.707 mm`, leaving a `0.207 mm` vector
error. Across the installed profile, the corrected interpolation changes
off-cardinal vectors by up to `0.485 mm`, enough to explain a visible
row-spacing regression.

## Implementation

- `BedCompensationProfile` precomputes each stored machine correction in the
  bed frame.
- Angular interpolation uses those bed-frame vectors.
- The interpolated bed-frame correction is rotated into machine XY at the
  requested angle.
- Exact sample angles still return the stored correction.
- The JSON profile schema, sample values, fingerprint, and 5 mm bound are
  unchanged.
- New compensated G-code includes `angular interpolation bed-frame` in its
  header so corrected files can be distinguished from earlier output.

## Verification

- Added a regression that failed under machine-frame blending and now passes:
  a constant bed error sampled at 0/90/180/270 degrees is recovered exactly at
  45 degrees.
- The existing angle interpolation/wrap test now verifies the rotating-frame
  result for both an intermediate angle and the 315-to-360 wrap.
- All 33 bed calibration, photo, compensation, and planner tests pass.
- The full converter suite passes 495 tests with one OpenGL-context skip.
- Repeated compensation/preview and saved-G-code parity tests remain green.

## Struggles and rejected approaches

- Keeping machine-frame linear interpolation and relying on the eight-angle
  test was rejected: finer sampling reduces but does not correct the frame
  mismatch.
- Changing the JSON schema was rejected because the stored values are already
  unambiguous machine-frame corrections; only the between-sample operation was
  wrong.
- Rotating only one endpoint was rejected because it does not preserve the
  sampled correction at either angle or the periodic 315/0 boundary.

## Risks and follow-up

- Every compensated G-code file generated before the header marker must be
  regenerated. Editing or reusing those coordinates retains the old error.
- The profile fingerprint is data-only and does not change; use the G-code
  header marker to distinguish the new interpolation algorithm.
- The eight-angle calibration remains necessary. Correct frame interpolation
  improves values between samples, while the expanded sheet measures the
  previously missing 45/135/225/315 fields directly.
- Physical row-spacing acceptance remains M-13 on the black and magenta wave
  screens.

## Files

- `software/converter_core/bed_compensation.py`: bed-frame correction cache and
  angular interpolation.
- `software/converter_core/gcode.py`: interpolation-version header marker.
- `software/tests/test_bed_compensation.py`: rotation-aware interpolation and
  end-to-end machine-point regression.
- `docs/decisions/ADR-009-post-registration-bed-compensation.md`,
  `software/README.md`, and `docs/integration/INTERFACES.md`: current transform
  semantics and regeneration requirement.
