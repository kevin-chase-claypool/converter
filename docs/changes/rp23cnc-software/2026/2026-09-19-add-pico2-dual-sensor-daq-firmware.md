---
id: RPSW-20260919-001
date: 2026-09-19
category: rp23cnc-software
affected_categories:
  - hardware
  - windows-software
status: implemented
components:
  - firmware/pen_pressure/pico2_dual_sensor_daq
  - docs/hardware/PICO2_DUAL_SENSOR_DAQ.md
  - docs/integration/INTERFACES.md
tags:
  - pico2
  - cs1238
  - ina101
  - force-calibration
  - raw-data
related:
  - HW-20260915-001
  - E-09C
---

# Add Pico 2 dual-sensor DAQ firmware

## Summary

Added native Raspberry Pi Pico SDK firmware for the temporary Pico 2
dual-sensor calibration fixture. It streams raw CS1238 and reference ADC0 data
with Pico-clock timestamps and does not control the plotter actuator.

## Reason

The installed toolhead load cell must be calibrated against the instructor's
5 N reference sensor. The historical HX711/kitchen-scale method does not
provide the required simultaneous raw channels or a shared measurement clock.

## Implementation

`pico2_dual_sensor_daq.cpp` configures CS1238 #1 as channel A, gain 128,
external reference, and 640 SPS. Each `SAMPLE` record includes a signed raw
24-bit CS1238 value plus an unfiltered Pico ADC0 code, timestamped from the
Pico monotonic microsecond timer. GP14 marker-edge interrupts emit `EVENT`
records. GP15 remains a latching physical DAQ enable; USB `START` requires it
to be ON and `STOP` is always accepted. USB CDC is the only Pico interface.

The required raw-stream grammar and Pico SDK build steps are documented with
the source. A later Windows runner can split `SAMPLE` and `EVENT` payloads into
separate CSV files while retaining PC wall-clock time as metadata.

## Verification

- `git diff --check` passed.
- Static source review confirmed no Arduino headers, Pro Micro UART pins,
  DRV8833 pins, or actuator-command code are present.
- A local Pico SDK / ARM GNU build toolchain is not installed, so compilation
  and actual-board CS1238/ADC timing remain unverified.

## Struggles and rejected approaches

Arduino-Pico firmware was rejected because this fixture is specifically for the
user's Raspberry Pi Pico 2 and needs an explicit Pico SDK target, not an
Arduino board-core dependency. The existing Pro Micro CS1238 Arduino sketch
remains intact as a separate sensor bring-up artifact.

## Risks and follow-up

The actual CS1238 board's wiring, excitation/reference behavior, and the
INA101 output span remain unverified. Do not connect ADC0 until the documented
0-3.3 V meter check passes. Build, flash, and perform the motor-unpowered
marker/30-second raw-stream dry run before applying toolhead 6 V or load.

## Files

- `firmware/pen_pressure/pico2_dual_sensor_daq/CMakeLists.txt`: Pico SDK build target.
- `firmware/pen_pressure/pico2_dual_sensor_daq/pico2_dual_sensor_daq.cpp`: raw two-channel fixture firmware.
- `firmware/pen_pressure/pico2_dual_sensor_daq/README.md`: build and serial protocol.
- `firmware/README.md`: identifies Pico 2 fixture ownership.
- `firmware/pen_pressure/README.md`: documents the source and safety boundary.
- `docs/hardware/PICO2_DUAL_SENSOR_DAQ.md`: records firmware behavior and raw data contract.
- `docs/hardware/WIRING_TABLE.md`: links fixture USB wiring to the implemented stream.
- `docs/integration/INTERFACES.md`: records the temporary serial data contract.
