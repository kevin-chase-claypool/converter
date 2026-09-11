# Lab Note: 2026-09-11 - P107 Q5 Preposition Diagnostic

## Objective

Isolate Q5's first bounded XY move after an observation that the controller
appeared to make additional limit-switch approaches after Q5 was issued.

## Method

After a successful `G65 P100 Q2`, execute `G65 P107`. P107 commands `M5`, a
three-second dwell, and one `G53 G0 X-280 Y-266` move. It uses no `$H`, probe,
Aux0, A-axis, or coordinate-write command.

## Result

Starting from Q2's `MPos:-10.000,-436.000` X/Y-home position, P107 made one
continuous diagonal move to `MPos:-280.000,-266.000`. It remained in `Run`
then `Idle`; no `Home` status or X/Y limit approach occurred. Its start and
completion messages remained available in the controller console.

## Boundary

P107 does not validate the Q5 handshake, probe transitions, raster, centroid,
or registration. Its passed result isolates the remaining concern to a later
Q5 stage, beginning with the Aux0 readiness handshake.
