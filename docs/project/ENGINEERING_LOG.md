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

The topic-based register is maintained separately in
[`STRUGGLES_AND_REJECTED_APPROACHES.md`](STRUGGLES_AND_REJECTED_APPROACHES.md).
When a struggle is significant or likely to recur, record the dated event here
and update the corresponding topic there.

Use Central Time and include the UTC offset in every timestamp:

```text
YYYY-MM-DD HH:MM:SS -0500
```

Git commit timestamps are authoritative for repository events. Bench events
should use the time the work was performed or recorded and link to a lab note,
photo, measurement, test ID, or source document.

## Entry format

```markdown
### YYYY-MM-DD HH:MM:SS -0500 - Short title

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

### 2026-06-06 18:55:00 -0500 - Separated struggle register from chronology

- Category: documentation
- Summary: Moved the topic-based failure and rejected-approach index into `STRUGGLES_AND_REJECTED_APPROACHES.md`, alongside this chronological log.
- Reason: Chronology and recurrence prevention serve different lookup needs and should not be conflated.
- Struggle/failure: The first implementation embedded the topic index inside the chronological document.
- Evidence: Project-owner clarification.
- Files/commit: `docs/project/ENGINEERING_LOG.md`, `docs/project/STRUGGLES_AND_REJECTED_APPROACHES.md`; commit recorded after this entry.
- Result: Dated events remain here; consolidated technical lessons live in the adjacent register.
- Retry conditions: Merge them again only if a future reporting requirement demonstrably benefits from one document.
- Next action: Update both documents when a new recurring struggle is discovered.

### 2026-06-06 18:45:00 -0500 - Expanded log to preserve struggles and failures

- Category: documentation
- Summary: Made failures, blockers, rejected approaches, and recovery details mandatory parts of the engineering chronology.
- Reason: Future contributors and AI sessions must not repeatedly attempt approaches that already failed.
- Struggle/failure: The initial log emphasized successful commits and did not make difficult debugging history easy to search.
- Evidence: Existing debugging history in `docs/HANDOFF.md` and recent hardware-source conflicts.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Added failure-specific fields and a searchable index of known struggles.
- Retry conditions: Add or revise an indexed item whenever new evidence changes why an approach might work.
- Next action: Log future failed tests at the time they occur, including exact configuration and evidence.

### 2026-06-06 18:30:00 -0500 - Established rolling engineering chronology

- Category: documentation
- Summary: Created this engineering log and reconstructed the major project milestones from Git commit timestamps.
- Reason: The Systems Integration report and AI handoffs require a reliable dated account of software, hardware, wiring, test, and decision work.
- Struggle/failure: Earlier history was distributed across Git messages and a long handoff document rather than one chronology.
- Evidence: Repository Git history through commit `87cf328`.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Updating this log is now part of the mandatory session handoff procedure.
- Retry conditions: Not applicable.
- Next action: Use actual timestamps for future work and link detailed bench measurements to dated lab notes.

### 2026-06-06 18:16:52 -0500 - Selected adjustable toolhead buck converter

- Category: hardware, wiring
- Summary: Selected two purchased B085T73CSD adjustable buck modules for the toolhead's 6 V supply. Existing fixed 5 V modules became spares.
- Reason: The adjustable module can supply the actuator's rated 6 V and has more claimed current margin.
- Struggle/failure: The previous fixed 5 V module was below the motor's rated voltage and had marginal unverified current capacity.
- Evidence: Amazon listing supplied by the project owner; acceptance tests E-14 and E-15 remain open.
- Files/commit: `87cf328`; `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/testing/TEST_PLAN.md`.
- Result: Selected but not bench-verified. Output must be set with a multimeter before connecting the DRV8833.
- Retry conditions: Reconsider another regulator if E-15 shows unacceptable droop, ripple, or temperature.
- Next action: Inspect module terminals, set 6.0 V, and characterize it under actuator load.

### 2026-06-06 18:04:05 -0500 - Evaluated fixed 5 V buck module

- Category: hardware, wiring
- Summary: Added B0F1WB3LJ5 fixed 5 V buck modules as an actuator-supply candidate.
- Reason: The project owner already had these modules available.
- Struggle/failure: Listing current limits left insufficient confidence for actuator stall or seek loads, and fixed 5 V sacrifices motor performance.
- Evidence: Listing specified about 1.5 A continuous and 1.8 A maximum output.
- Files/commit: `164bcdc`.
- Result: Later superseded for the actuator by the adjustable B085T73CSD module; retained as a spare for lower-current 5 V loads.
- Retry conditions: Use for the actuator only if measured demand is comfortably below its tested continuous capacity and 5 V performance is acceptable.
- Next action: Use only where measured load and thermal margin are acceptable.

### 2026-06-06 17:38:43 -0500 - Documented received S-120-12 terminal layout

- Category: hardware, wiring, documentation
- Summary: Corrected the main supply model to MEISHILE S-120-12 and documented terminals 1-7: L, N, protective earth, -V, -V, +V, +V, plus the adjacent +V ADJ control.
- Reason: Physical unit inspection superseded inconsistent reseller model information.
- Struggle/failure: Reseller data named a different model, and the QR-linked PDF was a web-viewer capture with little extractable text.
- Evidence: Project-owner inspection and archived QR-linked PDF `docs/hardware/references/MEISHILE-S-120-12-manual.pdf`.
- Files/commit: `a15ce9d`.
- Result: Supply terminal functions are documented. Mains enclosure, fusing, earth continuity, and DC branch allocation remain unresolved.
- Retry conditions: Re-extract or OCR the PDF only if a specific unreadable manual detail is needed.
- Next action: Complete test E-11 before applying power.

### 2026-06-06 17:24:07 -0500 - Added reseller power-supply reference data

- Category: hardware, documentation
- Summary: Added internally consistent same-ASIN details from Ubuy.
- Reason: The secondary listing exposed more product fields than Amazon.
- Struggle/failure: The same page mixed contradictory 30 A / 360 W specifications from another product.
- Evidence: Ubuy page for ASIN B0781ZJ7GP.
- Files/commit: `be5a6a3`.
- Result: Recorded useful secondary data but rejected contradictory 30 A / 360 W text as listing contamination.
- Retry conditions: Accept conflicting data only if confirmed by the received unit or manufacturer documentation.
- Next action: Prefer physical markings and manufacturer documentation over reseller text.

### 2026-06-06 16:05:10 -0500 - Selected 12 V main power supply

- Category: hardware
- Summary: Added the MEISHILE 12 V, 10 A, 120 W supply to the BOM, wiring table, and electrical tests.
- Reason: Project owner identified the purchased main supply.
- Evidence: Amazon ASIN B0781ZJ7GP.
- Files/commit: `3a3ffab`.
- Result: Supply selected; ratings still require confirmation from the received unit and bench measurements.
- Next action: Verify output voltage, adjustment, protection, and thermal margin.

### 2026-06-06 15:55:07 -0500 - Created authoritative wiring table

- Category: wiring, documentation
- Summary: Added a status-driven master table covering power, motion, motor phases, safety, toolhead, and communications.
- Reason: The system needed a continuously updated physical connection record rather than relying on a conceptual diagram.
- Evidence: `docs/hardware/WIRING_TABLE.md`.
- Files/commit: `bf2f5f7`.
- Result: All uncertain terminals remain TBD and require evidence before status promotion.
- Next action: Update the table after every component inspection, pin assignment, or wiring test.

### 2026-06-06 15:46:05 -0500 - Organized hardware integration and expanded converter behavior

- Category: software, hardware, documentation
- Summary: Added the AI handoff structure, BOM, interfaces, roadmap, tests, architecture decisions, firmware placeholders, and report templates. Also committed accumulated converter fill-planning and preview changes.
- Reason: Prepare for RP23CNC integration, repeatable AI handoffs, and Systems Integration reporting.
- Evidence: Repository documents and Python syntax validation.
- Files/commit: `b0ecd9a`.
- Result: Project structure now mirrors host software, motion firmware, toolhead control, testing, and reporting responsibilities.
- Next action: Complete electrical characterization before powered integration.

### 2026-06-05 10:56:12 -0500 - Updated sparse-infill handoff notes

- Category: software, documentation
- Summary: Consolidated the implemented sparse-infill behavior and known constraints in the handoff.
- Struggle/failure: Pattern generation required repeated fixes for clipping, compound regions, and preserving distinct lattice geometry.
- Files/commit: `a3b1459`.
- Result: Converter state became reproducible for the next development session.
- Retry conditions: Revisit algorithms when a repeatable SVG regression case demonstrates incorrect geometry.

### 2026-06-05 09:23:07 -0500 through 10:50:32 -0500 - Developed sparse fill patterns

- Category: software
- Summary: Added selectable fill patterns, expanded pattern options, clipped generated geometry to boundaries and compound regions, introduced shared lattices, and preserved pattern identity.
- Reason: Support reportable, distinct fill strategies while keeping generated pen paths inside artwork regions.
- Struggle/failure: Early pattern implementations crossed boundaries, disappeared at edges, or collapsed different patterns into similar geometry.
- Evidence: Commits `03b8a1b`, `feb05b7`, `132241c`, `f476730`, `60f8d6d`, `cf4154c`, `34e7275`, `0ed21ee`, and `302ac5c`.
- Result: Converter supports multiple clipped sparse-infill strategies.
- Retry conditions: Replace the current clipping/generation approach only with regression coverage for compound and boundary cases.
- Next action: Validate generated patterns on physical hardware after motion bring-up.

### 2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - Added preview navigation

- Category: software
- Summary: Added preview zoom controls followed by mouse zoom and pan interactions.
- Evidence: Commits `56a78ef` and `c3bb3ee`.
- Result: Artwork and motion previews are easier to inspect.

### 2026-06-05 09:04:15 -0500 - Chose RP23CNC and grblHAL

- Category: decision, firmware
- Summary: Recorded RP23CNC with grblHAL as the motion-control architecture.
- Reason: Reuse proven G-code parsing, coordinated planning, acceleration, homing, limits, and step generation.
- Evidence: Commit `690617b`; ADR-001 was added later.
- Result: Custom firmware is limited to configuration and toolhead integration unless a demonstrated requirement requires more.
- Next action: Identify the exact board revision and reproduce a known grblHAL build.

### 2026-06-05 08:28:30 -0500 - Established project repository

- Category: software, documentation
- Summary: Committed the initial SVG-to-G-code converter project, firmware/report folders, samples, and handoff documentation.
- Evidence: Commit `f3e2162`.
- Result: Created the baseline for subsequent software and integration work.
