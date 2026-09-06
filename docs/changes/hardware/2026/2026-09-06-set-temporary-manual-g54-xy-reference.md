---
id: HW-20260906-006
date: 2026-09-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB G54 work coordinate
  - center-bed magnet
  - TMAG sensing point and pen-axis centerline
tags:
  - g54
  - bed-center
  - tmag
  - pen-offset
  - commissioning
related:
  - M-07
  - M-08
  - M-09
  - HW-20260906-005
---

# Set temporary manual pen-corrected G54 XY reference

## Summary

After X/Y homing, the operator manually aligned the TMAG and then the pen axis
to the center magnet. The controller now has a temporary G54 X/Y zero at the
manually aligned pen axis; A was intentionally left unregistered.

## Reason

Pen-free checks need a known XY center while P100 magnetic raster, toolhead
handshake, and outer-magnet A-index commissioning remain unavailable.

## Implementation

The measured installed sensor-to-pen vector is `(0.000, -30.100)` mm, where
the vector is `pen - TMAG`. With the pen axis manually over the center magnet,
`G10 L20 P1 X0 Y0` replaced only the stale G54 X/Y offset. It did not write A.

## Verification

- TMAG-at-center: `MPos X=-232.900, Y=-283.300`.
- Pen-axis-at-center: `MPos X=-232.900, Y=-253.200`.
- The accepted G10 command produced matching G54 X/Y work zero and left A at
  its existing unregistered offset.

## Struggles and rejected approaches

Treating the center of the X/Y travel envelope as bed center was rejected. The
bed is not assumed centered in the gantry envelope; the physical center magnet
is the temporary reference and P100 will later measure it automatically.

## Risks and follow-up

This is not M-08 or M-09 completion and is not production authorization. Its
visual alignment uncertainty is unquantified, P100 must overwrite it, and no
A orientation reference exists. Use it only for guarded pen-free checks.

## Files

- `docs/report/lab-notes/2026-09-06-manual-temporary-g54-xy-reference.md`:
  raw alignment and controller evidence.
- `docs/integration/INTERFACES.md`: temporary-reference boundary.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: P100 supersession
  requirement.
