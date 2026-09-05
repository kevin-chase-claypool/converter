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
5. Removed A power before connecting the Y motor, then commanded 1-unit
   positive and negative Y moves at `F60` and observed the cardinal directions.
6. Removed Y power before connecting the X motor, then commanded 1-unit
   positive and negative X moves at `F60` and observed the cardinal directions.
7. Marked the X carriage against the stationary frame, ran ten `X5`/`X-5`
   relative cycles at `F60`, and compared the physical reference after the
   final return.
8. Marked the Y carriage against the stationary frame, ran ten `Y5`/`Y-5`
   relative cycles at `F60`, and compared the physical reference after the
   final return.
9. Marked the A motor pulley relative to the motor body, ran the repeat
   positive/negative A cycle, and compared the reference after the final
   return.

## Results

- `G1 A10 F120` completed successfully and rotated the A mechanism
  counterclockwise.
- `G1 A-10 F120` completed successfully and rotated the A mechanism clockwise.
- The measured supply current during the positive move was approximately
  `0.44 A`, below the 2 A supply limit.
- `G1 Y1 F60` completed successfully and moved the Y axis north; `G1 Y-1 F60`
  moved south. The reported supply current for both Y moves was approximately
  `0.43 A`.
- `G1 X1 F60` completed successfully and moved the X axis east; `G1 X-1 F60`
  moved west. The reported supply current for both X moves was approximately
  `0.42 A`.
- No stall or failed move was reported during the final direction checks.
- After ten X-axis `+5`/`-5` cycles, the physical carriage/frame marks were in
  the exact same relative position as at the start of the test.
- After ten Y-axis `+5`/`-5` cycles, the physical carriage/frame marks were in
  the exact same relative position as at the start of the test.
- No noticeable heating was reported at the X or Y motors or TB6600 drivers
  during their direction and return-position checks. This was a touch-based
  observation; no temperature instrument or numeric limit was recorded.
- The A motor pulley returned to the exact same position relative to the motor
  body after its repeat cycle set.
- No noticeable heating was reported by touch at any X, Y, or A motor or
  TB6600 driver; all remained cold. This is a qualitative observation, not a
  numeric temperature measurement.
- Disposition: **M-01 passed for the conducted low-speed X/Y/A direction,
  return-to-position, and preliminary heating checks.**

## Difficulties and corrective actions

An initial X-axis attempt was reported as jerking forward and backward. The
owner then rechecked the X phase termination and subsequently obtained clean
east/west jog results. The exact corrective wiring change was not recorded;
retain the pair check as the repeatable corrective action if the symptom
returns.

## Interpretation

The A, Y, and X motor phases and direction mappings are producing useful
bidirectional motion through their tested TB6600s. The X and Y physical
references returned exactly after ten cycles, and the A physical reference
returned exactly after its repeat cycle set. These results provide no
observable lost-step or coupling-slip evidence in the conducted tests. Current
draw remained comfortably below the temporary supply limit. No noticeable
heating was observed on any axis, but that observation was not instrumented.
This is a low-speed qualification; longer dwell and rate-ramp thermal behavior
remain follow-up work.

## Decisions and next action

Keep the 1.5 A/phase driver setting and 2 A supply limit. Begin M-02
controlled rate-ramp testing; record temperatures with an instrument if
available during the longer or faster runs.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-01
- [`2026-09-05-e-03-tb6600-installed-signal-response.md`](2026-09-05-e-03-tb6600-installed-signal-response.md)
