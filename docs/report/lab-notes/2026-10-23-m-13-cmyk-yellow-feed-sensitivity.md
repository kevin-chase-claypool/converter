# Lab Note: 2026-10-23 - CMYK wave-screen feed sensitivity

## Objective

Determine whether the striations remaining in the compensated CMYK yellow
wave-screen print are sensitive to drawing feed rate and therefore caused by
bed/A motion dynamics rather than incorrect compensation coordinates.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine; the operator
  reports that a replacement motor is arriving for the bed/A drive, intended to
  match the motor already installed on Y. The replacement was not installed for
  this observation.
- Wiring/pin map: unchanged.
- Firmware commit/build: the exact toolhead and controller builds active during
  the print were not captured. The converter G-code was generated before the
  130 ms M5-clearance source change in `98251f8`.
- grblHAL settings: the saved program assumes `$113=30000` motor deg/min and
  `$123=6000` motor deg/s2.
- Converter settings/sample: `samples/gcode/Ben1/IMG_0514-cmyk-yellow.gcode`;
  `feed 700 mm/min`, `travel 3000 mm/min`, `tolerance 0.050 mm`, centre hold
  `64 mm`, Xθ/Yθ bed motion, and bed-compensation profile
  `4c8270de8a74` / coverage `171.450 mm`.
- Instruments: direct visual inspection by the operator. No calibrated photo of
  the completed comparison region and no controller feed-override log were
  captured.

## Code, commands, and configuration used

```powershell
py tools\check_gcode_motion.py --strict samples\gcode\Ben1\IMG_0514-cmyk-yellow.gcode
```

The saved program reports:

```text
moves: 35136 drawing, 626 travel (14313 parked-bed moves)
largest bed rotation in one drawing move: 6.18 deg (cap 15.0)
largest A rate demanded: 254 motor deg/s (limit 500)
strategies: hold 14313, travel 627, x_theta 6636, y_theta 14187
bed re-registrations: 43
```

The operator reduced the controller feed override to **65 %** of the programmed
700 mm/min, or **455 mm/min**. The exact ioSender action and transition line
were not recorded.

## Procedure

1. Run the compensated yellow program at its programmed 700 mm/min draw feed.
2. Observe the recurring striations.
3. Continue the print with the controller feed override reduced to 65 %.
4. Compare the slowed region visually with the prior region.

## Results

- The operator reports that the striation appears to be eliminated in the
  455 mm/min region.
- Assuming a uniform feed override across X/Y/A, the file's largest A rate falls
  from about `254` to `165 motor deg/s`, still well below the `500 motor deg/s`
  limit.
- No fixed-feed repeat, calibrated image, or post-run measurement was captured,
  so this is partial bench evidence rather than a formal M-13 pass.

### 2026-10-24 magenta follow-up

- The same Ben1 set's magenta layer was run at a 60 % controller feed override,
  or `420 mm/min`. The operator reports that striations remained very visible,
  especially on the subject's right side of the face.
- `IMG_0514-cmyk-magenta.gcode` normally demands a maximum A rate of
  `254 motor deg/s`; at 60 % this falls to about `152 motor deg/s`. The file
  has 996 A-direction reversals, fewer than the yellow layer's 2,777.
- Magenta uses 893 planned contours and 26,850 drawing moves, versus yellow's
  627 contours and 34,509 drawing moves. The remaining magenta defect is
  therefore not explained by a larger file-wide reversal count or a higher
  command-rate demand alone.

### 2026-10-24 black and center-location follow-up

- The operator reports that black also shows the striation near the bed center
  and that both black and magenta defects are in the center region. The exact
  feed override used for the black run was not recorded.
- The black file has 11,481 `hold` moves and 726 contours containing hold
  moves. Magenta has 9,599 hold moves and 593 such contours; yellow has 14,313
  hold moves and 480 such contours.
- `IMG_0514-cmyk-black.gcode` passes its motion preflight. Its full-feed maximum
  A rate is about `254 motor deg/s`, and its largest drawing rotation is
  `6.70 bed deg`, both inside the configured caps.
- The center-hold implementation parks the bed within each contour, but it can
  choose a different held A angle for different contours. The saved programs
  contain hundreds of distinct held angles: magenta spans about `-241` to
  `173 deg`, black about `-102` to `46 deg`, and yellow about `-185` to
  `236 deg` after whole-revolution normalization.

### 2026-10-24 planner-spacing clarification

- The operator clarified that "striation" means adjacent wave-screen rows are
  not equidistant after compensation. It is not a generic description of ink
  texture or surface roughness.
- A dense fixed-angle sampling of the installed correction field around the
  center found that a nominal `2.2 mm` row pair remains within about
  `0.04 mm` of the requested spacing across all four calibrated angles. The
  local correction field therefore does not by itself introduce large
  fixed-angle spacing jumps.
- The center-hold planner does not use one common angle for the whole center:
  it can set a different held A angle for each contour. The verification
  residual is angle-dependent, with separate center-region vector offsets for
  0/90/180/270 degrees. Adjacent rows drawn at different held angles can
  therefore land with different residual shifts even though each row is
  individually represented in bed coordinates.

## Difficulties and corrective actions

- The exact feed-override transition point and resulting photo were not
  captured. A repeat should use separate files or an instrumented override
  transition so the 700 and 455 regions are directly comparable.
- Changing the converter's Feed rate alone would not necessarily reproduce this
  test because the bed tangential-speed setting is independent. To generate an
  equivalent whole-program rate reduction, scale both Feed rate and Theta
  tangential speed to 455 mm/min, or use a uniform controller feed override.
- The magenta follow-up had no accompanying photograph, so the stripe
  orientation, pitch, and exact location could not be measured.

## Interpretation

The compensation coordinates remain unchanged when feed rate changes. The clean
yellow print at 65 % therefore indicates rate-dependent motion error, not a
static bed-compensation or G-code-coordinate error. The leading boundary for
yellow is the rotating-bed/A drivetrain and its response under load.

Magenta remains defective at an even lower speed and has fewer A reversals, so
the yellow result cannot yet be generalized. With black also failing near the
bed center, the strongest software-side hypothesis is now **center-hold angle
inconsistency**: the bed is parked during each center contour, but it can stop
at a different A angle between contours. The correction profile is
angle-dependent and its verified residual differs by angle
(`90 deg: 0.278 mm RMS`, `180 deg: 0.389 mm`, `270 deg: 0.353 mm`), so adjacent
center contours drawn at different held angles can disagree by several tenths
of a millimetre even when every individual coordinate is "compensated."

The accepted `0.338 mm` overall RMS / `0.752 mm` maximum static residual is
common to all channels; the angle-dependent part is more likely to become
visible where hold angles vary. Magenta/black ink flow or contrast, local bed
height, and X/Y carriage behavior remain alternatives until a parked-bed test
rules them in or out.

For the clarified row-spacing symptom, the fixed-angle algorithm itself is not
currently showing a large error. The unresolved mechanism is the transition
between contours parked at different A angles, combined with imperfect
angle-dependent correction. It is also necessary to distinguish physical paper
spacing from Euclidean spacing in the rotated/compensated machine-coordinate
preview; the latter is not expected to remain constant because it is the
machine-space warp that compensates the paper.

### 2026-10-24 angular interpolation frame defect

- Follow-up testing found a separate compensation defect that can worsen
  striation: the profile linearly blended already-rotated machine-XY
  corrections between bed angles.
- A constant 1 mm bed-frame error sampled at 0/90 degrees produced a
  `0.500/0.500 mm` correction at 45 degrees instead of the correct
  `0.707/0.707 mm`. The installed profile's off-cardinal corrections changed
  by up to `0.485 mm` after converting interpolation into the rotating frame.
- The planner now converts neighboring machine corrections back into the bed
  frame, interpolates there, and rotates the result into machine XY. New
  compensated G-code carries `angular interpolation bed-frame` in its header.
- All compensated G-code saved before this change must be regenerated before
  continuing physical comparisons.
- This fix does not replace the eight-angle calibration: interpolation now
  behaves correctly between samples, while the new sheet measures 45° and the
  other previously missing angular fields directly.

### 2026-10-24 black edge-overrun follow-up

- The operator supplied `postcal.jpg`, which shows black wave rows continuing
  across blue edge tape near the subject's left shoulder while the nearby
  magenta/yellow fields end earlier.
- The Ben1 black G-code is an old compensated program: its header contains the
  profile fingerprint but not the new `angular interpolation bed-frame`
  marker.
- The program has no sudden coordinate excursion. Its largest pen-down move is
  `3.447 mm` near the bed center. The source bed-space clip reaches exactly
  `171.450 mm`, the configured 13.5-inch drawable radius.
- Pre-compensation clipping does allow machine-space corrections outside that
  nominal radius. The largest old black machine radius is `171.785 mm`. After
  replaying the recovered bed points through the corrected rotating-frame
  interpolation, the corresponding shoulder-side boundary point moves from
  `171.785` to `171.476 mm`.
- If the black overrun remains after regenerating with the interpolation
  marker, the next checks are the actual round-stock diameter and tape
  intrusion into the 6.35 mm configured rim margin.

### 2026-10-24 wave-amplitude aliasing isolated

- The operator confirmed that the same spacing bands occur in all four CMYK
  G-code layers after restarting the converter.
- The regenerated Ben1 set at 15:20 carries
  `angular interpolation bed-frame`, uses `F700`, and records a 60 mm centre
  hold. The current file therefore exercises the current compensation and
  controller settings.
- The intermediate yellow SVG has row centre pitches of exactly `3.08 mm`.
  Reconstructing the compensated bed-space G-code gives a `3.0736 mm` row fit
  with `0.0082 mm` RMS and `0.0465 mm` maximum residual. The motion planner is
  not changing the baseline grid.
- At a fixed horizontal position, the source SVG's local wave-to-wave gaps
  ranged from about `2.38` to `3.57 mm` around that `3.08 mm` pitch. Each row
  independently multiplied tone into the sine displacement, so vertical image
  detail at the row frequency produced the visible spacing bands.
- `_wave_rows` now averages displacement tone over four adjacent rows and
  limits its change to `0.04` between rows. The unsmoothed tone still controls
  ink coverage. The change applies to all four CMYK screen angles.
- Controlled regressions at `15/75/0/45` degrees reduce the adjacent-gap
  spread below `0.15 mm`; the failing zero-degree fixture previously varied
  by `2.28 mm`. A separate smooth-gradient test confirms wave amplitude still
  follows broad image shading.
- No post-fix paper print has been made yet, so M-13 remains open.

## Decisions and next action

- Regenerate all four Ben1 layers, require `angular interpolation bed-frame`
  in every header, and print the yellow layer first at the same `F700`,
  `$120=600`, and `$121=300` used for the failing run. This tests the current
  wave generator without changing a second variable.
- If the repaired wave screen still shows spacing bands, inspect row ink
  continuity and toolhead contact separately before changing acceleration.
- Keep 700 mm/min as the nominal requested feed for now and use a 65 % override
  for quality-critical Xθ/Yθ yellow work until the drivetrain is improved.
- Repeat magenta alone in **Bed motion = XY only** at the same 420 mm/min. If it
  is clean, the remaining defect is rotary/A motion; if it persists, move to
  pen/ink/screen isolation.
- Repeat black near the center under the same fixed bed angle. If both black
  and magenta become clean in XY only, test a center-hold implementation that
  uses one constant A angle for all center-held contours instead of selecting a
  new held angle per contour.
- Regenerate the black Ben1 layer before judging the edge overrun. Reject any
  compensated file that lacks `angular interpolation bed-frame`. If the new
  file still prints on the tape, record the stock diameter and increase Bed
  margin until the stock/tape boundary is outside the corrected edge envelope.
- Build a deterministic planner test with two adjacent center contours that
  starts from equal bed-space pitch, applies different held angles, and reports
  both bed-space and machine-space spacing. The acceptance target is the
  measured non-rigid compensation result on paper, not equal Euclidean spacing
  in raw machine coordinates.
- Photograph the completed magenta sheet from directly above, ideally with the
  four registration crosses enabled or with fixed sheet fiducials, so the
  striation pitch and direction can be measured.
- After installing the planned replacement bed/A motor, first repeat this same
  yellow and magenta layers at 700 mm/min. If clean, the 65 % workaround can be
  retired. If striation returns, run a controlled speed ladder at
  45 / 60 / 70 / 80 / 100 % and retain the highest fully clean setting per ink.
- The repeat must also confirm A direction, current, temperature, bed-ratio
  repeatability, and first-try M3 contact after the motor change.
