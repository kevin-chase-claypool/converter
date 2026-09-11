# Firmware - machine controller + pen pressure

Runs on the machine side, fully separate from the host `software/`. Two
independent subsystems:

Primary RP23CNC hardware and board-support reference:
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC).
Current motion-controller tasks are maintained in
[`../docs/project/ROADMAP.md`](../docs/project/ROADMAP.md).

| Folder | Role | Target |
|---|---|---|
| [`grblhal/`](grblhal/) | Motion control - parses the host G-code and drives the X/Y/A steppers | RP23CNC / RP23U5XBB running grblHAL on RP2350 |
| [`pen_pressure/`](pen_pressure/) | Closed-loop pen contact-force control and TMAG5273 magnetic sensing | Toolhead-mounted SparkFun Pro Micro RP2350 |

## Why this split

Writing a G-code parser plus acceleration-aware motion planner from scratch is
the hard 80% of plotter firmware. **grblHAL already does it** and has an
RP2040/RP2350 port, so motion is configuration, not new code. The selected
motion controller is the RP23CNC / RP23U5XBB 5-axis grblHAL controller with the
Ethernet adapter. The pen-pressure loop is a distinct real-time concern. Its
controller placement is now accepted: a separate SparkFun Pro Micro RP2350 on
the toolhead owns force control and TMAG5273 sensing so those workloads remain
isolated from grblHAL motion timing. See
[`../docs/decisions/ADR-002-toolhead-placement.md`](../docs/decisions/ADR-002-toolhead-placement.md).

## Integration contract

```text
host .gcode -> grblHAL on RP23CNC: X/Y/A motion, spindle/tool output state
                                          |
                                          +-> pen-pressure MCU
                                          M3 = ENGAGE (resume force loop, seek paper)
                                          M5 = PEN_CLEAR (release paper, add clearance pulse)
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
  its `Pen cycle ms`, so grblHAL pauses for the pen to clear the paper before
  travel and reach paper before drawing. Normal `M5` ends at the load-cell
  release threshold plus a calibrated clearance pulse; it does not travel to
  the distant `LIFT_HOME` switch. The toolhead firmware now has a
  disabled-by-default GP27 normal-print status guardrail, but grblHAL still
  uses the fixed dwell: no controller wait is enabled. A future bounded-timeout
  controller feature can consume that status after F-08 and force/clearance
  commissioning pass.
- **Homing and bed registration** - X/Y physical switches establish machine
  coordinates. A controller-resident `P100.macro` then uses the existing
  Aux0/GP28 arm and GP27/U3 return to capture a full center-magnet raster,
  compute an area centroid, register G54 X0/Y0, and scan the outer magnet twice
  to register G54 A0. The Pro Micro supplies only readiness and thresholded
  magnetic state; it never claims one threshold edge is the center. Send `M5`
  and verify the toolhead is retracted before any homing or scan. The production
  modes remain commissioning-locked. See
  [`grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`](grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md).
- **Candidate probe capture** - the 2026-09-10/11 motor-inert candidate
  proved direct and actual GP27/U3 `PRB` transitions, A-axis G38 capture, and
  the automated non-motion `G65 P100 Q1` readiness/release handshake.
  GP27/U3 is assigned to `PROBE SIG` with `$6=1`. The isolated Q2 X/Y homing
  branch passed both direct `$H` and SD-resident `G65 P100 Q2` execution on
  2026-09-11. Q0/Q3/Q4, coordinate semantics, and normal-status timing gates
  remain closed before P100 production use.

## Status

The RP23CNC grblHAL baseline now boots over native USB: F-01 passed on
2026-08-14 with the RP23U5XBB board target, four-axis XYZA build, W5500, and
SD/Ymodem support. Installed TB6600 signal response and unloaded X/Y/A motion
bring-up have since been partially commissioned: A M-01/M-02/M-04/M-05 and
X/Y M-01/M-02 checks passed for their documented scopes. The Y M-03 check
measured exactly 100 mm at `$101=80.000000`; the current owner-caliper-verified
X setting is `$100=80.00000`. X/Y physical homing then passed single-axis and
repeated combined tests using the east/south NC switches, with Z/A excluded.
The guarded X/Y software envelope is enabled at `$130=455.000` mm and
`$131=446.000` mm with `$20=$40=1` and hard limits disabled (`$21=0`);
controlled boundary-rejection testing remains open. G54 magnetic registration
and pen-loaded behavior remain open.
For guarded pen-free commissioning, the operator manually established a
temporary pen-corrected G54 X/Y reference from the center magnet on 2026-09-06;
the measured `sensor_to_pen` vector is `(0.000, -30.100)` mm. After the
guarded Y envelope changed the homed machine frame, that reference was
refreshed at `MPos:-232.900,-191.200`; the operator also chose a temporary G54
`A0` reference for a pen-free converter run, which returned exactly to its
references. This is not P100 or magnetic A registration and must be overwritten
before production drawing.
A dual-core toolhead implementation now exists at
[`pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`](pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino)
for integrated control of the DRV8833, HX711, TMAG5273, and M3/M5 command
input. Core 0 owns pressure/safety and Core 1 owns magnetic acquisition and the
two-phase readiness/scan handshake. HX711 acquisition is suspended while the
verified-lifted magnetic mode is active. With the PC817C module, GP29 M3/M5 and GP28 `HOME_ARM`
inputs are externally pulled HIGH and optocoupler assertions pull them LOW;
the integrated sketch is configured for that active-low interface. F-05/E-18
must still establish the RP23CNC ENA/Aux0 state mapping. Compile-time safety
gates deliberately prevent uncommissioned actuator and magnetic operation.
The separate normally-open `LIFT_HOME` microswitch is now installed from GP2
to local `TOOL_GND`; the integrated firmware configures it as an active-low
pull-up input and reports it through native USB and GP20/GP21 service UART.
The service interface uses Arduino-Pico `Serial2` (hardware UART1), and the
integrated firmware prints its service-UART-ready line before other
initialization. Its telemetry writer does not require a complete record to fit
in the UART FIFO, so GP20 telemetry is not silently suppressed.
T-01G must verify live transitions and guarded retract cycles before it
controls motor behavior.
Smaller Arduino sketches also exist for safer bring-up, including a GP2/GP20
LIFT_HOME UART-only diagnostic with no motor-related pin activity:
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
Use [`../docs/project/ROADMAP.md`](../docs/project/ROADMAP.md) for active
work, [`grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`](grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md)
for P100 design/commissioning, and
[`../docs/testing/TEST_PLAN.md`](../docs/testing/TEST_PLAN.md) for acceptance
conditions.
