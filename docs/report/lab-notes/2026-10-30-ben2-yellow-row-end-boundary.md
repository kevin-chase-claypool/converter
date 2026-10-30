# Lab Note: 2026-10-30 - Ben2 yellow row-end boundary

## Objective

Determine whether the uneven-looking yellow rows marked by red dots in the
latest Ben2 print were caused by a G-code spacing error or by the image mask
ending selected rows.

## Input

- Program:
  `samples\gcode\Ben2\PXL_20201128_211515508-cmyk-yellow-compensated.gcode`.
- Program SHA-256:
  `9CC04AEC4B2312922623D3E909A4F9F8B50B6EC6EE3F77807E692DE0C6D6F5C5`.
- Manifest motion: XY only, fixed A.
- Manifest screen: `waves_even`, `1.92 mm` effective pitch.
- Operator photo: phone image supplied in the 2026-10-30 session, with red
  marks identifying the affected row ends.

## Procedure

1. Load the saved set manifest and reconstruct the yellow layer using its
   source, image controls, screen angle, pitch, scale, and compensation.
2. Plan the layer in XY-only mode.
3. Sample the planned paths at 19 columns across the image.
4. Sort the row intersections at each column and round each observed gap
   against the nominal `1.9155 mm` pitch.
5. Report any gap not within `0.01 mm` of a whole-pitch multiple.

## Results

- Every sampled column contains the nominal one-pitch gap and, where the image
  tone mask omits rows, exact integer-multiple gaps of two, three, four, or
  more pitches.
- No intermediate or compressed row-centre gap was found at any sampled
  column.
- The result is unchanged by the red-dot region's position: surviving row
  centre lines remain on the same equidistant lattice.

## Interpretation

The unequal-looking spacing beside the red dots is caused by complete rows
being omitted where the yellow image mask falls below its ink floor. The gap
between the next visible rows is then an integer multiple of the row pitch.
This is image content, not rows drifting toward one another.

The operator's red marks identify row endpoints. Those endpoints naturally
stagger as they follow the outline of the yellow separation.

## Decision and next action

- Do not alter the planner or recalibrate the bed for this observation.
- If every row in a filled region must be visible, use a continuous-tone fill
  style rather than a wave mask, or explicitly change the image threshold.
  Forcing missing rows to print would fill background areas that intentionally
  contain no yellow ink.

## Final machine-space correction

The original procedure reconstructed the compensated paper trajectory and
therefore measured the lattice before the compensation displacement reached
the final machine coordinates. That was the wrong acceptance plane for the
operator's printed-row symptom. The same programs were re-audited directly
from their emitted `X/Y` drawing commands at 199 columns in each effective
screen frame.

All four inks were checked, not only yellow. The previous raw-compensated
programs used profile `18bfb4ed1c33` unchanged. The new canonical programs keep
that profile through a row-locked projection. The full field is averaged
across the perpendicular coordinate at each along-row coordinate; the common
result is then applied to every parallel row.

| Ink | Raw compensated adjacent gap range | Row-locked min / median / max | Row-locked spread |
|---|---:|---:|---:|
| Cyan | `1.807922-2.048475 mm` | `1.914045 / 1.915527 / 1.916477 mm` | `0.002432 mm` |
| Magenta | `1.819102-2.050997 mm` | `1.914134 / 1.915541 / 1.916389 mm` | `0.002255 mm` |
| Yellow | `1.731065-2.054542 mm` | `1.915396 / 1.915465 / 1.915511 mm` | `0.000115 mm` |
| Black | `1.810685-2.035515 mm` | `1.914453 / 1.915525 / 1.915994 mm` | `0.001541 mm` |

The residual row-locked variation is below `0.005 mm`, set eight times tighter
than the smallest row-spacing concern and about 1/320 of the `0.8 mm` pen
width. It includes four-decimal G-code quantization and interpolation at the
audit columns. All four canonical files pass the tightened bound.

This correction supersedes both the earlier paper-space conclusion and the
temporary no-compensation workaround. Complete rows can still be omitted by
the image mask, while the raw displacement field also compressed and expanded
surviving rows in final machine space. The row-locked projection removes only
the incompatible row-normal component. It retains `50.9-65.5 %` of raw
correction energy depending on screen angle, so the active mesh measurably
moves all four layers. Unchecking the guard applies the raw field at the cost
of row pitch.

## Dark-region row invariant

The operator observed that the remaining apparent spacing loss in the final
print occurred in darker regions. A targeted generator regression now isolates
that condition. It compares full tone with 15 % tone at the same sine phase:

- Sampled common wave offset at full tone is `1.951 mm`.
- Sampled common wave offset at 15 % tone is `0.295 mm`.
- All 15 adjacent gaps remain exactly `4.000000 mm` at both tones.
- Every row's baseline remains fixed; all rows receive the same vertical wave
  displacement at a given X position.

Local wave depth therefore remains tone-driven without changing row ownership
or row-to-row pitch. The superseded print used the same shared-displacement
source layout but then passed through the non-uniform bed-compensation field.
Any spacing change between light and dark regions in that output came after the
Wave geometry, not from darker tone moving an individual row baseline. The
row-locked final transform preserves the same invariant.

## Physical status

The software and emitted-motion gates pass. A comparison print of these four
canonical row-locked files is still required before accepting the projected
correction physically.
