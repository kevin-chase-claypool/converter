---
id: RPSW-20260902-004
date: 2026-09-02
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
  - windows-software
status: implemented
components:
  - docs/report
  - docs/p100-data-movement.html
tags:
  - presentation
  - p100
  - interaction
  - correction
related:
  - RPSW-20260902-003
  - HW-20260902-001
---

# Align P100 Presentation Detail States

## Summary

Corrected the interactive P100 detail slides so the information inside the map
matches the process card selected by the hover/click action.

## Reason

The first interactive presentation revision highlighted the selected process
but retained the static map image's Step 1 detail pane. This made the in-map
detail inconsistent with the process selected on the left.

## Implementation

- Replaced the frozen in-map Step 1 detail pane on each of the six detail views
  with the corresponding P100 process detail.
- Removed the duplicate right-side detail panel from the six detail views.
- Kept the right side only for concise navigation guidance and the existing
  **Back to overview** control.

## Verification

- Rendered the final 13-slide deck and visually checked representative Start,
  Toolhead Home, and Per-run Touch Check views.
- `slides_test.py` passed with no overflow.
- Verified all six overview mouse-click/mouse-over destinations and the back
  control in PowerPoint.

## Struggles and rejected approaches

The HTML map's native interactive detail pane cannot execute inside PowerPoint.
The PowerPoint detail states therefore mirror the same data as slide-native
overlays rather than embedding the webpage runtime.

## Risks and follow-up

Before presenting, briefly run Slide Show and hover/click any two process cards
to confirm the machine used for class honors PowerPoint mouse-over actions.

## Files

- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`: corrected
  interactive detail views.
