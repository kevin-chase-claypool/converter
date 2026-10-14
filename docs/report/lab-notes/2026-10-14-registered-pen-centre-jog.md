# Lab Note: 2026-10-14 - Registered pen-centre jog (DRO measurement)

## Objective

Measure the residual registration offset after `G65 P113` by jogging the pen
tip exactly onto the centre magnet and reading the ioSender DRO, then convert
that jog into the P100 axis-centre correction constants.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01, bed ratio 12.03324 motor deg
  per bed deg (4331.9664 per revolution).
- Wiring/pin map: unchanged by this measurement.
- Firmware commit/build: the installed grblHAL candidate build used for the
  2026-10-13 centre tests; no firmware change.
- grblHAL settings: unchanged (`$113=15000`, `$111=8000`, `$121=1500` per the
  2026-10-01/13 sessions).
- Converter settings/sample: none; controller-side.
- Instruments: ioSender DRO (work position, G54); operator visual judgement of
  the bed-circle centre.

## Code, commands, and configuration used

```text
G65 P113          (HOME + REGISTER; parks the pen at G54 X0 Y0 A0)
(jog X/Y until the pen tip is on the bed-circle centre; read the DRO at the
 park and at the centred position)
```

DRO readings (ioSender, G54 work position):

```text
park:     X -0.005   Y 0.004   (Z 0.000, A 0.113)
centred:  X  1.195   Y 0.904   (pen tip exactly on the centre magnet)
```

The operator identified these two readings as the authoritative basis for the
update.

## Procedure

1. Run `G65 P113` and let it park.
2. Note the park DRO (work position).
3. Jog X/Y until the pen tip is exactly on the centre magnet, then keep that
   reading.

## Results

- Jog delta: +1.200 mm X (east), +0.900 mm Y (north).
- Applied: `#<axis_center_correction_x>` 1.25 -> 2.45,
  `#<axis_center_correction_y>` 0.0 -> 0.9; the registration write becomes
  `G10 L20 P1 X-2.45 Y-30.3892` at the centroid, so the parked `G54 X0 Y0`
  moves by the full jog.
- **Park confirmed (2026-10-14):** the revised macro was uploaded and
  `G65 P113` re-run; the operator reports the park now lands the pen centred on
  the centre magnet. Remaining acceptance: the magnet-under-pen rotation check
  or `samples/gcode/center-registration-check.gcode`.

## Difficulties and corrective actions

- The reading conflicts with the 2026-10-13/14 centre-test deltas (2.0/1.44 mm)
  by about 1 mm, and the G54 form of that earlier correction did not collapse
  the eight-angle tick bundle, so the residual is not yet established as a
  pure constant offset.

## Interpretation

Under the verified frame model (`origin = centroid - written`), the jog is the
distance the registered origin must move, so it adds to the axis-centre
correction. The pen-offset equivalent `(-1.200, -30.3892)` is within 0.3 mm of
the historical `-30.100` Y measurement; attribution between an off-axis centre
magnet and a pen/TMAG value error remains open.

## Decisions and next action

- Change note `RPSW-20261014-001`; the constants and their guards are updated.
- Next: upload the revised `P100.macro`, run `G65 P113`, then the
  magnet-under-pen rotation check (or `center-registration-check.gcode`); then
  plot and measure `samples/gcode/xy-scale-check.gcode` before trusting a full
  fix.
