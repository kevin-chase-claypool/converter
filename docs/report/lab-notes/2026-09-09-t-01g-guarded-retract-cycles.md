# Lab Note: 2026-09-09 - T-01G guarded LIFT_HOME retract cycles

## Objective

Verify that the installed active-low GP2 `LIFT_HOME` input changes only when
the moving carriage flag reaches the fixed microswitch during bounded powered
retract/release motions.

## Configuration

- Hardware: installed N20/DRV8833, current preload spring, carriage flag, and
  normally-open LIFT_HOME microswitch from GP2 to local TOOL_GND.
- Supply: 6.0 V bench supply, current limit 0.20 A.
- Telemetry: 3.3 V USB-to-TTL adapter on GP20/GP21, COM8, 115200 baud; USB-C
  unplugged after firmware upload.
- Firmware: `e07b_hx711_actuator_steps`, commit `971e557`.
- Actuator commands: bounded 20 ms pulses; the driver sleeps after each pulse.

## Code, commands, and configuration used

```text
commit 971e557 toolhead: report lift switch in bounded test
firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino
6.0 V bench supply; current limit 0.20 A
COM8, 115200 baud; d=one down/release pulse; u=one up/retract pulse;
h=read GP2 without motor movement
```

## Procedure

1. Confirmed `h` reported `lift_home=0` released, `1` manually pressed, then
   `0` released.
2. Confirmed bounded `u` physically raises/retracts and `d` lowers the carriage.
3. From the switch-pressed position, pulsed `d` until the first `0`, then
   pulsed `u` until the first `1`; stopped without an extra pulse.
4. Repeated for ten total cycles and took three stationary pressed-state reads.

## Results

| Observation | Result |
|---|---|
| GP2 polarity | `0` released; `1` only with carriage flag visibly pressing the switch |
| Cycle count | 10 guarded release/retract cycles |
| Release result | First `lift_home=0` after 6 down pulses in every cycle |
| Retract result | First `lift_home=1` after 9 up/retract pulses in every cycle |
| Pressed-state stability | Three stationary reads: `1`, `1`, `1` |
| Driver state | Reported stopped/asleep after every pulse |

No spring-seat position, force, temperature, or rail-ripple measurement was
taken.

## Difficulties and corrective actions

`bench_motor_command` produced no COM8 output because it uses native USB
`Serial`; COM8 is the GP20/GP21 UART1 adapter. The bounded E-07B sketch was
updated to report GP2 after each pulse and on `h`, retaining its self-sleeping
motor behavior.

## Interpretation

The installed switch, GP2 polarity, carriage flag, and bounded actuator motion
are repeatable in this limited test. It is not authorization for automatic
LIFT_HOME: spring position, backstop margin, and missing-trigger fault behavior
are still unmeasured.

## Decisions and next action

Keep GP2 telemetry-only. Measure `L_lift`, `L_contact`, selected `L_min`,
free-spring solid height, and the LIFT-to-backstop margin before choosing an
automated retract boundary.
