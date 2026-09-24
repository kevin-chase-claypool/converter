# Change Index

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Category | Status | Summary |
|---|---|---|---|---|
| 2026-09-24 | `WSW-20260924-013` | windows-software, rp23cnc-software | implemented | [Give the program's first pen-down a cold-seek dwell](windows-software/2026/2026-09-24-first-pen-down-cold-seek-dwell.md) |
| 2026-09-24 | `WSW-20260924-012` | windows-software | implemented | [Fix stroke-only elements being treated as invisible](windows-software/2026/2026-09-24-fix-stroke-only-element-visibility.md) |
| 2026-09-24 | `WSW-20260924-011` | windows-software | implemented | [Restore manual-only preview refresh](windows-software/2026/2026-09-24-restore-manual-preview-refresh.md) |
| 2026-09-24 | `WSW-20260924-010` | windows-software | implemented | [Inset infill away from polygon boundaries](windows-software/2026/2026-09-24-inset-infill-away-from-boundaries.md) |
| 2026-09-24 | `WSW-20260924-009` | windows-software | implemented | [Drop sub-pen-width infill fragments](windows-software/2026/2026-09-24-drop-sub-pen-width-infill-fragments.md) |
| 2026-09-24 | `WSW-20260924-008` | windows-software | implemented | [Subdivide polar moves linearly so A-axis-dominant lines stay straight](windows-software/2026/2026-09-24-straighten-a-axis-polar-lines.md) |
| 2026-09-24 | `WSW-20260924-007` | windows-software | implemented | [Keep the pen down only between infill trails, never across shape outlines](windows-software/2026/2026-09-24-bridge-only-between-infill-trails.md) |
| 2026-09-24 | `WSW-20260924-006` | windows-software | implemented | [Fix fill leak and skip invisible white paths](windows-software/2026/2026-09-24-fix-fill-leak-and-skip-white-paths.md) |
| 2026-09-24 | `WSW-20260924-005` | windows-software | implemented | [Generate fill at on-paper resolution when the artwork is scaled down](windows-software/2026/2026-09-24-fill-at-on-paper-resolution.md) |
| 2026-09-24 | `WSW-20260924-004` | windows-software | implemented | [Eliminate duplicate theta planning during contour ordering](windows-software/2026/2026-09-24-eliminate-duplicate-theta-planning.md) |
| 2026-09-24 | `WSW-20260924-003` | windows-software | implemented | [Tame cell-lattice fill density and fix triangular lattice over-generation](windows-software/2026/2026-09-24-tame-cell-lattice-fill-density.md) |
| 2026-09-24 | `WSW-20260924-002` | windows-software | superseded | [Rebuild the preview when the fill pattern or raster shading changes (superseded)](windows-software/2026/2026-09-24-refresh-preview-on-fill-pattern-change.md) |
| 2026-09-24 | `WSW-20260924-001` | windows-software | implemented | [Speed up the parse/preview pipeline by removing duplicate theta candidates](windows-software/2026/2026-09-24-speed-up-theta-planning.md) |
| 2026-09-24 | `RPSW-20260924-002` | rp23cnc-software | implemented | [Report magnet detection instead of a compile flag in the `ready=[...]` field](rp23cnc-software/2026/2026-09-24-fix-toolhead-gp27-telemetry-field.md) |
| 2026-09-24 | `RPSW-20260924-001` | rp23cnc-software, hardware | verified | [Enable the integrated toolhead magnetic commissioning gate](rp23cnc-software/2026/2026-09-24-enable-magnetic-commissioning-gate.md) |
| 2026-09-23 | `WSW-20260923-004` | windows-software | implemented | [Add a curve-roundness test sample](windows-software/2026/2026-09-23-add-curve-roundness-test-sample.md) |
| 2026-09-23 | `WSW-20260923-003` | windows-software, rp23cnc-software | implemented | [Set converter defaults for the installed toolhead](windows-software/2026/2026-09-23-converter-defaults-for-toolhead.md) |
| 2026-09-23 | `WSW-20260923-002` | windows-software | implemented | [Subdivide draw moves so bed rotation traces straight lines](windows-software/2026/2026-09-23-subdivide-polar-draw-moves.md) |
| 2026-09-23 | `WSW-20260923-001` | windows-software | implemented | [Draw stroke centerlines by default instead of outlining the stroke width](windows-software/2026/2026-09-23-draw-stroke-centerlines-by-default.md) |
| 2026-09-23 | `RPSW-20260923-016` | rp23cnc-software, hardware | implemented | [Widen the force-hold band to ±10 g and move relief to 15 g](rp23cnc-software/2026/2026-09-23-widen-hold-band.md) |
| 2026-09-23 | `RPSW-20260923-015` | rp23cnc-software, hardware | verified | [Invert the grblHAL spindle enable to match the toolhead input](rp23cnc-software/2026/2026-09-23-invert-spindle-enable-for-toolhead.md) |
| 2026-09-23 | `RPSW-20260923-014` | rp23cnc-software, hardware | implemented | [Require a full filter window of implausible samples before faulting](rp23cnc-software/2026/2026-09-23-raise-implausible-fault-streak.md) |
| 2026-09-23 | `RPSW-20260923-013` | rp23cnc-software, hardware | implemented | [Stabilize warm-seek travel and stop motor-driven sensor-noise faults](rp23cnc-software/2026/2026-09-23-stabilize-warm-seek-travel.md) |
| 2026-09-23 | `RPSW-20260923-012` | rp23cnc-software, hardware | implemented | [Split the seek settle by proximity to the target](rp23cnc-software/2026/2026-09-23-split-seek-settle.md) |
| 2026-09-23 | `RPSW-20260923-011` | rp23cnc-software, hardware | implemented | [Reduce the M5 clearance air gap to about 1 mm](rp23cnc-software/2026/2026-09-23-reduce-m5-clearance-air-gap.md) |
| 2026-09-23 | `RPSW-20260923-010` | rp23cnc-software, hardware | implemented | [Widen the warm coarse-phase force gate](rp23cnc-software/2026/2026-09-23-widen-warm-coarse-force-gate.md) |
| 2026-09-23 | `RPSW-20260923-009` | rp23cnc-software, hardware | implemented | [Learn warm-seek travel to traverse it with coarse pulses](rp23cnc-software/2026/2026-09-23-learn-warm-seek-travel.md) |
| 2026-09-23 | `RPSW-20260923-008` | rp23cnc-software, hardware | implemented | [Replace the two-touch seek with a single descend](rp23cnc-software/2026/2026-09-23-replace-two-touch-with-single-descend.md) |
| 2026-09-23 | `RPSW-20260923-007` | rp23cnc-software, hardware | implemented | [Reject implausible CS1238 conversions](rp23cnc-software/2026/2026-09-23-reject-implausible-cs1238-samples.md) |
| 2026-09-23 | `RPSW-20260923-006` | rp23cnc-software, hardware | implemented | [Reduce the sensing settle to the measured 300 ms](rp23cnc-software/2026/2026-09-23-reduce-settle-to-measured-300ms.md) |
| 2026-09-23 | `RPSW-20260923-005` | rp23cnc-software, hardware | implemented | [Add a one-pulse settle trace to E-09E](rp23cnc-software/2026/2026-09-23-add-e09e-settle-trace.md) |
| 2026-09-23 | `RPSW-20260923-004` | rp23cnc-software, hardware | implemented | [Add hysteresis to the urgent over-force relief](rp23cnc-software/2026/2026-09-23-add-hysteresis-to-urgent-relief.md) |
| 2026-09-23 | `RPSW-20260923-003` | rp23cnc-software | implemented | [Report urgent over-force relief activity in telemetry](rp23cnc-software/2026/2026-09-23-report-urgent-relief-telemetry.md) |
| 2026-09-23 | `RPSW-20260923-002` | rp23cnc-software, hardware | implemented | [Add bounded urgent over-force relief to the hold loop](rp23cnc-software/2026/2026-09-23-add-urgent-over-force-relief.md) |
| 2026-09-23 | `RPSW-20260923-001` | rp23cnc-software, hardware | implemented | [Clamp the hold band below the hard-force limit](rp23cnc-software/2026/2026-09-23-clamp-hold-band-below-hard-limit.md) |
| 2026-09-22 | `WSW-20260922-002` | windows-software, rp23cnc-software, hardware | implemented | [File outstanding working-tree artifacts into the repository](windows-software/2026/2026-09-22-file-outstanding-working-tree-artifacts.md) |
| 2026-09-22 | `WSW-20260922-001` | windows-software, rp23cnc-software, hardware | implemented | [Ignore local tooling and build-scratch directories](windows-software/2026/2026-09-22-ignore-local-tooling-and-build-scratch.md) |
| 2026-09-22 | `RPSW-20260922-034` | rp23cnc-software, hardware | implemented | [Settle the home contact seek on settled force](rp23cnc-software/2026/2026-09-22-settle-contact-seek-on-settled-force.md) |
| 2026-09-22 | `RPSW-20260922-033` | rp23cnc-software, hardware | implemented | [Record E-07B trace-settle tuning](rp23cnc-software/2026/2026-09-22-record-e07b-trace-settle-tuning.md) |
| 2026-09-22 | `RPSW-20260922-032` | rp23cnc-software, hardware | implemented | [Refresh Tare after Normal Pen Clear](rp23cnc-software/2026/2026-09-22-tare-after-normal-clear.md) |
| 2026-09-22 | `RPSW-20260922-031` | rp23cnc-software, hardware | implemented | [Trend-gate Force-hold Corrections](rp23cnc-software/2026/2026-09-22-trend-gate-hold-corrections.md) |
| 2026-09-22 | `RPSW-20260922-030` | rp23cnc-software, hardware | implemented | [Bound Trend Contact to a Usable Envelope](rp23cnc-software/2026/2026-09-22-bound-trend-contact-envelope.md) |
| 2026-09-22 | `RPSW-20260922-029` | rp23cnc-software, hardware | implemented | [Re-acquire Contact after M5 Clearance](rp23cnc-software/2026/2026-09-22-reacquire-contact-after-clear.md) |
| 2026-09-22 | `RPSW-20260922-028` | rp23cnc-software, hardware | implemented | [Confirm Contact by Trend](rp23cnc-software/2026/2026-09-22-confirm-contact-trend.md) |
| 2026-09-22 | `RPSW-20260922-027` | rp23cnc-software, hardware | implemented | [Extend Fine Force-Tune Budget](rp23cnc-software/2026/2026-09-22-extend-fine-force-tune-budget.md) |
| 2026-09-22 | `RPSW-20260922-026` | rp23cnc-software, hardware | implemented | [Tare After Lift-Home Release](rp23cnc-software/2026/2026-09-22-tare-after-lift-home-release.md) |
| 2026-09-22 | `RPSW-20260922-025` | rp23cnc-software, hardware | implemented | [Add Two-Touch Home Approach](rp23cnc-software/2026/2026-09-22-add-two-touch-home-approach.md) |
| 2026-09-22 | `RPSW-20260922-024` | rp23cnc-software, hardware | implemented | [Bound Moving-Average Hold Pulses](rp23cnc-software/2026/2026-09-22-bound-moving-average-hold-pulses.md) |
| 2026-09-22 | `RPSW-20260922-023` | rp23cnc-software, hardware | implemented | [Tare Only After Home Retract](rp23cnc-software/2026/2026-09-22-tare-after-home-retract.md) |
| 2026-09-22 | `RPSW-20260922-022` | rp23cnc-software, hardware | implemented | [Add Fine Home Contact Approach](rp23cnc-software/2026/2026-09-22-add-fine-home-contact-approach.md) |
| 2026-09-22 | `RPSW-20260922-021` | rp23cnc-software, hardware | implemented | [Revise Home Contact-Seek Pacing](rp23cnc-software/2026/2026-09-22-revise-home-contact-seek-pacing.md) |
| 2026-09-22 | `RPSW-20260922-020` | rp23cnc-software, hardware | implemented | [Bound Home-Origin Contact Seek](rp23cnc-software/2026/2026-09-22-bound-home-origin-contact-seek.md) |
| 2026-09-22 | `RPSW-20260922-019` | rp23cnc-software | implemented | [Make integrated toolhead telemetry quiet by default](rp23cnc-software/2026/2026-09-22-quiet-integrated-toolhead-telemetry.md) |
| 2026-09-22 | `RPSW-20260922-018` | rp23cnc-software | implemented | [Set integrated force target to 35 g and limit to 60 g](rp23cnc-software/2026/2026-09-22-set-integrated-force-target-35g-limit-60g.md) |
| 2026-09-22 | `RPSW-20260922-017` | rp23cnc-software | verified | [Set integrated lift timeout to 3000 ms](rp23cnc-software/2026/2026-09-22-set-integrated-lift-timeout-3000ms.md) |
| 2026-09-22 | `RPSW-20260922-016` | rp23cnc-software, hardware | implemented | [Match integrated lift drive to validated bench pulses](rp23cnc-software/2026/2026-09-22-increase-integrated-lift-drive.md) |
| 2026-09-22 | `RPSW-20260922-015` | rp23cnc-software, hardware | implemented | [Correct integrated motor-direction polarity](rp23cnc-software/2026/2026-09-22-correct-integrated-direction-polarity.md) |
| 2026-09-22 | `RPSW-20260922-014` | rp23cnc-software, hardware | implemented | [Enable the mechanical-preload supervised bench build](rp23cnc-software/2026/2026-09-22-enable-mechanical-preload-bench-build.md) |
| 2026-09-22 | `RPSW-20260922-013` | rp23cnc-software, hardware | implemented | [Stage mechanical-preload M3/M5 behavior](rp23cnc-software/2026/2026-09-22-stage-mechanical-preload-m3m5.md) |
| 2026-09-22 | `RPSW-20260922-012` | rp23cnc-software, hardware | implemented | [Add E-09F manual down setup pulse](rp23cnc-software/2026/2026-09-22-add-e09f-manual-down-setup.md) |
| 2026-09-22 | `RPSW-20260922-011` | rp23cnc-software, hardware | implemented | [Delay E-09F air-gap telemetry](rp23cnc-software/2026/2026-09-22-delay-e09f-air-gap-telemetry.md) |
| 2026-09-22 | `RPSW-20260922-010` | rp23cnc-software, hardware | implemented | [Add E-09F manual retract recovery](rp23cnc-software/2026/2026-09-22-add-e09f-manual-retract-recovery.md) |
| 2026-09-22 | `RPSW-20260922-009` | rp23cnc-software, hardware | implemented | [Fix E-09F release hard-limit fault](rp23cnc-software/2026/2026-09-22-fix-e09f-release-hard-limit.md) |
| 2026-09-22 | `RPSW-20260922-008` | rp23cnc-software, hardware | implemented | [Add E-09F guarded force-hold test](rp23cnc-software/2026/2026-09-22-add-e09f-guarded-force-hold.md) |
| 2026-09-22 | `RPSW-20260922-007` | rp23cnc-software, hardware | implemented | [Refine E-09E pulses and stage pen-clear candidate](rp23cnc-software/2026/2026-09-22-refine-e09e-pulses-and-stage-pen-clear.md) |
| 2026-09-22 | `RPSW-20260922-006` | rp23cnc-software, hardware | implemented | [Add E-09E Serial Monitor shortcuts](rp23cnc-software/2026/2026-09-22-add-e09e-serial-monitor-shortcuts.md) |
| 2026-09-22 | `RPSW-20260922-005` | rp23cnc-software, windows-software, hardware | implemented | [Route E-09E runtime through service UART](rp23cnc-software/2026/2026-09-22-route-e09e-through-service-uart.md) |
| 2026-09-22 | `RPSW-20260922-004` | rp23cnc-software, windows-software | implemented | [Make E-09E pulse duration adjustable](rp23cnc-software/2026/2026-09-22-make-e09e-pulse-duration-adjustable.md) |
| 2026-09-22 | `RPSW-20260922-003` | rp23cnc-software, windows-software, hardware | implemented | [Add E-09E installed-pen scale pulse check](rp23cnc-software/2026/2026-09-22-add-e09e-pen-scale-pulse-check.md) |
| 2026-09-22 | `RPSW-20260922-002` | rp23cnc-software, hardware | implemented | [Replace E-09C profile with cap-free repeat](rp23cnc-software/2026/2026-09-22-replace-e09c-cap-free-calibration.md) |
| 2026-09-22 | `RPSW-20260922-001` | rp23cnc-software, windows-software, hardware | implemented | [Stage E-09C CS1238 force profile](rp23cnc-software/2026/2026-09-22-stage-e09c-cs1238-force-profile.md) |
| 2026-09-21 | `WINSW-20260921-002` | windows-software, rp23cnc-software, hardware | implemented | [Add known-mass force-direction projection](windows-software/2026/2026-09-21-add-known-mass-force-direction-projection.md) |
| 2026-09-21 | `WINSW-20260921-001` | rp23cnc-software, hardware | implemented | [Add Pro Micro known-mass calibration application](windows-software/2026/2026-09-21-add-pro-micro-known-mass-calibration-app.md) |
| 2026-09-21 | `RPSW-20260921-002` | rp23cnc-software, hardware | implemented | [Migrate Integrated Toolhead to CS1238 Backend](rp23cnc-software/2026/2026-09-21-migrate-integrated-toolhead-cs1238-backend.md) |
| 2026-09-21 | `RPSW-20260921-001` | hardware | implemented | [Replace dual-ADC fixture with Pro Micro known-mass calibration](rp23cnc-software/2026/2026-09-21-replace-dual-adc-fixture-with-known-mass-cs1238.md) |
| 2026-09-21 | `RP23CNC-20260921-008` | rp23cnc-software, hardware | implemented | [Add post-release pen-clear air-gap pulse](rp23cnc-software/2026/2026-09-21-add-post-release-pen-clear-air-gap.md) |
| 2026-09-21 | `RP23CNC-20260921-007` | rp23cnc-software, windows-software, hardware | implemented | [Add bounded GP27 toolhead-ready wait](rp23cnc-software/2026/2026-09-21-add-bounded-gp27-toolhead-wait.md) |
| 2026-09-19 | `WINSW-20260919-001` | hardware, rp23cnc-software | implemented | [Add guided force-calibration analysis workflow](windows-software/2026/2026-09-19-add-guided-force-calibration-analysis.md) |
| 2026-09-19 | `RPSW-20260919-001` | hardware, windows-software | implemented | [Add Pico 2 dual-sensor DAQ firmware](rp23cnc-software/2026/2026-09-19-add-pico2-dual-sensor-daq-firmware.md) |
| 2026-09-15 | `HW-20260915-001` | rp23cnc-software, windows-software | planned | [Plan Pico 2 dual-sensor calibration DAQ](hardware/2026/2026-09-15-plan-pico2-dual-sensor-calibration-daq.md) |
| 2026-09-14 | `RPSW-20260914-001` | hardware | implemented | [Add CS1238 motor-inert bring-up firmware](rp23cnc-software/2026/2026-09-14-add-cs1238-motor-inert-bringup.md) |
| 2026-09-13 | `RPSW-20260913-005` | hardware | implemented | [Add E-07B fast force trace](rp23cnc-software/2026/2026-09-13-add-e07b-fast-force-trace.md) |
| 2026-09-13 | `HW-20260913-013` | rp23cnc-software | planned | [Plan CS1238 force-sensor replacement](hardware/2026/2026-09-13-plan-cs1238-force-sensor-replacement.md) |
| 2026-09-13 | `HW-20260913-012` | hardware | implemented | [Lubricate toolhead motion path](hardware/2026/2026-09-13-lubricate-toolhead-motion-path.md) |
| 2026-09-13 | `HW-20260913-011` | hardware, rp23cnc-software | implemented | [Add E07B fine force-pulse control](hardware/2026/2026-09-13-add-e07b-fine-force-pulse-control.md) |
| 2026-09-13 | `HW-20260913-010` | hardware, rp23cnc-software | verified | [Calibrate E07B N20 direction](hardware/2026/2026-09-13-calibrate-e07b-n20-direction.md) |
| 2026-09-13 | `HW-20260913-009` | hardware, rp23cnc-software | verified | [Repair DRV8833 output solder joint](hardware/2026/2026-09-13-repair-drv8833-output-solder-joint.md) |
| 2026-09-13 | `HW-20260913-008` | hardware, rp23cnc-software | implemented | [Add manual historical E-05 step test](hardware/2026/2026-09-13-add-manual-legacy-e05-steps.md) |
| 2026-09-13 | `HW-20260913-007` | hardware, rp23cnc-software | implemented | [Preserve historical E-05 motor test](hardware/2026/2026-09-13-preserve-historical-e05-motor-test.md) |
| 2026-09-13 | `HW-20260913-006` | hardware, rp23cnc-software | implemented | [Extend E07B actuator pulse range](hardware/2026/2026-09-13-extend-e07b-actuator-pulse-range.md) |
| 2026-09-13 | `HW-20260913-005` | hardware, rp23cnc-software | implemented | [Add DRV8833 loaded-fault telemetry](hardware/2026/2026-09-13-add-drv8833-loaded-fault-telemetry.md) |
| 2026-09-13 | `HW-20260913-004` | hardware, rp23cnc-software | planned | [Isolate N20 output-connection failure](hardware/2026/2026-09-13-isolate-n20-output-connection-failure.md) |
| 2026-09-13 | `HW-20260913-003` | hardware, rp23cnc-software | implemented | [Add isolated DRV8833 output meter mode](hardware/2026/2026-09-13-add-isolated-drv8833-output-meter-mode.md) |
| 2026-09-13 | `HW-20260913-002` | hardware, rp23cnc-software | implemented | [Add non-motion DRV8833 meter mode](hardware/2026/2026-09-13-add-nonmotion-drv8833-meter-mode.md) |
| 2026-09-13 | `HW-20260913-001` | hardware, rp23cnc-software | implemented | [Correct confirmed DRV8833 sleep/fault mapping](hardware/2026/2026-09-13-correct-drv8833-sleep-fault-mapping.md) |
| 2026-09-12 | `RPSW-20260912-001` | rp23cnc-software, hardware | verified | [Record P113 unified registration command](rp23cnc-software/2026/2026-09-12-record-p113-unified-registration.md) |
| 2026-09-11 | `WSW-20260911-001` | windows-software, rp23cnc-software, hardware | implemented | [Add Ontoly investigation prompt](windows-software/2026/2026-09-11-add-ontoly-investigation-prompt.md) |
| 2026-09-11 | `RPSW-20260911-013` | rp23cnc-software, hardware | implemented | [Retune P100 Q5 Raster Density](rp23cnc-software/2026/2026-09-11-retune-p100-q5-raster.md) |
| 2026-09-11 | `RPSW-20260911-012` | rp23cnc-software, hardware | implemented | [Add P112 Outer-Index Survey](rp23cnc-software/2026/2026-09-11-add-p112-outer-index-survey.md) |
| 2026-09-11 | `RPSW-20260911-011` | rp23cnc-software, hardware | implemented | [Isolate P100 System Homing](rp23cnc-software/2026/2026-09-11-isolate-p100-system-homing.md) |
| 2026-09-11 | `RPSW-20260911-010` | rp23cnc-software, hardware | verified | [Add P110 Q5 First G38 Row Diagnostic](rp23cnc-software/2026/2026-09-11-add-p110-q5-first-g38-row-diagnostic.md) |
| 2026-09-11 | `RPSW-20260911-009` | rp23cnc-software, hardware | verified | [Add P109 Q5 Combined Diagnostic](rp23cnc-software/2026/2026-09-11-add-p109-q5-combined-diagnostic.md) |
| 2026-09-11 | `RPSW-20260911-008` | rp23cnc-software, hardware | verified | [Add P108 Q5 Handshake Diagnostic](rp23cnc-software/2026/2026-09-11-add-p108-q5-handshake-diagnostic.md) |
| 2026-09-11 | `RPSW-20260911-007` | rp23cnc-software, hardware | verified | [Add P107 Q5 Preposition Diagnostic](rp23cnc-software/2026/2026-09-11-add-p107-q5-preposition-diagnostic.md) |
| 2026-09-11 | `RPSW-20260911-006` | rp23cnc-software, hardware | verified | [Add P100 Q5 Centroid Survey](rp23cnc-software/2026/2026-09-11-add-p100-q5-centroid-survey.md) |
| 2026-09-11 | `RPSW-20260911-005` | rp23cnc-software, hardware | implemented | [Add P106 Manual Magnetic Survey](rp23cnc-software/2026/2026-09-11-add-p106-manual-magnetic-survey.md) |
| 2026-09-11 | `RPSW-20260911-004` | rp23cnc-software, hardware | implemented | [Record P100 Q3 Candidate Scan Parameters](rp23cnc-software/2026/2026-09-11-record-p100-q3-candidate-parameters.md) |
| 2026-09-11 | `RPSW-20260911-003` | rp23cnc-software, hardware | implemented | [Record P100 Q3 Candidate Scan Rectangle](rp23cnc-software/2026/2026-09-11-record-p100-q3-candidate-rectangle.md) |
| 2026-09-11 | `RPSW-20260911-002` | rp23cnc-software, hardware | verified | [Enable Isolated P100 Q2 X/Y Homing](rp23cnc-software/2026/2026-09-11-enable-isolated-p100-q2-home.md) |
| 2026-09-11 | `RPSW-20260911-001` | rp23cnc-software, hardware | verified | [Verify P100 Q1 probe handshake](rp23cnc-software/2026/2026-09-11-verify-p100-q1-probe-handshake.md) |
| 2026-09-11 | `RP23-20260911-024` | hardware | verified | [Enable Verified P100 Q0 Registration](rp23cnc-software/2026/2026-09-11-enable-verified-p100-q0-registration.md) |
| 2026-09-11 | `RP23-20260911-023` | hardware | verified | [Verify Manual Magnetic G54 Registration](rp23cnc-software/2026/2026-09-11-verify-manual-magnetic-g54-registration.md) |
| 2026-09-10 | `RPSW-20260910-003` | rp23cnc-software, hardware | verified | [Correct P100 installed Aux0 polarity](rp23cnc-software/2026/2026-09-10-correct-p100-aux-polarity.md) |
| 2026-09-10 | `RPSW-20260910-002` | rp23cnc-software, hardware | verified | [Verify real-magnet PRB/G38 path](rp23cnc-software/2026/2026-09-10-prb-g38-magnetic-path.md) |
| 2026-09-10 | `RPSW-20260910-001` | rp23cnc-software, hardware | verified | [Record motor-inert P100 handshake evidence](rp23cnc-software/2026/2026-09-10-record-motor-inert-p100-handshake.md) |
| 2026-09-09 | `RPSW-20260909-002` | rp23cnc-software, hardware | implemented | [Add motor-inert P100 handshake diagnostic](rp23cnc-software/2026/2026-09-09-add-motor-inert-p100-handshake-diagnostic.md) |
| 2026-09-09 | `RPSW-20260909-001` | rp23cnc-software, hardware | implemented | [Add lift-home status to bounded actuator test](rp23cnc-software/2026/2026-09-09-add-lift-home-status-to-bounded-actuator-test.md) |
| 2026-09-09 | `HW-20260909-003` | hardware, rp23cnc-software | implemented | [Document toolhead pen-mount mechanics](hardware/2026/2026-09-09-document-toolhead-pen-mount-mechanics.md) |
| 2026-09-09 | `HW-20260909-002` | hardware, rp23cnc-software | planned | [Order faster toolhead actuator candidates](hardware/2026/2026-09-09-order-faster-toolhead-actuator-candidates.md) |
| 2026-09-09 | `HW-20260909-001` | hardware, rp23cnc-software | partial | [Verify guarded lift-home repeatability](hardware/2026/2026-09-09-verify-guarded-lift-home-repeatability.md) |
| 2026-09-08 | `WSW-20260908-001` | windows-software, hardware, rp23cnc-software | implemented | [Calibrate the preview motion-time estimate](windows-software/2026/2026-09-08-calibrate-preview-motion-estimate.md) |
| 2026-09-08 | `RPSW-20260908-002` | rp23cnc-software, hardware | verified | [Fix integrated service-UART telemetry suppression](rp23cnc-software/2026/2026-09-08-fix-integrated-service-uart-telemetry.md) |
| 2026-09-08 | `RPSW-20260908-001` | rp23cnc-software, hardware | implemented | [Add LIFT_HOME UART diagnostic sketch](rp23cnc-software/2026/2026-09-08-add-lift-home-uart-diagnostic.md) |
| 2026-09-08 | `HW-20260908-004` | hardware, rp23cnc-software | implemented | [Install LIFT_HOME switch input diagnostics](hardware/2026/2026-09-08-install-lift-home-switch-input.md) |
| 2026-09-08 | `HW-20260908-003` | hardware, rp23cnc-software | implemented | [Record current spring geometry](hardware/2026/2026-09-08-record-current-spring-geometry.md) |
| 2026-09-08 | `HW-20260908-002` | hardware, rp23cnc-software | verified | [Verify toolhead power-path gates](hardware/2026/2026-09-08-verify-toolhead-power-path.md) |
| 2026-09-08 | `HW-20260908-001` | hardware | verified | [Identify and diagram the RP23CNC ESTOP screw terminal](hardware/2026/2026-09-08-identify-rp23cnc-estop-terminal.md) |
| 2026-09-07 | `HW-20260907-002` | hardware, rp23cnc-software, windows-software | verified | [Verify converter motion and guarded X/Y envelope](hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md) |
| 2026-09-07 | `HW-20260907-001` | hardware, rp23cnc-software | planned | [Require scale-force transfer calibration](hardware/2026/2026-09-07-require-scale-force-transfer-calibration.md) |
| 2026-09-06 | `WINSW-20260906-001` | windows-software, hardware | implemented | [Center G54 output and correct the M-06 sample](windows-software/2026/2026-09-06-center-g54-output-and-correct-m06-sample.md) |
| 2026-09-06 | `RPSW-20260906-001` | rp23cnc-software, hardware | implemented | [Add GP27 Normal-Status Guardrails](rp23cnc-software/2026/2026-09-06-gp27-normal-status-guardrails.md) |
| 2026-09-06 | `HW-20260906-006` | hardware, rp23cnc-software | verified | [Set temporary manual pen-corrected G54 XY reference](hardware/2026/2026-09-06-set-temporary-manual-g54-xy-reference.md) |
| 2026-09-06 | `HW-20260906-005` | hardware, rp23cnc-software | verified | [Commission X/Y physical homing](hardware/2026/2026-09-06-commission-xy-physical-homing.md) |
| 2026-09-06 | `HW-20260906-004` | hardware, rp23cnc-software | verified | [Verify pen-free coordinated X/Y/A repeatability](hardware/2026/2026-09-06-xya-coordinated-smoke-test.md) |
| 2026-09-06 | `HW-20260906-003` | hardware, rp23cnc-software | verified | [Configure the A axis without a finite travel limit](hardware/2026/2026-09-06-a-axis-unlimited-travel-configuration.md) |
| 2026-09-06 | `HW-20260906-002` | hardware, rp23cnc-software | verified | [Verify X-axis rate and dimensional calibration](hardware/2026/2026-09-06-x-axis-rate-and-dimensional-calibration.md) |
| 2026-09-05 | `WSW-20260905-007` | windows-software | implemented | [Share the preview motion plan](windows-software/2026/2026-09-05-share-preview-motion-plan.md) |
| 2026-09-05 | `WSW-20260905-006` | windows-software | implemented | [Make the production preview safe and complete](windows-software/2026/2026-09-05-production-preview-safety.md) |
| 2026-09-05 | `WSW-20260905-005` | windows-software, rp23cnc-software, hardware | implemented | [Consolidate current documentation ownership](windows-software/2026/2026-09-05-consolidate-current-documentation.md) |
| 2026-09-05 | `WSW-20260905-004` | windows-software, rp23cnc-software, hardware | implemented | [Make converter programs self-contained for ioSender](windows-software/2026/2026-09-05-self-contained-iosender-program-contract.md) |
| 2026-09-05 | `WSW-20260905-003` | windows-software, rp23cnc-software, hardware | implemented | [Record ioSender-to-converter compatibility review](windows-software/2026/2026-09-05-iosender-converter-compatibility-review.md) |
| 2026-09-05 | `WSW-20260905-002` | windows-software, rp23cnc-software, hardware | implemented | [Implement radius-aware A-axis feed for drawing](windows-software/2026/2026-09-05-radius-aware-a-feed-requirement.md) |
| 2026-09-05 | `HW-20260905-006` | hardware, rp23cnc-software | verified | [Verify Y-axis dimensional calibration](hardware/2026/2026-09-05-m-03-y-axis-dimensional-calibration.md) |
| 2026-09-05 | `HW-20260905-005` | hardware, rp23cnc-software | verified | [Verify the Y-axis rate and acceleration baseline](hardware/2026/2026-09-05-m-02-y-axis-rate-verification.md) |
| 2026-09-05 | `HW-20260905-004` | hardware, rp23cnc-software | verified | [Verify the A-axis 12:1 bed ratio](hardware/2026/2026-09-05-m-05-bed-ratio-verification.md) |
| 2026-09-05 | `HW-20260905-003` | hardware, rp23cnc-software | verified | [Correct A-axis calibration and characterize the F5000 ramp](hardware/2026/2026-09-05-a-axis-rate-calibration-and-acceleration-check.md) |
| 2026-09-05 | `HW-20260905-002` | hardware, rp23cnc-software | verified | [Verify installed TB6600 signal response](hardware/2026/2026-09-05-tb6600-installed-signal-response.md) |
| 2026-09-05 | `HW-20260905-001` | hardware, rp23cnc-software | verified | [RP23CNC USB source-selector bring-up](hardware/2026/2026-09-05-rp23cnc-usb-source-selector-bringup.md) |
| 2026-09-04 | `WSW-20260904-001` | windows-software, rp23cnc-software | implemented | [Move pen/TMAG XY offset ownership to P100](windows-software/2026/2026-09-04-remove-converter-tool-offset.md) |
| 2026-09-04 | `HW-20260904-007` | hardware, rp23cnc-software | implemented | [Replace Toolhead Preload Spring](hardware/2026/2026-09-04-replace-toolhead-preload-spring.md) |
| 2026-09-04 | `HW-20260904-006` | rp23cnc-software | implemented | [Make Pulse Response Tool-Specific During Preflight](hardware/2026/2026-09-04-per-tool-pulse-response-preflight.md) |
| 2026-09-04 | `HW-20260904-005` | hardware | partial | [Correct N20 Current After Lead-Screw Alignment and Preload Test](hardware/2026/2026-09-04-correct-n20-unloaded-current-after-alignment.md) |
| 2026-09-04 | `HW-20260904-003` | hardware | implemented | [Record TB6600 signal harness wiring](hardware/2026/2026-09-04-record-tb6600-signal-harness-wiring.md) |
| 2026-09-04 | `HW-20260904-002` | hardware | implemented | [Reroute top-down wiring schematic into clean lanes](hardware/2026/2026-09-04-reroute-top-down-wiring-diagram.md) |
| 2026-09-04 | `HW-20260904-001` | hardware | implemented | [Correct axis-specific motor cable colors in diagrams](hardware/2026/2026-09-04-correct-axis-motor-cable-colors-in-diagrams.md) |
| 2026-09-03 | `RPSW-20260903-008` | rp23cnc-software, hardware, windows-software | implemented | [Add Opto-Isolation Presentation Slide](rp23cnc-software/2026/2026-09-03-add-opto-isolation-presentation-slide.md) |
| 2026-09-03 | `HW-20260903-003` | hardware | implemented | [Add mobile wiring-table view](hardware/2026/2026-09-03-add-mobile-wiring-table-view.md) |
| 2026-09-03 | `HW-20260903-002` | hardware | implemented | [Land TB6600 power branches](hardware/2026/2026-09-03-land-tb6600-power-branches.md) |
| 2026-09-03 | `HW-20260903-001` | hardware, rp23cnc-software | implemented | [Record TB6600 signal and A-axis commissioning baseline](hardware/2026/2026-09-03-record-tb6600-signal-and-a-axis-commissioning-baseline.md) |
| 2026-09-02 | `RPSW-20260902-007` | rp23cnc-software, hardware, windows-software | implemented | [Full-Bleed Opening Slide Image](rp23cnc-software/2026/2026-09-02-full-bleed-opening-slide-image.md) |
| 2026-09-02 | `RPSW-20260902-006` | rp23cnc-software, hardware, windows-software | implemented | [Refresh Summer Presentation Opening Render](rp23cnc-software/2026/2026-09-02-refresh-summer-presentation-opening-render.md) |
| 2026-09-02 | `RPSW-20260902-005` | rp23cnc-software, hardware, windows-software | implemented | [Expand P100 Presentation to Full Slide](rp23cnc-software/2026/2026-09-02-expand-p100-presentation-to-full-slide.md) |
| 2026-09-02 | `RPSW-20260902-004` | rp23cnc-software, hardware, windows-software | implemented | [Align P100 Presentation Detail States](rp23cnc-software/2026/2026-09-02-align-p100-presentation-detail-states.md) |
| 2026-09-02 | `RPSW-20260902-003` | rp23cnc-software, hardware, windows-software | implemented | [Add P100 Presentation Interaction](rp23cnc-software/2026/2026-09-02-add-p100-presentation-interaction.md) |
| 2026-09-02 | `RPSW-20260902-002` | windows-software, rp23cnc-software, hardware | implemented | [Add Summer Progress Presentation](rp23cnc-software/2026/2026-09-02-add-summer-progress-presentation.md) |
| 2026-09-02 | `RPSW-20260902-001` | windows-software, rp23cnc-software, hardware | implemented | [Add Current System Data Flow Chart](rp23cnc-software/2026/2026-09-02-current-system-data-flow.md) |
| 2026-09-02 | `HW-20260902-001` | hardware, rp23cnc-software | planned | [Plan Interchangeable-Tool Force Preflight](hardware/2026/2026-09-02-plan-interchangeable-tool-force-preflight.md) |
| 2026-09-01 | `HW-20260901-002` | hardware, rp23cnc-software | planned | [Persist Toolhead Force Profile Separately from Boot Baseline](hardware/2026/2026-09-01-persist-toolhead-force-profile.md) |
| 2026-09-01 | `HW-20260901-001` | hardware, rp23cnc-software | planned | [Separate Normal Pen Clear from LIFT Home](hardware/2026/2026-09-01-separate-pen-clear-from-lift-home.md) |
| 2026-08-30 | `HW-20260830-005` | hardware, rp23cnc-software | planned | [Plan Toolhead LIFT-Home Switch](hardware/2026/2026-08-30-plan-toolhead-lift-home-switch.md) |
| 2026-08-30 | `HW-20260830-004` | hardware | planned | [Set Proposed Toolhead Lift Datum](hardware/2026/2026-08-30-set-toolhead-lift-datum.md) |
| 2026-08-30 | `HW-20260830-003` | hardware | partial | [Record Preliminary Toolhead Preload Current](hardware/2026/2026-08-30-record-preliminary-toolhead-preload-current.md) |
| 2026-08-30 | `HW-20260830-002` | hardware | planned | [Add Toolhead Test Stop/Go Rules](hardware/2026/2026-08-30-toolhead-test-stop-go-rules.md) |
| 2026-08-30 | `HW-20260830-001` | hardware, rp23cnc-software | planned | [Plan Toolhead Motor/Preload Physical-Envelope Test](hardware/2026/2026-08-30-toolhead-motor-preload-test-plan.md) |
| 2026-08-28 | `WSW-20260828-001` | windows-software, rp23cnc-software, hardware | implemented | [Establish sequential agent execution policy](windows-software/2026/2026-08-28-agent-execution-policy.md) |
| 2026-08-25 | `RPSW-20260825-001` | rp23cnc-software, hardware | planned | [Plan Slow PI Toolhead Force Control](rp23cnc-software/2026/2026-08-25-plan-slow-pi-toolhead-force-control.md) |
| 2026-08-23 | `HW-20260823-009` | hardware | planned | [Plan motor-harness strain-relief CAD](hardware/2026/2026-08-23-plan-motor-harness-strain-relief-cad.md) |
| 2026-08-23 | `HW-20260823-008` | hardware | verified | [Verify X sheath motor-phase isolation](hardware/2026/2026-08-23-verify-x-sheath-motor-phase-isolation.md) |
| 2026-08-23 | `HW-20260823-007` | hardware | verified | [Verify supply protective-earth chassis path](hardware/2026/2026-08-23-verify-supply-pe-chassis-path.md) |
| 2026-08-23 | `HW-20260823-006` | hardware | verified | [Verify X sheath DC-negative isolation](hardware/2026/2026-08-23-verify-x-sheath-dc-negative-isolation.md) |
| 2026-08-23 | `HW-20260823-005` | hardware | verified | [Verify mains terminal and X sheath landing](hardware/2026/2026-08-23-verify-mains-terminal-and-x-sheath-landing.md) |
| 2026-08-23 | `HW-20260823-004` | hardware | implemented | [Record X sheath protective-earth bond](hardware/2026/2026-08-23-record-x-sheath-pe-bond.md) |
| 2026-08-23 | `HW-20260823-003` | hardware | implemented | [Correct X-axis Phase B cable color](hardware/2026/2026-08-23-correct-x-axis-phase-b-color.md) |
| 2026-08-23 | `HW-20260823-002` | hardware | implemented | [Set X-axis motor shielding plan](hardware/2026/2026-08-23-set-x-axis-motor-shielding-plan.md) |
| 2026-08-23 | `HW-20260823-001` | hardware, rp23cnc-software | implemented | [Partially terminate toolhead-control harness](hardware/2026/2026-08-23-partially-terminate-toolhead-control-harness.md) |
| 2026-08-22 | `RPSW-20260822-003` | rp23cnc-software, hardware | implemented | [Implement Dual-Core Magnetic Registration](rp23cnc-software/2026/2026-08-22-dual-core-magnetic-registration.md) |
| 2026-08-22 | `RPSW-20260822-002` | rp23cnc-software, hardware | implemented | [Correct RP2350 Toolhead Ownership](rp23cnc-software/2026/2026-08-22-correct-rp2350-toolhead-ownership.md) |
| 2026-08-22 | `RPSW-20260822-001` | rp23cnc-software, hardware | planned | [Motorless PRB/G38 Feasibility Test](rp23cnc-software/2026/2026-08-22-motorless-prb-g38-feasibility-test.md) |
| 2026-08-22 | `HW-20260822-002` | hardware, rp23cnc-software | implemented | [Route toolhead PC817 harness](hardware/2026/2026-08-22-route-toolhead-pc817-harness.md) |
| 2026-08-22 | `HW-20260822-001` | hardware, rp23cnc-software | verified | [Verify X/Y limit live inputs](hardware/2026/2026-08-22-verify-x-y-limit-live-inputs.md) |
| 2026-08-21 | `HW-20260821-001` | hardware | implemented | [Separate Mains and DC Routes](hardware/2026/2026-08-21-separate-mains-and-dc-routes.md) |
| 2026-08-20 | `HW-20260820-001` | hardware | verified | [Record Main Supply No-Load Path Test](hardware/2026/2026-08-20-record-main-supply-no-load-path-test.md) |
| 2026-08-19 | `HW-20260819-004` | hardware | implemented | [Record HD064RT Output Allocation](hardware/2026/2026-08-19-record-hcdc-output-allocation.md) |
| 2026-08-19 | `HW-20260819-003` | hardware | implemented | [Correct Installed Stepper Cable Shielding](hardware/2026/2026-08-19-correct-installed-stepper-cable-shielding.md) |
| 2026-08-19 | `HW-20260819-002` | hardware, rp23cnc-software | implemented | [Correct TB6600 Axis Switch Settings](hardware/2026/2026-08-19-correct-tb6600-axis-switch-settings.md) |
| 2026-08-19 | `HW-20260819-001` | hardware | verified | [Record Y Stepper Coil Pair and Shielded Cable Mapping](hardware/2026/2026-08-19-y-stepper-coil-pair-and-shielded-cable-mapping.md) |
| 2026-08-15 | `HW-20260815-003` | hardware, rp23cnc-software | implemented | [Set X/Y 20T baseline](hardware/2026/2026-08-15-set-xy-20t-baseline.md) |
| 2026-08-15 | `HW-20260815-002` | hardware, rp23cnc-software | implemented | [Select A-axis TB6600 baseline](hardware/2026/2026-08-15-select-a-axis-tb6600-baseline.md) |
| 2026-08-15 | `HW-20260815-001` | hardware | implemented | [Record TB6600 factory switch state](hardware/2026/2026-08-15-record-tb6600-factory-switch-state.md) |
| 2026-08-14 | `RPSW-20260814-006` | rp23cnc-software, windows-software | implemented | [Document ioSender in the system overview](rp23cnc-software/2026/2026-08-14-document-iosender-in-system-overview.md) |
| 2026-08-14 | `RPSW-20260814-004` | rp23cnc-software, hardware | verified | [RP23U5XBB grblHAL baseline build prepared](rp23cnc-software/2026/2026-08-14-rp23cnc-grblhal-baseline-build.md) |
| 2026-08-14 | `RPSW-20260814-003` | hardware, rp23cnc-software | verified | [Add E-09 TMAG5273 Intended-Wiring Test](rp23cnc-software/2026/2026-08-14-e09-tmag5273-verification-test.md) |
| 2026-08-14 | `RPSW-20260814-002` | hardware, rp23cnc-software | verified | [Add E-08 HX711 Rate and Noise Test](rp23cnc-software/2026/2026-08-14-e08-hx711-rate-noise-test.md) |
| 2026-08-14 | `RPSW-20260814-001` | hardware | implemented | [Add dedicated HX711 E-07 calibration sketch](rp23cnc-software/2026/2026-08-14-e07-hx711-calibration-sketch.md) |
| 2026-08-14 | `HW-20260814-005` | hardware, rp23cnc-software | planned | [Use the RP23CNC Halt input for the initial E-stop](hardware/2026/2026-08-14-rp23cnc-halt-input-estop.md) |
| 2026-08-14 | `HW-20260814-004` | hardware, rp23cnc-software | planned | [Select X/Y Roller-Lever Limit Switches](hardware/2026/2026-08-14-select-xy-roller-limit-switches.md) |
| 2026-08-14 | `HW-20260814-003` | hardware, rp23cnc-software | verified | [Correct TMAG5273 I2C SDA/SCL Mapping](hardware/2026/2026-08-14-correct-tmag-i2c-sda-scl-mapping.md) |
| 2026-08-14 | `HW-20260814-002` | hardware, rp23cnc-software | implemented | [Toolhead UART Service Calibration Fixture](hardware/2026/2026-08-14-toolhead-uart-service-calibration.md) |
| 2026-08-14 | `HW-20260814-001` | rp23cnc-software | implemented | [Require complete E-series test records](hardware/2026/2026-08-14-e-series-test-record-requirement.md) |
| 2026-08-12 | `HW-20260812-002` | hardware | implemented | [Record Toolhead Perfboard Wiring Progress](hardware/2026/2026-08-12-toolhead-perfboard-wiring-progress.md) |
| 2026-08-12 | `HW-20260812-001` | hardware | implemented | [Recorded load-cell wire mapping](hardware/2026/2026-08-12-load-cell-wire-colors.md) |
| 2026-08-11 | `HW-20260811-002` | hardware, rp23cnc-software | implemented | [Moved HX711 to adjacent GP0/GP1 pins](hardware/2026/2026-08-11-hx711-adjacent-jst-pins.md) |
| 2026-08-11 | `HW-20260811-001` | hardware, rp23cnc-software | superseded | [Reconciled E-stop and HD064RT topology (superseded)](hardware/2026/2026-08-11-estop-hd064rt-topology.md) |
| 2026-08-10 | `HW-20260810-005` | hardware, rp23cnc-software | implemented | [Direct-Header Toolhead Harness](hardware/2026/2026-08-10-direct-header-toolhead-harness.md) |
| 2026-08-10 | `HW-20260810-004` | hardware, rp23cnc-software | implemented | [Record Recommended System Test Sequence](hardware/2026/2026-08-10-recommended-system-test-sequence.md) |
| 2026-08-10 | `HW-20260810-001` | hardware, rp23cnc-software | verified | [Minimum-wire PC817 interface](hardware/2026/2026-08-10-minimum-wire-pc817-interface.md) |
| 2026-08-06 | `HW-20260806-002` | hardware, rp23cnc-software | implemented | [KiCad PC817C interface and active-low correction](hardware/2026/2026-08-06-kicad-pc817-perfboard-schematic.md) |
| 2026-08-06 | `HW-20260806-001` | hardware, rp23cnc-software | superseded | [Compact PC817 interface module proposal](hardware/2026/2026-08-06-compact-pc817-interface-module-proposal.md) |
| 2026-08-03 | `HW-20260803-003` | hardware | implemented | [B07WFGTNQC Optocoupler Interface](hardware/2026/2026-08-03-b07wfgtnqc-opto-interface.md) |
| 2026-08-03 | `HW-20260803-002` | hardware | implemented | [Power Distribution Document And Schematic](hardware/2026/2026-08-03-power-distribution-doc-and-schematic.md) |
| 2026-08-03 | `HW-20260803-001` | hardware | implemented | [RP23CNC To Pro Micro Interface Schematic](hardware/2026/2026-08-03-rp23cnc-pro-micro-interface-schematic.md) |
| 2026-08-02 | `HW-20260802-003` | hardware | implemented | [Onshape API CAD Workflow](hardware/2026/2026-08-02-onshape-api-cad-workflow.md) |
| 2026-08-02 | `HW-20260802-002` | hardware | implemented | [Shielded Stepper Cable Selection](hardware/2026/2026-08-02-shielded-stepper-cable-selection.md) |
| 2026-08-02 | `HW-20260802-001` | hardware, rp23cnc-software | implemented | [Toolhead Local 5 V Regulator And 6 V Rail](hardware/2026/2026-08-02-toolhead-local-5v-regulator.md) |
| 2026-07-31 | `RPSW-20260731-001` | rp23cnc-software, hardware | verified | [RP2350 Toolhead Prototype Firmware](rp23cnc-software/2026/2026-07-31-rp2350-toolhead-prototype-firmware.md) |
| 2026-07-31 | `HW-20260731-001` | hardware, rp23cnc-software | implemented | [Toolhead Wiring Diagram](hardware/2026/2026-07-31-toolhead-wiring-diagram.md) |
| 2026-07-04 | `WSW-20260704-001` | windows-software, rp23cnc-software, hardware | implemented | [Project Management Overview HTML](windows-software/2026/2026-07-04-project-management-overview-html.md) |
| 2026-07-04 | `RPSW-20260704-003` | rp23cnc-software, hardware | implemented | [Homing Data Flow Sheet](rp23cnc-software/2026/2026-07-04-homing-data-flow-sheet.md) |
| 2026-07-04 | `RPSW-20260704-002` | rp23cnc-software, hardware | implemented | [Pen-Up Calibration Workflow](rp23cnc-software/2026/2026-07-04-pen-up-calibration-workflow.md) |
| 2026-07-04 | `RPSW-20260704-001` | rp23cnc-software, hardware | planned | [Magnetic Homing Calibration Plan](rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md) |
| 2026-07-04 | `HW-20260704-003` | hardware, rp23cnc-software | implemented | [Fixed TMAG5273 Height](hardware/2026/2026-07-04-fixed-tmag5273-height.md) |
| 2026-07-04 | `HW-20260704-002` | hardware, rp23cnc-software | implemented | [RP23CNC Reference PDFs](hardware/2026/2026-07-04-rp23cnc-reference-pdfs.md) |
| 2026-07-04 | `HW-20260704-001` | hardware, rp23cnc-software | implemented | [Electronics Layout Wiring HTML](hardware/2026/2026-07-04-electronics-layout-wiring-html.md) |
| 2026-06-15 | `HW-20260615-001` | hardware | implemented | [Tecmojo Sliding Shelf Reference CAD](hardware/2026/2026-06-15-tecmojo-sliding-shelf-reference-cad.md) |
| 2026-06-09 | `RPSW-20260609-001` | rp23cnc-software, hardware | planned | [RP23U5XBB Ethernet Bring-Up Plan](rp23cnc-software/2026/2026-06-09-rp23u5xbb-ethernet-bring-up-plan.md) |
| 2026-06-07 | `WSW-20260607-006` | windows-software | verified | [Animated Pen-Up Travel](windows-software/2026/2026-06-07-animated-pen-up-travel.md) |
| 2026-06-07 | `WSW-20260607-005` | windows-software | verified | [Preview Cancellation](windows-software/2026/2026-06-07-preview-cancellation.md) |
| 2026-06-07 | `WSW-20260607-004` | windows-software, rp23cnc-software, hardware | verified | [Single-File Engineering Topic Index](windows-software/2026/2026-06-07-single-file-engineering-topic-index.md) |
| 2026-06-07 | `WSW-20260607-003` | windows-software, rp23cnc-software, hardware | verified | [Documentation Navigation and Index Automation](windows-software/2026/2026-06-07-documentation-navigation-and-index-automation.md) |
| 2026-06-07 | `WSW-20260607-002` | windows-software, rp23cnc-software, hardware | verified | [Continuous Maintainability Policy](windows-software/2026/2026-06-07-continuous-maintainability-policy.md) |
| 2026-06-07 | `WSW-20260607-001` | windows-software | verified | [Preview Build Progress and Responsive Processing](windows-software/2026/2026-06-07-preview-build-progress.md) |
<!-- END GENERATED CHANGES -->

Category-specific indexes:

- [`windows-software/README.md`](windows-software/README.md)
- [`rp23cnc-software/README.md`](rp23cnc-software/README.md)
- [`hardware/README.md`](hardware/README.md)
