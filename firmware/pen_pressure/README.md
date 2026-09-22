# Pen pressure control

Independent closed-loop control of pen contact force, on its own MCU. Driven by
the grblHAL spindle-enable line as a **mode override**, not a position command.

## Current contract and behavior source

`M3` requests contact seek and force hold; `M5` requests normal `PEN_CLEAR`.
The converter follows both with a calibrated fixed `G4` dwell while the
toolhead reaches the requested state. This is the current no-new-wire
synchronization method; it is not a controller-visible ready handshake. The
integrated firmware contains a disabled-by-default GP27 normal-print-status
path for later use; it changes neither the controller endpoint nor the fixed
dwell until commissioning and a bounded controller-side wait are separately
approved.

[`CONTROL_STRATEGY.md`](CONTROL_STRATEGY.md) is the authoritative behavior
document for state transitions, force thresholds, per-tool preflight, profile
persistence, and tuning policy. This README owns current firmware status,
implemented pin assignments, staged sketches, and commissioning gates.

## Open verification

The upstream D36V50F6 6 V supply gate (E-14, constant 6.05 V), toolhead
perfboard inspection (E-14B), DRV8833/J2 mapping gate (E-14C), and S7V8F5
logic-rail gate (E-15A) passed on 2026-09-08. E-15 remains separate: it must
measure loaded D36V50F6 current, ripple, and temperature before force-control
work.

- Complete the T-01A through T-01J motor/preload physical-capability sequence
  in [`docs/testing/TEST_PLAN.md`](../../docs/testing/TEST_PLAN.md) before
  choosing travel limits, force limits, LIFT dwell, or correction-pulse bounds.
  T-01A currently establishes an in-housing spring-seat range of 20.37 mm
  unloaded to 1.95 mm at the lower hard endpoint (18.42 mm compression span).
  The 25.00 mm free length establishes 4.63 mm captured preload only; 1.95 mm
  is not spring solid height and is not an approved powered preload limit.
- Do not enable a firmware LIFT_HOME reference until T-01G verifies the planned
  `GP2`/`TOOL_GND` normally-open switch input and separate mechanical
  backstop margin.
- Do not enable normal M5 `PEN_CLEAR` until T-01H verifies the release
  hysteresis, debounce, calibrated clearance pulse, and actual pen-tip gap.
- Do not enable stored force-control parameters until T-01I proves that the
  accepted profile survives power cycles and that a fresh no-contact baseline
  stays RAM-only.
- Do not allow an interchangeable pen/pencil to plot until T-01J validates its
  contact/release preflight and its selected target-force/clearance settings.
- The installed HX711 failed the required E-07 transfer test and is retained
  only as diagnostic evidence. The selected CS1238 breakout will replace it on
  the same 300 g load cell, in the same two-hole HX711-form-factor footprint.
  It retains GP0→`DT`/`DRDY-DOUT` and GP1→`SCK`; it requires a new driver and
  a measured rate/noise/force-path qualification (E-07C through E-09C) before
  any force threshold or control gain is selected. The earlier NAU7802 purchase
  is retained as a spare, not the active design. This is an occasional
  service-calibration activity, not a scale check required before every print.
- The motor-inert CS1238 bring-up source is now available at
  [`e07c_cs1238_sensor_bringup/e07c_cs1238_sensor_bringup.ino`](e07c_cs1238_sensor_bringup/e07c_cs1238_sensor_bringup.ino).
  It uses native USB `Serial` only, leaves GP2 and GP4--GP7 untouched, and has
  no actuator command path. Before interpreting its output, E-07C must measure
  the *actual connected* load-cell excitation at `E+`--`E-`; some common
  CS1238 breakouts use a TL431-based bridge reference whose stock resistor
  arrangement may be unsuitable for a low-impedance load cell. The exact
  received board determines whether its documented reference modification is
  needed. This is a qualification check, not an approved circuit change.
- E-07D now uses only the Pro Micro and CS1238 with known precision masses.
  GP0/GP1 resume their intended CS1238 `DT`/`SCK` roles. The sensor-only sketch
  retains raw samples for a load/unload fit; its companion Windows program at
  `e07d_cs1238_known_mass_calibration/pc_logger/` guides capture through one
  native-USB COM port and writes raw CSV records plus report figures. Pico 2,
  INA101KU, and the instructor reference board are removed from the calibration
  method.
- The E-07B `r` fast-trace method is hardware-validated as a bounded bench
  procedure. A second, correctly clear-started 10 ms trace reached 59.3 g and
  returned to 0.0 g before the scale auto-off timer. It solves the manual
  workflow timing problem, but it also proved the present HX711 value cannot
  serve as pen force: 25.0 g occurred at essentially the same delta as zero
  force, and the HX711 remained strongly loaded after physical release. Do
  **not** enable automatic approach, a target, or a force limit until the
  load-cell force path/signal discrepancy is isolated.
- Complete actuator travel, stall, seek-timeout, and safe-fault testing.
- Decide whether the later `CONTACT_READY`/`TOOL_FAULT` handshake is necessary
  after the fixed-dwell version is proven. If adopted, complete F-08 input
  polarity/endpoint evidence, T-01H M5 clearance evidence, and a controller
  timeout/alarm implementation before enabling `GP27_NORMAL_STATUS_ENABLED`.
- Complete the remaining E-18/F-08 macro and coordinate stages for the Pro
  Micro RP2350 magnetic-output path. The 2026-09-10 motor-inert diagnostic
  passed installed Aux0/U2/GP28, local TMAG scan state, controller-visible PRB
  transitions, and real-magnet A-axis G38 entry/release through GP27/U3.
  `G65 P100 Q1`, parameters/coordinates, and all motion modes remain open.

## Force-control strategy

The target is a slow pulse-based P/PI trim loop. The former approximately
11.93 Hz HX711 result is historical only; select the CS1238 loop cadence from
its measured installed rate and noise, not its advertised maximum rate. The
full rationale, characterization sequence, anti-windup bounds, and rotating-bed policy live in
[`CONTROL_STRATEGY.md`](CONTROL_STRATEGY.md). Do not tune from this README;
choose measured limits only after the named tests pass.

## SparkFun Pro Micro RP2350 dual-core implementation

The integrated separate-MCU bench firmware lives in
[`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino).
It targets the Arduino IDE with the SparkFun Pro Micro RP2350 board selected.

Prototype wiring assumptions mirror `docs/hardware/WIRING_TABLE.md`:

| RP2350 pin | Connection |
|---|---|
| `GP29` / `A3` | M3/M5 command input from PC817C U1. The module has an external 10 kΩ pullup to local 3.3 V; an asserted optocoupler pulls GP29 LOW. |
| `GP27` / `A1` | Conditioned output through U3. During GP28/P100 it is exclusively the readiness/magnetic state; when P100 is idle it can later report contact/clear completion, but that mode is disabled by default. Installed at `LIMA`, candidate `PRB` only after F-08. |
| `GP28` / `A2` | Two-phase arm input from PC817C U2. An assertion pulls GP28 LOW: first arm requests readiness ACK, release clears it, second arm exposes threshold state on GP27. |
| `GP2` | `LIFT_HOME` normally-open microswitch to local `TOOL_GND`. Firmware uses `INPUT_PULLUP`; released reads HIGH and the fully retracted carriage reads LOW. The current implementation reports this in native-USB and GP20/GP21 service-UART telemetry only; it does not yet control motor motion. |
| `GP4` | DRV8833 `IN1` |
| `GP5` | DRV8833 `IN2` |
| `GP6` | Confirmed DRV8833 `EEP` low-true sleep input; drive HIGH to enable |
| `GP7` | Confirmed DRV8833 `ULT` low-true protection/fault output; `INPUT_PULLUP`, LOW is fault |
| `GP0` | CS1238 `DT`/`DRDY-DOUT` (channel A) |
| `GP1` | CS1238 `SCK` |
| Qwiic `GPIO16/GPIO17` | TMAG5273 `SDA/SCL` |

The integrated sketch divides work across the RP2350 cores. Core 0 owns the
pressure state machine, CS1238, DRV8833, GP29, faults, telemetry, and watchdog.
Core 1 owns the TMAG5273, GP28 two-phase arm/readiness handshake, and GP27
output arbitration. GP28 activity always suppresses normal-print status; Core
1 first forces GP27 inactive for 20 ms before issuing a fresh magnetic ACK.
Outside P100, it can expose Core 0's stable-contact or proven-clear status only
when the explicit gate is enabled. Fixed-size atomics carry status between cores.
During a magnetic scan, a verified lifted state is required and the CS1238 is
powered down because pressure measurement is unnecessary.

The integrated CS1238 backend configures channel A, gain 128, and 640 SPS. It
uses nonblocking `DT`/`DRDY` readiness followed by a CS123x `forceRead()`, then
forms a candidate 16-sample raw moving average. This source path is **not**
force-control authorization: `PRESSURE_CALIBRATION_VALID` remains false,
`CS1238_CONTACT_FORCE_SIGN` is deliberately zero, and all raw contact/target/
hard-limit values are zero placeholders until E-09C plus a later actuator-
response test establish them.

The temporary service interface is `Serial2` / hardware UART1 on GP20 (TX) and
GP21 (RX) at 115200 baud. The integrated sketch immediately writes `Theta
toolhead service UART ready` after configuring that interface, before pressure
or magnetic initialization. It writes completed telemetry records directly to
the UART; do not reintroduce an `availableForWrite() >= full_record_length`
gate, because the UART FIFO can be smaller than an entire record and would
silently suppress all service telemetry. Native USB `Serial` remains the
separate USB diagnostic/command interface.

The firmware defaults to a safe lift/stop behavior, supports serial diagnostics,
and keeps all actuator, force, lift-reference, and magnetic commissioning gates
false until their named tests establish measured values. Do not install the pen or connect the
RP23CNC M3/M5 line until motor direction, load-cell polarity, and input polarity
are verified on the bench. The integrated sketch is configured for the PC817C
module's active-low GP29/GP28 output; F-05 and E-18 must still verify the
RP23CNC-side ENA and Aux0 state mappings before the controller harness is
connected.

For staged bring-up, use the smaller sketches first. Each Arduino sketch must be
opened from its own folder:

| Sketch | Purpose | Libraries |
|---|---|---|
| [`bench_motor_command/bench_motor_command.ino`](bench_motor_command/bench_motor_command.ino) | Tests only `GP29`, DRV8833 `IN1/IN2`, `EEP`, and `ULT` with manual serial commands and short automatic M3/M5 pulses. | none beyond Arduino core |
| [`e07_hx711_calibration/e07_hx711_calibration.ino`](e07_hx711_calibration/e07_hx711_calibration.ino) | Tests only HX711 raw readings, tare, force sign, and known-mass calibration; keeps the motor driver inactive. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`](e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino) | GP20/GP21 `Serial2` service-UART test: single sleeping actuator pulses with pre-enable and during-drive `ULT` fault telemetry, HX711 diagnostics, read-only active-low GP2 `LIFT_HOME` reports, and two meter modes. `r`, after a clear-state `t` tare, runs a bounded 12-down/12-up 10 ms trace with timestamped HX samples and `x` abort. `v` holds logic states without motor motion. `o` holds each OUT1/OUT2 polarity for 30 seconds and is permitted only while both N20 leads are disconnected. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e07c_cs1238_sensor_bringup/e07c_cs1238_sensor_bringup.ino`](e07c_cs1238_sensor_bringup/e07c_cs1238_sensor_bringup.ino) | E-07C/E-08C native-USB sensor-only CS1238 bring-up. It provides raw sample/tare, 40/640/1280 SPS selection, 60-second Welford RMS-noise windows, and an internal-short diagnostic. It does not configure GP2 or GP4--GP7 and contains no motor, DRV8833, M3/M5, or TMAG code. | CS123x by FMazz97, 1.1.0 |
| [`e07d_cs1238_known_mass_calibration/e07d_cs1238_known_mass_calibration.ino`](e07d_cs1238_known_mass_calibration/e07d_cs1238_known_mass_calibration.ino) | Pro Micro-only E-07D known-mass CS1238 calibration. Its `pc_logger/run_known_mass_calibration.bat` companion opens a one-COM-port Windows capture/fit/graph application. Neither program configures motor, DRV8833, M3/M5, or TMAG pins. | CS123x by FMazz97, 1.1.0; Windows app: pyserial and matplotlib |
| [`e05_historical_03f6c00/e05_historical_03f6c00.ino`](e05_historical_03f6c00/e05_historical_03f6c00.ino) | Verbatim copy of historical commit `03f6c00` E-05 source: GP7 is driven high as sleep, GP6 is `INPUT_PULLUP` fault, followed by automatic 500 ms first and reverse pulses. Use only as an A/B historical reproduction, with clear travel in both directions. | none beyond Arduino core |
| [`e05_legacy_manual_steps/e05_legacy_manual_steps.ino`](e05_legacy_manual_steps/e05_legacy_manual_steps.ino) | Manual COM8/`Serial2` version of the historical GP7-high / GP6-`INPUT_PULLUP` roles. `u`/`d` use selected 100–1000 ms pulses in 100 ms increments; it never automatically issues a reverse motion. | none beyond Arduino core |
| [`e08_hx711_rate_noise/e08_hx711_rate_noise.ino`](e08_hx711_rate_noise/e08_hx711_rate_noise.ino) | Measures actual stationary HX711 sample rate and raw-count noise in one quiet 15-second UART result; keeps the motor driver inactive. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e09_tmag5273_verification/e09_tmag5273_verification.ino`](e09_tmag5273_verification/e09_tmag5273_verification.ino) | Verifies TMAG5273 I2C identity, on-demand magnetic vector, and stationary field stability through the intended Qwiic wiring; keeps the motor driver inactive. | SparkFun TMAG5273 Arduino Library |
| [`bench_sensors/bench_sensors.ino`](bench_sensors/bench_sensors.ino) | Tests HX711 raw readings and TMAG5273 Qwiic telemetry without energizing the motor driver. | HX711 and SparkFun TMAG5273 |
| [`p100_handshake_test/p100_handshake_test.ino`](p100_handshake_test/p100_handshake_test.ino) | Motor-inert F-08/E-18 diagnostic for the actual GP28 two-phase arm and GP27 readiness/threshold return. It never configures or writes DRV8833, M3/M5, HX711, or LIFT_HOME pins. | SparkFun TMAG5273 |
| [`t01g_lift_home_uart/t01g_lift_home_uart.ino`](t01g_lift_home_uart/t01g_lift_home_uart.ino) | Motor-safe T-01G diagnostic: reads GP2 with `INPUT_PULLUP` and writes a fixed 115200-baud `lift_home` line only through GP20/GP21 UART1. | none beyond Arduino core |
| [`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino) | Dual-core integrated pressure/safety and magnetic-readiness/threshold controller for GP29, GP28, GP27, DRV8833, CS1238, and TMAG5273. Its CS1238 threshold/sign placeholders and all motion gates are disabled. | CS123x by FMazz97, 1.1.0; SparkFun TMAG5273 |

Recommended CS1238 bench order: run `e07c_cs1238_sensor_bringup` first, then
the motor-inert `e07d_cs1238_known_mass_calibration` known-mass workflow. The
historical `bench_sensors` sketch remains only for preserving its HX711/TMAG
diagnostic evidence. For F-08/E-18 before the replacement actuator is installed,
`p100_handshake_test` may validate the real
GP28/GP27 handshake with no actuator-related pin activity. It is diagnostic
firmware only: it does not authorize P100 `Q3`/`Q4`, does not establish a safe
lift, and must be replaced with `pro_micro_rp2350_toolhead` before actuator or
production-P100 work. Run `bench_motor_command` with the actuator unloaded,
then flash `pro_micro_rp2350_toolhead` only after the sensor signs, motor
direction, and command polarity are known.

Arduino IDE must use these libraries:

| Library Manager name | Version checked | Purpose |
|---|---:|---|
| `HX711 Arduino Library` by Bogdan Necula / bogde | 0.7.5 | HX711 load-cell ADC |
| `CS123x` by FMazz97 | 1.1.0 | CS1238 load-cell ADC |
| `SparkFun TMAG5273 Arduino Library` | 2.0.0 | TMAG5273 Qwiic Hall sensor |
| `SparkFun Toolkit` | 1.2.0 | Dependency installed by the SparkFun TMAG5273 library |

Historical HX711 sketches require Bogde's `HX711 Arduino Library`; do not
install or select Rob Tillaart's separate `HX711` library for those sketches
because it also provides `HX711.h` and can create an ambiguous include. The
integrated controller instead requires CS123x 1.1.0.
