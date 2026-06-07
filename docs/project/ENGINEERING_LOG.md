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

### 🟨 2026-06-06 16:05:10 -0500 - MIXED/OPEN - Selected 12 V main power supply

- Status: mixed/open
- Category: hardware
- Summary: Added the MEISHILE 12 V, 10 A, 120 W supply to the BOM, wiring table, and electrical tests.
- Reason: Project owner identified the purchased main supply.
- Evidence: Amazon ASIN B0781ZJ7GP.
- Files/commit: `3a3ffab`.
- Result: Supply selected; ratings still require confirmation from the received unit and bench measurements.
- Next action: Verify output voltage, adjustment, protection, and thermal margin.

### 🟩 2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table

- Status: success
- Category: wiring, documentation
- Summary: Added a status-driven master table covering power, motion, motor phases, safety, toolhead, and communications.
- Reason: The system needed a continuously updated physical connection record rather than relying on a conceptual diagram.
- Evidence: `docs/hardware/WIRING_TABLE.md`.
- Files/commit: `bf2f5f7`.
- Result: All uncertain terminals remain TBD and require evidence before status promotion.
- Next action: Update the table after every component inspection, pin assignment, or wiring test.

### 🟩 2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior

- Status: success
- Category: software, hardware, documentation
- Summary: Added the AI handoff structure, BOM, interfaces, roadmap, tests, architecture decisions, firmware placeholders, and report templates. Also committed accumulated converter fill-planning and preview changes.
- Reason: Prepare for RP23CNC integration, repeatable AI handoffs, and Systems Integration reporting.
- Evidence: Repository documents and Python syntax validation.
- Files/commit: `b0ecd9a`.
- Result: Project structure now mirrors host software, motion firmware, toolhead control, testing, and reporting responsibilities.
- Next action: Complete electrical characterization before powered integration.

### 🟩 2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes

- Status: success
- Category: software, documentation
- Summary: Consolidated the implemented sparse-infill behavior and known constraints in the handoff.
- Struggle/failure: Pattern generation required repeated fixes for clipping, compound regions, and preserving distinct lattice geometry.
- Files/commit: `a3b1459`.
- Result: Converter state became reproducible for the next development session.
- Retry conditions: Revisit algorithms when a repeatable SVG regression case demonstrates incorrect geometry.

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

### 🟩 2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - SUCCESS - Added preview navigation

- Status: success
- Category: software
- Summary: Added preview zoom controls followed by mouse zoom and pan interactions.
- Evidence: Commits `56a78ef` and `c3bb3ee`.
- Result: Artwork and motion previews are easier to inspect.

### 🟩 2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL

- Status: success
- Category: decision, firmware
- Summary: Recorded RP23CNC with grblHAL as the motion-control architecture.
- Reason: Reuse proven G-code parsing, coordinated planning, acceleration, homing, limits, and step generation.
- Evidence: Commit `690617b`; ADR-001 was added later.
- Result: Custom firmware is limited to configuration and toolhead integration unless a demonstrated requirement requires more.
- Next action: Identify the exact board revision and reproduce a known grblHAL build.

### 🟩 2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository

- Status: success
- Category: software, documentation
- Summary: Committed the initial SVG-to-G-code converter project, firmware/report folders, samples, and handoff documentation.
- Evidence: Commit `f3e2162`.
- Result: Created the baseline for subsequent software and integration work.

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
