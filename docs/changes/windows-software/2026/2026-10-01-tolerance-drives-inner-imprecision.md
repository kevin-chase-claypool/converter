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

## Follow-up 2026-10-02: the old files measured, and the numbers are large

The setting was changed: the operator now runs `Tolerance = 0.15`. Measuring the
programs that produced the bad prints, with
`tools/check_gcode_motion.py` (which reports the worst commanded bed-path bow,
its radius and its strategy from the file alone):

| Program | Worst commanded bow | Share of a 2 mm row pitch |
|---|---|---|
| `mom.gcode` | **1.908 mm** at 18 mm radius (`fallback`) | **95 %** |
| `kaleidoscope1.gcode` | **1.599 mm** at 165 mm radius (`x_theta`) | **80 %** |
| `mandala1.gcode` | **1.232 mm** at 100 mm radius (`x_theta`) | **62 %** |
| `washington.gcode` | 0.310 mm at 14 mm radius | 16 % |
| `ben.gcode` (re-saved) | 0.020 mm at 1 mm radius | 1 % |

So the rows in those prints were *commanded* to wander between 62 % and 95 % of
the way into their neighbours wherever the bed rotated most per millimetre. That
is the reported "waveforms are supposed to be evenly spaced, but they're tending
to overlap", and it is a converter setting rather than a machine fault: no lost
step, no slip and no belt winding produces that shape.

On a kaleidoscope-style mandala the bow tracks the tolerance almost exactly -
0.690 mm at `Tolerance 1.0`, 0.345 at 0.5, 0.230 at 0.25, **0.148 at 0.15**,
0.100 at 0.1 - and tightening it is nearly free: 18,479 emitted moves at 1.0
versus 18,506 at 0.1, a 0.15 % increase, because only the few moves that bow are
split. `mom.gcode` also shows the strategy that produces the worst cases:
`fallback`, the near-centre singularity path that the bed-step guard now parks
instead of sweeping.

The three failure modes are now separable and each has its own number:

- **rows drifting or converging gradually** - the commanded bow, bounded by
  `Tolerance`; old files 62-95 % of a row pitch, now 7 % at 0.15;
- **a fan or tangle at the bed centre** - the huge sweeps the planner used to
  command there (46.6 deg inside one move at r < 9 mm), now parked;
- **a whole-pattern shift or rotation** - lost steps from the impossible A rate
  (1333 motor deg/s demanded), now capped at 15000 motor deg/min and verified by
  the circle test.

## Files

- `software/converter_core/gcode.py`, `software/qt_kaleidoscope.pyw`,
  `software/tests/test_theta_wrap.py`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`.
