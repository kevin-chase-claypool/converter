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
| `M3` | Toolhead ENGAGE: seek paper, then hold target force |
| `M5` | Toolhead PEN_CLEAR: release paper by load-cell threshold, then add a calibrated clearance pulse |
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

The initial ioSender screenshot from the 2026-09-05 rate-ramp session showed
`$103 = 250.000 step/deg`, but the operator corrected the setting to
`$103 = 4.44444`; the later `$$` report confirms the corrected value. M-04
then passed the one-motor-revolution check with `A360 F300` in both directions.
M-05 still must verify the 12:1 bed ratio before the system treats a full bed
rotation as validated. At `$113=5000` and `$123=10 deg/sec^2`, short A-axis
moves can be dominated by acceleration and deceleration rather than steady
speed.

The angular increment is uniform across the bed; tangential increment is
`radius × 0.00032725` in the same linear unit as the radius. At 9 in from the
center, one A pulse is about 0.00295 in (0.0748 mm). A planned two-bed-
revolution index search takes `120 / bed_RPM` seconds at constant speed: 24 s
at 5 RPM, 12 s at 10 RPM, or 6 s at 20 RPM, plus ramps and detection dwell.
Commission the actual scan rate through loaded A-axis M-01/M-02 testing.

Do not use ioSender's guided Stepper calibration page as the primary A-axis
calibration method unless its target and measured values are explicitly angular
motor degrees. The current A procedure is the mechanical calculation above,
followed by M-04 (`A360` for one motor revolution) and M-05 (`A4320` for one
bed revolution). The guided page is appropriate for measured linear X/Y/Z
steps-per-unit calibration; it does not tune `$113` maximum rate or `$123`
acceleration.

### X/Y TB6600 baseline

Both X and Y use GT2 belts (2 mm pitch) with confirmed 20-tooth motor pulleys.
The opposite 20-tooth belt pulley is an idler and does not change this ratio.
The initial settings are 16 microsteps (`SW1 OFF`, `SW2 OFF`, `SW3 ON`) and the
motor-rated 1.5 A/phase current row (`SW4 ON`, `SW5 OFF`, `SW6 ON`). With the
200-full-step motors, the initial grblHAL values are:

```text
X steps/mm ($100) = (200 * 16) / (2 mm * 20 teeth) = 80.000000
Y steps/mm ($101) = (200 * 16) / (2 mm * 20 teeth) = 80.000000
```

M-03 remains the physical travel calibration: use measured motion to correct
either value if belt compliance, pulley geometry, or actual travel differs.

## RP23CNC to stepper drivers

Each axis uses `STEP`, `DIR`, and common `ENABLE`. The final wiring table must be
copied from the exact RP23CNC revision and received driver labels.

Record the result in `docs/hardware/WIRING_TABLE.md` and mirror the final
controller pin assignments in `firmware/grblhal/config/pin-map.md`.

## Homing and magnetic bed calibration

Normal startup home and registration is a grblHAL/RP23CNC responsibility. The
eventual ioSender button sends `G65 P100 Q0`. P100 commands M5, homes X/Y from
physical switches, performs a serpentine center-magnet raster, calculates an
area centroid, registers G54 X0/Y0, then scans the outer magnet twice and
registers G54 A0. Every startup uses the full sequence; the physical switches
define machine bounds, not the actual bed center.

The TMAG and pen tip have a fixed CAD/measured XY separation. P100 owns that
transformation: it records `pen - TMAG` as a commissioning-gated offset and
sets G54 so `X0 Y0` means **pen at bed center**. The converter must not add the
same offset to plot coordinates.

The Pro Micro RP2350 reads the TMAG5273 and uses the existing GP28/GP27 pair for
a two-phase protocol. The first Aux0 assertion requests a GP27 readiness ACK;
Aux0 is released and the ACK must clear; the second assertion arms GP27 as the
thresholded magnetic probe state. Therefore one GP27 edge never means
"center." grblHAL records entry and exit coordinates and computes the result.

| Interface | Contract |
|---|---|
| X/Y limit switches -> RP23CNC | Physical home/limit references for grblHAL homing |
| TMAG5273 -> Pro Micro RP2350 | Qwiic/I2C 3D Hall readings at the fixed installed sensor height |
| Pro Micro RP2350 -> host PC | Service diagnostics only; host is not in the real-time centroid loop |
| RP23CNC Aux 0 -> PC817C U2 -> Pro Micro RP2350 `GP28` | Active-low two-phase readiness/scan arm |
| Pro Micro RP2350 `GP27` -> PC817C U3 -> candidate RP23CNC `PRB` | First-phase readiness ACK, then second-phase thresholded magnetic state |

The center bed magnet locates the geometric bed center after X/Y homing. The
outer bed magnet, nominally 8.9 in from center, provides the theta/A angular
index. The calibration routine should locate the geometric center of each
saturated or thresholded magnetic footprint from opposing edges; it should not
depend on an unsaturated peak.

Normal A registration records two entry/exit pairs separated by one bed
revolution, validates spacing near `4320` A motor degrees, and averages the
equivalent centers before setting G54 A0. Any inconsistent edge, sensor fault, motion alarm, or unknown
toolhead-lift state exits through the abort/fault handling path instead of
retrying automatically.

The current installed endpoint remains GP27/U3 -> RP23CNC `LIMA`. The
implemented candidate terminates that same routed return at `PRB` so
controller-resident G38 moves can capture entry and release coordinates.
That retermination is not yet authorized: F-08 must first prove direct `PRB`
polarity, X transition capture, coordinate reporting, and the installed XYZA
build's A-axis G38 behavior without motors connected, followed by an actual
GP27/U3 isolated-path test. Until then, do not reterminate the conductor or
change the normal `$H` contract.

Do not connect the Pro Micro output directly to an RP23CNC input until the
RP23CNC input polarity, voltage/current requirement, output driver, and
isolation behavior are verified in `docs/hardware/WIRING_TABLE.md`.

## grblHAL to toolhead

Minimum interface:

| Signal | Meaning | Fail-safe state |
|---|---|---|
| ENGAGE/PEN_CLEAR | grblHAL spindle/tool output pin state: M3 = engage, M5 = normal fast pen clear | PEN_CLEAR |
| TOOL_FAULT | Toolhead cannot safely draw | Active/fault |
| CONTACT_READY, optional | Contact force is stable | Not ready |

Version 1 may use only ENGAGE/PEN_CLEAR plus fixed `G4` delays. A later plugin may
feed-hold until `CONTACT_READY` or alarm on `TOOL_FAULT`.

`M5` is not the toolhead's absolute position-reference command. The planned
local `GP2` switch establishes `LIFT_HOME` only at boot, recovery, or an
explicit service action. Normal M5 uses the same load cell as M3, but detects
the no-contact release band and then applies a verified clearance pulse.

The planned P100 toolhead preflight is a separate commissioning-gated contract
for an installed pen, marker, or pencil: home; capture a no-contact baseline;
seek paper at limited force; perform normal M5 clear; and require a stable
clear result. Current `P100.macro` does not yet implement or wait for that
sequence, so it must not claim that tool changes are automatically validated.
No-contact force proves release, not an exact air gap; the per-tool clearance
pulse and target force require T-01J evidence.

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

The SparkFun Pro Micro RP2350 firmware assigns `GP0/GP1` to HX711,
`GP4/GP5/GP6/GP7` to DRV8833 control/fault, Qwiic `GPIO17/GPIO16` to TMAG5273,
`GP29` to the active-low M3/M5 input through PC817C U1, `GP27` to the
conditioned `A_HOME` output through PC817C U3's bench-verified direct/0 Ω
link, and
`GP28` to the active-low RP23CNC `Aux 0` `HOME_ARM` input through PC817C U2.
The module's local 10 kΩ pullups make an idle GP29/GP28 read HIGH and an
asserted optocoupler read LOW. The RP23CNC ENA/Aux0 state mapping remains
provisional until F-05/E-18 bench tests are complete. Core 0 owns pressure and
safety; Core 1 owns TMAG sampling and GP28/GP27 magnetic protocol. HX711
acquisition is suspended only while a verified-lifted magnetic scan is active.

This Pro Micro RP2350 is also the installed TMAG5273 reader and magnetic-output
owner. It is not paired with a separate RP2040 magnetic adapter.

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
