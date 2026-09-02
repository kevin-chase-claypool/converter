# System Architecture

## Primary controller reference

- RP23CNC hardware repository:
  [`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC)

Use this upstream repository for the current board documentation, schematics,
pin assignments, assembly information, and RP23CNC-specific firmware guidance.
Record the exact board revision used by this project before finalizing wiring.

## Subsystems

| Subsystem | Responsibility | Implementation |
|---|---|---|
| Host converter | SVG parsing, geometry, XY+A kinematic planning, G-code generation, preview | Python/PySide6 in `software/` |
| G-code sender / operator console | Streams the converter's saved G-code, exposes jog/status/console, and configures grblHAL | ioSender on the host PC, connected by USB or Ethernet |
| Motion controller | G-code parsing, modal state, lookahead, coordinated acceleration, step/direction generation, homing, limits | grblHAL on RP23CNC |
| Stepper power stage | Convert RP23CNC step/direction signals into motor phase current | Three external TB6600-class drivers |
| Toolhead controller | Dual-core lift/pressure safety plus fixed-height magnetic sensing and readiness/threshold output | SparkFun Pro Micro RP2350 reading HX711 and TMAG5273 over Qwiic/I2C |
| Toolhead sensors | Pen force and magnetic reference feedback | 300 g load cell + HX711; TMAG5273 3D Hall sensor |

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
