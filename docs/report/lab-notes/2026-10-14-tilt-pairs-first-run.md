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

- The generator gains `--station-shift-y`; the committed sample is
  regenerated with `--station-shift-y -25` so the next run uses clean rows
  (y = +25 and -75) on the same sheet.
- Next: feeler-gauge the tip-to-paper gap at the four spots with the pen up
  to pin which corner is high or low and by how much; adjust the rail ends -
  raise the end where the gap is small, lower it where the gap is large,
  starting with about half the difference - then re-run the pairs test on the
  shifted stations and compare. Caliper cross-check requested: 180 deg pair
  ~1.0-1.2 mm, 90 deg pair ~0.6-0.7 mm.
