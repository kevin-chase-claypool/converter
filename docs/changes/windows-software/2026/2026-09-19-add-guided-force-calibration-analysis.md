---
id: WINSW-20260919-001
date: 2026-09-19
category: windows-software
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/force_calibration_test/pc_logger
  - firmware/pen_pressure/force_calibration_test
  - docs/hardware/PICO2_DUAL_SENSOR_DAQ.md
tags:
  - force-calibration
  - pico2
  - cs1238
  - ina101
  - plotting
related:
  - RPSW-20260919-001
  - E-09C
---

# Add guided force-calibration analysis workflow

## Summary

The temporary Windows fixture application now guides reference-sensor
calibration from known masses, toolhead CS1238 transfer acquisition, and the
saved analysis products needed for review and the course paper.

## Reason

Raw dual-channel records alone cannot establish a defensible transfer function.
The reference strain gauge first needs an ADC-count-to-force conversion; the
toolhead fit must then compare its raw CS1238 count to calibrated reference
force without silently discarding raw transients.

## Implementation

The app persists known-mass reference points and their linear fit, and writes a
reference CSV, JSON, and plot. Auto Calibrate retains every raw sample but uses
only the common post-settling region for the CS1238-to-reference-force fit. A
result folder contains the combined raw CSV, summary JSON, time-trace,
transfer-fit, and residual plots. The live monitor also shows independent
CS1238/reference settling estimates and the slower combined result.

## Verification

- `python -m py_compile` passed for both Python fixture programs.
- Synthetic raw-trace settling calculation and exact linear-fit checks passed.
- `python tools\docs_index.py --write`, `--check`, and `git diff --check`
  passed.
- No physical hardware, INA101 output-span check, or loaded force run has been
  performed.

## Struggles and rejected approaches

Fitting every dynamic sample would bias a static transfer calibration with
mechanical transient and hysteresis behavior. The app therefore preserves every
sample for its time-trace graph but uses only detected settled samples for the
proposed linear fit.

## Risks and follow-up

Matplotlib is installed by the batch launcher on first use. The resulting
linear fit remains a proposal until the operator reviews the residual and
up/down hysteresis plots and records physical bench evidence. The reference
board output must still be metered within Pico ADC range before connection.

## Files

- `firmware/pen_pressure/force_calibration_test/pc_logger/force_calibration_gui.py`: guided UI, persistence, stable-window fit, and plots.
- `firmware/pen_pressure/force_calibration_test/pc_logger/requirements.txt`: plotting dependency.
- `firmware/pen_pressure/force_calibration_test/pc_logger/run_force_calibration.bat`: first-run dependency installation.
- `firmware/pen_pressure/force_calibration_test/README.md`: operator workflow.
- `docs/hardware/PICO2_DUAL_SENSOR_DAQ.md`: fixture-data and analysis boundary.
