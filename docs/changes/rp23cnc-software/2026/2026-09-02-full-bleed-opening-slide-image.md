---
id: RPSW-20260902-007
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
  - title-slide
  - toolhead
related:
  - RPSW-20260902-006
---

# Full-Bleed Opening Slide Image

## Summary

Updated the presentation opening slide to use the supplied full-machine render
as a full-bleed background.

## Reason

The wider machine view gives the professor immediate context for the complete
plotter while retaining a readable title and project summary.

## Implementation

- Filled the entire 16:9 title slide with the supplied machine image.
- Applied a dark translucent reading panel on the left side.
- Restyled the existing title, subtitle, caption, and date text for contrast.
- Preserved all other slides and the native P100 hover/click navigation.

## Verification

- Rendered and visually inspected the revised opening slide.
- `slides_test.py` passed with no overflow across all 13 slides.
- Existing P100 navigation remains in the deck and was not modified.

## Risks and follow-up

Run the deck in Slide Show mode on the classroom computer to confirm display
scaling and mouse-over behavior.

## Files

- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`: revised opening
  slide.
