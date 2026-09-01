# ADR-004: Separate normal PEN_CLEAR from absolute LIFT_HOME

- Status: accepted for implementation; commissioning gated
- Date: 2026-09-01

## Context

The plotter produces many M3/M5 transitions. The pen must leave the paper
quickly before each pen-up travel move, but the GP2 microswitch is deliberately
located at a farther, repeatable full-retract `LIFT_HOME` position. Reaching it
on every M5 would add needless travel and switch cycles.

The load cell can distinguish pen contact from the no-contact condition, but a
no-contact reading alone does not uniquely describe actuator height. More than
one pen-clear position can produce the same no-contact force.

## Decision

- M3 requests `ENGAGE`: seek down until filtered force crosses
  `F_contact_on`, then run the bounded force-hold loop.
- Normal M5 requests `PEN_CLEAR`: retract until filtered force remains below
  the distinct lower `F_release_off` threshold for its debounce interval, then
  apply one bounded, calibrated clearance pulse and stop.
- `LIFT_HOME` is a separate full-retract action for boot, recovery, and service
  only. It uses the planned normally-open GP2 switch input; it is not a normal
  per-stroke M5 feedback signal.
- The mechanical backstop remains independent of GP2. The switch establishes a
  reference position; it is not a load-bearing stop.

No threshold, debounce duration, PWM, pulse duration, or clearance distance is
accepted as a firmware constant until the named commissioning tests establish
it.

## Consequences

- Fast plotting uses load-cell contact/release feedback without requiring a
  complete move to the distant switch on every stroke.
- Startup and recovery retain one absolute actuator reference, avoiding
  accumulated uncertainty after reset, fault, or manual disturbance.
- The toolhead state model is `BOOT -> LIFT_HOME -> PEN_CLEAR ->
  SEEK_CONTACT -> HOLD_FORCE`, with guarded fault transitions.
- T-01G verifies GP2 `LIFT_HOME`; T-01H verifies M5 release hysteresis,
  debounce, clearance pulse, pen-tip gap, and 30-cycle repeatability.
- Firmware stays commissioning-gated until those tests and load-cell force
  calibration succeed.
