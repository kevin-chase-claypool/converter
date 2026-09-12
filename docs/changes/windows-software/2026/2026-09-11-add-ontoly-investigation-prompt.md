---
id: WSW-20260911-001
date: 2026-09-11
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - ONTOLY_PROMPT.md
  - README.md
  - docs/README.md
tags:
  - ontoly
  - architecture
  - impact-analysis
  - agent-workflow
related:
  - WSW-20260828-001
---

# Add Ontoly investigation prompt

## Summary

Added a reusable repository-specific prompt for evidence-based architecture,
dependency, impact, and cross-subsystem investigations.

## Reason

The project spans host software, motion-control firmware, toolhead firmware,
and safety-relevant hardware. A generic code graph can accelerate scoped code
inspection but cannot establish wiring, commissioning, or runtime behavior.

## Implementation

The root prompt directs an investigator to use the local Ontoly graph first,
then to consult the authoritative subsystem documents. It records the graph's
current topology limits, makes the system contracts explicit, and requires
evidence, ownership, risk, and a minimal next step in each report.

The documentation-index checker now excludes `node_modules`, so third-party
package README links cannot invalidate repository-documentation checks.

## Verification

- Queried the local Ontoly CLI: the graph contains 512 nodes and 540 edges.
- Confirmed its current relationships are static code-topology relationships
  (`CONTAINS`, `DECORATES`, `EXTENDS`, and `IMPORTS`), not runtime or hardware
  evidence.
- Ran `python tools\docs_index.py --write` and
  `python tools\docs_index.py --check`.

## Struggles and rejected approaches

`pnpm ontoly` could not run because this repository has no `package.json`.
The prompt therefore uses the existing local CLI directly and does not assume
that a package-manager install or graph rebuild is authorized.

## Risks and follow-up

The graph must be rebuilt after material source changes, but only after the
person running the investigation approves generating graph artifacts. Its
coverage and relationship types should be rechecked at that time.

## Files

- `ONTOLY_PROMPT.md`: reusable investigation prompt and graph caveats.
- `README.md`: root-level discovery link.
- `docs/README.md`: task-to-authority routing entry.
- `tools/docs_index.py`: skip third-party package documentation during link checks.
