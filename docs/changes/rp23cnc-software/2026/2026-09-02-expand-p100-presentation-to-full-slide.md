---
id: RPSW-20260902-005
date: 2026-09-02
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
  - windows-software
status: implemented
components:
  - docs/report
tags:
  - presentation
  - p100
  - interaction
  - layout
related:
  - RPSW-20260902-004
---

# Expand P100 Presentation to Full Slide

## Summary

Reformatted the P100 overview and its six interactive detail views as
full-slide dark process maps.

## Reason

The previous framing left a white presentation background and duplicate slide
chrome around information that was already complete within the P100 map.

## Implementation

- Removed the white slide chrome, footer, and outer summary panels from the
  P100 overview and all six detail views.
- Enlarged the map to the full slide height and extended its dark background
  across the entire widescreen slide.
- Retained the P100 detail panel inside the map and the card hover/click
  interaction; detail views retain only a compact **Back** control.

## Verification

- Rendered all 13 slides and inspected the full-slide overview plus Start and
  Per-run Touch Check detail views.
- `slides_test.py` passed with no overflow.
- Verified the six overview card destinations and the detail-view back action
  in PowerPoint.

## Struggles and rejected approaches

Stretching the source map to fill the slide width would noticeably distort its
text and process cards. The map therefore preserves its aspect ratio at full
slide height; the remaining space uses the matching dark background.

## Risks and follow-up

Run a short Slide Show test on the class presentation computer to verify its
mouse-over behavior and display scaling.

## Files

- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`: full-slide P100
  views.
