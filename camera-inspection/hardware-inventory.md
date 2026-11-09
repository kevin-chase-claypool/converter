# Hardware inventory — XYθ plotter and CoreZB camera inspection

**Status basis:** Project conversations, not receipts. “Owned” means explicitly reported in use/possession; “selected” does not mean purchased. Quantities and exact revisions must be reconciled against orders and physical hardware.

## 1. Existing XYθ machine

| Hardware | Model / details | Status | Notes |
|---|---|---|---|
| Main controller | RP23CNC, grblHAL | Owned / in use | Ethernet to ioSender |
| Host | Windows laptop, ioSender V2 | Owned / in use | Job sender |
| Microcontrollers | Raspberry Pi Pico 2; Pro Micro RP2350 | Used/discussed | Final role of each to verify |
| X/Y drivers | BTT TMC2209 v1.3 | Owned / in use | |
| θ driver | TB6600 | Owned / in use | 12 V initially; 24 V considered |
| Earlier stepper motors | 17HS15-1504S-X1 NEMA 17, 1.5 A, 45 N·cm | Previously used | |
| Upgraded stepper motors | LDO 42STH48-2804AC-R NEMA 17, 2.8 A | User-reported acquired | Quantity and axis assignment verify |
| Alternatives | LDO 42STH48-2504AC-REVA; NEMA 23 | Considered | Not confirmed bought |
| Rotary transmission | GT2 720-tooth bed ring, 60-tooth motor pulley | Existing design | 12:1 nominal reduction |
| Belts | GT2 10 mm | Existing design | |
| Rotary bed | ~18-inch PETG-CF printed disc, ~600 g | Fabricated / owned | Mechanical precision to characterize |
| Center magnet | Embedded center reference magnet | Owned / installed | Not guaranteed true rotation center |
| Perimeter magnet | Embedded θ index magnet | Owned / installed | |
| Z toolhead drive | N20 1024GA20 encoder motor, 6 V; 200/300/400 RPM discussed | Existing design | Exact variant verify |
| Pen force sensor | 0.3 kg load cell | Owned / in use | Separate controller; **not available in ioSender DRO** |
| Reference strain gauge | 5 N, instructor-provided | Owned / provided | |
| ADC | CS1238, 640 SPS discussed | Existing design | |
| Other analog front end | INA101KU and Pico ADC | Discussed/tested | |
| Z carriage | MGN9C | Owned / in use | Stiction noted |
| Spring | ~0.3 mm wire × 7 mm × 25 mm | Specified | Installed variant verify |
| Endstops/index | Two per axis; TMAG sensing | Existing design | |
| Joysticks | 8-way XY and Z up/down | Existing design | |
| Opto-isolator | Module under test | Owned / testing | |
| Power | 12 V, 10 A, 120 W PSU | Owned / in use | Prior peak ~40 W |
| Boost | Pololu 24 V boost | Discussed/added | Installation status verify |
| Frame | Existing frame; 3030 upgrade discussed | Existing / upgrade planned | |

## 2. CoreZB camera and control — selections vs purchases

| Hardware | Model / details discussed | Status | Verification needed |
|---|---|---|---|
| Vision MCU board | Waveshare ESP32-P4 PoE Ethernet development board / ESP32-P4-ETH family | **Selected; purchase unconfirmed** | Exact SKU, PoE implementation, CSI pinout |
| CSI camera | OV5647 5 MP adjustable-focus module | **Selected; purchase unconfirmed** | Sensor driver, lens, connector compatibility |
| CSI cable | 200 mm 22-to-15-pin ribbon | **Selected; purchase unconfirmed** | Pinout, orientation, length suitability |
| Network switch | Steloproad 3-port Gigabit PoE switch, 12–48 V advertised | **Selected; purchase unconfirmed** | Actual port count, 12 V input and PoE output capability |
| Lighting | BTF-LIGHTING 12 V, 4000 K COB LED strip | **Selected; purchase unconfirmed** | Two ~500 mm stationary segments, wiring |
| Gantry structure | Independent CoreZB overhead camera XY; 3030 extrusion | **Planned** | Rail length, motor brackets, alignment |
| Motors and drivers | CoreZB stepper pair, drivers | **Not finalized** | Torque, controller allocation, supply |
| Belts, pulleys, idlers | GT2/CoreXY-style | **Planned** | Belt width, geometry, tensioning |
| Linear guides | Rails and carriages | **Not finalized** | Exact size/length |
| Camera mount | Rigid, adjustable mount | **Planned** | Tilt and optical offset calibration |
| Display | 7-inch 1280×720 landscape touchscreen | **Specified; purchase unconfirmed** | Actual display model, touch connection |
| Display host | Ethernet-connected browser-capable SBC | **Planned** | Model, power, browser performance |
| Network cabling | Cat6A ~10 ft, drag-chain-rated option | **Discussed; purchase unconfirmed** | Flex rating, cable routing |
| PoE injector | Standalone PoE injector | **Considered** | May not be needed with suitable switch |
| Power conversion | 12 V fused distribution, 5 V buck as needed | Existing distribution; additions planned | Load and protection calculations |
| Calibration targets | Black center and perimeter circles referenced to embedded magnets | **Proposed** | On rigid rotating surface; removable magnets only for placement |

## 3. Other camera alternatives discussed

| Hardware | Status | Notes |
|---|---|---|
| Arducam Raspberry Pi Camera Module 3 | **Explicitly reported owned** | Does not establish compatibility with ESP32-P4 |
| Raspberry Pi Zero 2 W | Considered | Earlier Tailscale remote camera idea |
| SparkFun ESP32-P4 PoE board | Considered | Alternative to Waveshare |
| 75° and 120° FOV lenses | Considered | Final FOV not fixed |
| 4-port / larger Ethernet switch | Considered | Four network endpoints may require more ports |

## 4. Purchase reconciliation — not yet verified

Check receipts or delivered parts before changing any selection to **Purchased**:

- [ ] Waveshare ESP32-P4 board — exact model / quantity / order date
- [ ] OV5647 adjustable-focus camera — exact model / quantity / order date
- [ ] 200 mm CSI cable — connector details / order date
- [ ] Steloproad PoE switch — exact listing / number of usable ports
- [ ] BTF-LIGHTING COB LED strip — length / color temperature
- [ ] 3030 extrusions, rails, belts, pulleys, motors and drivers
- [ ] Cat6A and drag-chain Ethernet cable
- [ ] 7-inch 1280×720 display and browser host
- [ ] Buck converters, fuses, fasteners and brackets

## 5. Integration checks

1. Count Ethernet endpoints: PC, RP23CNC, ESP32-P4 and display host. Confirm switch ports before buying.
2. Verify 12 V switch input and whether it can actually supply required PoE at that input.
3. Confirm exact ESP32-P4 CSI driver and OV5647 compatibility before committing to cable/mount.
4. Confirm camera exposure timestamp can be associated with camera gantry pose and θ pose.
5. Distinguish encoder/motor command resolution from independently measured position accuracy.
6. Preserve original receipts/part numbers and record installed revision once confirmed.
