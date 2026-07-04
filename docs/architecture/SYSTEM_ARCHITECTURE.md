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
| Motion controller | G-code parsing, modal state, lookahead, coordinated acceleration, step/direction generation, homing, limits | grblHAL on RP23CNC |
| Stepper power stage | Convert RP23CNC step/direction signals into motor phase current | Three external TB6600-class drivers |
| Toolhead controller | Lift/engage state machine, load-cell sampling, force regulation, actuator drive, fault handling | grblHAL plugin or separate MCU; decision pending bench validation |
| Magnetic homing adapter | Fixed-height magnetic sensing, setup diagnostics, and switch-like A home/index signal | RP2040 adapter reading TMAG5273 over Qwiic/I2C |
| Toolhead sensors | Pen force feedback | 300 g load cell + HX711 |

## Motion data path

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
       +<- X/Y home switches and RP2040 A_HOME
```

The project should extend grblHAL rather than duplicate its parser or planner.
The converter intentionally emits a small, documented G-code subset.

## Dual-core strategy

RP2350 is dual-core, but the split must follow the grblHAL RP2040/RP2350
driver's supported execution model. Do not move driver internals between cores
without first tracing and testing the upstream implementation.

### Baseline

- Let upstream grblHAL own parsing, planning, real-time commands, and step timing.
- Use the RP23CNC/grblHAL board map and plugins before adding custom multicore code.
- Measure planner starvation, step jitter, and sensor-loop timing before claiming a need for core separation.

### Preferred split if a supported core-1 extension is feasible

| Core/resource | Work |
|---|---|
| Core 0 | grblHAL protocol, parser, planner, machine state, alarms, homing, and command dispatch |
| PIO/DMA/interrupt hardware | Deterministic step pulse generation as provided by the upstream driver |
| Core 1 | Toolhead state machine, HX711 sampling, force-control calculation, and bounded telemetry |

Cross-core communication should use fixed-size single-producer/single-consumer
queues or atomics. It must not use blocking locks in the motion path.

Core 0 remains authoritative for machine alarm state. Either core may request a
toolhead shutdown, but the actuator must default to LIFT/OFF on reset, timeout,
or communication loss.

### Fallback

If grblHAL does not expose a maintainable core-1 integration point, put the
toolhead loop on a separate small MCU. This is preferable to a fragile fork of
the motion driver and gives the force loop independent fault containment.

## Toolhead control states

```text
BOOT -> LIFT -> SEEK_CONTACT -> HOLD_FORCE
          ^          |              |
          |          +-> FAULT <----+
          +--------------------------+
```

- `LIFT`: retract actuator; force loop disabled.
- `SEEK_CONTACT`: approach at limited duty/speed until force threshold.
- `HOLD_FORCE`: closed-loop force regulation.
- `FAULT`: motor disabled or commanded to safe retract, depending on verified mechanics.

M5 commands `LIFT`. M3 commands `SEEK_CONTACT`, then `HOLD_FORCE`.

## Homing and magnetic reference

Normal startup homing is owned by grblHAL: X/Y use physical home switches and A
uses the RP2040/TMAG5273 adapter's validated switch-like `A_HOME` signal. The
TMAG5273 is not a Z-axis sensor; it is installed at a fixed toolhead/gantry
height. Setup calibration scans the center and outer magnets to determine
thresholds, hysteresis, A offset, and repeatability. During normal startup, the
user should not have to coordinate a separate calibration script.

The grblHAL build may expose a Z axis slot to enable A in a four-axis
configuration, but Z is unused and unwired for this machine.

## Important constraints

- HX711 sample rate is limited and must be measured in the actual configuration before selecting PID bandwidth.
- DRV8833 suitability depends on measured actuator stall current and supply voltage.
- RP23CNC pin availability and voltage levels must be checked against its current user manual and schematic.
- The TB6600 listing is a marketplace product. Its actual input circuit, current calibration, and microstep table must be verified on the received units.
