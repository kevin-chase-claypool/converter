# Lab Note: 2026-09-11 - Direct X/Y Homing Before P100 Q2 Enablement

## Objective

Establish whether the installed X/Y home inputs, motor branches, and configured
homing direction are safe enough to expose P100 Q2 as a limited macro stage.

## Setup

- X and Y TB6600 fuses installed.
- Z is unused; Z/A are excluded from the homing cycle.
- Both X and Y switches began released, more than 50 mm from the toolhead.
- Hard-limit input checks showed each respective X/Y signal only while its
  individual switch was pressed.
- Homing rates were temporarily reduced to `$25=300` and `$24=100` for the
  observed test.

## Verification

`$H` entered `Home`, completed without an alarm, and returned to `Idle`.
During the cycle the controller reported `H:1,3`; final machine position was
`MPos:-10.000,-436.000,0.000,0.000`. The 10 mm X pull-off and Y endpoint are
consistent with the installed homing configuration and `$23=2`.

## Result

The direct controller X/Y `$H` operation is proven for this installed setup.
The SD-resident macro then passed `G65 P100 Q2`: it entered `Home`, reported
`H:1,3`, returned `Idle` at `MPos:-10.000,-436.000,0.000,0.000`, and printed
`P100 Q2 X/Y homing complete` followed by `ok`. Q2 is therefore verified as
`M5`, a three-second settle, `$H`, and an immediate return. This evidence does
not authorize Q0, Q3, Q4, raster motion, G54 registration, or A motion.

## Next action

Define and validate the bounded machine-coordinate rectangle required for Q3.
Restore the normal homing-rate settings only after deciding whether another
observed homing test is needed.
