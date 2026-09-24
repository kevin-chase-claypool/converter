# Windows Software Changes

Scope: the PySide6 Windows converter, conversion engine, launcher, desktop
workflow, and converter-specific samples.

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Status | Summary | Tags |
|---|---|---|---|---|
| 2026-09-24 | `WSW-20260924-012` | implemented | [Fix stroke-only elements being treated as invisible](2026/2026-09-24-fix-stroke-only-element-visibility.md) | `visibility`, `stroke`, `regression` |
| 2026-09-24 | `WSW-20260924-011` | implemented | [Restore manual-only preview refresh](2026/2026-09-24-restore-manual-preview-refresh.md) | `preview`, `shading`, `fill-pattern`, `ux` |
| 2026-09-24 | `WSW-20260924-010` | implemented | [Inset infill away from polygon boundaries](2026/2026-09-24-inset-infill-away-from-boundaries.md) | `infill`, `inset`, `boundary`, `correctness` |
| 2026-09-24 | `WSW-20260924-009` | implemented | [Drop sub-pen-width infill fragments](2026/2026-09-24-drop-sub-pen-width-infill-fragments.md) | `infill`, `pen-cycle`, `sliver`, `performance` |
| 2026-09-24 | `WSW-20260924-008` | implemented | [Subdivide polar moves linearly so A-axis-dominant lines stay straight](2026/2026-09-24-straighten-a-axis-polar-lines.md) | `polar`, `subdivision`, `straightness`, `a-axis` |
| 2026-09-24 | `WSW-20260924-007` | implemented | [Keep the pen down only between infill trails, never across shape outlines](2026/2026-09-24-bridge-only-between-infill-trails.md) | `infill`, `pen-up`, `bridge`, `correctness` |
| 2026-09-24 | `WSW-20260924-006` | implemented | [Fix fill leak and skip invisible white paths](2026/2026-09-24-fix-fill-leak-and-skip-white-paths.md) | `fill`, `correctness`, `point-in-polygon`, `invisibility` |
| 2026-09-24 | `WSW-20260924-005` | implemented | [Generate fill at on-paper resolution when the artwork is scaled down](2026/2026-09-24-fill-at-on-paper-resolution.md) | `performance`, `fill`, `scale`, `shading` |
| 2026-09-24 | `WSW-20260924-004` | implemented | [Eliminate duplicate theta planning during contour ordering](2026/2026-09-24-eliminate-duplicate-theta-planning.md) | `performance`, `theta`, `planner` |
| 2026-09-24 | `WSW-20260924-003` | implemented | [Tame cell-lattice fill density and fix triangular lattice over-generation](2026/2026-09-24-tame-cell-lattice-fill-density.md) | `shading`, `fill-pattern`, `performance`, `lattice` |
| 2026-09-24 | `WSW-20260924-002` | superseded | [Rebuild the preview when the fill pattern or raster shading changes (superseded)](2026/2026-09-24-refresh-preview-on-fill-pattern-change.md) | `preview`, `shading`, `fill-pattern`, `ux` |
| 2026-09-24 | `WSW-20260924-001` | implemented | [Speed up the parse/preview pipeline by removing duplicate theta candidates](2026/2026-09-24-speed-up-theta-planning.md) | `performance`, `theta`, `preview` |
| 2026-09-23 | `WSW-20260923-004` | implemented | [Add a curve-roundness test sample](2026/2026-09-23-add-curve-roundness-test-sample.md) | `sample`, `gcode`, `curve-flattening` |
| 2026-09-23 | `WSW-20260923-003` | implemented | [Set converter defaults for the installed toolhead](2026/2026-09-23-converter-defaults-for-toolhead.md) | `gcode`, `pen-plot`, `defaults`, `toolhead` |
| 2026-09-23 | `WSW-20260923-002` | implemented | [Subdivide draw moves so bed rotation traces straight lines](2026/2026-09-23-subdivide-polar-draw-moves.md) | `gcode`, `theta`, `polar`, `geometry` |
| 2026-09-23 | `WSW-20260923-001` | implemented | [Draw stroke centerlines by default instead of outlining the stroke width](2026/2026-09-23-draw-stroke-centerlines-by-default.md) | `gcode`, `pen-plot`, `performance` |
| 2026-09-22 | `WSW-20260922-002` | implemented | [File outstanding working-tree artifacts into the repository](2026/2026-09-22-file-outstanding-working-tree-artifacts.md) | `repository-hygiene`, `evidence`, `samples` |
| 2026-09-22 | `WSW-20260922-001` | implemented | [Ignore local tooling and build-scratch directories](2026/2026-09-22-ignore-local-tooling-and-build-scratch.md) | `repository-hygiene`, `tooling`, `commit-workflow` |
| 2026-09-22 | `RPSW-20260922-005` | implemented | [Route E-09E runtime through service UART](../rp23cnc-software/2026/2026-09-22-route-e09e-through-service-uart.md) | `e-09e`, `uart`, `usb-to-ttl`, `power-safety` |
| 2026-09-22 | `RPSW-20260922-004` | implemented | [Make E-09E pulse duration adjustable](../rp23cnc-software/2026/2026-09-22-make-e09e-pulse-duration-adjustable.md) | `e-09e`, `n20`, `pulse-duration`, `safety` |
| 2026-09-22 | `RPSW-20260922-003` | implemented | [Add E-09E installed-pen scale pulse check](../rp23cnc-software/2026/2026-09-22-add-e09e-pen-scale-pulse-check.md) | `cs1238`, `n20`, `kitchen-scale`, `e-09e`, `pen-pressure` |
| 2026-09-22 | `RPSW-20260922-001` | implemented | [Stage E-09C CS1238 force profile](../rp23cnc-software/2026/2026-09-22-stage-e09c-cs1238-force-profile.md) | `cs1238`, `e-09c`, `force-profile`, `pen-pressure`, `calibration` |
| 2026-09-21 | `WINSW-20260921-002` | implemented | [Add known-mass force-direction projection](2026/2026-09-21-add-known-mass-force-direction-projection.md) | `cs1238`, `known-mass`, `force-direction`, `pen-force`, `calibration`, `e-09c` |
| 2026-09-21 | `RP23CNC-20260921-007` | implemented | [Add bounded GP27 toolhead-ready wait](../rp23cnc-software/2026/2026-09-21-add-bounded-gp27-toolhead-wait.md) | `gp27`, `prb`, `m3-m5`, `pen-ready`, `synchronization`, `f-05a` |
| 2026-09-19 | `RPSW-20260919-001` | implemented | [Add Pico 2 dual-sensor DAQ firmware](../rp23cnc-software/2026/2026-09-19-add-pico2-dual-sensor-daq-firmware.md) | `pico2`, `cs1238`, `ina101`, `force-calibration`, `raw-data` |
| 2026-09-15 | `HW-20260915-001` | planned | [Plan Pico 2 dual-sensor calibration DAQ](../hardware/2026/2026-09-15-plan-pico2-dual-sensor-calibration-daq.md) | `pico2`, `cs1238`, `ina101`, `strain-gauge`, `force-calibration`, `testing` |
| 2026-09-11 | `WSW-20260911-001` | implemented | [Add Ontoly investigation prompt](2026/2026-09-11-add-ontoly-investigation-prompt.md) | `ontoly`, `architecture`, `impact-analysis`, `agent-workflow` |
| 2026-09-08 | `WSW-20260908-001` | implemented | [Calibrate the preview motion-time estimate](2026/2026-09-08-calibrate-preview-motion-estimate.md) | `preview`, `timing`, `m-06`, `calibration` |
| 2026-09-07 | `HW-20260907-002` | verified | [Verify converter motion and guarded X/Y envelope](../hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md) | `m-03`, `m-06`, `m-07`, `soft-limits`, `g54`, `xya` |
| 2026-09-06 | `WINSW-20260906-001` | implemented | [Center G54 output and correct the M-06 sample](2026/2026-09-06-center-g54-output-and-correct-m06-sample.md) | `g54`, `coordinates`, `parking`, `m-06`, `a-axis` |
| 2026-09-05 | `WSW-20260905-007` | implemented | [Share the preview motion plan](2026/2026-09-05-share-preview-motion-plan.md) | `preview`, `performance`, `motion-planning` |
| 2026-09-05 | `WSW-20260905-006` | implemented | [Make the production preview safe and complete](2026/2026-09-05-production-preview-safety.md) | `preview`, `gcode`, `validation`, `safety`, `iosender` |
| 2026-09-05 | `WSW-20260905-005` | implemented | [Consolidate current documentation ownership](2026/2026-09-05-consolidate-current-documentation.md) | `documentation`, `consolidation`, `source-of-truth`, `grblhal`, `toolhead` |
| 2026-09-05 | `WSW-20260905-004` | implemented | [Make converter programs self-contained for ioSender](2026/2026-09-05-self-contained-iosender-program-contract.md) | `iosender`, `grblhal`, `gcode`, `m3`, `m5`, `z-axis` |
| 2026-09-05 | `WSW-20260905-003` | implemented | [Record ioSender-to-converter compatibility review](2026/2026-09-05-iosender-converter-compatibility-review.md) | `iosender`, `grblhal`, `gcode`, `p100`, `integration-review` |
| 2026-09-05 | `WSW-20260905-002` | implemented | [Implement radius-aware A-axis feed for drawing](2026/2026-09-05-radius-aware-a-feed-requirement.md) | `theta`, `a-axis`, `tangential-speed`, `radius`, `feed-planning` |
| 2026-09-04 | `WSW-20260904-001` | implemented | [Move pen/TMAG XY offset ownership to P100](2026/2026-09-04-remove-converter-tool-offset.md) | `coordinate-frames`, `tool-offset`, `p100`, `g54` |
| 2026-09-03 | `RPSW-20260903-008` | implemented | [Add Opto-Isolation Presentation Slide](../rp23cnc-software/2026/2026-09-03-add-opto-isolation-presentation-slide.md) | `presentation`, `opto-isolation`, `wiring`, `p100` |
| 2026-09-02 | `RPSW-20260902-007` | implemented | [Full-Bleed Opening Slide Image](../rp23cnc-software/2026/2026-09-02-full-bleed-opening-slide-image.md) | `presentation`, `title-slide`, `toolhead` |
| 2026-09-02 | `RPSW-20260902-006` | implemented | [Refresh Summer Presentation Opening Render](../rp23cnc-software/2026/2026-09-02-refresh-summer-presentation-opening-render.md) | `presentation`, `toolhead`, `summer-progress` |
| 2026-09-02 | `RPSW-20260902-005` | implemented | [Expand P100 Presentation to Full Slide](../rp23cnc-software/2026/2026-09-02-expand-p100-presentation-to-full-slide.md) | `presentation`, `p100`, `interaction`, `layout` |
| 2026-09-02 | `RPSW-20260902-004` | implemented | [Align P100 Presentation Detail States](../rp23cnc-software/2026/2026-09-02-align-p100-presentation-detail-states.md) | `presentation`, `p100`, `interaction`, `correction` |
| 2026-09-02 | `RPSW-20260902-003` | implemented | [Add P100 Presentation Interaction](../rp23cnc-software/2026/2026-09-02-add-p100-presentation-interaction.md) | `presentation`, `p100`, `interaction`, `toolhead` |
| 2026-09-02 | `RPSW-20260902-002` | implemented | [Add Summer Progress Presentation](../rp23cnc-software/2026/2026-09-02-add-summer-progress-presentation.md) | `presentation`, `summer-progress`, `p100`, `toolhead`, `force-control` |
| 2026-09-02 | `RPSW-20260902-001` | implemented | [Add Current System Data Flow Chart](../rp23cnc-software/2026/2026-09-02-current-system-data-flow.md) | `data-flow`, `system-architecture`, `plotting`, `p100`, `toolhead`, `safety` |
| 2026-08-28 | `WSW-20260828-001` | implemented | [Establish sequential agent execution policy](2026/2026-08-28-agent-execution-policy.md) | `agent-workflow`, `token-efficiency`, `quality`, `project-policy` |
| 2026-08-14 | `RPSW-20260814-006` | implemented | [Document ioSender in the system overview](../rp23cnc-software/2026/2026-08-14-document-iosender-in-system-overview.md) | `iosender`, `system-overview`, `gcode` |
| 2026-07-04 | `WSW-20260704-001` | implemented | [Project Management Overview HTML](2026/2026-07-04-project-management-overview-html.md) | `project-management`, `dashboard`, `documentation`, `navigation` |
| 2026-06-07 | `WSW-20260607-006` | verified | [Animated Pen-Up Travel](2026/2026-06-07-animated-pen-up-travel.md) | `preview`, `playback`, `travel`, `simulation` |
| 2026-06-07 | `WSW-20260607-005` | verified | [Preview Cancellation](2026/2026-06-07-preview-cancellation.md) | `preview`, `cancellation`, `threading`, `safety` |
| 2026-06-07 | `WSW-20260607-004` | verified | [Single-File Engineering Topic Index](2026/2026-06-07-single-file-engineering-topic-index.md) | `engineering-log`, `topic-index`, `navigation`, `single-source` |
| 2026-06-07 | `WSW-20260607-003` | verified | [Documentation Navigation and Index Automation](2026/2026-06-07-documentation-navigation-and-index-automation.md) | `documentation`, `navigation`, `automation`, `maintainability` |
| 2026-06-07 | `WSW-20260607-002` | verified | [Continuous Maintainability Policy](2026/2026-06-07-continuous-maintainability-policy.md) | `maintainability`, `technical-debt`, `documentation`, `project-policy` |
| 2026-06-07 | `WSW-20260607-001` | verified | [Preview Build Progress and Responsive Processing](2026/2026-06-07-preview-build-progress.md) | `preview`, `ui`, `threading`, `progress`, `elapsed-time` |
<!-- END GENERATED CHANGES -->

See the [combined change index](../INDEX.md).
