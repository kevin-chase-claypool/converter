# Lab Note: 2026-10-14 - Line-replay test, first run and photo analysis

## Objective

First bench run of `samples/gcode/a-line-replay-test.gcode` after the
2026-10-14 registration update: does the line bundle collapse, and what
residual does it show per bed angle?

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01, bed ratio 12.03324 motor
  deg per bed deg.
- Wiring/pin map: unchanged.
- Firmware: the installed build of the 2026-10-13/14 sessions; no change.
- grblHAL settings: unchanged (`$113=15000`, `$111=8000`, `$121=1500`).
- Pen: Pigma Micron 003 on a single US Letter sheet taped flat on the bed.
- Instruments: operator calipers; phone photo `PXL_20261014_210030743.jpg`
  (3072x4080, straight down).

## Code, commands, and configuration used

```text
G65 P113     (HOME + REGISTER)
(load samples/gcode/a-line-replay-test.gcode, Cycle Start)
```

Nominal line lengths: origin 140, closing 128, controls 120, replays 112 /
104 / 96 mm for the 90 / 180 / 270 deg passes.

## Procedure

1. HOME + REGISTER, fresh sheet, Micron 003 mounted as a normal pen.
2. Run the replay program (seven passes, about three minutes, parks at end).
3. Operator calipers the line lengths; straight-down photo of the sheet.

## Results

- **Operator calipers:** origin reads **140.78 mm** (nominal 140); the
  180 deg replay reads **104.91 mm** (nominal 104). Both of those lines run
  along machine X, so both are X-direction length samples.
- **Visual:** most lines coincide; some land exactly on one another.
- **Photo analysis (agent):** paper-derived scale 11.635 px/mm (letter paper;
  width and height agree to 0.1 percent, and the paper edge is sharp at
  2-3 px). The ink resolves into three distinct lines at mid-sheet: the
  reference group (origin + both controls + closing overlapping), a line
  **0.602 mm** off, and a line **1.204 mm** off.
- **Rotation fit** (`e(theta) = C - R(-theta) C`): 90 and 270 deg both land
  at 0.602 mm on the same side (they coincide - one of the "on top of each
  other" pairs), and 180 deg lands at 1.204 mm = 2 x 0.602. That is the
  signature of a residual registration-centre offset of **about 0.60 mm
  perpendicular to the test line** (along-line component not resolved),
  compared with the ~2.46 mm class measured by the different
  pen-to-bed-circle method on 2026-10-13 before the registration update.
- **Length note:** both X-direction lengths read long (+0.78 mm on 140 =
  +0.56 percent; +0.91 mm on 104 = +0.88 percent). The Y-direction lengths
  (the 112 and 96 mm lines) were not yet calipered; the photo length reads
  carry a threshold bias of +/- 1 mm class and are not used for this.

## Difficulties and corrective actions

- The offsets are small relative to the photo's 0.09 mm/pixel. The photo is
  sharp enough to split 0.6 mm lines but not to read below ~0.2 mm; the next
  run should add one straight-down close-up of the cluster (fill the frame).
- The 270 deg replay did not appear as its own line - it coincides with the
  90 deg line, which is exactly what the rotation model predicts for a
  centre offset that is almost purely perpendicular to the tested line.

## Interpretation

The test reads the rotation record directly and the residual is small and
self-consistent: roughly 0.60 mm of centre offset perpendicular to the line
and near zero along it. Two follow-throughs: confirm the sheet's +X
orientation so the offset can be stated in machine Y terms and nudged in the
registration constants, and settle the X-axis length reading with the
Y-direction calipers and the X/Y scale sheet.

## Decisions and next action

- Evidence under `WSW-20261014-001`; bench acceptance still open.
- Next: close-up photo, caliper the 112/96 mm lines, run
  `samples/gcode/xy-scale-check.gcode`, then one registration-constant nudge
  if the ~0.6 mm offset is confirmed.
