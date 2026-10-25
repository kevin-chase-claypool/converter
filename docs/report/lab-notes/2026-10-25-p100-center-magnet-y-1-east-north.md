# Lab Note: 2026-10-25 - P100 center-magnet placement check

> Superseded by
> `2026-10-25-p100-center-magnet-north-1mm.md`: the final direction requires
> the pen to move 1 mm north, giving Y `+1.30`, not Y `-0.70`.

## Objective

Correct the P100 G54 registration so the physical pen tip lands at the center
of the bed's embedded center magnet after `G65 P113`.

## Configuration

- Hardware: installed RP23CNC/RP23U5XBB and production integrated toolhead.
- Previous P100 axis-center correction: X `+2.45 mm`, Y `+0.30 mm`.
- Wired and firmware state unchanged for this measurement.
- Measurement instrument: visual center-magnet placement under the pen tip.

## Procedure

1. Run `G65 P113` and let the controller complete registration.
2. With the pen in its registered `G54 X0 Y0` position, compare the pen tip
   against the embedded center magnet.
3. Record the residual direction and distance.
4. Convert the residual into a replacement P100 axis-center correction.

## Results

- The registered pen position was `1.000 mm` east and `1.000 mm` north of the
  embedded center magnet.
- The registered origin therefore needs to move 1 mm west and 1 mm south.
- Because `G10 L20` subtracts the correction constants, the replacement is:
  - X: `2.45 - 1.00 = 1.45`
  - Y: `0.30 - 1.00 = -0.70`
- No artwork offset, pen/TMAG value, or bed-compensation profile was changed.

## Software verification

```text
python tools\check_macros.py
All 17 macro(s) parse-safe.

python tools\validate_homing_macro.py
P100/P115 validation passed.
```

Repository P100 SHA-256:
`11DBE7A25408496B0A77B79EA0B7FAB76DF836B05A0783C32DBB515544E964A2`.

## Deployment status

FTP connection to the controller at `10.10.10.2:21` timed out before upload,
so the repository source is updated but the controller still has the previous
P100 file. Do not treat the new constants as active until the revised macro is
uploaded and `G65 P113` is repeated.

## Acceptance

1. Upload the revised `P100.macro`.
2. Run `G65 P113`.
3. Confirm the parked pen tip is centered over the embedded magnet.
4. Rotate the bed with the magnet directly under the lifted pen and require it
   to remain centered.
5. If the center error changes with bed angle, record the A0 and A180 vectors
   for the still-open magnet-versus-axis attribution.

## Evidence

- `RPSW-20261025-002`
- `firmware/grblhal/macros/P100.macro`
- `tools/validate_homing_macro.py`
