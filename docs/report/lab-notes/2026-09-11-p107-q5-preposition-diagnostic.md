# Lab Note: 2026-09-11 - P107 Q5 Preposition Diagnostic

## Objective

Isolate Q5's first bounded XY move after an observation that the controller
appeared to make additional limit-switch approaches after Q5 was issued.

## Method

After a successful `G65 P100 Q2`, execute `G65 P107`. P107 commands `M5`, a
three-second dwell, and one `G53 G0 X-280 Y-266` move. It uses no `$H`, probe,
Aux0, A-axis, or coordinate-write command.

## Expected result

Starting from the Q2 X/Y-home position, the toolhead makes one bounded move to
the southwest corner of the known Q5 rectangle. It must not enter `Home` and
must not approach or open the X/Y home switches. It prints one start message
and one completion message, which remain visible even if the controller's
rolling status buffer overwrites older telemetry.

## Boundary

P107 does not validate the Q5 handshake, probe transitions, raster, centroid,
or registration. A P107 result is needed before any further Q5 execution after
the reported unexpected limit behavior.
