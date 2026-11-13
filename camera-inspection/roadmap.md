# Implementation roadmap and unresolved engineering questions

## Phase 0 — Inventory and verification
- [ ] Inspect current converter repository and ioSender fork structure before coding.
- [ ] Confirm RP23CNC/grblHAL axes, free axis allocation, controller limits and CoreZB motion-controller architecture.
- [ ] Verify exact ESP32-P4-ETH, OV5647 module/connector, driver support, memory, and achievable camera formats.
- [ ] Verify network switch ports, 12 V input and PoE module compatibility.
- [ ] Establish mechanical drawings, bed dimensions, camera field of view, working distance and lighting.

## Phase 1 — CoreZB motion and networking
- [ ] Build/harden camera gantry; home repeatedly; measure positional repeatability.
- [ ] Bring up camera and Ethernet streaming.
- [ ] Implement timestamped camera gantry pose reporting.
- [ ] Test power, EMI, cable chain and Ethernet reliability.

## Phase 2 — Host integration
- [ ] Fork ioSender V2 and inspect code paths for grblHAL status, feed override, jog and streaming.
- [ ] Add a safe authenticated browser-facing service; keep one motion-control authority.
- [x] Deliver the 720×1280 portrait UI with persistent DRO and
  Home/Run/Jog/Tools/Inspect navigation, then deploy it to the RPI4-HMI
  Chromium kiosk (`RPSW-20261113-001`). Camera and machine values remain
  demo/placeholder data.
- [ ] Connect the deployed HMI to a safe authenticated status/command service,
  live camera preview, and real progress/fault state.
- [ ] Define a post-print scan command and scan-tile pose capture; no live pen-exposure synchronization required for the initial design.

## Phase 3 — Metrology and inspection
- [ ] Calibrate optics and paper-plane projection.
- [ ] Implement center/index optical target detection.
- [ ] Fit multi-angle perimeter target orbit and quantify repeatability.
- [ ] Detect ink and compare to executed reference geometry.
- [ ] Benchmark ESP32-P4 vs host CV processing.
- [ ] Display expected/actual/deviation layers and quantitative error metrics.

## Phase 4 — Compensation and validation
- [ ] Independently validate actual angular accuracy and XY center estimates.
- [ ] Diagnose and mechanically fix nonrepeatable errors.
- [ ] Build correction table(s) for verified repeatable errors.
- [ ] Apply compensation in one chosen layer only.
- [ ] Run blind held-out test patterns and document before/after performance.

## Open questions
- Does CoreZB use the same grblHAL controller or a second synchronized controller?
- How are θ and camera pose timestamped at exposure?
- Is the paper attached rigidly to the rotating bed, and are calibration circles permanent on bed or removable calibration sheet?
- What target inspection tolerance (mm), field of view, and throughput are required?
- Can ESP32-P4 process selected ROIs at the needed rate, or is host processing required?
- What machine-specific feed, homing, pause, pen-change and ETA actions are actually exposed by ioSender?
- How will errors be distinguished from pen stroke width, paper slip and bed tilt?

## Design principles
- Measure before compensating.
- Preserve raw data and uncertainty.
- Keep sample UI values separate from real telemetry.
- Validate on measurements not used for fitting.
- Treat all performance figures as hypotheses until tested.

## Post-print correction cycle (preferred)
- [ ] Print a known calibration pattern without camera interruptions.
- [ ] Scan the completed sheet in overlapping stationary tiles with the bed at a known angle.
- [ ] Register/stitch imagery into paper coordinates; compare measured ink centerlines with expected toolpath.
- [ ] Separate repeatable machine errors from pen/paper/random errors using repeated test prints.
- [ ] Fit and version a correction profile for the SVG-to-G-code converter; do not automatically compensate every observed discrepancy.
- [ ] Test corrected G-code on new patterns and compare before/after errors independently.
- [ ] Keep continuous inspection as a later optional research milestone.
