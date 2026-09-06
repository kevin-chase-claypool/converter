# M-02 X-axis rate ramp - 2026-09-06

## Objective

Verify smooth unloaded X-axis motion and repeatable return at a preliminary
maximum rate and acceleration before coordinated X/Y/A tests.

## Configuration

- Hardware: X 17HS15 motor and its TB6600 driver on the GT2 gantry.
- Driver setting: 16x microstep and 1.5 A/phase current setting.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- X travel calibration: `$100=79.71303` steps/mm, established by the same
  session's M-03 measurement.
- Accepted unloaded motion settings: `$110=1500` mm/min and
  `$120=500` mm/sec^2.
- Pen/toolhead: no pen installed; M3/M5 were not commanded.

## Code, commands, and configuration used

The reusable test program is
[`x-axis-rate-repeat.gcode`](../../testing/gcode/x-axis-rate-repeat.gcode):

```gcode
G21
G94
G91

G1 X50 F1500
G1 X-50 F1500
G1 X50 F1500
G1 X-50 F1500
G1 X50 F1500
G1 X-50 F1500
G1 X50 F1500
G1 X-50 F1500
G1 X50 F1500
G1 X-50 F1500

G90
```

## Procedure

1. Confirmed pen-free, unobstructed X travel and marked the carriage against a
   fixed frame reference.
2. Set `$110=1500` mm/min and `$120=500` mm/sec^2, matching the accepted
   preliminary Y-axis unloaded settings.
3. Ran five matched 50 mm positive/negative moves at `F1500` in incremental
   millimeter/feed-per-minute mode.
4. Compared the final carriage position with the initial reference mark.

## Results

- The motion was reported as problem-free and smooth.
- The carriage returned exactly to its starting reference mark after the
  repeated reversals.
- No skipped-step, stall, or jerk symptom was reported.
- Motor and driver temperature was not recorded during this X run.
- Disposition: **M-02 passed for the conducted unloaded X-axis rate and
  repeatability check.** Retain `$110=1500` mm/min and `$120=500` mm/sec^2 as
  preliminary settings.

## Interpretation

This result establishes a repeatable, pen-free motion baseline at the selected
settings. It is not a final pen-loaded production limit, a thermal endurance
result, or a coordinated X/Y/A result.

## Decisions and next action

Keep the selected X settings for pen-free coordinated-motion testing. Record a
temperature observation in a later longer or loaded motion test, and do not
treat this result as toolhead or drawing validation.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-02
- [`2026-09-06-m-03-x-axis-dimensional-calibration.md`](2026-09-06-m-03-x-axis-dimensional-calibration.md)
- [`2026-09-06-x-axis-rate-and-dimensional-calibration.md`](../../changes/hardware/2026/2026-09-06-x-axis-rate-and-dimensional-calibration.md)
