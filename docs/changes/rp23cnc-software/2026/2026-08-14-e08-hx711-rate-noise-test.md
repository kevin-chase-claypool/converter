---
id: RPSW-20260814-002
date: 2026-08-14
category: rp23cnc-software
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/e08_hx711_rate_noise/e08_hx711_rate_noise.ino
  - docs/testing/TEST_PLAN.md
  - docs/report/lab-notes/2026-08-14-e-08-hx711-rate-noise.md
tags:
  - hx711
  - sample-rate
  - noise
  - toolhead
related:
  - RPSW-20260814-001
  - HW-20260814-002
---

# Add E-08 HX711 Rate and Noise Test

## Summary

Added a quiet, powered-toolhead E-08 sketch that reports the actual HX711
sample rate and stationary raw-count noise over a fixed 15-second window.

## Reason

The force-control filter and correction timing must use the installed HX711's
measured data-ready rate and noise, rather than an assumed converter setting.

## Implementation

The sketch uses the established GP0/GP1 HX711 wiring and the temporary
GP20/GP21 `Serial2` service UART. It never enables the DRV8833. Command `r`
collects samples for 15 seconds and reports sample count, elapsed time, sample
rate, mean, minimum, maximum, peak-to-peak span, and sample standard deviation
using an online variance calculation.

## Verification

Compiled for `rp2040:rp2040:sparkfun_promicrorp2350`. Two stationary 15-second
bench windows each produced 179 samples, or 11.933 Hz. Peak-to-peak noise was
300 then 484 counts; standard deviation was 69.1 then 120.5 counts.

## Struggles and rejected approaches

Continuous telemetry was not used because it obscures a concise result in the
UART Serial Monitor and does not measure the actual data-ready rate as clearly.

## Risks and follow-up

The E-08 result supports a three-ready-sample median (about 0.25 s) and a
maximum approximately 4 Hz force-correction cadence after actuator settling.
Actual force setpoint/deadband tuning remains E-07/T-03 work because mechanical
preload, rather than ADC noise, dominates force uncertainty.

## Files

- `firmware/pen_pressure/e08_hx711_rate_noise/e08_hx711_rate_noise.ino`: E-08 firmware.
- `docs/testing/TEST_PLAN.md`: E-08 execution status.
- `docs/report/lab-notes/2026-08-14-e-08-hx711-rate-noise.md`: procedure and results record.
