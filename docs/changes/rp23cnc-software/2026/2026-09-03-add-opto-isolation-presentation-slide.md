---
id: RPSW-20260903-008
date: 2026-09-03
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
  - opto-isolation
  - wiring
  - p100
related:
  - RPSW-20260902-007
---

# Add Opto-Isolation Presentation Slide

## Summary

Added an at-a-glance slide explaining the three PC817C signal paths between
the RP23CNC and Pro Micro toolhead controller.

## Reason

The professor-facing presentation needed a concise explanation of why the
controller interface is isolated before introducing homing and P100 behavior.

## Implementation

- Inserted the slide after the high-level architecture slide.
- Showed U1, U2, and U3 with signal direction, GPIO endpoints, and controller
  versus toolhead voltage domains.
- Added the takeaway that only digital states cross the boundary; power,
  grounds, load-cell data, motor current, and UART remain local.
- Preserved the existing slide content and P100 navigation.

## Verification

- Rendered the new slide and inspected it at full size.
- Rendered all 13 slides; `slides_test.py` passed with no overflow.
- Confirmed the new slide has readable labels, correctly directed arrows, and
  the LIMA/PRB commissioning note.

## Risks and follow-up

The GP27 return remains installed at LIMA; PRB is still a candidate pending
F-08 verification. Run the deck in Slide Show mode before presenting.

## Files

- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`: added interface
  protection slide.
