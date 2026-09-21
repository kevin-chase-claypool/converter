---
id: WINSW-20260921-001
date: 2026-09-21
category: windows-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration
tags:
  - cs1238
  - calibration
  - known-mass
  - plotting
related:
  - RPSW-20260921-001
  - E-09C
  - ADR-006
---

# Add Pro Micro known-mass calibration application

## Summary

Added a separate Windows application for the single-Pro-Micro CS1238
known-mass test. It connects to one native-USB COM port, captures raw sensor
records, and writes reviewable CSV and graph outputs.

## Reason

Manual serial commands would make repeated 0–70 g loading/unloading captures
and later paper figures error-prone. The simplified hardware method requires
an equally simple operator workflow without restoring the Pico/INA101 fixture.

## Implementation

`run_known_mass_calibration.bat` launches a Tkinter application after installing
its `pyserial` and `matplotlib` dependencies if needed. The app sends only
`STATUS`, `TARE`, and `CAPTURE <ms>` to E-07D firmware. Each completed capture
is immediately stored as an unmodified `raw/point_*.csv`; its final-half mean
is a separate row in `calibration_points.csv`. The app fits
`grams = slope * raw + offset` and writes the JSON summary plus calibration,
residual, and raw-trace PNG graphs.

## Verification

- Python syntax compilation passed for the Windows program.
- Deterministic synthetic points verify the ordinary-least-squares fit and
  residual calculation.
- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350
  firmware\pen_pressure\e07d_cs1238_known_mass_calibration` passed.
- No Pro Micro, CS1238, load cell, weights, or actuator was connected for this
  source-only milestone.

## Risks and follow-up

The app cannot prove the CS1238 wiring, effective sample rate, load-cell
mounting, or weight alignment. E-07C/E-08C remain first. Do not treat the
displayed 40–60 g raw window as a force-controller setting until E-09C and the
subsequent actuator-response work are documented.

## Files

- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py`: one-port guided capture, raw storage, fit, and graphs.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/run_known_mass_calibration.bat`: Windows launcher.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/README.md`: updated operator method.
- `docs/testing/TEST_PLAN.md`: current E-09C method and acceptance record.
- `docs/decisions/ADR-006-pro-micro-known-mass-cs1238-calibration.md`: lasting calibration-architecture decision.
