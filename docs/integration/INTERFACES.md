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

The grblHAL build may expose a Z axis slot because the Web Builder uses a
four-axis configuration to enable A alongside X/Y. Z is unused for this machine:
do not wire a Z motor, do not home Z, and do not treat the TMAG5273 as a Z-axis
sensor.

The converter currently applies the 12:1 bed ratio. Therefore:

```text
A steps/degree = motor full-steps/rev * microsteps / 360
```

Do not multiply by 12 again in grblHAL. If this convention changes, update the
converter, firmware configuration, sample files, and this document together.

### A-axis TB6600 baseline

The observed drive ratio is 12 motor revolutions for one bed revolution. With
the 1.8 degree, 200-full-step NEMA 17 and the received TB6600's **8-microstep**
setting (`SW1 OFF`, `SW2 ON`, `SW3 OFF`), the initial configuration is:

| Quantity | Value |
|---|---:|
| Motor pulses/revolution | 1,600 |
| Motor steps per commanded A motor-degree | 4.444444 |
| Motor degrees per bed revolution | 4,320 |
| Pulses per bed revolution | 19,200 |
| Nominal bed angle per pulse | 0.01875 degrees |

Set the grblHAL A-axis steps-per-unit (`$103`, subject to the controller's
reported setting-number map) to **4.444444** because A commands use
motor-shaft degrees. Do not set it to 53.333333 steps per *bed* degree: that
would silently change the established host/controller contract. Eight
microsteps is the recommended starting point because the 12:1 reduction already
provides fine bed resolution; 16 or 32 microsteps would increase pulse demand
and reduce incremental torque without a demonstrated plotting benefit. M-04
and M-05 must still verify one motor revolution and one full bed revolution.

## RP23CNC to stepper drivers

Each axis uses `STEP`, `DIR`, and common `ENABLE`. The final wiring table must be
copied from the exact RP23CNC revision and received driver labels.

Record the result in `docs/hardware/WIRING_TABLE.md` and mirror the final
controller pin assignments in `firmware/grblhal/config/pin-map.md`.

## Homing and magnetic bed calibration

Normal startup homing remains a grblHAL/RP23CNC responsibility. ioSender sends
`M5`, waits for the toolhead lift dwell, then starts homing with `$H`.
grblHAL homes X/Y from physical home switches and homes A from a validated,
switch-like `A_HOME` signal generated from the TMAG5273 readings. In the current
toolhead prototype, the SparkFun Pro Micro RP2350 reads the TMAG5273 over Qwiic
and drives `GP27` as the intended final conditioned `A_HOME` output through the
selected switch-like interface after the threshold, hysteresis, polarity, and
RP23CNC input behavior are verified. `A_HOME` is gated by the Pro Micro `GP28`
`HOME_ARM` input so normal plotting does not assert the RP23CNC A limit/home
input when the bed magnet passes the sensor. `HOME_ARM` uses PC817C U2 with
RP23CNC `Aux 0` on the LED side and Pro Micro `GP28` on the phototransistor
side. U2 assertion pulls GP28 LOW against its local 3.3 V pullup. The intended
operator workflow is
`M64 P0`, `$H`, then `M65 P0`.
Setup and maintenance calibration are separate from normal startup homing and
are used to determine magnetic thresholds, hysteresis, offsets, and
repeatability before those constants are trusted.

| Interface | Contract |
|---|---|
| X/Y limit switches -> RP23CNC | Physical home/limit references for grblHAL homing |
| TMAG5273 -> Pro Micro RP2350 | Qwiic/I2C 3D Hall readings at the fixed installed sensor height |
| Pro Micro RP2350 -> host PC | USB serial diagnostics and magnetic readings during setup calibration scans |
| Host PC -> RP23CNC/grblHAL | Setup scan moves over USB or Ethernet while recording magnetic readings |
| RP23CNC Aux 0 -> PC817C U2 -> Pro Micro RP2350 `GP28` | Active-low isolated `HOME_ARM` input that allows `GP27` `A_HOME` to assert only during homing |
| Pro Micro RP2350 -> RP23CNC | Validated conditioned digital `A_HOME` signal for grblHAL A/theta homing |

The center bed magnet locates the geometric bed center after X/Y homing. The
outer bed magnet, nominally 8.9 in from center, provides the theta/A angular
index. The calibration routine should locate the geometric center of each
saturated or thresholded magnetic footprint from opposing edges; it should not
depend on an unsaturated peak.

Normal A homing scans two full bed revolutions, or `8640` A motor degrees with
the current 12:1 convention, records two entry/exit pairs, validates agreement,
and averages the two computed centers before setting or reporting the A
reference. Any inconsistent edge, sensor fault, motion alarm, or unknown
toolhead-lift state exits through the abort/fault handling path instead of
retrying automatically.

Do not connect the Pro Micro output directly to an RP23CNC input until the
RP23CNC input polarity, voltage/current requirement, output driver, and
isolation behavior are verified in `docs/hardware/WIRING_TABLE.md`.

## grblHAL to toolhead

Minimum interface:

| Signal | Meaning | Fail-safe state |
|---|---|---|
| ENGAGE/LIFT | grblHAL spindle/tool output pin state: M3 = engage, M5 = lift | LIFT |
| TOOL_FAULT | Toolhead cannot safely draw | Active/fault |
| CONTACT_READY, optional | Contact force is stable | Not ready |

Version 1 may use only ENGAGE/LIFT plus fixed `G4` delays. A later plugin may
feed-hold until `CONTACT_READY` or alarm on `TOOL_FAULT`.

## Toolhead internal interfaces

Power boundary:

| Rail | Owner | Contract |
|---|---|---|
| 6 V toolhead rail | DIN-mounted Pololu D36V50F6 | Feeds the drag-chain toolhead power pair and DRV8833 motor supply after E-14/E-15 verification |
| 5 V toolhead logic | Toolhead-mounted Pololu S7V8F5 | Generated locally from the 6 V rail for the SparkFun Pro Micro RP2350 logic input |
| 3.3 V sensor rail | SparkFun Pro Micro RP2350 | Powers HX711 and TMAG5273/Qwiic so signal levels remain RP2350-safe |

| Connection | Purpose |
|---|---|
| HX711 `DOUT/SCK` | Load-cell sample acquisition |
| DRV8833 `IN1/IN2` or phase/enable | Bidirectional DC motor command |
| DRV8833 `EEP`/sleep enable | Explicit motor-driver enable under toolhead firmware control |
| DRV8833 `ULT`/fault | Optional driver fault input to the toolhead controller |
| TMAG5273 Qwiic `SDA/SCL` | Position/reference magnetic sensor readings |

The prototype SparkFun Pro Micro RP2350 firmware assigns `GP0/GP1` to HX711,
`GP4/GP5/GP6/GP7` to DRV8833 control/fault, Qwiic `GPIO17/GPIO16` to TMAG5273,
`GP29` to the active-low M3/M5 input through PC817C U1, `GP27` to the
conditioned `A_HOME` output through PC817C U3's bench-verified direct/0 Ω
link, and
`GP28` to the active-low RP23CNC `Aux 0` `HOME_ARM` input through PC817C U2.
The module's local 10 kΩ pullups make an idle GP29/GP28 read HIGH and an
asserted optocoupler read LOW. The RP23CNC ENA/Aux0 state mapping remains
provisional until F-05/E-18 bench tests are complete.

## Safety invariants

- SW1 NC-A asserts the RP23CNC E-stop/Halt input. NC-B is individually
  insulated and unused. E-stop does not remove motor/tool 12 V; the main power
  switch is the deliberate full-power shutdown. SW1 release does not authorize
  motion.
- Reset, watchdog expiry, or invalid state commands LIFT/OFF.
- No contact found before the seek timeout causes FAULT.
- Force above the hard limit causes immediate retract or motor disable.
- Toolhead processing may never block step generation or real-time stop handling.
- Homing and E-stop behavior must be tested without a pen installed first.
