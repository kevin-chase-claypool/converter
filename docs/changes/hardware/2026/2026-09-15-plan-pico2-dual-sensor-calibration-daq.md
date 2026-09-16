---
id: HW-20260915-001
date: 2026-09-15
category: hardware
affected_categories:
  - rp23cnc-software
  - windows-software
status: planned
components:
  - hardware/toolhead
  - firmware/pen_pressure
  - pico2-daq
tags:
  - pico2
  - cs1238
  - ina101
  - strain-gauge
  - force-calibration
  - testing
related:
  - E-07C
  - E-08C
  - E-09C
---

# Plan Pico 2 dual-sensor calibration DAQ

## Summary

Defined a temporary, USB-streaming Pico 2 fixture for calibrating the installed
toolhead load cell against the instructor-supplied 5 N reference sensor.

## Reason

The installed HX711 and kitchen-scale procedure failed the required
force-transfer classification. The replacement test needs one local monotonic
time base for raw toolhead-CS1238 counts and raw reference-sensor readings.

## Implementation

CS1238 #1 is assigned to Pico GP2 (`SCK`) and GP3 (`DT`/`DRDY-DOUT`) during
the test; the INA101 board's metered-safe analogue output is assigned to
Pico GP26/ADC0 through a 1 kOhm series resistor. The Pico emits raw records
over micro-USB to a PC logger. The plan explicitly retains production Pro
Micro GP0/GP1 ownership after the temporary fixture is removed.

## Verification

Documentation and schematic review only. No sensor, INA101 board, Pico pin,
or load-cell connection has been energized or measured under this plan.

## Struggles and rejected approaches

Directly connecting the unknown INA101 output to Pico ADC0 was rejected. TI
specifies the INA101 as requiring at least 10 V total supply and having
substantial output headroom, so the actual board's supply, gain, output
reference, and full-scale output must be metered before connection.

## Risks and follow-up

The board photo identifies INA101KU and labels `OUT`, `5V`, `+V`, `-V`, and
`GND`; it also shows a 100 kOhm trim and 4.3 kOhm fixed resistor. The INA101
gain law is `G = 1 + 40 kOhm / R_G`, but the photo alone does not establish
whether the trim is series or parallel with the fixed resistor. The reference
sensor terminal mapping and actual output span remain open. Preserve raw data;
no force conversion, filtering, or automatic actuation is authorized by this
plan. Keep the physical E-stop and main-power cutoff accessible during any
later loaded test.

The bench diagram explicitly shows the two supply boundaries: PC USB supplies
the Pico (which supplies 3.3 V only to CS1238 #1), while a verified external
dual supply provides INA101 `+V`, `-V`, and `GND`. Its separately drawn 5 V
lead is intentionally marked TBD: terminal labelling alone is not evidence it
is the reference bridge-excitation connection.

## Files

- `docs/hardware/PICO2_DUAL_SENSOR_DAQ.md`: test wiring, storage, and safety authority.
- `docs/hardware/pico2-dual-sensor-daq.html`: viewable bench schematic.
- `docs/hardware/WIRING_TABLE.md`: planned fixture connections.
- `docs/hardware/BOM.md`: DAQ components and verification gates.
