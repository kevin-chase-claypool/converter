# Hardware Inventory

Physical connections are maintained in
[`WIRING_TABLE.md`](WIRING_TABLE.md), with the current power topology summarized
in [`POWER_DISTRIBUTION.md`](POWER_DISTRIBUTION.md). The BOM says what parts
exist; the wiring table says exactly how each conductor is connected and whether
it has been verified.

Status values: `selected`, `received`, `verified`, `rejected`, or `TBD`.

## Motion hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | RP23CNC / RP23U5XBB V1.01 with Assembly and Ethernet Kits | Received Brookwood Design variant `48493912129751`; front silkscreen confirms `RP23U5XBB V1.01`. Overview photographs show installed terminal strips, basic headers, and two Wiz850io sockets. Supplied Ethernet module shows a Wiznet W5500 IC and two six-pin rows. | received | Complete explicit kit inventory; perform magnified solder inspection and continuity/power-rail checks; install Ethernet module; archive matching V1.01 schematic, pin map, and firmware target |
| 1 | MEISHILE `S-120-12`, Amazon ASIN B0781ZJ7GP | Received enclosed constant-voltage supply. Unit markings identify model `S-120-12` with seven terminals: `L`, `N`, protective earth, two `-V`, and two `+V`; `+V ADJ` is beside terminal 7. Listings specify 100-240 VAC input, 50/60 Hz, 12 VDC, 10 A, 120 W nominal. | received | Photograph rating label, verify protective-earth continuity, measure output and adjustment range, design branch fusing, and confirm continuous-load thermal margin |
| 1 | HCDC `HD064RT` DIN-rail 8-channel DC fuse distribution module | Installed module; 5-32 V DC, eight pluggable fused outputs, 20 A aggregate specification, and factory 3 A fuses. Owner allocation: `OUT1` RP23CNC, `OUT4` D36V50F6, `OUT6` X TB6600, `OUT7` Y TB6600, `OUT8` A TB6600; `OUT2`/`OUT3`/`OUT5` unused. Owner-selected starting fuse values: 3 A each for `OUT6`/`OUT7`/`OUT8`; physical fitted values remain to be confirmed. The six TB6600 branch conductors are owner-reported 20 AWG. | received | With power removed, verify DC-input/output polarity, continuity, actual fitted fuse markings, and branch current before energizing loads |
| 1 | mxuteuk `HB2-BS544` 22 mm 2NC latching mushroom E-stop | Purchased 2026-08-11. Two independent normally-closed contact pairs, push-to-stop/twist-to-release. NC-A is allocated to the manual-supported RP23CNC Halt input; NC-B is unused/insulated. | purchased | Verify contact-pair isolation and released/pressed continuity; complete E-19 before machine operation |
| 3 | STEPPERONLINE 17HS15-1504S-X1 | Bipolar NEMA 17, 1.8 deg, 1.5 A/phase, 45 Ncm, 4 wires. X/Y use confirmed GT2 20-tooth motor pulleys; A uses the 60T-to-720T (12:1) bed drive. | selected | Coil pairs, mechanics, required acceleration and torque margin |
| 3 | Amazon ASIN B0FQ5GBNZ1 | Listed as TB6600, 9-42 V, up to 4 A, step/direction, three-pack. The product-label image maps `SW1/SW2/SW3`: 8× = OFF/ON/OFF and 16× = OFF/OFF/ON; `SW4/SW5/SW6`: 1.5 A = ON/OFF/ON. Initial configuration is X/Y at 16× (3,200 pulses/rev; 80 steps/mm with 20T GT2 pulleys) and A at 8× (1,600 pulses/rev; 19,200 pulses/bed revolution through 12:1 reduction). | selected | With power removed, set current to 1.5 A: SW4 ON, SW5 OFF, SW6 ON. Verify all three received labels/switch numbering and input polarity before motor power; verify thermal behavior during motion tests. |
| TBD length | KWANGIL 20 AWG 4C AMESB shielded cable, Amazon ASIN B0GVBF51Q7 | Purchased 4-conductor UL2464-style shielded cable for the X NEMA17 phase wiring; listing identifies flexible stranded tinned-copper conductors, overall shield with drain, and tinned-copper braid (`OS+Drain+TC BRD`). X is the only motor cable with a grounded sheath: driver-side Phase A is black/green and Phase B is red/white, with white continuing the motor's blue B- lead. Y/A use unshielded leads, retaining black/green and red/blue coil pairs. | purchased | Confirm received gauge/markings, flexibility in the drag chain, conductor colors, drain-wire continuity to shield, and fit through strain reliefs/connectors before any future replacement. X cable shielding is documented in the master wiring table. |
| 2 | HiLetgo KW12-3 roller-lever microswitch, Amazon ASIN B07X142VGC | SPDT mechanical limit switch with terminals marked `COM`, `NO`, and `NC`; project owner selected these for X and Y limits. The NC contact is planned for fail-safe operation. | selected | Confirm terminal markings with a meter: released `COM`-`NC` closed, lever pressed open. Use short temporary leads for F-04 before choosing the permanent drag-chain cable route. Then verify exact RP23CNC limit-input terminal labels, input polarity, and grblHAL inversion. |

Motor lead colors from the manufacturer listing:

| Phase | Positive | Negative |
|---|---|---|
| A | Black | Green |
| B | Red | Blue |

Do not energize a driver until coil pairs are confirmed with an ohmmeter.

## Electronics mounting hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | Tecmojo `14130201` sliding rack shelf, Amazon ASIN `B0BMW9V6MS` | 1U cold-rolled-steel shelf for a four-post 19-inch rack; published width 482.6 mm, shelf depth 350 mm, adjustable rack-post depth 350-500 mm, body height 44-44.45 mm, and capacity 110 lb / 50 kg. Reference STEP models and modeling limits are documented in [`cad/README.md`](cad/README.md). | selected | Confirm received SKU and revision; measure sheet thickness, tray width, mounting-hole locations, slide profiles, vent pitch, cable passages, anti-slip stops, and actual closed/open travel before relying on inferred CAD details |

## Signal interface hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | B07WFGTNQC 4-channel optocoupler isolation / voltage-converter module | Amazon listing describes 3.3 V or 5 V control inputs and a 3.6-24 V output side. That output specification does not establish safe direct compatibility with an RP2350 3.3 V GPIO input. | rejected | Retain only as a spare or bench-test item; do not use it in the RP23CNC-to-Pro-Micro harness without a separately verified 3.3 V-safe output circuit. |
| 50 | BOJACK PC817C DIP-4 optocouplers, Amazon ASIN B08CXRHDHP | Purchased 2026-08-06. Listing identifies phototransistor output, 2.54 mm DIP-4 package, and a 50% minimum CTR at `I_F = 5 mA`. Three parts are allocated to the proposed compact interface board. | purchased | Inspect package markings; bench-test representative parts with the actual 5 V and 3.3 V drive circuits before installation. |
| 1 | Custom three-channel PC817C minimum-wire module, 40.16 × 22.65 mm envelope | Current source: `hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_pcb`, matching schematic, `PERFBOARD_BUILD.md`, and `PRO_MICRO_JST_HARNESS.md`. Two controller-to-toolhead channels feed GP29 and GP28; reverse GP27 sinks `A_HOME`. All parts are THT: three PC817C DIP-4, three 1N4148 clamps, `R1/R2 = 680 Ω`, `R3/R4 = 10 kΩ`, `R5 = 390 Ω`, direct wire or 0 Ω `R6`, `C1/C2 = 47 nF`, and two 1×6 2.54 mm screw terminals. C3 is omitted. The two-layer map uses 38 segments, 161.83 mm total route length, and no vias. | bench circuit verified; harness re-test required | The prior GP8/GP20/GP9 bench tests passed. Repeat U1/U2/U3 after moving to GP29/GP28/GP27; then verify actual RP23CNC ENA/Aux0 behavior in F-05. |

## Toolhead hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | Amazon ASIN B0CDQSVBFC | 1024GA20/N20 threaded gearmotor, selected listing option 6 V 200 RPM, M4 x 55 mm shaft | selected | E-05 no-load passed; corrected aligned unloaded motion is 0.009 A; bounded E-06 stall/preload-hold test passed at 0.18 A; thermal margin, travel limits, polarity, backlash, and required force remain to be characterized |
| 1 | ACEIRMC DRV8833 module, Amazon ASIN B08RMWTDLM | 3-10 V dual H-bridge module; seller specifies 1.5 A per H-bridge and labels the low-true sleep input `ULT` and protection/fault output `EEP`. Mounted on the shared toolhead perfboard. | received | Installed harness is GP7→`ULT` and GP6←`EEP`; firmware matches it. Inspect J2 sleep-control bridge, then complete E-14C, E-05, E-06, and T-01. |
| 1 | Pololu D36V50F6 6 V, 5.5 A step-down regulator, item 4092 | Selected for DIN-side 12 V to 6 V toolhead power regulation; manufacturer specifies fixed 6 V output, 6.5-50 V input range, typical maximum continuous output current 3.3-8 A depending on conditions, power-good output, enable input, soft start, reverse-voltage protection up to 40 V, over-current/short-circuit protection, over-temperature shutoff, and 1 x 1 x 0.375 in size | selected | Purchase/receipt status TBD; verify output, ripple, thermal behavior, mounting, and current margin under actuator load |
| 2 | Adjustable buck module, Amazon ASIN B085T73CSD | Purchased two-pack; listing specifies 4-38 V input, adjustable 1.25-36 V output, LED voltmeter/display, and 5 A maximum output | spare | Superseded for final 6 V toolhead rail by the Pololu D36V50F6; retain for bench/prototype use only after setting output with a meter |
| 1 | Pololu S7V8F5 5 V step-up/step-down regulator, item 2123 | Mounted on the shared toolhead perfboard for local logic regulation from the 6 V rail; manufacturer specifies 2.7-11.8 V input, fixed 5 V output, compact 0.45 x 0.65 in module, and about 500 mA to 1 A output across most of the input range. The shared board's 6 V input is a pending two-pin JST connection. | received | E-14B pre-power check; then verify 5.0 V output under RP2350, HX711, and TMAG5273 load; confirm thermal behavior and that motor-current dips do not reset the RP2350 |
| 5 | Fixed 5 V buck module, Amazon ASIN B0F1WB3LJ5 | Existing modules; listing specifies 5-30 V input, approximately 1.5 A continuous and 1.8 A maximum output | spare | Retain for low-current 5 V loads; superseded for toolhead logic by the Pololu S7V8F5 buck-boost |
| 1 | Amazon ASIN B00XRRNCOO | HiLetgo HX711 24-bit load-cell ADC module | selected | Board data rate selection, noise, grounding, actual sample interval |
| 1 | Amazon ASIN B07NRVML17 | uxcell 300 g wired load cell; manufacturer mapping is Red `EXC+`, Black `EXC-`, Green `SEN+`, White `SEN-`; sensitivity `0.7 ± 0.15 mV/V`, error `±0.05% F.S.` | selected | Verify received connector/wire labels and calibrate in E-07; characterize overload margin |
| 1 | Amazon ASIN B0CQVG659B | SparkFun TMAG5273 Qwiic 3D Hall-effect sensor | selected | I2C address/configuration, magnet geometry, usable position resolution |

## Power and protection still TBD

- Confirm the received main supply matches the advertised 12 VDC, 10 A, 120 W model.
- Determine the machine's measured current budget and suitable continuous-load margin.
- Separate regulated toolhead motor supply if the main supply exceeds DRV8833/motor limits.
- Toolhead logic grounding, decoupling, and local 6 V to 5 V regulation topology.
- Select FMAIN/FCTRL hardware and measured fuse values; the HD064RT factory 3 A fuses are provisional.
- Toolhead hard-travel switch selection and all X/Y controller-side limit wiring.
- Flyback/noise suppression and cable shielding strategy.
- Connectors, strain relief, and cable management for the rotating bed, including
  capacity and bend-radius verification for the most crowded drawer-side drag
  chain before permanent X/Y limit wiring is installed.

## Compatibility gates

These checks must pass before integrated wiring:

1. RP23CNC STEP/DIR outputs are electrically compatible with each received TB6600 input.
2. Driver current can be set at or below the motor's 1.5 A/phase rating using the driver's documented current convention.
3. Toolhead motor stall current is inside the specific DRV8833 module's safe operating range.
4. Toolhead buck-converter current and thermal capacity exceed measured actuator demand with margin.
5. The 6 V motor cannot be exposed to the stepper supply voltage.
6. HX711, TMAG5273, and RP23CNC logic share compatible voltage levels.
7. Enough RP23CNC I/O remains after X/Y/A, limits, Ethernet, SD, and spindle/tool command assignments.

## Source links

- RP23CNC: https://github.com/phil-barrett/RP23CNC
- Purchased RP23CNC variant: https://brookwood-design-77.myshopify.com/products/ro?variant=48493912129751
- RP23CNC board information: https://www.grbl.org/rp23u5xbb
- Archived RP23CNC user manual: [`references/RP23CNC-user-manual.pdf`](references/RP23CNC-user-manual.pdf)
- Archived RP23U5XBB assembly instructions: [`references/RP23U5XBB-assembly-instructions.pdf`](references/RP23U5XBB-assembly-instructions.pdf)
- grblHAL RP2040/RP2350 driver: https://github.com/grblHAL/RP2040
- Tecmojo electronics shelf: https://www.amazon.com/dp/B0BMW9V6MS
- Tecmojo shelf product page: https://tecmojo.com/products/tecmojo-1u-adjustable-vented-sliding-server-rack-mount-shelf-110lbs-14-16inch-adjustable-mounting-depth-4-post-universal-tray-for-19inch-av-network-equipment-rack
- Main 12 V supply: https://www.amazon.com/dp/B0781ZJ7GP
- Additional reseller data for the same ASIN: https://www.ubuy.ec/en/product/3PQED2A14-12v-10a-120w-led-driver-switching-power-supply-smps-universal-regulated-transformer-converter-ac-100v-240v-to-dc-12v-for-led-strip-lights
- Archived QR-linked documentation: [`references/MEISHILE-S-120-12-manual.pdf`](references/MEISHILE-S-120-12-manual.pdf)
- Stepper motor listing/datasheet: https://www.omc-stepperonline.com/
- TB6600 listing: https://www.amazon.com/dp/B0FQ5GBNZ1
- Selected NEMA17 shielded cable: https://www.amazon.com/AMESB-20AWG-Shielded-Cable-UL2464/dp/B0GVBF51Q7
- Toolhead motor: https://www.amazon.com/dp/B0CDQSVBFC
- Spare adjustable toolhead buck converter: https://www.amazon.com/dp/B085T73CSD
- Selected 6 V toolhead regulator: https://www.pololu.com/product/4092
- Selected local 5 V toolhead regulator: https://www.pololu.com/product/2123
- Amazon listing for selected local 5 V toolhead regulator: https://us.amazon.com/Pololu-Step-Up-Step-Down-Voltage-Regulator/dp/B01IGGMSCM
- Spare 5 V buck converter: https://www.amazon.com/dp/B0F1WB3LJ5
- Selected B07WFGTNQC optocoupler isolation module: https://www.amazon.com/dp/B07WFGTNQC
- HX711 modules: https://www.amazon.com/dp/B00XRRNCOO
- 300 g load cell: https://www.amazon.com/dp/B07NRVML17
- TMAG5273 board: https://www.amazon.com/dp/B0CQVG659B
