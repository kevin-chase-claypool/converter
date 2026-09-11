---
id: RPSW-20260911-004
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
tags:
  - P100
  - Q3
  - scan-feed
  - tool-offset
  - safety
related:
  - RPSW-20260911-003
---

# Record P100 Q3 Candidate Scan Parameters

## Summary

P100 records candidate Q3 scan parameters of 10 mm row pitch, 1000 mm/min
feed, and a `pen - TMAG` vector of `(0.000, -29.4892)` mm. Q3 remains locked.

## Reason

The operator supplied the intended first-pass pitch and feed and measured the
pen as 1.160992 in directly south of the TMAG. With the jogged coordinate
orientation, south is negative Y; 1.160992 in converts to 29.4891968 mm.

## Implementation

The source uses the rounded `-29.4892` mm Y component. The static validator
checks the exact candidate values and confirms that
`sensor_to_pen_offset_valid` remains zero. Therefore they configure a reviewable
plan but cannot release Q3.

## Verification

- Conversion: `1.160992 × 25.4 = 29.4891968` mm.
- `python tools\\validate_homing_macro.py`: pending after this source update.

## Struggles and rejected approaches

The historical temporary manual G54 offset was not silently overwritten as a
commissioned result. The new value is stored only as a candidate P100 constant
until a supervised raster validates registration.

## Risks and follow-up

The scan still has no measured magnetic chord width, corner-baseline evidence,
or supervised first-pass path. Q0/Q3/Q4 remain locked.

## Files

- `firmware/grblhal/macros/P100.macro`: candidate offset, pitch, and feed.
- `tools/validate_homing_macro.py`: candidate-parameter lock checks.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: commissioning status.
- `docs/report/lab-notes/2026-09-11-p100-q3-candidate-parameters.md`: source measurement record.
