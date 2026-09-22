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

## Next action

Run E-09F clear (`a`, `c`) with the scale/paper fixture in place. Record `CLEAR_COMPLETE`, visible tip clearance, and whether the 100 ms candidate air-gap pulse reaches GP2 LIFT_HOME. Production M3/M5, GP27, and force-control gates remain disabled.

## References

- [E-09F test plan](../../testing/TEST_PLAN.md)
- [E-09F source](../../firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino)
- [E-09E installed-pen direction evidence](2026-09-22-e-09e-installed-pen-scale-direction.md)
