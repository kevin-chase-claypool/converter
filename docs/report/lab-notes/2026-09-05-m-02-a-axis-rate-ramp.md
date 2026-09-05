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
- ioSender A-axis settings observed after the ramp: maximum rate `500.000 deg/min`
  (`$113`), acceleration `10.000 deg/sec^2` (`$123`), and maximum
  travel `200.000 deg` (`$133`). The screenshot also reports `$103 = 250.000
  step/deg`, which conflicts with the project's planned `4.444444 step/deg`
  A-axis contract and must be resolved by M-04 before converting F rates to
  motor or bed speed.
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
G1 A10 F600
G1 A-10 F600
G90
```

## Procedure

1. Kept only the A-axis motor connected and retained the 2 A supply limit.
2. Increased the commanded `G1` feed in bounded steps from `F180` through
   `F600`, using equal positive and negative moves at each rate.
3. Observed motion smoothness, direction, return to the physical reference
   mark, supply current, and motor temperature after the moves.

## Results

- The A-axis completed the tested rate steps at `F180`, `F240`, `F300`,
  `F360`, `F420`, `F480`, and `F540` without reported stalling or jerking.
- At `F480`, the mechanism landed exactly on the established reference mark
  after the return move.
- At `F540`, the mechanism also landed exactly on the established reference
  mark after the return move.
- At `F600`, motion was smooth, the mechanism remained cool, and the apparent
  return offset was later traced to the operator having moved the pulley while
  checking the mark; it was not a machine repeatability error.
- The measured supply current during the `F480` move was approximately
  `0.465 A`, below the 2 A supply limit.
- The motor remained cool to the touch after the `F480` and `F540` tests.
- A prior longer A-axis run was observed at approximately `0.47-0.476 A` on
  the supply and also remained cool; the exact rate associated with that
  reading was not recorded separately from the rate-ramp steps.
- Dwell duration and an instrumented temperature measurement were not
  recorded.
- The measured supply current during the `F540` move was approximately
  `0.476 A`, below the 2 A supply limit.
- The measured supply current during the `F600` move was approximately
  `0.485 A`, below the 2 A supply limit.
- The operator reported that the audible speed appeared to plateau near
  `F500`; this was not instrumented and may reflect the configured A-axis rate
  ceiling or the short move not reaching cruise speed.
- The ioSender settings screen confirms the A-axis maximum rate is
  `500.000 deg/min` (`$113`), so commands above `F500` are planner-limited.
- In a follow-up comparison, the operator could distinguish `F495`, while
  `F500`, `F540`, and `F600` sounded identical. This is consistent with the
  configured `F500` cap, although the current `$103` resolution mismatch means
  the actual step frequency must not be inferred from the planned baseline.
- Disposition: **M-02 is in progress; `F500` is the highest actual A-axis rate
  configured and validated so far. `F540` and `F600` were accepted commands but
  were limited by `$113`.**

## Difficulties and corrective actions

An apparent `0.5 mm` return offset at `F600` was initially reported, but the
operator then identified that the pulley had been moved during the check. The
offset is therefore discarded as a reference-handling error, not attributed to
the motor or driver. The earlier X-axis jerking was part of M-01 and was not
observed in the A-axis rate ramp.

## Interpretation

The A-axis has demonstrated clean motion for commands through `F600` for the
tested move pattern, with no confirmed position loss or heating. Because
`$113 = 500.000 deg/min`, however, the controller likely executed `F540` and
`F600` at no more than `F500`; those commands do not prove higher actual cruise
rates. The apparent `F600` reference discrepancy was caused by moving the
pulley during inspection. The measured supply currents at `F480`, `F540`, and
`F600` (`0.465 A`, `0.476 A`, and `0.485 A`) remained below the
temporary 2 A limit; current and touch temperature alone cannot establish the
absolute motor or controller limit. The `$113 = 500.000 deg/min` setting
confirms that the higher F commands did not request a higher actual planner
rate. The `$103 = 250.000` setting still conflicts with the planned
`4.444444 step/deg` contract and must be resolved before converting these F
values to pulse frequency or mechanical speed.

## Decisions and next action

Keep `F500` as the highest configured A-axis rate for now; `F540` and `F600`
were accepted commands but were limited by `$113`. Resolve the `$103=250.000`
versus planned `4.444444 step/deg` discrepancy with M-04 (one motor revolution
and bed-ratio check) before changing `$103` or converting F rates to pulse
frequency. Do not move the pulley while inspecting the mark.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-05-m-01-a-axis-direction-jog.md`](2026-09-05-m-01-a-axis-direction-jog.md)
