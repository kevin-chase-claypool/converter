# Lab Note: 2026-10-23 - M-12 retaped verification sheet invalid

## Objective

Determine whether the latest compensated verification sheet can be used to
accept or reject the corrected bed-compensation profile after the operator
changed tape while trying to remove a paper bubble.

## Configuration

- Hardware revisions: RP23CNC `RP23U5XBB` V1.01; installed production
  X/Y/A mechanics and toolhead.
- Wiring/pin map: unchanged.
- Firmware commit/build: installed production controller build; no firmware
  changed for this check.
- grblHAL settings: not supplied with this run.
- Intended verification program: `samples\gcode\bed-error-verify.gcode`,
  corrected machine-frame profile `2cdf3731de4a`.
- Actual loaded program/fingerprint: not proven by the supplied photo or
  console log.
- Sheet: 14-inch round stock, with multiple blue tape changes around the rim
  while attempting to remove a bubble.
- Photo:
  `assets/2026-10-23-m-12-retaped-verification-invalid.jpg`, 1742 x 2313 px,
  SHA-256
  `4efb24a9e6bb132e1547105bed50a41f195d9f40573dbb816702cba82e91c790`.

## Code, commands, and configuration used

```text
G65 P113
(intended corrected verification: samples\gcode\bed-error-verify.gcode,
 profile fingerprint 2cdf3731de4a)
(tape around the sheet was changed during the workflow to address a bubble)
```

```powershell
python tools\measure_bed_error_photo.py `
  C:\Users\jacks\AppData\Local\Temp\cal3_rotated.jpg `
  --seed-diagnostic samples\gcode\bed-error-map-2026-10-23-photo.json `
  --maximum-assignment-px 24
```

The source photo is portrait-oriented with the printed labels rotated by
90 degrees. It was rotated counter-clockwise for inspection; this does not
alter the geometry.

## Procedure

1. Inspect the supplied photo and rotate it so the station labels are upright.
2. Attempt seeded marker extraction against the known 37-station layout.
3. Check whether all 185 station L markers can be assigned uniquely and
   consistently from the four fiducials.
4. Reject the sheet if paper motion or local distortion prevents a stable
   one-to-one marker extraction.

## Results

- The sheet shows multiple changed tape placements around the periphery.
- Several long drag lines cross the field, particularly around stations 19,
  24, 28, and 30.
- Seed-assisted extraction found four fiducials but could not assign all 185
  station markers within a safe 24 px local radius. The failed assignment
  included residuals over 40 px, far beyond the expected 10 mm lane spacing.
- The visible station pattern is locally irregular around the retaped region.
  No valid 189-row measurement set was produced.

## Difficulties and corrective actions

Changing tape after printing starts can move, stretch, or relax the paper.
Even if the bed and controller do not move, the measurement coordinates for
marks made before the tape change no longer describe the same paper geometry
as marks made afterward. The four fiducials cannot correct a non-rigid change
in the sheet.

The long drag lines also mean the paper was not a clean reference surface:
either the toolhead did not fully clear or the sheet changed under the pen.
Those lines cannot be separated from the compensation result reliably.

## Interpretation

This print is invalid for accepting or rejecting profile `2cdf3731de4a`.
It is useful as handling evidence: a moving sheet, trapped bubble, or tape
adjusted during a run can create the same class of local displacement as a
bed/planner defect.

## Decisions and next action

- Do not enter this image into the compensation comparison.
- Do not use this sheet as the reference for another print.
- Prepare a fresh sheet completely before `G65 P113`: flatten the center,
  secure the perimeter, inspect for bubbles, and do not change any tape after
  the first drawing mark.
- If a bubble develops or the sheet moves during the run, abort. Finish the
  verification on a new sheet instead of retaping the active one.
- The corrected profile remains provisional at fingerprint `2cdf3731de4a`.
