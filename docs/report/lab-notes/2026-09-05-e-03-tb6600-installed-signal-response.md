# E-03 TB6600 installed-driver signal response - 2026-09-05

## Objective

Verify that the installed X, Y, and A TB6600 signal inputs respond correctly
to RP23CNC commands through the completed common-cathode signal harnesses.

## Configuration

- Hardware revisions: Brookwood Design RP23CNC/RP23U5XBB V1.01; three received
  TB6600 drivers (X, Y, and A).
- Wiring/pin map: Each axis RP23CNC `G` is connected to its TB6600 `PUL-`,
  `DIR-`, and `ENA-`. `Stp`, `Dir`, and `En` connect to `PUL+`, `DIR+`, and
  `ENA+`. The harness uses 24 AWG conductors: black common, yellow `En`,
  white `Dir`, and blue `Stp`.
- Firmware/software: Installed grblHAL build controlled through ioSender 2.0.47;
  exact RP23CNC firmware commit was not recorded during this bench run.
- Test state: One driver at a time; motor phases disconnected during the
  signal test. The same response was then observed on the other two drivers.
- Instruments: Owner's multimeter and FNIRSI/ADS1014D oscilloscope. Probe
  ratio and meter model were not recorded.

## Code, commands, and configuration used

```gcode
G91
G0 A10 F60
G0 A-10 F60
G90
```

Each command returned `ok`. The A-axis status moved from MPos A=150 to A=160
and returned to A=150, with `Run` reports followed by `Idle`.

## Procedure

1. Powered the RP23CNC and connected ioSender after recovering the board's
   USB source selection.
2. Kept the motor phases disconnected and tested the A TB6600 signal input
   harness one signal at a time, using the TB6600 signal return as the meter
   or oscilloscope reference.
3. Checked `ENA+` during an A move, `DIR+` after positive and negative
   relative moves, and `PUL+` with the oscilloscope during motion.
4. Repeated the same signal-response check on the X and Y TB6600s. The owner
   reports that both matched the A-axis behavior.

## Results

- `ENA+`: approximately 4.82 V at idle; it dropped toward 0 V during motion
  and returned high at `Idle`. This is the observed active-low enable behavior.
- `DIR+`: approximately 0 V after `G0 A10 F60` and approximately 4.82 V after
  `G0 A-10 F60`. The line held its state after the move completed. The
  positive/negative polarity assignment is arbitrary; the required direction
  state change was present.
- `PUL+`: oscilloscope maximum was approximately 5.22 V during commanded
  motion. The step activity was present for both directions.
- X and Y TB6600s: owner reports the same enable, direction, and step response
  as A.
- Disposition: **E-03 passed for installed-driver logic response on X, Y, and
  A.**

## Difficulties and corrective actions

The first inspection of the console showed command text without visible
acknowledgements. Enabling the reply view and sending the commands one at a
time showed `ok` responses and the expected `Run`/`Idle` sequence. A direction
measurement initially used the `ENA+` terminal; moving the meter to `DIR+`
separated the active-low enable behavior from the held direction state.

## Interpretation

The RP23CNC-to-TB6600 signal harnesses are powered and logically functional
on all three axes. The controller accepts G-code, generates A-axis motion
planning, enables the driver while moving, changes direction polarity for
opposite moves, and produces approximately 5 V step pulses. The result does
not yet qualify motor-phase wiring, current/microstep DIP settings, loaded
motion, lost-step performance, or thermal behavior.

## Decisions and next action

Treat E-03 as complete and promote the corresponding signal rows in
[`docs/hardware/WIRING_TABLE.md`](../../hardware/WIRING_TABLE.md) to
`bench-verified`. Proceed to E-04 DIP/current confirmation, then M-01 with
one motor connected at a time. Keep the `Pn:ZA` active-input observation in
view before enabling full-machine homing.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), E-03 and E-04
- [`WIRING_TABLE.md`](../../hardware/WIRING_TABLE.md), MOT-001 through MOT-008
- [`2026-09-05-tb6600-installed-signal-response.md`](../../changes/hardware/2026/2026-09-05-tb6600-installed-signal-response.md)
