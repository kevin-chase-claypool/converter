# Hardware Inventory

Status values: `selected`, `received`, `verified`, `rejected`, or `TBD`.

## Motion hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | RP23CNC / RP23U5XBB | RP235x grblHAL breakout; 5 axes; step/dir/enable; limit inputs; Ethernet option | selected | Exact board revision, assembled options, pin map, firmware board target |
| 3 | STEPPERONLINE 17HS15-1504S-X1 | Bipolar NEMA 17, 1.8 deg, 1.5 A/phase, 45 Ncm, 4 wires | selected | Coil pairs, mechanics, required acceleration and torque margin |
| 3 | Amazon ASIN B0FQ5GBNZ1 | Listed as TB6600, 9-42 V, up to 4 A, step/direction, three-pack | selected | Received model, logic input current/polarity, current switch table, microstep table, thermal behavior |

Motor lead colors from the manufacturer listing:

| Phase | Positive | Negative |
|---|---|---|
| A | Black | Green |
| B | Red | Blue |

Do not energize a driver until coil pairs are confirmed with an ohmmeter.

## Toolhead hardware

| Qty | Item | Known information | Status | Verification needed |
|---:|---|---|---|---|
| 1 | Amazon ASIN B0CDQSVBFC | 1024GA20/N20 threaded gearmotor, selected listing option 6 V 200 RPM, M4 x 55 mm shaft | selected | No-load and stall current, travel limits, polarity, backlash, required force |
| 1 | DRV8833 module | Dual H-bridge motor driver | selected | Module pinout, logic levels, supply range, continuous/peak current and cooling |
| 1 | Amazon ASIN B00XRRNCOO | HiLetgo HX711 24-bit load-cell ADC module | selected | Board data rate selection, noise, grounding, actual sample interval |
| 1 | Amazon ASIN B07NRVML17 | uxcell 300 g wired load cell | selected | Wiring colors, excitation/signal pairs, calibration, overload margin |
| 1 | Amazon ASIN B0CQVG659B | SparkFun TMAG5273 Qwiic 3D Hall-effect sensor | selected | I2C address/configuration, magnet geometry, usable position resolution |

## Power and protection still TBD

- Main stepper supply voltage and current rating.
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
4. The 6 V motor cannot be exposed to the stepper supply voltage.
5. HX711, TMAG5273, and RP23CNC logic share compatible voltage levels.
6. Enough RP23CNC I/O remains after X/Y/A, limits, Ethernet, SD, and spindle/tool command assignments.

## Source links

- RP23CNC: https://github.com/phil-barrett/RP23CNC
- grblHAL RP2040/RP2350 driver: https://github.com/grblHAL/RP2040
- Stepper motor listing/datasheet: https://www.omc-stepperonline.com/
- TB6600 listing: https://www.amazon.com/dp/B0FQ5GBNZ1
- Toolhead motor: https://www.amazon.com/dp/B0CDQSVBFC
- HX711 modules: https://www.amazon.com/dp/B00XRRNCOO
- 300 g load cell: https://www.amazon.com/dp/B07NRVML17
- TMAG5273 board: https://www.amazon.com/dp/B0CQVG659B
