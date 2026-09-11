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
- [x] Measure N20 motor no-load and current-limited stall current. (`E-05` passed; bounded `E-06` passed at 6.0 V / 0.20 A limit / 0.18 A stall with 10 repeats; thermal characterization remains separate)
- [ ] Calibrate the 300 g load cell through the HX711. (`E-07`)
- [ ] Measure usable HX711 sample rate and noise. (`E-08`)
- [ ] Verify TMAG5273 readings with the intended magnet and geometry. (`E-09`)
- [x] Verify Pololu D36V50F6 input/output polarity and fixed 6.0 V output. (`E-14`; 6.05 V constant, 2026-09-08)
- [x] Inspect the completed toolhead perfboard, JST input, and Pro Micro-to-DRV8833 logic wiring unpowered. (`E-14B`; passed 2026-09-08)
- [x] Verify ACEIRMC DRV8833's existing GP7→`ULT` sleep and GP6←`EEP` fault mapping in firmware, then inspect the `J2` bridge. (`E-14C`; passed 2026-09-08)
- [ ] Characterize Pololu D36V50F6 voltage, ripple, current, and temperature with actuator load. (`E-15`)
- [x] Characterize toolhead-mounted Pololu S7V8F5 5.0 V output with RP2350/sensors active and actuator moving. (`E-15A`; owner reported prior TMAG test passed, 2026-09-08.)
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

- [x] Correct the converter's production defaults and self-contained program
  preamble: non-Z M3/M5 mode plus explicit `G21 G90 G94 G17 G54`.
- [ ] Re-run F-02 with a newly generated default file before allowing ioSender
  direct-stream operation.
- [ ] Repeat driver and motor bring-up for X, Y, and A.
- [x] Determine and calibrate X/Y steps per millimeter. (`M-03`; Y: 2026-09-05,
  X: 2026-09-06)
- [x] Implement radius-aware A-axis feed planning in the converter so a target
  tangential writing speed remains bounded as pen radius changes; the software
  handles the 12:1 motor-degree contract, combined XY/A feed, controller caps,
  and the near-center limit. (2026-09-05; M-06 hardware validation remains.)
- [ ] Set A steps per motor-shaft degree. (`M-04`)
- [ ] Verify the 12:1 bed ratio. (`M-05`)
- [ ] Tune max rate and acceleration one axis at a time.
- [ ] Complete M-07 hard/soft-limit behavior. X/Y physical homing passed on
  2026-09-06 with a repeatable XY-only cycle. The conservative X/Y software
  envelope (`$130=455`, `$131=446`, `$20=$40=1`) was enabled on 2026-09-07;
  controlled boundary rejection/recovery and production G54 registration remain
  open. (`M-07`)
- [ ] Complete M-06 coordinated X/Y/A validation. Initial pen-free symmetric
  repeatability smoke test passed through `F20000` on 2026-09-06, and the
  pen-free converter-generated house-and-sun sample returned exactly to G54
  `X0 Y0 A0` on 2026-09-07. The 2026-09-08 controlled radius sweep also
  reportedly completed perfectly and returned exactly to all G54 reference
  marks. Its actual 1:15.05 motion interval was 2.14× faster than the 2:40.58
  preview; the converter now applies their `0.467368` ratio as a display-only
  motion-time calibration. A like-for-like repeat or per-radius elapsed times
  remain before further estimator refinement. The converter now centers SVG output at G54 zero
  and the replacement sample exercises both A directions. (`M-06`)
- [x] Run a pen-free converter-generated sample G-code. (House-and-sun sample
  passed 2026-09-07; it does not replace the controlled M-06 radius sweep.)
- [ ] **Post-M-06 converter refinement — time-optimal X/Y/A candidate cost.**
  The current theta candidate selector minimizes a weighted combined-distance
  cost across X, Y, and A motor degrees; it does not yet rank alternatives by
  measured per-axis rate/acceleration limits and grblHAL look-ahead behavior.
  After M-06 records those observations, evaluate candidate orientations by
  predicted coordinated block time. Preserve the 12:1 A motor-degree contract,
  output geometry, and existing safe caps. Acceptance: representative
  inner/mid/outer-radius paths show no lost steps or geometry change, and the
  predicted ordering agrees with measured elapsed time within a documented
  tolerance.

## Phase 5: toolhead

- [x] Finalize toolhead controller placement: use the toolhead-mounted SparkFun
  Pro Micro RP2350 for pressure control and TMAG5273 sensing/output (ADR-002).
- [ ] Verify open-loop actuator direction and safe travel. (`T-01`)
- [x] Implement commissioning-gated BOOT, LIFT, SEEK_CONTACT, HOLD_FORCE, and FAULT states in source. (2026-08-22 compile; bench verification remains.)
- [x] Add source-level core heartbeat, seek-timeout, sensor, driver, and force-limit faults. (2026-08-22 compile; installed verification remains.)
- [ ] Establish the motor/preload physical control envelope, including spring force curve, actuator hold/retract reserve, global pulse bounds, per-tool response checks, LIFT-home repeatability, and safe controller limits. (`T-01A` through `T-01J`)
- [ ] Characterize actuator backlash and response.
- [ ] Implement bounded contact seek. (`T-02`)
- [ ] Implement proportional or PI force control at the measured sensor rate. (`T-03`)
- [ ] Verify missing-paper fault. (`T-04`)
- [ ] Verify overforce fault. (`T-05`)
- [ ] Verify sensor-disconnect fault. (`T-06`)

## Phase 6: system integration

- [x] Implement the locked P100 physical-home, centroid-raster, and A-registration macro source. (2026-08-22 static validation; F-08/M-08 remain. The non-registering M-09 P112 survey passed physical center verification on 2026-09-11; its verified stationary stop was manually recorded as G54 A0. Q5 then returned to the center and a manual pen-offset G54 write plus `G54 G0 X0 Y0` visually verified pen-at-center. Automatic registration remains locked until P111/Q5/P112 replace the stale combined path.)
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

Re-run F-02 with a newly generated default converter file. Then complete the
converter-generated M-06 inner/mid/outer-radius timing and geometry check on
installed grblHAL. Do not enable direct P100-to-print operation until its
commissioning and toolhead gates also pass.
