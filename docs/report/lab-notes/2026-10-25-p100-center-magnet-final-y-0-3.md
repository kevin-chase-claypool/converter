# Lab Note: 2026-10-25 - Final P100 center correction Y 0.30

> Superseded by `2026-10-25-p100-center-magnet-y-1-3-deployed.md`: Y `0.30`
> still left the pen approximately 1 mm south, so the final deployed Y is
> `1.30`.

## Objective

Finalize the P100 center correction after observing that the currently
deployed interim macro left the pen 1 mm south of the required magnet-center
position.

## Configuration

- Hardware: installed RP23CNC/RP23U5XBB and production integrated toolhead.
- Deployed interim P100 source: X `1.45 mm`, Y `-0.70 mm`; remote listing
  size 15,218 bytes matched the interim repository source.
- Required movement: 1.000 mm north in machine Y.
- Center reference: embedded magnet under the pen.

## Procedure

1. Observe the pen-center error after the interim macro.
2. Record the required movement direction and distance.
3. Add the movement to the currently deployed P100 correction.
4. Validate the resulting macro.

## Results

- Required Y movement: `+1.000 mm` north.
- Final Y correction:

```text
-0.70 + 1.00 = +0.30 mm
```

- Final X correction remains `+1.45 mm`.
- Final registration write:

```text
G10 L20 P1 X-1.45 Y-29.7892
```

## Verification

```text
python tools\check_macros.py
All 17 macro(s) parse-safe.

python tools\validate_homing_macro.py
P100/P115 validation passed.
```

## Acceptance

1. Upload the final `P100.macro`.
2. Run `G65 P113`.
3. Confirm the pen parks centered on the embedded magnet.
4. Rotate the bed with the magnet under the lifted pen and confirm it remains
   centered.

## Evidence

- `RPSW-20261025-004`
- `firmware/grblhal/macros/P100.macro`
- `tools/validate_homing_macro.py`
