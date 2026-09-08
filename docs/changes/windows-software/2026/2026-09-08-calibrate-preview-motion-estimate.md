---
id: WSW-20260908-001
date: 2026-09-08
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_theta_feed.py
tags:
  - preview
  - timing
  - m-06
  - calibration
related:
  - HW-20260907-002
---

# Calibrate the preview motion-time estimate

## Summary

The converter now applies a display-only `0.467368` calibration to draw and
rapid-motion time. It was derived from the pen-free M-06 radius-sweep result:
75.05 s observed motion divided by the prior 160.58 s model estimate. The
preview now displays the calibrated estimate and the unscaled model time.

## Reason

The installed RP23CNC completed the controlled radius sweep cleanly in 1:15.05
while the preview estimated 2:40.58. The owner requested that the estimator
reflect that measured machine behavior.

## Implementation

`DEFAULT_MOTION_ESTIMATE_SCALE` and `calibrated_motion_seconds()` provide a
validated conversion seam. The Qt Preview settings panel exposes `Motion
estimate scale`, defaulting to `0.467368`. The scale applies only to planned
draw/rapid motion duration; configured pen dwell time remains literal, and no
feed rate, preview geometry, or emitted G-code changes.

## Verification

- `python -m unittest discover -s software\tests -v` passed: 20 tests.
- The new calibration test verifies 160.58 model seconds maps to 75.05 seconds.
- `python -m py_compile software\converter_core\settings.py software\converter_core\gcode.py` passed.

## Struggles and rejected approaches

Scaling generated feed rates was rejected: the M-06 run validates the current
machine motion and the requested change concerns scheduling information, not
motion commands. Scaling pen dwell time was also rejected because those are
explicit G4 durations and were absent from the pen-free measurement.

## Risks and follow-up

This is one total pen-free measurement, not a general performance model. Repeat
with like-for-like timing or capture inner/middle/outer durations before
changing the factor. Production pen behavior may be slower because pen dwells
remain unscaled by design.

## Files

- `software/converter_core/settings.py`: calibration constant and validator.
- `software/qt_svg_to_gcode.pyw`: editable display-only scale and transparent estimate output.
- `software/tests/test_theta_feed.py`: regression coverage.
- `software/README.md`: current estimate behavior and scope.
