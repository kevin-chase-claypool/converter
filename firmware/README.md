# Firmware - machine controller + pen pressure

Runs on the machine side, fully separate from the host `software/`. Two
independent subsystems:

| Folder | Role | Target |
|---|---|---|
| [`grblhal/`](grblhal/) | Motion control - parses the host G-code and drives the X/Y/A steppers | RP23CNC / RP23U5XBB running grblHAL on RP2350 |
| [`pen_pressure/`](pen_pressure/) | Closed-loop pen contact-force control | separate MCU (load cell + force PID) |

## Why this split

Writing a G-code parser plus acceleration-aware motion planner from scratch is
the hard 80% of plotter firmware. **grblHAL already does it** and has an
RP2040/RP2350 port, so motion is configuration, not new code. The selected
motion controller is the RP23CNC / RP23U5XBB 5-axis grblHAL controller with the
Ethernet adapter. The pen-pressure loop is a distinct real-time concern and
lives on its own MCU so grblHAL's timing cannot starve it, and vice versa.

## Integration contract

```text
host .gcode -> grblHAL on RP23CNC: X/Y/A motion, M3/M5 spindle-enable output
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

## Status

Not started - this is the next build phase. See
[`../docs/HANDOFF.md`](../docs/HANDOFF.md) -> "Goals / roadmap -> Pi Pico 2 firmware"
for the full plan and the open sub-decisions.
