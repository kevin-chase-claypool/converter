# Lab Note: 2026-09-04 - E-06 N20 Endpoint Stall Current

## Objective

Record the N20 current when it retracts to the travel endpoint and presses the
LIFT_HOME switch under a deliberately limited 6 V supply.

## Configuration

- Hardware: aligned N20 threaded gearmotor, DRV8833, pen carriage, spring, and
  heat-set insert.
- Supply: 6.0 V bench supply with current limit set to 0.20 A.
- Measurement: current read through the bench power supply.
- Spring/tool: a spring was installed, but its identity and compression at the
  endpoint were not recorded.
- Temperature/rail instrumentation: not used for this bounded test.

## Code, commands, and configuration used

```text
Owner-operated retract/stall test; firmware/build and command sequence were
not recorded.
```

## Procedure

1. Correct the lead-screw alignment against the heat-set insert.
2. Install the spring and command the N20 to retract until it cannot travel
   farther and presses the LIFT_HOME switch.
3. Observe the switch-pressed endpoint for approximately 30 seconds while
   monitoring the bench-supply current.
4. Repeat the same endpoint test ten times.

## Results

- Supply voltage: 6.0 V.
- Supply current limit: 0.20 A.
- Endpoint stall current measured at the supply: 0.18 A.
- Endpoint hold duration: approximately 30 seconds per repetition.
- LIFT_HOME switch: pressed at the non-moving endpoint.
- Operating-preload hold: not measured.
- Repetitions: 10 successful tests.

## Difficulties and corrective actions

The earlier higher unloaded-motion current was traced to a lead screw that was
not nearly straight against the heat-set insert. The alignment was corrected
before this result was recorded.

## Interpretation

This passes only the bounded E-06 endpoint-stall observation for the tested
configuration. It does not provide T-01C preload-hold evidence: the 0.18 A
reading was taken while the motor was pressing the LIFT_HOME switch at the end
of travel, not while holding a known operating compression. It also does not
characterize temperature, rail droop, driver-fault behavior, or multi-hour
endurance.

## Decisions and next action

Use the corrected 0.009 A aligned unloaded-motion value as the unloaded N20
baseline and retain 0.18 A only as a bounded switch-pressed endpoint-stall
observation. Keep the spring out of solid height and do not use the switch-
pressed stall as a normal operating point. Repeat a guarded current/hold test
at a known safe compression before claiming T-01C preload capability; then
continue with T-01A/T-01B/T-01D/T-01E and the force-control commissioning
gates.
