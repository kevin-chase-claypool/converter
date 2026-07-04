# Engineering Log

This is the rolling chronological record of project work. It answers: what
changed, when it changed, why it changed, what evidence exists, and what should
happen next.

This log must include unsuccessful work as well as successful work. Record:

- Failed experiments and approaches that were abandoned.
- Bugs that were difficult to diagnose.
- Incorrect assumptions and misleading source data.
- Tooling failures, blockers, and workarounds.
- Rejected components or architectures.
- Conditions that would justify retrying a rejected approach.

Do not rewrite a failed attempt as if the successful result was reached
directly. The struggle, evidence, and recovery are part of the engineering
record and are useful report material.

## Visual status

VS Code Markdown Preview renders these markers consistently:

- 🟩 **SUCCESS** - completed implementation or verified result.
- 🟥 **STRUGGLE** - failed attempt, bug, blocker, or rejected approach.
- 🟨 **MIXED/OPEN** - useful progress with unresolved risk or required testing.

Every event belongs in this one chronology. A struggle and its later resolution
should normally be separate entries at their actual times. If the exact time of
an older struggle is unknown, use `Time not recorded` and place it before the
first event known to have occurred afterward. Never invent a timestamp.

Use Central Time and include the UTC offset in every timestamp:

```text
YYYY-MM-DD HH:MM:SS -0500
```

Git commit timestamps are authoritative for repository events. Bench events
should use the time the work was performed or recorded and link to a lab note,
photo, measurement, test ID, or source document.

## Browse by topic

<!-- BEGIN GENERATED TOPIC INDEX -->
The links below are alternate views of the single chronological log.
Entry details remain only in the chronology.

### Windows software
- [2026-06-07 14:02:21 -0500 - SUCCESS - Animated pen-up preview travel](#elog-20260607140221)
- [2026-06-07 13:16:27 -0500 - SUCCESS - Added cooperative preview cancellation](#elog-20260607131627)
- [2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress](#elog-20260607115128)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)
- [2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes](#elog-20260605105612)
- [2026-06-05 09:23:07 -0500 through 10:50:32 -0500 - MIXED/OPEN - Developed sparse fill patterns](#elog-20260605092307)
- [2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - SUCCESS - Added preview navigation](#elog-20260605090940)
- [2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository](#elog-20260605082830)
- [Before 2026-06-05 - Time not recorded - STRUGGLE - OpenGL preview type and binding bugs](#elog-20260605-opengl-preview-type-and-binding-bugs)
- [Before 2026-06-05 - Time not recorded - STRUGGLE - Theta DP winding reference failed](#elog-20260605-theta-dp-winding-reference-failed)
- [Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff](#elog-20260605-hold-steady-theta-grid-tradeoff)

### RP23CNC and machine software
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference](#elog-20260606185401)
- [2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL](#elog-20260605090415)

### Hardware and wiring
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf](#elog-20260615095711)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:16:52 -0500 - MIXED/OPEN - Selected adjustable toolhead buck converter](#elog-20260606181652)
- [2026-06-06 18:04:05 -0500 - STRUGGLE - Fixed 5 V buck was marginal](#elog-20260606180405)
- [2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout](#elog-20260606173843)
- [2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated](#elog-20260606172407)
- [2026-06-06 16:05:10 -0500 - MIXED/OPEN - Selected 12 V main power supply](#elog-20260606160510)
- [2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table](#elog-20260606155507)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)

### Testing and verification
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)

### Decisions and architecture
- [2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement](#elog-20260607115739)
- [2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL](#elog-20260605090415)
- [Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff](#elog-20260605-hold-steady-theta-grid-tradeoff)

### Documentation and project organization
- [2026-07-04 17:41:19 -0500 - SUCCESS - Added project management overview HTML](#elog-20260704174119)
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf](#elog-20260615095711)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-07 12:21:44 -0500 - SUCCESS - Added single-file engineering-log topic navigation](#elog-20260607122144)
- [2026-06-07 12:02:21 -0500 - SUCCESS - Reduced documentation navigation and indexing friction](#elog-20260607120221)
- [2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement](#elog-20260607115739)
- [2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress](#elog-20260607115128)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:58:24 -0500 - SUCCESS - Added roadmap completion checkboxes](#elog-20260606185824)
- [2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference](#elog-20260606185401)
- [2026-06-06 18:45:28 -0500 - STRUGGLE - Misinterpreted requested log structure](#elog-20260606184528)
- [2026-06-06 18:41:06 -0500 - STRUGGLE - Separated struggles from chronology](#elog-20260606184106)
- [2026-06-06 18:37:31 -0500 - SUCCESS - Required failure details in log](#elog-20260606183731)
- [2026-06-06 18:34:25 -0500 - SUCCESS - Established rolling engineering chronology](#elog-20260606183425)
- [2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout](#elog-20260606173843)
- [2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated](#elog-20260606172407)
- [2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table](#elog-20260606155507)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)
- [2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes](#elog-20260605105612)
- [2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository](#elog-20260605082830)
<!-- END GENERATED TOPIC INDEX -->

## Entry format

```markdown
### 🟩 YYYY-MM-DD HH:MM:SS -0500 - SUCCESS - Short title

- Status: success | struggle | mixed/open
- Category: software | firmware | hardware | wiring | test | decision | documentation
- Summary:
- Reason:
- Struggle/failure:
- Evidence:
- Files/commit:
- Result:
- Retry conditions:
- Next action:
```

Add new entries at the top of the log below this line.

---

<a id="elog-20260704174119"></a>
### 🟩 2026-07-04 17:41:19 -0500 - SUCCESS - Added project management overview HTML

- Status: success
- Category: documentation, project-management
- Summary: Added a root-level HTML dashboard for at-a-glance project status, current phase, next work, blockers, subsystem status, and links to controlling documents.
- Reason: The roadmap and engineering log are detailed, but the repository needed a quick visual project management overview accessible directly from the root folder.
- Struggle/failure: A Markdown overview was rejected after the requested format was clarified; the final artifact is HTML for faster visual scanning.
- Evidence: Change note `WSW-20260704-001`; `project_management_overview.html`.
- Files/commit: `project_management_overview.html`, `README.md`, `docs/START_HERE.md`, `docs/changes/windows-software/2026/2026-07-04-project-management-overview-html.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The project now has a root dashboard while keeping the roadmap, test plan, wiring table, interface contract, engineering log, and change index as authoritative sources.
- Next action: Update the dashboard whenever phase status, immediate priorities, or major blockers change.

<a id="elog-20260704123000"></a>
### 🟨 2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML

- Status: mixed/open
- Category: hardware, wiring, firmware, documentation
- Summary: Added a standalone dark-mode HTML planning diagram for the current electronics layout and wiring concept, covering RP23CNC Ethernet control, 12 V distribution, X/Y/A TB6600 drivers, toolhead electronics, and the TMAG5273/RP2040 magnetic calibration adapter.
- Reason: The wiring table is authoritative but dense; the project needed a visual overview that shows the current architecture while preserving all TBD gates.
- Struggle/failure: None.
- Evidence: Change note `HW-20260704-001`; `docs/electronics_layout_and_wiring.html`.
- Files/commit: `docs/electronics_layout_and_wiring.html`, `docs/hardware/WIRING_TABLE.md`, `docs/changes/hardware/2026/2026-07-04-electronics-layout-wiring-html.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: A browser-viewable electronics layout exists with a nighttime-friendly palette, and the wiring table explicitly states that the HTML is explanatory only.
- Retry conditions: Update the diagram when terminal labels, fusing, E-stop architecture, RP23CNC input behavior, or toolhead controller placement become verified.
- Next action: Visually inspect the HTML and keep using `docs/hardware/WIRING_TABLE.md` as the source of truth for actual wiring.

<a id="elog-20260704120000"></a>
### 🟨 2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration

- Status: mixed/open
- Category: firmware, hardware, wiring, test, documentation
- Summary: Added a planned homing and magnetic bed-calibration architecture using physical X/Y limit switches, RP23CNC/grblHAL motion, a TMAG5273 Qwiic Hall sensor, an RP2040 adapter, a center magnet, and an outer theta-index magnet.
- Reason: The XY theta plotter needs repeatable X/Y homing, geometric bed-center calibration, and A/theta index detection without making grblHAL parse raw I2C sensor data.
- Struggle/failure: A direct TMAG5273 grblHAL plugin was rejected for first bring-up because it adds custom real-time firmware before proving that the host-coordinated RP2040 adapter approach is insufficient. Treating the center magnet as a theta reference was also rejected because it cannot define angular phase.
- Evidence: Change note `RPSW-20260704-001`; `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`.
- Files/commit: `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`, `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/UPCOMING_CODING_STEPS.md`, `docs/integration/INTERFACES.md`, `docs/hardware/WIRING_TABLE.md`, `docs/testing/TEST_PLAN.md`, `docs/changes/rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Homing and calibration responsibilities are documented: grblHAL owns motion and digital home/limit handling; the RP2040/TMAG5273 path supplies magnetic readings and, after verification, may provide a conditioned `A_HOME` signal.
- Retry conditions: Consider custom grblHAL code only after host-coordinated scans prove a concrete limitation.
- Next action: Verify TMAG5273 readings, RP2040 telemetry, RP23CNC input requirements, and scan repeatability before recording thresholds or wiring status.

<a id="elog-20260615095711"></a>
### 🟨 2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf

- Status: mixed/open
- Category: hardware, documentation
- Summary: Added parametric STEP assemblies for the Tecmojo `14130201` 1U sliding shelf at its published 350 mm and 500 mm rack-post depths.
- Reason: Electronics placement and cable-clearance planning need a usable 3D shelf envelope before plotter integration is finalized.
- Struggle/failure: The Amazon catalog dimensions `20.9 x 3.35 x 1.73 in` do not describe the installed shelf, and an older manual listed only 350-400 mm adjustment. The current manufacturer manual and specification sheet resolved SKU `14130201` to 482.6 mm width, 350-500 mm adjustment, and 44 mm height. Tecmojo did not provide production CAD for the product, leaving sheet, slide, vent, hole, and stop details to be inferred from images.
- Evidence: Amazon ASIN `B0BMW9V6MS`; current Tecmojo manual and specification sheet; valid 13-solid STEP re-imports; body envelopes `482.6 x 350 x 44.45 mm` and `482.6 x 500 x 44.45 mm`; rendered previews; change note `HW-20260615-001`.
- Files/commit: `tools/cad/generate_tecmojo_14130201.py`, `docs/hardware/cad/`, `docs/hardware/BOM.md`, `docs/changes/hardware/2026/2026-06-15-tecmojo-sliding-shelf-reference-cad.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Minimum- and maximum-depth layout models are available for electronics packaging work, with published interfaces separated from inferred geometry.
- Retry conditions: Replace image-derived constants after measuring the received shelf or if Tecmojo publishes production CAD for SKU `14130201`.
- Next action: Confirm the received SKU/revision and record physical dimensions before drilling a mounting plate or depending on vent and fastener locations.

<a id="elog-20260609130334"></a>
### 🟨 2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up

- Status: mixed/open
- Category: firmware, hardware, documentation
- Summary: Reviewed the RP23CNC user manual and assembly instructions and converted them into a staged RP23U5XBB/Wiz850io firmware and Ethernet bring-up plan.
- Reason: The controller and Ethernet kit have been received, so the next work must distinguish physical assembly gates from reproducible firmware configuration and network verification.
- Struggle/failure: The reported `RP23U5BB` name differed from the official `RP23U5XBB` name. Front-board photography later resolved the identity as `RP23U5XBB V1.01`. Overview photographs cannot replace magnified joint inspection or continuity tests. A custom source build was deferred because the Web Builder is the documented baseline path.
- Evidence: Official RP23CNC user manual versions 1.0/1.01; official RP23U5XBB assembly instructions; supplied module photograph showing a Wiznet W5500 and two six-pin rows; lab notes `docs/report/lab-notes/2026-06-09-rp23cnc-w5500-module-inspection.md` and `docs/report/lab-notes/2026-06-09-rp23u5xbb-v1.01-board-inspection.md`; change note `RPSW-20260609-001`.
- Files/commit: `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/UPCOMING_CODING_STEPS.md`, `docs/changes/`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The received board is identified as RP23U5XBB V1.01, visible assembly evidence is archived, and upcoming work specifies remaining solder/continuity gates, four-axis/W5500 build options, USB recovery, DHCP/Telnet proof, settings capture, and the threshold for custom plugin code.
- Retry conditions: Revise the plan if the received PCB revision, module marking, current Web Builder, or boot output differs from the reviewed manual.
- Next action: Photograph the board revision and kit contents, complete E-16/E-17, then generate and archive the first UF2.

<a id="elog-20260607140221"></a>
### 🟩 2026-06-07 14:02:21 -0500 - SUCCESS - Animated pen-up preview travel

- Status: success
- Category: software, testing
- Summary: Made pen-up travel visibly interpolate from the lift point to its destination and paced it with the configured travel command duration.
- Reason: The full travel overlay appeared immediately and fixed 100 mm/s pacing made rapid moves look like endpoint jumps during playback.
- Struggle/failure: Coordinate interpolation already existed, so the initial assumption that travel positions were not interpolated was incomplete; the premature full-segment overlay was the main visual defect.
- Evidence: Change note `WSW-20260607-006`; synthetic midpoint/timing test; sample-preview travel checks; Python compilation; `git diff --check`; documentation index validation.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/README.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The gray pen-up marker and active route now advance continuously across each travel command.
- Retry conditions: Revisit travel pacing after measured RP23CNC coordinated X/Y/A rapid behavior is available.
- Next action: Verify perceived playback speed against the assembled machine once axis rates are calibrated.

<a id="elog-20260607131627"></a>
### 🟩 2026-06-07 13:16:27 -0500 - SUCCESS - Added cooperative preview cancellation

- Status: success
- Category: software
- Summary: Added a Cancel button and cooperative cancellation checkpoints throughout preview geometry and motion generation.
- Reason: Accidental high-density settings or very large contour files could leave preview generation running for an unreasonable time with no safe way to stop it.
- Struggle/failure: Forced thread termination was rejected because it could corrupt Qt, OpenGL, Python, or geometry-cache state. Stage-boundary-only cancellation was insufficient for nested fill loops.
- Evidence: Change note `WSW-20260607-005`; core cancellation tests for gyroid generation and a 5,000-point plan; offscreen Qt lifecycle test retained the previous 527-command preview and restored controls; Python compilation; `git diff --check`.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/converter_core/cancellation.py`, `geometry.py`, `kinematics.py`, `gcode.py`, `software/README.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Preview creation can be safely stopped without force-closing the program or losing the last successful preview.
- Retry conditions: Add more checkpoints if a measured operation remains unresponsive to cancellation for an unacceptable interval.
- Next action: Consider applying the same worker/cancellation pattern to Save G-code if large synchronous conversions become disruptive.

<a id="elog-20260607122144"></a>
### 🟩 2026-06-07 12:21:44 -0500 - SUCCESS - Added single-file engineering-log topic navigation

- Status: success
- Category: documentation, project management
- Summary: Added generated high-level topic views and stable anchors to the existing chronological engineering log without copying entry bodies.
- Reason: The chronological log will become difficult to browse by subsystem, but splitting or duplicating entries would weaken the single source of truth.
- Struggle/failure: Historical entries recorded only as `Before 2026-06-05` initially generated duplicate date-based anchors; title slugs were added for date-only entries.
- Evidence: Change note `WSW-20260607-004`; `python tools\docs_index.py --write`; `python tools\docs_index.py --check`; Python compilation; `git diff --check`.
- Files/commit: `docs/project/ENGINEERING_LOG.md`, `tools/docs_index.py`, `docs/README.md`, `AGENTS.md`, `docs/changes/`; commit not yet created.
- Result: One Markdown file now supports chronological reading and topic-based lookup while storing each full event exactly once.
- Retry conditions: Introduce separate archive files only after the documented engineering-log scaling threshold is reached.
- Next action: Categorize future events accurately and regenerate the indexes after edits.

<a id="elog-20260607120221"></a>
### 🟩 2026-06-07 12:02:21 -0500 - SUCCESS - Reduced documentation navigation and indexing friction

- Status: success
- Category: documentation, project management
- Summary: Added task-oriented documentation navigation, clarified document ownership, reduced duplicate recording requirements, and automated categorized change indexes and link validation.
- Reason: The initial organization was searchable but would become clunky because onboarding began with a 483-line reference and each note required manual edits to several indexes.
- Struggle/failure: Treating every incidental edit as both a change note and engineering-log event would make the record noisier than the project. Rewriting the full technical handoff would risk losing valuable rationale.
- Evidence: Change note `WSW-20260607-003`; `python tools\docs_index.py --check`; Python compilation; `git diff --check`.
- Files/commit: `docs/README.md`, `tools/docs_index.py`, `AGENTS.md`, `docs/START_HERE.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Contributors can navigate by task, meaningful history remains preserved, and category indexes cannot silently drift from note metadata.
- Retry conditions: Split large historical files only when search and task-oriented navigation no longer provide adequate access.
- Next action: Use generated indexes and keep detailed information in one authoritative location with links elsewhere.

<a id="elog-20260607115739"></a>
### 🟩 2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement

- Status: success
- Category: documentation, decision
- Summary: Added explicit instructions requiring focused cleanup, technical-debt tracking, proportional verification, and evidence-based optimization during future work.
- Reason: Long-running projects become difficult to modify when maintainability depends on conversational memory or occasional cleanup requests.
- Struggle/failure: The expectation had been stated in conversation but was not yet encoded in repository instructions, so a new thread could miss it.
- Evidence: `AGENTS.md` maintainability section, `docs/START_HERE.md`, and change note `WSW-20260607-002`.
- Files/commit: `AGENTS.md`, `docs/START_HERE.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Future threads opened in this repository receive the maintainability policy automatically.
- Retry conditions: Revise the policy when a recurring maintenance problem demonstrates that the current rules are insufficient.
- Next action: Apply the policy during each implementation and add concrete larger cleanup work to the roadmap when discovered.

<a id="elog-20260607115128"></a>
### 🟩 2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress

- Status: success
- Category: software, documentation
- Summary: Added responsive preview generation with stage, percentage, and elapsed-time feedback, then established indexed Windows-software, RP23CNC-software, and hardware change streams with mandatory repository instructions.
- Reason: Preview generation provided no indication of active work, and subsystem changes were difficult to find inside the long chronological handoff and engineering log.
- Struggle/failure: The first progress widget reused the existing numeric `preview_progress` playback field; integration testing caught the collision. A background geometry path also contained a direct Qt log write and was corrected to avoid cross-thread widget access.
- Evidence: `python -m py_compile software\qt_svg_to_gcode.pyw`; `git diff --check`; offscreen PySide6 preview test generated 527 commands and restored controls; `docs/changes/windows-software/2026/2026-06-07-preview-build-progress.md`.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/changes/`, `docs/START_HERE.md`, `docs/HANDOFF.md`, `docs/project/ROADMAP.md`; commit not yet created.
- Result: Preview work is visible and non-blocking, and future changes now require a categorized note plus the chronological audit entry without waiting for an owner reminder.
- Retry conditions: Replace stage-based percentages only if core geometry/planner APIs provide reliable item-level callbacks.
- Next action: Use the new category indexes for all subsequent converter, RP23CNC, firmware, hardware, and wiring changes.

<a id="elog-20260606210916"></a>
### 🟨 2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit

- Status: mixed/open
- Category: hardware, firmware, documentation
- Summary: Identified the purchased controller as Brookwood Design RP23CNC variant `48493912129751`, With Assembly and Ethernet Kits.
- Reason: Generic RP23CNC assumptions needed to be tied to the exact purchased configuration.
- Struggle/failure: The product title can sound assembled, but the listing explicitly requires the customer to solder connectors and Ethernet components.
- Evidence: https://brookwood-design-77.myshopify.com/products/ro?variant=48493912129751 and https://www.grbl.org/rp23u5xbb
- Files/commit: BOM, wiring table, test plan, roadmap, and `firmware/grblhal/README.md`; commit recorded after this entry.
- Result: Kit inventory, soldering, visual inspection, continuity, and power-rail checks are now required before board power or firmware bring-up.
- Retry conditions: Mark assembly tasks complete only after E-16 and E-17 evidence exists.
- Next action: Record the received PCB revision and photograph all kit contents before soldering.

<a id="elog-20260606185824"></a>
### 🟩 2026-06-06 18:58:24 -0500 - SUCCESS - Added roadmap completion checkboxes

- Status: success
- Category: documentation, project management
- Summary: Converted every roadmap phase and task into Markdown checklists and separated previously combined phases.
- Reason: Completion state needed to be visible at both phase and task level in VS Code Markdown Preview.
- Struggle/failure: The earlier roadmap used prose bullets and a status table, so individual task completion could not be marked.
- Evidence: `docs/project/ROADMAP.md`.
- Files/commit: `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Phase 0 is checked; all unverified hardware, firmware, motion, toolhead, integration, and report tasks remain unchecked.
- Retry conditions: Check tasks only when evidence exists; do not use partial completion as completed.
- Next action: Begin Phase 1 and update boxes as electrical tests pass.

<a id="elog-20260606185401"></a>
### 🟩 2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference

- Status: success
- Category: documentation, firmware
- Summary: Added `phil-barrett/RP23CNC` as the canonical board reference in onboarding, architecture, firmware, and controller-configuration documentation.
- Reason: Board schematics, revisions, pin assignments, and RP23CNC-specific guidance must remain traceable to the upstream hardware repository.
- Struggle/failure: The link previously appeared only in the BOM source list and was easy to miss during controller work.
- Evidence: https://github.com/phil-barrett/RP23CNC
- Files/commit: `docs/START_HERE.md`, `docs/architecture/SYSTEM_ARCHITECTURE.md`, `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/config/README.md`; commit recorded after this entry.
- Result: Controller-facing documents now point directly to the authoritative upstream repository.
- Retry conditions: Replace the link only if the upstream project relocates.
- Next action: Record the exact received RP23CNC board revision and archive the matching schematic before pin assignment.

<a id="elog-20260606184528"></a>
### 🟥 2026-06-06 18:45:28 -0500 - STRUGGLE - Misinterpreted requested log structure

- Status: struggle
- Category: documentation
- Summary: Split struggles into a separate topic-based document even though the requested design was one chronological record containing both struggles and successes.
- Reason: The phrase "alongside the chronology" was interpreted as a separate file instead of interleaved chronological entries.
- Struggle/failure: This reduced the ability to see the sequence from failure to resolution.
- Evidence: Project-owner correction after commit `1ef58cb`.
- Files/commit: `1ef58cb`; corrected by the commit following this entry.
- Result: Separate register removed and all records returned to this chronology.
- Retry conditions: Create a separate failure register only after explicit approval.
- Next action: Use colored status markers while preserving strict chronological order.

<a id="elog-20260606184106"></a>
### 🟥 2026-06-06 18:41:06 -0500 - STRUGGLE - Separated struggles from chronology

- Status: struggle
- Category: documentation
- Summary: Moved the topic-based failure index into a separate document.
- Reason: Attempted to optimize lookup by topic.
- Struggle/failure: The change contradicted the intended single chronological narrative.
- Evidence: Commit `1ef58cb` and subsequent project-owner correction.
- Files/commit: `1ef58cb`.
- Result: Rejected and reversed.
- Retry conditions: Do not retry without explicit approval.
- Next action: Keep struggles interleaved with successes by occurrence time.

<a id="elog-20260606183731"></a>
### 🟩 2026-06-06 18:37:31 -0500 - SUCCESS - Required failure details in log

- Status: success
- Category: documentation
- Summary: Made failures, blockers, rejected approaches, and recovery details mandatory parts of the engineering chronology.
- Reason: Future contributors and AI sessions must not repeatedly attempt approaches that already failed.
- Struggle/failure: The initial log emphasized successful commits and did not make difficult debugging history easy to search.
- Evidence: Existing debugging history in `docs/HANDOFF.md` and recent hardware-source conflicts.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Added failure-specific fields and a searchable index of known struggles.
- Retry conditions: Add or revise an indexed item whenever new evidence changes why an approach might work.
- Next action: Log future failed tests at the time they occur, including exact configuration and evidence.

<a id="elog-20260606183425"></a>
### 🟩 2026-06-06 18:34:25 -0500 - SUCCESS - Established rolling engineering chronology

- Status: success
- Category: documentation
- Summary: Created this engineering log and reconstructed the major project milestones from Git commit timestamps.
- Reason: The Systems Integration report and AI handoffs require a reliable dated account of software, hardware, wiring, test, and decision work.
- Struggle/failure: Earlier history was distributed across Git messages and a long handoff document rather than one chronology.
- Evidence: Repository Git history through commit `87cf328`.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Updating this log is now part of the mandatory session handoff procedure.
- Retry conditions: Not applicable.
- Next action: Use actual timestamps for future work and link detailed bench measurements to dated lab notes.

<a id="elog-20260606181652"></a>
### 🟨 2026-06-06 18:16:52 -0500 - MIXED/OPEN - Selected adjustable toolhead buck converter

- Status: mixed/open
- Category: hardware, wiring
- Summary: Selected two purchased B085T73CSD adjustable buck modules for the toolhead's 6 V supply. Existing fixed 5 V modules became spares.
- Reason: The adjustable module can supply the actuator's rated 6 V and has more claimed current margin.
- Struggle/failure: The previous fixed 5 V module was below the motor's rated voltage and had marginal unverified current capacity.
- Evidence: Amazon listing supplied by the project owner; acceptance tests E-14 and E-15 remain open.
- Files/commit: `87cf328`; `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/testing/TEST_PLAN.md`.
- Result: Selected but not bench-verified. Output must be set with a multimeter before connecting the DRV8833.
- Retry conditions: Reconsider another regulator if E-15 shows unacceptable droop, ripple, or temperature.
- Next action: Inspect module terminals, set 6.0 V, and characterize it under actuator load.

<a id="elog-20260606180405"></a>
### 🟥 2026-06-06 18:04:05 -0500 - STRUGGLE - Fixed 5 V buck was marginal

- Status: struggle
- Category: hardware, wiring
- Summary: Added B0F1WB3LJ5 fixed 5 V buck modules as an actuator-supply candidate.
- Reason: The project owner already had these modules available.
- Struggle/failure: Listing current limits left insufficient confidence for actuator stall or seek loads, and fixed 5 V sacrifices motor performance.
- Evidence: Listing specified about 1.5 A continuous and 1.8 A maximum output.
- Files/commit: `164bcdc`.
- Result: Later superseded for the actuator by the adjustable B085T73CSD module; retained as a spare for lower-current 5 V loads.
- Retry conditions: Use for the actuator only if measured demand is comfortably below its tested continuous capacity and 5 V performance is acceptable.
- Next action: Use only where measured load and thermal margin are acceptable.

<a id="elog-20260606173843"></a>
### 🟨 2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Corrected the main supply model to MEISHILE S-120-12 and documented terminals 1-7: L, N, protective earth, -V, -V, +V, +V, plus the adjacent +V ADJ control.
- Reason: Physical unit inspection superseded inconsistent reseller model information.
- Struggle/failure: Reseller data named a different model, and the QR-linked PDF was a web-viewer capture with little extractable text.
- Evidence: Project-owner inspection and archived QR-linked PDF `docs/hardware/references/MEISHILE-S-120-12-manual.pdf`.
- Files/commit: `a15ce9d`.
- Result: Supply terminal functions are documented. Mains enclosure, fusing, earth continuity, and DC branch allocation remain unresolved.
- Retry conditions: Re-extract or OCR the PDF only if a specific unreadable manual detail is needed.
- Next action: Complete test E-11 before applying power.

<a id="elog-20260606172407"></a>
### 🟥 2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated

- Status: struggle
- Category: hardware, documentation
- Summary: Added internally consistent same-ASIN details from Ubuy.
- Reason: The secondary listing exposed more product fields than Amazon.
- Struggle/failure: The same page mixed contradictory 30 A / 360 W specifications from another product.
- Evidence: Ubuy page for ASIN B0781ZJ7GP.
- Files/commit: `be5a6a3`.
- Result: Recorded useful secondary data but rejected contradictory 30 A / 360 W text as listing contamination.
- Retry conditions: Accept conflicting data only if confirmed by the received unit or manufacturer documentation.
- Next action: Prefer physical markings and manufacturer documentation over reseller text.

<a id="elog-20260606160510"></a>
### 🟨 2026-06-06 16:05:10 -0500 - MIXED/OPEN - Selected 12 V main power supply

- Status: mixed/open
- Category: hardware
- Summary: Added the MEISHILE 12 V, 10 A, 120 W supply to the BOM, wiring table, and electrical tests.
- Reason: Project owner identified the purchased main supply.
- Evidence: Amazon ASIN B0781ZJ7GP.
- Files/commit: `3a3ffab`.
- Result: Supply selected; ratings still require confirmation from the received unit and bench measurements.
- Next action: Verify output voltage, adjustment, protection, and thermal margin.

<a id="elog-20260606155507"></a>
### 🟩 2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table

- Status: success
- Category: wiring, documentation
- Summary: Added a status-driven master table covering power, motion, motor phases, safety, toolhead, and communications.
- Reason: The system needed a continuously updated physical connection record rather than relying on a conceptual diagram.
- Evidence: `docs/hardware/WIRING_TABLE.md`.
- Files/commit: `bf2f5f7`.
- Result: All uncertain terminals remain TBD and require evidence before status promotion.
- Next action: Update the table after every component inspection, pin assignment, or wiring test.

<a id="elog-20260606154605"></a>
### 🟩 2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior

- Status: success
- Category: software, hardware, documentation
- Summary: Added the AI handoff structure, BOM, interfaces, roadmap, tests, architecture decisions, firmware placeholders, and report templates. Also committed accumulated converter fill-planning and preview changes.
- Reason: Prepare for RP23CNC integration, repeatable AI handoffs, and Systems Integration reporting.
- Evidence: Repository documents and Python syntax validation.
- Files/commit: `b0ecd9a`.
- Result: Project structure now mirrors host software, motion firmware, toolhead control, testing, and reporting responsibilities.
- Next action: Complete electrical characterization before powered integration.

<a id="elog-20260605105612"></a>
### 🟩 2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes

- Status: success
- Category: software, documentation
- Summary: Consolidated the implemented sparse-infill behavior and known constraints in the handoff.
- Struggle/failure: Pattern generation required repeated fixes for clipping, compound regions, and preserving distinct lattice geometry.
- Files/commit: `a3b1459`.
- Result: Converter state became reproducible for the next development session.
- Retry conditions: Revisit algorithms when a repeatable SVG regression case demonstrates incorrect geometry.

<a id="elog-20260605092307"></a>
### 🟨 2026-06-05 09:23:07 -0500 through 10:50:32 -0500 - MIXED/OPEN - Developed sparse fill patterns

- Status: mixed/open
- Category: software
- Summary: Added selectable fill patterns, expanded pattern options, clipped generated geometry to boundaries and compound regions, introduced shared lattices, and preserved pattern identity.
- Reason: Support reportable, distinct fill strategies while keeping generated pen paths inside artwork regions.
- Struggle/failure: Early pattern implementations crossed boundaries, disappeared at edges, or collapsed different patterns into similar geometry.
- Evidence: Commits `03b8a1b`, `feb05b7`, `132241c`, `f476730`, `60f8d6d`, `cf4154c`, `34e7275`, `0ed21ee`, and `302ac5c`.
- Result: Converter supports multiple clipped sparse-infill strategies.
- Retry conditions: Replace the current clipping/generation approach only with regression coverage for compound and boundary cases.
- Next action: Validate generated patterns on physical hardware after motion bring-up.

<a id="elog-20260605090940"></a>
### 🟩 2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - SUCCESS - Added preview navigation

- Status: success
- Category: software
- Summary: Added preview zoom controls followed by mouse zoom and pan interactions.
- Evidence: Commits `56a78ef` and `c3bb3ee`.
- Result: Artwork and motion previews are easier to inspect.

<a id="elog-20260605090415"></a>
### 🟩 2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL

- Status: success
- Category: decision, firmware
- Summary: Recorded RP23CNC with grblHAL as the motion-control architecture.
- Reason: Reuse proven G-code parsing, coordinated planning, acceleration, homing, limits, and step generation.
- Evidence: Commit `690617b`; ADR-001 was added later.
- Result: Custom firmware is limited to configuration and toolhead integration unless a demonstrated requirement requires more.
- Next action: Identify the exact board revision and reproduce a known grblHAL build.

<a id="elog-20260605082830"></a>
### 🟩 2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository

- Status: success
- Category: software, documentation
- Summary: Committed the initial SVG-to-G-code converter project, firmware/report folders, samples, and handoff documentation.
- Evidence: Commit `f3e2162`.
- Result: Created the baseline for subsequent software and integration work.

<a id="elog-20260605-opengl-preview-type-and-binding-bugs"></a>
### 🟥 Before 2026-06-05 - Time not recorded - STRUGGLE - OpenGL preview type and binding bugs

- Status: struggle
- Category: software
- Summary: Preview development encountered repeated paint exceptions, incorrect bed rotation, a theta uniform stuck at zero, and brittle VBO attribute binding.
- Reason: PySide6/OpenGL type and overload behavior differed from assumptions in the original implementation.
- Struggle/failure: `QVector4D` was unpacked as a tuple; bed theta sign was reversed; generic scalar `setUniformValue` selected an integer overload; raw `glVertexAttribPointer` was unreliable.
- Evidence: Resolved debugging history in `docs/HANDOFF.md`.
- Files/commit: Exact originating commits were not preserved in the current Git history.
- Result: Return a tuple, use positive bed theta, call `setUniformValue1f`, and use `setAttributeBuffer`.
- Retry conditions: Do not restore the failed forms without focused regression tests.
- Next action: Preserve future debugging events at the time they occur.

<a id="elog-20260605-theta-dp-winding-reference-failed"></a>
### 🟥 Before 2026-06-05 - Time not recorded - STRUGGLE - Theta DP winding reference failed

- Status: struggle
- Category: software
- Summary: A tangent-following winding reference excluded valid low-winding theta solutions.
- Reason: The reference itself accumulated winding, moving desirable candidates outside the search window.
- Struggle/failure: Candidate winding was encoded relative to a moving, winding reference.
- Evidence: Kinematics gotchas in `docs/HANDOFF.md`.
- Files/commit: Exact originating commit not recorded.
- Result: Use principal angles and nearest-wrap edge costs so winding emerges from the selected path.
- Retry conditions: Do not retry tangent-reference anchoring.
- Next action: Add a hard net-winding constraint later if cable management requires it.

<a id="elog-20260605-hold-steady-theta-grid-tradeoff"></a>
### 🟨 Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff

- Status: mixed/open
- Category: software, decision
- Summary: A 45-degree orientation grid made planning and execution much faster but left the bed stationary for roughly 94% of segments.
- Reason: Uniform hold-steady candidates dominated the motion cost.
- Struggle/failure: The faster result conflicted with the project goal that theta visibly participates in curve generation.
- Evidence: Measurements recorded in `docs/HANDOFF.md`.
- Files/commit: Exact experiment commit not recorded.
- Result: Grid disabled by default.
- Retry conditions: Enable only when throughput is explicitly prioritized over visible theta participation.
- Next action: Keep the tradeoff available as a documented non-default option.
