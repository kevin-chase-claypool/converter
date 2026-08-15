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
| PWR-001 | AC mains | Hot | MEISHILE S-120-12 | Terminal 1 `L` | AC line/live | 100-240 VAC listing range | Mains-rated TBD | Enclosure, switch, line fuse, strain relief TBD | documented | Do not energize until enclosure and protection design are complete |
| PWR-001N | AC mains | Neutral | MEISHILE S-120-12 | Terminal 2 `N` | AC neutral | 100-240 VAC listing range | Mains-rated TBD | Same protected inlet as PWR-001 | documented | Keep neutral distinct from protective earth |
| PWR-001E | Protective earth | PE | MEISHILE S-120-12 | Terminal 3 earth | Protective earth | Safety bonding conductor | Green/yellow, gauge TBD | Bonding hardware TBD | documented | Verify low-resistance chassis continuity before power |
| PWR-002 | FMAIN protected 12 V bus | Through FCTRL (value TBD) | RP23CNC | Main power input TBD | Controller/control-input supply | 12 VDC nominal, always on during E-stop | TBD | FCTRL after FMAIN | planned | Controller remains powered when SW1 is pressed; final terminal allocation and fuse value require E-19/current measurement |
| PWR-003 | HCDC HD064RT | `OUT1 +` | X TB6600 | `VCC`/`DC+` TBD | X stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | HD064RT branch fuse, factory 3 A provisional | planned | Fed from the protected 12 V bus; do not bypass the HD064RT branch fuse. |
| PWR-004 | HCDC HD064RT | `OUT1 -` | X TB6600 | `GND`/`DC-` TBD | X stepper return | 0 VDC | TBD | Paired with PWR-003 | planned | DC return remains continuous. |
| PWR-005 | HCDC HD064RT | `OUT2 +` | Y TB6600 | `VCC`/`DC+` TBD | Y stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | HD064RT branch fuse, factory 3 A provisional | planned | Fed from the protected 12 V bus; do not bypass the HD064RT branch fuse. |
| PWR-006 | HCDC HD064RT | `OUT2 -` | Y TB6600 | `GND`/`DC-` TBD | Y stepper return | 0 VDC | TBD | Paired with PWR-005 | planned | DC return remains continuous. |
| PWR-007 | HCDC HD064RT | `OUT3 +` | A TB6600 | `VCC`/`DC+` TBD | A stepper power | 12 VDC nominal; E-stop does not remove this power | TBD | HD064RT branch fuse, factory 3 A provisional | planned | Fed from the protected 12 V bus; do not bypass the HD064RT branch fuse. |
| PWR-008 | HCDC HD064RT | `OUT3 -` | A TB6600 | `GND`/`DC-` TBD | A stepper return | 0 VDC | TBD | Paired with PWR-007 | planned | DC return remains continuous. |
| PWR-009A | HCDC HD064RT | `OUT4 +` | Pololu D36V50F6 | `VIN` | Toolhead 6 V regulator input | 12 VDC nominal; E-stop does not remove this power; regulator accepts 6.5-50 V input | TBD | HD064RT branch fuse, factory 3 A provisional | planned | Pololu item 4092 selected; fed from the protected 12 V bus. |
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

The RP23CNC terminal names and TB6600 common-anode/common-cathode wiring remain
TBD until the exact board revision and received driver input circuits are
verified. Do not use the conceptual HTML diagram as proof of polarity.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| MOT-001 | RP23CNC | X output group `STEP` | X TB6600 | `PUL+` or `PUL-` TBD | X step pulse | 5 V pulse activity observed only during commanded motion; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: 0 V idle, about 50 mV DC-meter average during move; test E-03 input polarity before final wiring |
| MOT-002 | RP23CNC | X output group `DIR` | X TB6600 | `DIR+` or `DIR-` TBD | X direction | 0 V positive direction, 5 V negative direction; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: held direction level; test E-03 before final wiring |
| MOT-003 | RP23CNC | X output group `EN` | X TB6600 | `ENA+` or `ENA-` TBD | X enable | Active-low: 5 V idle, 0 V while moving; final TB6600 topology TBD | Twisted pair TBD | controller side passed | F-03; test E-03 before final wiring |
| MOT-004 | RP23CNC | Y output group `STEP` | Y TB6600 | `PUL+` or `PUL-` TBD | Y step pulse | 5 V pulse activity observed only during commanded motion; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: 0 V idle, about 50 mV DC-meter average during move; test E-03 input polarity before final wiring |
| MOT-005 | RP23CNC | Y output group `DIR` | Y TB6600 | `DIR+` or `DIR-` TBD | Y direction | 0 V positive direction, 5 V negative direction; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: held direction level; test E-03 before final wiring |
| MOT-006 | RP23CNC | Y output group `EN` | Y TB6600 | `ENA+` or `ENA-` TBD | Y enable | Active-low: 5 V idle, 0 V while moving; final TB6600 topology TBD | Twisted pair TBD | controller side passed | F-03; test E-03 before final wiring |
| MOT-007 | RP23CNC | A output group `STEP` | A TB6600 | `PUL+` or `PUL-` TBD | A step pulse | 5 V pulse activity observed only during commanded motion; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: 0 V idle, about 50 mV DC-meter average during move; test E-03 input polarity before final wiring |
| MOT-008 | RP23CNC | A output group `DIR` | A TB6600 | `DIR+` or `DIR-` TBD | A direction | 0 V positive direction, 5 V negative direction; final TB6600 polarity/topology TBD | Twisted pair TBD | controller side passed | F-03: held direction level; test E-03 before final wiring |
| MOT-009 | RP23CNC | A output group `EN` | A TB6600 | `ENA+` or `ENA-` TBD | A enable | Active-low: 5 V idle, 0 V while moving; final TB6600 topology TBD | Twisted pair TBD | controller side passed | F-03; test E-03 before final wiring |

## Stepper motor phases

Manufacturer colors are documented, but each motor must still pass continuity
test E-01 before connection.

Selected replacement stepper cable is KWANGIL 20 AWG 4C AMESB shielded cable
with an overall shield, drain wire, and tinned-copper braid. Use one 4-conductor
cable per NEMA17 motor. Assign the four internal conductors to `A+`, `A-`, `B+`,
and `B-` only. Bond the shield/drain to PE/chassis at the TB6600/DIN-rail end
only; cut back and insulate the shield at the motor end. Do not connect the
shield/drain to DC `-V`, motor phase terminals, or RP23CNC signal ground.

| ID | From device | From terminal | To device | To terminal | Signal | Wire color | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|
| XPH-001 | X TB6600 | `A+` | X motor | A+ lead | Phase A+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead black | documented | 17HS15-1504S-X1 manufacturer listing; confirm with E-01 before splicing |
| XPH-002 | X TB6600 | `A-` | X motor | A- lead | Phase A- | KWANGIL 20 AWG 4C conductor TBD; original motor lead green | documented | Confirm with E-01 before splicing |
| XPH-003 | X TB6600 | `B+` | X motor | B+ lead | Phase B+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead red | documented | Confirm with E-01 before splicing |
| XPH-004 | X TB6600 | `B-` | X motor | B- lead | Phase B- | KWANGIL 20 AWG 4C conductor TBD; original motor lead blue | documented | Confirm with E-01 before splicing |
| XSH-001 | X motor cable shield/drain | Drain wire at TB6600 end | DIN rail PE/chassis terminal | PE/chassis TBD | Cable shield bond | Bare/tinned drain | TBD | Bond at driver/DIN end only; insulate shield at motor end; verify continuity to PE and isolation from DC `-V` |
| YPH-001 | Y TB6600 | `A+` | Y motor | A+ lead | Phase A+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead black | documented | Confirm with E-01 before splicing |
| YPH-002 | Y TB6600 | `A-` | Y motor | A- lead | Phase A- | KWANGIL 20 AWG 4C conductor TBD; original motor lead green | documented | Confirm with E-01 before splicing |
| YPH-003 | Y TB6600 | `B+` | Y motor | B+ lead | Phase B+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead red | documented | Confirm with E-01 before splicing |
| YPH-004 | Y TB6600 | `B-` | Y motor | B- lead | Phase B- | KWANGIL 20 AWG 4C conductor TBD; original motor lead blue | documented | Confirm with E-01 before splicing |
| YSH-001 | Y motor cable shield/drain | Drain wire at TB6600 end | DIN rail PE/chassis terminal | PE/chassis TBD | Cable shield bond | Bare/tinned drain | TBD | Bond at driver/DIN end only; insulate shield at motor end; verify continuity to PE and isolation from DC `-V` |
| APH-001 | A TB6600 | `A+` | A motor | A+ lead | Phase A+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead black | documented | Confirm with E-01 before splicing |
| APH-002 | A TB6600 | `A-` | A motor | A- lead | Phase A- | KWANGIL 20 AWG 4C conductor TBD; original motor lead green | documented | Confirm with E-01 before splicing |
| APH-003 | A TB6600 | `B+` | A motor | B+ lead | Phase B+ | KWANGIL 20 AWG 4C conductor TBD; original motor lead red | documented | Confirm with E-01 before splicing |
| APH-004 | A TB6600 | `B-` | A motor | B- lead | Phase B- | KWANGIL 20 AWG 4C conductor TBD; original motor lead blue | documented | Confirm with E-01 before splicing |
| ASH-001 | A motor cable shield/drain | Drain wire at TB6600 end | DIN rail PE/chassis terminal | PE/chassis TBD | Cable shield bond | Bare/tinned drain | TBD | Bond at driver/DIN end only; insulate shield at motor end; verify continuity to PE and isolation from DC `-V` |

## Limits, controls, and safety

| ID | From device | From terminal | To device | To terminal | Signal | Expected behavior | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| SAF-001 | X HiLetgo KW12-3 limit switch | `COM` and `NC` planned | RP23CNC | X limit input pair, silkscreen TBD | X home/limit | NC released/healthy, opens when tripped or wire breaks; controller inversion TBD | Twisted pair TBD | selected, not wired | Verify `COM`-`NC` continuity and exact controller terminal labels/polarity in F-04 before connection |
| SAF-002 | Y HiLetgo KW12-3 limit switch | `COM` and `NC` planned | RP23CNC | Y limit input pair, silkscreen TBD | Y home/limit | NC released/healthy, opens when tripped or wire breaks; controller inversion TBD | Twisted pair TBD | selected, not wired | Verify `COM`-`NC` continuity and exact controller terminal labels/polarity in F-04 before connection |
| SAF-003 | A index sensor | TBD | RP23CNC | A limit/probe input TBD | Bed index/home | Polarity TBD | Shielded/twisted TBD | TBD | Sensor selection pending |
| SAF-004 | SW1 mxuteuk `HB2-BS544` E-stop, NC-A | Contact pair A | RP23CNC | Opto-isolated E-stop/Halt terminal pair TBD | Immediate grblHAL Halt | NC released/healthy, open when pressed; use NC input configuration (planned `$14=6`, verify live) | Low-current protected control wire TBD | planned | Initial manual-supported E-stop. RP23CNC stays powered; verify in E-19. |
| SAF-005 | SW1 mxuteuk `HB2-BS544` E-stop, NC-B | Contact pair B | None | Both terminals individually insulated | Unused | No electrical connection | None | planned | K1 is not part of this project. |
| SAF-006 | MEISHILE `S-120-12` | `+V` through FMAIN | HCDC `HD064RT` | `DC INPUT +` | 12 V motor/tool feed | 12 V while the main power is on; E-stop does not remove this power | Protected 12 V positive TBD | planned | FMAIN maximum 10 A; do not bypass it. |
| SAF-007 | HCDC `HD064RT` | `OUT1` / fused pair | X TB6600 | 12 V input | X motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | Factory 3 A fuse is provisional |
| SAF-008 | HCDC `HD064RT` | `OUT2` / fused pair | Y TB6600 | 12 V input | Y motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | Factory 3 A fuse is provisional |
| SAF-009 | HCDC `HD064RT` | `OUT3` / fused pair | A TB6600 | 12 V input | A motor power | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | Factory 3 A fuse is provisional |
| SAF-010 | HCDC `HD064RT` | `OUT4` / fused pair | Pololu D36V50F6 | `VIN/GND` | Toolhead motor supply source | Remains powered when SW1 is pressed | Branch wire/fuse TBD | planned | Factory 3 A fuse may be insufficient; characterize E-15 |

## Magnetic bed calibration adapter

The intended final magnetic calibration sensor path uses the toolhead SparkFun
Pro Micro RP2350 as the TMAG5273 reader because the TMAG5273 is wired to the
toolhead Qwiic connector. The Pro Micro drives `GP27` as the conditioned
`A_HOME` output to the RP23CNC A limit/home input through a selected
open-drain, transistor, optocoupler, or equivalent switch-like interface. `GP27`
must only assert when both the TMAG5273 threshold condition is true and the
`GP28` `HOME_ARM` input is active, so the bed magnet cannot trip the A
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

| ID | From device | From terminal | To device | To terminal | Signal | Expected behavior | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| MAG-001 | SparkFun TMAG5273 Qwiic | Qwiic `SDA/SCL/3V3/GND` | SparkFun Pro Micro RP2350 | Qwiic `GPIO16/GPIO17/3V3/GND` | 3D Hall readings | 3.3 V I2C; stable magnetic vector or magnitude readings | Qwiic cable TBD | bench-verified | E-09 passed after correcting the signal pair: GP16 is SDA and GP17 is SCL. Far/near/return magnitudes were 0.24/7.51/7.44 mT; initial threshold guidance 3.5 mT with 1.0 mT hysteresis. |
| MAG-002 | SparkFun Pro Micro RP2350 | USB device TBD | Host PC | USB TBD | Calibration telemetry | Reports TMAG5273 readings during host-commanded scan moves | USB cable TBD | TBD | Calibration script/interface TBD; current bench firmware prints TMAG telemetry |
| MAG-003 | SparkFun Pro Micro RP2350 | `GP27` through PC817C U3 | RP23CNC | `LIMA` / A limit-home input | `A_HOME` magnetic index | RP23CNC V1.0 page 4: idle approximately 12 V; assert by sinking to `GND1` through its 2 kΩ / input-opto path (about 5.3 mA). Do not drive this terminal high. | Shielded/twisted TBD | harness re-test required | U3 passed the 12 V / 2.2 kΩ sample test on prior GP9 wiring; repeat it on GP27 after repinning. |
| MAG-003A | RP23CNC | `Aux 0` digital output | PC817C module U2 LED cathode | `AUX0` / pin 2 | `HOME_ARM` command into isolation module | `M64 P0` arms A/theta homing; U2 LED on only when Aux0 sinks current from controller `+5V` through `R2`; `M65 P0` disarms | Protected signal conductor TBD | simulated-input bench verified; controller mapping pending | U2 changed GPIO20 HIGH/LOW using the 5 V low-side-sink bench simulation. Verify actual RP23CNC Aux0 terminal polarity/current before connection. |
| MAG-003B | PC817C module U2 collector | `GP28` / pullup node | SparkFun Pro Micro RP2350 | `GP28` / A2 | `HOME_ARM` isolated output to Pro Micro | Local 3.3 V pullup through `R4`; U2 on pulls GP28 low | Protected signal conductor TBD | harness re-test required | Assigned to the consecutive right-side harness; repeat the U2 test after repinning. |
| MAG-004 | Center bed magnet | Embedded bed center | TMAG5273 scan path | Sensor over bed | Bed-center reference | Saturated or thresholded footprint centered on bed rotation axis | Mechanical placement | TBD | Cylindrical magnet; diameter, grade, polarity, and depth TBD |
| MAG-005 | Outer bed magnet | Embedded near 8.9 in radius | TMAG5273 scan path | Sensor over bed | Theta/A index reference | Saturated or thresholded footprint centered on angular index mark | Mechanical placement | TBD | Cylindrical magnet; final measured radius and angular reference TBD |

## Toolhead control and sensors

Toolhead prototype controller is the SparkFun Pro Micro RP2350 mounted with the
toolhead electronics. Pin choices below are prototype firmware assignments and
must pass bench tests before being treated as final machine wiring.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| TH-001A | RP23CNC | Spindle group `ENA` | PC817C module U1 LED cathode | `ENA` / pin 2 | M3/M5 command into isolation module | U1 LED on only when ENA sinks current from controller `+5V` through `R1`; M3/M5 behavior and fail-safe LIFT remain polarity-test dependent | Shielded/twisted TBD | TBD | See `hardware/pc817-interface/pc817-interface.sch`; RP23U5XBB manual identifies spindle `ENA`; verify voltage, polarity, and current before connection; test F-05 |
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
