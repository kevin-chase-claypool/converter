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
| [`pen_pressure/`](pen_pressure/) | Closed-loop pen contact-force control | RP2350 plugin/core 1 or separate MCU, pending tests |

## Why this split

Writing a G-code parser plus acceleration-aware motion planner from scratch is
the hard 80% of plotter firmware. **grblHAL already does it** and has an
RP2040/RP2350 port, so motion is configuration, not new code. The selected
motion controller is the RP23CNC / RP23U5XBB 5-axis grblHAL controller with the
Ethernet adapter. The pen-pressure loop is a distinct real-time concern. Its
final placement is still under evaluation: a supported RP2350 core-1/plugin
implementation is preferred if it does not disturb grblHAL timing; otherwise it
will use a separate MCU. See
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

## Status

Planning is complete; physical assembly and firmware bring-up are not started.
Follow [`grblhal/UPCOMING_CODING_STEPS.md`](grblhal/UPCOMING_CODING_STEPS.md),
then see
[`../docs/HANDOFF.md`](../docs/HANDOFF.md) -> "Goals / roadmap -> Pi Pico 2 firmware"
for the full plan and the open sub-decisions.
