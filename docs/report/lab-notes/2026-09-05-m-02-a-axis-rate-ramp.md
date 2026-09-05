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
- In a follow-up comparison, the operator could distinguish `F495`, while
  `F500`, `F540`, and `F600` sounded identical. This makes an approximately
  `F500` configured-rate cap the leading hypothesis, pending instrumented
  verification.
- Disposition: **M-02 is in progress; `F600` is the highest A-axis rate
  validated so far under this test setup.**

## Difficulties and corrective actions

An apparent `0.5 mm` return offset at `F600` was initially reported, but the
operator then identified that the pulley had been moved during the check. The
offset is therefore discarded as a reference-handling error, not attributed to
the motor or driver. The earlier X-axis jerking was part of M-01 and was not
observed in the A-axis rate ramp.

## Interpretation

The A-axis has demonstrated clean motion through `F600` for the tested move
pattern, with no confirmed position loss or heating. The apparent `F600`
reference discrepancy was caused by moving the pulley during inspection, so
`F600` remains qualified for this run. The measured supply currents at `F480`,
`F540`, and `F600` (`0.465 A`, `0.476 A`, and `0.485 A`) remained below the
temporary 2 A limit; current and touch temperature alone cannot establish the
absolute motor or controller limit. The reported audible plateau near `F500`
must be checked with the controller setting or measured STEP frequency before
assuming that the axis actually reached `F600` cruise speed.

## Decisions and next action

Keep `F600` as the highest qualified A-axis command for now. Before raising the
rate, read the configured A-axis maximum in ioSender and measure STEP frequency
on a longer, safe move. At the present `4.444444` steps/degree, `F500`, `F540`,
and `F600` correspond to approximately `37.0`, `40.0`, and `44.4 Hz`. If the
frequency tops out near `37 Hz`, the controller is limiting the axis near
`F500`; if it reaches `44.4 Hz`, the apparent plateau was acoustic or
acceleration-related. Do not move the pulley while inspecting the mark.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-05-m-01-a-axis-direction-jog.md`](2026-09-05-m-01-a-axis-direction-jog.md)
