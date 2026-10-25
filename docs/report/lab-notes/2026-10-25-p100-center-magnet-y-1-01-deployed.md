# Lab Note: 2026-10-25 - P100 final Y 1.01 deployment

## Objective

Apply the precise 0.29 mm south correction after the Y `1.30` center-magnet
test landed almost centered.

## Configuration

- Hardware: installed RP23U5XBB and production integrated toolhead.
- Previous tested correction: X `1.45 mm`, Y `1.30 mm`.
- Required additional movement: 0.29 mm south in machine Y.
- Controller FTP: `10.10.10.2:21`.

## Procedure

1. Subtract 0.29 mm from the P100 Y correction.
2. Keep X unchanged.
3. Run macro syntax and safety validators.
4. Upload the macro over binary FTP.
5. Verify the remote file size.

## Results

- Final values:

```text
#<axis_center_correction_x> = 1.45
#<axis_center_correction_y> = 1.01
```

- Registration write:

```text
G10 L20 P1 X-1.45 Y-30.4992
```

- Local/remote file size: 15,244 bytes.
- FTP upload response: `226 Closing data connection`.
- Local SHA-256:
  `05C52C0C335D2F322B5699D793182DB1F967879EC811E9732845C576C13A73EF`.

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

- `RPSW-20261025-006`
- `firmware/grblhal/macros/P100.macro`
- `firmware/grblhal/macros/controller-manifest-2026-10-25.txt`
