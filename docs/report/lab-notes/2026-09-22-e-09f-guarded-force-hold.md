# Lab Note: 2026-09-22 - E-09F guarded force hold

## Objective

Exercise the E-09C precision-weight CS1238 profile through E-09F's bounded automatic installed-pen test without enabling production M3/M5 control.

## Configuration

- Sketch/commit: `e09f_cs1238_guarded_force_hold.ino`, `a02dc59 Add guarded E09F force hold test`.
- SparkFun Pro Micro RP2350, external toolhead rail, CS1238 channel A/gain 128/640 SPS.
- Existing 3.3 V GP20/GP21 USB-to-TTL service UART, Arduino IDE Serial Monitor at 115200 baud, adapter VCC disconnected.
- Installed pen over a kitchen scale. E-09C precision weights remain the force authority; the scale is a range/behavior check only.

## Procedure and result

With the pen clear, the operator issued `t`, `a`, and `s` twice. E-09F used 5 ms corrections separated by 500 ms, entered the 40–60 g raw band, and held for five seconds with the driver asleep between pulses.

The first run reached and held **40.0 g**; the second reached and held **40.4 g**. Both are inside the requested practical 40–60 g band and repeatable to the available kitchen-scale resolution. E-09F intentionally stops correction as soon as it enters the band, so arriving near 40 g rather than the nominal 50 g center is expected. This is a band-hold pass, not a centered 50 g production-force result.

## Clear result and next action

The operator then ran E-09F clear (`a`, `c`). The pen cleared the scale/paper,
stayed nowhere near the GP2 LIFT_HOME switch, and measured approximately
**1.75 mm** above the scale after the staged 100 ms air-gap pulse. The exact
terminal serial line was not retained, so `CLEAR_COMPLETE` is not asserted as
captured evidence; the reported physical outcome is a one-cycle air-gap pass.

The next action is repeated-clear testing. Production M3/M5, GP27, and
force-control gates remain disabled until normal M5 behavior is exercised
repeatedly rather than through this temporary E-09F sketch.

## Delayed air-gap confirmation correction

After a fresh-tare/arm, the latest E-09F run reached `HOLD_COMPLETE` and then
entered clear. Three 5 ms UP pulses reduced the mean to `tare_delta=-2728`,
which is inside the 3 g release band. The subsequent 100 ms UP pulse visibly
cleared the pen by approximately 1.75 mm from paper without approaching GP2
LIFT_HOME. The sketch immediately read `tare_delta=-25545` in the same
millisecond as motor stop and reported `FAULT,reason=air_gap_not_clear`.

That result does not show failed clearance: release had already been proven
before the known-duration gap pulse, and the physical gap was observed. The
immediate post-drive CS1238 reading is a motor/mechanical settling transient,
not a valid test of an already-completed gap. E-09F now waits 500 ms, emits an
`AIR_GAP_SETTLED` telemetry record, then prints `CLEAR_COMPLETE`; that delayed
value is recorded but does not retroactively fault the completed air-gap
motion. Repeat the cycle with the updated sketch and retain the complete
terminal trace.

## Failed clear attempt and correction

On a later `a`, `c` attempt, the serial stream reported:

```text
CLEAR_START,release_raw_delta=15116,air_gap_ms=100
READING,raw=-666510,tare_delta=967934,tare_valid=1
FAULT,reason=hard_force_limit
```

This was a firmware-state error: E-09F applied the downward contact-force hard
limit during an UP/release state before commanding an UP pulse. The preceding
hold had completed safely and the driver was asleep. The release code now
bypasses that downward-only limit; seek/hold retains it with an immediate second
CS1238 confirmation. The same fault also showed a recovery usability gap: the
pre-fix sketch had no manual retract command while the pen remained on the
fixture. E-09F now provides `u`, one guarded 5 ms UP pulse that works after a
fault and sleeps the driver. Reflash, use `u` only until clear, fresh-tare, and
then repeat the automatic test.

## References

- [E-09F test plan](../../testing/TEST_PLAN.md)
- [E-09F source](../../../firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino)
- [E-09E installed-pen direction evidence](2026-09-22-e-09e-installed-pen-scale-direction.md)
