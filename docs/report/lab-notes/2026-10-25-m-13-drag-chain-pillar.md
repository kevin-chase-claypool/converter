# M-13 drag-chain pillar and striation result

**Date:** 2026-10-25

## Scope

Operator-reported mechanical change and visual result on the rotating-bed
plotter. This note does not measure the new part or photograph the old and new
pillar side by side.

## Reported symptom

The Y-axis drag chain had to climb a stepped transition onto the northeast
pillar where the rails attach. The operator identified this as a source of
travel friction. It was consistent with the earlier feed-dependent striations
and the fact that slowing the machine reduced but did not universally remove
them.

## Change

The stepped northeast pillar was replaced with a straight version. The drag
chain now follows the 3030 extrusion without a stairstep for the full Y-axis
print distance.

## Result

The operator reports that the XY-only version of the same print is now
flawless after the mechanical change. The rotating-bed case still needs a
controlled test for simultaneous X/Y/A tracking.

This is strong evidence that the striation mechanism was substantially
mechanical and that drag-chain friction was a leading cause. It is not by
itself a pass of the rotating-bed task because the successful observation was
XY-only.

## Verification status

- Change executed: yes, operator reported.
- XY-only visual result: clean, operator reported.
- Rotating-bed visual result after the change: pending.
- Part dimensions/material/model: not recorded.
- Before/after force or current measurement: none.
- Formal test ID: M-13.

## Follow-up

Run the one-sheet
[`bed-compensation-motion-test.gcode`](../../../samples/gcode/bed-compensation-motion-test.gcode)
to separate residual A-axis mechanics from compensation-induced motion
dynamics. Keep the bed compensation active for the compensated cases and keep
`$123=6000`, `$701=0` for the baseline comparison.
