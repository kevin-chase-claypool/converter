# RP23CNC Software Changes

Scope: RP23CNC/grblHAL builds, controller configuration, plugins, settings,
transport, and other machine-side embedded software including the pen-pressure
controller.

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Status | Summary | Tags |
|---|---|---|---|---|
| 2026-09-04 | `WSW-20260904-001` | implemented | [Move pen/TMAG XY offset ownership to P100](../windows-software/2026/2026-09-04-remove-converter-tool-offset.md) | `coordinate-frames`, `tool-offset`, `p100`, `g54` |
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
