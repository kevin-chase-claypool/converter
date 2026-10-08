# Windows Software Changes

Scope: the PySide6 Windows converter, conversion engine, launcher, desktop
workflow, and converter-specific samples.

Newest changes appear first.

<!-- BEGIN GENERATED CHANGES -->
| Date | ID | Status | Summary | Tags |
|---|---|---|---|---|
| 2026-10-08 | `WSW-20261008-005` | implemented | [Set the CMYK defaults to the owner's gamma-led tuning](2026-10-08-cmyk-gamma-led-defaults.md) | `cmyk`, `defaults`, `gamma`, `tone` |
| 2026-10-08 | `WSW-20261008-004` | implemented | [Extend contrast past 200 % and push colour into the mix](2026-10-08-cmyk-contrast-headroom-color.md) | `cmyk`, `contrast`, `tone`, `defaults` |
| 2026-10-08 | `WSW-20261008-003` | implemented | [Add a brightness lift and restore contrast to 200 %](2026-10-08-cmyk-brightness-control.md) | `cmyk`, `tone`, `brightness`, `defaults` |
| 2026-10-08 | `WSW-20261008-002` | implemented | [Open rectilinear light tones instead of hatching them](2026-10-08-cmyk-rectilinear-light-stretch.md) | `cmyk`, `rectilinear`, `tone`, `screening` |
| 2026-10-08 | `WSW-20261008-001` | implemented | [Soften the CMYK tone curve and rebalance the defaults](2026-10-08-cmyk-soft-contrast-defaults.md) | `cmyk`, `tone`, `contrast`, `defaults`, `rectilinear` |
| 2026-10-07 | `WSW-20261007-025` | implemented | [Set the CMYK defaults to the owner's tuned rectilinear set](2026-10-07-cmyk-owner-tuned-rectilinear-defaults.md) | `cmyk`, `defaults`, `rectilinear` |
| 2026-10-07 | `WSW-20261007-024` | implemented | [Tune the CMYK defaults for the rectilinear fill](2026-10-07-cmyk-rectilinear-defaults.md) | `cmyk`, `defaults`, `rectilinear` |
| 2026-10-07 | `WSW-20261007-023` | implemented | [Ink simulation draws at the real pen width and explains the pitch chain](2026-10-07-cmyk-ink-sim-pen-width.md) | `cmyk`, `preview`, `ink-simulation` |
| 2026-10-07 | `WSW-20261007-022` | implemented | [Add an ink-simulation (multiply) preview for CMYK](2026-10-07-cmyk-ink-simulation-preview.md) | `cmyk`, `preview`, `opengl`, `ink-simulation` |
| 2026-10-07 | `WSW-20261007-021` | implemented | [Fix rectilinear stitching on multi-dash rows](2026-10-07-cmyk-rectilinear-stitch-fix.md) | `cmyk`, `rectilinear`, `bugfix` |
| 2026-10-07 | `WSW-20261007-020` | implemented | [Add a rectilinear fill screen that joins rows](2026-10-07-cmyk-rectilinear-fill.md) | `cmyk`, `screening`, `rectilinear`, `pen-cycles` |
| 2026-10-07 | `WSW-20261007-019` | implemented | [Show per-ink M3 counts in the preview data area](2026-10-07-cmyk-preview-m3-counts.md) | `cmyk`, `preview`, `user-interface` |
| 2026-10-07 | `WSW-20261007-018` | implemented | [Filter CMYK preview layers live instead of re-rendering](2026-10-07-cmyk-live-preview-layers.md) | `cmyk`, `preview`, `opengl`, `user-interface` |
| 2026-10-07 | `WSW-20261007-017` | implemented | [Apply the CMYK Artwork scale to the screened marks](2026-10-07-cmyk-artwork-scale.md) | `cmyk`, `bugfix`, `user-interface` |
| 2026-10-07 | `WSW-20261007-016` | implemented | [Raise the CMYK max-marks cap](2026-10-07-cmyk-max-marks-cap.md) | `cmyk`, `user-interface`, `screening` |
| 2026-10-07 | `WSW-20261007-015` | implemented | [Set the CMYK defaults to the owner's tuned workflow](2026-10-07-cmyk-owner-defaults.md) | `cmyk`, `defaults`, `crosshatch`, `user-interface` |
| 2026-10-07 | `WSW-20261007-014` | implemented | [Extend crosshatch screens past four families](2026-10-07-cmyk-crosshatch-levels.md) | `cmyk`, `screening`, `crosshatch` |
| 2026-10-07 | `WSW-20261007-013` | implemented | [Raise the CMYK resolution cap for large sources](2026-10-07-cmyk-resolution-cap.md) | `cmyk`, `resolution`, `user-interface` |
| 2026-10-07 | `WSW-20261007-012` | implemented | [Print the calibration mix cells at the dense spot spacing](2026-10-07-cmyk-dense-mix-cells.md) | `cmyk`, `calibration`, `test-print`, `ai-handoff` |
| 2026-10-07 | `WSW-20261007-011` | implemented | [Add the C+M+Y+K quad to the calibration mixes](2026-10-07-cmyk-calibration-quad-mix.md) | `cmyk`, `calibration`, `test-print`, `ai-handoff` |
| 2026-10-07 | `WSW-20261007-010` | implemented | [Strip the calibration sheet to what a scan needs](2026-10-07-cmyk-quiet-calibration-sheet.md) | `cmyk`, `calibration`, `test-print`, `ai-handoff`, `line-screen` |
| 2026-10-07 | `WSW-20261007-009` | implemented | [Make CMYK calibration scans analyzable from the image alone](2026-10-07-cmyk-calibration-ai-handoff.md) | `cmyk`, `calibration`, `test-print`, `ai-handoff`, `tools` |
| 2026-10-07 | `WSW-20261007-008` | implemented | [Let the CMYK calibration sheet follow the screen style](2026-10-07-cmyk-calibration-line-screens.md) | `cmyk`, `calibration`, `line-screen`, `crosshatch`, `test-print` |
| 2026-10-07 | `WSW-20261007-007` | implemented | [Add a labeled CMYK calibration sheet and scan tool](2026-10-07-cmyk-calibration-sheet.md) | `cmyk`, `calibration`, `test-print`, `color-separation`, `tools` |
| 2026-10-07 | `WSW-20261007-006` | implemented | [Add a Red motion lines toggle to the preview panel](2026-10-07-preview-motion-lines-toggle.md) | `preview`, `user-interface`, `opengl` |
| 2026-10-07 | `WSW-20261007-005` | implemented | [Photo-ready CMYK defaults: auto levels, solid dots, 1.2 mm pitch](2026-10-07-cmyk-photo-defaults.md) | `cmyk`, `defaults`, `auto-levels`, `halftone`, `photo` |
| 2026-10-07 | `WSW-20261007-004` | implemented | [Plan the four CMYK programs automatically; drop the Analyze button](2026-10-07-cmyk-background-planning.md) | `cmyk`, `workflow`, `preview`, `cost-analysis`, `x-theta`, `y-theta` |
| 2026-10-07 | `WSW-20261007-003` | implemented | [Draw the CMYK preview per ink colour](2026-10-07-cmyk-ink-preview.md) | `cmyk`, `opengl`, `preview`, `color-separation`, `generator-tabs` |
| 2026-10-07 | `WSW-20261007-002` | implemented | [Add six CMYK mark styles and an overdraw control](2026-10-07-cmyk-mark-styles.md) | `cmyk`, `color-separation`, `screening`, `line-screen`, `tsp`, `contours`, `gcode` |
| 2026-10-07 | `WSW-20261007-001` | implemented | [Add the CMYK separation tool with one G-code file per ink](2026-10-07-cmyk-separation-tool.md) | `cmyk`, `color-separation`, `generator-tabs`, `gcode`, `cost-analysis`, `x-theta`, `y-theta` |
| 2026-10-06 | `WSW-20261006-031` | implemented | [Raise the pen-up dwell default to 1000 ms](2026-10-06-pen-up-dwell-1000ms.md) | `converter`, `pen`, `timing` |
| 2026-10-06 | `WSW-20261006-030` | implemented | [Fix Vector Trace closed loops collapsing to invisible paths](2026-10-06-vector-trace-closed-loop-fix.md) | `generators`, `bug-fix`, `vector-trace` |
| 2026-10-06 | `WSW-20261006-029` | implemented | [High-quality tier: Stipple/TSP, Reaction-Diffusion, and Vector Trace](2026-10-06-high-quality-stipple-rd-trace.md) | `generators`, `quality` |
| 2026-10-06 | `WSW-20261006-028` | implemented | [Add Plotterfun, Voronoi, Path Prep, and Layers tools](2026-10-06-plotterfun-voronoi-path-prep-layers.md) | `user-interface`, `generators` |
| 2026-10-06 | `WSW-20261006-027` | implemented | [Group tools by input type: Photo-based and Algorithm only](2026-10-06-photo-vs-algorithm-groups.md) | `user-interface`, `navigation`, `generators` |
| 2026-10-06 | `WSW-20261006-026` | implemented | [Recommended default settings for every tool](2026-10-06-recommended-default-settings.md) | `user-interface`, `generators`, `defaults` |
| 2026-10-06 | `WSW-20261006-025` | implemented | [Tool accuracy audit and source-parity fixes](2026-10-06-tools-accuracy-audit-fixes.md) | `generators`, `fidelity`, `audit` |
| 2026-10-06 | `WSW-20261006-024` | implemented | [Add SquiggleCam, Pixel Art, and Wobble tools](2026-10-06-squigglecam-pixel-art-wobble.md) | `user-interface`, `generators` |
| 2026-10-06 | `WSW-20261006-023` | implemented | [Flow Field formula source](2026-10-06-flow-field-formulas.md) | `generators`, `flow-field`, `fidelity` |
| 2026-10-06 | `WSW-20261006-022` | implemented | [Add File / Tools / View / Help menus and move tool selection into Tools](2026-10-06-menu-bar-navigation.md) | `user-interface`, `navigation` |
| 2026-10-06 | `WSW-20261006-021` | implemented | [Replace the tab bar with an All tools dashboard](2026-10-06-all-tools-dashboard.md) | `user-interface`, `navigation` |
| 2026-10-06 | `WSW-20261006-020` | implemented | [Generator fidelity audit, restored options, and attribution corrections](2026-10-06-fidelity-audit-and-restorations.md) | `generators`, `documentation`, `fidelity` |
| 2026-10-06 | `WSW-20261006-019` | implemented | [Raise Artwork scale to 1000 percent](2026-10-06-artwork-scale-range-1000.md) | `user-interface`, `generators`, `scale` |
| 2026-10-06 | `WSW-20261006-018` | implemented | [Add Text, Substitution, and Postcard generator tabs](2026-10-06-text-substitution-postcard-tabs.md) | `user-interface`, `generators`, `text` |
| 2026-10-06 | `WSW-20261006-017` | implemented | [Plot generator pages 1:1 so Artwork scale works](2026-10-06-generator-1to1-preview.md) | `user-interface`, `generators`, `scale` |
| 2026-10-06 | `WSW-20261006-016` | implemented | [Add Harmonograph, Snowflake, and Truchet tabs](2026-10-06-harmonograph-snowflake-truchet-tabs.md) | `user-interface`, `generators` |
| 2026-10-06 | `WSW-20261006-015` | implemented | [Artwork scale control on every generator tab](2026-10-06-artwork-scale-on-every-tab.md) | `user-interface`, `generators`, `scale` |
| 2026-10-06 | `WSW-20261006-014` | implemented | [Generator controls fill the settings column](2026-10-06-generator-controls-fill-column.md) | `user-interface`, `generators`, `layout` |
| 2026-10-06 | `WSW-20261006-013` | implemented | [Settings pane fills its column and removes the dead strip](2026-10-06-settings-pane-fills-column.md) | `user-interface`, `layout`, `preview` |
| 2026-10-06 | `WSW-20261006-012` | implemented | [Lift the tab bar above the import and save row](2026-10-06-tab-bar-above-import-row.md) | `user-interface`, `layout` |
| 2026-10-06 | `WSW-20261006-011` | implemented | [Make the settings pane content-width so the preview fills the rest](2026-10-06-content-width-settings-pane.md) | `user-interface`, `preview`, `layout` |
| 2026-10-06 | `WSW-20261006-010` | implemented | [Remove the G-code command list and let the preview fill the workspace](2026-10-06-remove-gcode-command-list.md) | `user-interface`, `preview` |
| 2026-10-06 | `WSW-20261006-009` | implemented | [Put the G-code output to the right of the preview](2026-10-06-gcode-output-right-of-preview.md) | `user-interface`, `preview`, `gcode` |
| 2026-10-06 | `WSW-20261006-008` | implemented | [Move Preview and Cancel into the preview panel](2026-10-06-preview-buttons-in-preview-panel.md) | `user-interface`, `preview` |
| 2026-10-06 | `WSW-20261006-007` | implemented | [Tab-driven preview in the shared preview panel](2026-10-06-tab-driven-shared-preview.md) | `user-interface`, `generators`, `preview` |
| 2026-10-06 | `WSW-20261006-006` | implemented | [Remove redundant per-tab image pickers](2026-10-06-remove-redundant-tab-imports.md) | `user-interface`, `generators`, `import` |
| 2026-10-06 | `WSW-20261006-005` | implemented | [Keep import, export, and preview static across generator tabs](2026-10-06-static-import-export-preview.md) | `user-interface`, `generators`, `preview` |
| 2026-10-06 | `WSW-20261006-004` | implemented | [3D Wireframe generator tab](2026-10-06-3d-wireframe-tab.md) | `user-interface`, `generators`, `3d` |
| 2026-10-06 | `WSW-20261006-003` | implemented | [Line Draw generator tab](2026-10-06-line-draw-tab.md) | `user-interface`, `generators`, `line-art` |
| 2026-10-06 | `WSW-20261006-002` | implemented | [Flow Field generator tab](2026-10-06-flow-field-tab.md) | `user-interface`, `generators`, `flow-field` |
| 2026-10-06 | `WSW-20261006-001` | implemented | [Generator tab shell in the main converter window](2026-10-06-generator-tab-shell.md) | `user-interface`, `generators`, `converter` |
| 2026-10-04 | `WSW-20261004-004` | implemented | [Terrain: stop stacking contours on hard outlines](2026/2026-10-04-terrain-outline-thinning.md) | `fill`, `shading`, `terrain`, `topographic`, `image-tone`, `plotter-art` |
| 2026-10-04 | `WSW-20261004-003` | implemented | [Terrain on image tone follows the photo's shading](2026/2026-10-04-terrain-follows-image-tone.md) | `fill`, `shading`, `terrain`, `topographic`, `image-tone`, `plotter-art` |
| 2026-10-04 | `WSW-20261004-002` | implemented | [Terrain fill: topographic contour shading](2026/2026-10-04-terrain-fill-pattern.md) | `fill`, `shading`, `terrain`, `topographic`, `image-tone`, `plotter-art` |
| 2026-10-04 | `WSW-20261004-001` | implemented | [Default the GP27 handshake and recover options on](2026/2026-10-04-default-gp27-handshake-and-recover.md) | `converter`, `gp27`, `p115`, `handshake`, `pen-dwell`, `defaults` |
| 2026-10-03 | `WSW-20261003-001` | implemented | [Stipple, halftone and single-line (TSP) photo shading](2026/2026-10-03-stipple-halftone-single-line-shading.md) | `fill`, `shading`, `stipple`, `halftone`, `tsp`, `image-tone`, `plotter-art` |
| 2026-10-02 | `WSW-20261002-001` | implemented | [Add an independent Maps tab to the kaleidoscope app](2026/2026-10-02-add-plotting-maps-tab.md) | `kaleidoscope`, `maps`, `openstreetmap`, `tab`, `webengine`, `vendored` |
| 2026-10-01 | `WSW-20261001-010` | implemented | [Theta: no bed sweep the machine cannot follow](2026/2026-10-01-theta-centre-sweep-and-travel-limits.md) | `theta`, `kinematics`, `drift`, `safety`, `calibration` |
| 2026-10-01 | `WSW-20261001-009` | implemented | [Auto fit measures the artwork before it fills it](2026/2026-10-01-auto-fit-measures-before-filling.md) | `fill`, `performance`, `fit`, `interface` |
| 2026-10-01 | `WSW-20261001-008` | implemented | [Photos import directly and plot as sine-wave tone](2026/2026-10-01-photo-raster-input.md) | `fill`, `tone`, `raster`, `photo`, `interface` |
| 2026-10-01 | `WSW-20261001-007` | implemented | [Image-tone fill spacing is millimetres on paper](2026/2026-10-01-image-tone-fill-spacing-units.md) | `fill`, `tone`, `performance`, `units` |
| 2026-10-01 | `WSW-20261001-006` | implemented | [Ornament spacing: the wallpaper density is a control, not a constant](2026/2026-10-01-ornament-spacing-control.md) | `kaleidoscope`, `generative`, `interface` |
| 2026-10-01 | `WSW-20261001-005` | implemented | [The kaleidoscope control column scrolls instead of running off the window](2026/2026-10-01-scrollable-kaleidoscope-sidebar.md) | `kaleidoscope`, `interface`, `usability` |
| 2026-10-01 | `WSW-20261001-004` | implemented | [Sine gradient: gradient tone plotted as continuous adjacent sinusoids](2026/2026-10-01-sine-gradient-fill.md) | `fill`, `gradient`, `tone`, `plotter-art` |
| 2026-10-01 | `WSW-20261001-003` | implemented | [Sparse ornaments: the bead, stud and dot rows stop carpeting the design](2026/2026-10-01-sparse-ornament-layers.md) | `kaleidoscope`, `generative`, `style` |
| 2026-10-01 | `WSW-20261001-002` | implemented | [Region overlay: neighbouring bands braid instead of tiling](2026/2026-10-01-region-overlay.md) | `kaleidoscope`, `generative`, `interface` |
| 2026-10-01 | `WSW-20261001-001` | implemented | [The centre wobble was the Tolerance budget, and it is now reported](2026/2026-10-01-tolerance-drives-inner-imprecision.md) | `kaleidoscope`, `tolerance`, `kinematics`, `diagnosis` |
| 2026-10-01 | `RPSW-20261001-001` | verified | [Lower the A-axis maximum rate to 20000 motor deg/min](../rp23cnc-software/2026/2026-10-01-a-axis-rate-limit-20000.md) | `grblhal`, `settings`, `theta`, `drift`, `safety` |
| 2026-09-30 | `WSW-20260930-023` | implemented | [Keep the commanded A small: re-register the bed each contour](2026/2026-09-30-theta-reregistration.md) | `theta`, `kinematics`, `drift`, `calibration` |
| 2026-09-30 | `WSW-20260930-022` | implemented | [Pen tip diameter for the installed Pigma Micron 005](2026/2026-09-30-pen-width-control.md) | `pen`, `interface`, `gcode` |
| 2026-09-30 | `WSW-20260930-021` | implemented | [Theta drift: record the ratio in the G-code and ship a calibration plot](2026/2026-09-30-theta-drift-diagnosis-and-calibration-plot.md) | `theta`, `kinematics`, `calibration`, `diagnostics` |
| 2026-09-30 | `WSW-20260930-020` | implemented | [Kaleidoscope: close the empty bands in motif patterns](2026/2026-09-30-kaleidoscope-fill-the-gaps.md) | `kaleidoscope`, `generative`, `style` |
| 2026-09-30 | `WSW-20260930-019` | implemented | [Engraving motifs: Haeckel plates cut into organisms](2026/2026-09-30-kaleidoscope-engraving-motifs.md) | `kaleidoscope`, `motifs`, `assets`, `generative` |
| 2026-09-30 | `WSW-20260930-018` | implemented | [Kaleidoscope: hatched, organic shapes in the drawn pattern generator](2026/2026-09-30-kaleidoscope-hatched-organic-shapes.md) | `kaleidoscope`, `generative`, `style` |
| 2026-09-30 | `WSW-20260930-017` | implemented | [Kaleidoscope: use a random set of ten motifs, not the whole folder](2026/2026-09-30-kaleidoscope-motif-selection-cap.md) | `kaleidoscope`, `motifs`, `interface` |
| 2026-09-30 | `WSW-20260930-016` | implemented | [Kaleidoscope: remembered setup and a default motif folder](2026/2026-09-30-kaleidoscope-remembered-setup.md) | `kaleidoscope`, `interface`, `motifs` |
| 2026-09-30 | `WSW-20260930-015` | implemented | [Kaleidoscope: auto-fit no longer overwrites typed numbers](2026/2026-09-30-kaleidoscope-non-destructive-autofit.md) | `kaleidoscope`, `interface`, `bounds` |
| 2026-09-30 | `WSW-20260930-014` | implemented | [Realistic nature motifs and deeper motif rings](2026/2026-09-30-realistic-nature-motifs.md) | `kaleidoscope`, `motifs`, `assets`, `generative` |
| 2026-09-30 | `WSW-20260930-013` | implemented | [Kaleidoscope: no cap on source size or typed bounds](2026/2026-09-30-kaleidoscope-uncapped-sizes.md) | `kaleidoscope`, `interface`, `bounds` |
| 2026-09-30 | `WSW-20260930-012` | implemented | [Kaleidoscope: zoom and pan the preview like the main converter](2026/2026-09-30-kaleidoscope-preview-zoom-pan.md) | `kaleidoscope`, `preview`, `interface` |
| 2026-09-30 | `WSW-20260930-011` | implemented | [Nature motif library for the kaleidoscope generator](2026/2026-09-30-nature-motif-library.md) | `kaleidoscope`, `motifs`, `assets`, `tooling` |
| 2026-09-30 | `WSW-20260930-010` | implemented | [Kaleidoscope: natural PNG motifs as the source of pattern diversity](2026/2026-09-30-kaleidoscope-natural-motifs.md) | `kaleidoscope`, `generative`, `motifs`, `raster` |
| 2026-09-30 | `WSW-20260930-009` | implemented | [Kaleidoscope: seeds choose a design, not just its phases](2026/2026-09-30-kaleidoscope-seed-diversity.md) | `kaleidoscope`, `generative`, `pattern-generator`, `seeds` |
| 2026-09-30 | `WSW-20260930-008` | implemented | [Kaleidoscope: complex multi-layer random patterns](2026/2026-09-30-kaleidoscope-complex-layers.md) | `kaleidoscope`, `generative`, `pattern-generator`, `density` |
| 2026-09-30 | `WSW-20260930-007` | implemented | [Kaleidoscope: engraving-density random patterns](2026/2026-09-30-kaleidoscope-engraving-density.md) | `kaleidoscope`, `generative`, `pattern-generator`, `density` |
| 2026-09-30 | `WSW-20260930-006` | implemented | [Kaleidoscope: deterministic random-pattern generator](2026/2026-09-30-kaleidoscope-random-pattern-generator.md) | `kaleidoscope`, `generative`, `pattern-generator`, `interface` |
| 2026-09-30 | `WSW-20260930-005` | implemented | [Kaleidoscope: typed printable bounds and a draggable image](2026/2026-09-30-kaleidoscope-typed-bounds-and-draggable-image.md) | `kaleidoscope`, `bounds`, `dragging`, `interface` |
| 2026-09-30 | `WSW-20260930-004` | implemented | [Add the Kaleidoscope Converter app](2026/2026-09-30-kaleidoscope-converter.md) | `kaleidoscope`, `raster`, `tracing`, `application`, `design` |
| 2026-09-30 | `WSW-20260930-003` | implemented | [Default to outlines only and fill only genuinely closed loops](2026/2026-09-30-outlines-only-default-and-closed-fill-regions.md) | `infill`, `correctness`, `defaults`, `fill-regions` |
| 2026-09-30 | `WSW-20260930-002` | implemented | [Keep pen-down bridging off by default and tag generated fill trails](2026/2026-09-30-tag-fill-trails-for-bridging.md) | `infill`, `bridge`, `pen-up`, `correctness`, `preview` |
| 2026-09-30 | `WSW-20260930-001` | implemented | [Calibrate the bed ratio from the measured A-index spacing](2026/2026-09-30-calibrated-bed-ratio.md) | `theta`, `kinematics`, `a-axis`, `calibration`, `registration`, `drift` |
| 2026-09-30 | `RPSW-20260930-004` | implemented | [Require a homed frame before the park macro moves](../rp23cnc-software/2026/2026-09-30-park-macro-requires-homed-frame.md) | `iosender`, `macro`, `p116`, `p111`, `park`, `g53`, `soft-limit`, `homing`, `safety`, `failed-approach` |
| 2026-09-30 | `RPSW-20260930-003` | implemented | [Add a manual pen-up-to-lift-home and park macro](../rp23cnc-software/2026/2026-09-30-manual-pen-up-and-park-macro.md) | `iosender`, `macro`, `p116`, `p115`, `lift-home`, `gp2`, `park`, `g53`, `service` |
| 2026-09-29 | `WSW-20260929-003` | implemented | [Re-derive the reach radius and give it a registration-drift margin](2026/2026-09-29-reach-radius-re-derived-with-drift-margin.md) | `converter`, `clipping`, `soft-limit`, `reachable-area`, `g54`, `alarm-2` |
| 2026-09-29 | `WSW-20260929-002` | implemented | [Auto-fit to the bed, and fill that follows the final scale](2026/2026-09-29-auto-fit-and-scale-aware-fill-cache.md) | `converter`, `usability`, `scale`, `reach`, `fill`, `cache` |
| 2026-09-29 | `WSW-20260929-001` | implemented | [Fill bed sizing and recentring for the fit actions](2026/2026-09-29-fill-bed-and-recenter-fits.md) | `converter`, `usability`, `scale`, `reach`, `placement` |
| 2026-09-29 | `RPSW-20260929-003` | implemented | [Define the level-1 system decomposition](../rp23cnc-software/2026/2026-09-29-level-1-system-decomposition.md) | `system-architecture`, `systems-integration`, `interfaces`, `documentation`, `project-management` |
| 2026-09-29 | `RPSW-20260929-002` | verified | [F-05A: the commissioned GP27/PRB pen-transition acknowledgement passed](../rp23cnc-software/2026/2026-09-29-f-05a-gp27-prb-handshake-verified.md) | `p115`, `gp27`, `prb`, `handshake`, `f-05a`, `commissioning` |
| 2026-09-28 | `WSW-20260928-002` | implemented | [Call out over-scale artwork and out-of-date previews](2026/2026-09-28-call-out-overscale-artwork-and-stale-previews.md) | `converter`, `usability`, `scale`, `reach`, `clipping`, `preview` |
| 2026-09-28 | `WSW-20260928-001` | implemented | [Automatic fill source and an intuitive settings layout](2026/2026-09-28-automatic-fill-and-settings-regroup.md) | `converter`, `usability`, `fill`, `hatch`, `line-art`, `settings-layout` |
| 2026-09-27 | `WSW-20260927-008` | implemented | [Restore the fixed-dwell default until F-05A passes](2026/2026-09-27-restore-dwell-default-until-f05a.md) | `converter`, `gp27`, `p115`, `error-39`, `f-05a`, `pen-dwell` |
| 2026-09-27 | `WSW-20260927-007` | implemented | [Drag the artwork on the bed to place it](2026/2026-09-27-drag-artwork-placement.md) | `converter`, `preview`, `placement`, `bed`, `drag`, `g54` |
| 2026-09-27 | `WSW-20260927-006` | implemented | [Show keep-down connectors in the preview](2026/2026-09-27-preview-keep-down-connectors.md) | `converter`, `preview`, `infill`, `serpentine`, `pen-cycle` |
| 2026-09-27 | `WSW-20260927-005` | implemented | [Chain line-family infill passes instead of lifting between them](2026/2026-09-27-chain-line-family-infill-passes.md) | `converter`, `infill`, `hatch`, `pen-cycle`, `serpentine`, `print-time` |
| 2026-09-27 | `WSW-20260927-004` | implemented | [Draw the gantry reach in the preview and report the artwork radius](2026/2026-09-27-preview-machine-reach-guide.md) | `converter`, `preview`, `gantry-reach`, `scaling`, `soft-limit`, `g54` |
| 2026-09-27 | `WSW-20260927-003` | implemented | [Apply the fill bleed margin by pulling back clipped passes](2026/2026-09-27-apply-fill-margin-by-pull-back.md) | `converter`, `fill`, `hatch`, `inset`, `clipping`, `correctness` |
| 2026-09-27 | `WSW-20260927-002` | implemented | [Accelerate fill generation with a polygon spatial index](2026/2026-09-27-speed-up-fill-region-with-spatial-index.md) | `converter`, `performance`, `fill`, `hatch`, `spatial-index`, `svg` |
| 2026-09-27 | `WSW-20260927-001` | implemented | [Resolve inherited SVG presentation attributes](2026/2026-09-27-resolve-inherited-svg-presentation-attributes.md) | `converter`, `svg`, `style-inheritance`, `shading`, `hatch`, `fill`, `line-art` |
| 2026-09-27 | `RPSW-20260927-002` | implemented | [Add a lift-and-continue recover mode to the P115 handshake](../rp23cnc-software/2026/2026-09-27-add-p115-recover-mode.md) | `p115`, `gp27`, `handshake`, `error-39`, `recover`, `f-05a` |
| 2026-09-27 | `RPSW-20260927-001` | implemented | [Parameterize the P115 handshake bounds and add a warn-only mode](../rp23cnc-software/2026/2026-09-27-parameterize-p115-bounds-and-warn-mode.md) | `p115`, `gp27`, `handshake`, `error-39`, `f-05a`, `warn-only` |
| 2026-09-26 | `WSW-20260926-002` | implemented | [Cap the drawable radius at the gantry's reach](2026/2026-09-26-cap-drawable-radius-to-gantry-reach.md) | `converter`, `clipping`, `soft-limit`, `reachable-area`, `bed` |
| 2026-09-26 | `WSW-20260926-001` | implemented | [Restore the generated pen-down path in the preview](2026/2026-09-26-restore-pen-down-preview-path.md) | `converter`, `preview`, `gcode`, `pen-down` |
| 2026-09-25 | `WSW-20260925-004` | implemented | [Add a single-centerline text SVG generator and Constitution preamble sample](2026/2026-09-25-add-single-line-text-svg-generator.md) | `converter`, `svg`, `hershey`, `single-line`, `text`, `sample` |
| 2026-09-25 | `WSW-20260925-003` | implemented | [Park the toolhead off the bed at program end](2026/2026-09-25-park-off-bed-at-program-end.md) | `converter`, `parking`, `g53`, `program-end` |
| 2026-09-25 | `WSW-20260925-002` | implemented | [Lower the pen-down dwell default to 2500 ms](2026/2026-09-25-lower-pen-down-dwell.md) | `converter`, `pen-dwell` |
| 2026-09-25 | `WSW-20260925-001` | implemented | [Default the GP27 handshake on](2026/2026-09-25-default-gp27-handshake.md) | `converter`, `gp27`, `handshake` |
| 2026-09-25 | `RPSW-20260925-009` | implemented | [Full retract the pen to GP2 at program end](../rp23cnc-software/2026/2026-09-25-full-retract-at-program-end.md) | `toolhead`, `full-retract`, `gp28`, `aux0`, `program-end`, `converter` |
| 2026-09-24 | `WSW-20260924-015` | implemented | [Show the artwork alone in the preview](2026/2026-09-24-clean-preview-artwork-only.md) | `converter`, `preview`, `polar` |
| 2026-09-24 | `WSW-20260924-014` | implemented | [Fill wide strokes instead of outlining thin ones](2026/2026-09-24-fill-wide-strokes-instead-of-outlining-thin.md) | `converter`, `stroke`, `fill`, `pen-width` |
| 2026-09-24 | `WSW-20260924-013` | implemented | [Give the program's first pen-down a cold-seek dwell](2026/2026-09-24-first-pen-down-cold-seek-dwell.md) | `converter`, `pen-dwell`, `cold-seek`, `gp2`, `first-plot` |
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
