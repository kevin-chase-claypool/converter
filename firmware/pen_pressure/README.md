# Pen pressure control

Independent closed-loop control of pen contact force, on its own MCU. Driven by
the grblHAL spindle-enable line as a **mode override**, not a position command.

## Behavior

- **LIFT** (input = M5): drive the pen actuator open-loop to a safe retract
  height; force loop paused. Report `pen_is_lifted` when there.
- **ENGAGE** (input = M3): release the override; seek down slowly until the load
  cell crosses the contact threshold, then hold target force, tracking paper/bed
  unevenness while drawing. Report `pen_in_contact` once settled.

The host's `G4` dwell after M3/M5 gives this loop time to reach the LIFT/ENGAGE
state before motion resumes (open-loop handshake). A later upgrade: feed-hold
grblHAL until `pen_in_contact` is asserted (true closed-loop handshake, e.g., via
a grblHAL plugin reading a contact input).

## Safety (build into ENGAGE)

- approach rate-limit (don't slam the pen down)
- max-seek / stall guard → abort to LIFT if no contact (paper missing / bed too low)
- force clamp on PID output
- force LIFT on any fault / E-stop

## Open decisions

- load-cell interface: HX711 vs ADC + instrumentation amp
- actuator type for pen height (geared DC + encoder, stepper, voice coil…)
- separate MCU now vs. fold into a grblHAL plugin later

## SparkFun Pro Micro RP2350 prototype

The integrated separate-MCU bench firmware lives in
[`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino).
It targets the Arduino IDE with the SparkFun Pro Micro RP2350 board selected.

Prototype wiring assumptions mirror `docs/hardware/WIRING_TABLE.md`:

| RP2350 pin | Connection |
|---|---|
| `GP29` / `A3` | M3/M5 command input from PC817C U1. The module has an external 10 kΩ pullup to local 3.3 V; an asserted optocoupler pulls GP29 LOW. |
| `GP27` / `A1` | Conditioned `A_HOME` output to RP23CNC A limit/home input through the selected switch-like interface |
| `GP28` / `A2` | `HOME_ARM` input from PC817C U2. The module has an external 10 kΩ pullup to local 3.3 V; an asserted optocoupler pulls GP28 LOW, allowing `GP27 A_HOME` to assert only while homing is intentionally armed. |
| `GP4` | DRV8833 `IN1` |
| `GP5` | DRV8833 `IN2` |
| `GP6` | ACEIRMC DRV8833 `EEP` protection/fault output |
| `GP7` | ACEIRMC DRV8833 `ULT` low-true sleep input |
| `GP0` | HX711 `DT`/`DOUT` |
| `GP1` | HX711 `SCK` |
| Qwiic `GPIO16/GPIO17` | TMAG5273 `SDA/SCL` |

The sketch defaults to a safe lift/stop behavior, supports serial bench commands,
and keeps HX711 force thresholds as raw-count placeholders until E-07/E-08
establish calibration and noise data. Do not install the pen or connect the
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
| [`e08_hx711_rate_noise/e08_hx711_rate_noise.ino`](e08_hx711_rate_noise/e08_hx711_rate_noise.ino) | Measures actual stationary HX711 sample rate and raw-count noise in one quiet 15-second UART result; keeps the motor driver inactive. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e09_tmag5273_verification/e09_tmag5273_verification.ino`](e09_tmag5273_verification/e09_tmag5273_verification.ino) | Verifies TMAG5273 I2C identity, on-demand magnetic vector, and stationary field stability through the intended Qwiic wiring; keeps the motor driver inactive. | SparkFun TMAG5273 Arduino Library |
| [`bench_sensors/bench_sensors.ino`](bench_sensors/bench_sensors.ino) | Tests HX711 raw readings and TMAG5273 Qwiic telemetry without energizing the motor driver. | HX711 and SparkFun TMAG5273 |
| [`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino) | Combines GP29 command input, GP27 A_HOME output assignment gated by GP28 HOME_ARM, DRV8833 motor control, HX711 force feedback, and TMAG5273 telemetry. | HX711 and SparkFun TMAG5273 |

Recommended bench order: run `bench_sensors` first, run `bench_motor_command`
with the actuator unloaded, then flash `pro_micro_rp2350_toolhead` only after
the sensor signs, motor direction, and command polarity are known.

Arduino IDE must use these libraries:

| Library Manager name | Version checked | Purpose |
|---|---:|---|
| `HX711 Arduino Library` by Bogdan Necula / bogde | 0.7.5 | HX711 load-cell ADC |
| `SparkFun TMAG5273 Arduino Library` | 2.0.0 | TMAG5273 Qwiic Hall sensor |
| `SparkFun Toolkit` | 1.2.0 | Dependency installed by the SparkFun TMAG5273 library |

Do not install or select Rob Tillaart's separate `HX711` library for this
sketch; it also provides `HX711.h` and can create an ambiguous include.
