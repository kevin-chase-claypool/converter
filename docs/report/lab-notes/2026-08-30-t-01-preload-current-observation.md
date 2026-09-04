# Lab Note: 2026-08-30 - T-01 Preliminary Preload Current Observation

## Objective

Record the initial current observed while the installed N20 retracted against
the newly fitted spring.

## Configuration

- Hardware: installed N20 threaded gearmotor, DRV8833, toolhead carriage, and
  compression spring.
- Spring: owner-measured free length 1.19 in; nominal wire diameter 0.027 in
  and outside diameter 0.295 in.
- Power: toolhead local supply; voltage, supply current limit, and regulator
  configuration were not recorded.
- Instrument: current-measurement instrument and its bandwidth were not
  recorded.
- Firmware/build and command method: not recorded.

## Code, commands, and configuration used

```text
Not recorded for this preliminary owner observation.
```

## Procedure

1. Installed the spring in the toolhead mechanism.
2. Ran a retract motion while observing current.
3. Observed current through retraction and at the reported fully compressed
   end condition.

## Results

- Reported retract current: approximately 0.019-0.050 A.
- Owner clarification received 2026-09-04: the approximately 0.18 A endpoint
  reading is the N20 stall current, and the motor holds the selected spring
  preload.
- Interpretation: current increased as the motor opposed the greatest observed
  spring load. The result provides useful actuator-capability evidence, but it
  does not by itself establish the formal E-06 electrical/thermal margin or a
  T-01C hold pass because the test setup, dwell, force, rail behavior, and
  temperatures were not recorded.

## Difficulties and corrective actions

The spring compression, force, supply limit, meter response, temperature, and
command settings were not captured. Treat this as preliminary actuator
evidence, not a passed E-06 or T-01 result. The next test must use a guarded
non-solid working end point, a current-limited supply, and documented
measurements.

## Decisions and next action

Do not use the fully compressed end condition as normal operation. Complete
T-01A, then repeat the measurement at the intended maximum working compression
with the current limit, voltage, force/position, peak current, hold dwell, and
temperature recorded. The reported preload hold should be formalized as T-01C
evidence before it is used as a controller assumption. The later-corrected
0.009 A value applies to aligned **unloaded** motor motion; it does not replace
this spring-installed preload observation.
