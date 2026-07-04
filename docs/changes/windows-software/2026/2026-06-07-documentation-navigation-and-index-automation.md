---
id: WSW-20260607-003
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: verified
components:
  - docs/README.md
  - tools/docs_index.py
  - AGENTS.md
tags:
  - documentation
  - navigation
  - automation
  - maintainability
related:
  - WSW-20260607-002
---

# Documentation Navigation and Index Automation

## Summary

The documentation system now provides task-oriented navigation, explicit
sources of truth, tiered recording rules, and automatically generated
subsystem change indexes.

## Reason

The categorized structure was useful but still had three scaling problems:
new contributors were directed first to a 483-line technical reference,
minor changes could require duplicate narratives, and every change note
required several manually synchronized index edits.

## Implementation

- Added `docs/README.md` as a task-to-document map and source-of-truth matrix.
- Changed onboarding to read only documents relevant to the current task.
- Reclassified `HANDOFF.md` as a searchable deep technical reference.
- Defined separate roles for current-state docs, change notes, the engineering
  log, roadmap, ADRs, lab notes, and Git history.
- Added tiered documentation rules so meaningful changes remain documented
  without duplicating trivial formatting or mechanical edits.
- Added `tools/docs_index.py` to generate category indexes from front matter and
  validate metadata, duplicate IDs, stale generated content, and local links.
- Added objective growth triggers for splitting the technical reference,
  archiving the engineering log, and introducing deeper date folders.

## Verification

- `python -m py_compile tools\docs_index.py software\qt_svg_to_gcode.pyw`
- `python tools\docs_index.py --write`
- `python tools\docs_index.py --check`
- `git diff --check`
- Result: four indexes generated from three notes; metadata and local links
  validated.

## Struggles and rejected approaches

- Splitting or rewriting the entire technical handoff was rejected because it
  would create high churn and risk losing useful historical rationale.
- Requiring a change note and engineering-log entry for every typo or
  mechanical cleanup was rejected because it would cause the documentation
  system itself to become the source of clunkiness.

## Risks and follow-up

- `HANDOFF.md` and `ENGINEERING_LOG.md` remain large by design. Their role is
  now explicit, and both should be searched rather than read sequentially.
- The index parser intentionally supports the project's simple front-matter
  subset, not general YAML.
- If the engineering log becomes difficult to search, archive completed years
  without breaking chronological ordering. The working agreement now sets an
  approximate 1,000-line trigger.

## Files

- `docs/README.md`: task-oriented map and document ownership.
- `tools/docs_index.py`: generated indexes and validation.
- `AGENTS.md`: tiered documentation policy and required checks.
- `docs/START_HERE.md`: shorter onboarding path.
- `docs/HANDOFF.md`: clarified reference role.
- `docs/changes/`: generated-index markers and workflow.
