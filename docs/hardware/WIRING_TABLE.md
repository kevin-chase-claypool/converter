# Master Wiring Table

This is the authoritative wiring record for the machine. Update it whenever a
part, pin assignment, connector, voltage, wire color, or test result changes.

The visual diagrams in `docs/full_wiring_diagram.html`,
`docs/electronics_layout_and_wiring.html`,
`../rp23cnc-pro-micro-interface-schematic.png`, and
`../power-distribution-schematic.png` are explanatory only. The current
power-distribution narrative is in [`POWER_DISTRIBUTION.md`](POWER_DISTRIBUTION.md).
If any diagram or narrative disagrees with this table, this table controls.

Selected controller: Brookwood Design RP23CNC / RP23U5XBB V1.01 variant
`48493912129751`, **With Assembly and Ethernet Kits**. Connectors and Ethernet
components must be soldered and inspected before wiring. Front and back
photographs confirm the PCB revision and visible connector population; E-17
magnified inspection and continuity checks remain required.

## Status definitions

| Status | Meaning |
|---|---|
| `TBD` | Proposed or not yet assigned; do not connect |
| `documented` | Supported by a manufacturer schematic/manual but not checked on this machine |
| `continuity-checked` | Wiring has been checked unpowered with a meter |
| `bench-verified` | Connection has passed a powered subsystem test |
| `machine-verified` | Connection has passed an integrated machine test |
| `rejected` | Connection was tested or reviewed and must not be used |

## Update rules

1. Give every physical conductor a stable connection ID.
2. Never replace an uncertain value with a guess. Leave it `TBD`.
3. Record terminal labels exactly as printed on the received hardware.
4. Add wire color and gauge only after the physical wire is selected.
5. Promote status only when the evidence column identifies a manual, photo, meter check, or test ID.
6. Update the revision log after every wiring change.
7. Re-run affected tests in `docs/testing/TEST_PLAN.md` after changing a powered connection.

## Power distribution

For the current power-only schematic and branch-level explanation, see
[`POWER_DISTRIBUTION.md`](POWER_DISTRIBUTION.md).

### MEISHILE S-120-12 terminal map

Terminal numbering is left-to-right when facing the seven-position terminal
block as reported from the received unit.

| Terminal | Marking | Function | Verification status | Evidence/notes |
|---:|---|---|---|---|
| 1 | `L` | AC line/live input | documented | Physical unit observation; QR-linked manual archived in `references/` |
| 2 | `N` | AC neutral input | documented | Physical unit observation |
| 3 | Protective-earth symbol | Protective earth/chassis safety ground | documented | Physical unit observation; continuity to chassis must be tested before power |
| 4 | `-V` | DC output negative | documented | One of two parallel negative output terminals |
| 5 | `-V` | DC output negative | documented | One of two parallel negative output terminals |
| 6 | `+V` | DC output positive | documented | One of two parallel positive output terminals |
| 7 | `+V` | DC output positive | documented | One of two parallel positive output terminals |
| Adjacent to 7 | `+V ADJ` | Output-voltage adjustment screw | documented | Measure with no load before connecting electronics; adjustment is not a current control |

| ID | From device | From terminal | To device | To terminal | Signal/rail | Expected level | Wire | Protection | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|---|
| PWR-001 | AC mains | Hot | MEISHILE S-120-12 | Terminal 1 `L` | AC line/live | 100-240 VAC listing range | Red, verified | Enclosure, switch, line fuse, strain relief TBD | verified — terminal identity only | Owner verified red is landed at the printed `L` terminal. Enclosure/protection and powered checks remain open. |
| PWR-001N | AC mains | Neutral | MEISHILE S-120-12 | Terminal 2 `N` | AC neutral | 100-240 VAC listing range | Blue, verified | Same protected inlet as PWR-001 | verified — terminal identity only | Owner verified blue is landed at the printed `N` terminal. Keep neutral distinct from protective earth. |
| PWR-001E | Protective earth | PE | MEISHILE S-120-12 | Terminal 3 earth | Protective earth | Safety bonding conductor | Green, verified | X cable shield/drain landed here; supply PE/chassis path passed | verified — terminal identity/landing/PE path | Owner verified the green wall-earth conductor and green X sheath/drain are landed at the protective-earth symbol terminal, and the PE terminal-to-supply-chassis path passes. The powder-coated machine structure is not used as the protective-earth reference. This is never `-V`, `L`, or `N`. |
| PWR-002 | HCDC HD064RT | `OUT1` fused pair | RP23CNC | Main power input TBD | Controller/control-input supply | 12 VDC nominal, always on during E-stop | TBD | `OUT1`/FCTRL, 2 A selected; confirm fitted marking | planned | Owner allocated RP23CNC to `OUT1`. Controller remains powered when SW1 is pressed; final terminal allocation and E-19/current measurement remain required. |
| PWR-003 | HCDC HD064RT | `OUT6 +` | X TB6600 | `VCC`/`DC+` TBD | X stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | `OUT6` branch fuse, 2 A selected; confirm fitted marking | planned — wired, unverified | Owner reports the positive conductor is physically landed from `OUT6`; confirm exact driver terminal, polarity, fuse marking, and continuity before power. Do not bypass the HD064RT branch fuse. |
| PWR-004 | HCDC HD064RT | `OUT6 -` | X TB6600 | `GND`/`DC-` TBD | X stepper return | 0 VDC | TBD | Paired with PWR-003 | planned — wired, unverified | Owner reports the return conductor is physically landed; confirm exact driver terminal and continuity with power removed. |
| PWR-005 | HCDC HD064RT | `OUT7 +` | Y TB6600 | `VCC`/`DC+` TBD | Y stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | `OUT7` branch fuse, 2 A selected; confirm fitted marking | planned — wired, unverified | Owner reports the positive conductor is physically landed from `OUT7`; confirm exact driver terminal, polarity, fuse marking, and continuity before power. Do not bypass the HD064RT branch fuse. |
| PWR-006 | HCDC HD064RT | `OUT7 -` | Y TB6600 | `GND`/`DC-` TBD | Y stepper return | 0 VDC | TBD | Paired with PWR-005 | planned — wired, unverified | Owner reports the return conductor is physically landed; confirm exact driver terminal and continuity with power removed. |
| PWR-007 | HCDC HD064RT | `OUT8 +` | A TB6600 | `VCC`/`DC+` TBD | A stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | `OUT8` branch fuse, 2 A selected; confirm fitted marking | planned — wired, unverified | Owner reports the positive conductor is physically landed from `OUT8`; confirm exact driver terminal, polarity, fuse marking, and continuity before power. Do not bypass the HD064RT branch fuse. |
| PWR-008 | HCDC HD064RT | `OUT8 -` | A TB6600 | `GND`/`DC-` TBD | A stepper return | 0 VDC | TBD | Paired with PWR-007 | planned — wired, unverified | Owner reports the return conductor is physically landed; confirm exact driver terminal and continuity with power removed. |
| PWR-009A | HCDC HD064RT | `OUT4 +` | Pololu D36V50F6 | `VIN` | Toolhead 6 V regulator input | 12 VDC nominal; E-stop does not remove this power; regulator accepts 6.5-50 V input | TBD | `OUT4` branch fuse, 3 A intended; confirm fitted marking | planned | Pololu item 4092 selected; owner allocated it to `OUT4`. |
| PWR-009B | HCDC HD064RT | `OUT4 -` | Pololu D36V50F6 | `GND` | Toolhead 6 V regulator return | 0 VDC | TBD | Paired with PWR-009A | planned | DC return remains continuous. |
| PWR-009 | Pololu D36V50F6 | `VOUT` via 2-pin toolhead JST | DRV8833 | `VCC`/`VM` TBD | Actuator motor power | Fixed 6.0 V output | 20 AWG red/black twisted pair TBD | Output fuse/capacitance TBD | bench-verified | The local JST-to-DRV8833 path delivered 6 V from a bench supply on 2026-08-12. This verifies the toolhead wiring only; the D36V50F6-to-JST harness remains untested. |
| PWR-010 | Pololu D36V50F6 | `GND` via 2-pin toolhead JST | DRV8833 | `GND` TBD | Actuator return | 0 V | 20 AWG black return in the same twisted pair TBD | Same branch as PWR-009 | bench-verified | Continuity passed and the DRV8833 received the correct bench-powered rail. Do not use the JST as a logic-only connector: this ground is the driver power return and local logic reference. |
| PWR-011A | Toolhead 6 V input at 2-pin JST | Pololu S7V8F5 | `VIN` | Toolhead logic-regulator input | 6.0 V nominal from local toolhead motor rail | Short local conductor on shared perfboard | Local input capacitance TBD | bench-verified | The local JST-to-S7V8F5 input path delivered 6 V from a bench supply on 2026-08-12. Motor-current-dip behavior remains E-15A. |
| PWR-011B | Toolhead 6 V input return at 2-pin JST | Pololu S7V8F5 | `GND` | Toolhead logic-regulator return | 0 V common reference | Short local conductor on shared perfboard | Same branch as PWR-011A | bench-verified | Power-ground continuity passed. Common ground is required for DRV8833 control and sensors; it must not be tied to PC817 `CTRL_GND`. |
| PWR-011 | Pololu S7V8F5 | `VOUT` | SparkFun Pro Micro RP2350 | `RAW`/`5V` | Toolhead controller power | Regulated 5.0 V; do not feed 6 V directly to `RAW`/`5V` | Short local conductor | bench-verified | Continuity passed and the Pro Micro received the correct multimeter-verified voltage from the S7V8F5 with a 6 V bench input on 2026-08-12. Exact readings and loaded behavior remain to be recorded in E-15A. |
| PWR-012 | Pololu S7V8F5 | `GND` | SparkFun Pro Micro RP2350 | `GND` | Toolhead controller return | 0 V common reference | Short local conductor | bench-verified | Power-ground continuity passed; toolhead power test completed with the Pro Micro powered. Tie to the local DRV8833/HX711/TMAG return node only. |
| PWR-013 | SparkFun Pro Micro RP2350 | `3V3`/Qwiic | HX711 | `VCC` | HX711 power | 3.3 V so `DT` remains RP2350-safe | Short local conductor TBD | Local decoupling TBD | TBD | Verify HX711 module operates acceptably at 3.3 V in E-07/E-08 |
| PWR-014 | SparkFun Pro Micro RP2350 | `GND` | HX711 | `GND` | HX711 return | 0 V | Short local conductor TBD | Same reference as PWR-013 | TBD | Keep HX711 close to load cell |
| PWR-015 | SparkFun Pro Micro RP2350 | Qwiic `3V3/GND` | TMAG5273 Qwiic | Qwiic `3V3/GND` | Hall sensor power | 3.3 V Qwiic | Qwiic cable TBD | Qwiic pullups on controller side | documented | SparkFun documents Pro Micro RP2350 Qwiic on GPIO16/17 with 3.3 V pullups |

## Motion control signals

The supplied TB6600 schematic defines the planned common-cathode pattern:
each RP23CNC axis `G` is jumpered to its TB6600 `PUL-`, `DIR-`, and `ENA-`;
`Stp`, `Dir`, and `En` go to `PUL+`, `DIR+`, and `ENA+`. This is documented,
not yet powered-driver verified: E-03 must prove the installed inputs behave
correctly before mechanics are attached. Compare every terminal with received
hardware silkscreen before wiring.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| MOT-001 | RP23CNC | X `Stp` | X TB6600 | `PUL+` | X step pulse | 5 V pulse activity during commanded motion | Twisted pair TBD | documented — controller side passed | F-03; supplied schematic establishes endpoint; E-03 remains installed-driver verification. |
| MOT-002 | RP23CNC | X `Dir` | X TB6600 | `DIR+` | X direction | 0 V positive, 5 V negative direction | Twisted pair TBD | documented — controller side passed | F-03; E-03 remains required. |
| MOT-003 | RP23CNC | X `En` | X TB6600 | `ENA+` | X enable | Active-low: 5 V idle, 0 V moving | Twisted pair TBD | documented — controller side passed | F-03; E-03 remains required. |
| MOT-004 | RP23CNC | Y `Stp` / `Dir` / `En` | Y TB6600 | `PUL+` / `DIR+` / `ENA+` | Y step, direction, enable | Same F-03 logic as X | Twisted pair TBD | documented — controller side passed | Supplied schematic; E-03 remains required. |
| MOT-005 | RP23CNC | A `Stp` / `Dir` / `En` | A TB6600 | `PUL+` / `DIR+` / `ENA+` | A step, direction, enable | Same F-03 logic as X | Twisted pair TBD | documented — controller side passed | Supplied schematic; E-03 remains required. |
| MOT-006 | RP23CNC | X `G` | X TB6600 | `PUL-`, `DIR-`, `ENA-` via common block | X signal return | Axis-local common reference | Three jumpers/common block TBD | documented | Do not use isolated-input ground; E-03 remains required. |
| MOT-007 | RP23CNC | Y `G` | Y TB6600 | `PUL-`, `DIR-`, `ENA-` via common block | Y signal return | Axis-local common reference | Three jumpers/common block TBD | documented | Do not use isolated-input ground; E-03 remains required. |
| MOT-008 | RP23CNC | A `G` | A TB6600 | `PUL-`, `DIR-`, `ENA-` via common block | A signal return | Axis-local common reference | Three jumpers/common block TBD | documented | Do not use isolated-input ground; E-03 remains required. |

## Stepper motor phases

Manufacturer colors are documented, but each motor must still pass continuity
test E-01 before connection. An unpowered hand-turn generated-voltage test on
2026-08-19 identified black/green as one coil and red/blue as the other. The
current cable plan uses that same color pairing on the unshielded Y and A runs.

Only the X motor cable has a grounded shield/sheath. Its shield/drain bonds to
PE/chassis at the TB6600/DIN-rail end only and is cut back and insulated at the
motor end. Do not connect that shield/drain to DC `-V`, motor phase terminals,
or RP23CNC signal ground. The X shielded run uses black/green for Phase A and
red/white for Phase B (white continues the motor's blue B- lead). Y and A use
unshielded four-wire motor leads, with black/green as one coil and red/blue as
the other.

| ID | From device | From terminal | To device | To terminal | Signal | Wire color | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|
| XPH-001 | X TB6600 | `A+` | X motor | A+ lead | Phase A+ | Planned shielded motor run; black lead | partial | Owner hand-turn generated-voltage test, 2026-08-19: black/green is one coil; retain lead order pending M-01 direction check and shielded-run installation. |
| XPH-002 | X TB6600 | `A-` | X motor | A- lead | Phase A- | Planned shielded motor run; green lead | partial | Owner hand-turn generated-voltage test, 2026-08-19: black/green is one coil. |
| XPH-003 | X TB6600 | `B+` | X motor | B+ lead | Phase B+ | Planned shielded motor run; red -> motor red | partial | Owner correction, 2026-08-23: X `B+` is red; retain lead order pending M-01 direction check and shielded-run installation. |
| XPH-004 | X TB6600 | `B-` | X motor | B- lead | Phase B- | Planned shielded motor run; white -> motor blue | partial | Owner correction, 2026-08-23: X `B-` is white; white is the cable-side continuation of the motor's blue B- lead. |
| XSH-001 | X motor cable shield/drain | Green sheath/drain wire at TB6600 end | MEISHILE S-120-12 protective-earth terminal | Earth symbol / PE | Cable shield bond | Green, verified | verified — PE path and isolation passed | Owner verified this wire is landed at the same protective-earth terminal as the wall's earth conductor; the PE terminal-to-supply-chassis path passes and the sheath has no continuity to DC `-V` or any motor-phase conductor. Keep the shield insulated at the motor end. |
| YPH-001 | Y TB6600 | `A+` | Y motor | A+ lead | Phase A+ | Unshielded motor lead black | continuity-checked | Owner report, 2026-08-23: black/green is one coil; final driver direction remains M-01/M-03. |
| YPH-002 | Y TB6600 | `A-` | Y motor | A- lead | Phase A- | Unshielded motor lead green | continuity-checked | Owner report, 2026-08-23: black/green is one coil. |
| YPH-003 | Y TB6600 | `B+` | Y motor | B+ lead | Phase B+ | Unshielded motor lead red | continuity-checked | Owner report, 2026-08-23: red/blue is one coil; final driver direction remains M-01/M-03. |
| YPH-004 | Y TB6600 | `B-` | Y motor | B- lead | Phase B- | Unshielded motor lead blue | continuity-checked | Owner report, 2026-08-23: red/blue is one coil. |
| APH-001 | A TB6600 | `A+` | A motor | A+ lead | Phase A+ | Supplied unshielded 24 AWG motor lead black | continuity-checked | Owner hand-turn generated-voltage test, 2026-08-19: black/green is one coil; retain lead order pending M-01 direction check. |
| APH-002 | A TB6600 | `A-` | A motor | A- lead | Phase A- | Supplied unshielded 24 AWG motor lead green | continuity-checked | Owner hand-turn generated-voltage test, 2026-08-19: black/green is one coil. |
| APH-003 | A TB6600 | `B+` | A motor | B+ lead | Phase B+ | Supplied unshielded 24 AWG motor lead red | continuity-checked | Owner hand-turn generated-voltage test, 2026-08-19: red/blue is one coil; retain lead order pending M-01 direction check. |
| APH-004 | A TB6600 | `B-` | A motor | B- lead | Phase B- | Supplied unshielded 24 AWG motor lead blue | continuity-checked | Owner hand-turn generated-voltage test, 2026-08-19: red/blue is one coil. |

## Limits, controls, and safety

| ID | From device | From terminal | To device | To terminal | Signal | Expected behavior | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| SAF-001 | X HiLetgo KW12-3 limit switch | `COM` (yellow) and `NC` (green) | RP23CNC | `LIM X`: `SIG` and `GND` | X home/limit | NC released/healthy, opens when tripped or wire breaks; X is inactive released and reports active only while pressed with `$5=0` | Two-conductor limit lead | partial — wired and live-report tested | `COM` to `SIG`; `NC` to `GND`. Owner meter-verified COM–NC continuity with lever released and open circuit pressed. ioSender live indicator changed only for X while its switch was pressed (2026-08-22). Hard-limit alarm test remains open. |
| SAF-002 | Y HiLetgo KW12-3 limit switch | `COM` (yellow) and `NC` (green) | RP23CNC | `LIM Y`: `SIG` and `GND` | Y home/limit | NC released/healthy, opens when tripped or wire breaks; Y is inactive released and reports active only while pressed with `$5=0` | Two-conductor limit lead | partial — wired and live-report tested | `COM` to `SIG`; `NC` to `GND`. Owner meter-verified COM–NC continuity with lever released and open circuit pressed. ioSender live indicator changed only for Y while its switch was pressed (2026-08-22). Hard-limit alarm test remains open. |
| SAF-003 | A index sensor | TBD | RP23CNC | A limit/probe input TBD | Bed index/home | Polarity TBD | Shielded/twisted TBD | TBD | Sensor selection pending |
| SAF-004 | SW1 mxuteuk `HB2-BS544` E-stop, NC-A | Contact pair A | RP23CNC | Opto-isolated E-stop/Halt terminal pair TBD | Immediate grblHAL Halt | NC released/healthy, open when pressed; use NC input configuration (planned `$14=6`, verify live) | Low-current protected control wire TBD | planned | Initial manual-supported E-stop. RP23CNC stays powered; verify in E-19. |
| SAF-005 | SW1 mxuteuk `HB2-BS544` E-stop, NC-B | Contact pair B | None | Both terminals individually insulated | Unused | No electrical connection | None | planned | K1 is not part of this project. |
| SAF-006 | MEISHILE `S-120-12` | `+V` through FMAIN | HCDC `HD064RT` | `DC INPUT +` | 12 V motor/tool feed | 12 V while the main power is on; E-stop does not remove this power | Protected 12 V positive TBD | partial | On 2026-08-20, the powered HD064RT input and one output pair each measured 12.05 VDC and polarity matched the block markings. On 2026-08-21, the mains-input and DC-output conductors were rerouted not to overlap. FMAIN maximum 10 A; do not bypass it. PE bonding, adjustment range, fitted fuse, and loaded behavior remain open; see E-11 lab note. |
| SAF-007 | HCDC `HD064RT` | `OUT6` / fused pair | X TB6600 | 12 V input | X motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | 2 A selected; confirm fitted marking/current before power |
| SAF-008 | HCDC `HD064RT` | `OUT7` / fused pair | Y TB6600 | 12 V input | Y motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | 2 A selected; confirm fitted marking/current before power |
| SAF-009 | HCDC `HD064RT` | `OUT8` / fused pair | A TB6600 | 12 V input | A motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | 2 A selected; confirm fitted marking/current before power |
| SAF-010 | HCDC `HD064RT` | `OUT4` / fused pair | Pololu D36V50F6 | `VIN/GND` | Toolhead motor supply source | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | Owner intends 3 A; confirm fitted marking and characterize E-15 |
| SAF-011 | HCDC `HD064RT` | `OUT1` / fused pair | RP23CNC | 12 V main input TBD | Controller/control-input supply | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | 2 A selected; confirm fitted marking, terminal labels, and E-19 behavior before power |

## Magnetic bed registration interface

The implemented magnetic registration candidate uses the toolhead SparkFun
Pro Micro RP2350 as the TMAG5273 reader because the TMAG5273 is wired to the
toolhead Qwiic connector. The same Pro Micro also owns the HX711/DRV8833
pen-pressure controller; there is no separate RP2040 magnetic adapter. The Pro
Micro drives `GP27` as the conditioned readiness/magnetic-state return through an
open-drain, transistor, optocoupler, or equivalent switch-like interface. `GP27`
uses a two-phase `GP28` handshake: GP27 first acknowledges readiness, clears,
then represents thresholded field during the second arm. Therefore one edge is
never interpreted as the computed center, and the bed magnet cannot trip the A
limit/home input during normal printing. RP23CNC V1.0 schematic page 4 shows
the `LIMA` input as an active-low, switch-to-`GND1` 12 V input with a 2 kΩ
series resistor and internal input optocoupler LED. Its nominal asserted
current is about 5.3 mA. A bench test of the installed U3 sample with a 12 V,
2.2 kΩ simulated controller load measured about 12 V idle and 0.2 V asserted.
That validates this sample at the tested load but does not improve the generic
PC817C's 50%-minimum-CTR guarantee. The current tested assembly may use a
direct wire or a 0 Ω R6 link between `A_HOME` and `A_HOME_SW`; repeat the load
test if U3 is replaced. U3 has the Pro Micro on its LED side and the RP23CNC
`LIMA` input on its phototransistor side.

The current circuit is the all-through-hole, minimum-wire KiCad design
[`../../hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_pcb`](../../hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_pcb),
with the exact perfboard build map
[`../../hardware/pc817-interface/PERFBOARD_BUILD.md`](../../hardware/pc817-interface/PERFBOARD_BUILD.md)
and matching schematic
[`../../hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_sch`](../../hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_sch).
The 40.16 × 22.65 mm board uses PC817C DIP-4 parts, axial DO-35 1N4148 clamps,
¼ W axial resistors, radial capacitors, two generic six-pin 2.54 mm screw
terminals, and short insulated point-to-point links. Connector pins are
channel-aligned; J1.3 and J2.5 are NC.
U1/U2 use the RP23CNC logic output as a low-side sink with an independent
controller `+5V` LED feed. On the Pro Micro side, R3/R4 pull GP29/GP28 to local
`3V3` and an on PC817 pulls its GPIO LOW; firmware therefore treats LOW as
asserted. The reverse `GP27` channel uses the tested `R6`/direct A_HOME link;
repeat the 12 V / 2.2 kΩ load test if U3 is replaced.

`PRB` is the implemented but test-gated candidate endpoint for the existing
GP27/U3 return, not the current wiring assignment. F-08 first tests the controller's probe
input and G38 behavior with TB6600 signal leads and motors disconnected. Keep
MAG-003 and the routed harness on `LIMA` until F-08 proves X transition capture,
the installed build's A-axis behavior, coordinate reporting, and the subsequent
GP27/U3 path test. The RP23CNC and grblHAL documentation establish the component
probe functions but do not explicitly certify the complete TMAG raster/A-index
application.

| ID | From device | From terminal | To device | To terminal | Signal | Expected behavior | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| MAG-001 | SparkFun TMAG5273 Qwiic | Qwiic `SDA/SCL/3V3/GND` | SparkFun Pro Micro RP2350 | Qwiic `GPIO16/GPIO17/3V3/GND` | 3D Hall readings | 3.3 V I2C; stable magnetic vector or magnitude readings | Qwiic cable TBD | bench-verified | E-09 passed after correcting the signal pair: GP16 is SDA and GP17 is SCL. Far/near/return magnitudes were 0.24/7.51/7.44 mT; initial threshold guidance 3.5 mT with 1.0 mT hysteresis. |
| MAG-002 | SparkFun Pro Micro RP2350 | USB device TBD | Host PC | USB TBD | Service telemetry | Reports pressure state, magnetic state/vector, and faults for commissioning; it does not send numeric centroids to RP23CNC | USB cable TBD | source implemented; installed test TBD | P100 owns position capture and centroid arithmetic. |
| MAG-003 | SparkFun Pro Micro RP2350 | `GP27` through PC817C U3 | RP23CNC | Installed `LIMA`; candidate `PRB` after F-08 | Phase 1 readiness ACK; phase 2 thresholded magnetic state | Isolated switch-like return; never drive a controller input high | Existing routed control conductor | harness re-test and F-08 required | No new drag-chain wire. Retermination is controller-end only and prohibited until direct PRB and GP27/U3 stages pass. |
| MAG-003A | RP23CNC | `Aux 0` digital output | PC817C module U2 LED cathode | `AUX0` / pin 2 | Two-phase magnetic arm | First `M64 P0` requests readiness ACK; `M65 P0` clears it; second `M64 P0` enters scan state; final `M65 P0` disarms | Existing routed control conductor | source implemented; controller mapping pending | U2 assertion pulls GP28 low. Toolhead must be commissioned, lifted, safe, and TMAG-ready before ACK. |
| MAG-003B | PC817C module U2 collector | `GP28` / pullup node | SparkFun Pro Micro RP2350 | `GP28` / A2 | Isolated two-phase arm input | Local 3.3 V pullup through `R4`; U2 on pulls GP28 low | Existing routed control conductor | harness re-test required | Core 1 owns the handshake; unsafe state or timeout suppresses GP27. |
| MAG-004 | Center bed magnet | Embedded bed center | TMAG5273 scan path | Sensor over bed | Bed-center reference | Saturated or thresholded footprint centered on bed rotation axis | Mechanical placement | TBD | Cylindrical magnet; diameter, grade, polarity, and depth TBD |
| MAG-005 | Outer bed magnet | Embedded near 8.9 in radius | TMAG5273 scan path | Sensor over bed | Theta/A index reference | Saturated or thresholded footprint centered on angular index mark | Mechanical placement | TBD | Cylindrical magnet; final measured radius and angular reference TBD |

## Toolhead control and sensors

Toolhead prototype controller is the SparkFun Pro Micro RP2350 mounted with the
toolhead electronics. Pin choices below are prototype firmware assignments and
must pass bench tests before being treated as final machine wiring.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| TH-001A | RP23CNC | Spindle group `ENA` | PC817C module U1 LED cathode | `ENA` / pin 2 | M3/M5 command into isolation module | U1 LED on only when ENA sinks current from controller `+5V` through `R1`; M3/M5 behavior and fail-safe LIFT remain polarity-test dependent | Shielded/twisted TBD | TBD | See `hardware/pc817-interface/pc817-interface.sch`; RP23U5XBB manual identifies spindle `ENA`; verify voltage, polarity, and current before connection; test F-05 |
| TH-001A-RT | RP23CNC | `5V`, spindle `ENA`, `Aux 0`, control `GND`, and `LIMA` | Toolhead PC817C module J1.1, J1.2, J1.4, J1.5, and J1.6 respectively | Controller-side moving harness | Isolated tool command, `HOME_ARM`, and reverse `A_HOME` path | Controller and toolhead ground domains remain galvanically isolated; endpoint behavior remains test-gated | Five routed control conductors through drag chain | partially terminated, unverified | On 2026-08-23, owner reported and supplied an image showing J1.1 `CTRL_5V`, J1.2 `ENA`, J1.4 `AUX0`, and J1.5 `CTRL_GND` wired at the RP23CNC. J1.6 `A_HOME` remains disconnected; `PRB` remains a candidate only. No continuity, isolation, polarity/current, or energized test is claimed. J1.3 remains unused. |
| TH-001B | PC817C module U1 collector | `GP29` / pullup node | SparkFun Pro Micro RP2350 | `GP29` / A3 | M3/M5 isolated output to Pro Micro | Local 3.3 V pullup through `R3`; U1 on pulls GP29 low | Shielded/twisted TBD | harness re-test required | U1 passed the simulated test on prior GP8 wiring; repeat it on GP29. Actual RP23CNC ENA behavior remains F-05. |
| TH-002 | SparkFun Pro Micro RP2350 | `GP4` | DRV8833 | `IN1` | Motor direction/PWM | 3.3 V logic PWM | Short local conductor | continuity-checked | Continuity passed 2026-08-12; powered direction/PWM behavior remains T-01. Module label may read `AIN1` on other DRV8833 boards. |
| TH-003 | SparkFun Pro Micro RP2350 | `GP5` | DRV8833 | `IN2` | Motor direction/PWM | 3.3 V logic PWM | Short local conductor | continuity-checked | Continuity passed 2026-08-12; powered direction/PWM behavior remains T-01. Module label may read `AIN2` on other DRV8833 boards. |
| TH-003A | DRV8833 | `EEP` / protection-fault output | SparkFun Pro Micro RP2350 | `GP6` | Driver fault input | Treat as open-drain-style fault until module behavior is bench-proven; firmware uses a pullup | Short local conductor | continuity-checked | Exact ACEIRMC B08RMWTDLM mapping: installed `EEP`→GP6 wire passed continuity. |
| TH-003B | SparkFun Pro Micro RP2350 | `GP7` | DRV8833 | `ULT` / sleep input | Driver enable/sleep | Drive high to enable driver | Short local conductor | continuity-checked | Exact ACEIRMC B08RMWTDLM mapping: installed GP7→`ULT` wire passed continuity. Inspect J2 bridge and complete E-14C before relying on software sleep control. |
| TH-003C | SparkFun Pro Micro RP2350 | `GP4`, `GP5`, `GP6`, `GP7` | DRV8833 | logic connector | One 1×4 direct-header harness | Consecutive left-side GPIO run; GND is supplied by the separate DRV8833 power connector | Short local harness | continuity-checked | GP4/GP5/GP6/GP7 logic wires passed continuity. Firmware maps GP7 to `ULT` and GP6 to `EEP`; E-14C remains the function check before T-01. |
| TH-003D | SparkFun Pro Micro RP2350 | `GND`, `RST` NC, `3V3`, `GP29`, `GP28`, `GP27` | PC817C module | J2.4, NC, J2.2, J2.1, J2.3, J2.6 | One 1×6 direct-header harness | Consecutive right-side Pro Micro run; `RST` remains unconnected and `CTRL_GND` is excluded | 1×6 JST-compatible harness | continuity-checked | All currently wired Pro Micro logic pins passed continuity 2026-08-12. `RST` remains intentionally unconnected; repeat functional E-18 testing after repinning. |
| TH-004 | DRV8833 | `OUT1` | N20 actuator | Motor lead 1 | Actuator drive | First E-05 pulse retracts/lifts the pen | Existing temporary motor pair; final 22 AWG red/black twisted pair pending | Local bulk capacitance at driver | direction verified | E-05 now runs reliably after repair of one intermittent DRV8833 output-pin solder joint. Record no-load current before integrated operation. |
| TH-005 | DRV8833 | `OUT2` | N20 actuator | Motor lead 2 | Actuator drive | Second E-05 pulse moves the pen down | Existing temporary motor pair; final 22 AWG red/black twisted pair pending | Local bulk capacitance at driver | direction verified | E-05 now runs reliably after repair of one intermittent DRV8833 output-pin solder joint. Record no-load current before integrated operation. |
| TH-006 | uxcell 300 g load cell | Red (`EXC+`) | HX711 | `E+` | Bridge excitation positive | Manufacturer wire/function mapping | Short local conductor TBD | documented | Load cell is between fixed gantry and the gray actuator/pen-guide block. The blue piece holds the pen, which slides through the gray block; the linear rail guides the moving assembly. E-07 must calibrate against pen-tip force and quantify guide/screw friction and hysteresis. Red `EXC+`, Black `EXC-`, Green `SEN+`, White `SEN-`; verify connector labels and E-07 before use. |
| TH-007 | uxcell 300 g load cell | Black (`EXC-`) | HX711 | `E-` | Bridge excitation negative | Manufacturer wire/function mapping | Short local conductor TBD | documented | Same manufacturer mapping; verify connector labels and E-07 before use |
| TH-008 | uxcell 300 g load cell | Green (`SEN+`) | HX711 | `A+` | Bridge signal positive | Manufacturer wire/function mapping | Short local conductor TBD | documented | Same manufacturer mapping; calibrate in E-07 |
| TH-009 | uxcell 300 g load cell | White (`SEN-`) | HX711 | `A-` | Bridge signal negative | Manufacturer wire/function mapping | Short local conductor TBD | documented | Same manufacturer mapping; calibrate in E-07 |
| TH-010 | HX711 | `DOUT`/`DT` | SparkFun Pro Micro RP2350 | `GP0` | Load-cell data | 3.3 V logic when HX711 is powered from RP2350 `3V3` | Short local conductor | continuity-checked | Continuity passed 2026-08-12. Reassigned to the adjacent left-side *signal* pair; `3V3` remains a separate local power branch; tests E-07/E-08. |
| TH-011 | SparkFun Pro Micro RP2350 | `GP1` | HX711 | `SCK` | Load-cell clock | 3.3 V logic | Short local conductor | continuity-checked | Continuity passed 2026-08-12. Reassigned to the adjacent left-side *signal* pair; `3V3` remains a separate local power branch; tests E-07/E-08. |
| TH-012 | SparkFun Pro Micro RP2350 | Qwiic `SDA` / `GPIO16` | TMAG5273 Qwiic | SDA | Hall sensor data | 3.3 V I2C | Qwiic cable TBD | bench-verified | Corrected E-09 mapping GP16→SDA passed the TMAG5273 identity and far/near/return test. |
| TH-013 | SparkFun Pro Micro RP2350 | Qwiic `SCL` / `GPIO17` | TMAG5273 Qwiic | SCL | Hall sensor clock | 3.3 V I2C | Qwiic cable TBD | bench-verified | Corrected E-09 mapping GP17→SCL passed the TMAG5273 identity and far/near/return test. |
| TH-018 | LIFT-home microswitch | Terminals `1` and `3` | SparkFun Pro Micro RP2350 | `GP2` and `TOOL_GND` | Absolute `LIFT_HOME` reference at boot/recovery/service, not normal M5 | `GP2` uses its internal pullup; switch pressed pulls `GP2` LOW | Short local pair TBD | planned | Owner identified terminals `1` and `3` as the intended COM/NO dry-contact pair. The contact has no electrical polarity: either terminal may connect to `GP2`, the other to `TOOL_GND`; leave the NC terminal unused. Mount the switch fixed and its flag on the moving pen carriage. Do not connect 5 V, 6 V, or PC817C `CTRL_GND`. T-01G must pass before firmware relies on this input. Normal M5 uses load-cell release plus a calibrated clearance pulse and must not routinely actuate this switch. |
| TH-014 | Toolhead controller | FAULT output TBD | RP23CNC | Feed hold/halt input TBD | Tool fault | Fail-safe polarity TBD | TBD | TBD | Later integration phase |
| TH-015 | Toolhead controller | READY output TBD | RP23CNC | Auxiliary input TBD | Contact ready | Optional; polarity TBD | TBD | TBD | Later handshake upgrade |
| TH-016 | SparkFun Pro Micro RP2350 | `GP20` / UART1 TX | DSD TECH SH-U09C2 USB-to-TTL service adapter | `RXD` | Toolhead test telemetry | 3.3 V UART, 115200 baud; adapter receives Pro Micro output | Short temporary jumper | bench-verified | E-07B UART startup telemetry passed 2026-08-14. Cross TX to adapter RXD; set adapter jumper to 3.3 V. Adapter VCC remains disconnected; this attaches only to `TOOL_GND`, never PC817C `CTRL_GND`. |
| TH-017 | DSD TECH SH-U09C2 USB-to-TTL service adapter | `TXD` | SparkFun Pro Micro RP2350 | `GP21` / UART1 RX | Toolhead test commands | 3.3 V UART, 115200 baud | Short temporary jumper | bench-verified | E-07B UART command path ready; telemetry startup passed 2026-08-14. Cross adapter TXD to Pro Micro RX; adapter GND must connect to `TOOL_GND`; adapter VCC remains disconnected. |

## Communications

| ID | From device | From terminal | To device | To terminal | Signal | Cable | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|
| COM-001 | Host PC | USB TBD | RP23CNC | USB-C | G-code/control | USB data cable TBD | TBD | Baseline transport candidate |
| COM-002 | Host/network | Ethernet | RP23CNC WizNet module | Ethernet | G-code/WebUI/network | Cat5e or better | TBD | Optional adapter/build configuration |
| COM-003 | microSD card | Card contacts | RP23CNC | microSD socket | Offline G-code | microSD | TBD | Optional transport candidate |

## Revision log

| Date | Revision | Change | Updated by | Related evidence |
|---|---:|---|---|---|
| 2026-08-30 | 4.3 | Added planned toolhead LIFT-home microswitch input on `GP2`/`TOOL_GND`; terminals `1` and `3` are the intended COM/NO pair. | Codex | Owner terminal identification; T-01G planned |
| 2026-08-22 | 3.5 | Documented the implemented dual-core readiness/threshold protocol and controller-resident centroid/A-registration macro. Reused all five routed control conductors; retained `LIMA` until F-08 authorizes controller-end retermination to `PRB`. | Codex | `RPSW-20260822-003`; source compile and macro validator only |
| 2026-08-22 | 3.4 | Corrected stale separate-RP2040-adapter language: the installed SparkFun Pro Micro RP2350 toolhead controller owns both pen-pressure control and TMAG5273 magnetic sensing/output. No wiring changed. | Codex | `RPSW-20260822-002`; current GP27/GP28/GP29 wiring rows |
| 2026-08-22 | 3.3 | Added motorless F-08 as the gate for the candidate GP27/U3-to-`PRB` probe path; retained `LIMA` as the authoritative endpoint until X/A G38 behavior, coordinate reporting, and the actual isolated path pass. | Codex | `RPSW-20260822-001`; F-08 planned |
| 2026-08-21 | 3.2 | Recorded physical segregation of the mains-input and DC-output conductor routes at the main-supply/fuse-block area. | Codex | Owner report; `HW-20260821-001` |
| 2026-08-20 | 3.1 | Recorded a partial E-11 no-load power-path check: the HD064RT input and one output pair measured 12.05 VDC, with polarity matching the block markings. | Codex | `2026-08-20-e-11-main-supply-no-load-path-test.md` |
| 2026-08-19 | 3.0 | Recorded the actual HD064RT output allocation: RP23CNC on OUT1, Pololu D36V50F6 on OUT4, and X/Y/A TB6600s on OUT6/OUT7/OUT8; OUT2/OUT3/OUT5 are unused. Recorded selected branch-fuse starting values pending physical confirmation. | Codex | Project-owner allocation report; `HW-20260819-004` |
| 2026-08-23 | 3.6 | Superseded the prior shield assignment: only X now has the grounded motor-cable sheath; Y and A are unshielded, with black/green and red/blue coil pairs. | Codex | Project-owner note; `HW-20260823-002` |
| 2026-08-23 | 3.7 | Corrected the X shielded-run Phase B colors: `B+` is red and `B-` is white, with white continuing the motor's blue B- lead. | Codex | Project-owner correction; `HW-20260823-003` |
| 2026-08-23 | 3.8 | Recorded the owner-reported mains color convention: red `L`, blue `N`, and green PE; the green X sheath/drain is landed at PE. | Codex | Project-owner report; `HW-20260823-004` |
| 2026-08-23 | 3.9 | Verified the red/blue/green mains terminal identities and the green X sheath landing at the protective-earth terminal. PE/chassis continuity and powered tests remain open. | Codex | Project-owner verification; `HW-20260823-005` |
| 2026-08-23 | 4.0 | Verified the X sheath has no continuity to DC `-V`; PE/chassis and motor-phase isolation remain open. | Codex | Project-owner measurement; `HW-20260823-006` |
| 2026-08-23 | 4.1 | Verified the power-supply PE terminal-to-chassis path; the powder-coated machine structure is not the PE reference. | Codex | Project-owner measurement; `HW-20260823-007` |
| 2026-08-23 | 4.2 | Verified the X sheath has no continuity to any motor-phase conductor; its PE bond and DC `-V` isolation are complete. | Codex | Project-owner measurement; `HW-20260823-008` |
| 2026-08-19 | 2.9 | Corrected motor-cable installation: only Y has a shield/drain; X and A retain their supplied unshielded 24 AWG leads. Removed the nonexistent X/A shield-bond rows. | Codex | Superseded by `HW-20260823-002`. |
| 2026-08-19 | 2.8 | Recorded E-01 hand-turn coil-pair results for all three 17HS15 motors: black/green and red/blue. The Y axis has the special shielded-cable splice: cable black/green continues motor black/green, while cable red/white continues motor red/blue. | Codex | Owner hand-turn generated-voltage test; `2026-08-19-e-01-y-stepper-coil-pair-test.md` |
| 2026-08-13 | 2.7 | Reconciled the continuity-checked ACEIRMC DRV8833 harness with its exact labels without solder rework: GP7 drives `ULT` sleep and GP6 reads `EEP` protection/fault. Firmware now matches the installed harness. E-14C still checks the J2 bridge and live behavior before motor testing. | Codex | Owner bench report; Amazon ASIN B08RMWTDLM; E-14C required |
| 2026-08-12 | 1.4 | Recorded manufacturer-confirmed uxcell load-cell mapping: Red `EXC+` to HX711 `E+`, Black `EXC-` to `E-`, Green `SEN+` to `A+`, White `SEN-` to `A-` | Codex | Owner-supplied product specification; E-07 still required |
| 2026-08-10 | 2.5 | Reassigned PC817 tool-side pins to direct-header GP29/GP28/GP27 and recorded separate 1×4 DRV8833 plus 1×6 PC817 JST harnesses; reset is intentionally NC | Codex | `PRO_MICRO_JST_HARNESS.md`; E-18 harness re-test required |
| 2026-08-10 | 2.4 | Completed simulated-input tests for U1/U2/U3 and confirmed controller/tool ground isolation; removed the rebuild-only R6 gate for the tested U3 sample | Codex | `2026-08-10-e-18-pc817-interface-bench-test.md`; F-05 remains required |
| 2026-08-10 | 2.3 | Replaced the invalid recovered route with the 38-segment minimum-wire v2 design, changed unavailable GP10 to exposed GPIO20, and recorded the U1/U3 bench evidence | Codex | `pc817-perfboard-v2-minwire.kicad_pcb`; E-18 lab note; DRC/ERC reports |
| 2026-08-06 | 2.1 | Replaced the two five-pin headers with one six-pin 2.54 mm screw terminal on each short side; pin 6 is intentionally NC/spare on both blocks | Codex | `pc817-perfboard-v1.2.kicad_pcb`; F-05/E-18 remain required |
| 2026-08-09 | 2.2 | Verified RP23CNC V1.0 `LIMA` as a 12 V active-low sink input; blocked the generic-PC817C U3/A_HOME connection because its 50% guaranteed CTR cannot guarantee the approximately 5.3 mA controller input current | Codex | RP23CNC `Schematic/V1.0 schematic.pdf`, page 4; BOJACK PC817C listing / BOM |
| 2026-08-06 | 2.0 | Superseded the unrouted SMD PCB placement with an all-through-hole 14 × 6 perfboard component/underside-wire map and matching KiCad THT assembly view | Codex | `PERFBOARD_BUILD.md`; `pc817-perfboard-v1.1.kicad_pcb`; F-05/E-18 remain required |
| 2026-08-06 | 1.9 | Corrected the PC817 U1/U2 firmware contract to active-low GP8/GP10, changed the inputs to use the module's external 10 kΩ pullups, and added a separately named unrouted two-layer PCB review placement | Codex | `pc817-interface-v0.2.kicad_pcb`; F-05/E-18 remain required |
| 2026-08-06 | 1.8 | Replaced the proposed JST-GH PCB concept with a KiCad PC817C perfboard schematic using axial parts and 2.54 mm right-angle headers; rejected the B07WFGTNQC as an unverified RP2350 3.3 V interface | Codex | `hardware/pc817-interface/pc817-interface.sch`; E-18 remains required |
| 2026-08-06 | 1.7 | Added proposed 40.16 × 22.65 mm three-channel PC817C module layout with 90° JST GH connectors; retained B07WFGTNQC as the selected interface and R6/A_HOME verification gate | Codex | `pc817-three-channel-module-proposal.png`; E-18 remains required |
| 2026-08-03 | 1.6 | Added B07WFGTNQC optocoupler module wiring for RP23CNC-to-Pro-Micro `M3/M5` and `HOME_ARM` command inputs while leaving reverse `A_HOME` path as a separate verification item | Codex | `power-distribution-schematic.png`; Amazon B07WFGTNQC listing |
| 2026-08-03 | 1.5 | Added dedicated power-distribution document and PNG/SVG schematic showing the active D36V50F6 6 V rail, toolhead S7V8F5 5 V regulator, 12 V branch loads, and remaining fuse/terminal/wire-gauge TBDs | Codex | `docs/hardware/POWER_DISTRIBUTION.md`; `power-distribution-schematic.png` |
| 2026-08-03 | 1.4 | Added explanatory RP23CNC-to-Pro-Micro interface schematic PNG/SVG for the HiLetgo logic-level shifter and Zopsc A_HOME optocoupler paths while keeping exact RP23CNC terminals and common points unverified | Codex | `rp23cnc-pro-micro-interface-schematic.png` |
| 2026-08-02 | 1.3 | Added purchased KWANGIL 20 AWG 4C AMESB shielded stepper cable, conductor assignment guidance, and one-end shield/drain bonding rows for X/Y/A motor cables | Codex | Project-owner purchase note; Amazon listing for KWANGIL B0GVBF51Q7 |
| 2026-08-02 | 1.2 | Added purchased Pololu S7V8F5 local 5 V toolhead regulator, selected Pololu D36V50F6 as the DIN-side fixed 6 V toolhead regulator, and clarified that the toolhead Pro Micro reads TMAG5273 and outputs `GP9` `A_HOME` gated by RP23CNC `Aux 0` -> `GP10` `HOME_ARM` through a 5 V-to-3.3 V interface | Codex | Project-owner purchase note; Pololu S7V8F5 and D36V50F6 product pages; `toolhead-wiring-diagram.svg` |
| 2026-07-31 | 1.1 | Added SparkFun Pro Micro RP2350 toolhead prototype pin choices for DRV8833, HX711, TMAG5273, and M3/M5 input while retaining bench-test status | Codex | `toolhead-wiring-diagram.svg` |
| 2026-07-04 | 1.0 | Added an explanatory electronics layout and wiring concept HTML while retaining this table as the authority for terminal labels, connection status, and evidence | Codex | `docs/electronics_layout_and_wiring.html` |
| 2026-07-04 | 0.9 | Added planned TMAG5273/RP2040 magnetic bed calibration adapter, center magnet, outer theta-index magnet, and gated A_HOME interface placeholders | Codex | `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md` |
| 2026-06-09 | 0.8 | Confirmed received controller as RP23U5XBB V1.01 from front silkscreen; recorded visible connector and Wiz850io socket installation while retaining E-17 inspection and continuity gates | Codex | `docs/report/lab-notes/2026-06-09-rp23u5xbb-v1.01-board-inspection.md` |
| 2026-06-06 | 0.7 | Identified purchased RP23CNC variant as With Assembly and Ethernet Kits; added required soldering and inspection gate before pin assignment or power | Codex | Brookwood Design variant 48493912129751 |
| 2026-06-06 | 0.6 | Replaced the fixed 5 V actuator candidate with purchased B085T73CSD adjustable modules; target output is 6.0 V and the claimed 5 A maximum remains subject to load/thermal testing | Codex | Amazon listing and tests E-14/E-15 |
| 2026-06-06 | 0.5 | Added B0F1WB3LJ5 fixed 5 V buck as a toolhead bench-test candidate; final acceptance depends on measured actuator current, ripple, and temperature | Codex | Amazon listing and tests E-06/E-14 |
| 2026-06-06 | 0.4 | Corrected received model to S-120-12; documented terminals 1-7 and +V ADJ from the physical unit; split AC line, neutral, and protective-earth conductors; archived QR-linked PDF | Codex | Owner inspection and `references/MEISHILE-S-120-12-manual.pdf` |
| 2026-06-06 | 0.3 | Added internally consistent same-ASIN reseller details: reported model SE-1500-12, 50/60 Hz, approximate size/weight, protection claims, and no included connectors. Rejected contradictory 30 A/360 W text as unrelated listing contamination. | Codex | Ubuy product page supplied by project owner |
| 2026-06-06 | 0.2 | Added selected MEISHILE B0781ZJ7GP 12 V, 10 A, 120 W supply and updated proposed 12 V distribution | Codex | Amazon listing supplied by project owner |
| 2026-06-06 | 0.1 | Created master table from current BOM, interface contract, and conceptual diagram; all unverified terminals retained as TBD | Codex | Repository organization phase |
