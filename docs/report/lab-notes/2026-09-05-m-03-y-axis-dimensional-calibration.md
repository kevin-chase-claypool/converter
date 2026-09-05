# M-03 Y-axis dimensional calibration - 2026-09-05

## Objective

Verify that the calculated Y-axis setting produces accurate physical travel
and returns to the same position after a matched reverse move.

## Configuration

- Hardware: Y 17HS15-1504S-X1 motor and GT2 belt gantry.
- Driver settings: 16x microstep and 1.5 A/phase current setting.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- Y steps-per-unit before test: `$101 = 80.000000` steps/mm.
- Motion settings: `$111 = 1500` mm/min and `$121 = 500` mm/sec^2.
- Measurement: calipers and a fixed carriage/frame reference mark.

## Code, commands, and configuration used

The test used millimeters, feed-per-minute mode, and relative motion. The
operator verified the modal state with `$G` before moving:

```gcode
G21
G94
G90
G91

G1 Y100 F120
G1 Y-100 F120

G90
```

The `$G` response confirmed `G21 G91 G94` before the forward move.

## Procedure

1. Positioned the Y carriage with at least 100 mm of safe travel.
2. Marked the starting carriage position against a fixed frame reference.
3. Commanded `G1 Y100 F120` and measured the physical displacement with
   calipers.
4. Commanded `G1 Y-100 F120` and compared the carriage with the original mark.
5. Restored absolute mode with `G90`.

## Results

- The commanded 100 mm Y move measured exactly 100 mm with calipers.
- The matched `Y-100` move returned exactly to the starting reference mark.
- No `$101` correction was required; `$101=80.000000` is validated for this
  measured Y travel check.
- Disposition: **M-03 passed for the conducted Y-axis dimensional check.**
  The X-axis portion remains open.

## Difficulties and corrective actions

The earlier Y measurement attempt used `G90` with `$101=250`, producing an
unexpected long move. The controller was then returned to the calculated
`$101=80` baseline and the test was repeated explicitly in `G91`; the repeat
produced the expected 100 mm travel and exact return.

## Interpretation

The Y steps-per-millimeter calculation matches the measured installed belt
travel over the 100 mm check. This supports using `$101=80.000000` for the
current unloaded configuration. It does not calibrate X, quantify belt
backlash over the full frame, or qualify dimensional accuracy under pen load.

## Decisions and next action

Retain `$101=80.000000`. Perform the same physical 100 mm check on X with
`$100=80.000000`, then use both axes in a coordinated-motion test.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-03
- [`2026-09-05-m-02-y-axis-rate-ramp.md`](2026-09-05-m-02-y-axis-rate-ramp.md)
- [`2026-09-05-m-03-y-axis-dimensional-calibration.md`](../../changes/hardware/2026/2026-09-05-m-03-y-axis-dimensional-calibration.md)
