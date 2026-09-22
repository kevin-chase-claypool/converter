# Lab Note: 2026-09-22 - Integrated direction polarity fault

## Objective

Verify the first boot of the supervised integrated mechanical-preload build and
confirm that its lift direction matches the already validated E-09E direction.

## Configuration

- Firmware: `pro_micro_rp2350_toolhead` supervised bench build before the
  polarity correction.
- Supply: external toolhead rail; runtime command/telemetry through UART1.
- Gates: mechanical preload, actuator direction, and pressure calibration true;
  lift reference, normal clear, magnetic, and GP27 production gates false.

## Code, commands, and configuration used

```text
Firmware: firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino
UART: GP20/GP21, 115200 baud
Observed record:
pressure=FAULT cmd=M5 fault=GP2 lift-home not reached during retract
cs1238_raw=245772 cs1238_filtered=245974 cs1238_delta=41836 lift_home=0
commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Procedure

1. Boot the integrated test build with the pen clear and the GP2 switch
   released.
2. Observe the automatic bounded retract toward the GP2 maximum-UP limit.
3. Stop after the controller reports its bounded timeout fault.

## Results

The controller reached its 700 ms boot-retract timeout with `lift_home=0` and
entered `FAULT` with `GP2 lift-home not reached during retract`. No driver
fault was reported. This did not prove a mechanical failure: comparison with
the E-09E direction record showed the integrated `LIFT_USES_IN1_PWM` and
`SEEK_USES_IN1_PWM` selections were reversed.

## Difficulties and corrective actions

- Observed: the integrated build did not reach GP2 during its boot retract.
- Diagnosis: E-09E establishes IN1 HIGH/IN2 LOW as DOWN and IN1 LOW/IN2 HIGH
  as UP, while the integrated constants selected the opposite phases.
- Correction: set `LIFT_USES_IN1_PWM = false` and
  `SEEK_USES_IN1_PWM = true` in `toolhead_config.h`; recompile before retrying.

## Interpretation

The fault was a firmware phase-selection error, not evidence that GP2 failed.
The bounded timeout stopped the motor safely. The corrected build must be
flashed before any further integrated motion test.

## Decisions and next action

Do not clear or retry the old binary. Flash the corrected integrated sketch,
start with the pen clear and GP2 reachable, verify `lift_home=1`, then run a
single supervised `e`/`l` cycle.
