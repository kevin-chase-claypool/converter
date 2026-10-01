---
id: WSW-20261001-010
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/kinematics.py
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
tags:
  - theta
  - kinematics
  - drift
  - safety
  - calibration
related:
  - WSW-20260930-021
  - WSW-20260930-015
  - software/README.md
---

# Theta: no bed sweep the machine cannot follow

## Summary

Three linked fixes to what the converter asks of the A axis:

1. **Park the bed at the centre singularity.** When a segment's axis-lock
   solution would rotate the bed more than `MAX_BED_STEP_DEG` (15 deg), or when
   no axis-lock root exists at all (the bed-centre case), the planner now offers
   a parked-bed candidate that traces the move with the gantry in X and Y and
   lets the usual cost choose.
2. **A realistic assumed A rate.** `ThetaControllerLimits.max_rate_deg_min`
   drops from 80,000 to 20,000 motor deg/min. 80,000 was the controller's
   configured `$113`, i.e. 1333 motor deg/s = 111 bed deg/s through a 12:1
   reducer, which the bed cannot follow. 20,000 is 27.7 bed deg/s: the same
   surface speed as the 700 mm/min tangential limit expressed at a 25 mm radius.
3. **Pen-up moves that rotate the bed are fed, not rapid.** A `theta_wrap`
   re-registration unwinds a *whole bed revolution* between two contours, and
   that was emitted as a bare `G0 ... A<theta>` - the controller ran it at its
   configured A rapid rate. It is now `G1 ... F<limited> (travel)` with the feed
   the A axis can hold; pure X/Y travel stays a rapid.

## Reason

"the waveforms are supposed to be evenly spaced, but they're tending to overlap
... it might have something to do with the theta", then "the bed rotated around
180 degrees as it approached the center of the bed, it was printing one of the
sine waves and the straight path of the sine wave bent as the bed turned", and
the photograph of the finished plot with its rows fanned around the bed centre.

Measured on the file that was on the machine (`samples/gcode/ben.gcode`,
321,587 cuts reconstructed into bed coordinates):

- rows are exactly 2.000 mm apart and never cross *as commanded* - the file is
  geometrically even, so the damage is done by the machine following commands it
  cannot execute;
- 64 drawing moves rotate the bed more than 60 motor deg each, up to **561
  motor deg (46.6 bed deg) in a single move**, all at radii of 0.35-9.1 mm;
- the largest A rate demanded is **1333 motor deg/s (111 bed deg/s)**, which is
  the 80,000 motor deg/min cap being hit;
- one travel move commands a **full 4332 motor deg revolution as a `G0` rapid**,
  which is `theta_wrap` re-registering the bed.

Sweeps too fast to follow leave the bed lagging, which bends the stroke being
drawn and rotates every contour after it - the fan around the centre in the
photo, and the "waveforms drifting into adjacent waveforms" before it.

## Implementation

- `converter_core/kinematics.py`
  - `MAX_BED_STEP_DEG = 15.0` and `_held_segment_plan()`: the parked-bed
    candidate, offered when the axis-lock sweep exceeds the step limit or when
    no axis-lock root exists, and then compared by the existing cost.
  - `plan_travel_move()`: feed plan for a pen-up move that rotates the bed,
    using the travel rate for X/Y and the A rate limit for rotation; returns
    `None` for pure X/Y travel so it stays a `G0` rapid.
- `converter_core/gcode.py`: the contour-entry travel and the between-contour
  travel emit `G1 ... F<feed> (travel)` when the move rotates the bed, and the
  preview move list records the same duration.
- `converter_core/settings.py`: the new A rate default and a docstring that says
  these are the limits the *converter* assumes, not the controller's configured
  maxima - and why the two must be brought together.

## Verification

- 165 tests pass, including a new
  `test_fill_centred_on_the_bed_centre_stays_inside_the_axis_limits`: a gradient
  fill centred on the bed centre may not rotate the bed more than one safe step
  per move, may not ask for more than the assumed A rate, and may not carry a
  bed rotation as a bare `G0`. The two M-06 diagnostic tests were rewritten to
  assert the same contract on the radius sweep and the XY-theta lettering.
- Local reproduction of the reported print (96 mm dark disc centred on the bed
  centre, `Fill spacing 2`, `sine_gradient`, `theta_mode optimized`):

  | | before | after |
  |---|---|---|
  | worst A rate, drawing | 1333 motor deg/s | **333 motor deg/s** |
  | drawing moves over 200 motor deg/s | 2051 | 1933 (all capped at 333) |
  | moves rotating > 30 motor deg in one `G1` | 100 | 37 |
  | bare `G0` moves carrying bed rotation | 1 (a full revolution) | **0** |

- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- First attempt let the parked bed compete on *every* segment by ranking
  candidates by estimated time. That is arguably the "right" cost model, but it
  parks the bed for almost all artwork inside the reach disc and silently turned
  the rotating-bed feature off - the M-06 diagnostics no longer exercised the A
  axis at all. Rejected in favour of a guard that only fires where rotation is
  impossible to execute.
- Rejected lowering `max_acceleration_deg_s2` as well: the per-move acceleration
  cap already scales with the move, and the observed failures are rate-limited.
- Considered replacing the `theta_wrap` unwind with a `G92` A position
  redefinition, which would remove the physical revolution entirely. It needs
  controller verification and changes a documented contract, so it is left as a
  follow-up rather than smuggled into this fix.

## Risks and follow-up

- **The controller still allows the old rates.** `$113`/`$123` must be brought
  down to the same 20,000 motor deg/min (and a matching acceleration) or
  controller-side rapids - jogging, homing, and any `G0` the converter still
  emits for pure X/Y travel - remain as fast as before. That is a bench action
  with a settings dump as evidence; it is recorded in the roadmap.
- A plot whose bed used to spin will now take longer where the bed is the
  bottleneck, and strokes that used to sweep will instead be drawn with the bed
  parked. The drawing is the same; the motion is slower and repeatable.
- The 15 deg step limit is a judgement between bed wear and travel; it is a
  module constant, not a UI field, so changing it is a deliberate code change.

## Files

- `software/converter_core/kinematics.py`: parked-bed candidate, step limit,
  travel feed plan.
- `software/converter_core/gcode.py`: fed pen-up rotations in the emitter.
- `software/converter_core/settings.py`: the A limit default and its rationale.
- `software/tests/test_theta_feed.py`: the centre-fill contract and the rewritten
  M-06 diagnostics.
- `software/README.md`: the operator-facing note.
