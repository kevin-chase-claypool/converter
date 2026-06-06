# Integration Interfaces

Logical contracts live here. Exact terminals, conductors, wire colors, voltage
domains, and verification status live in the authoritative
[`../hardware/WIRING_TABLE.md`](../hardware/WIRING_TABLE.md).

## Host to grblHAL

Transport is not yet fixed. Candidate transports are USB serial, Ethernet, and
SD card.

The converter emits:

| Command | Contract |
|---|---|
| `G21` | Millimeters |
| `G90` | Absolute positioning |
| `G0 X Y A F` | Pen-up travel |
| `G1 X Y A F` | Pen-down coordinated move |
| `M3` | Toolhead ENGAGE |
| `M5` | Toolhead LIFT |
| `G4 P...` | Fixed toolhead settling delay |
| `M2` | Program end |

Unknown or unsupported commands must cause an explicit error during test, not
silent motion.

## Axis and unit convention

| Axis | Physical meaning | G-code unit |
|---|---|---|
| X | Gantry X | mm |
| Y | Gantry Y | mm |
| A | Rotating-bed motor shaft | degrees |

The converter currently applies the 12:1 bed ratio. Therefore:

```text
A steps/degree = motor full-steps/rev * microsteps / 360
```

Do not multiply by 12 again in grblHAL. If this convention changes, update the
converter, firmware configuration, sample files, and this document together.

## RP23CNC to stepper drivers

Each axis uses `STEP`, `DIR`, and common `ENABLE`. The final wiring table must be
copied from the exact RP23CNC revision and received driver labels.

Record the result in `docs/hardware/WIRING_TABLE.md` and mirror the final
controller pin assignments in `firmware/grblhal/config/pin-map.md`.

## grblHAL to toolhead

Minimum interface:

| Signal | Meaning | Fail-safe state |
|---|---|---|
| ENGAGE/LIFT | M3 = engage, M5 = lift | LIFT |
| TOOL_FAULT | Toolhead cannot safely draw | Active/fault |
| CONTACT_READY, optional | Contact force is stable | Not ready |

Version 1 may use only ENGAGE/LIFT plus fixed `G4` delays. A later plugin may
feed-hold until `CONTACT_READY` or alarm on `TOOL_FAULT`.

## Toolhead internal interfaces

| Connection | Purpose |
|---|---|
| HX711 `DOUT/SCK` | Load-cell sample acquisition |
| TMAG5273 I2C/Qwiic | Tool/actuator position or reference sensing |
| DRV8833 `IN1/IN2` or phase/enable | Bidirectional DC motor command |

The exact controller pins, update rates, and electrical levels remain TBD until
the RP23CNC pin audit and benchtop component tests are complete.

## Safety invariants

- Reset, watchdog expiry, or invalid state commands LIFT/OFF.
- No contact found before the seek timeout causes FAULT.
- Force above the hard limit causes immediate retract or motor disable.
- Toolhead processing may never block step generation or real-time stop handling.
- Homing and E-stop behavior must be tested without a pen installed first.
