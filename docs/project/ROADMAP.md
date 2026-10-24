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
- [ ] Replace the failed HX711 force-sensing path with the selected CS1238,
  then calibrate the 300 g load cell with raw data and reproducible
  final-paper figures. (`E-07C`, `E-09C`; existing `E-07` failed)
- [ ] Measure installed CS1238 sample rate and RMS noise. (`E-08C`; existing
  HX711 `E-08` is historical only)
- [ ] Verify TMAG5273 readings with the intended magnet and geometry. (`E-09`)
- [x] Verify Pololu D36V50F6 input/output polarity and fixed 6.0 V output. (`E-14`; 6.05 V constant, 2026-09-08)
- [ ] Reconfirm the completed toolhead perfboard's GP6→`EEP` sleep and `ULT` fault→GP7 behavior after the corrected firmware reflash. (`E-14B`; prior opposite-role interpretation superseded 2026-09-13)
- [ ] Function-check the confirmed DRV8833 labels: GP6→`EEP` sleep and `ULT` fault→GP7, then record J2 state. (`E-14C`; corrected mapping pending re-test)
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
- [x] Confirm M3/M5 tool output behavior. (`F-05`; 2026-09-23: the spindle
  `ENA` output is active-high by default, so the controller sets `$16=1`
  (invert spindle enable). M3 drives the pen down and M5 lifts it, with the
  pen-up fail-safe intact. `F-05A` passed 2026-09-29.)
- [ ] Verify B07WFGTNQC optocoupler channel direction, polarity, input current, output-side 3.3 V compatibility, and safe RP2350 logic levels before wiring `M3/M5` or `HOME_ARM`.
- [ ] Save a complete `$` settings dump and verify persistence. (`F-06`)

## Phase 3: single-axis motion

- [ ] Verify each TB6600's current and microstep configuration. Baseline: X/Y 16 microsteps and A 8 microsteps, all at 1.5 A/phase; the A drive is nominally 12:1 and measures 4331.97 A motor-degrees (19,253 pulses) per bed revolution.
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
  handles the 12.03324:1 motor-degree contract, combined XY/A feed, controller caps,
  and the near-center limit. (2026-09-05; M-06 hardware validation remains.)
- [ ] Set A steps per motor-shaft degree. (`M-04`)
- [x] Establish the effective bed ratio. (M-05 coarse check passed 2026-09-05;
  three P112 surveys measured 4331.97 A motor-degrees per bed revolution, now
  used as `theta_drive_ratio = 12.03324`. See `WSW-20260930-001`.)
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
  predicted coordinated block time. Preserve the 12.03324:1 A motor-degree contract,
  output geometry, and existing safe caps. Acceptance: representative
  inner/mid/outer-radius paths show no lost steps or geometry change, and the
  predicted ordering agrees with measured elapsed time within a documented
  tolerance.
- [ ] **Calibrate the residual rotating-bed centre offset.**
  Problem: opposite-quadrant portions of a rotating-bed print can separate
  because G54 X0/Y0 is a small vector `C` away from the true rotation axis;
  the returned-bed displacement is `e(theta) = C - R(-theta)C`, reaching `2C`
  at a half-turn. Benefit: the precision error can be removed at the single P100
  ownership point instead of requiring XY-only printing. The cross-replay
  generator and least-squares fitter are implemented (`WSW-20261023-002`).
  Acceptance: run `rotation-center-calibration.gcode` after `G65 P113`,
  measure the raw X/Y gaps at 90/180/270, subtract the 20 mm pair baseline,
  apply the fitted P100 constants, re-register, and show every gap returns to
  the baseline within the remaining mechanical tolerance; if fit residual
  stays above 0.20 mm, resolve bed plane/runout instead of forcing the centre
  constants. Status 2026-10-23: the first photo-derived run had a control
  within ~0.1 mm but 0.350 mm RMS / 0.412 mm max centre-model residual; P100
  remains unchanged pending bed-plane/runout separation. A 12-station balanced
  layout and companion CSV are now generated (`WSW-20261023-003`) for the
  required spatial-repeat measurement. The first dense run showed a 1.421 mm
  A=0 Y spread across positions and a centre-model maximum residual of
  0.551 mm; a second photo reproduced the spatial spread and a 0.501 mm
  maximum residual. A full-field one-pen sheet now measures A=0 spatial error,
  fixed-position 90/180/270 response, and an A=0 control at 37 stations, with
  four fiducials and isolated lanes. `tools\analyze_bed_error_calibration.py`
  validates complete measurements, correlates them with the bed mesh, performs
  leave-one-station-out validation, and emits an optional
  `theta-bed-compensation-v2` profile for the host planner. The converter
  applies that residual map to saved G-code after theta planning and P100
  registration, supports exact compensated preview, rejects uncovered artwork,
  and caps each correction at 5 mm (`WSW-20261023-004`). Fast interactive
  preview now displays nominal X/Y by default (`WSW-20261023-007`). The first
  full-field photo resolved all 189 markers: A=0 spatial error was 0.292 mm RMS
  / 0.537 mm maximum, leave-one-station-out profile prediction was 0.197 mm RMS
  / 0.552 mm maximum with 66.1 % improvement, and the fitted profile passed the
  software gates at a 1.331 mm worst correction. The bed mesh has mixed correlations
  (A=0 Y `r=-0.548`, 90-degree `r=-0.574`, 270-degree `r=+0.744`), so both
  position and rotation/height coupling remain physically credible. The first
  compensated print then failed and exposed a bed-to-machine frame-rotation
  defect: profile `911d2694c8c9` increased overall RMS from 0.581 to 1.169 mm
  and approximately doubled the 180-degree error while leaving A=0 nearly
  unchanged. The analyzer now rotates every correction by its bed angle; the
  corrected profile is `2cdf3731de4a`. P100 stays unchanged.
  The next attempted verification was invalid because the sheet was retaped to
  address a bubble after printing began; marker extraction could not assign all
  185 stations within a safe local radius. A final stationary verification
  sheet then passed every acceptance gate: overall station RMS fell from
  `0.581` to `0.338 mm`, maximum from `1.309` to `0.752 mm`, and error by
  `41.9 %`; 90/180/270 RMS fell to `0.278/0.389/0.353 mm`. Profile
  `2cdf3731de4a` is accepted for the current machine configuration. P100 and
  its registration remain unchanged. The localized residual at station 09/14,
  A=270 does not justify fitting the verification sheet again; physical bed
  plane/runout work remains optional unless an application requires less than
  the accepted approximately `0.34 mm` RMS residual.
- [ ] **Verify the extrapolated 13.5-inch compensation annulus.**
  Problem: the default `4c8270de8a74` profile extends the accepted 165.1 mm
  correction field to 171.45 mm by local-affine extrapolation. Its
  `1.054 mm` boundary correction is below the safety bound, but the outer
  6.35 mm annulus has no compensated verification print. Benefit: precision
  work can use the full 13.5-inch diameter with a measured error bound rather
  than an extrapolation assumption. Risk: continuing to treat extrapolated
  values as verified can hide a local edge or rotation/height response.
  Acceptance: print a stationary edge-band verification covering 165.1 to
  171.45 mm at 0/90/180/270 degrees, measure it with the existing photo
  pipeline, and show at most `0.35 mm` RMS / `0.90 mm` maximum with no angle
  stage more than `0.05 mm` worse than the inner field.
- [ ] **Optimize exact compensation subdivision for dense artwork.**
  Problem: a combined 8,699-contour CMYK preview spends most of its time in
  `compensation_step_count`, which evaluates the local-affine correction 16
  times per segment even when almost every segment needs no extra subdivision.
  The 100-contour sample required only three extra subdivisions across 7,466
  probes but took 4.9 seconds instead of 0.06 seconds. Benefit: exact preview
  and saved G-code become responsive for photo-screen and vector-trace work.
  Risk: skipping or coarsening curvature probes can under-subdivide a move and
  let the compensation field bow beyond the path tolerance. Acceptance: exact
  preview and G-code retain their current points within a documented
  sub-tolerance numerical bound, a dense 8,699-contour benchmark completes
  materially faster, and regression coverage includes both constant and
  sharply varying correction fields.
  Status 2026-10-23: a four-point early-out with the original 16-point
  fallback now preserves every subdivision count across a 15,694-segment
  real-field sample while cutting probe time `8.838 -> 2.673 s` (`3.31x`) and
  a 100-contour exact move build `4.891 -> 2.423 s` (`2.02x`). The remaining
  opportunity is replacing repeated local-affine lookup with a triangulated or
  precomputed table, then measuring a complete dense save.

## Phase 5: toolhead

- [x] Finalize toolhead controller placement: use the toolhead-mounted SparkFun
  Pro Micro RP2350 for pressure control and TMAG5273 sensing/output (ADR-002).
- [ ] Verify open-loop actuator direction and safe travel. (`T-01`)
- [x] Implement commissioning-gated BOOT, LIFT, SEEK_CONTACT, HOLD_FORCE, and FAULT states in source. (2026-08-22 compile; bench verification remains.)
- [x] Add source-level core heartbeat, seek-timeout, sensor, driver, and force-limit faults. (2026-08-22 compile; installed verification remains.)
- [ ] Establish the motor/preload physical control envelope, including spring force curve, actuator hold/retract reserve, global pulse bounds, per-tool response checks, LIFT-home repeatability, and safe controller limits. (`T-01A` through `T-01J`)
- [ ] Characterize actuator backlash and response.
- [ ] Hardware-validate the supervised bounded two-touch home-origin seek. Source finds light surface contact using 25 ms pulses while far away then 5 ms pulses, backs off 10 ms, and fine-tunes drawing force using only 5 ms pulses, with force, switch, pulse-count, and time limits. (`T-02`, `T-01J`)
- [ ] Hardware-validate the moving-average, bounded 5 ms pulse force hold through stationary and moving T-03 cases. (`T-03`)
- [ ] Verify missing-paper fault. (`T-04`)
- [ ] Verify overforce fault. (`T-05`)
- [ ] Verify sensor-disconnect fault. (`T-06`)

## Phase 6: system integration

- [x] Implement and hardware-verify the P113 unified physical-home, centroid-raster, and A-registration macro source. (2026-09-11: P113 performs the verified M5/dwell/P111/P100-Q0 sequence. Q0 uses P111/Q5/P112 geometry, defers G54 writes, and parks the pen at center. The P113 run completed without alarm and visually centered the pen. Q3/Q4 remain locked.)
- [x] Implement the dual-core GP28/GP27 readiness and magnetic-state protocol without adding drag-chain wires. (2026-08-22 compile; E-18 remains.)
- [x] Verify P113 end to end on the production integrated toolhead firmware. (2026-09-24: `MAGNETIC_CALIBRATION_VALID = true` build ran the full P100 Q0 to completion and wrote G54 `-232.136,-189.980,0.000,5649.193` from a center centroid at `MPos:-232.138,-219.475`; the operator then confirmed the parked pen tip perfectly centered over the magnet. E-18/M-08/M-09 accepted. See `RPSW-20260924-001`.)
- [ ] **Arm-watchdog headroom.** An earlier P113 attempt faulted at exactly `MAG_MAX_ARM_TIME_MS` (300000 ms) after `SCAN_ACTIVE` armed, because the 21-row 100 mm raster needed about 172 s just to reach the magnet. Acceptance: unattended `G65 P113` completes with the magnet found at the worst-case raster position, either by raising the toolhead watchdog with a stated safety rationale or by shortening the raster (row pitch, scan square, or feed) and re-recording the run.
- [x] **Re-derive the outer A index spacing budget.** Done 2026-09-30: three surveys (`4331.818` on 2026-09-11, `4331.930` on 2026-09-24, `4332.153` on 2026-09-30; total spread 0.335) set the P100/P112/P103 gate to `4332 +/- 10`, and the converter now emits A with the measured `theta_drive_ratio = 12.03324`. Evidence: `WSW-20260930-001` and the 2026-09-30 P112 lab note.
- [ ] Connect grblHAL M3/M5 to toolhead ENGAGE/LIFT.
- [ ] **Fix and re-verify the manual `PEN UP + PARK` macro.** The first press on
  2026-09-30 drove the gantry into the `-Y` end: `G53 G0 Y-436` ran with no
  machine frame, so it travelled the whole commanded distance from an unknown
  position. `P116` now runs `G65 P111` before the park and no longer risks a
  spurious magnetic arm when the pen is already at GP2. Acceptance: from cold
  `IDLE` the button homes X/Y and parks at `G53 X-10 Y-436` with the pen clear,
  no drag, and no alarm; an out-of-envelope target raises `Alarm:2` instead of
  moving; a stuck or faulted toolhead raises `error[39]` before any gantry
  move; and the press is safe while the pen is at contact. See
  `RPSW-20260930-003` and `RPSW-20260930-004`.
- [ ] Verify reset and E-stop leave the toolhead safe.
- [ ] Validate fixed G4 lift and engage dwell timing.
- [ ] Verify toolhead workload does not cause lost steps or unacceptable jitter.
- [ ] Complete a calibration drawing.
- [ ] Complete a theta-heavy drawing.
- [ ] **Isolate and remove magenta wave-screen striation, then re-qualify
  700 mm/min drawing.**
  Problem: the compensated CMYK yellow wave screen showed striations at the
  programmed 700 mm/min; a 65 % override (`455 mm/min`) appeared to eliminate
  them. Magenta still shows severe striations at an even lower 60 % override
  (`420 mm/min`), especially on the subject's right face, so slow feed is not a
  general fix and a rate-dependent bed/A effect is not yet isolated. Benefit:
  quality plotting can return to 700 mm/min once the limiting subsystem is
  identified, instead of carrying a 30-35 % throughput penalty. The next
  discriminating test is the same magenta layer in XY-only at 420 mm/min.
  Risk: a stronger motor can mask rather than remove belt, bearing, carriage, or
  pen-drag dynamics; a clean print alone does not establish the limiting cause.
  The owner reports that the replacement is the same motor model already
  installed on Y and is not yet installed. Acceptance: record the installed
  motor identity, direction/current/temperature, A repeatability, bed-ratio
  marker, and first-try M3 contact; then repeat the same yellow and magenta
  layers at 700 mm/min. If either striates, use the M-13 XY-only and feed ladder
  to identify whether rotation, X/Y motion, or ink/screen behavior limits it.
  Evidence:
  `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`.

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

## Known technical debt

- [ ] Plan the four CMYK layer programs in one shared page frame.
  Problem: each per-ink SVG is recentered on its own contour bounding box, so
  unequal ink coverage shifts the four saved passes apart (reproduced at
  132 x 137 mm on an asymmetric test image at the shipped 280 % artwork
  scale). The preview plans one combined SVG, so it looks aligned.
  Benefit: the four files align by construction, independent of ink coverage
  and scale; the corner crosses then measure only real machine registration.
  Risk: a shared frame changes placement of existing CMYK output (relative to
  the page centre instead of each ink's centre); preview and per-ink saves
  must use the same anchor.
  Acceptance: an asymmetric image produces four programs with identical
  page-anchor coordinates, a bench print shows the four corner crosses
  overlapping, and a regression test covers the framing.
  Status 2026-10-20: implementation and regression tests complete
  (`WSW-20261020-001`; asymmetric 280 % reproduction now 0.00 mm anchor
  spread). Open only for the bench print of the four corner crosses.

- [ ] Bench-verify the CMYK per-pen offsets and set preflight.
  Problem: per-ink X/Y offsets, measured-cross conversion and save preflight
  are implemented (`WSW-20261023-001`), but no four-pen bench measurement
  has validated the workflow yet.
  Benefit: separates a constant pen-tip translation from frame/A/bed error
  and records a reproducible set manifest with every save.
  Risk: an offset cannot correct a fan/rotation or a moving sheet; measuring
  the crosses at centre and corners is required before trusting it.
  Acceptance: the four pens' alignment crosses agree within the remaining
  machine tolerance, a CMYK set overlays correctly, and its `-set.json`
  records the measurements and preflight results.

- [ ] Verify the heavy gantry axis under load.
  Problem: the operator reports that the Y motor carries markedly more mass than
  X or A. The converter's pen-up travels are `G0`, and grblHAL ignores the `F`
  word on a rapid, so they run at the controller's `$110`/`$111` maximum rate
  (20000 mm/min = 333 mm/s) while the preview assumes the 3000 mm/min travel
  rate - a 6.7x mismatch, on the axis with the most inertia, in the direction
  where a slip is silent at the time and shifts every row drawn afterwards.
  Benefit: either the axis is proven to hold that rate (and the mismatch is only
  cosmetic), or its limits come down to a value it can hold and the drift class
  closes for X/Y as it did for A.
  Risk: lowering `$110`/`$111` slows every rapid and makes the park move
  noticeably longer; too low and the 30-odd bed re-registration travels in a
  photo fill become the slowest part of the job.
  Acceptance: `samples/gcode/y-repeatability-test.gcode` is run at the 3000 /
  6000 / 12000 / 20000 mm/min ladder and the paired ticks at each rung coincide;
  if a rung shows a gap, `$111`/`$121` are lowered until it does not, and the
  measured ladder is recorded in a lab note and the grblHAL settings document.
  Operator action 2026-10-01: `$111` lowered to 8000 mm/min (the ladder's top
  rung then no longer matches a configured rapid; re-run the ladder to confirm).

- [x] Bring the controller's A-axis limits down to what the converter assumes.
  Problem: `$113` is 80000 motor deg/min (1333 motor deg/s, 111 bed deg/s for
  the 12:1 bed) and `$123` matches it. The converter now caps its own A rates at
  20000 motor deg/min, but controller-side rapids - jogging, homing, and the
  pure-X/Y `G0` travel the converter still emits - run at the configured rate
  and can still stall the bed and lose steps.
  Benefit: the whole system agrees on one A limit, so no path can command a rate
  the bed cannot follow.
  Risk: a lower `$113` slows every rapid that includes A; too low and a
  `theta_wrap` re-registration becomes a visible pause. The value needs a
  settings dump and a plot to confirm.
  Acceptance: `$$` shows `$113`/`$123` at or below 20000 motor deg/min (with a
  matching acceleration), a full-revolution A rapid completes without losing
  steps (a mark drawn before and after lands on itself), and the setting is
  recorded in the grblHAL document.
  Status: the "before" `$$` dump is recorded in
  [`2026-10-01-theta-a-rate-limit-lowering.md`](../report/lab-notes/2026-10-01-theta-a-rate-limit-lowering.md);
  `$113` is now `20000` (the only value that needed changing; `$123` was already
  6000) and it survived a power cycle, per `RPSW-20261001-001`.
  **Verified 2026-10-01:** `samples/gcode/a-repeatability-test.gcode` produced
  perfect circles at both r = 100 mm and r = 160 mm after two revolutions out and
  two back at the new limit, i.e. no lost motion over 104 s of continuous bed
  rotation, and the radial ticks at each station coincide.

- [ ] Sine-gradient fill follow-ups.
  Problem: `sine_gradient` is render-checked but has never been plotted, its
  amplitude curve is linear in tone with a fixed 0.04 ink floor, and its
  wavelength is locked to twice the row spacing. The row-end join that makes a
  gradient one continuous stroke covers up to two row spacings where two
  antiphase rows meet at full amplitude.
  Benefit: an on-paper judgement of the amplitude curve and of the joins, plus a
  wavelength control, turns a plausible-looking pattern into a chosen one.
  Risk: the plotter-art look is subjective; the amplitude curve and the ink
  floor are the two knobs, and changing them changes every existing gradient
  program.
  Acceptance: `samples/svg/gradient-sine-demo.svg` (or an equivalent gradient)
  is plotted at `Fill spacing 3`, the light-end banding and the row joins are
  judged from the paper, and any change to the amplitude curve or ink floor is
  recorded with the plot as evidence.

- [ ] Chain the remaining per-segment fill generators.
  Problem: `wave_region_contours` and `gyroid_region_contours` clip one segment
  at a time, so a vector-path fill arrives as one contour per clipped sample.
  `waves` and `sine_gradient` now pass their rows through
  `chain_segments_to_paths`, but `gyroid` still pays one pen cycle per segment.
  Benefit: a continuous gyroid fill and a much smaller program, with no
  geometric change - the point set is identical.
  Risk: chaining merges only contours that already share endpoints, so the
  drawing cannot change, but a future generator that emits crossing segments
  would chain them differently.
  Acceptance: `gyroid` output has the same points inside a tested square or
  circle, far fewer contours, and the existing fill tests still pass.

- [ ] `Raster px/unit` is per SVG user unit, but its label says per mm.
  Problem: the 2026-10-01 fill-spacing fix converted `Fill spacing mm` and the
  pattern sizes into user units, but `raster_px_per_unit` still multiplies the
  viewBox directly. On a 1000-unit artwork the tone raster is rendered about
  five times finer than "2 px/mm" asks for, so it costs more to draw, sample
  and hold in memory, and the tooltip describes a value the field does not hold.
  Benefit: the setting means what it says, and tone rasters stop being sized by
  the exporter's choice of user units.
  Risk: lowering the sampling resolution makes dark/light edges of the rendered
  tone coarser, which changes which wave rows carry ink at a boundary. The
  on-paper result has to be checked on a gradient before it ships.
  Acceptance: `raster_px_per_unit` is documented and implemented as pixels per
  paper millimetre (or renamed and documented as pixels per user unit), and a
  render check shows the same gradient fill before and after at a scale of 1.0.

- [ ] Kaleidoscope converter follow-ups.
  Problem: the new app traces rasters by threshold (no photo-tone shading), the
  preview has no playback, and a dragged image can leave the wedge empty with
  only the preview and log to show it.
  Benefit: photos and placement-heavy designs need fewer workarounds, and the
  main app's image-tone renderer stops being a capability only one window has.
  Risk: tone shading depends on the Qt renderer path, which currently lives in
  the main app window instead of the core.
  Acceptance: a photo imports and plots with tonal shading, an emptied wedge is
  reported as an explicit warning, and everything stays inside the typed bounds.

- [ ] **Park targets are literals pinned to the edge of the soft-limit
  envelope.**
  Problem: the converter's `park_x_machine`/`park_y_machine` defaults (`-10`,
  `-436`) and the matching `P116` target sit 5 mm inside the enforced Y end and
  exactly on the X pull-off edge. They are derived from `$130`, `$131`, `$27`,
  and the registered bed centre, so drift in any of them turns the program-end
  park into `Alarm:2`.
  Benefit: a park target that stays valid across setting drift and registration
  movement, and that never needs a hand edit in two places at once.
  Risk: the off-bed room is genuinely small - the bed edge is roughly 17 mm
  from the Y limit - so a "safer" target trades clearance for margin, and the
  choice has to be made with the bed geometry in hand.
  Acceptance: the target is derived from a fresh `$$` readout and the
  registered bed centre, its margin to each envelope edge is stated in
  `software/README.md` and `firmware/grblhal/macros/README.md`, and the
  converter and `P116` both use the stated value.

- [ ] Re-enable keep-down bridging by default once a print verifies the
  fill-trail tag.
  Problem: bridging only joins `FillTrail` contours now and ships off
  (`keep_down_bridges`), because the 2026-09-30 mandala defect showed the old
  open/closed guard could stitch artwork strokes across blank paper; no printed
  job has verified the tagged path.
  Benefit: dense fills return to one continuous zigzag, about 48 minutes saved
  on the 2026-09-30 mandala job.
  Risk: a transform that drops the tag costs pen cycles only (safe), but one
  that ever adds the tag to artwork contours would reintroduce the defect.
  Acceptance: a fill-heavy print with the option on shows no connector outside
  a filled region, and the emitted bridge count matches the preview.

- [ ] Give shape-pattern fills a boundary margin again.
  Problem: the 2026-09-27 pull-back change moved the fill bleed margin into the
  line-family clip. `dots`, `circles`, `diamonds`, `triangular`, `hexagonal`,
  `waves`, `gyroid`, and `concentric` test the region rather than clipping a
  pass, so a mark placed near the boundary can touch the outline.
  Benefit: those patterns keep the same clearance from the linework that the
  line families now have.
  Risk: testing a mark's extremities instead of its centre is a behaviour change
  for those patterns and drops marks near boundaries, thinning the tone.
  Acceptance: a placed mark's full extent lies inside the region minus the
  margin, each pattern has an identity test, and line-family output is
  unchanged.

- [ ] Index fill geometry at edge level for regions made of a few very large
  polygons.
  Problem: the 2026-09-27 polygon grid narrowed fill work by subpath count, but a
  region built from few, enormous contours still walks every edge. The spirit
  logo sample is 105 polygons totalling 83,233 points (largest 14,685) and its
  geometry stage still takes 45 s; the F15 cutaway, with 4,875 tiny polygons,
  dropped from 134 s to 1.8 s.
  Benefit: the remaining large-polygon cases become tractable, and dense solid
  fills stop being dominated by ray-casts over thousands of edges.
  Risk: two new indexes (y-band buckets for the ray-cast, an edge bounding-box
  grid for segment clipping) must stay exactly equivalent to the unindexed
  predicates; an error would shift geometry rather than crash.
  Acceptance: the same contour-identity check used on 2026-09-27 still reports
  identical output for every `samples/svg/*.svg` plus the F15 cutaway, both new
  indexes have identity tests, and the spirit logo geometry stage drops well
  below its current 45 s.

- [ ] Bring the engineering log back inside its own size and index rules.
  Problem: `docs/project/ENGINEERING_LOG.md` is 6,421 lines as of 2026-09-29
  against the roughly 1,000-line archive threshold in `AGENTS.md`, and its 88
  newest entries sit above the log's `---` separator, so the generated topic
  index does not contain them. `python tools\docs_index.py --check` still passes
  because it only compares the regenerated index against the entries below the
  separator.
  Benefit: recent entries become reachable through the topic index and the log
  matches the documented structure.
  Risk: relocating entries is a large mechanical edit, and a mistake orphans
  anchors that other documents link to.
  Acceptance: every `###` entry appears exactly once below the separator, the
  topic index links all of them, completed calendar years are archived under
  `docs/project/engineering-log/`, and `--check` passes.

- [ ] Integrate permissively licensed r/plotterart generators into the existing
  converter UI.
  Problem: the 2026-10-06 survey found 35 SVG-generating projects that are
  safe to reuse (MIT/Unlicense/CC0) plus 14 copyleft projects, but the app has
  no in-port for their features, so every one of them is a manual
  export/import job. The current UI is a three-pane layout with collapsible,
  data-driven settings groups and the Kaleidoscope app already has a tabbed
  Maps page for a vendored web tool, so the gap is features, not window
  structure.
  Benefit: squiggle, linedraw, flow-field, 3D-to-SVG, monoline-text, and path
  cleanup features become available in the app that already owns the preview
  and G-code pipeline, without a second GUI.
  Risk: license contamination (only Table A licenses may be copied; GPL tools
  stay external), vendored web bundles add size and a QtWebEngine dependency,
  and adding controls can clutter the sidebar. A new app would duplicate the
  GUI and split maintenance.
  Acceptance: one Table A generator is integrated end-to-end first
  (recommended: `linedraw` as a new Fill pattern, or SquiggleCam as a vendored
  Generators tab following the Maps-tab pattern), its license notice is
  preserved, tests cover the new path, `software/README.md` documents the
  control, and no `converter2.bat` or duplicated GUI is created. The full
  shortlist and mention evidence are in
  [`docs/research/2026-10-06-r-plotterart-svg-generators.md`](../research/2026-10-06-r-plotterart-svg-generators.md).
  Status 2026-10-06: the first batch is implemented and unit-tested as three
  tabs - Flow Field (`WSW-20261006-002`), Line Draw (`WSW-20261006-003`), and
  3D Wireframe (`WSW-20261006-004`) - with the shell from
  `WSW-20261006-001`. Owner review on the running converter is the next gate;
  the next batch of Table A tabs waits for that review.

- [ ] Close the remaining upstream option gaps recorded in
  [`docs/research/2026-10-06-generator-tab-fidelity-audit.md`](../research/2026-10-06-generator-tab-fidelity-audit.md).
  Problem: the generator tabs are simplified ports. Restored already: Line
  Draw simplify/resolution, Postcard message, Flow Field formulas, the
  harmonograph physical pendulum model, 3D perspective/primitives, and the
  linedraw patch hatch. Still missing: Line Draw's upstream contour pipeline
  and Perlin sketch style; 3D CSG, surface texturing, and eye/center/up
  camera; the snowflake lattice simulation; Text custom fonts and kerning;
  Substitution/Postcard/Pixel Art per-colour layers.
  Benefit: the tabs can honestly claim the upstream feature set, or the audit
  note states exactly what is not ported.
  Risk: 3D CSG, the lattice model, and colour layers are each large features,
  and multi-pen options need a layer workflow the converter does not have yet.
  Acceptance: each gap is either implemented with tests and README/docs
  updates, or explicitly closed as out of scope in the audit note. Prioritize
  the Flow Field formula input and the 3D perspective/primitive set first.

## Next concrete task

Re-run F-02 with a newly generated default converter file. Then complete the
converter-generated M-06 inner/mid/outer-radius timing and geometry check on
installed grblHAL. Do not enable direct P100-to-print operation until its
commissioning and toolhead gates also pass.
