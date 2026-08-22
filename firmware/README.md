# Firmware - machine controller + pen pressure

Runs on the machine side, fully separate from the host `software/`. Two
independent subsystems:

Primary RP23CNC hardware and board-support reference:
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC).
The board-specific implementation sequence is
[`grblhal/UPCOMING_CODING_STEPS.md`](grblhal/UPCOMING_CODING_STEPS.md).

| Folder | Role | Target |
|---|---|---|
| [`grblhal/`](grblhal/) | Motion control - parses the host G-code and drives the X/Y/A steppers | RP23CNC / RP23U5XBB running grblHAL on RP2350 |
| [`pen_pressure/`](pen_pressure/) | Closed-loop pen contact-force control | Separate SparkFun Pro Micro RP2350 prototype; final placement pending tests |

## Why this split

Writing a G-code parser plus acceleration-aware motion planner from scratch is
the hard 80% of plotter firmware. **grblHAL already does it** and has an
RP2040/RP2350 port, so motion is configuration, not new code. The selected
motion controller is the RP23CNC / RP23U5XBB 5-axis grblHAL controller with the
Ethernet adapter. The pen-pressure loop is a distinct real-time concern. Its
final placement is still under evaluation: a supported RP2350 core-1/plugin
implementation is preferred if it does not disturb grblHAL timing; the current
bench prototype uses a separate SparkFun Pro Micro RP2350. See
[`../docs/decisions/ADR-002-toolhead-placement.md`](../docs/decisions/ADR-002-toolhead-placement.md).

## Integration contract

```text
host .gcode -> grblHAL on RP23CNC: X/Y/A motion, spindle/tool output state
                                      |
                                      +-> pen-pressure MCU
                                          M3 = ENGAGE (resume force loop, seek paper)
                                          M5 = LIFT   (retract, pause force loop)
```

- **Selected controller** - RP23CNC / RP23U5XBB with Ethernet adapter. Use its
  X/Y/A step-dir outputs, opto-isolated limit inputs for homing, and
  spindle-enable or another suitable digital output for the pen-pressure
  ENGAGE/LIFT signal.
- **`A` is motor-shaft degrees** - the host already applied the 12:1 pulley
  ratio. Configure grblHAL's A steps-per-unit as *motor steps per degree*; do
  **not** reapply the ratio. Or set `Theta ratio = 1` in the host and own the
  ratio here. Pick exactly one place.
- **Settle handshake** - the host emits a `G4` dwell after each `M3`/`M5`, from
  its `Pen cycle ms`, so grblHAL pauses for the pen to lift before travel and
  reach paper before drawing. A future grblHAL plugin can replace the fixed
  dwell with a feed-hold until the load cell reports actual contact.
- **Homing and bed calibration** - grblHAL owns normal X/Y/A homing and limit
  behavior. X/Y use physical limit switches. A uses a validated switch-like
  `A_HOME` signal from a separate RP2040/TMAG5273 magnetic adapter; the
  adapter reads the fixed-height TMAG5273, applies measured threshold and
  hysteresis behavior, and presents a digital home input to RP23CNC. The host
  calibration script is for setup and maintenance: it commands scan moves,
  records RP2040 diagnostics, and determines constants before normal startup
  homing is trusted. Send `M5` and verify the pen/toolhead is retracted before
  any homing or magnetic scan. See
  [`grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`](grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md).
- **Candidate probe capture** - F-08 will test the RP23CNC `PRB` input and
  grblHAL G38 transition/coordinate behavior without TB6600 signal leads or
  motors attached. The installed XYZA build must explicitly prove or reject A
  probing. GP27/U3 remains assigned to `LIMA` until that motorless test and the
  subsequent isolated-path check pass.

## Status

The RP23CNC grblHAL baseline now boots over native USB: F-01 passed on
2026-08-14 with the RP23U5XBB board target, four-axis XYZA build, W5500, and
SD/Ymodem support. Controller I/O and motion remain untested and disconnected.
A separate-MCU pen-pressure prototype sketch
now exists at
[`pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino)
for integrated bench testing the DRV8833, HX711, TMAG5273, and M3/M5 command
input. With the proposed PC817C module, its GP29 M3/M5 and GP28 `HOME_ARM`
inputs are externally pulled HIGH and optocoupler assertions pull them LOW;
the integrated sketch is configured for that active-low interface. F-05/E-18
must still establish the RP23CNC ENA/Aux0 state mapping before the harness is
connected. Two smaller Arduino sketches also exist for safer bring-up:
[`pen_pressure/bench_motor_command/bench_motor_command.ino`](pen_pressure/bench_motor_command/bench_motor_command.ino)
tests only GP29 and the DRV8833, and
[`pen_pressure/bench_sensors/bench_sensors.ino`](pen_pressure/bench_sensors/bench_sensors.ino)
tests only the HX711 and TMAG5273.
For powered pen-tip calibration, use
[`pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`](pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino).
It uses a 3.3 V USB-to-TTL service adapter on GP20/GP21 rather than the Pro
Micro USB-C port, and limits every actuator command to one short step followed
by DRV8833 sleep. This is a temporary bench/service interface, not part of the
normal plotter control path.
Follow [`grblhal/UPCOMING_CODING_STEPS.md`](grblhal/UPCOMING_CODING_STEPS.md),
then see
[`../docs/HANDOFF.md`](../docs/HANDOFF.md) -> "Goals / roadmap -> Pi Pico 2 firmware"
for the full plan and the open sub-decisions.
