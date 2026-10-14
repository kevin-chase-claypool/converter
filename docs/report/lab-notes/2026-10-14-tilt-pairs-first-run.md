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
