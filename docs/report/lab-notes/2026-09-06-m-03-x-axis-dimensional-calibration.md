# M-03 X-axis dimensional calibration - 2026-09-06

## Objective

Calibrate and verify X-axis physical travel over a 100 mm span, including a
matched reverse return to a fixed reference mark.

## Configuration

- Hardware: X 17HS15 motor and GT2 belt gantry.
- Driver setting: 16x microstep and 1.5 A/phase current setting.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- Initial calculated value: `$100=80.000000` steps/mm.
- Final accepted value: `$100=79.71303` steps/mm.
- Measurement: calipers and a fixed carriage/frame reference mark.
- Pen/toolhead: no pen installed.

## Code, commands, and configuration used

The definitive check used relative millimeter motion at a moderate feed:

```gcode
G21
G94
G91
G1 X100 F300
G1 X-100 F300
G90
```

## Procedure

1. Positioned the carriage with more than 100 mm of clear positive X travel
   and marked a fixed starting reference.
2. A first short `X10` measurement was later identified as incorrect and was
   not retained as calibration evidence.
3. Restored the calculated `$100=80.000000`, commanded `X100`, and measured
   `100.36 mm` with calipers.
4. Returned using `X-100` before changing the scale, preserving the reference
   position under the old setting.
5. Applied the measured correction: `80 * 100 / 100.36 = 79.71303`.
6. With `$100=79.71303`, commanded `X100` again; calipers measured exactly
   `100 mm`.
7. Commanded `X-100` and verified exact return to the original mark.

## Results

- `$100=80.000000` produced a 100.36 mm physical move for a 100 mm command.
- `$100=79.71303` produced exactly 100 mm on the repeated caliper check.
- The matched reverse move returned exactly to the reference mark.
- Disposition: **M-03 passed for the conducted X-axis dimensional check.**

## Difficulties and corrective actions

The first 10 mm measurement was reported as 9 mm and led to a provisional
`$100=88.88889` value. A later 100 mm caliper measurement showed that short
measurement was not reliable. The calibration was therefore recomputed only
from the 100 mm measurement and independently verified before acceptance.

## Interpretation

The installed X-axis scale is validated for the measured 100 mm unloaded span.
This does not quantify full-frame backlash or pen-loaded dimensional error.

## Decisions and next action

Retain `$100=79.71303` steps/mm. X and Y now have measured 100 mm travel
checks; proceed with pen-free coordinated X/Y/A motion after the relevant
clearance and registration setup is ready.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-03
- [`2026-09-06-m-02-x-axis-rate-ramp.md`](2026-09-06-m-02-x-axis-rate-ramp.md)
- [`2026-09-06-x-axis-rate-and-dimensional-calibration.md`](../../changes/hardware/2026/2026-09-06-x-axis-rate-and-dimensional-calibration.md)
