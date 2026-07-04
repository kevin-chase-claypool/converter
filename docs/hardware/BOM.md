# Hardware Inventory

Physical connections are maintained in
[`WIRING_TABLE.md`](WIRING_TABLE.md). The BOM says what parts exist; the wiring
table says exactly how each conductor is connected and whether it has been
verified.

Status values: `selected`, `received`, `verified`, `rejected`, or `TBD`.

## Motion hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | RP23CNC / RP23U5XBB V1.01 with Assembly and Ethernet Kits | Received Brookwood Design variant `48493912129751`; front silkscreen confirms `RP23U5XBB V1.01`. Overview photographs show installed terminal strips, basic headers, and two Wiz850io sockets. Supplied Ethernet module shows a Wiznet W5500 IC and two six-pin rows. | received | Complete explicit kit inventory; perform magnified solder inspection and continuity/power-rail checks; install Ethernet module; archive matching V1.01 schematic, pin map, and firmware target |
| 1 | MEISHILE `S-120-12`, Amazon ASIN B0781ZJ7GP | Received enclosed constant-voltage supply. Unit markings identify model `S-120-12` with seven terminals: `L`, `N`, protective earth, two `-V`, and two `+V`; `+V ADJ` is beside terminal 7. Listings specify 100-240 VAC input, 50/60 Hz, 12 VDC, 10 A, 120 W nominal. | received | Photograph rating label, verify protective-earth continuity, measure output and adjustment range, design branch fusing, and confirm continuous-load thermal margin |
| 3 | STEPPERONLINE 17HS15-1504S-X1 | Bipolar NEMA 17, 1.8 deg, 1.5 A/phase, 45 Ncm, 4 wires | selected | Coil pairs, mechanics, required acceleration and torque margin |
| 3 | Amazon ASIN B0FQ5GBNZ1 | Listed as TB6600, 9-42 V, up to 4 A, step/direction, three-pack | selected | Received model, logic input current/polarity, current switch table, microstep table, thermal behavior |

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

## Toolhead hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | Amazon ASIN B0CDQSVBFC | 1024GA20/N20 threaded gearmotor, selected listing option 6 V 200 RPM, M4 x 55 mm shaft | selected | No-load and stall current, travel limits, polarity, backlash, required force |
| 1 | DRV8833 module | Dual H-bridge motor driver | selected | Module pinout, logic levels, supply range, continuous/peak current and cooling |
| 2 | Adjustable buck module, Amazon ASIN B085T73CSD | Purchased two-pack; listing specifies 4-38 V input, adjustable 1.25-36 V output, LED voltmeter/display, and 5 A maximum output | purchased | Set to 6.0 V before connecting the DRV8833; verify display accuracy, ripple, peak/continuous current, and temperature under actuator load |
| 5 | Fixed 5 V buck module, Amazon ASIN B0F1WB3LJ5 | Existing modules; listing specifies 5-30 V input, approximately 1.5 A continuous and 1.8 A maximum output | spare | Retain for low-current 5 V loads; no longer preferred for the actuator |
| 1 | Amazon ASIN B00XRRNCOO | HiLetgo HX711 24-bit load-cell ADC module | selected | Board data rate selection, noise, grounding, actual sample interval |
| 1 | Amazon ASIN B07NRVML17 | uxcell 300 g wired load cell | selected | Wiring colors, excitation/signal pairs, calibration, overload margin |
| 1 | Amazon ASIN B0CQVG659B | SparkFun TMAG5273 Qwiic 3D Hall-effect sensor | selected | I2C address/configuration, magnet geometry, usable position resolution |

## Power and protection still TBD

- Confirm the received main supply matches the advertised 12 VDC, 10 A, 120 W model.
- Determine the machine's measured current budget and suitable continuous-load margin.
- Separate regulated toolhead motor supply if the main supply exceeds DRV8833/motor limits.
- Logic supply and grounding topology.
- Fuse sizes and branch protection.
- Emergency-stop behavior and whether power is removed from motor drivers.
- Limit switches for X, Y, and toolhead hard travel.
- Flyback/noise suppression and cable shielding strategy.
- Connectors, wire gauge, strain relief, and cable management for the rotating bed.

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
- Toolhead motor: https://www.amazon.com/dp/B0CDQSVBFC
- Selected adjustable toolhead buck converter: https://www.amazon.com/dp/B085T73CSD
- Candidate 5 V buck converter: https://www.amazon.com/dp/B0F1WB3LJ5
- HX711 modules: https://www.amazon.com/dp/B00XRRNCOO
- 300 g load cell: https://www.amazon.com/dp/B07NRVML17
- TMAG5273 board: https://www.amazon.com/dp/B0CQVG659B
