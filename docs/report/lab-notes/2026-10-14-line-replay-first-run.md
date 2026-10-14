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

## Second run (tagged build, 21:16)

Photo `PXL_20261014_211653708.jpg` (3072x4080; paper-derived scale
12.98 px/mm). All twelve end tags matched the stepped ladder within about
1 mm, so every line was attributable without tracing.

- **Residuals reproduce the first run.** The reference group is tight to
  about 0.1 mm after the slope is removed; the 90 and 270 deg lines coincide
  at 0.62-0.65 mm from the reference; 180 deg sits at 1.16-1.22 mm - again
  2 x the single step, the same centre-offset signature as run 1
  (0.60 / 0.60 / 1.20 mm). The image-side of the offsets is opposite to the
  first photo, so the sheets were placed differently; the machine-frame
  direction still needs the origin's +X mark to resolve.
- **Photo-scale spans:** X-direction passes read +0.3 percent (origin 140.4,
  closing 128.4, control 120.4, 180 deg 104.2 mm - mutually consistent);
  Y-direction passes read ~0 percent (90 deg 112.2, 270 deg 95.9 mm). Photo
  scale uncertainty is ~0.3 percent, but this sits with the +0.78/+0.91 mm
  caliper reads as a small X-long, Y-true anisotropy - the scale sheet
  remains the clean measurement.
- **Direction resolved and correction applied (operator, evening):** the end
  tags point toward machine +Y, so the replays sitting opposite the tags put
  the true axis about 0.6 mm toward -Y of the registered origin
  (`e(180) = 2C` with `C = (0, -0.6) mm`). Applied
  `#<axis_center_correction_y>` 0.9 -> 0.3 (`RPSW-20261014-002`), X
  unchanged. Expected: the replays collapse onto the reference within
  registration reproducibility; if the centre magnet is on the axis, the
  park now sits about 0.6 mm off the magnet (attribution datum, not a
  fault).
- **Closed (2026-10-14 evening):** the Y 0.3 `P100.macro` was copied to the
  controller SD card; the operator confirms the result looks correct and
  closed the item. The replays-collapse check rides along with the next
  line-replay run; the magnet-versus-chain attribution and the X/Y scale
  sheet remain open.
