# Pico 2 dual-sensor calibration DAQ

## Purpose and boundary

This is a temporary, supervised bench fixture for calibrating the installed
toolhead 300 g load cell. It replaces the historical HX711/kitchen-scale
method. It does not change the production toolhead controller, force-control
state machine, M3/M5 interface, or E-stop topology.

The Pico 2 reads both channels on one monotonic microsecond time base and
streams raw records through its micro-USB connection to a PC logger. The PC
wall clock identifies a run; Pico timestamps are the measurement time base.

The accompanying wiring diagram is
[`pico2-dual-sensor-daq.html`](pico2-dual-sensor-daq.html).

## Test wiring

| Path | Connection | Status / condition |
|---|---|---|
| Toolhead sensor | Installed 300 g load cell -> CS1238 #1 channel A | Planned. Use the received board's verified `E+`, `E-`, `A+`, and `A-` labels. The load cell must not be connected to an HX711 or Pro Micro ADC at the same time. |
| CS1238 power | Pico 2 `3V3(OUT)` -> `VCC`; Pico `GND` -> `GND` | Planned. Confirm the actual CS1238 board is 3.3 V-safe and its bridge-reference configuration/excitation before power. |
| CS1238 digital | Pico `GP2` -> `SCK`; CS1238 `DT`/`DRDY-DOUT` -> Pico `GP3` | Planned. Both signals are 3.3 V logic. No level shifting is authorized until the received board is inspected. |
| Reference sensor | Instructor 5 N strain-gauge sensor -> existing INA101 board input | Planned. Identify the sensor conductors and board input/excitation terminals from their markings before connecting. |
| INA101 supply | Isolated/bench supply according to the actual INA101 board marking | Required verification. The INA101 IC is not a Pico-3.3-V-powered amplifier; do not infer the board's supply pinout or required rails. |
| INA101 output | Confirmed, nonnegative, 0-3.3 V `OUT` -> 1 kOhm series resistor -> Pico `GP26` / ADC0 | Required verification. Probe the output first. A negative or greater-than-3.3-V output must never reach Pico ADC0. |
| ADC reference | INA101 output reference/return -> Pico `AGND` only after the board's output reference is identified | Required verification. This is the signal reference, not permission to tie unknown power rails together. |
| Test switch | Pico `GP15` -> normally-open momentary switch -> Pico `GND` | Optional physical START/STOP. Firmware uses `INPUT_PULLUP`. |
| PC link | Pico micro-USB -> PC | USB power and CDC serial stream for the DAQ fixture. |

The production Pro Micro retains its existing GP0/GP1/3V3/GND CS1238 path when
the test fixture is removed. The test harness temporarily gives CS1238 #1 its
own Pico connections; do not parallel either ADC's clock or data pins.

## Raw stream and PC storage

The Pico emits one record per CS1238 conversion at the measured delivered
rate, starting at the Pico `t = 0` event. It samples ADC0 immediately before
or after that conversion and preserves both acquisition timestamps:

```csv
toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw
0,5823412,8,1247
1563,5825518,1571,1251
```

The PC-side logger owns a dated run directory, `samples.csv`, a plain-text
serial log, and `metadata.json`. Metadata includes the PC wall-clock start,
Pico firmware version, CS1238 configuration, INA101 supply/gain settings,
sensor identities, and operator notes. No moving average, tare subtraction,
or force conversion is permitted in the acquisition CSV.

## Required checks before live loading

1. With power removed, inspect and photograph both CS1238 boards, the INA101
   board, and the reference sensor; record labels and wire mapping.
2. Complete E-07C bridge-resistance and `E+`--`E-` excitation checks for
   CS1238 #1 before accepting readings.
3. Power the INA101 only from its verified supply arrangement. With the
   reference sensor unloaded and then gently loaded, meter its output before
   connecting Pico ADC0. It must stay in the inclusive 0-3.3 V range with
   margin across the planned 5 N range.
4. Verify the Pico `AGND` signal-reference connection produces a stable ADC
   reading without creating an unexpected supply-to-supply current path.
5. Verify raw CS1238 and ADC records with no actuator power. Only then permit
   a guarded, operator-supervised loading test with the existing physical
   E-stop and main-power cutoff accessible.

## Calibration interpretation

Calibrate the reference-sensor path independently into force first. Use its
timestamped force and the closest raw CS1238 sample to evaluate the toolhead
sensor's signed transfer, linearity, hysteresis, and residuals. Do not assume
the relationship is linear or copy resulting constants into the toolhead
controller until the force-path acceptance test is documented.
