---
id: WSW-20260704-001
date: 2026-07-04
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - .gitignore
  - project_management_overview.html
  - README.md
  - docs/START_HERE.md
tags:
  - project-management
  - dashboard
  - documentation
  - navigation
related:
  - RPSW-20260704-003
  - HW-20260704-001
---

# Project Management Overview HTML

## Summary

Added a root-level HTML project management dashboard for quickly interpreting
current project status.

## Reason

The roadmap and engineering log are detailed source-of-truth documents, but the
project also needs a readable at-a-glance overview that can be opened directly
from the repository root.

## Implementation

Created `project_management_overview.html` with a dark-mode dashboard showing
the current phase, next phase, immediate work queue, phase-gate strip, open
blockers, recent homing/electronics clarifications, required evidence, subsystem
status, and links to controlling documents. Updated the root README and
`docs/START_HERE.md` so the dashboard is discoverable before deeper project
navigation. Added ignore rules for local Codex attachment and Obsidian
application metadata folders so repository cleanup does not stage workspace-only
artifacts.

## Verification

Documentation-only change. The dashboard uses local relative links and does not
replace the roadmap, test plan, wiring table, interface contract, engineering
log, or change index.

`python tools\docs_index.py --write` and `python tools\docs_index.py --check`
must pass before this session is complete.

## Struggles and rejected approaches

A Markdown project overview was rejected after the requested format was
clarified; the final artifact is HTML for easier visual scanning.

## Risks and follow-up

The dashboard is a summary and can become stale if the roadmap, tests, or
engineering log change without a corresponding overview update. Treat the linked
source documents as authoritative.

## Files

- `project_management_overview.html`: root-level at-a-glance dashboard.
- `.gitignore`: excludes local Codex attachment and Obsidian application
  metadata folders.
- `README.md`: links the dashboard from the repository entry point.
- `docs/START_HERE.md`: adds the dashboard to the recommended reading order.
