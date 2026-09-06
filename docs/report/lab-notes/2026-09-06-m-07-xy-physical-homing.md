# M-07 X/Y physical homing - 2026-09-06

## Objective

Commission the installed X-east and Y-south normally-closed limit switches as
repeatable physical machine-home references, without homing the unwired Z axis
or continuous A axis.

## Configuration

- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- Home corner: southeast: X homes toward East (`+X`) and Y homes toward South
  (`-Y`).
- Switches: X and Y are normally closed; released switches report inactive
  with `$5=0`.
- Homing settings: `$20=0`, `$21=0`, `$22=3` (enabled plus single-axis
  commands), `$23=2` (Y only inverted), `$24=50` mm/min, `$25=500` mm/min,
  `$26=250` ms, `$27=10.000` mm, `$43=1`, `$44=3` (XY first phase), and
  `$45=$46=$47=0` (no later homing phases).
- Z and A were excluded from the homing cycle. A remains continuous and is not
  a conventional switch-homed axis.

## Procedure

1. Positioned the X carriage west of the east-side switch and ran `$HX`.
2. Positioned the Y gantry north of the south-side switch and ran `$HY`.
3. Jogged both axes clear of the southeast corner and ran `$H`.
4. Repeated the combined `$H` cycle twice after jogging clear of both switches.

## Results

- X single-axis homing successfully approached east, triggered, pulled off,
  performed the slower locate pass, and finished clear of the switch.
- Y single-axis homing successfully approached south and completed the same
  cycle.
- The initial combined `$H` run succeeded. Two subsequent logged combined
  runs ended at the identical machine position:

```text
<Idle|MPos:-10.000,-498.000,0.000,0.000|...|Pn:ZA|H:1,3>
```

- `H:1,3` confirms X and Y were marked homed. No homing alarm was reported.
- `$27=10.000` mm is intentional: it provides clearance so a nearby wire cannot
  catch on a home switch. It is the value used by the successful combined runs.
- The controller displayed a pre-existing `G54` work-coordinate offset
  (`WCO:58.681,50.000,0.000,720.000`). Physical homing did not change it.

## Struggles and limitations

- The prior phase assignment attempted Z, then A, before X/Y. It was replaced
  with a single XY-only phase before homing was enabled.
- An MDI `?` status query did not visibly return in the console; ordinary
  controller status reporting during `$H` supplied the required final evidence.
- This is not a hard-limit or soft-limit test. Both remain disabled, and the
  `Pn:ZA` state remains outside this X/Y homing scope.
- This does not establish bed-center or A-index G54 coordinates. P100 magnetic
  registration remains commissioning-gated.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-07
- [`HOMING_AND_MAGNETIC_CALIBRATION.md`](../../../firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md)
