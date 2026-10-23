# Lab Note: 2026-10-23 - M-12 rotation-centre calibration photo analysis

## Objective

Determine whether the printed `rotation-center-calibration.gcode` sheet has
enough fiducial and scale information for one-shot image measurement, and
whether the measured 90/180/270-degree errors are explained by a single
rotation-centre offset.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01; measured bed ratio
  12.03324 motor degrees per bed degree.
- Wiring/pin map: unchanged.
- Firmware commit/build: installed production controller and toolhead build
  used for normal plotting; exact source commit not printed by the run.
- grblHAL settings: not changed for this measurement; converter assumed
  `30000` motor deg/min and `6000` motor deg/s^2.
- P100 correction during the run: `axis_center_correction_x = 2.45`,
  `axis_center_correction_y = 0.3`.
- Converter sample: `samples/gcode/rotation-center-calibration.gcode` from
  commit `112eafe`; 13-inch layout on 14-inch round stock.
- Pen: fine dark/magenta fiber-tip pen on white round paper; exact tip size
  not recorded in the supplied message.
- Instruments: straight-down phone photo
  `PXL_20261023_194750580.jpg` (1790 x 2377 pixels), plus software line fitting.

## Code, commands, and configuration used

```text
G65 P113
(load samples\gcode\rotation-center-calibration.gcode, Cycle Start)
```

The four known A=0 reference crosses were used as planar correspondence
points. Their known 40 mm arms were also used to refine the image scale and
orientation. After correcting photo rotation and perspective, the fitted
replay-centre displacements were converted to raw reference-to-replay gaps.

```powershell
python tools\fit_rotation_center.py --baseline-mm 20 `
  --measurement 90,20.7819,19.5908 `
  --measurement 180,20.0076,19.6381 `
  --measurement 270,19.3944,19.6488
```

## Procedure

1. Run `G65 P113`.
2. Plot `samples/gcode/rotation-center-calibration.gcode`.
3. Photograph the completed sheet from above.
4. Locate each longer A=0 reference cross, its L-fiducial, and the shorter
   shifted replay cross.
5. Fit line centres and intersections, use the four reference crosses to
   remove image rotation/perspective, and evaluate the known 20 mm pair
   baseline.
6. Run the centre-offset least-squares fit.

## Results

Image-derived raw gaps:

| Station | Bed angle | GAP_X mm | GAP_Y mm | Centre error X,Y mm |
|---|---:|---:|---:|---:|
| W0 control | 0 | 20.0895 | 19.9904 | +0.0895, -0.0096 |
| S90 | 90 | 20.7819 | 19.5908 | +0.7819, -0.4092 |
| E180 | 180 | 20.0076 | 19.6381 | +0.0076, -0.3619 |
| N270 | 270 | 19.3944 | 19.6488 | -0.6056, -0.3512 |

- The control is within about `0.09 mm` of the nominal 20 mm gaps, which
  validates the label/fiducial layout and image scale.
- The 180-degree pair, directly relevant to the Q1/Q3 complaint, is about
  **0.36 mm short in Y** and essentially zero in X.
- A two-component centre fit gives `C = (+0.0167, -0.3590)` mm, suggesting a
  P100 candidate of `X 2.4667 / Y -0.0590`.
- That centre-only model has `0.350 mm` RMS and `0.412 mm` maximum residual.
  The 90 and 270 degree X errors are too different to be explained by a single
  centre vector.

## Difficulties and corrective actions

- The original concentric-cross design put the thin pen lines almost on top of
  one another. Separated stations and a 20 mm pair baseline corrected the
  read/wet-ink ambiguity.
- The raw phone image is rotated relative the drawing frame. Its perspective
  was resolved from all four printed reference crosses and their known 40 mm
  arms; no additional print was required.
- The apparent small angular component is not being treated as an A-axis
  calibration. Lens distortion, line fit, bed plane, and station-location
  effects remain mixed in one photo.

## Interpretation

The layout is usable for one-shot image calibration, and the single-centre
model is **not** sufficient to explain the full angle-dependent result. The
180-degree residual predicts that a Y correction of about `-0.18 mm` would
improve the explicit Q1/Q3 case, but applying the all-angle centre fit would
still leave a substantial residual and could trade one local error for another.

The remaining pattern is consistent with the previously observed bed
plane/runout error rather than a pure registration-centre error. Keep the P100
constants unchanged until that distinction is resolved.

## Decisions and next action

- No P100 constants changed from this run.
- No additional paper plot is required to extract the four stations from this
  image.
- Next: repeat the measurement analysis on another digital image of the same
  station layout after a fresh registration without reprinting, if possible;
  otherwise add a second station per angle at the next planned calibration
  sheet to separate angle error from bed-position error.
- M-12 status remains partial: image extraction and control passed; a single
  centre correction did not explain the full field.
- Follow-up generated: `WSW-20261023-003` replaces the four-station layout
  with 12 balanced stations and a companion CSV for the next planned sheet.
