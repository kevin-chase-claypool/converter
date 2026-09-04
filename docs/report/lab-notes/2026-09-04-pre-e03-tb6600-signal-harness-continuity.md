# Pre-E-03 TB6600 signal-harness continuity check - 2026-09-04

## Objective

Confirm that the three short RP23CNC-to-TB6600 signal harnesses are connected
end-to-end before attempting the installed-driver STEP/DIR/ENABLE test.

## Configuration

- Hardware revisions: RP23CNC/RP23U5XBB V1.01; X, Y, and A TB6600 drivers.
- Wiring/pin map: Each axis uses approximately six inches of 24 AWG wiring:
  black common `G`, yellow `En`, white `Dir`, and blue `Stp`. The black
  common is distributed to `ENA-`, `DIR-`, and `PUL-`; the colored conductors
  land on `ENA+`, `DIR+`, and `PUL+`.
- Firmware commit/build: No firmware or powered command used.
- Instruments: Owner's continuity meter; model and accuracy not recorded.

## Code, commands, and configuration used

```text
No firmware, software, or controller commands used.
```

## Procedure

1. Removed power before checking the harnesses.
2. Checked the installed signal conductors end-to-end from the RP23CNC side to
   their corresponding TB6600 terminals.
3. Repeated the check for all three axes, including the common-`G` conductors
   and their common-block jumpers.

## Results

- The owner reports end-to-end continuity for all X, Y, and A signal
  conductors and their common returns.
- This confirms physical conductor continuity only. No powered STEP/DIR/EN
  response, input-current, polarity, or inter-wire short measurement was
  recorded in this check.
- Disposition: **continuity gate complete; E-03 remains TBD**.

## Difficulties and corrective actions

None reported.

## Interpretation

The harnesses are physically connected through the intended endpoints, so the
project can proceed to the installed-driver input test. Continuity does not
prove that the TB6600 optocoupler inputs respond correctly or that the selected
common-cathode polarity is correct.

## Decisions and next action

Keep all motors disconnected and perform E-03 one TB6600 at a time using the
documented common-cathode pattern. Record the meter/setup details, signal
levels, input behavior, and pass/fail result before connecting motor phases.
