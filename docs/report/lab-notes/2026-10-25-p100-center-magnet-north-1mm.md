# Lab Note: 2026-10-25 - P100 pen must move 1 mm north

> Superseded by `2026-10-25-p100-center-magnet-final-y-0-3.md`: the controller
> was already running Y `-0.70`, so the required 1 mm north move produces final
> Y `0.30`.

## Objective

Encode the center-magnet result that the registered pen position must move
1 mm north in machine Y.

## Configuration

- Hardware: installed RP23CNC/RP23U5XBB and production integrated toolhead.
- Previously deployed P100 constants: X `2.45 mm`, Y `0.30 mm`.
- Measurement: embedded center magnet compared with the parked pen position
  after `G65 P113`.

## Procedure

1. Complete `G65 P113`.
2. Compare the parked pen position with the embedded center magnet.
3. Record the required movement in machine axes.
4. Update the P100 axis-center correction and validate the macro.

## Results

- Required movement: 1.000 mm west in X and 1.000 mm north in Y.
- Replacement constants:
  - `#<axis_center_correction_x> = 1.45`
  - `#<axis_center_correction_y> = 1.3`
- The G10 registration write becomes:

```text
G10 L20 P1 X-1.45 Y-30.7892
```

- No artwork offset or bed-compensation setting was changed.

## Verification

```text
python tools\check_macros.py
All 17 macro(s) parse-safe.

python tools\validate_homing_macro.py
P100/P115 validation passed.
```

FTP to the controller at `10.10.10.2:21` timed out, so the new constants are
not yet active on the controller.

## Acceptance

1. Upload the revised `P100.macro`.
2. Run `G65 P113`.
3. Confirm the parked pen is centered on the embedded magnet.
4. Rotate the bed with the magnet under the lifted pen and confirm it remains
   centered.
5. If the error changes with angle, record the A0/A180 vectors because the
   residual is not a pure constant offset.

## Evidence

- `RPSW-20261025-003`
- `firmware/grblhal/macros/P100.macro`
- `tools/validate_homing_macro.py`
