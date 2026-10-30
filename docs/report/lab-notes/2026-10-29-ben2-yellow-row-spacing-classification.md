# Lab Note: 2026-10-29 - Ben2 yellow row-spacing classification

## Objective

Determine whether the unequal yellow row gaps visible during the Ben2 print
were already present in the saved commands or were introduced by bed rotation
and machine calibration.

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
- Corrected program:
  `samples\gcode\Ben2\PXL_20201128_211515508-cmyk-yellow-equidistant.gcode`,
  SHA-256
  `4BDE0728D6273F73CBA10159B210C8FE810202CFC2B3F4333B0B6E63EBCCCABD`.

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

## Results

| Program | Adjacent-gap minimum | Median | Maximum |
|---|---:|---:|---:|
| Original `waves_zero` | `1.791184 mm` | `1.915371 mm` | `2.048935 mm` |
| Corrected `waves_even` | `1.899351 mm` | `1.915456 mm` | `1.931536 mm` |

The corrected file's off-centre sampled columns varied by at most `0.000216
mm`. Small excursions near the bed-centre hold are the only wider values in
the aggregate range.

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

## Decision and next action

- Stop the known-unequal `waves_zero` print and use the generated
  `waves_even` file for the next yellow check.
- Select **Wave screen - equidistant rows** whenever constant row pitch is a
  hard requirement.
- Compare the corrected print against the decoded `1.91546 mm` nominal pitch
  before reopening the planner or compensation investigation.

## Verification

- The source image hash matches the saved set manifest.
- `python tools\check_macros.py` passes on the corrected file.
- `python tools\check_gcode_motion.py --strict` passes with a largest bed step
  of `5.74 deg`, A rate `270 motor deg/s`, and worst bounded path bow
  `0.110 mm`.
- All `575` converter tests pass with one expected OpenGL-context skip.
