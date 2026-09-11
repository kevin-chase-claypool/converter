# Lab Note: 2026-09-11 - P110 Q5 First G38 Raster-Row Diagnostic

## Objective

Isolate Q5's first probe-motion command after P109 verified all pre-raster
operations without a `Home` transition.

## Preconditions

- A fresh `G65 P100 Q2` completed after the shaft-adapter adjustment.
- X/Y travel is clear through the measured scan row G53 X `-280..-180`, Y
  `-266`.
- The southwest corner is magnetically clear.

## Method

Run `G65 P110`. It reproduces Q5 preposition and readiness sequencing, then
performs just `G91 G38.3 X100 F1000` from the southwest corner. It returns to
absolute mode and releases Aux0 regardless of whether the probe triggers.

## Result

The first scan row was clear. P110 ran east from `MPos:-280.000,-266.000`
(southwest) to `MPos:-180.000,-266.000` (southeast), reported
`[PRB:-180.000,-266.000:0]`, and printed `P110 complete: clear first G38.3
row passed`. It never entered `Home`. It has no centroid, G54, or A action.

## Stop condition

No stop condition occurred. The remaining Q5 behavior is its repeated raster
loop and magnet-detecting rows.
