---
id: WSW-20260607-004
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: verified
components:
  - docs/project/ENGINEERING_LOG.md
  - tools/docs_index.py
tags:
  - engineering-log
  - topic-index
  - navigation
  - single-source
related:
  - WSW-20260607-003
---

# Single-File Engineering Topic Index

## Summary

The engineering log remains one chronological Markdown file but now includes
generated high-level topic views that link to the original entries.

## Reason

Chronological history preserves the sequence from failures to resolutions, but
it becomes slow to browse by subsystem as the log grows. Copying entry bodies
into topic sections or separate files would create competing versions of the
same record.

## Implementation

- Added generated topic groups for Windows software, RP23CNC and machine
  software, hardware and wiring, testing, decisions, and project organization.
- Added explicit stable HTML anchors before every chronological entry.
- Topic lists contain only entry titles and links to those anchors.
- Extended `tools/docs_index.py` to rebuild and validate the topic index.
- Added validation that every engineering-log entry belongs to at least one
  recognized topic.

## Verification

- `python -m py_compile tools\docs_index.py`
- `python tools\docs_index.py --write`
- `python tools\docs_index.py --check`
- `git diff --check`
- Result: all existing entries received unique anchors and appeared in their
  applicable topic views without duplicating entry bodies.

## Struggles and rejected approaches

- Date-only historical entries initially produced duplicate anchors because
  three entries were recorded as `Before 2026-06-05`. Their anchors now include
  a short title slug.
- Separate topic files containing copied entry text were rejected because they
  would drift from the chronological source.

## Risks and follow-up

- Link titles necessarily repeat the entry heading, but the entry narrative and
  evidence exist only once.
- Topic membership depends on the `Category` field. New category names must be
  added to the generator's topic map before validation will pass.

## Files

- `docs/project/ENGINEERING_LOG.md`: generated topic index and entry anchors.
- `tools/docs_index.py`: topic mapping, generation, and validation.
- `docs/README.md`: description of the single-source topic views.
