# Master Wiring Table

This is the authoritative wiring record for the machine. Update it whenever a
part, pin assignment, connector, voltage, wire color, or test result changes.

The visual diagram in `docs/full_wiring_diagram.html` is explanatory only. If it
disagrees with this table, this table controls.

Selected controller: Brookwood Design RP23CNC / RP23U5XBB variant
`48493912129751`, **With Assembly and Ethernet Kits**. Connectors and Ethernet
components must be soldered and inspected before wiring.

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
| PWR-002 | MEISHILE S-120-12 | Terminal 6 or 7 `+V` TBD | RP23CNC | Main power input TBD | Controller power | 12 VDC nominal | TBD | Branch fuse TBD | TBD | Final positive terminal allocation not assigned |
| PWR-003 | MEISHILE S-120-12 | Terminal 6 or 7 `+V` TBD | X TB6600 | `VCC`/`DC+` TBD | Stepper power | 12 VDC nominal | TBD | Branch fuse TBD | TBD | Use a fused distribution block if terminal capacity is insufficient |
| PWR-004 | MEISHILE S-120-12 | Terminal 4 or 5 `-V` TBD | X TB6600 | `GND`/`DC-` TBD | Stepper return | 0 VDC | TBD | Same branch as PWR-003 | TBD | Final negative terminal allocation not assigned |
| PWR-005 | MEISHILE S-120-12 | Terminal 6 or 7 `+V` TBD | Y TB6600 | `VCC`/`DC+` TBD | Stepper power | 12 VDC nominal | TBD | Branch fuse TBD | TBD | Use a fused distribution block if terminal capacity is insufficient |
| PWR-006 | MEISHILE S-120-12 | Terminal 4 or 5 `-V` TBD | Y TB6600 | `GND`/`DC-` TBD | Stepper return | 0 VDC | TBD | Same branch as PWR-005 | TBD | Final negative terminal allocation not assigned |
| PWR-007 | MEISHILE S-120-12 | Terminal 6 or 7 `+V` TBD | A TB6600 | `VCC`/`DC+` TBD | Stepper power | 12 VDC nominal | TBD | Branch fuse TBD | TBD | Use a fused distribution block if terminal capacity is insufficient |
| PWR-008 | MEISHILE S-120-12 | Terminal 4 or 5 `-V` TBD | A TB6600 | `GND`/`DC-` TBD | Stepper return | 0 VDC | TBD | Same branch as PWR-007 | TBD | Final negative terminal allocation not assigned |
| PWR-009A | MEISHILE S-120-12 | Terminal 6 or 7 `+V` TBD | B085T73CSD buck | `IN+` TBD | Toolhead buck input | 12 VDC nominal; module listing accepts 4-38 V | TBD | Branch fuse TBD | TBD | Confirm received terminal labels |
| PWR-009B | MEISHILE S-120-12 | Terminal 4 or 5 `-V` TBD | B085T73CSD buck | `IN-` TBD | Toolhead buck return | 0 VDC | TBD | Same branch as PWR-009A | TBD | Final distribution terminal not assigned |
| PWR-009 | B085T73CSD buck | `OUT+` TBD | DRV8833 | `VM` TBD | Actuator motor power | Adjust to 6.0 V before connection | TBD | Output fuse/capacitance TBD | purchased | Listing claims adjustable 1.25-36 V and 5 A maximum; continuous rating unverified |
| PWR-010 | B085T73CSD buck | `OUT-` TBD | DRV8833 | `GND` TBD | Actuator return | 0 V | TBD | Same branch as PWR-009 | purchased | Common-reference plan pending |
| PWR-011 | Logic supply/controller | TBD | HX711 | `VCC` TBD | HX711 power | TBD after module inspection | TBD | TBD | TBD | Verify module voltage requirements |
| PWR-012 | Logic supply/controller | TBD | TMAG5273 Qwiic | `3V3`/Qwiic | Hall sensor power | 3.3 V | Qwiic cable TBD | TBD | documented | Verify controller-side Qwiic/I2C connection |

## Motion control signals

The RP23CNC terminal names and TB6600 common-anode/common-cathode wiring remain
TBD until the exact board revision and received driver input circuits are
verified. Do not use the conceptual HTML diagram as proof of polarity.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| MOT-001 | RP23CNC | X STEP TBD | X TB6600 | `PUL+` or `PUL-` TBD | X step pulse | 5 V-compatible output; topology TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-002 | RP23CNC | X DIR TBD | X TB6600 | `DIR+` or `DIR-` TBD | X direction | Polarity TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-003 | RP23CNC | ENABLE TBD | X TB6600 | `ENA+` or `ENA-` TBD | X enable | Shared vs individual TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-004 | RP23CNC | Y STEP TBD | Y TB6600 | `PUL+` or `PUL-` TBD | Y step pulse | Topology TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-005 | RP23CNC | Y DIR TBD | Y TB6600 | `DIR+` or `DIR-` TBD | Y direction | Polarity TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-006 | RP23CNC | ENABLE TBD | Y TB6600 | `ENA+` or `ENA-` TBD | Y enable | Shared vs individual TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-007 | RP23CNC | A STEP TBD | A TB6600 | `PUL+` or `PUL-` TBD | A step pulse | Topology TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-008 | RP23CNC | A DIR TBD | A TB6600 | `DIR+` or `DIR-` TBD | A direction | Polarity TBD | Twisted pair TBD | TBD | Test E-03/F-03 |
| MOT-009 | RP23CNC | ENABLE TBD | A TB6600 | `ENA+` or `ENA-` TBD | A enable | Shared vs individual TBD | Twisted pair TBD | TBD | Test E-03/F-03 |

## Stepper motor phases

Manufacturer colors are documented, but each motor must still pass continuity
test E-01 before connection.

| ID | From device | From terminal | To device | To terminal | Signal | Wire color | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|
| XPH-001 | X TB6600 | `A+` | X motor | A+ lead | Phase A+ | Black | documented | 17HS15-1504S-X1 manufacturer listing |
| XPH-002 | X TB6600 | `A-` | X motor | A- lead | Phase A- | Green | documented | Confirm with E-01 |
| XPH-003 | X TB6600 | `B+` | X motor | B+ lead | Phase B+ | Red | documented | Confirm with E-01 |
| XPH-004 | X TB6600 | `B-` | X motor | B- lead | Phase B- | Blue | documented | Confirm with E-01 |
| YPH-001 | Y TB6600 | `A+` | Y motor | A+ lead | Phase A+ | Black | documented | Confirm with E-01 |
| YPH-002 | Y TB6600 | `A-` | Y motor | A- lead | Phase A- | Green | documented | Confirm with E-01 |
| YPH-003 | Y TB6600 | `B+` | Y motor | B+ lead | Phase B+ | Red | documented | Confirm with E-01 |
| YPH-004 | Y TB6600 | `B-` | Y motor | B- lead | Phase B- | Blue | documented | Confirm with E-01 |
| APH-001 | A TB6600 | `A+` | A motor | A+ lead | Phase A+ | Black | documented | Confirm with E-01 |
| APH-002 | A TB6600 | `A-` | A motor | A- lead | Phase A- | Green | documented | Confirm with E-01 |
| APH-003 | A TB6600 | `B+` | A motor | B+ lead | Phase B+ | Red | documented | Confirm with E-01 |
| APH-004 | A TB6600 | `B-` | A motor | B- lead | Phase B- | Blue | documented | Confirm with E-01 |

## Limits, controls, and safety

| ID | From device | From terminal | To device | To terminal | Signal | Expected behavior | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| SAF-001 | X limit switch | TBD | RP23CNC | X limit input TBD | X home/limit | Fail-safe polarity TBD | Shielded/twisted TBD | TBD | Switch not selected |
| SAF-002 | Y limit switch | TBD | RP23CNC | Y limit input TBD | Y home/limit | Fail-safe polarity TBD | Shielded/twisted TBD | TBD | Switch not selected |
| SAF-003 | A index sensor | TBD | RP23CNC | A limit/probe input TBD | Bed index/home | Polarity TBD | Shielded/twisted TBD | TBD | Sensor selection pending |
| SAF-004 | E-stop | TBD | RP23CNC | Halt/E-stop input TBD | Immediate stop | Normally closed preferred; verify design | TBD | TBD | Power-removal strategy pending |
| SAF-005 | E-stop | TBD | Motor power contactor/enable | TBD | Remove motor energy | Architecture TBD | TBD | TBD | Must be coordinated with SAF-004 |

## Toolhead control and sensors

Controller placement is unresolved. `Toolhead controller` below means either
the RP23CNC plugin/core-1 implementation or the separate MCU selected later.

| ID | From device | From terminal | To device | To terminal | Signal | Expected level/polarity | Wire | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|---|
| TH-001 | RP23CNC | Spindle enable/output TBD | Toolhead controller | ENGAGE input TBD | M3/M5 engage/lift | M3/M5 polarity TBD; fail-safe LIFT | TBD | TBD | Test F-05 |
| TH-002 | Toolhead controller | Motor output 1 TBD | DRV8833 | `AIN1`/`IN1` TBD | Motor direction/PWM | Logic level TBD | TBD | TBD | Module inspection required |
| TH-003 | Toolhead controller | Motor output 2 TBD | DRV8833 | `AIN2`/`IN2` TBD | Motor direction/PWM | Logic level TBD | TBD | TBD | Module inspection required |
| TH-004 | DRV8833 | `AOUT1`/`OUT1` TBD | N20 actuator | Motor lead 1 | Actuator drive | Polarity assigned during T-01 | TBD | TBD | Reverse leads or logic if direction is wrong |
| TH-005 | DRV8833 | `AOUT2`/`OUT2` TBD | N20 actuator | Motor lead 2 | Actuator drive | Polarity assigned during T-01 | TBD | TBD | 6 V motor |
| TH-006 | 300 g load cell | Excitation+ TBD | HX711 | `E+` TBD | Bridge excitation+ | Wire color TBD | TBD | TBD | Identify with datasheet/meter |
| TH-007 | 300 g load cell | Excitation- TBD | HX711 | `E-` TBD | Bridge excitation- | Wire color TBD | TBD | TBD | Identify with datasheet/meter |
| TH-008 | 300 g load cell | Signal+ TBD | HX711 | `A+` TBD | Force signal+ | Wire color TBD | TBD | TBD | Calibrate in E-07 |
| TH-009 | 300 g load cell | Signal- TBD | HX711 | `A-` TBD | Force signal- | Wire color TBD | TBD | TBD | Calibrate in E-07 |
| TH-010 | HX711 | `DOUT`/`DT` TBD | Toolhead controller | GPIO TBD | Load-cell data | Logic level TBD | Twisted with ground TBD | TBD | Tests E-07/E-08 |
| TH-011 | Toolhead controller | GPIO TBD | HX711 | `SCK` TBD | Load-cell clock | Logic level TBD | Twisted with ground TBD | TBD | Tests E-07/E-08 |
| TH-012 | Toolhead controller | I2C SDA TBD | TMAG5273 Qwiic | SDA | Hall sensor data | 3.3 V I2C | Qwiic cable TBD | TBD | Test E-09 |
| TH-013 | Toolhead controller | I2C SCL TBD | TMAG5273 Qwiic | SCL | Hall sensor clock | 3.3 V I2C | Qwiic cable TBD | TBD | Test E-09 |
| TH-014 | Toolhead controller | FAULT output TBD | RP23CNC | Feed hold/halt input TBD | Tool fault | Fail-safe polarity TBD | TBD | TBD | Later integration phase |
| TH-015 | Toolhead controller | READY output TBD | RP23CNC | Auxiliary input TBD | Contact ready | Optional; polarity TBD | TBD | TBD | Later handshake upgrade |

## Communications

| ID | From device | From terminal | To device | To terminal | Signal | Cable | Status | Evidence/notes |
|---|---|---|---|---|---|---|---|---|
| COM-001 | Host PC | USB TBD | RP23CNC | USB-C | G-code/control | USB data cable TBD | TBD | Baseline transport candidate |
| COM-002 | Host/network | Ethernet | RP23CNC WizNet module | Ethernet | G-code/WebUI/network | Cat5e or better | TBD | Optional adapter/build configuration |
| COM-003 | microSD card | Card contacts | RP23CNC | microSD socket | Offline G-code | microSD | TBD | Optional transport candidate |

## Revision log

| Date | Revision | Change | Updated by | Related evidence |
|---|---:|---|---|---|
| 2026-06-06 | 0.7 | Identified purchased RP23CNC variant as With Assembly and Ethernet Kits; added required soldering and inspection gate before pin assignment or power | Codex | Brookwood Design variant 48493912129751 |
| 2026-06-06 | 0.6 | Replaced the fixed 5 V actuator candidate with purchased B085T73CSD adjustable modules; target output is 6.0 V and the claimed 5 A maximum remains subject to load/thermal testing | Codex | Amazon listing and tests E-14/E-15 |
| 2026-06-06 | 0.5 | Added B0F1WB3LJ5 fixed 5 V buck as a toolhead bench-test candidate; final acceptance depends on measured actuator current, ripple, and temperature | Codex | Amazon listing and tests E-06/E-14 |
| 2026-06-06 | 0.4 | Corrected received model to S-120-12; documented terminals 1-7 and +V ADJ from the physical unit; split AC line, neutral, and protective-earth conductors; archived QR-linked PDF | Codex | Owner inspection and `references/MEISHILE-S-120-12-manual.pdf` |
| 2026-06-06 | 0.3 | Added internally consistent same-ASIN reseller details: reported model SE-1500-12, 50/60 Hz, approximate size/weight, protection claims, and no included connectors. Rejected contradictory 30 A/360 W text as unrelated listing contamination. | Codex | Ubuy product page supplied by project owner |
| 2026-06-06 | 0.2 | Added selected MEISHILE B0781ZJ7GP 12 V, 10 A, 120 W supply and updated proposed 12 V distribution | Codex | Amazon listing supplied by project owner |
| 2026-06-06 | 0.1 | Created master table from current BOM, interface contract, and conceptual diagram; all unverified terminals retained as TBD | Codex | Repository organization phase |
