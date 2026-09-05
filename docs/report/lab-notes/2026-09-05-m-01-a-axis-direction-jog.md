# M-01 A-axis initial direction jog - 2026-09-05

## Objective

Verify that the A-axis motor starts, moves smoothly in both commanded
directions, and has the expected coordinate-to-rotation relationship before
testing longer motion or the other axes.

## Configuration

- Hardware: A 17HS15-1504S-X1 motor and its TB6600 driver.
- Motor phases: `A+` black, `A-` green, `B+` red, `B-` blue.
- Driver settings: 8× microstep for A; 1.5 A/phase current setting.
- Power: 12 V supply with a 2 A current limit for this single-driver test.
- Mechanics: A-axis circular bed, with no hard stop in the tested range.
- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender; signal E-03 had
  already passed.
- Instrument: Power-supply current display; meter model and temperature
  instrument were not recorded.

## Code, commands, and configuration used

```gcode
G91
G1 A10 F120
G1 A-10 F120
G90
```

Each move was issued at `F120` in incremental mode, then absolute mode was
restored with `G90`.

## Procedure

1. Connected only the A motor to the A TB6600 with power removed.
2. Applied the current-limited 12 V supply.
3. Commanded a positive 10-unit A move, observed the rotation, and recorded
   supply current.
4. Commanded a negative 10-unit A move and observed the reverse rotation.

## Results

- `G1 A10 F120` completed successfully and rotated the A mechanism
  counterclockwise.
- `G1 A-10 F120` completed successfully and rotated the A mechanism clockwise.
- The measured supply current during the positive move was approximately
  `0.44 A`, below the 2 A supply limit.
- No stall or failed move was reported.
- Disposition: **initial M-01 A-axis direction/smooth-motion check passed;
  full M-01 remains partial pending repeatability and heating evidence.**

## Difficulties and corrective actions

None encountered during this initial A-axis jog.

## Interpretation

The A motor phases and direction mapping are producing useful bidirectional
motion through the tested TB6600. The motor reverses as commanded and the
current draw is comfortably below the temporary supply limit. This is not yet
a full thermal or lost-step qualification.

## Decisions and next action

Keep the 1.5 A/phase driver setting and 2 A supply limit for the next guarded
check. Repeat positive/negative A moves for multiple cycles, verify that the
mechanism returns to its starting mark, and record motor/driver temperature
before treating M-01 as complete. Then perform the equivalent X/Y low-speed
jog tests.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-01
- [`2026-09-05-e-03-tb6600-installed-signal-response.md`](2026-09-05-e-03-tb6600-installed-signal-response.md)
