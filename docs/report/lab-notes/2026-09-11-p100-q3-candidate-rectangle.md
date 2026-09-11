# Lab Note: 2026-09-11 - P100 Q3 Candidate G53 Rectangle

## Objective

Capture a safe machine-coordinate rectangle around the center magnet without
running automatic raster motion.

## Measurements

The TMAG sensor was jogged to four G54 DRO corners:

| Corner | X | Y |
|---|---:|---:|
| NW | -47.100 | 25.200 |
| NE | 52.900 | 25.200 |
| SE | 52.900 | -74.800 |
| SW | -47.100 | -74.800 |

Readback confirmed `G54:-232.900,-191.200,0.000,0.000`. Therefore the
machine-coordinate conversion `MPos = WPos + WCO` gives X `-280.000` to
`-180.000` and Y `-266.000` to `-166.000`.

## Result

The candidate area is 100 × 100 mm and remains at least 166 mm from every
configured machine envelope end. It is recorded in P100 but is not executable:
Q3 remains locked and `row_pitch` remains zero.

## Next action

Prepare an inspectable, non-motion first-pass raster plan using these bounds.
Choose row pitch and feed only after estimating duration and confirming the
magnetic footprint can yield at least the required number of hit rows.
