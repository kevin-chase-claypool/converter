# Lab Note: 2026-10-25 - P100 final Y 1.30 deployment

## Objective

Apply the second 1 mm northward center correction requested after the P100
Y `0.30` macro tested almost centered.

## Configuration

- Hardware: installed RP23U5XBB and production integrated toolhead.
- Previous tested correction: X `1.45 mm`, Y `0.30 mm`.
- Required additional movement: 1.000 mm north.
- Controller FTP: `10.10.10.2:21`.

## Procedure

1. Increase P100 Y by the requested 1 mm.
2. Keep X unchanged.
3. Run macro syntax and safety validators.
4. Upload `P100.macro` over binary FTP.
5. Verify the remote file size.

## Results

- Final values:

```text
#<axis_center_correction_x> = 1.45
#<axis_center_correction_y> = 1.3
```

- Registration write:

```text
G10 L20 P1 X-1.45 Y-30.7892
```

- Local/remote file size: 15,228 bytes.
- FTP upload response: `226 Closing data connection`.
- Controller listing reports the expected remote `P100.macro` size.
- Local SHA-256:
  `C3AE0A5B6E8112A93CE09855437A423834618578663C4D34D2B61849CC7AECEB`.

## Verification

```text
python tools\check_macros.py
All 17 macro(s) parse-safe.

python tools\validate_homing_macro.py
P100/P115 validation passed.
```

## Acceptance

1. Run `G65 P113`.
2. Confirm the parked pen is centered on the embedded magnet.
3. Rotate the bed with the magnet under the lifted pen and confirm it remains
   centered.

## Evidence

- `RPSW-20261025-005`
- `firmware/grblhal/macros/P100.macro`
- `firmware/grblhal/macros/controller-manifest-2026-10-25.txt`
