# Lab Note: 2026-09-04 - E-06/T-01C N20 Stall and Preload Hold

## Objective

Verify that the aligned N20 can hold the selected spring preload while the
6 V actuator supply remains within a deliberately limited current envelope.

## Configuration

- Hardware: aligned N20 threaded gearmotor, DRV8833, pen carriage, spring, and
  heat-set insert.
- Supply: 6.0 V bench supply with current limit set to 0.20 A.
- Measurement: current read through the bench power supply.
- Spring/tool: selected spring preload; exact compression was not re-recorded
  in this session.
- Temperature/rail instrumentation: not used for this bounded test.

## Code, commands, and configuration used

```text
Owner-operated retract/stall test; firmware/build and command sequence were
not recorded.
```

## Procedure

1. Correct the lead-screw alignment against the heat-set insert.
2. Install the spring and command the N20 to the selected preload endpoint.
3. Observe the stalled motor for approximately 30 seconds while monitoring
   the bench-supply current.
4. Repeat the same guarded test ten times.

## Results

- Supply voltage: 6.0 V.
- Supply current limit: 0.20 A.
- Stall current measured at the supply: 0.18 A.
- Hold duration: approximately 30 seconds per repetition.
- Preload hold: successful.
- Repetitions: 10 successful tests.

## Difficulties and corrective actions

The earlier higher unloaded-motion current was traced to a lead screw that was
not nearly straight against the heat-set insert. The alignment was corrected
before this result was recorded.

## Interpretation

This passes E-06 for the tested, current-limited stall condition and provides
functional T-01C preload-hold evidence. The result shows that the N20 can
maintain the selected preload without reaching the 0.20 A bench limit in this
test. It does not characterize temperature, rail droop, driver-fault behavior,
or multi-hour endurance.

## Decisions and next action

Use the corrected 0.009 A aligned unloaded-motion value and the bounded 0.18 A
stall result as the current N20 electrical baselines. Keep the spring out of
solid height during normal operation. If a full production safety envelope is
required, add rail, temperature, and longer-duration measurements; otherwise
continue with T-01A/T-01B/T-01D/T-01E and the force-control commissioning gates.
