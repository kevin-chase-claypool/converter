# Lab Note: 2026-09-11 - P100 Q5 Automatic Centroid Survey Plan

## Objective

Run the first automatic center-magnet raster only within the measured 100 mm
square, then stop at the calculated TMAG centroid without changing G54 or A.

## Preconditions

- Q2 X/Y homing has passed immediately before Q5.
- Candidate G53 rectangle: X `-280..-180`, Y `-266..-166`.
- Candidate pitch/feed: 10 mm / 1000 mm/min.
- X/Y travel is clear and the operator watches the motion.

## Expected result

Q5 enters the P100 magnetic protocol, runs the chord-validating raster,
approaches the calculated G53 centroid, releases Aux0, and prints its Q5
completion message. The final MPos records the measured TMAG centroid. G54
and A must not change.

## Boundary

Q5 is source-enabled but unverified on hardware. It is not Q3 and does not
authorize center, pen-offset, or A-index registration.
