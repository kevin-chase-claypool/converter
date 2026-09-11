# Lab Note: 2026-09-11 - P100 Q5 Automatic Centroid Survey Plan

## Objective

Run the first automatic center-magnet raster only within the measured 100 mm
square, then stop at the calculated TMAG centroid without changing G54 or A.

## Preconditions

- P111 X/Y homing has passed immediately before Q5.
- Candidate G53 rectangle: X `-280..-180`, Y `-266..-166`.
- Candidate pitch/feed: 10 mm / 1000 mm/min.
- X/Y travel is clear and the operator watches the motion.

## Result

Q5 entered the P100 magnetic protocol, ran the chord-validating raster,
approached the calculated G53 centroid, released Aux0, and printed its Q5
completion message. After the queued approach fully completed, final position
was `MPos:-232.325,-217.950,0.000,0.000`. A magnet placed under that final
TMAG position appeared visually centered.

The original SD P100 also executed three unintended `$H` cycles during Q5,
before the raster. `$H` is a grblHAL system command and was processed despite
the false O-word branches surrounding its three literal instances. The full
raster and centroid result are still valid, but this P100 revision must not be
reused; P111 now owns the one intentional physical X/Y home. G54 and A
remained unchanged.

P111 was then installed and successfully performed exactly one X/Y home.
The first corrected-P100 execution stopped before motion with `error:71`:
the new explanatory parenthesized comment had been split across two physical
lines. That has been corrected to one line and is now rejected by static
validation if reintroduced.

The corrected P100 Q5 then completed without any `Home` state after the Q5
command. Its final position was `MPos:-232.013,-218.775,0.000,0.000`; a
magnet placed under the TMAG at that endpoint was visually centered.

## Boundary

Q5 is hardware-verified as a center-magnet survey. It is not Q3 and does not
authorize center, pen-offset, or A-index registration.
