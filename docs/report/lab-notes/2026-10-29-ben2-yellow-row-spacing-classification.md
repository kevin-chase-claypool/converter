# Lab Note: 2026-10-29 - Ben2 CMYK row-spacing classification

## Objective

Determine whether the unequal yellow row gaps visible during the Ben2 print
were already present in the saved commands or were introduced by bed rotation
and machine calibration, then verify the corrected spacing in all four ink
programs.

## Configuration

- Source image:
  `PXL_20201128_211515508.jpg`, SHA-256
  `DDD4D5BA8FFB54BF5063039B15659A05D01628E7F82977B1F2D4DD7EF27068B2`.
- Original yellow program:
  `samples\gcode\Ben2\PXL_20201128_211515508-cmyk-yellow.gcode`, SHA-256
  `DA4826610832ED83EB774A721F6B9A8B08812C83E04E182F650E61A2F403F894`.
- Screen recipe: `waves_zero`, `0.8 mm` source pitch, `240 %` artwork
  scale, `1.92 mm` effective pitch, seed `8`, `200 x 200 mm` page, `0.8 mm`
  pen, `F700`, and centered `60 mm` hold diameter.
- Compensation profile: `18bfb4ed1c33`, measured radius `165.100 mm`.
- Corrected programs:
  `samples\gcode\Ben2\PXL_20201128_211515508-cmyk-{cyan,magenta,yellow,black}-equidistant.gcode`.
  Their SHA-256 values are recorded in
  `PXL_20201128_211515508-cmyk-equidistant-set.json`.

## Procedure

1. Parse each pen-down move into its contour order.
2. Convert each commanded machine point back through the saved A motor angle
   using the `12.03324` drive ratio.
3. Invert the active bed-compensation profile with local iteration and verify
   the recovered point against the forward rotation-plus-correction mapping.
4. Interpolate every contour at common paper X columns and measure the nearest
   adjacent centreline gaps.
5. Compare the original `waves_zero` program with an otherwise identical
   `waves_even` regeneration.
6. Repeat the paper-screen audit across all four ink angles. The SVG import
   flips Y, so the effective screen angles are `-15`, `-75`, `0`, and `-45`
   degrees rather than the unflipped source values.

## Results

The first yellow comparison:

| Program | Adjacent-gap minimum | Median | Maximum |
|---|---:|---:|---:|
| Original `waves_zero` | `1.791184 mm` | `1.915371 mm` | `2.048935 mm` |
| Corrected `waves_even` | `1.899351 mm` | `1.915456 mm` | `1.931536 mm` |

The corrected file's off-centre sampled columns varied by at most `0.000216
mm`. Small excursions near the bed-centre hold are the only wider values in
the aggregate range.

All four corrected layers decode to an integer row lattice:

| Ink | Effective angle | Fitted base pitch | Maximum plane residual |
|---|---:|---:|---:|
| Cyan | `-15 deg` | `1.915506 mm` | `0.001125 mm` |
| Magenta | `-75 deg` | `1.915488 mm` | `0.001121 mm` |
| Yellow | `0 deg` | `1.915457 mm` | `0.000000 mm` |
| Black | `-45 deg` | `1.915490 mm` | `0.000933 mm` |

Tone-masked missing rows create exact integer multiples of one base pitch;
they do not create a smaller or intermediate gap.

The operator's accompanying paper photo visibly marked two close approaches
between wave rows. No archived photo path is available for this chat-supplied
image, so it is retained as operator observation rather than a measurement
artifact.

## Interpretation

For this print, the unequal gaps were already encoded in the paper-space
trajectory before the controller received the program. The A rotation and
compensation preserve the bed-frame path, but they cannot make
variable-amplitude rows equidistant. Bed-mesh refinement addresses residual
position error, not this spacing defect.

The result does not exclude a separate mechanical following error after the
equidistant program is printed. That question can only be evaluated from the
corrected print.

## XY-only follow-up

The operator then reported the same visual unevenness with bed motion set to
XY only. The newest standard Ben2 set was saved at `19:36:11`, four minutes
after the converter enforcement commit, but its manifest still contained the
pre-fix `waves_zero` style and the old style label. The running GUI therefore
had not loaded the new converter code.

Inverse-decoding the saved XY-only yellow program produced a median gap of
`1.915439 mm`, but individual gaps ranged from `1.885051` to `1.944691 mm` and
hundreds of gaps did not belong to one row lattice. The bed remained fixed
throughout, proving the bad geometry was again the saved screen style rather
than A-axis motion.

The standard four Ben2 programs were replaced with new XY-only `waves_even`
outputs. Their manifest records `bed_motion: XY only`, `style: waves_even`, and
`wave_phase_mode: identical_translated_rows`. The four strict motion checks
report zero A motion.

## Decision and next action

- Stop the known-unequal `waves_zero` print and use the generated four-file
  `waves_even` set.
- Normal converter output now exposes only **Wave screen - equidistant rows**;
  legacy variable-spacing style values are promoted unless a diagnostic tool
  explicitly opts into the old behavior.
- Compare the corrected print against the decoded `1.91546 mm` nominal pitch
  before reopening the planner or compensation investigation.

## Verification

- The source image hash matches the saved set manifest.
- `python tools\check_macros.py` passes on all four corrected files.
- `python tools\check_gcode_motion.py --strict` passes on all four. The largest
  observed drawing-bed step is `6.08 deg`, the largest A rate is
  `270 motor deg/s`, and the worst bounded path bow is `0.130 mm`.
- All `575` converter tests pass with one expected OpenGL-context skip.
