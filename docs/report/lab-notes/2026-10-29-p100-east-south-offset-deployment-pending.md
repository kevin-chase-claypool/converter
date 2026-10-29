# Lab Note: 2026-10-29 - P100 east/south offset update pending deployment

## Objective

Correct the latest overshoot and set the final P100 registered position after
iterative east/west adjustments.

## Configuration

- Hardware: installed RP23CNC / `RP23U5XBB` V1.01 and production toolhead.
- Previous P100 correction: X `1.45 mm`, Y `1.01 mm`.
- First attempted movement: +2.3 mm machine X and -0.7 mm machine Y.
- Subsequent X corrections: -1.0 mm and -0.45 mm.
- Net movement from the prior `1.45 / 1.01` frame: +0.85 mm X and -0.7 mm Y.
- Controller endpoint: `10.10.10.2`, FTP port 21.

## Code, commands, and configuration used

P100's `G10 L20` write subtracts the correction values:

```text
G10 L20 P1 X[[#<sensor_to_pen_x> - #<axis_center_correction_x>]]
             Y[[#<sensor_to_pen_y> - #<axis_center_correction_y>]]
```

Increasing the correction moves the registered pen east/north; decreasing it
moves the pen west/south. Applied calculation:

```text
axis_center_correction_x = 3.75 - 1.00 - 0.45 = 2.30
axis_center_correction_y = 1.01 - 0.70 = 0.31
```

The unchanged sensor-to-pen vector is `(0.0, -29.4892)`, so the registration
write becomes:

```text
G10 L20 P1 X-2.30 Y-29.7992
```

Validation commands:

```powershell
python tools\validate_homing_macro.py
python tools\check_macros.py
python -m unittest software.tests.test_rotation_calibration -v
```

Reachability checks:

```powershell
Test-NetConnection 10.10.10.2 -Port 21 -InformationLevel Quiet
ping.exe -n 2 -w 2000 10.10.10.2
```

## Procedure

1. Update only `axis_center_correction_x/y`; keep `sensor_to_pen` unchanged.
2. Validate macro syntax and the pinned P100 safety contract.
3. Check controller reachability before attempting FTP deployment.
4. Do not rewrite the controller while the network is unavailable.

## Results

- Local P100 source now has X `2.30`, Y `0.31`.
- Local file: 15,469 bytes, SHA-256
  `5F938610621D94DEC3A293A62E37646810BD580B792A9C80105599FEEB7505C3`.
- P100/P115 safety validation passes.
- All 17 repository macros parse safely.
- All 20 rotation-calibration tests pass.
- Controller deployment did **not** occur: TCP port 21 returned `False`, and
  two pings to `10.10.10.2` timed out.

## Difficulties and corrective actions

The direct Ethernet controller is currently offline or disconnected. No FTP
upload was attempted after the failed connection check, so the controller
retains its previous P100 file.

## Interpretation

The required source change is complete and validated, but the physical
registered position will not move until the updated macro is uploaded and
`G65 P113` is run.

## Decisions and next action

- Restore the direct Ethernet link.
- Upload the validated `P100.macro` over binary FTP.
- Run `G65 P113`.
- Verify the parked pen moved 0.85 mm east and 0.7 mm south from the prior
  center-magnet observation.
- Rotate the bed under the lifted pen and confirm the indicated center remains
  stable.

The source change is recorded in `RPSW-20261029-001`.
