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
- Reported current at the fully compressed end condition: approximately 0.18 A.
- Interpretation: current increased as the motor opposed the greatest observed
  spring load, but the observation does not establish a safe continuous hold,
  stall current, peak current, spring rate, force, or a coil-bind margin.

## Difficulties and corrective actions

The spring compression, force, supply limit, meter response, temperature, and
command settings were not captured. Treat this as a preliminary observation,
not a passed E-06 or T-01 result. The next test must use a guarded non-solid
working end point, a current-limited supply, and documented measurements.

## Decisions and next action

Do not use the fully compressed end condition as normal operation. Complete
T-01A, then repeat the measurement at the intended maximum working compression
with the current limit, voltage, force/position, peak current, and temperature
recorded.
