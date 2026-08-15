---
id: RPSW-20260731-001
date: 2026-07-31
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/README.md
  - firmware/pen_pressure/bench_motor_command/bench_motor_command.ino
  - firmware/pen_pressure/bench_sensors/bench_sensors.ino
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino
  - firmware/pen_pressure/README.md
  - docs/integration/INTERFACES.md
tags:
  - toolhead
  - rp2350
  - arduino
  - drv8833
  - hx711
  - tmag5273
related:
  - HW-20260731-001
  - F-05
  - E-07
  - E-08
  - E-09
---

# RP2350 Toolhead Prototype Firmware

## Summary

Added Arduino C++ bench firmware sketches for the SparkFun Pro Micro RP2350
toolhead controller.

## Reason

The toolhead wiring now has prototype RP2350 pin assignments, and the next
bench step needs firmware that can verify M3/M5 input behavior, DRV8833 motor
direction, HX711 readings, and TMAG5273 telemetry before installing a pen.

## Implementation

The integrated sketch boots into a safe lift/stop state, reads the protected
`GP8` M3/M5 command input, drives DRV8833 `IN1/IN2` with conservative PWM,
controls DRV8833 `EEP`/sleep, reads the optional DRV8833 fault line, reads
HX711 raw counts, and streams TMAG5273 Qwiic magnetic readings when the sensor
is present. Serial bench commands allow manual engage, lift, jog, stop, tare,
telemetry, and fault clear.

Two smaller sketches were added for staged bring-up. `bench_motor_command`
tests only `GP8` and the DRV8833 wiring without sensor dependencies.
`bench_sensors` tests only HX711 raw readings and TMAG5273 Qwiic telemetry
without energizing the motor driver.

## Verification

- Reviewed the sketch for pin consistency against `docs/hardware/WIRING_TABLE.md`.
- Installed `arduino-cli` 1.5.1 and compiled the sketch for
  `rp2040:rp2040:sparkfun_promicrorp2350`.
- Confirmed Arduino resolves `HX711.h` to `HX711 Arduino Library` 0.7.5 from
  `bogde/HX711`; removed the conflicting Rob Tillaart `HX711` library from the
  local Arduino library folder.
- Confirmed the SparkFun Pro Micro RP2350 board variant uses GPIO-numbered pins
  for the prototype assignments and Qwiic maps to `GPIO17/GPIO16`.
- Integrated sketch compile result after resolving libraries: 73,148 bytes
  program storage and 11,708 bytes dynamic memory.
- `bench_motor_command` compile result: 60,328 bytes program storage and
  10,872 bytes dynamic memory.
- `bench_sensors` compile result: 70,668 bytes program storage and 11,648 bytes
  dynamic memory.
- Ran `python tools\docs_index.py --write` and
  `python tools\docs_index.py --check`.

## Struggles and rejected approaches

The sketch intentionally does not include final calibrated force gains or
thresholds. Those values depend on E-07/E-08 load-cell calibration and noise
measurements.

## Risks and follow-up

The DRV8833 module label orientation, `EEP`/`ULT` behavior, HX711 3.3 V
operation, load-cell polarity, and RP23CNC M3/M5 polarity must be bench-tested
before integrated plotting.

## Files

- `firmware/README.md`: top-level firmware status now references the separate-MCU prototype and staged bench sketches.
- `firmware/pen_pressure/bench_motor_command/bench_motor_command.ino`: motor and M3/M5 command bench sketch.
- `firmware/pen_pressure/bench_sensors/bench_sensors.ino`: HX711 and TMAG5273 sensor bench sketch.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: Arduino C++ toolhead prototype firmware.
- `firmware/pen_pressure/README.md`: prototype firmware usage and pin table.
- `docs/integration/INTERFACES.md`: internal toolhead interface contract update.
