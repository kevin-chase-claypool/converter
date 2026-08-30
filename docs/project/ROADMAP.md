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
- [x] Create categorized, indexed change histories for Windows software, RP23CNC software, and hardware.
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
- [ ] Measure N20 motor no-load and current-limited stall current. (`E-05` passed; `E-06` remains)
- [ ] Calibrate the 300 g load cell through the HX711. (`E-07`)
- [ ] Measure usable HX711 sample rate and noise. (`E-08`)
- [ ] Verify TMAG5273 readings with the intended magnet and geometry. (`E-09`)
- [ ] Verify Pololu D36V50F6 input/output polarity and fixed 6.0 V output. (`E-14`)
- [ ] Inspect the completed toolhead perfboard, JST input, and Pro Micro-to-DRV8833 logic wiring unpowered. (`E-14B`)
- [ ] Verify ACEIRMC DRV8833's existing GP7→`ULT` sleep and GP6←`EEP` fault mapping in firmware, then inspect the `J2` bridge. (`E-14C`)
- [ ] Characterize Pololu D36V50F6 voltage, ripple, current, and temperature with actuator load. (`E-15`)
- [ ] Characterize toolhead-mounted Pololu S7V8F5 5.0 V output with RP2350/sensors active and actuator moving. (Motor-only portion of `E-15A` passed; sensor portion remains.)
- [ ] Complete the measured power budget.
- [ ] Select branch fuses, wire gauges, connectors, and distribution hardware.
- [ ] Update every affected master-wiring-table row with evidence.

## Phase 2: controller baseline

- [x] Confirm RP23CNC soldering/continuity inspection passed before power. (`E-17`; passed 2026-08-14)
- [x] Record the exact RP23CNC board revision. (`RP23U5XBB V1.01`; 2026-06-09 board inspection lab note)
- [ ] Build or obtain current RP23CNC-compatible grblHAL firmware.
- [ ] Archive the exact source commits, board target, plugins, and build options.
- [x] Flash and identify the expected firmware. (`F-01`; passed 2026-08-14)
- [ ] Confirm USB communication.
- [ ] Confirm Ethernet communication if required.
- [x] Confirm converter G-code subset parsing. (`F-02`; passed 2026-08-14)
- [x] Confirm unpowered STEP/DIR output pins and polarity. (`F-03`; passed 2026-08-14)
- [ ] Confirm limit input behavior and polarity. (`F-04`)
- [ ] F-04 temporary-switch harness: verify X/Y roller switches with short leads before permanent drag-chain routing.
- [ ] Measure the drawer-side drag chain's internal envelope and bend radius against every planned moving cable; replace it if the 4C shielded cable plus the remaining required conductors cannot move freely with margin.
- [ ] Design CAD strain-relief features for the X, Y, and A motor wire harnesses. Acceptance: each feature grips the harness cable jacket rather than individual conductors, preserves bend radius and service slack, prevents terminal load under normal motion, and keeps the X PE sheath termination electrically and mechanically undisturbed.
- [ ] Confirm M3/M5 tool output behavior. (`F-05`)
- [ ] Verify B07WFGTNQC optocoupler channel direction, polarity, input current, output-side 3.3 V compatibility, and safe RP2350 logic levels before wiring `M3/M5` or `HOME_ARM`.
- [ ] Save a complete `$` settings dump and verify persistence. (`F-06`)

## Phase 3: single-axis motion

- [ ] Verify each TB6600's current and microstep configuration. Baseline: X/Y 16 microsteps and A 8 microsteps, all at 1.5 A/phase; the 12:1 A drive is 19,200 pulses per bed revolution.
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

- [x] Finalize toolhead controller placement: use the toolhead-mounted SparkFun
  Pro Micro RP2350 for pressure control and TMAG5273 sensing/output (ADR-002).
- [ ] Verify open-loop actuator direction and safe travel. (`T-01`)
- [x] Implement commissioning-gated BOOT, LIFT, SEEK_CONTACT, HOLD_FORCE, and FAULT states in source. (2026-08-22 compile; bench verification remains.)
- [x] Add source-level core heartbeat, seek-timeout, sensor, driver, and force-limit faults. (2026-08-22 compile; installed verification remains.)
- [ ] Establish the motor/preload physical control envelope, including spring force curve, actuator hold/retract reserve, pulse response, LIFT-home repeatability, and safe controller limits. (`T-01A` through `T-01G`)
- [ ] Characterize actuator backlash and response.
- [ ] Implement bounded contact seek. (`T-02`)
- [ ] Implement proportional or PI force control at the measured sensor rate. (`T-03`)
- [ ] Verify missing-paper fault. (`T-04`)
- [ ] Verify overforce fault. (`T-05`)
- [ ] Verify sensor-disconnect fault. (`T-06`)

## Phase 6: system integration

- [x] Implement the locked P100 physical-home, centroid-raster, and A-registration macro source. (2026-08-22 static validation; F-08/M-08/M-09 remain.)
- [x] Implement the dual-core GP28/GP27 readiness and magnetic-state protocol without adding drag-chain wires. (2026-08-22 compile; E-18 remains.)
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
