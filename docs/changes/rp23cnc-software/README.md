# RP23CNC Software Changes

Scope: RP23CNC/grblHAL builds, controller configuration, plugins, settings,
transport, and other machine-side embedded software including the pen-pressure
controller.

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Status | Summary | Tags |
|---|---|---|---|---|
| 2026-09-24 | `WSW-20260924-013` | implemented | [Give the program's first pen-down a cold-seek dwell](../windows-software/2026/2026-09-24-first-pen-down-cold-seek-dwell.md) | `converter`, `pen-dwell`, `cold-seek`, `gp2`, `first-plot` |
| 2026-09-24 | `RPSW-20260924-004` | implemented | [Raise the toolhead force envelope 5 g](2026/2026-09-24-raise-force-envelope-5g.md) | `toolhead`, `force`, `calibration` |
| 2026-09-24 | `RPSW-20260924-003` | implemented | [Bound the coarse seek step and auto-recover from hard-limit overshoot](2026/2026-09-24-bound-coarse-seek-and-recover-hard-limit.md) | `toolhead`, `force-control`, `hard-limit`, `recovery`, `seek` |
| 2026-09-24 | `RPSW-20260924-002` | implemented | [Report magnet detection instead of a compile flag in the `ready=[...]` field](2026/2026-09-24-fix-toolhead-gp27-telemetry-field.md) | `telemetry`, `magnetic-homing`, `e-18` |
| 2026-09-24 | `RPSW-20260924-001` | verified | [Enable the integrated toolhead magnetic commissioning gate](2026/2026-09-24-enable-magnetic-commissioning-gate.md) | `p100`, `magnetic-homing`, `e-18`, `m-08`, `commissioning` |
| 2026-09-23 | `WSW-20260923-003` | implemented | [Set converter defaults for the installed toolhead](../windows-software/2026/2026-09-23-converter-defaults-for-toolhead.md) | `gcode`, `pen-plot`, `defaults`, `toolhead` |
| 2026-09-23 | `RPSW-20260923-016` | implemented | [Widen the force-hold band to ±10 g and move relief to 15 g](2026/2026-09-23-widen-hold-band.md) | `t03`, `hold`, `force-band`, `reliability` |
| 2026-09-23 | `RPSW-20260923-015` | verified | [Invert the grblHAL spindle enable to match the toolhead input](2026/2026-09-23-invert-spindle-enable-for-toolhead.md) | `f05`, `m3m5`, `spindle`, `toolhead`, `polarity` |
| 2026-09-23 | `RPSW-20260923-014` | implemented | [Require a full filter window of implausible samples before faulting](2026/2026-09-23-raise-implausible-fault-streak.md) | `t02`, `sensor-health`, `reliability` |
| 2026-09-23 | `RPSW-20260923-013` | implemented | [Stabilize warm-seek travel and stop motor-driven sensor-noise faults](2026/2026-09-23-stabilize-warm-seek-travel.md) | `t02`, `contact-seek`, `latency`, `sensor-health`, `learning` |
| 2026-09-23 | `RPSW-20260923-012` | implemented | [Split the seek settle by proximity to the target](2026/2026-09-23-split-seek-settle.md) | `t02`, `contact-seek`, `latency` |
| 2026-09-23 | `RPSW-20260923-011` | implemented | [Reduce the M5 clearance air gap to about 1 mm](2026/2026-09-23-reduce-m5-clearance-air-gap.md) | `m5`, `clearance`, `performance` |
| 2026-09-23 | `RPSW-20260923-010` | implemented | [Widen the warm coarse-phase force gate](2026/2026-09-23-widen-warm-coarse-force-gate.md) | `t02`, `contact-seek`, `learning` |
| 2026-09-23 | `RPSW-20260923-009` | implemented | [Learn warm-seek travel to traverse it with coarse pulses](2026/2026-09-23-learn-warm-seek-travel.md) | `t02`, `contact-seek`, `performance`, `learning` |
| 2026-09-23 | `RPSW-20260923-008` | implemented | [Replace the two-touch seek with a single descend](2026/2026-09-23-replace-two-touch-with-single-descend.md) | `t02`, `contact-seek`, `performance`, `simplification` |
| 2026-09-23 | `RPSW-20260923-007` | implemented | [Reject implausible CS1238 conversions](2026/2026-09-23-reject-implausible-cs1238-samples.md) | `cs1238`, `force-control`, `false-fault`, `observability` |
| 2026-09-23 | `RPSW-20260923-006` | implemented | [Reduce the sensing settle to the measured 300 ms](2026/2026-09-23-reduce-settle-to-measured-300ms.md) | `settle`, `performance`, `force-control`, `t02` |
| 2026-09-23 | `RPSW-20260923-005` | implemented | [Add a one-pulse settle trace to E-09E](2026/2026-09-23-add-e09e-settle-trace.md) | `settle`, `characterization`, `observability`, `e09e` |
| 2026-09-23 | `RPSW-20260923-004` | implemented | [Add hysteresis to the urgent over-force relief](2026/2026-09-23-add-hysteresis-to-urgent-relief.md) | `t03`, `force-control`, `hold`, `hunting` |
| 2026-09-23 | `RPSW-20260923-003` | implemented | [Report urgent over-force relief activity in telemetry](2026/2026-09-23-report-urgent-relief-telemetry.md) | `observability`, `telemetry`, `force-control` |
| 2026-09-23 | `RPSW-20260923-002` | implemented | [Add bounded urgent over-force relief to the hold loop](2026/2026-09-23-add-urgent-over-force-relief.md) | `t03`, `force-control`, `hold`, `hard-limit` |
| 2026-09-23 | `RPSW-20260923-001` | implemented | [Clamp the hold band below the hard-force limit](2026/2026-09-23-clamp-hold-band-below-hard-limit.md) | `t02`, `force-control`, `hard-limit`, `safety-margin` |
| 2026-09-22 | `WSW-20260922-002` | implemented | [File outstanding working-tree artifacts into the repository](../windows-software/2026/2026-09-22-file-outstanding-working-tree-artifacts.md) | `repository-hygiene`, `evidence`, `samples` |
| 2026-09-22 | `WSW-20260922-001` | implemented | [Ignore local tooling and build-scratch directories](../windows-software/2026/2026-09-22-ignore-local-tooling-and-build-scratch.md) | `repository-hygiene`, `tooling`, `commit-workflow` |
| 2026-09-22 | `RPSW-20260922-034` | implemented | [Settle the home contact seek on settled force](2026/2026-09-22-settle-contact-seek-on-settled-force.md) | `t02`, `contact-seek`, `settle`, `cs1238`, `force-control` |
| 2026-09-22 | `RPSW-20260922-033` | implemented | [Record E-07B trace-settle tuning](2026/2026-09-22-record-e07b-trace-settle-tuning.md) | `hx711`, `e07b`, `bench-diagnostic`, `historical-evidence` |
| 2026-09-22 | `RPSW-20260922-032` | implemented | [Refresh Tare after Normal Pen Clear](2026/2026-09-22-tare-after-normal-clear.md) | `cs1238`, `tare`, `pen-clear`, `m3-m5` |
| 2026-09-22 | `RPSW-20260922-031` | implemented | [Trend-gate Force-hold Corrections](2026/2026-09-22-trend-gate-hold-corrections.md) | `cs1238`, `moving-average`, `force-control`, `stiction` |
| 2026-09-22 | `RPSW-20260922-030` | implemented | [Bound Trend Contact to a Usable Envelope](2026/2026-09-22-bound-trend-contact-envelope.md) | `cs1238`, `force-limit`, `contact-detection`, `safety` |
| 2026-09-22 | `RPSW-20260922-029` | implemented | [Re-acquire Contact after M5 Clearance](2026/2026-09-22-reacquire-contact-after-clear.md) | `cs1238`, `m3-m5`, `contact-detection`, `force-control` |
| 2026-09-22 | `RPSW-20260922-028` | implemented | [Confirm Contact by Trend](2026/2026-09-22-confirm-contact-trend.md) | `cs1238`, `contact-detection`, `moving-average`, `force-control` |
| 2026-09-22 | `RPSW-20260922-027` | implemented | [Extend Fine Force-Tune Budget](2026/2026-09-22-extend-fine-force-tune-budget.md) | `cs1238`, `n20`, `force-tune`, `safety` |
| 2026-09-22 | `RPSW-20260922-026` | implemented | [Tare After Lift-Home Release](2026/2026-09-22-tare-after-lift-home-release.md) | `cs1238`, `tare`, `lift-home`, `gp2` |
| 2026-09-22 | `RPSW-20260922-025` | implemented | [Add Two-Touch Home Approach](2026/2026-09-22-add-two-touch-home-approach.md) | `cs1238`, `force-control`, `n20`, `surface-touch` |
| 2026-09-22 | `RPSW-20260922-024` | implemented | [Bound Moving-Average Hold Pulses](2026/2026-09-22-bound-moving-average-hold-pulses.md) | `cs1238`, `force-hold`, `n20`, `safety` |
| 2026-09-22 | `RPSW-20260922-023` | implemented | [Tare Only After Home Retract](2026/2026-09-22-tare-after-home-retract.md) | `cs1238`, `tare`, `contact-seek` |
| 2026-09-22 | `RPSW-20260922-022` | implemented | [Add Fine Home Contact Approach](2026/2026-09-22-add-fine-home-contact-approach.md) | `contact-seek`, `pulse-timing`, `force-limit` |
| 2026-09-22 | `RPSW-20260922-021` | implemented | [Revise Home Contact-Seek Pacing](2026/2026-09-22-revise-home-contact-seek-pacing.md) | `contact-seek`, `pulse-timing`, `cs1238` |
| 2026-09-22 | `RPSW-20260922-020` | implemented | [Bound Home-Origin Contact Seek](2026/2026-09-22-bound-home-origin-contact-seek.md) | `contact-seek`, `cs1238`, `pen-pressure` |
| 2026-09-22 | `RPSW-20260922-019` | implemented | [Make integrated toolhead telemetry quiet by default](2026/2026-09-22-quiet-integrated-toolhead-telemetry.md) | `serial-monitor`, `telemetry`, `fault-diagnostics`, `cs1238` |
| 2026-09-22 | `RPSW-20260922-018` | implemented | [Set integrated force target to 35 g and limit to 60 g](2026/2026-09-22-set-integrated-force-target-35g-limit-60g.md) | `cs1238`, `force-target`, `hard-force-limit`, `supervised-bench` |
| 2026-09-22 | `RPSW-20260922-017` | verified | [Set integrated lift timeout to 3000 ms](2026/2026-09-22-set-integrated-lift-timeout-3000ms.md) | `gp2`, `lift-home`, `timeout` |
| 2026-09-22 | `RPSW-20260922-016` | implemented | [Match integrated lift drive to validated bench pulses](2026/2026-09-22-increase-integrated-lift-drive.md) | `motor-drive`, `gp2`, `supervised-bench` |
| 2026-09-22 | `RPSW-20260922-015` | implemented | [Correct integrated motor-direction polarity](2026/2026-09-22-correct-integrated-direction-polarity.md) | `motor-direction`, `gp2`, `supervised-bench` |
| 2026-09-22 | `RPSW-20260922-014` | implemented | [Enable the mechanical-preload supervised bench build](2026/2026-09-22-enable-mechanical-preload-bench-build.md) | `supervised-bench`, `mechanical-preload`, `moving-average-force-control` |
| 2026-09-22 | `RPSW-20260922-013` | implemented | [Stage mechanical-preload M3/M5 behavior](2026/2026-09-22-stage-mechanical-preload-m3m5.md) | `mechanical-preload`, `m3-m5`, `cs1238`, `pen-clearance` |
| 2026-09-22 | `RPSW-20260922-012` | implemented | [Add E-09F manual down setup pulse](2026/2026-09-22-add-e09f-manual-down-setup.md) | `e-09f`, `n20`, `pen-installation`, `manual-control` |
| 2026-09-22 | `RPSW-20260922-011` | implemented | [Delay E-09F air-gap telemetry](2026/2026-09-22-delay-e09f-air-gap-telemetry.md) | `e-09f`, `cs1238`, `pen-clear`, `settling` |
| 2026-09-22 | `RPSW-20260922-010` | implemented | [Add E-09F manual retract recovery](2026/2026-09-22-add-e09f-manual-retract-recovery.md) | `e-09f`, `n20`, `retract`, `recovery`, `safety` |
| 2026-09-22 | `RPSW-20260922-009` | implemented | [Fix E-09F release hard-limit fault](2026/2026-09-22-fix-e09f-release-hard-limit.md) | `e-09f`, `cs1238`, `pen-clear`, `fault-handling` |
| 2026-09-22 | `RPSW-20260922-008` | implemented | [Add E-09F guarded force-hold test](2026/2026-09-22-add-e09f-guarded-force-hold.md) | `e-09f`, `cs1238`, `force-hold`, `pen-clear`, `safety` |
| 2026-09-22 | `RPSW-20260922-007` | implemented | [Refine E-09E pulses and stage pen-clear candidate](2026/2026-09-22-refine-e09e-pulses-and-stage-pen-clear.md) | `e-09e`, `n20`, `pen-clear`, `pulse-duration`, `safety` |
| 2026-09-22 | `RPSW-20260922-006` | implemented | [Add E-09E Serial Monitor shortcuts](2026/2026-09-22-add-e09e-serial-monitor-shortcuts.md) | `e-09e`, `uart`, `arduino-ide`, `kitchen-scale`, `safety` |
| 2026-09-22 | `RPSW-20260922-005` | implemented | [Route E-09E runtime through service UART](2026/2026-09-22-route-e09e-through-service-uart.md) | `e-09e`, `uart`, `usb-to-ttl`, `power-safety` |
| 2026-09-22 | `RPSW-20260922-004` | implemented | [Make E-09E pulse duration adjustable](2026/2026-09-22-make-e09e-pulse-duration-adjustable.md) | `e-09e`, `n20`, `pulse-duration`, `safety` |
| 2026-09-22 | `RPSW-20260922-003` | implemented | [Add E-09E installed-pen scale pulse check](2026/2026-09-22-add-e09e-pen-scale-pulse-check.md) | `cs1238`, `n20`, `kitchen-scale`, `e-09e`, `pen-pressure` |
| 2026-09-22 | `RPSW-20260922-002` | implemented | [Replace E-09C profile with cap-free repeat](2026/2026-09-22-replace-e09c-cap-free-calibration.md) | `cs1238`, `e-09c`, `calibration`, `load-cell`, `pen-pressure` |
| 2026-09-22 | `RPSW-20260922-001` | implemented | [Stage E-09C CS1238 force profile](2026/2026-09-22-stage-e09c-cs1238-force-profile.md) | `cs1238`, `e-09c`, `force-profile`, `pen-pressure`, `calibration` |
| 2026-09-21 | `WINSW-20260921-002` | implemented | [Add known-mass force-direction projection](../windows-software/2026/2026-09-21-add-known-mass-force-direction-projection.md) | `cs1238`, `known-mass`, `force-direction`, `pen-force`, `calibration`, `e-09c` |
| 2026-09-21 | `WINSW-20260921-001` | implemented | [Add Pro Micro known-mass calibration application](../windows-software/2026/2026-09-21-add-pro-micro-known-mass-calibration-app.md) | `cs1238`, `calibration`, `known-mass`, `plotting` |
| 2026-09-21 | `RPSW-20260921-002` | implemented | [Migrate Integrated Toolhead to CS1238 Backend](2026/2026-09-21-migrate-integrated-toolhead-cs1238-backend.md) | `CS1238`, `load-cell`, `force-control`, `safety-gates` |
| 2026-09-21 | `RP23CNC-20260921-008` | implemented | [Add post-release pen-clear air-gap pulse](2026/2026-09-21-add-post-release-pen-clear-air-gap.md) | `pen-clear`, `air-gap`, `n20`, `cs1238`, `t-01h` |
| 2026-09-21 | `RP23CNC-20260921-007` | implemented | [Add bounded GP27 toolhead-ready wait](2026/2026-09-21-add-bounded-gp27-toolhead-wait.md) | `gp27`, `prb`, `m3-m5`, `pen-ready`, `synchronization`, `f-05a` |
| 2026-09-19 | `WINSW-20260919-001` | implemented | [Add guided force-calibration analysis workflow](../windows-software/2026/2026-09-19-add-guided-force-calibration-analysis.md) | `force-calibration`, `pico2`, `cs1238`, `ina101`, `plotting` |
| 2026-09-15 | `HW-20260915-001` | planned | [Plan Pico 2 dual-sensor calibration DAQ](../hardware/2026/2026-09-15-plan-pico2-dual-sensor-calibration-daq.md) | `pico2`, `cs1238`, `ina101`, `strain-gauge`, `force-calibration`, `testing` |
| 2026-09-13 | `HW-20260913-013` | planned | [Plan CS1238 force-sensor replacement](../hardware/2026/2026-09-13-plan-cs1238-force-sensor-replacement.md) | `toolhead`, `cs1238`, `hx711`, `load-cell`, `force-control`, `testing` |
| 2026-09-13 | `HW-20260913-011` | implemented | [Add E07B fine force-pulse control](../hardware/2026/2026-09-13-add-e07b-fine-force-pulse-control.md) | `n20`, `force-control`, `pulse-duration`, `e-07b` |
| 2026-09-13 | `HW-20260913-010` | verified | [Calibrate E07B N20 direction](../hardware/2026/2026-09-13-calibrate-e07b-n20-direction.md) | `n20`, `drv8833`, `direction`, `e-07b` |
| 2026-09-13 | `HW-20260913-009` | verified | [Repair DRV8833 output solder joint](../hardware/2026/2026-09-13-repair-drv8833-output-solder-joint.md) | `drv8833`, `n20`, `solder-repair`, `e-14c` |
| 2026-09-13 | `HW-20260913-008` | implemented | [Add manual historical E-05 step test](../hardware/2026/2026-09-13-add-manual-legacy-e05-steps.md) | `n20`, `drv8833`, `e-05`, `pulse-duration`, `diagnostics` |
| 2026-09-13 | `HW-20260913-007` | implemented | [Preserve historical E-05 motor test](../hardware/2026/2026-09-13-preserve-historical-e05-motor-test.md) | `n20`, `drv8833`, `e-05`, `regression-test` |
| 2026-09-13 | `HW-20260913-006` | implemented | [Extend E07B actuator pulse range](../hardware/2026/2026-09-13-extend-e07b-actuator-pulse-range.md) | `n20`, `toolhead`, `pulse-duration`, `diagnostics` |
| 2026-09-13 | `HW-20260913-005` | implemented | [Add DRV8833 loaded-fault telemetry](../hardware/2026/2026-09-13-add-drv8833-loaded-fault-telemetry.md) | `drv8833`, `fault`, `diagnostics`, `toolhead` |
| 2026-09-13 | `HW-20260913-004` | planned | [Isolate N20 output-connection failure](../hardware/2026/2026-09-13-isolate-n20-output-connection-failure.md) | `drv8833`, `n20`, `toolhead`, `diagnostics` |
| 2026-09-13 | `HW-20260913-003` | implemented | [Add isolated DRV8833 output meter mode](../hardware/2026/2026-09-13-add-isolated-drv8833-output-meter-mode.md) | `drv8833`, `toolhead`, `diagnostics`, `e-14c` |
| 2026-09-13 | `HW-20260913-002` | implemented | [Add non-motion DRV8833 meter mode](../hardware/2026/2026-09-13-add-nonmotion-drv8833-meter-mode.md) | `drv8833`, `toolhead`, `diagnostics`, `e-14c` |
| 2026-09-13 | `HW-20260913-001` | implemented | [Correct confirmed DRV8833 sleep/fault mapping](../hardware/2026/2026-09-13-correct-drv8833-sleep-fault-mapping.md) | `drv8833`, `toolhead`, `wiring`, `pen-pressure` |
| 2026-09-12 | `RPSW-20260912-001` | verified | [Record P113 unified registration command](2026/2026-09-12-record-p113-unified-registration.md) | `P113`, `P100`, `P111`, `homing`, `magnetic-registration`, `G54` |
| 2026-09-11 | `WSW-20260911-001` | implemented | [Add Ontoly investigation prompt](../windows-software/2026/2026-09-11-add-ontoly-investigation-prompt.md) | `ontoly`, `architecture`, `impact-analysis`, `agent-workflow` |
| 2026-09-11 | `RPSW-20260911-013` | implemented | [Retune P100 Q5 Raster Density](2026/2026-09-11-retune-p100-q5-raster.md) | `P100`, `Q5`, `raster`, `scan-feed`, `safety` |
| 2026-09-11 | `RPSW-20260911-012` | implemented | [Add P112 Outer-Index Survey](2026/2026-09-11-add-p112-outer-index-survey.md) | `P112`, `P100`, `A-axis`, `index-magnet`, `M-09`, `safety` |
| 2026-09-11 | `RPSW-20260911-011` | implemented | [Isolate P100 System Homing](2026/2026-09-11-isolate-p100-system-homing.md) | `P100`, `P111`, `homing`, `grblHAL`, `safety` |
| 2026-09-11 | `RPSW-20260911-010` | verified | [Add P110 Q5 First G38 Row Diagnostic](2026/2026-09-11-add-p110-q5-first-g38-row-diagnostic.md) | `P100`, `P110`, `Q5`, `G38`, `probe`, `diagnostic`, `safety` |
| 2026-09-11 | `RPSW-20260911-009` | verified | [Add P109 Q5 Combined Diagnostic](2026/2026-09-11-add-p109-q5-combined-diagnostic.md) | `P100`, `P109`, `Q5`, `diagnostic`, `handshake`, `raster`, `safety` |
| 2026-09-11 | `RPSW-20260911-008` | verified | [Add P108 Q5 Handshake Diagnostic](2026/2026-09-11-add-p108-q5-handshake-diagnostic.md) | `P100`, `P108`, `Q5`, `handshake`, `diagnostic`, `safety` |
| 2026-09-11 | `RPSW-20260911-007` | verified | [Add P107 Q5 Preposition Diagnostic](2026/2026-09-11-add-p107-q5-preposition-diagnostic.md) | `P100`, `P107`, `Q5`, `diagnostic`, `homing`, `safety` |
| 2026-09-11 | `RPSW-20260911-006` | verified | [Add P100 Q5 Centroid Survey](2026/2026-09-11-add-p100-q5-centroid-survey.md) | `P100`, `Q5`, `centroid`, `raster`, `safety` |
| 2026-09-11 | `RPSW-20260911-005` | implemented | [Add P106 Manual Magnetic Survey](2026/2026-09-11-add-p106-manual-magnetic-survey.md) | `P100`, `Q3`, `P106`, `magnetic-survey`, `safety` |
| 2026-09-11 | `RPSW-20260911-004` | implemented | [Record P100 Q3 Candidate Scan Parameters](2026/2026-09-11-record-p100-q3-candidate-parameters.md) | `P100`, `Q3`, `scan-feed`, `tool-offset`, `safety` |
| 2026-09-11 | `RPSW-20260911-003` | implemented | [Record P100 Q3 Candidate Scan Rectangle](2026/2026-09-11-record-p100-q3-candidate-rectangle.md) | `P100`, `Q3`, `scan-bounds`, `G53`, `safety` |
| 2026-09-11 | `RPSW-20260911-002` | verified | [Enable Isolated P100 Q2 X/Y Homing](2026/2026-09-11-enable-isolated-p100-q2-home.md) | `P100`, `homing`, `safety`, `grblHAL` |
| 2026-09-11 | `RPSW-20260911-001` | verified | [Verify P100 Q1 probe handshake](2026/2026-09-11-verify-p100-q1-probe-handshake.md) | `p100`, `q1`, `probe`, `gp27`, `safety` |
| 2026-09-10 | `RPSW-20260910-003` | verified | [Correct P100 installed Aux0 polarity](2026/2026-09-10-correct-p100-aux-polarity.md) | `p100`, `aux0`, `gp28`, `safety`, `macro` |
| 2026-09-10 | `RPSW-20260910-002` | verified | [Verify real-magnet PRB/G38 path](2026/2026-09-10-prb-g38-magnetic-path.md) | `p100`, `f-08`, `probe`, `g38`, `magnetic-homing`, `safety` |
| 2026-09-10 | `RPSW-20260910-001` | verified | [Record motor-inert P100 handshake evidence](2026/2026-09-10-record-motor-inert-p100-handshake.md) | `p100`, `magnetic-homing`, `e-18`, `f-08`, `safety` |
| 2026-09-09 | `RPSW-20260909-002` | implemented | [Add motor-inert P100 handshake diagnostic](2026/2026-09-09-add-motor-inert-p100-handshake-diagnostic.md) | `p100`, `magnetic-homing`, `f-08`, `e-18`, `safety` |
| 2026-09-09 | `RPSW-20260909-001` | implemented | [Add lift-home status to bounded actuator test](2026/2026-09-09-add-lift-home-status-to-bounded-actuator-test.md) | `toolhead`, `t-01g`, `lift-home`, `uart`, `commissioning` |
| 2026-09-09 | `HW-20260909-003` | implemented | [Document toolhead pen-mount mechanics](../hardware/2026/2026-09-09-document-toolhead-pen-mount-mechanics.md) | `toolhead`, `pen-mount`, `spring`, `mechanics`, `t-01` |
| 2026-09-09 | `HW-20260909-002` | planned | [Order faster toolhead actuator candidates](../hardware/2026/2026-09-09-order-faster-toolhead-actuator-candidates.md) | `toolhead`, `n20`, `actuator`, `commissioning` |
| 2026-09-09 | `HW-20260909-001` | partial | [Verify guarded lift-home repeatability](../hardware/2026/2026-09-09-verify-guarded-lift-home-repeatability.md) | `toolhead`, `lift-home`, `t-01g`, `commissioning` |
| 2026-09-08 | `WSW-20260908-001` | implemented | [Calibrate the preview motion-time estimate](../windows-software/2026/2026-09-08-calibrate-preview-motion-estimate.md) | `preview`, `timing`, `m-06`, `calibration` |
| 2026-09-08 | `RPSW-20260908-002` | verified | [Fix integrated service-UART telemetry suppression](2026/2026-09-08-fix-integrated-service-uart-telemetry.md) | `toolhead`, `uart`, `telemetry`, `diagnostics` |
| 2026-09-08 | `RPSW-20260908-001` | implemented | [Add LIFT_HOME UART diagnostic sketch](2026/2026-09-08-add-lift-home-uart-diagnostic.md) | `toolhead`, `lift-home`, `uart`, `diagnostics`, `t-01g` |
| 2026-09-08 | `HW-20260908-004` | implemented | [Install LIFT_HOME switch input diagnostics](../hardware/2026/2026-09-08-install-lift-home-switch-input.md) | `toolhead`, `lift-home`, `t-01g`, `safety` |
| 2026-09-08 | `HW-20260908-003` | implemented | [Record current spring geometry](../hardware/2026/2026-09-08-record-current-spring-geometry.md) | `toolhead`, `spring`, `t-01a`, `safety` |
| 2026-09-08 | `HW-20260908-002` | verified | [Verify toolhead power-path gates](../hardware/2026/2026-09-08-verify-toolhead-power-path.md) | `toolhead`, `power`, `d36v50f6`, `drv8833`, `e-14` |
| 2026-09-07 | `HW-20260907-002` | verified | [Verify converter motion and guarded X/Y envelope](../hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md) | `m-03`, `m-06`, `m-07`, `soft-limits`, `g54`, `xya` |
| 2026-09-07 | `HW-20260907-001` | planned | [Require scale-force transfer calibration](../hardware/2026/2026-09-07-require-scale-force-transfer-calibration.md) | `force-calibration`, `hx711`, `grams-force`, `toolhead`, `testing` |
| 2026-09-06 | `RPSW-20260906-001` | implemented | [Add GP27 Normal-Status Guardrails](2026/2026-09-06-gp27-normal-status-guardrails.md) | `gp27`, `contact-ready`, `p100`, `safety` |
| 2026-09-06 | `HW-20260906-006` | verified | [Set temporary manual pen-corrected G54 XY reference](../hardware/2026/2026-09-06-set-temporary-manual-g54-xy-reference.md) | `g54`, `bed-center`, `tmag`, `pen-offset`, `commissioning` |
| 2026-09-06 | `HW-20260906-005` | verified | [Commission X/Y physical homing](../hardware/2026/2026-09-06-commission-xy-physical-homing.md) | `homing`, `limits`, `xy`, `m-07`, `commissioning` |
| 2026-09-06 | `HW-20260906-004` | verified | [Verify pen-free coordinated X/Y/A repeatability](../hardware/2026/2026-09-06-xya-coordinated-smoke-test.md) | `xya`, `coordinated-motion`, `m-06`, `repeatability`, `commissioning` |
| 2026-09-06 | `HW-20260906-003` | verified | [Configure the A axis without a finite travel limit](../hardware/2026/2026-09-06-a-axis-unlimited-travel-configuration.md) | `a-axis`, `rotary`, `soft-limits`, `configuration` |
| 2026-09-06 | `HW-20260906-002` | verified | [Verify X-axis rate and dimensional calibration](../hardware/2026/2026-09-06-x-axis-rate-and-dimensional-calibration.md) | `x-axis`, `rate`, `acceleration`, `dimensional-calibration`, `commissioning` |
| 2026-09-05 | `WSW-20260905-005` | implemented | [Consolidate current documentation ownership](../windows-software/2026/2026-09-05-consolidate-current-documentation.md) | `documentation`, `consolidation`, `source-of-truth`, `grblhal`, `toolhead` |
| 2026-09-05 | `WSW-20260905-004` | implemented | [Make converter programs self-contained for ioSender](../windows-software/2026/2026-09-05-self-contained-iosender-program-contract.md) | `iosender`, `grblhal`, `gcode`, `m3`, `m5`, `z-axis` |
| 2026-09-05 | `WSW-20260905-003` | implemented | [Record ioSender-to-converter compatibility review](../windows-software/2026/2026-09-05-iosender-converter-compatibility-review.md) | `iosender`, `grblhal`, `gcode`, `p100`, `integration-review` |
| 2026-09-05 | `WSW-20260905-002` | implemented | [Implement radius-aware A-axis feed for drawing](../windows-software/2026/2026-09-05-radius-aware-a-feed-requirement.md) | `theta`, `a-axis`, `tangential-speed`, `radius`, `feed-planning` |
| 2026-09-05 | `HW-20260905-006` | verified | [Verify Y-axis dimensional calibration](../hardware/2026/2026-09-05-m-03-y-axis-dimensional-calibration.md) | `y-axis`, `dimensional-calibration`, `steps-per-mm`, `commissioning` |
| 2026-09-05 | `HW-20260905-005` | verified | [Verify the Y-axis rate and acceleration baseline](../hardware/2026/2026-09-05-m-02-y-axis-rate-verification.md) | `y-axis`, `rate`, `acceleration`, `commissioning` |
| 2026-09-05 | `HW-20260905-004` | verified | [Verify the A-axis 12:1 bed ratio](../hardware/2026/2026-09-05-m-05-bed-ratio-verification.md) | `a-axis`, `bed-ratio`, `calibration`, `commissioning` |
| 2026-09-05 | `HW-20260905-003` | verified | [Correct A-axis calibration and characterize the F5000 ramp](../hardware/2026/2026-09-05-a-axis-rate-calibration-and-acceleration-check.md) | `a-axis`, `calibration`, `acceleration`, `tb6600`, `commissioning` |
| 2026-09-05 | `HW-20260905-002` | verified | [Verify installed TB6600 signal response](../hardware/2026/2026-09-05-tb6600-installed-signal-response.md) | `tb6600`, `step`, `direction`, `enable`, `e-03`, `commissioning` |
| 2026-09-05 | `HW-20260905-001` | verified | [RP23CNC USB source-selector bring-up](../hardware/2026/2026-09-05-rp23cnc-usb-source-selector-bringup.md) | `rp23cnc`, `usb`, `power-selector`, `tb6600` |
| 2026-09-04 | `WSW-20260904-001` | implemented | [Move pen/TMAG XY offset ownership to P100](../windows-software/2026/2026-09-04-remove-converter-tool-offset.md) | `coordinate-frames`, `tool-offset`, `p100`, `g54` |
| 2026-09-04 | `HW-20260904-007` | implemented | [Replace Toolhead Preload Spring](../hardware/2026/2026-09-04-replace-toolhead-preload-spring.md) | `toolhead`, `spring`, `preload`, `lift`, `testing` |
| 2026-09-04 | `HW-20260904-006` | implemented | [Make Pulse Response Tool-Specific During Preflight](../hardware/2026/2026-09-04-per-tool-pulse-response-preflight.md) | `toolhead`, `n20`, `force-control`, `interchangeable-tools`, `preflight` |
| 2026-09-03 | `RPSW-20260903-008` | implemented | [Add Opto-Isolation Presentation Slide](2026/2026-09-03-add-opto-isolation-presentation-slide.md) | `presentation`, `opto-isolation`, `wiring`, `p100` |
| 2026-09-03 | `HW-20260903-001` | implemented | [Record TB6600 signal and A-axis commissioning baseline](../hardware/2026/2026-09-03-record-tb6600-signal-and-a-axis-commissioning-baseline.md) | `tb6600`, `stepper`, `a-axis`, `calibration`, `homing` |
| 2026-09-02 | `RPSW-20260902-007` | implemented | [Full-Bleed Opening Slide Image](2026/2026-09-02-full-bleed-opening-slide-image.md) | `presentation`, `title-slide`, `toolhead` |
| 2026-09-02 | `RPSW-20260902-006` | implemented | [Refresh Summer Presentation Opening Render](2026/2026-09-02-refresh-summer-presentation-opening-render.md) | `presentation`, `toolhead`, `summer-progress` |
| 2026-09-02 | `RPSW-20260902-005` | implemented | [Expand P100 Presentation to Full Slide](2026/2026-09-02-expand-p100-presentation-to-full-slide.md) | `presentation`, `p100`, `interaction`, `layout` |
| 2026-09-02 | `RPSW-20260902-004` | implemented | [Align P100 Presentation Detail States](2026/2026-09-02-align-p100-presentation-detail-states.md) | `presentation`, `p100`, `interaction`, `correction` |
| 2026-09-02 | `RPSW-20260902-003` | implemented | [Add P100 Presentation Interaction](2026/2026-09-02-add-p100-presentation-interaction.md) | `presentation`, `p100`, `interaction`, `toolhead` |
| 2026-09-02 | `RPSW-20260902-002` | implemented | [Add Summer Progress Presentation](2026/2026-09-02-add-summer-progress-presentation.md) | `presentation`, `summer-progress`, `p100`, `toolhead`, `force-control` |
| 2026-09-02 | `RPSW-20260902-001` | implemented | [Add Current System Data Flow Chart](2026/2026-09-02-current-system-data-flow.md) | `data-flow`, `system-architecture`, `plotting`, `p100`, `toolhead`, `safety` |
| 2026-09-02 | `HW-20260902-001` | planned | [Plan Interchangeable-Tool Force Preflight](../hardware/2026/2026-09-02-plan-interchangeable-tool-force-preflight.md) | `toolhead`, `interchangeable-tools`, `load-cell`, `p100`, `pen-clear`, `testing` |
| 2026-09-01 | `HW-20260901-002` | planned | [Persist Toolhead Force Profile Separately from Boot Baseline](../hardware/2026/2026-09-01-persist-toolhead-force-profile.md) | `toolhead`, `load-cell`, `calibration`, `force-profile`, `startup-baseline`, `nonvolatile-storage` |
| 2026-09-01 | `HW-20260901-001` | planned | [Separate Normal Pen Clear from LIFT Home](../hardware/2026/2026-09-01-separate-pen-clear-from-lift-home.md) | `toolhead`, `m3`, `m5`, `pen-clear`, `lift-home`, `load-cell` |
| 2026-08-30 | `HW-20260830-005` | planned | [Plan Toolhead LIFT-Home Switch](../hardware/2026/2026-08-30-plan-toolhead-lift-home-switch.md) | `toolhead`, `lift-home`, `microswitch`, `gp2` |
| 2026-08-30 | `HW-20260830-001` | planned | [Plan Toolhead Motor/Preload Physical-Envelope Test](../hardware/2026/2026-08-30-toolhead-motor-preload-test-plan.md) | `toolhead`, `preload`, `spring`, `n20`, `force-control`, `test-plan` |
| 2026-08-28 | `WSW-20260828-001` | implemented | [Establish sequential agent execution policy](../windows-software/2026/2026-08-28-agent-execution-policy.md) | `agent-workflow`, `token-efficiency`, `quality`, `project-policy` |
| 2026-08-25 | `RPSW-20260825-001` | planned | [Plan Slow PI Toolhead Force Control](2026/2026-08-25-plan-slow-pi-toolhead-force-control.md) | `toolhead`, `load-cell`, `n20`, `force-control`, `pi` |
| 2026-08-23 | `HW-20260823-001` | implemented | [Partially terminate toolhead-control harness](../hardware/2026/2026-08-23-partially-terminate-toolhead-control-harness.md) | `toolhead`, `optocoupler`, `wiring`, `rp23cnc` |
| 2026-08-22 | `RPSW-20260822-003` | implemented | [Implement Dual-Core Magnetic Registration](2026/2026-08-22-dual-core-magnetic-registration.md) | `dual-core`, `magnetic-registration`, `centroid`, `probe` |
| 2026-08-22 | `RPSW-20260822-002` | implemented | [Correct RP2350 Toolhead Ownership](2026/2026-08-22-correct-rp2350-toolhead-ownership.md) | `toolhead`, `rp2350`, `tmag5273`, `documentation-correction` |
| 2026-08-22 | `RPSW-20260822-001` | planned | [Motorless PRB/G38 Feasibility Test](2026/2026-08-22-motorless-prb-g38-feasibility-test.md) | `probing`, `magnetic-calibration`, `motorless-test`, `g38` |
| 2026-08-22 | `HW-20260822-002` | implemented | [Route toolhead PC817 harness](../hardware/2026/2026-08-22-route-toolhead-pc817-harness.md) | `toolhead`, `optocoupler`, `drag-chain`, `wiring` |
| 2026-08-22 | `HW-20260822-001` | verified | [Verify X/Y limit live inputs](../hardware/2026/2026-08-22-verify-x-y-limit-live-inputs.md) | `limits`, `homing`, `safety`, `iosender` |
| 2026-08-19 | `HW-20260819-002` | implemented | [Correct TB6600 Axis Switch Settings](../hardware/2026/2026-08-19-correct-tb6600-axis-switch-settings.md) | `tb6600`, `dip-switch`, `microstepping`, `current-limit`, `x-axis`, `y-axis`, `a-axis` |
| 2026-08-15 | `HW-20260815-003` | implemented | [Set X/Y 20T baseline](../hardware/2026/2026-08-15-set-xy-20t-baseline.md) | `x-axis`, `y-axis`, `gt2`, `calibration` |
| 2026-08-15 | `HW-20260815-002` | implemented | [Select A-axis TB6600 baseline](../hardware/2026/2026-08-15-select-a-axis-tb6600-baseline.md) | `a-axis`, `tb6600`, `microstepping`, `calibration` |
| 2026-08-14 | `RPSW-20260814-006` | implemented | [Document ioSender in the system overview](2026/2026-08-14-document-iosender-in-system-overview.md) | `iosender`, `system-overview`, `gcode` |
| 2026-08-14 | `RPSW-20260814-004` | verified | [RP23U5XBB grblHAL baseline build prepared](2026/2026-08-14-rp23cnc-grblhal-baseline-build.md) | `rp23cnc`, `rp23u5xbb`, `grblhal`, `firmware-build`, `web-builder` |
| 2026-08-14 | `RPSW-20260814-003` | verified | [Add E-09 TMAG5273 Intended-Wiring Test](2026/2026-08-14-e09-tmag5273-verification-test.md) | `tmag5273`, `i2c`, `qwiic`, `toolhead` |
| 2026-08-14 | `RPSW-20260814-002` | verified | [Add E-08 HX711 Rate and Noise Test](2026/2026-08-14-e08-hx711-rate-noise-test.md) | `hx711`, `sample-rate`, `noise`, `toolhead` |
| 2026-08-14 | `HW-20260814-005` | planned | [Use the RP23CNC Halt input for the initial E-stop](../hardware/2026/2026-08-14-rp23cnc-halt-input-estop.md) | `estop`, `safety`, `rp23cnc` |
| 2026-08-14 | `HW-20260814-004` | planned | [Select X/Y Roller-Lever Limit Switches](../hardware/2026/2026-08-14-select-xy-roller-limit-switches.md) | `limit-switch`, `homing`, `safety`, `rp23cnc` |
| 2026-08-14 | `HW-20260814-003` | verified | [Correct TMAG5273 I2C SDA/SCL Mapping](../hardware/2026/2026-08-14-correct-tmag-i2c-sda-scl-mapping.md) | `tmag5273`, `i2c`, `qwiic`, `wiring-correction` |
| 2026-08-14 | `HW-20260814-002` | implemented | [Toolhead UART Service Calibration Fixture](../hardware/2026/2026-08-14-toolhead-uart-service-calibration.md) | `toolhead`, `uart`, `hx711`, `calibration` |
| 2026-08-14 | `HW-20260814-001` | implemented | [Require complete E-series test records](../hardware/2026/2026-08-14-e-series-test-record-requirement.md) | `verification`, `lab-notes`, `test-process` |
| 2026-08-11 | `HW-20260811-002` | implemented | [Moved HX711 to adjacent GP0/GP1 pins](../hardware/2026/2026-08-11-hx711-adjacent-jst-pins.md) | `rp2350`, `hx711`, `jst`, `pin-assignment` |
| 2026-08-11 | `HW-20260811-001` | superseded | [Reconciled E-stop and HD064RT topology (superseded)](../hardware/2026/2026-08-11-estop-hd064rt-topology.md) | `emergency-stop`, `power-distribution`, `hd064rt`, `rp23cnc` |
| 2026-08-10 | `HW-20260810-005` | implemented | [Direct-Header Toolhead Harness](../hardware/2026/2026-08-10-direct-header-toolhead-harness.md) | `jst`, `harness`, `rp2350`, `pc817` |
| 2026-08-10 | `HW-20260810-004` | implemented | [Record Recommended System Test Sequence](../hardware/2026/2026-08-10-recommended-system-test-sequence.md) | `test-plan`, `safety`, `sequencing` |
| 2026-08-10 | `HW-20260810-001` | verified | [Minimum-wire PC817 interface](../hardware/2026/2026-08-10-minimum-wire-pc817-interface.md) | `pc817`, `perfboard`, `isolation`, `kicad`, `gpio20` |
| 2026-08-06 | `HW-20260806-002` | implemented | [KiCad PC817C interface and active-low correction](../hardware/2026/2026-08-06-kicad-pc817-perfboard-schematic.md) | `kicad`, `optocoupler`, `perfboard`, `a-home` |
| 2026-08-06 | `HW-20260806-001` | superseded | [Compact PC817 interface module proposal](../hardware/2026/2026-08-06-compact-pc817-interface-module-proposal.md) | `optocoupler`, `pcb-layout`, `toolhead`, `a-home` |
| 2026-08-02 | `HW-20260802-001` | implemented | [Toolhead Local 5 V Regulator And 6 V Rail](../hardware/2026/2026-08-02-toolhead-local-5v-regulator.md) | `power`, `toolhead`, `regulator`, `drag-chain` |
| 2026-07-31 | `RPSW-20260731-001` | verified | [RP2350 Toolhead Prototype Firmware](2026/2026-07-31-rp2350-toolhead-prototype-firmware.md) | `toolhead`, `rp2350`, `arduino`, `drv8833`, `hx711`, `tmag5273` |
| 2026-07-31 | `HW-20260731-001` | implemented | [Toolhead Wiring Diagram](../hardware/2026/2026-07-31-toolhead-wiring-diagram.md) | `wiring`, `toolhead`, `rp2350`, `drv8833`, `hx711`, `tmag5273` |
| 2026-07-04 | `WSW-20260704-001` | implemented | [Project Management Overview HTML](../windows-software/2026/2026-07-04-project-management-overview-html.md) | `project-management`, `dashboard`, `documentation`, `navigation` |
| 2026-07-04 | `RPSW-20260704-003` | implemented | [Homing Data Flow Sheet](2026/2026-07-04-homing-data-flow-sheet.md) | `homing`, `data-flow`, `grblhal`, `tmag5273`, `toolhead` |
| 2026-07-04 | `RPSW-20260704-002` | implemented | [Pen-Up Calibration Workflow](2026/2026-07-04-pen-up-calibration-workflow.md) | `homing`, `calibration`, `toolhead`, `safety` |
| 2026-07-04 | `RPSW-20260704-001` | planned | [Magnetic Homing Calibration Plan](2026/2026-07-04-magnetic-homing-calibration-plan.md) | `homing`, `tmag5273`, `rp2040`, `magnetic-calibration`, `grblhal` |
| 2026-07-04 | `HW-20260704-003` | implemented | [Fixed TMAG5273 Height](../hardware/2026/2026-07-04-fixed-tmag5273-height.md) | `tmag5273`, `magnetic-calibration`, `sensor-mount`, `homing` |
| 2026-07-04 | `HW-20260704-002` | implemented | [RP23CNC Reference PDFs](../hardware/2026/2026-07-04-rp23cnc-reference-pdfs.md) | `rp23cnc`, `rp23u5xbb`, `references`, `manual` |
| 2026-07-04 | `HW-20260704-001` | implemented | [Electronics Layout Wiring HTML](../hardware/2026/2026-07-04-electronics-layout-wiring-html.md) | `wiring`, `layout`, `electronics`, `rp23cnc`, `tmag5273`, `toolhead` |
| 2026-06-09 | `RPSW-20260609-001` | planned | [RP23U5XBB Ethernet Bring-Up Plan](2026/2026-06-09-rp23u5xbb-ethernet-bring-up-plan.md) | `grblhal`, `ethernet`, `w5500`, `firmware-build` |
| 2026-06-07 | `WSW-20260607-004` | verified | [Single-File Engineering Topic Index](../windows-software/2026/2026-06-07-single-file-engineering-topic-index.md) | `engineering-log`, `topic-index`, `navigation`, `single-source` |
| 2026-06-07 | `WSW-20260607-003` | verified | [Documentation Navigation and Index Automation](../windows-software/2026/2026-06-07-documentation-navigation-and-index-automation.md) | `documentation`, `navigation`, `automation`, `maintainability` |
| 2026-06-07 | `WSW-20260607-002` | verified | [Continuous Maintainability Policy](../windows-software/2026/2026-06-07-continuous-maintainability-policy.md) | `maintainability`, `technical-debt`, `documentation`, `project-policy` |
<!-- END GENERATED CHANGES -->

See the [combined change index](../INDEX.md).
