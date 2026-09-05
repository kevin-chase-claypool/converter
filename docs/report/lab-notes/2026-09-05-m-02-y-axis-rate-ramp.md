# M-02 Y-axis rate ramp - 2026-09-05

## Objective

Verify smooth unloaded Y-axis motion in both directions and select a
conservative working rate and acceleration for continued commissioning.

## Configuration

- Hardware: Y 17HS15-1504S-X1 motor and its TB6600 driver on the GT2 gantry.
- Driver settings: 16x microstep and 1.5 A/phase current setting.
- Power: 12 V supply with the existing 2 A current limit.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- Y calibration: `$101 = 80.000000` steps/mm baseline for the 20-tooth GT2
  pulley.
- Initial Y motion settings: `$111 = 500` mm/min and `$121 = 10` mm/sec^2.
- Accepted follow-up settings: `$111 = 1500` mm/min and `$121 = 500` mm/sec^2.
- Pen/toolhead: retracted and not engaged during the test.

## Code, commands, and configuration used

The initial rate steps used equal positive and negative 5 mm moves in
incremental mode. Absolute mode was restored afterward:

```gcode
G21
G94
G91

G1 Y5 F60
G1 Y-5 F60
G1 Y5 F120
G1 Y-5 F120
G1 Y5 F240
G1 Y-5 F240
G1 Y5 F360
G1 Y-5 F360
G1 Y5 F500
G1 Y-5 F500

G90
```

After the stepped checks passed, the operator increased `$121` to `500` and
`$111` to `1500` and reported that the resulting Y motion remained smooth.

## Procedure

1. Confirmed the Y carriage had clear travel in both directions and kept the
   pen retracted.
2. Established millimeter units (`G21`), feed-per-minute mode (`G94`), and
   incremental motion (`G91`).
3. Ran matched north/south moves at `F60`, `F120`, `F240`, `F360`, and `F500`.
4. Observed direction, smoothness, skipped-step symptoms, and return behavior.
5. Raised the Y acceleration and maximum-rate settings to `$121=500` and
   `$111=1500`, then checked the resulting motion.
6. Restored absolute mode with `G90`.

## Results

- All stepped Y moves completed successfully in both directions.
- No skipped steps, stalls, or jerking were observed.
- The operator reported the post-change motion at `$111=1500` and
  `$121=500` as smooth and acceptable for continued commissioning.
- No numeric current or instrumented temperature measurement was recorded for
  this rate ramp; the result is a motion/position observation.
- Disposition: **M-02 passed for the conducted unloaded Y-axis rate test and
  the selected preliminary settings.**

## Difficulties and corrective actions

The first attempted `G1 Y5 F60` was rejected with grblHAL error 22 because the
controller did not receive a valid feed-rate modal state. Sending `G21` and
`G94` before repeating the command established millimeter/feed-per-minute
mode, after which the stepped tests ran successfully.

## Interpretation

The Y axis moves cleanly with the selected 16-microstep setup and has no
observed skipped-step symptom through the conducted stepped tests. `$111=1500`
and `$121=500` are a useful preliminary unloaded setting, but they do not by
themselves establish a final production rate under pen load or prove a true
constant-speed plateau on a long move.

## Decisions and next action

Retain `$111=1500` mm/min and `$121=500` mm/sec^2 for the next commissioning
step unless a longer validation move exposes a problem. Continue with the X
rate check, then perform coordinated X/Y/A and loaded toolhead tests before
selecting final plotting settings.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-05-m-02-a-axis-rate-ramp.md`](2026-09-05-m-02-a-axis-rate-ramp.md)
- [`2026-09-05-m-02-y-axis-rate-verification.md`](../../changes/hardware/2026/2026-09-05-m-02-y-axis-rate-verification.md)
