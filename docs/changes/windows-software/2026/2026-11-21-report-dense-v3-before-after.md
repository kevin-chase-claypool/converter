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

# Show the first and latest bed-compensation results

## Summary

Figure 5 now compares the later 91-station dense-v3 calibration field before
and after compensation instead of showing a single earlier calibration
photograph. Figure 6 now shows the first post-repair baseline and compensated
result together with the latest dense-v3 baseline and compensated result. The
report states that the denser measurement represented a more complete spatial
model than the earlier sheets.

The Figure 5 caption records the measured dense-v3 comparison: overall RMS fell
from `0.550` to `0.486 mm` (`11.6%`), while maximum error remained essentially
unchanged at `1.171 mm`. The Figure 6 chart shows both measurement epochs and
states that the latest residual is `72.1%` lower in RMS and `60.5%` lower in
maximum error than the first post-repair baseline. It also preserves the
qualification boundary because the latest candidate missed the formal promotion
gates and was selected by owner override.

The report explains that mesh density has diminishing returns after the dominant
repeatable field has been removed. The latest independent result did not reach
the `0.274 mm` leave-one-station-out prediction, so the remaining error includes
variation that a static spatial map cannot reliably cancel.

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
