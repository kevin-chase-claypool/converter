---
id: RPSW-20260814-001
date: 2026-08-14
category: rp23cnc-software
affected_categories:
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07_hx711_calibration/e07_hx711_calibration.ino
tags:
  - hx711
  - load-cell
  - calibration
  - bench-test
related:
  - docs/testing/TEST_PLAN.md
  - docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md
---

# Add dedicated HX711 E-07 calibration sketch

## Summary

Added a sensor-only Pro Micro RP2350 sketch for E-07 that reports raw HX711
readings, supports an unloaded tare, and exposes signed deltas for known-mass
calibration without energizing the motor driver.

## Reason

The HX711 and load cell need independent raw-data and sign verification before
their measurements are used in closed-loop pen control or combined with the
TMAG5273 test.

## Implementation

The sketch uses GP0 for HX711 `DT`/`DOUT` and GP1 for `SCK`. It reports at 500
ms intervals at 115200 baud and accepts `t` to tare and `p` to request an
immediate record. The associated E-07 lab note embeds the exact code and
procedure, including USB-only power with the 6 V toolhead JST disconnected.

## Verification

- Arduino compilation for `rp2040:rp2040:sparkfun_promicrorp2350`: pending.
- Bench readings and known-mass calibration: E-07 pending.

## Struggles and rejected approaches

The general `bench_sensors` sketch also initializes TMAG5273, which would mix
two independent tests. It is retained for later combined diagnostics; E-07 uses
the smaller HX711-only sketch.

## Risks and follow-up

Determine measured noise, sample rate, sign, and counts-per-mass in E-07/E-08
before selecting contact and force-hold thresholds.

## Files

- `firmware/pen_pressure/e07_hx711_calibration/e07_hx711_calibration.ino`: E-07 firmware.
- `firmware/pen_pressure/README.md`: staged-sketch index.
- `docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md`: exact test record.
