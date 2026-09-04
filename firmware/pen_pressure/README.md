# Pen pressure control

Independent closed-loop control of pen contact force, on its own MCU. Driven by
the grblHAL spindle-enable line as a **mode override**, not a position command.

## Planned behavior

- **PEN_CLEAR** (input = M5): retract until the filtered load-cell value returns
  to its measured no-contact release band, then apply one bounded, calibrated
  clearance pulse. The force loop is paused and `pen_is_clear` is reported.
- **ENGAGE** (input = M3): release the override; seek down slowly until the load
  cell crosses the contact threshold, then hold target force, tracking paper/bed
  unevenness while drawing. Report `pen_in_contact` once settled.
- **LIFT_HOME** (boot/recovery/service only): retract fully until the planned
  `GP2` switch reference is reached. This establishes an absolute lift datum;
  it is not the normal high-cycle M5 operation.

Different pens, markers, and pencils may sit at different heights in the
clamp. Normal control therefore uses the calibrated load-cell residual to
identify **pressing** (`F_contact_on`) and **clear** (`F_release_off`), not one
shared pen-tip height. The planned P100 toolhead preflight will home, baseline,
seek actual paper at limited force, clear normally, and require a stable clear
result before allowing a newly installed tool to plot. It proves contact and
release only; the load cell cannot report an exact unloaded air gap.

The host's `G4` dwell after M3/M5 gives this loop time to reach the
`PEN_CLEAR`/`ENGAGE` state before motion resumes (open-loop handshake). A later
upgrade: feed-hold
grblHAL until `pen_in_contact` is asserted (true closed-loop handshake, e.g., via
a grblHAL plugin reading a contact input).

## Safety (build into ENGAGE)

- approach rate-limit (don't slam the pen down)
- max-seek / stall guard → abort to LIFT if no contact (paper missing / bed too low)
- force clamp on PID output
- force LIFT on any fault / E-stop

## Open verification

- Complete the T-01A through T-01J motor/preload physical-capability sequence
  in [`docs/testing/TEST_PLAN.md`](../../docs/testing/TEST_PLAN.md) before
  choosing travel limits, force limits, LIFT dwell, or correction-pulse bounds.
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
- Calibrate the installed HX711/load-cell force slope and final control gains.
- Complete actuator travel, stall, seek-timeout, and safe-fault testing.
- Decide whether the later `CONTACT_READY`/`TOOL_FAULT` handshake is necessary
  after the fixed-dwell version is proven.
- Complete E-18/F-08 for the Pro Micro RP2350 magnetic-output path.

## Planned force-control strategy

Use a **slow, pulse-based PI trim loop**, not a conventional high-bandwidth PID.
The installed HX711 measured 11.93 Hz (E-08), and the current three-sample
median plus correction cadence yields approximately four useful corrections per
second.  That is appropriate for compensating slow paper/bed height change,
but it cannot cancel pen vibration or a fast height disturbance.

The N20/50:1/M4 actuator has ample low-speed mechanical advantage for pen
force, but its gearbox, lead screw, rail, and pen mechanism introduce static
friction, backlash, and a likely self-locking hold.  Continuous PWM around a
force setpoint would therefore tend to alternately stick and jump.  Treat one
correction as a bounded directional motor pulse followed by measurement and
settling:

1. Convert the load-cell reading to a signed force unit after E-07 establishes
   a repeatable slope. Normalize the installed negative sensor sign in software;
   do not depend on raw-count polarity in the controller.
2. Filter only enough to reject spikes: the existing median-of-three is the
   starting point. Measure its settled noise with the motor and motion system
   active before selecting a deadband.
3. At no more than 4 Hz, calculate `error = target_force - measured_force`.
   A deadband around zero commands no motion. Outside it, proportional effort
   selects pulse direction and duration; a small, leaky integral term removes
   slow bias from friction and bed slope.
4. Clamp pulse width, duty/PWM, total consecutive correction travel, and the
   integral state. Integrate only when a commanded correction is not saturated;
   clear or decay it when lifting, seeking, changing direction, entering a
   deadband, or faulting. This is required anti-windup, not an optional tune.
5. After a pulse, keep the driver asleep/idle until at least one new filtered
   HX711 result is available. A direction reversal requires an extra settle
   window. The hard force limit remains an immediate independent fault.

Start with **P only**. Add the small leaky I term only after repeated, static
contact shows a consistent force bias that P cannot remove. Do not add a D
term to force error: at this sample rate it chiefly amplifies HX711 noise and
motor/pen vibration while adding delay. If damping is later needed, use a
bounded change-of-command rule or a derivative of the *filtered* force only;
keep it disabled unless a logged comparison shows an improvement.

The mechanical design has an equally important role. Give the pen a compliant
element (spring/flexure or compliant pen mount) with useful travel around the
target force, minimize guide friction and moving mass, and avoid a loose
load-cell/pen force path. The control loop should correct quasi-static surface
variation; compliance must absorb stroke vibration and height changes faster
than the roughly 4 Hz loop can follow.

### Bed unevenness and rotating-bed plan

First run force hold with X/Y/A stationary, then translate only, then rotate
the bed at progressively higher constant angular speeds. Record force versus
bed angle, radius, feed rate, and drawing direction. A printed circular bed
can have a repeatable height field `h(radius, angle)` as well as random
vibration. The PI loop corrects the slow residual. Only after it is stable
should firmware add a bounded, optional angle-indexed feed-forward table
learned from those measurements; index it by bed angle and radius, blend it
smoothly, and retain the force loop and all limits as the authority.

Choose drawing speeds so the dominant once-per-revolution error is comfortably
slower than the demonstrated closed-loop bandwidth. If testing shows the
surface disturbance is faster, increase compliance or slow the bed; do not
raise PID gains beyond the HX711/actuator settling limit.

### Required characterization and tuning sequence

1. E-06 bounded stall check passed with a 6.0 V supply limited to 0.20 A: the
   owner reports 0.18 A stall current, approximately 30 s hold duration, and
   10 successful repeats while holding the selected preload. This establishes
   the tested actuator capability; optional thermal/rail/endurance
   characterization remains separate before making a full production safety
   claim.
2. Complete T-01 and map lift/seek direction. Use a representative pen or
   guarded force fixture to establish global 5, 10, 20, and 40 ms pulse bounds
   in both directions, then wait for a new filtered sample. Record force
   increment, delay, overshoot, repeatability, and minimum pulse that reliably
   breaks stiction. Do not treat that force-per-pulse response as universal:
   each installed pen or pencil gets a short bounded response check during
   T-01J, while the load cell remains the force-control authority. The existing
   50 ms final approach is explicitly too coarse for a production calibration.
3. Complete E-07 using at least three gentle force levels and repeated
   lift/re-contact cycles. Establish the force slope, offset drift, force-path
   hysteresis, and a target range safely below the 300 g load-cell capacity.
   The known preload change with Z position means every contact sequence must
   use its current unloaded reference; an old tare is not valid after travel.
4. Set the deadband from motor-active noise and the smallest repeatable pulse
   effect, not from E-08 stationary ADC noise alone. Tune P upward from a
   conservative pulse duration until the step response is prompt but does not
   reverse/oscillate. Then add the smallest leaky I that removes sustained
   error without creating a limit cycle.
5. Run T-03's static, X/Y, and A rotation profiles. Save the telemetry and
   report mean error, 95th-percentile absolute error, peak force, correction
   count, reversals, faults, and force-versus-angle plots. Enable a
   feed-forward map only if repeatable angle/radius structure remains.

## SparkFun Pro Micro RP2350 dual-core implementation

The integrated separate-MCU bench firmware lives in
[`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino).
It targets the Arduino IDE with the SparkFun Pro Micro RP2350 board selected.

Prototype wiring assumptions mirror `docs/hardware/WIRING_TABLE.md`:

| RP2350 pin | Connection |
|---|---|
| `GP29` / `A3` | M3/M5 command input from PC817C U1. The module has an external 10 kΩ pullup to local 3.3 V; an asserted optocoupler pulls GP29 LOW. |
| `GP27` / `A1` | Conditioned readiness/magnetic-state output through U3; installed at `LIMA`, candidate `PRB` only after F-08 |
| `GP28` / `A2` | Two-phase arm input from PC817C U2. An assertion pulls GP28 LOW: first arm requests readiness ACK, release clears it, second arm exposes threshold state on GP27. |
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
readiness/magnetic output. Fixed-size atomics carry status between cores.
During a magnetic scan, a verified lifted state is required and the HX711 is
powered down because pressure measurement is unnecessary.

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
| [`e08_hx711_rate_noise/e08_hx711_rate_noise.ino`](e08_hx711_rate_noise/e08_hx711_rate_noise.ino) | Measures actual stationary HX711 sample rate and raw-count noise in one quiet 15-second UART result; keeps the motor driver inactive. | HX711 Arduino Library by Bogdan Necula / bogde |
| [`e09_tmag5273_verification/e09_tmag5273_verification.ino`](e09_tmag5273_verification/e09_tmag5273_verification.ino) | Verifies TMAG5273 I2C identity, on-demand magnetic vector, and stationary field stability through the intended Qwiic wiring; keeps the motor driver inactive. | SparkFun TMAG5273 Arduino Library |
| [`bench_sensors/bench_sensors.ino`](bench_sensors/bench_sensors.ino) | Tests HX711 raw readings and TMAG5273 Qwiic telemetry without energizing the motor driver. | HX711 and SparkFun TMAG5273 |
| [`pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino) | Dual-core integrated pressure/safety and magnetic-readiness/threshold controller for GP29, GP28, GP27, DRV8833, HX711, and TMAG5273. | HX711 and SparkFun TMAG5273 |

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
