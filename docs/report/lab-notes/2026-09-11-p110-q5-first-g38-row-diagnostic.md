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

## Expected result

The first scan row is expected to be clear. P110 should make one preposition
move and one eastward G38.3 row, remain out of `Home`, and print `P110
complete: clear first G38.3 row passed`. It has no centroid, G54, or A action.

## Stop condition

If `Home` appears or the axes approach X/Y switches, press Reset and retain
the P110 messages/status. Do not run Q5 after that outcome.
