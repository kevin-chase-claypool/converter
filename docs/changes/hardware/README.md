# Hardware Changes

Scope: mechanical parts, electronics, power distribution, wiring, pin
assignments, enclosures, assembly, and physical measurements.

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Status | Summary | Tags |
|---|---|---|---|---|
| 2026-08-30 | `HW-20260830-002` | planned | [Add Toolhead Test Stop/Go Rules](2026/2026-08-30-toolhead-test-stop-go-rules.md) | `toolhead`, `testing`, `safety`, `preload` |
| 2026-08-30 | `HW-20260830-001` | planned | [Plan Toolhead Motor/Preload Physical-Envelope Test](2026/2026-08-30-toolhead-motor-preload-test-plan.md) | `toolhead`, `preload`, `spring`, `n20`, `force-control`, `test-plan` |
| 2026-08-28 | `WSW-20260828-001` | implemented | [Establish sequential agent execution policy](../windows-software/2026/2026-08-28-agent-execution-policy.md) | `agent-workflow`, `token-efficiency`, `quality`, `project-policy` |
| 2026-08-25 | `RPSW-20260825-001` | planned | [Plan Slow PI Toolhead Force Control](../rp23cnc-software/2026/2026-08-25-plan-slow-pi-toolhead-force-control.md) | `toolhead`, `load-cell`, `n20`, `force-control`, `pi` |
| 2026-08-23 | `HW-20260823-009` | planned | [Plan motor-harness strain-relief CAD](2026/2026-08-23-plan-motor-harness-strain-relief-cad.md) | `cad`, `strain-relief`, `stepper`, `cable-management` |
| 2026-08-23 | `HW-20260823-008` | verified | [Verify X sheath motor-phase isolation](2026/2026-08-23-verify-x-sheath-motor-phase-isolation.md) | `protective-earth`, `shielding`, `isolation`, `wiring`, `stepper` |
| 2026-08-23 | `HW-20260823-007` | verified | [Verify supply protective-earth chassis path](2026/2026-08-23-verify-supply-pe-chassis-path.md) | `protective-earth`, `chassis`, `shielding`, `mains`, `wiring` |
| 2026-08-23 | `HW-20260823-006` | verified | [Verify X sheath DC-negative isolation](2026/2026-08-23-verify-x-sheath-dc-negative-isolation.md) | `protective-earth`, `shielding`, `isolation`, `wiring`, `x-axis` |
| 2026-08-23 | `HW-20260823-005` | verified | [Verify mains terminal and X sheath landing](2026/2026-08-23-verify-mains-terminal-and-x-sheath-landing.md) | `mains`, `protective-earth`, `shielding`, `wiring` |
| 2026-08-23 | `HW-20260823-004` | implemented | [Record X sheath protective-earth bond](2026/2026-08-23-record-x-sheath-pe-bond.md) | `protective-earth`, `mains`, `shielding`, `wiring`, `x-axis` |
| 2026-08-23 | `HW-20260823-003` | implemented | [Correct X-axis Phase B cable color](2026/2026-08-23-correct-x-axis-phase-b-color.md) | `stepper`, `wiring`, `x-axis`, `coil-pair` |
| 2026-08-23 | `HW-20260823-002` | implemented | [Set X-axis motor shielding plan](2026/2026-08-23-set-x-axis-motor-shielding-plan.md) | `stepper`, `cable`, `shielding`, `wiring`, `x-axis` |
| 2026-08-23 | `HW-20260823-001` | implemented | [Partially terminate toolhead-control harness](2026/2026-08-23-partially-terminate-toolhead-control-harness.md) | `toolhead`, `optocoupler`, `wiring`, `rp23cnc` |
| 2026-08-22 | `RPSW-20260822-003` | implemented | [Implement Dual-Core Magnetic Registration](../rp23cnc-software/2026/2026-08-22-dual-core-magnetic-registration.md) | `dual-core`, `magnetic-registration`, `centroid`, `probe` |
| 2026-08-22 | `RPSW-20260822-002` | implemented | [Correct RP2350 Toolhead Ownership](../rp23cnc-software/2026/2026-08-22-correct-rp2350-toolhead-ownership.md) | `toolhead`, `rp2350`, `tmag5273`, `documentation-correction` |
| 2026-08-22 | `RPSW-20260822-001` | planned | [Motorless PRB/G38 Feasibility Test](../rp23cnc-software/2026/2026-08-22-motorless-prb-g38-feasibility-test.md) | `probing`, `magnetic-calibration`, `motorless-test`, `g38` |
| 2026-08-22 | `HW-20260822-002` | implemented | [Route toolhead PC817 harness](2026/2026-08-22-route-toolhead-pc817-harness.md) | `toolhead`, `optocoupler`, `drag-chain`, `wiring` |
| 2026-08-22 | `HW-20260822-001` | verified | [Verify X/Y limit live inputs](2026/2026-08-22-verify-x-y-limit-live-inputs.md) | `limits`, `homing`, `safety`, `iosender` |
| 2026-08-21 | `HW-20260821-001` | implemented | [Separate Mains and DC Routes](2026/2026-08-21-separate-mains-and-dc-routes.md) | `mains`, `dc-power`, `wiring-segregation`, `e-11` |
| 2026-08-20 | `HW-20260820-001` | verified | [Record Main Supply No-Load Path Test](2026/2026-08-20-record-main-supply-no-load-path-test.md) | `power-supply`, `fuse-block`, `e-11`, `voltage` |
| 2026-08-19 | `HW-20260819-004` | implemented | [Record HD064RT Output Allocation](2026/2026-08-19-record-hcdc-output-allocation.md) | `hcdc`, `hd064rt`, `power-distribution`, `fuse`, `tb6600`, `rp23cnc` |
| 2026-08-19 | `HW-20260819-003` | implemented | [Correct Installed Stepper Cable Shielding](2026/2026-08-19-correct-installed-stepper-cable-shielding.md) | `stepper`, `cable`, `shielding`, `y-axis`, `protective-earth` |
| 2026-08-19 | `HW-20260819-002` | implemented | [Correct TB6600 Axis Switch Settings](2026/2026-08-19-correct-tb6600-axis-switch-settings.md) | `tb6600`, `dip-switch`, `microstepping`, `current-limit`, `x-axis`, `y-axis`, `a-axis` |
| 2026-08-19 | `HW-20260819-001` | verified | [Record Y Stepper Coil Pair and Shielded Cable Mapping](2026/2026-08-19-y-stepper-coil-pair-and-shielded-cable-mapping.md) | `y-axis`, `stepper`, `coil-pair`, `shielded-cable`, `wiring` |
| 2026-08-15 | `HW-20260815-003` | implemented | [Set X/Y 20T baseline](2026/2026-08-15-set-xy-20t-baseline.md) | `x-axis`, `y-axis`, `gt2`, `calibration` |
| 2026-08-15 | `HW-20260815-002` | implemented | [Select A-axis TB6600 baseline](2026/2026-08-15-select-a-axis-tb6600-baseline.md) | `a-axis`, `tb6600`, `microstepping`, `calibration` |
| 2026-08-15 | `HW-20260815-001` | implemented | [Record TB6600 factory switch state](2026/2026-08-15-record-tb6600-factory-switch-state.md) | `tb6600`, `stepper-driver`, `microstepping`, `current-limit` |
| 2026-08-14 | `RPSW-20260814-004` | verified | [RP23U5XBB grblHAL baseline build prepared](../rp23cnc-software/2026/2026-08-14-rp23cnc-grblhal-baseline-build.md) | `rp23cnc`, `rp23u5xbb`, `grblhal`, `firmware-build`, `web-builder` |
| 2026-08-14 | `RPSW-20260814-003` | verified | [Add E-09 TMAG5273 Intended-Wiring Test](../rp23cnc-software/2026/2026-08-14-e09-tmag5273-verification-test.md) | `tmag5273`, `i2c`, `qwiic`, `toolhead` |
| 2026-08-14 | `RPSW-20260814-002` | verified | [Add E-08 HX711 Rate and Noise Test](../rp23cnc-software/2026/2026-08-14-e08-hx711-rate-noise-test.md) | `hx711`, `sample-rate`, `noise`, `toolhead` |
| 2026-08-14 | `RPSW-20260814-001` | implemented | [Add dedicated HX711 E-07 calibration sketch](../rp23cnc-software/2026/2026-08-14-e07-hx711-calibration-sketch.md) | `hx711`, `load-cell`, `calibration`, `bench-test` |
| 2026-08-14 | `HW-20260814-005` | planned | [Use the RP23CNC Halt input for the initial E-stop](2026/2026-08-14-rp23cnc-halt-input-estop.md) | `estop`, `safety`, `rp23cnc` |
| 2026-08-14 | `HW-20260814-004` | planned | [Select X/Y Roller-Lever Limit Switches](2026/2026-08-14-select-xy-roller-limit-switches.md) | `limit-switch`, `homing`, `safety`, `rp23cnc` |
| 2026-08-14 | `HW-20260814-003` | verified | [Correct TMAG5273 I2C SDA/SCL Mapping](2026/2026-08-14-correct-tmag-i2c-sda-scl-mapping.md) | `tmag5273`, `i2c`, `qwiic`, `wiring-correction` |
| 2026-08-14 | `HW-20260814-002` | implemented | [Toolhead UART Service Calibration Fixture](2026/2026-08-14-toolhead-uart-service-calibration.md) | `toolhead`, `uart`, `hx711`, `calibration` |
| 2026-08-12 | `HW-20260812-002` | implemented | [Record Toolhead Perfboard Wiring Progress](2026/2026-08-12-toolhead-perfboard-wiring-progress.md) | `toolhead`, `drv8833`, `rp2350`, `power`, `testing` |
| 2026-08-12 | `HW-20260812-001` | implemented | [Recorded load-cell wire mapping](2026/2026-08-12-load-cell-wire-colors.md) | `hx711`, `load-cell`, `wiring` |
| 2026-08-11 | `HW-20260811-002` | implemented | [Moved HX711 to adjacent GP0/GP1 pins](2026/2026-08-11-hx711-adjacent-jst-pins.md) | `rp2350`, `hx711`, `jst`, `pin-assignment` |
| 2026-08-11 | `HW-20260811-001` | superseded | [Reconciled E-stop and HD064RT topology (superseded)](2026/2026-08-11-estop-hd064rt-topology.md) | `emergency-stop`, `power-distribution`, `hd064rt`, `rp23cnc` |
| 2026-08-10 | `HW-20260810-005` | implemented | [Direct-Header Toolhead Harness](2026/2026-08-10-direct-header-toolhead-harness.md) | `jst`, `harness`, `rp2350`, `pc817` |
| 2026-08-10 | `HW-20260810-004` | implemented | [Record Recommended System Test Sequence](2026/2026-08-10-recommended-system-test-sequence.md) | `test-plan`, `safety`, `sequencing` |
| 2026-08-10 | `HW-20260810-001` | verified | [Minimum-wire PC817 interface](2026/2026-08-10-minimum-wire-pc817-interface.md) | `pc817`, `perfboard`, `isolation`, `kicad`, `gpio20` |
| 2026-08-06 | `HW-20260806-002` | implemented | [KiCad PC817C interface and active-low correction](2026/2026-08-06-kicad-pc817-perfboard-schematic.md) | `kicad`, `optocoupler`, `perfboard`, `a-home` |
| 2026-08-06 | `HW-20260806-001` | superseded | [Compact PC817 interface module proposal](2026/2026-08-06-compact-pc817-interface-module-proposal.md) | `optocoupler`, `pcb-layout`, `toolhead`, `a-home` |
| 2026-08-03 | `HW-20260803-003` | implemented | [B07WFGTNQC Optocoupler Interface](2026/2026-08-03-b07wfgtnqc-opto-interface.md) | `optocoupler`, `level-shifting`, `toolhead-interface`, `wiring` |
| 2026-08-03 | `HW-20260803-002` | implemented | [Power Distribution Document And Schematic](2026/2026-08-03-power-distribution-doc-and-schematic.md) | `power-distribution`, `buck-regulator`, `wiring`, `toolhead` |
| 2026-08-03 | `HW-20260803-001` | implemented | [RP23CNC To Pro Micro Interface Schematic](2026/2026-08-03-rp23cnc-pro-micro-interface-schematic.md) | `wiring`, `interface`, `rp23cnc`, `toolhead` |
| 2026-08-02 | `HW-20260802-003` | implemented | [Onshape API CAD Workflow](2026/2026-08-02-onshape-api-cad-workflow.md) | `cad`, `onshape`, `api`, `documentation` |
| 2026-08-02 | `HW-20260802-002` | implemented | [Shielded Stepper Cable Selection](2026/2026-08-02-shielded-stepper-cable-selection.md) | `stepper`, `cable`, `shielding`, `drag-chain` |
| 2026-08-02 | `HW-20260802-001` | implemented | [Toolhead Local 5 V Regulator And 6 V Rail](2026/2026-08-02-toolhead-local-5v-regulator.md) | `power`, `toolhead`, `regulator`, `drag-chain` |
| 2026-07-31 | `RPSW-20260731-001` | verified | [RP2350 Toolhead Prototype Firmware](../rp23cnc-software/2026/2026-07-31-rp2350-toolhead-prototype-firmware.md) | `toolhead`, `rp2350`, `arduino`, `drv8833`, `hx711`, `tmag5273` |
| 2026-07-31 | `HW-20260731-001` | implemented | [Toolhead Wiring Diagram](2026/2026-07-31-toolhead-wiring-diagram.md) | `wiring`, `toolhead`, `rp2350`, `drv8833`, `hx711`, `tmag5273` |
| 2026-07-04 | `WSW-20260704-001` | implemented | [Project Management Overview HTML](../windows-software/2026/2026-07-04-project-management-overview-html.md) | `project-management`, `dashboard`, `documentation`, `navigation` |
| 2026-07-04 | `RPSW-20260704-003` | implemented | [Homing Data Flow Sheet](../rp23cnc-software/2026/2026-07-04-homing-data-flow-sheet.md) | `homing`, `data-flow`, `grblhal`, `tmag5273`, `toolhead` |
| 2026-07-04 | `RPSW-20260704-002` | implemented | [Pen-Up Calibration Workflow](../rp23cnc-software/2026/2026-07-04-pen-up-calibration-workflow.md) | `homing`, `calibration`, `toolhead`, `safety` |
| 2026-07-04 | `RPSW-20260704-001` | planned | [Magnetic Homing Calibration Plan](../rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md) | `homing`, `tmag5273`, `rp2040`, `magnetic-calibration`, `grblhal` |
| 2026-07-04 | `HW-20260704-003` | implemented | [Fixed TMAG5273 Height](2026/2026-07-04-fixed-tmag5273-height.md) | `tmag5273`, `magnetic-calibration`, `sensor-mount`, `homing` |
| 2026-07-04 | `HW-20260704-002` | implemented | [RP23CNC Reference PDFs](2026/2026-07-04-rp23cnc-reference-pdfs.md) | `rp23cnc`, `rp23u5xbb`, `references`, `manual` |
| 2026-07-04 | `HW-20260704-001` | implemented | [Electronics Layout Wiring HTML](2026/2026-07-04-electronics-layout-wiring-html.md) | `wiring`, `layout`, `electronics`, `rp23cnc`, `tmag5273`, `toolhead` |
| 2026-06-15 | `HW-20260615-001` | implemented | [Tecmojo Sliding Shelf Reference CAD](2026/2026-06-15-tecmojo-sliding-shelf-reference-cad.md) | `electronics-rack`, `sliding-shelf`, `step`, `cad`, `tecmojo-14130201` |
| 2026-06-09 | `RPSW-20260609-001` | planned | [RP23U5XBB Ethernet Bring-Up Plan](../rp23cnc-software/2026/2026-06-09-rp23u5xbb-ethernet-bring-up-plan.md) | `grblhal`, `ethernet`, `w5500`, `firmware-build` |
| 2026-06-07 | `WSW-20260607-004` | verified | [Single-File Engineering Topic Index](../windows-software/2026/2026-06-07-single-file-engineering-topic-index.md) | `engineering-log`, `topic-index`, `navigation`, `single-source` |
| 2026-06-07 | `WSW-20260607-003` | verified | [Documentation Navigation and Index Automation](../windows-software/2026/2026-06-07-documentation-navigation-and-index-automation.md) | `documentation`, `navigation`, `automation`, `maintainability` |
| 2026-06-07 | `WSW-20260607-002` | verified | [Continuous Maintainability Policy](../windows-software/2026/2026-06-07-continuous-maintainability-policy.md) | `maintainability`, `technical-debt`, `documentation`, `project-policy` |
<!-- END GENERATED CHANGES -->

See the [combined change index](../INDEX.md).
