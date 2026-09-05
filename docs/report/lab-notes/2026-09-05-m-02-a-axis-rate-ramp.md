# M-02 A-axis rate ramp - 2026-09-05

## Objective

Identify a repeatable A-axis rate that completes cleanly without lost position,
unexpected motion, or noticeable motor heating while remaining within the
current-limited bench-test setup.

## Configuration

- Hardware: A 17HS15-1504S-X1 motor and its TB6600 driver.
- Motor phases: `A+` black, `A-` green, `B+` red, `B-` blue.
- Driver settings: 8× microstep for A; 1.5 A/phase current setting.
- Power: 12 V supply with a 2 A current limit for this single-driver test.
- Mechanics: A-axis circular bed, with no hard stop in the tested range.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender; installed E-03 and
  M-01 checks had already passed.
- Instruments: power-supply current display and touch-based temperature
  observation; no numeric temperature instrument was used.

## Code, commands, and configuration used

The test used incremental, controlled-feed moves. Absolute mode was restored
after each test set.

```gcode
G91
G1 A10 F180
G1 A-10 F180
G1 A10 F240
G1 A-10 F240
G1 A10 F300
G1 A-10 F300
G1 A10 F360
G1 A-10 F360
G1 A10 F420
G1 A-10 F420
G1 A10 F480
G1 A-10 F480
G1 A10 F540
G1 A-10 F540
G90
```

## Procedure

1. Kept only the A-axis motor connected and retained the 2 A supply limit.
2. Increased the commanded `G1` feed in bounded steps from `F180` through
   `F540`, using equal positive and negative moves at each rate.
3. Observed motion smoothness, direction, return to the physical reference
   mark, supply current, and motor temperature after the moves.

## Results

- The A-axis completed the tested rate steps at `F180`, `F240`, `F300`,
  `F360`, `F420`, `F480`, and `F540` without reported stalling or jerking.
- At `F480`, the mechanism landed exactly on the established reference mark
  after the return move.
- At `F540`, the mechanism also landed exactly on the established reference
  mark after the return move.
- The measured supply current during the `F480` move was approximately
  `0.465 A`, below the 2 A supply limit.
- The motor remained cool to the touch after the `F480` and `F540` tests.
- A prior longer A-axis run was observed at approximately `0.47-0.476 A` on
  the supply and also remained cool; the exact rate associated with that
  reading was not recorded separately from the rate-ramp steps.
- Dwell duration and an instrumented temperature measurement were not
  recorded.
- A numeric supply-current reading specifically at `F540` was not recorded.
- Disposition: **M-02 is in progress; `F540` is the highest A-axis rate
  validated so far under this test setup.**

## Difficulties and corrective actions

None encountered during the recorded `F180`-`F540` A-axis rate steps. The
earlier X-axis jerking was part of M-01 and was not observed in this A-axis
rate ramp.

## Interpretation

The A-axis has demonstrated clean, repeatable motion through `F540` for the
tested move pattern, with no observed position loss or heating. The measured
`0.465 A` supply current at `F480` is well below the temporary 2 A limit. This
supports using `F540` as the highest currently tested rate, subject to the configured A-axis
maximum rate and the actual operating duty cycle. It is not yet evidence that
`F540` is the absolute motor or controller limit. The lack of a F540-specific
current reading and quantitative temperature/dwell data limits the strength of
the thermal conclusion.

## Decisions and next action

Do not command above the controller's configured A-axis maximum rate. Record
the A-axis setting in ioSender before selecting a production rate. Keep
`F540` as the highest A-axis rate tested so far and continue M-02 with the X
and Y axes. Record F540 current and add a longer dwell or instrumented
temperature check if thermal margin is needed.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-05-m-01-a-axis-direction-jog.md`](2026-09-05-m-01-a-axis-direction-jog.md)
