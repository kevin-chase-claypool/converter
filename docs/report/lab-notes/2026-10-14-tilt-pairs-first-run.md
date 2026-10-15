# Lab Note: 2026-10-14 - Bed-tilt pair test, first run (post frame fix)

## Objective

First bench run of `samples/gcode/a-tilt-pairs-test.gcode`, on the sheet
already on the bed and after the Y 0.3 re-registration: measure the pair
offsets per quadrant and decide whether they still carry the pre-fix frame
ladder or the real bed-height-vs-angle signal.

## Configuration

- RP23CNC / `RP23U5XBB` V1.01; bed ratio 12.03324; installed firmware of the
  2026-10-13/14 sessions.
- Re-registered with the new P100 (`Y 0.3`) before the run. The operator
  verified the park with a magnet: the pen sits at the magnet centre.
- Pen: Pigma Micron 003 on the same sheet as the line-replay runs; the sheet
  stayed taped, nothing was moved.
- Photo: `PXL_20261014_215907601.jpg`, 3072x4080. The image is mirrored
  (front camera): the layout-vs-label check and the operator's +X jog
  (moves toward image-right) both indicated it, so measurements were
  converted with machine_x = -image_x, machine_y = +image_y.

## Code, commands, and configuration used

```text
G65 P113      (HOME + REGISTER; new P100 with Y 0.3)
(load samples/gcode/a-tilt-pairs-test.gcode; Cycle Start)
```

## Procedure

1. Re-register; the magnet check confirmed the park.
2. Run the pairs test: four pairs (control / 90 / 180 / 270), each pair = the
   same paper segment drawn at A=0 (constant, 80 mm) and at that angle
   (test, 66 mm); zigzag labels of 1-4 teeth.
3. Photos, plus the operator's jog check for +X.

## Results

- Control pair: the two passes printed on top of each other - a single line,
  <= ~0.15 mm.
- 90 deg: two lines ~0.6-0.7 mm apart mid-length, crossing/merging toward
  both ends (lens shape).
- 180 deg: the cleanest split, ~1.0-1.2 mm over most of the length, slight
  taper.
- 270 deg: two lines close in the middle (~0.3-0.6 mm) opening to
  ~0.8-1.1 mm toward one end.
- Pattern: single-step pairs ~0.6-0.7 mm, double pair ~1.1 mm, control zero.
  The ratio repeats the pre-fix frame ladder, but the frame was re-registered
  and magnet-verified this time, and every non-control pair tapers along the
  line - which a pure frame offset cannot produce.

## Difficulties and corrective actions

- The photo is mirrored (front camera); resolved with the layout check and
  the operator's +X jog direction.
- Reading resolution at this framing is ~0.1-0.2 mm; a close-up shot would
  tighten it, but the current numbers already separate the two hypotheses.

## Interpretation

The residuals match the bed-height-vs-angle mechanism read through the pen
carriage: a tilt of roughly 1 percent along the NE-SW diagonal (consistent
with the static ~1 mm map) would produce single-step ~0.6 mm and double-step
~1.1 mm at these stations, with the observed taper/lens shapes. The frame
term is no longer the explanation.

## Decisions and next action

- The operator flipped the sheet after the run, so the next run repeats the
  original station layout on the now-blank other side - a directly
  comparable before/after. The generator gains `--station-shift-y` for
  later re-runs once that side fills up.
- Next: feeler-gauge the tip-to-paper gap at the four spots with the pen up
  to pin which corner is high or low and by how much; adjust the rail ends -
  raise the end where the gap is small, lower it where the gap is large,
  starting with about half the difference - then re-run the pairs test on the
  shifted stations and compare. Caliper cross-check requested: 180 deg pair
  ~1.0-1.2 mm, 90 deg pair ~0.6-0.7 mm.

## Second run (flipped sheet, new pen)

After the first run the operator flipped the sheet, re-taped it and swapped
to a new pen; the same program ran on the now-blank side (photo
`PXL_20261014_224427293.jpg`). Pairs were read by their tooth labels:

- control: single line, <= 0.15 mm.
- 90 deg: ~0.70-0.80 mm.
- 180 deg: ~1.00-1.20 mm.
- 270 deg: tapers from ~0.1-0.2 mm at one end to ~0.7 mm (its test line
  printed noticeably fainter than the others).

Every value reproduces the first run within ~0.05-0.1 mm - on the other
sheet side and with a different pen. The tilt signature is stable and the
measurement is reproducible.

The operator also marked the sheet with +X/+Y direction arrows plus a DRO
coordinate whose first value was crossed out (the kept value is the true
one at the moment the print stopped). The arrow frame read from the photo
(+X pointing down, +Y pointing right) does not yet agree with the pairs
arrangement, so machine directions need a wording confirmation before any
compass-based rail-end instruction.

## Decisions and next action (updated)

- Immediate next step: the four-spot pen-up gap check at machine (-50,-50),
  (50,-50), (50,50), (-50,50) - no ink, repeatable every iteration. Report
  the smallest and largest corner and the differences.
- The committed pairs sample is set to `--station-shift-y -25` (fresh rows
  at y = +25 / -75 on the flipped side) for a confirmation run once the
  gaps are under control.

## Static gap check at the four quadrant centres (2026-10-14 evening)

Pen-up gap readings with the bed left at the print's stopping angle and the
pen at full GP2 retract (absolute values ~5-6 mm; only the differences
matter):

| quadrant | machine (X, Y) | gap mm | vs Q3 |
|---|---|---:|---:|
| Q1 (180 deg pair) | (+50, +50) | 6.13 | +1.12 |
| Q2 (270 deg pair) | (-50, +50) | 5.73 | +0.72 |
| Q3 (control) | (-50, -50) | 5.01 | reference |
| Q4 (90 deg pair) | (+50, -50) | 5.69 | +0.68 |

Plane fit: +0.54 mm per 100 mm along +X and +0.58 mm per 100 mm along +Y
(about 0.8 percent, tilted toward the Q3-Q1 diagonal), residuals within
+/-0.07 mm - a clean plane across these four points.

**Cross-check with the pairs test:** each quadrant's drawn split equals its
static gap difference almost exactly (Q1: 1.0-1.2 mm vs 1.12; Q4:
0.70-0.80 vs 0.68; Q2: taper to ~0.7 vs 0.72). The ink displacement tracks
the height difference about 1:1, so the two independent measurements agree
and fixing the heights should fix the drawings by the same amount.

**Adjustment (Q3 stays the constant):** a larger gap means the surface sits
farther from the pen, so bring that corner's rail end DOWN (toward the bed) -
Q1 by ~1.1 mm, Q2 by ~0.7 mm, Q4 by ~0.7 mm (about 1.6 / 1.0 / 1.0 turns if
the screws are M4 at 0.7 mm per turn); Q3's end is untouched.

The amounts are those measured at the +/-50 mm spots. An adjuster sitting
farther from the bed centre needs a proportionally larger move, so half the
amounts first if the corner-to-mount mapping needs verifying, then re-read
the same four spots at the same bed angle and trim. Per-adjuster numbers
come from `bed_tilt_map.py --rail-mounts` once the four rail-end XY
coordinates are supplied.

## Third run - post bed-mount adjustment (2026-10-14 23:55)

After the operator's bed-mount adjustment, the pairs test ran again (photo
`PXL_20261014_235526094.jpg`). The sheet carries only this run's four
labeled pairs. Pairs were read by tooth label, with the line profile
measured in the photo (px/mm about 8.5 from the letter sheet, cross-checked
against the 100 mm column spacing; read precision about +/-0.1-0.15 mm):

| pair | label | split this run | previous runs |
|---|---|---:|---|
| control | 1 tooth | single line (<= 0.2 mm) | single |
| 90 deg | 2 teeth | ~1.0 mm, steady along the line | 0.70-0.80 |
| 180 deg | 3 teeth | ~0.9 mm, slight taper | 1.00-1.20 |
| 270 deg | 4 teeth | collapsed - single (double-inked) line | taper ~0.1-0.2 to ~0.7 |

The 270 deg pair collapsed - the first quadrant to come flat. The 90 deg
and 180 deg pairs still split about a millimetre, roughly the same
magnitude as before, so the pending four-spot gap re-read and the applied
adjustment amounts will say whether those two corners simply need more
trim or something else is at play.

Gap re-reads after the adjustment (same four spots, pen fully retracted):

| spot | before | after | vs control (after) |
|---|---:|---:|---:|
| Q1 (+50, +50) | 6.13 | 9.55 | +0.38 |
| Q2 (-50, +50) | 5.73 | 9.48 | +0.31 |
| Q3 (-50, -50) control | 5.01 | 9.17 | reference |
| Q4 (+50, -50) | 5.69 | 8.94 | -0.23 |

The plane flattened: the spread fell from 1.12 mm to 0.61 mm and Q4 crossed
slightly past the control. Every gap, however, rose by about 3.2-4.2 mm
(+3.6 mm on average). The operator confirms the adjustment was applied as
prescribed (Q1 +1.12, Q2 +0.72, Q4 +0.68 mm, control untouched) and that
the pen was replaced afterwards - the new pen seats with a shorter tip
protrusion, so the global rise is the pen, not a mount effect. Absolute
gaps are therefore comparable only within one pen; the differences remain
valid.

The pairs pin the rest: 90 deg (~1.0 mm) and 180 deg (~0.9 mm) are both
driven by the same single remaining tilt of about 1 mm per 100 mm along
machine Y, while the 270 deg pair - the component along the other axis,
now at zero - reads clean. The next trim targets that one component. The
committed sample is regenerated with `--station-shift-y 25` (fresh rows at
y = -25 / +75) for the next run.

## Fourth run and corner re-read after the direction-check trim (2026-10-14 evening)

Timeline note: the photo ID `PXL_20261015_004437657` is on the phone clock
(UTC), i.e. 2026-10-14 19:44:37 CDT. The operator sent it together with a
fresh four-corner caliper read; which adjusters had been moved by that point
is not yet confirmed.

Corner gaps as reported (same four spots as the earlier read, pen retracted,
bed at the current park angle):

| spot | machine (X, Y) | gap mm | vs control |
|---|---|---:|---:|
| Q1 | (+50, +50) | 8.68 | +0.19 |
| Q2 | (-50, +50) | 9.30 | +0.81 |
| Q3 | (-50, -50) control | 8.49 | reference |
| Q4 | (+50, -50) | 8.94 | +0.45 |

- Spread 0.81 mm (read history: 1.12 mm before the first adjustment,
  0.61 mm after it).
- Plane fit: -0.09 mm per 100 mm along X, +0.28 mm per 100 mm along Y,
  corner residuals +/-0.27 mm - a twist the two earlier reads did not show
  (+/-0.08 and +/-0.07 mm).
- Against the post-adjustment read (9.55 / 9.48 / 9.17 / 8.94):
  Q1 -0.87, Q2 -0.18, Q3 -0.68, Q4 0.00. The control corner moved 0.68 mm
  with no mount move, so unless the bed angle matched, the two reads are
  not piecewise comparable; the A value of a gap read is not recorded yet.
- Q2 is now the single worst corner at +0.81 mm over the control.

Pairs re-run (photo `PXL_20261015_004437657`; line-profile analysis,
y-scale from the sheet height and the 100 mm row spacing, about 8.9 px/mm,
read precision about +/-0.1 mm). The sheet is not the third run's sheet
(that one carried an extra corner sketch this one does not), so this is a
new run, not a re-photo. The third-run photo was re-measured with the same
method for comparison.

| pair | fourth run | third run (same method) |
|---|---:|---:|
| control | single (<=0.2 mm) | single |
| 90 deg | ~1.26 mm | ~0.98 mm |
| 180 deg | ~1.09 mm | ~0.90 mm |
| 270 deg | single | single |

- The 90 deg and 180 deg pairs still split about a millimetre; the trim did
  not shrink them - they read 0.2-0.3 mm larger than the third run. The
  plan's own rule ("splits shrink -> finish with a scaled second step;
  grow -> reverse") would point at reversing, but the change is close to
  the reading precision and the applied adjuster moves are unconfirmed, so
  confirm before turning screws.
- Both photos place the four pairs at the same paper-relative positions
  (top row about 62-64 mm below the sheet's top edge), so the "next fresh
  band" shift does not appear in what was run; the two runs sample
  equivalent stations up to the usual 180 deg sheet-placement ambiguity.

Cross-check: the static corner differences (<=0.8 mm across the read, and
roughly 0.1-0.3 mm in the directions the pairs sample) are far smaller
than the ~1.1-1.3 mm pair splits, and no plane can produce them. The
leading candidate remains a bed-angle-dependent term - the disc plane not
normal to the rotation axis, or surface warp (the queued `HW-20261011-001`
follow-up) - which neither single-angle corner reads nor rail-end trims
capture.

Next measurements, before another adjuster move:

1. Record the bed angle A with every gap read; read the four corners at A
   and at A+180 and use the two-angle average (it cancels the wobble term).
2. Run the committed rotation gap map
   (`samples/gcode/gap_map_rot.gcode`, r = 60/90, 30 deg steps,
   `gap_map_rot.csv`) and analyze with `bed_tilt_map.py` - gap versus angle
   separates wobble from rail tilt.
3. Supply the four rail-end XY coordinates for
   `bed_tilt_map.py --rail-mounts`, and verify the corner-to-adjuster
   mapping with one single-adjuster move before the next trim.

## Rotation gap map - first ring scan (2026-10-14, after the fourth run)

The committed `gap_map_rot.gcode` scan (r = 60 / 90 mm, 30 deg steps) was
read start to finish; the `M0` pauses worked on the installed build, and the
24 readings are in `samples/gcode/gap_map_rot.csv`. Instrument
(operator-confirmed): hand-held digital caliper at the pen tip, best-effort
placement - a ~+/-0.1-0.2 mm class measurement per reading. The ring spreads
and the 60 / 240 deg dips stand well outside that; the sub-0.15 mm harmonic
details are provisional.

Raw readings (gap mm per index):

| index | 0 | 30 | 60 | 90 | 120 | 150 | 180 | 210 | 240 | 270 | 300 | 330 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r = 60 | 9.69 | 9.18 | 8.51 | 8.75 | 9.11 | 8.91 | 9.14 | 9.09 | 8.62 | 8.98 | 8.92 | 9.22 |
| r = 90 | 9.02 | 8.85 | 9.39 | 9.20 | 9.48 | 9.42 | 9.31 | 9.29 | 9.39 | 9.27 | 9.26 | 9.05 |

- r = 60: mean 9.01 mm, spread 1.18 mm (8.51 .. 9.69). r = 90: mean
  9.24 mm, spread 0.63 mm (8.85 .. 9.48).
- Harmonic content (index space): r = 60 is dominated by a two-lobe term
  (0.31 mm, maxima near index -10 / 170 deg) plus a 0.13 one-lobe and a
  0.14 three-lobe; fit residual rms 0.18 mm. r = 90 is mostly one-lobe
  (0.18 mm, maximum near index 176 deg) with a small 0.11 two-lobe; fit
  residual rms 0.10 mm.
- `bed_tilt_map.py` verdict: plane part only 0.078 mm per 100 mm; residual
  after the plane fit rms 0.241 mm, max 0.726 mm - "not a rigid tilt;
  expect warp/bearing runout". Per-radius residuals: r = 60 -> 0.308 mm,
  r = 90 -> 0.147 mm.
- One rigid tilt (single direction, amplitude growing with radius) cannot
  produce both rings: the best-constrained rigid model leaves rms 0.23 mm
  and the one-lobe phases of the two rings sit ~106 deg away from the
  rigid-tilt relation. The biggest single feature is the r = 60 two-lobe
  dip (indices 60 and 240, about 0.5 mm below the ring mean).
- Scale check: the gap-versus-index spread (0.6-1.2 mm) is the same class
  as the pair-test splits (1.0-1.3 mm) the rail trims could not remove, and
  the plane part is now tiny - the remaining error is a surface-shape term,
  not a rail-plane tilt. Whether that shape sits in the sheet/tape or in
  the disc/hub is not yet resolved (the scan runs on the taped sheet), and
  how the pair-test splits couple to it still needs the follow-up checks.

Next checks, cheapest first:

1. Repeat the r = 60 ring (or re-read the eight extreme stops in a shuffled
   order) to test repeatability of the 60 / 240 deg dips.
2. Re-run part of the r = 60 ring with the sheet removed (bare disc):
   pattern persists -> disc/hub; pattern moves with the sheet -> paper
   ripple or tape.
3. Run the grid scan with the bed parked and the same gauge for the
   machine-frame plane at the working angle, then decide whether any rail
   trim remains.
4. Prefer a dial indicator clamped to the carriage for the repeat scans so
   neither the hand placement nor the pen-tip `M5` position is in the
   measurement chain; a repeat with the digital caliper is still useful as
   a same-method reproducibility check.
