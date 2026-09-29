# System Architecture

This document defines the system boundaries. The level-1 systems below are cut
along integration seams, not along parts or technologies: each one has a single
responsibility, named interfaces, and a test that can prove it works before it
is integrated with its neighbours.

## System of interest (level 0)

An operator-driven XY gantry plus rotating-bed plotter that converts 2D vector
artwork into ink on a bed-mounted sheet.

External interfaces: the operator (artwork files, commands, calibration, stop);
the host PC (converter and ioSender); facility mains power; consumables (paper
and pen); and maintenance access (service UART, firmware flashing).

## Level-1 systems

The five mission-chain systems carry a drawing from file to ink. The three
cross-cutting systems enable all of them and are integrated through their own
seams.

### Mission chain

| # | System | Responsibility | Primary seams | Integration evidence |
|---|---|---|---|---|
| 1 | Host planning and operator | SVG parsing, geometry, XY+A kinematic planning, G-code generation, preview, machine settings, and the ioSender operator session | Operator to UI; G-code program and settings to system 2 | Converter output streams and executes; `M-06` pen-free run |
| 2 | Motion control | G-code parsing, modal state, lookahead, coordinated acceleration, step/direction generation, homing, limits | G-code contract from 1; STEP/DIR and enable to 3; X/Y home, E-stop, and PRB inputs from 5 and 7; M3/M5 and Aux0 to 4 | `F-02`, `F-03`; `M-07` X/Y homing; `M-06` coordinated X/Y/A |
| 3 | Motion and actuation | Convert step/direction signals into motor phase current and physical motion: X/Y gantry, A bed rotation, 12:1 pulley drive, transmission | Commanded pulses from 2; mechanism to 8 | `E-01`-`E-03`; `M-01`-`M-05` axis calibration and bed-ratio check |
| 4 | Toolhead and tool | Pen lift and force control, interchangeable tool mounting, M3/M5 behavior, faults local to the toolhead | M3/M5 and Aux0 from 2; GP27 status and service UART to 2 and the operator; sensor signals from 5 | `T-01`, `T-02`, `E-09F`; `F-05A` GP27/PRB completion |
| 5 | Sensing and feedback | Pen force, magnetic bed registration, X/Y home references, toolhead telemetry | Sensor signals to 2 and 4; registered G54 frame to 1 | `F-04`; `E-09C`; `E-18`/`P113` registration |

### Cross-cutting systems

| # | System | Responsibility | Primary seams | Integration evidence |
|---|---|---|---|---|
| 6 | Power and energy | Mains entry, protective earth, 12 V and 6 V/5 V rails, branch protection, grounding | Rail and PE interfaces to 2, 3, 4, 5, and 8 | `E-11`, `E-14`, `E-15` |
| 7 | Safety and fault handling | E-stop, limits, watchdogs, over-force relief, implausible-reading rejection, safe retract, operator notification | Binding stop and fault behavior on 1-6 and 8 | `E-19`; `F-04`; toolhead relief and fault runs |
| 8 | Structure, cabling, and EMC | Frame, gantry, rotating bed, enclosures, drag chain, strain relief, shielding, cable-wrap policy | Mechanical mounting; shield and PE lands; cable routing to 1-7 | Shielded-cable, sheath-isolation, and drag-chain records |

Components are not systems at this level. The TB6600 drivers and the belt and
pulley drive are inside system 3; the CS1238, TMAG5273, and home switches are
inside system 5. A level-1 boundary changes only when this document,
[`../integration/INTERFACES.md`](../integration/INTERFACES.md), the applicable
ADR, and a categorized change note are updated together.

### Worked cross-system tradeoff: bed rotation and cable wrap

The rotating bed makes the seams visible. System 1 chooses how much the bed
rotates while drawing (the r-theta resolver and `monotonic_theta` in
`software/converter_core/kinematics.py`); accumulated rotation becomes cable
wrapping owned by system 8; and system 7 bounds how much wrap is acceptable
before the machine must not move. A planner change that saves plot time by
increasing net winding is therefore also a mechanical and safety change, and it
is only accepted when all three systems are considered together.

## Physical realization view

The subsystem table below is retained as the physical view: it names the
concrete implementations that make up the level-1 systems above.

| Subsystem | Responsibility | Implementation |
|---|---|---|
| Host converter | SVG parsing, geometry, XY+A kinematic planning, G-code generation, preview | Python/PySide6 in `software/` |
| G-code sender / operator console | Streams the converter's saved G-code, exposes jog/status/console, and configures grblHAL | ioSender on the host PC, connected by USB or Ethernet |
| Motion controller | G-code parsing, modal state, lookahead, coordinated acceleration, step/direction generation, homing, limits | grblHAL on RP23CNC |
| Stepper power stage | Convert RP23CNC step/direction signals into motor phase current | Three external TB6600-class drivers |
| Toolhead controller | Dual-core lift/pressure safety plus fixed-height magnetic sensing and readiness/threshold output | SparkFun Pro Micro RP2350 reading CS1238 and TMAG5273 over Qwiic/I2C |
| Toolhead sensors | Pen force and magnetic reference feedback | 300 g load cell + CS1238; TMAG5273 3D Hall sensor |

## Primary controller reference

- RP23CNC hardware repository:
  [`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC)

Use this upstream repository for the current board documentation, schematics,
pin assignments, assembly information, and RP23CNC-specific firmware guidance.
Record the exact board revision used by this project before finalizing wiring.

## Motion data path

The current, scenario-by-scenario visual is
[`../system_data_flow.html`](../system_data_flow.html). It is the visual
companion to this architecture: its routed lanes show normal plotting, P100
registration, toolhead control, fault/recovery, and commissioning without
connector crossings. Interface details and verification status remain in their
authoritative documents.

[`SYSTEM_DATA_FLOW_RECORD.md`](SYSTEM_DATA_FLOW_RECORD.md) makes the visual a
controlled record: it defines comparison baselines, traceable authorities, and
the procedure for recording an inconsistency before changing the diagram.

```text
Host G-code stream
       |
       v
grblHAL parser -> planner/lookahead -> RP2350 driver/PIO/interrupts
       |                                  |
       |                                  +-> X/Y/A STEP + DIR
       |
       +-> M3/M5 spindle/tool output pin state
       |
       +<- X/Y home switches and candidate Pro Micro GP27 -> PRB state
```

The project should extend grblHAL rather than duplicate its parser or planner.
The converter intentionally emits a small, documented G-code subset.

## RP23CNC execution strategy

RP2350 is dual-core, but the split must follow the grblHAL RP2040/RP2350
driver's supported execution model. Do not move driver internals between cores
without first tracing and testing the upstream implementation.

### Baseline

- Let upstream grblHAL own parsing, planning, real-time commands, and step timing.
- Use the RP23CNC/grblHAL board map and plugins before adding custom multicore code.
- Measure planner starvation, step jitter, and sensor-loop timing before claiming a need for core separation.

The toolhead loop is already isolated on its own Pro Micro RP2350; do not move
it into an RP23CNC core or fork the motion driver.

## Toolhead RP2350 dual-core split

| Core | Work |
|---|---|
| Core 0 | GP29, pressure states, HX711, DRV8833, faults, USB diagnostics, watchdog |
| Core 1 | TMAG5273, GP28 two-phase arm, GP27 readiness/magnetic state |

The cores exchange fixed-size atomic status. Core 0 feeds the watchdog only
while Core 1 is fresh. Magnetic mode requires verified lift and suspends HX711
acquisition; any unsafe state suppresses the magnetic output.

## Toolhead control states

```text
BOOT -> LIFT_HOME -> PEN_CLEAR -> SEEK_CONTACT -> HOLD_FORCE
            ^             ^              |              |
            |             |              +-> FAULT <----+
            +-------------+------------------------------+
```

- `LIFT_HOME`: full retract to the planned GP2 switch reference, used at boot,
  recovery, and service only.
- `PEN_CLEAR`: normal M5 action; retract to the load-cell release threshold,
  add a calibrated clearance pulse, then pause the force loop.
- `SEEK_CONTACT`: approach at limited duty/speed until force threshold.
- `HOLD_FORCE`: closed-loop force regulation.
- `FAULT`: motor disabled or commanded to safe retract, depending on verified mechanics.

M5 commands `PEN_CLEAR`. M3 commands `SEEK_CONTACT`, then `HOLD_FORCE`.
The toolhead enters `LIFT_HOME` only for boot, recovery, or an explicit service
request; it is not used for every plotting stroke.

The toolhead is intended to accept interchangeable pens, markers, and pencils
without relying on one shared vertical pen-tip datum. Load-cell thresholds
determine pressing versus clear; the clearance pulse creates travel gap after
release. A planned P100 toolhead preflight must verify home, no-contact
baseline, limited-force contact seek, normal clear, and a stable clear result
for the installed tool before plotting. It cannot calculate an exact unloaded
tip-to-paper gap from a load-cell reading.

## Homing and magnetic reference

Normal startup is owned by grblHAL's P100 macro. X/Y physical switches establish
machine coordinates; a serpentine center-magnet raster registers G54 X0/Y0 and
a two-observation outer-magnet scan registers G54 A0. The Pro Micro supplies a
two-phase readiness acknowledgement and threshold state through existing
GP28/GP27 wiring. The TMAG5273 is not a Z-axis sensor, and no separate host
calibration process participates in the real-time sequence.

The grblHAL build may expose a Z axis slot to enable A in a four-axis
configuration, but Z is unused and unwired for this machine.

## Important constraints

- HX711 sample rate is limited and must be measured in the actual configuration before selecting PID bandwidth.
- DRV8833 suitability depends on measured actuator stall current and supply voltage.
- RP23CNC pin availability and voltage levels must be checked against its current user manual and schematic.
- The TB6600 listing is a marketplace product. Its actual input circuit, current calibration, and microstep table must be verified on the received units.
