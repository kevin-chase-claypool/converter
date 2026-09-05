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
- ioSender A-axis settings during the initial ramp: maximum rate
  `500.000 deg/min` (`$113`), acceleration `10.000 deg/sec^2` (`$123`), and
  maximum travel `200.000 deg` (`$133`). The initial screenshot showed
  `$103 = 250.000 step/deg`; the operator corrected it to `$103 = 4.44444`,
  which the later `$$` report confirms. For the follow-up high-rate check,
  `$113` was raised to `5000.000 deg/min`; `$123` remained `10.000 deg/sec^2`.
  The A-axis contract therefore uses motor-shaft degrees.
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
  configured `F500` cap; the later `$103` correction makes the motor-degree
  interpretation explicit.
- After correcting `$103` to `4.44444` and raising `$113` to `5000.000`, the
  operator ran `G1 A720 F5000` and then `G1 A1440 F5000`. Both moves were
  reported as smooth with slow ramp-up and ramp-down. At `$123 = 10 deg/sec^2`,
  `F5000` is `83.33 deg/sec`; each ramp takes about `8.3 s` and `347` commanded
  degrees. The `A1440` move therefore should have about `746` commanded degrees
  of constant-speed travel, but the ramp occupies a large visual portion.
- Disposition: **M-02 is in progress. `F500` was the highest actual A-axis rate
  validated under the initial `$113=500` configuration; the later `F5000` runs
  used `$113=5000` and are acceleration-profile observations, not a final
  plotting-rate decision.**

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
absolute motor or controller limit. The initial `$113 = 500.000 deg/min`
setting confirms that the earlier higher F commands did not request a higher
actual planner rate; the follow-up `$113` was then raised to `5000.000`. The
corrected `$103 = 4.44444` setting now matches the planned motor-degree
contract. The observed slow `F5000` profile is explained by the
low `$123 = 10` setting, not by a failure to command motion. If an `A1440`
move shows no constant-speed interval, verify the actual commanded position,
feed, and elapsed time before increasing acceleration.

## Decisions and next action

Keep `$113 = 5000` for this rate experiment, but do not select a final plotting
acceleration from the unloaded bed test. M-04's one-motor-revolution check now
passes at `A360 F300` in both directions; M-05 must still verify the 12:1 bed
ratio. Test `$123` in controlled steps, beginning at `25`, then `50` if the
move remains smooth and returns to its mark. Repeat under the eventual pen-load
condition before adopting a production value, and do not move the pulley while
inspecting the mark.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-05-m-01-a-axis-direction-jog.md`](2026-09-05-m-01-a-axis-direction-jog.md)
