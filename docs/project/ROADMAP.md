# Project Roadmap

## Status

| Phase | State | Exit condition |
|---|---|---|
| 0. Repository organization | complete | AI entry point, interfaces, BOM, roadmap, and test structure exist |
| 1. Electrical characterization | next | Received components measured and compatibility gates resolved |
| 2. RP23CNC/grblHAL baseline | pending | Board flashes, accepts commands, and toggles unpowered axis outputs |
| 3. Single-axis motion | pending | One motor homes and moves repeatably at conservative settings |
| 4. Three-axis motion | pending | X/Y/A calibrated and coordinated sample G-code runs without a tool |
| 5. Toolhead bench loop | pending | Lift, seek, force hold, and faults work independently |
| 6. System integration | pending | M3/M5 controls toolhead and a calibration drawing completes |
| 7. Validation/report | pending | Measurements, plots, photos, results, and limitations are documented |

## Phase 1: electrical characterization

- Identify exact board and module revisions.
- Measure stepper coil pairs and resistance.
- Document TB6600 switch tables and input behavior from the received units.
- Measure N20 motor no-load current and current under a safely limited stall test.
- Calibrate the 300 g load cell through the HX711.
- Measure usable HX711 sample rate and noise.
- Verify TMAG5273 readings with the intended magnet and geometry.
- Complete the power budget and wiring diagram.

## Phase 2: controller baseline

- Build or obtain the current RP23CNC-compatible grblHAL firmware.
- Archive the exact source commit/build options.
- Confirm USB, then Ethernet if required.
- Confirm axis pin mapping and limit input polarity.
- Save a complete `$` settings dump.

## Phase 3-4: motion

- Bring up one driver and motor with no mechanics attached.
- Set conservative current and microstepping.
- Determine steps/mm for X/Y from pulley or leadscrew geometry.
- Set A steps/degree using motor-shaft degrees.
- Tune max rate and acceleration one axis at a time.
- Add homing and soft limits.
- Run short parser tests, then coordinated X/Y/A tests.

## Phase 5: toolhead

- Implement the state machine before PID control.
- Add hard travel/timeout and force-limit faults.
- Characterize actuator direction, backlash, and response.
- Start with proportional or PI control at a bandwidth supported by the measured sensor rate.
- Compare a grblHAL plugin/core-1 implementation against a separate MCU based on timing, pin availability, and maintenance risk.

## Phase 6-7: integration and report

- Connect M3/M5 to LIFT/ENGAGE.
- Validate fixed dwell timing.
- Draw a square, circle, center cross, and theta-heavy pattern.
- Compare commanded and measured dimensions.
- Compare estimated and actual execution times.
- Record force error during straight, curved, and bed-rotation moves.
- Document failures and design changes, not only the final successful configuration.

## Next concrete task

Complete the Phase 1 bench worksheet in
`docs/testing/TEST_PLAN.md` before connecting motors or the toolhead to RP23CNC.
