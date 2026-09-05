# M-05 A-axis bed-ratio check - 2026-09-05

## Objective

Verify that the calibrated A-axis command produces the intended 12:1
motor-to-bed relationship: 4,320 commanded A motor-degrees (12 motor
revolutions) must produce exactly one 360-degree bed revolution.

## Configuration

- Hardware: A 17HS15-1504S-X1 motor, TB6600 driver, and 12:1 rotating bed.
- Driver settings: 8x microstep and 1.5 A/phase current setting.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- A-axis calibration: `$103 = 4.44444` steps per commanded motor-degree.
- A-axis operating state: pen not engaged; the circular bed has no hard stop in
  the tested range.
- Previous commissioning state: M-01, M-02, and M-04 had passed for their
  documented scopes; M-05 was the remaining unloaded A-axis ratio check.

## Code, commands, and configuration used

The bed was marked against a fixed frame reference before the test. The
forward and reverse commands were issued in incremental mode, and absolute
mode was restored afterward:

```gcode
G90
G91
G1 A4320 F10000
G90

G91
G1 A-4320 F10000
G90
```

`A4320` is 12 motor revolutions at the 12:1 reduction, so it should equal one
bed revolution. `A-4320` returns the bed in the opposite direction.

## Procedure

1. Confirmed the A-axis calibration and marked the bed relative to a fixed
   frame pointer.
2. Commanded one positive `A4320` move and waited for the controller to return
   to `Idle`.
3. Compared the bed mark with the fixed pointer.
4. Commanded one negative `A-4320` move and compared the mark with its original
   position.
5. Repeated the forward/reverse check and inspected the return position each
   time.

## Results

- The bed mark returned exactly to its starting position after each completed
  forward/reverse check.
- No position error, lost-step symptom, or unexpected motion was reported.
- The result verifies one bed revolution for `A4320` and the expected 12:1
  motor-to-bed ratio under the unloaded test conditions.
- No instrumented current or temperature measurement was recorded as part of
  this ratio check; those observations are not required to establish the
  geometric ratio.
- Disposition: **M-05 passed.**

## Difficulties and corrective actions

None encountered. The bed reference mark remained stable throughout the
forward/reverse checks.

## Interpretation

The calibrated A-axis unit contract is consistent with the installed 12:1
reduction: 4,320 motor-degree commands correspond to one complete bed turn.
This validates the bed-angle scaling needed for later magnetic index
registration and coordinated X/Y/A testing. It does not by itself select the
final plotting rate or qualify pen-engaged force behavior.

## Decisions and next action

Mark M-05 complete and retain `$103 = 4.44444`. Continue with the remaining
X/Y rate checks, then proceed to the separate homing, magnetic registration,
and pen-engaged toolhead tests.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-05
- [`2026-09-05-m-02-a-axis-rate-ramp.md`](2026-09-05-m-02-a-axis-rate-ramp.md)
- [`2026-09-05-m-05-bed-ratio-verification.md`](../../changes/hardware/2026/2026-09-05-m-05-bed-ratio-verification.md)
