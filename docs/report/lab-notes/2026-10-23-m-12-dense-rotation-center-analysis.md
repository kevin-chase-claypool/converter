# Lab Note: 2026-10-23 - M-12 dense rotation-centre sheet

## Objective

Use the 12-station balanced calibration sheet to determine whether the
rotation-angle error is a common centre offset or changes with position across
the bed.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; measured bed ratio
  12.03324 motor degrees per bed degree.
- Wiring/pin map: unchanged.
- Firmware commit/build: installed production controller build; no settings
  changed for this measurement.
- P100 correction during the run: `axis_center_correction_x = 2.45`,
  `axis_center_correction_y = 0.3`.
- Converter sample: `samples/gcode/rotation-center-calibration.gcode` from
  commit `de6c4fc`; 12 stations in a 4 x 3 lattice.
- Sheet: 14-inch round stock, 13-inch planned pattern footprint.
- Pen: fine dark fiber-tip pen; exact tip size not recorded in the supplied
  photo.
- Instruments: photo `PXL_20261023_202125801.jpg` (1784 x 2369), rotated 90
  degrees for analysis, then fitted from the printed L-fiducials, reference
  crosses, and known 36 mm reference arms.

## Code, commands, and configuration used

```text
G65 P113
(load samples\gcode\rotation-center-calibration.gcode, Cycle Start)
```

```powershell
python tools\fit_rotation_center.py `
  --baseline-mm 20 `
  --measurements-csv samples\gcode\rotation-center-calibration-2026-10-23.csv
```

## Procedure

1. Run `G65 P113`.
2. Plot the 12-station calibration program on a fresh 14-inch sheet.
3. Photograph the complete sheet from above.
4. Rotate the image to make the printed labels upright.
5. Locate all twelve L-fiducials and use them with the known lattice positions
   to establish the sheet-to-image transform.
6. Locate the longer A=0 reference crosses and shorter replay crosses at all
   twelve stations.
7. Convert the reference-to-replay displacements to bed-frame gaps, subtract
   the 20 mm baseline, and fit the repeated angles.

## Results

| Station | Bed position mm | Angle | GAP_X mm | GAP_Y mm |
|---|---|---:|---:|---:|
| 0-1 | (-90, -70) | 0 | 20.0592 | 20.1615 |
| 0-2 | (-30, 0) | 0 | 19.9314 | 19.0388 |
| 0-3 | (30, 70) | 0 | 20.1122 | 20.4598 |
| 90-1 | (-30, -70) | 90 | 20.5891 | 19.7230 |
| 90-2 | (30, 0) | 90 | 19.8290 | 19.4766 |
| 90-3 | (90, 70) | 90 | 19.9774 | 19.5520 |
| 180-1 | (30, -70) | 180 | 20.1393 | 19.4491 |
| 180-2 | (90, 0) | 180 | 20.2564 | 20.1323 |
| 180-3 | (-90, 70) | 180 | 19.8474 | 19.5254 |
| 270-1 | (90, -70) | 270 | 20.1997 | 19.5450 |
| 270-2 | (-90, 0) | 270 | 20.2507 | 19.6178 |
| 270-3 | (-30, 70) | 270 | 19.4466 | 19.8634 |

- Control raw gaps: X mean `20.0343`, range `19.9314..20.1122` (0.181 mm);
  Y mean `19.8867`, range `19.0388..20.4598` (1.421 mm).
- Control bias removed from the angle rows: `(+0.0343, -0.1133)` mm.
- Corrected 90-degree mean error: `(+0.098, -0.303)` mm; position spread
  `(0.403, 0.126)` mm standard deviation.
- Corrected 180-degree mean error: `(+0.047, -0.184)` mm; spread
  `(0.211, 0.374)` mm.
- Corrected 270-degree mean error: `(-0.069, -0.211)` mm; spread
  `(0.450, 0.167)` mm.
- Repeated-angle centre fit: `C=(+0.004,-0.131)` mm, RMS residual `0.385 mm`,
  maximum residual `0.551 mm`.
- The fit would suggest P100 `X 2.4539 / Y 0.1689`, but that correction was
  **not applied**.

## Difficulties and corrective actions

- The lens/perspective fit across the printed fiducials has roughly 0.1-0.2 mm
  class uncertainty. The measured A=0 Y spread is much larger than that.
- The first four-station layout could not separate angle from position. The
  balanced 4 x 3 station set was created specifically for this run.
- A mechanical datum was not available to separate image measurement error from
  pen-carriage motion caused by bed height. That distinction remains open.

## Interpretation

The tight control consistency was not present across locations: even at A=0,
the Y baseline varies by 1.421 mm across the bed. The three repeated angle
samples also scatter by about 0.2-0.45 mm around their means. A single P100
centre offset fits the repeated set poorly (`0.551 mm` maximum residual), while
the per-angle mean offsets are small.

Therefore the larger defect is **position-dependent bed/pen geometry**, not a
global rotation-centre error. This is consistent with the previously measured
bed plane/runout and carriage coupling. Applying the centre-fit constants would
give a small average correction but would not remove the visible striations.

## Decisions and next action

- Keep P100 unchanged.
- Do not print another calibration sheet until the spatial term is addressed.
- Use the existing bed mesh/probe workflow to correlate the 4 x 3 station
  offsets with bed height at A=0. If that correlation is strong, correct the
  mechanical plane/runout or implement a separately validated spatial
  compensation map.
- If a software spatial correction is pursued, it must be tested against these
  repeated stations, including all three A=0 controls, and must not be folded
  into the P100 centre constants.
