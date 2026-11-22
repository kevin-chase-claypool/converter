---
id: WSW-20261121-002
date: 2026-11-21
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: verified
components:
  - docs/report/System_Integration_Robotics_Paper.docx
  - docs/report/System_Integration_Robotics_Paper.md
  - docs/report/build_system_integration_paper.py
tags:
  - report
  - bed-calibration
  - bed-compensation
  - dense-mesh
  - before-after
---

# Show the later dense-v3 bed-compensation comparison

## Summary

Figure 5 now compares the later 91-station dense-v3 calibration field before
and after compensation instead of showing a single earlier calibration
photograph. The report states that the denser measurement represented a more
complete spatial model than the earlier sheets.

The caption records the measured comparison: overall RMS fell from `0.550` to
`0.486 mm` (`11.6%`), while maximum error remained essentially unchanged at
`1.171 mm`. It also preserves the qualification boundary because this candidate
missed the formal promotion gates and was selected by owner override.

## Implementation

The report builder now creates a two-panel PRE/POST image from the retained
centered dense-v3 overlays. The existing DOCX was updated directly so the
Word-only text edits were preserved rather than regenerating the report from
Markdown.

## Verification

- Confirmed the pre/post pair and comparison metrics from the 2026-10-29 M-12
  dense-v3 lab notes and comparison JSON.
- Rendered the updated DOCX and inspected the affected pages.
- Ran the document accessibility audit.
- Ran the repository documentation index write and check commands.

## Risks and follow-up

The dense-v3 compensated verification reduced RMS by only `11.6%` and slightly
increased maximum error. The figure must not be presented as a fully passed
promotion result.
