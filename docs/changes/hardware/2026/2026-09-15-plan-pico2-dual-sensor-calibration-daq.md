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

The bench diagram shows PC USB supplying the Pico (which supplies 3.3 V only
to CS1238 #1), while one series-linked dual-output bench supply provides the
INA101 `+5 V`, `0 V`, and `-5 V` rails. If continuity proves the board's `5V`
terminal is the reference bridge-excitation input, it branches from that same
+5 V rail; it is not a separate third supply. Terminal mapping remains a
power-off prerequisite.

An operator checklist now makes the power-off inspection, exclusive ADC
ownership, supply/output-span proof, raw-data acceptance, and de-energized
shutdown gates explicit. It does not claim DAQ firmware or the PC logger
exists yet.

The test purpose is commanded downward pen-pressure calibration, not a static
sensor-only exercise: the established 6 V toolhead rail powers the DRV8833 and
the S7V8F5-regulated Pro Micro path during the loaded phase. The Pico owns
measurement only; the existing 3.3 V service UART sends supervised Pro Micro
commands. The toolhead bridge remains disconnected from the Pro Micro ADC.

Research selected the existing USB-to-TTL service adapter as the lowest-change
second PC COM port: it preserves external Pro Micro power, sends only
low-rate commanded-motion events, and leaves all 640-SPS force data on Pico
USB. Direct externally powered Pro Micro USB CDC is a separately metered
later option, not a prerequisite.

The fixture now reserves temporary Pro Micro `GP1` as a 3.3 V
`MOTION_ACTIVE` output to Pico `GP14`, with a separate `TOOL_GND` to Pico
`GND` reference wire. The Pico must timestamp both edges locally, so a command
event and both force channels share the same clock. The marker is not a
production interface and GP1 returns to CS1238 clock duty after the test.

Each completed E-09C run now requires a raw-data package and reproducible
paper figure set: raw dual-sensor overlay, calibrated-reference/toolhead-count
overlay, force-transfer and residual plot, and timestamp/sample-quality
evidence. The Pico's marker-event lane represents Pro Micro actuation; PC
command-receipt timestamps are retained only as an audit log.

## Files

- `docs/hardware/PICO2_DUAL_SENSOR_DAQ.md`: test wiring, storage, and safety authority.
- `docs/hardware/pico2-dual-sensor-daq.html`: viewable bench schematic.
- `docs/hardware/WIRING_TABLE.md`: planned fixture connections.
- `docs/hardware/BOM.md`: DAQ components and verification gates.
- `docs/report/FORCE_CALIBRATION_RESULTS.md`: raw-data and final-paper figure requirements.
