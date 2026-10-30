# Lab Note: 2026-10-30 - Ben2 yellow row-end boundary

## Objective

Determine whether the uneven-looking yellow rows marked by red dots in the
latest Ben2 print were caused by a G-code spacing error or by the image mask
ending selected rows.

## Input

- Program:
  `samples\gcode\Ben2\PXL_20201128_211515508-cmyk-yellow.gcode`.
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
