---
id: WSW-20260607-006
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
status: verified
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - playback
  - travel
  - simulation
related:
  - WSW-20260607-001
---

# Animated Pen-Up Travel

## Summary

Preview playback now visibly moves the lifted toolhead between contours instead
of making the pen-up transition appear to jump to its destination.

## Reason

The active travel overlay previously displayed the complete rapid segment as
soon as the command began. Travel was also paced at a fixed 100 mm/s rather
than the configured G0 rate. Together these made pen-up moves look sudden even
though the underlying point interpolation existed.

## Implementation

- Travel playback and estimated travel time now use the planned move duration
  generated from the configured travel rate.
- The active draw/travel overlay ends at the current interpolated tool point.
  It grows along the route as playback advances.
- The gray pen-up tool marker continues to identify travel separately from the
  configured draw color.

## Verification

- Confirmed a synthetic 100 mm travel interpolates to 50 mm at half progress.
- Confirmed the same move receives 2,000 ms playback duration at the default
  3,000 mm/min travel rate rather than the former fixed 1,000 ms.
- Built the sample SVG preview and checked all nonzero travel commands for
  positive duration and midpoint interpolation.
- Compiled the Qt application and converter modules.
- `git diff --check`
- `python tools\docs_index.py --check`

## Struggles and rejected approaches

The existing coordinate interpolation initially suggested travel was already
fully simulated. Inspection showed the full active segment was rendered ahead
of the marker, which visually concealed that interpolation. Enlarging only the
marker was rejected because it would not correct the premature path highlight
or fixed travel timing.

## Risks and follow-up

Long rapid moves now consume their planned duration in preview playback. This
is more faithful but can make jobs with large coordinated theta travel slower
to watch; the slider remains available for scrubbing.

## Files

- `software/qt_svg_to_gcode.pyw`: travel timing and active-segment rendering.
- `software/README.md`: user-facing playback behavior.
- `docs/HANDOFF.md`: preview timing and renderer reference.
