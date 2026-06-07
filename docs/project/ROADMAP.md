# Project Roadmap

## Checklist rules

- `[ ]` means not completed or not yet verified.
- `[x]` means completed with evidence.
- Check a phase gate only when its exit condition and every required task are complete.
- Link completed hardware/test tasks to a test ID, lab note, measurement, photo, or commit.
- Partial work stays unchecked; explain partial status in the engineering log.

## Phase gates

- [x] **Phase 0 - Repository organization**
  Exit: AI entry point, engineering log, interfaces, BOM, wiring table, roadmap,
  tests, firmware placeholders, and report structure exist.
- [ ] **Phase 1 - Electrical characterization**
  Exit: Received components are measured and compatibility gates are resolved.
- [ ] **Phase 2 - RP23CNC/grblHAL baseline**
  Exit: Board flashes, accepts commands, and toggles unpowered axis outputs.
- [ ] **Phase 3 - Single-axis motion**
  Exit: One motor homes and moves repeatably at conservative settings.
- [ ] **Phase 4 - Three-axis motion**
  Exit: X/Y/A are calibrated and coordinated sample G-code runs without a tool.
- [ ] **Phase 5 - Toolhead bench loop**
  Exit: Lift, seek, force hold, and faults work independently.
- [ ] **Phase 6 - System integration**
  Exit: M3/M5 controls the toolhead and a calibration drawing completes.
- [ ] **Phase 7 - Validation and report**
  Exit: Measurements, plots, photos, results, failures, and limitations are documented.

## Phase 0: repository organization

- [x] Create a single AI/contributor entry point.
- [x] Define the system architecture and subsystem boundaries.
- [x] Create the hardware BOM.
- [x] Create the authoritative master wiring table.
- [x] Create the integration interface contract.
- [x] Create the test plan and lab-note template.
- [x] Create the chronological engineering log containing successes and struggles.
- [x] Create firmware configuration and toolhead-control placeholders.
- [x] Push the organized project to GitHub.

## Phase 1: electrical characterization

- [ ] Inventory and photograph the RP23CNC Assembly and Ethernet Kits and PCB revision. (`E-16`)
- [ ] Solder and inspect required RP23CNC connectors and Ethernet components. (`E-17`)
- [ ] Identify and photograph exact driver, sensor, and module revisions.
- [ ] Verify MEISHILE S-120-12 terminal labels and protective-earth continuity. (`E-11`)
- [ ] Measure S-120-12 no-load output and adjustment range. (`E-11`)
- [ ] Measure stepper coil pairs and resistance. (`E-01`)
- [ ] Document TB6600 switch tables and input behavior from the received units. (`E-02`, `E-03`)
- [ ] Measure N20 motor no-load and current-limited stall current. (`E-05`, `E-06`)
- [ ] Calibrate the 300 g load cell through the HX711. (`E-07`)
- [ ] Measure usable HX711 sample rate and noise. (`E-08`)
- [ ] Verify TMAG5273 readings with the intended magnet and geometry. (`E-09`)
- [ ] Configure the B085T73CSD buck to 6.0 V and record display error. (`E-14`)
- [ ] Characterize buck voltage, ripple, current, and temperature with actuator load. (`E-15`)
- [ ] Complete the measured power budget.
- [ ] Select branch fuses, wire gauges, connectors, and distribution hardware.
- [ ] Update every affected master-wiring-table row with evidence.

## Phase 2: controller baseline

- [ ] Confirm RP23CNC soldering/continuity inspection passed before power. (`E-17`)
- [ ] Record the exact RP23CNC board revision.
- [ ] Build or obtain current RP23CNC-compatible grblHAL firmware.
- [ ] Archive the exact source commits, board target, plugins, and build options.
- [ ] Flash and identify the expected firmware. (`F-01`)
- [ ] Confirm USB communication.
- [ ] Confirm Ethernet communication if required.
- [ ] Confirm converter G-code subset parsing. (`F-02`)
- [ ] Confirm unpowered STEP/DIR output pins and polarity. (`F-03`)
- [ ] Confirm limit input behavior and polarity. (`F-04`)
- [ ] Confirm M3/M5 tool output behavior. (`F-05`)
- [ ] Save a complete `$` settings dump and verify persistence. (`F-06`)

## Phase 3: single-axis motion

- [ ] Verify one TB6600 current and microstep configuration.
- [ ] Connect one motor without mechanics attached.
- [ ] Complete low-speed jog test. (`M-01`)
- [ ] Measure motor and driver temperature.
- [ ] Ramp rate and acceleration to find a stable operating limit. (`M-02`)
- [ ] Configure a conservative margin below the measured limit.
- [ ] Install and verify that axis's home/limit switch.

## Phase 4: three-axis motion

- [ ] Repeat driver and motor bring-up for X, Y, and A.
- [ ] Determine and calibrate X/Y steps per millimeter. (`M-03`)
- [ ] Set A steps per motor-shaft degree. (`M-04`)
- [ ] Verify the 12:1 bed ratio. (`M-05`)
- [ ] Tune max rate and acceleration one axis at a time.
- [ ] Add and verify homing and soft limits. (`M-07`)
- [ ] Run short coordinated X/Y/A parser and motion tests. (`M-06`)
- [ ] Run converter-generated sample G-code without the tool installed.

## Phase 5: toolhead

- [ ] Finalize toolhead controller placement: RP2350 plugin/core 1 or separate MCU.
- [ ] Verify open-loop actuator direction and safe travel. (`T-01`)
- [ ] Implement BOOT, LIFT, SEEK_CONTACT, HOLD_FORCE, and FAULT states.
- [ ] Add hard travel, seek-timeout, sensor, and force-limit faults.
- [ ] Characterize actuator backlash and response.
- [ ] Implement bounded contact seek. (`T-02`)
- [ ] Implement proportional or PI force control at the measured sensor rate. (`T-03`)
- [ ] Verify missing-paper fault. (`T-04`)
- [ ] Verify overforce fault. (`T-05`)
- [ ] Verify sensor-disconnect fault. (`T-06`)

## Phase 6: system integration

- [ ] Connect grblHAL M3/M5 to toolhead ENGAGE/LIFT.
- [ ] Verify reset and E-stop leave the toolhead safe.
- [ ] Validate fixed G4 lift and engage dwell timing.
- [ ] Verify toolhead workload does not cause lost steps or unacceptable jitter.
- [ ] Complete a calibration drawing.
- [ ] Complete a theta-heavy drawing.

## Phase 7: validation and report

- [ ] Compare commanded and measured calibration-pattern dimensions.
- [ ] Compare estimated and actual execution times.
- [ ] Record force error during straight, curved, and bed-rotation moves.
- [ ] Photograph the final wiring and mechanical configuration.
- [ ] Archive final firmware build record, pin map, and settings.
- [ ] Summarize successful implementations.
- [ ] Summarize struggles, failed tests, and rejected approaches chronologically.
- [ ] Document limitations and future work.
- [ ] Complete and export the Systems Integration in Robotics report.

## Next concrete task

Complete the Phase 1 bench worksheet in
`docs/testing/TEST_PLAN.md` before connecting motors or the toolhead to RP23CNC.
