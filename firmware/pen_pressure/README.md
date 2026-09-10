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
- Complete E-07's digital-scale transfer calibration with a capped/dummy tool
  clamped as a real pen: establish the signed filtered-HX711-delta to
  grams-force conversion, residual, and hysteresis before selecting raw force
  thresholds or final control gains. This is an occasional service
  calibration/profile-verification activity, not a scale check required at
  every print.
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

The target is a slow pulse-based P/PI trim loop using the measured approximately
11.93 Hz HX711 input. The full rationale, characterization sequence,
anti-windup bounds, and rotating-bed policy live in
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
| `GP6` | ACEIRMC DRV8833 `EEP` protection/fault output |
| `GP7` | ACEIRMC DRV8833 `ULT` low-true sleep input |
| `GP0` | HX711 `DT`/`DOUT` |
| `GP1` | HX711 `SCK` |
| Qwiic `GPIO16/GPIO17` | TMAG5273 `SDA/SCL` |

The integrated sketch divides work across the RP2350 cores. Core 0 owns the
pressure state machine, HX711, DRV8833, GP29, faults, telemetry, and watchdog.
Core 1 owns the TMAG5273, GP28 two-phase arm/readiness handshake, and GP27
output arbitration. GP28 activity always suppresses normal-print status; Core
1 first forces GP27 inactive for 20 ms before issuing a fresh magnetic ACK.
Outside P100, it can expose Core 0's stable-contact or proven-clear status only
when the explicit gate is enabled. Fixed-size atomics carry status between cores.
During a magnetic scan, a verified lifted state is required and the HX711 is
powered down because pressure measurement is unnecessary.

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
| [`e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`](e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino) | GP20/GP21 `Serial2` service-UART test: single sleeping actuator pulses, HX711 diagnostics, and read-only active-low GP2 `LIFT_HOME` reports for guarded T-01G movement. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e08_hx711_rate_noise/e08_hx711_rate_noise.ino`](e08_hx711_rate_noise/e08_hx711_rate_noise.ino) | Measures actual stationary HX711 sample rate and raw-count noise in one quiet 15-second UART result; keeps the motor driver inactive. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e09_tmag5273_verification/e09_tmag5273_verification.ino`](e09_tmag5273_verification/e09_tmag5273_verification.ino) | Verifies TMAG5273 I2C identity, on-demand magnetic vector, and stationary field stability through the intended Qwiic wiring; keeps the motor driver inactive. | SparkFun TMAG5273 Arduino Library |
| [`bench_sensors/bench_sensors.ino`](bench_sensors/bench_sensors.ino) | Tests HX711 raw readings and TMAG5273 Qwiic telemetry without energizing the motor driver. | HX711 and SparkFun TMAG5273 |
| [`p100_handshake_test/p100_handshake_test.ino`](p100_handshake_test/p100_handshake_test.ino) | Motor-inert F-08/E-18 diagnostic for the actual GP28 two-phase arm and GP27 readiness/threshold return. It never configures or writes DRV8833, M3/M5, HX711, or LIFT_HOME pins. | SparkFun TMAG5273 |
| [`t01g_lift_home_uart/t01g_lift_home_uart.ino`](t01g_lift_home_uart/t01g_lift_home_uart.ino) | Motor-safe T-01G diagnostic: reads GP2 with `INPUT_PULLUP` and writes a fixed 115200-baud `lift_home` line only through GP20/GP21 UART1. | none beyond Arduino core |
| [`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino) | Dual-core integrated pressure/safety and magnetic-readiness/threshold controller for GP29, GP28, GP27, DRV8833, HX711, and TMAG5273. | HX711 and SparkFun TMAG5273 |

Recommended bench order: run `bench_sensors` first. For F-08/E-18 before the
replacement actuator is installed, `p100_handshake_test` may validate the real
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
| `SparkFun TMAG5273 Arduino Library` | 2.0.0 | TMAG5273 Qwiic Hall sensor |
| `SparkFun Toolkit` | 1.2.0 | Dependency installed by the SparkFun TMAG5273 library |

Do not install or select Rob Tillaart's separate `HX711` library for this
sketch; it also provides `HX711.h` and can create an ambiguous include.
