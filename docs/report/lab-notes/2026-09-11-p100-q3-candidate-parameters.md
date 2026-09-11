# Lab Note: 2026-09-11 - P100 Q3 Candidate Scan Parameters

## Objective

Record the operator's first-pass Q3 scan values without authorizing automatic
motion.

## Inputs

- Row pitch: 10.000 mm.
- Scan feed: 1000.000 mm/min.
- Pen location: 1.160992 in directly south of the TMAG.

The machine/G54 orientation from the jogged square establishes south as
negative Y. Therefore `pen - TMAG = (0.000, -29.4891968)` mm, stored in P100
as `(0.000, -29.4892)` mm.

## Result

The candidate values are in source and are covered by static validation. Q3 is
still unable to execute because both commissioning gates remain zero. The
historical temporary G54 manual-alignment value is not treated as superseded
commissioning evidence.

## Next action

Calculate and inspect the complete 11-row, 100 mm-per-row first-pass raster
plan and run a no-motion magnetic corner-baseline check before considering any
Q3 unlock.
