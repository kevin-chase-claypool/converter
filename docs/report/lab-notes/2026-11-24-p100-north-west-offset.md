# Lab Note: 2026-11-24 - P100 north/west registration offset

## Objective

Encode the operator-reported correction from another P100 `HOME + REGISTER`
result: move the registered pen 1.20 mm north and 1.000 mm west.

## Configuration

- Hardware revisions: installed RP23CNC / `RP23U5XBB` V1.01 and production
  integrated toolhead.
- Wiring/pin map: unchanged from the verified P100/P113 path.
- Firmware commit/build: repository baseline `4c4896e` plus this local P100
  source revision.
- grblHAL settings: unchanged.
- Converter settings/sample: unchanged; no artwork or bed-compensation offset
  was modified.
- Instruments: operator visual comparison after `G65 P113`; no DRO delta was
  supplied.
- Controller endpoint: `10.10.10.2`, FTP port 21 and Telnet port 23.

## Code, commands, and configuration used

```text
#<sensor_to_pen_x> = 0.0
#<sensor_to_pen_y> = -29.4892
#<axis_center_correction_x> = 1.30
#<axis_center_correction_y> = 1.51
G10 L20 P1 X[[#<sensor_to_pen_x> - #<axis_center_correction_x>]] Y[[#<sensor_to_pen_y> - #<axis_center_correction_y>]]
```

The resulting registration write is:

```text
G10 L20 P1 X-1.30 Y-30.9992
```

Validation commands:

```powershell
python tools\validate_homing_macro.py
python tools\check_macros.py
```

Reachability check:

```powershell
Test-NetConnection 10.10.10.2 -Port 21 -InformationLevel Quiet
Test-NetConnection 10.10.10.2 -Port 23 -InformationLevel Quiet
```

## Procedure

1. Treat the latest tracked P100 source frame as X `2.30`, Y `0.31`.
2. Subtract the requested 1.000 mm west movement from X.
3. Add the requested 1.20 mm north movement to Y.
4. Keep `sensor_to_pen` unchanged.
5. Validate macro syntax and the pinned P100 safety contract.
6. Check the controller before uploading.

## Results

- Required movement: 1.20 mm north and 1.000 mm west.
- Previous source values: X `2.30`, Y `0.31`.
- New values: X `1.30`, Y `1.51`.
- P100 file size: 15,819 bytes.
- P100 SHA-256:
  `DABBA2E165B02A7752E1510C330DFDE0D1B9105BBAB3C31E628B5CE554C8AA8F`.
- `validate_homing_macro.py` passed.
- All 17 repository macros passed `check_macros.py`.
- Both controller ports returned `False`; no upload or remote listing occurred.

## Difficulties and corrective actions

The controller was not reachable, so the active `P100.macro` could not be
compared with the latest tracked `2.30 / 0.31` source. The local change was
therefore calculated from that tracked frame and explicitly records the
assumption. The corrective action is to restore controller connectivity,
verify or replace the remote file with this complete 15,819-byte revision, and
then perform the physical check.

No DRO values accompanied the operator observation, so this note preserves the
requested movement but does not claim an instrument-level residual.

## Interpretation

The source now encodes the requested north/west translation while preserving
the measured TMAG-to-pen geometry and the single-owner registration contract.
It does not establish that the physical machine is centered until the updated
macro is active.

## Decisions and next action

1. Restore the direct Ethernet connection to `10.10.10.2:21`.
2. Verify the remote base or upload this complete P100 revision.
3. Run `G65 P113`.
4. Confirm the pen is centered over the embedded magnet.
5. Rotate the bed under the lifted pen and record A0/A180 vectors if any
   residual remains.

Evidence links:

- [M-08 registration test](../../testing/TEST_PLAN.md)
- [Change note](../../changes/rp23cnc-software/2026/2026-11-24-p100-north-1-2-west-1-0.md)
- [Engineering-log event](../../project/ENGINEERING_LOG.md#elog-20261124-p100-north-west-offset)
- [Current P100 source](../../../firmware/grblhal/macros/P100.macro)
