---
id: WSW-20261001-001
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - tolerance
  - kinematics
  - diagnosis
related:
  - WSW-20260930-023
  - software/README.md
---

# The centre wobble was the Tolerance budget, and it is now reported

## Summary

The operator's plot of `kaleidoscope1.gcode` was generally good but the centre
and the inner wave band were imprecise - "the same place as the biggest issues
before". The cause is not drift or registration: it is the `Tolerance` setting
the file was made with (**1.0 mm**, not the 0.25 mm default). Tolerance is the
budget for how far the commanded path may sit from the intended line on the
bed, and it binds hardest where the bed rotates most per millimetre of travel:
the tight curves near the centre and the inner sweep of the wave band.

The exact design was reproduced from the saved session (seed 83382, intricacy
10, 4 divisions, no motifs) and measured at several tolerances; the emitter now
also reports the worst deviation it produced, so a saved program says how
accurate it is.

## Reason

"look at the zoomed in image and notice how the outer waves are not precise
... in the center to the 4 inch radius the pen doesnt appear to print as
exactly as it does elsewhere. search for the reason this could be occuring in
software."

## Evidence

Reconstructing the commanded path from the G-code and comparing it with the
intended straight bed lines, binned by radius, gave, at tolerance 1.0 mm:

| radius | worst deviation | moves over 0.3 mm |
| --- | --- | --- |
| 0-25 mm | **0.899 mm** | 10 |
| 25-50 mm | 0.087 mm | 0 |
| 50-75 mm | 0.186 mm | 0 |
| 75-100 mm (4 in) | **0.677 mm** | 12 |
| 100-190 mm | 0.059 mm | 0 |

That is precisely the two regions the operator described. Re-emitting the same
design at tighter tolerances shows the deviation tracks the setting, and that
it costs almost nothing:

| tolerance | worst deviation | G1 moves |
| --- | --- | --- |
| 1.00 mm | 0.899 mm | 212,296 |
| 0.25 mm | 0.245 mm | 212,350 |
| 0.10 mm | 0.100 mm | 212,528 |
| 0.05 mm | 0.050 mm | 212,864 |

## Implementation

- `converter_core/gcode.py`: `contours_to_gcode()` takes an optional `stats`
  dict and records `worst_bed_deviation_mm`, its radius and the strategy of the
  worst move, using the deviation the subdivider already computes. No extra
  kinematics work is done.
- `qt_kaleidoscope.pyw`: saving a program now logs the tolerance, the worst
  commanded deviation, where it is and which strategy produced it, with the
  hint to lower `Tolerance` if it matters.
- `software/tests/test_theta_wrap.py`: a test asserts the stats are produced,
  that a coarse tolerance leaves a larger deviation than a tight one, and that
  a 0.1 mm tolerance keeps the worst deviation within 0.1 mm.

## Risks and follow-up

- The report is produced when a program is saved (the emitter walks the whole
  plan), not on every interactive rebuild, because emitting is the expensive
  step.
- Lowering `Tolerance` also tightens the raster/SVG simplification, which is
  usually wanted but does add points on detailed sources.
- The operator's saved settings still hold `tolerance: 1.0`; the value needs
  changing in the app (or in `software\kaleidoscope_settings.json`) before the
  next plot is re-saved.

## Files

- `software/converter_core/gcode.py`, `software/qt_kaleidoscope.pyw`,
  `software/tests/test_theta_wrap.py`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`.
