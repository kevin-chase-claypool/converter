# Bed compensation and simultaneous X/Y/A motion

**Date:** 2026-10-25

## Question

Can the host-side bed-compensation profile make the pen/toolhead stop tracking
simultaneously with the rotating bed during coordinated pen-down moves or
pen-up travel? Does grblHAL's `$701` rotary-feed option provide a missing
synchronization fix?

## Conclusion

No direct synchronization defect was found in bed compensation or `$701`.

grblHAL converts one `G1 X Y A F` line into one planner block. The step
generator then advances all axes from one shared step-event count, so X, Y, and
A reach that block's endpoint together. Compensation does not emit an
independent A command or a separate timing plan. It changes only machine X/Y
and may add X/Y/A endpoint samples. Therefore compensation cannot, by itself,
give the bed a different clock from the toolhead.

The compensation profile is spatial, not temporal. It corrects a measured
static X/Y error at each bed position; it has no sensor feedback and cannot
measure or correct mechanical lag while the axes are moving.

Compensation can still correlate with a physical tracking error:

- It changes the local direction and length of the X/Y/A machine-space vector.
- Extra subdivision creates more planner junctions and velocity-direction
  changes.
- The converter reuses one feed for each compensated subdivision rather than
  recalculating it for every emitted sub-block.
- At `$123=6000 motor deg/s^2`, those velocity changes can expose A-axis torque
  loss, belt compliance, backlash, or intermittent mechanical drag.

Those are indirect dynamic effects. They must be demonstrated on paper; source
inspection does not establish mechanical following loss.

The installed build is grblHAL `1.1f.20260908`, matching core commit
`c48fc078883747d8a60b7dc145273d1181cf781d`. It has `$376=1` (A designated
rotary) and `$701=0`. At `$701=0`, a G94 combined linear/rotary block uses
grblHAL's legacy mixed-unit vector interpretation. The converter currently
matches that interpretation. Turning `$701=1` would make G94 feed refer to the
linear axes and internally use inverse-time behavior; it would not make the
axes share a different clock. It would also invalidate the converter's current
feed calculation unless that calculation were changed with it.

## Primary-source evidence

### Installed controller configuration

- [`settings-2026-10-25.txt`](../../firmware/grblhal/config/settings-2026-10-25.txt)
  records `$376=1`, `$701=0`, `$113=30000`, and `$123=6000`.
- grblHAL `settings.c` maps the user value for `$376` by shifting it into the
  ABC axes mask:
  [set_rotary_axes](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/settings.c#L1364-L1375).
  Thus `$376=1` means the A axis, not X.
- The build number in the researched core source is `20260908`:
  [grbl.h](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/grbl.h#L39-L45).

### Mixed linear/rotary feed interpretation

- With `$701` enabled, grblHAL converts a mixed G94 block to inverse-time mode
  and computes its time from the linear-axis component:
  [planner.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/planner.c#L488-L519).
- With either `$701` setting, grblHAL next computes one unit vector and scales
  one block-wide nominal rate and acceleration by every commanded axis:
  [planner.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/planner.c#L523-L566).
- Per-axis maximum rate and acceleration constrain that one block-wide
  velocity profile:
  [planner.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/planner.c#L343-L381).

### Shared endpoint timing

- The stepper execution state is loaded with the planner block's single
  `step_event_count`:
  [stepper.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/stepper.c#L497-L552).
- Each axis Bresenham counter applies steps against that same count:
  [stepper.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/stepper.c#L603-L650).
  There is no separate A-step clock in a coordinated block.

### Look-ahead

- grblHAL recalculates buffered entry and exit speeds in reverse and forward
  passes:
  [planner.c](https://github.com/grblHAL/core/blob/c48fc078883747d8a60b7dc145273d1181cf781d/planner.c#L115-L186).
  Short compensated blocks are not individually forced to stop. They can carry
  speed across planner junctions when acceleration, direction change, and
  buffer content permit it.

### Converter behavior

- [`gcode.py`](../../software/converter_core/gcode.py) applies compensation
  only to machine X/Y, then emits one X/Y/A line for each subdivision. A is
  still the planned motor angle.
- Pen-up travel uses the compensated destination but is not subdivided by the
  compensation field. It remains one fed X/Y/A block, so this can change the
  travel vector and junction while preserving the common endpoint clock.
- [`kinematics.py`](../../software/converter_core/kinematics.py) computes a
  feed duration from compensated X/Y length and A motor-degree delta. It keeps
  two independent constraints: the X/Y feed and the requested tangential bed
  speed. The longer component duration determines the feed.
- [`bed_compensation.py`](../../software/converter_core/bed_compensation.py)
  maps `machine = R(theta) * bed_point + correction(theta, bed_point)` and
  subdivides when the correction varies enough to exceed path tolerance.

For the installed `$701=0` behavior, the converter's one-feed-per-source-segment
calculation is internally consistent at the source endpoints. Reusing that
feed across compensation subdivisions can change the local velocity ratios,
but it does not make one axis finish a controller block late.

## Ranked hypotheses for the remaining tracking symptom

1. **Residual A-axis mechanics or torque loss under combined motion.** If this
   is the cause, rotating uncompensated and compensated traces will both show
   errors, while the parked-A control stays clean. The drag-chain-pillar repair
   makes this less likely for Y but does not clear the A drivetrain.
2. **Planner dynamics caused by many compensation-induced direction changes.**
   If this is the cause, only compensated cases will show separation at the
   production feed, and a lower feed will reduce it.
3. **Converter feed choice around compensation subdivisions.** If this is the
   cause, compensated and uncompensated production files will diverge even
   though every block is coordinated; changing compensation subdivisions
   should change the result.
4. **Belt compliance, backlash, or A-direction reversals.** Errors should
   depend on direction and reversals, not compensation alone.
5. **Toolhead/carriage drag or an XY mechanics defect.** The parked-A control
   would also be imperfect, or the initial/return witness crosses would fail
   after travel.

## Discriminating physical test

[`bed-compensation-motion-test.gcode`](../../samples/gcode/bed-compensation-motion-test.gcode)
contains five cases in one pause-free file:

| Case | Bed motion | Compensation | Requested feed |
|---|---|---|---|
| 1 | A parked at 0 | off | 700 mm/min |
| 2 | rotates -14.5 through +14.5 and back | off | 700 mm/min |
| 3 | same rotation schedule | on | 700 mm/min |
| 4 | same rotation schedule | off | 350 mm/min |
| 5 | same rotation schedule | on | 350 mm/min |

Every case has the same bed-space sine path and A schedule. It starts with an
A0 witness cross, performs a simultaneous rotating pen-up move, draws the path
forward and immediately back over itself, returns with another simultaneous
rotating pen-up move to A0, and draws the same witness cross again.

Interpretation:

- Case 1 clean confirms the repaired Y drag-chain path and basic XY motion.
- Cases 2 and 3 both doubled or distorted means residual A mechanics,
  compliance, or torque loss is more likely than compensation.
- Only case 3/5 distorted means compensation-induced planner dynamics or feed
  selection remains in scope.
- Fast cases fail while slow cases pass means dynamics or torque margin, not
  static compensation geometry.
- Initial and return crosses separate means position was lost during a
  rotating pen-up move.
- Forward and reverse traces separate while witnesses still coincide means
  transient following error recovered by the end of the move.

## Limitations

- The exact grblHAL source build is identified by its build date and matching
  core version, but the builder configuration archive does not contain a
  source commit field.
- Source inspection proves the commanded timing model, not whether steppers
  physically lose steps or belts mechanically lag.
- The profile changes the physical X/Y command by at most `1.3305 mm`, so the
  test is designed to detect pattern changes, not to infer a large static
  positional shift.
- No compensated-versus-uncompensated physical result existed when this note
  was written.
