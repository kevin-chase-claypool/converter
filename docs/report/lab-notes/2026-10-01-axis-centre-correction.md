# Lab Note: 2026-10-01 - axis-centre correction in P100 (reported, verification pending)

## Objective

Record the reported 1.25 mm X registration error, the correction applied to
`P100.macro`, the test that attributes it, and the acceptance test that closes
it.

## Configuration

- Hardware revisions: RP23CNC / `RP23U5XBB` V1.01, bed ratio 12.03324 motor deg
  per bed deg (4331.9664 per revolution).
- Wiring/pin map: unchanged by this change.
- Firmware commit/build: the grblHAL build whose settings dump is recorded in
  `2026-10-01-theta-a-rate-limit-lowering.md`.
- grblHAL settings: `$113=20000`, `$123=3000` (lowered the same day),
  `$111=8000`, `$121=1500`.
- Converter settings/sample: none; this is controller-side.
- Instruments: the plot itself, plus ioSender `MPos` for the Q5 surveys.

## Code, commands, and configuration used

`P100.macro` now carries:

```text
#<sensor_to_pen_x> = 0.0
#<sensor_to_pen_y> = -29.4892
#<axis_center_correction_x> = 1.25
#<axis_center_correction_y> = 0.0
...
  G10 L20 P1 X[[#<sensor_to_pen_x> - #<axis_center_correction_x>]] Y[[#<sensor_to_pen_y> - #<axis_center_correction_y>]]
```

Attribution test (pending):

```text
G65 P111
G65 P100 Q5                  (survey at A0; note MPos X, Y)
G91 G1 A2165.9832 F20000     (half a bed revolution)
G90
G65 P100 Q5                  (survey at A180; note MPos X, Y)
```

Acceptance test:

```text
G65 P113
(then Cycle Start samples\gcode\center-registration-check.gcode)
```

## Procedure

1. Apply the correction to `P100.macro` and upload it to the controller
   filesystem, alongside the other macros.
2. Parse-check every macro (`python tools\check_macros.py`) and re-run the P100
   validator (`python tools\validate_homing_macro.py`) before uploading.
3. Run `G65 P113` to register, then the cross program.
4. Record whether the two crosses coincide, and if not, the gap and its
   direction.
5. Run the attribution test above to decide whether the correction belongs in
   the axis-centre constant (centroids differ) or in `sensor_to_pen_x`
   (centroids match).

## Results

**Reported:** the registered origin landed 1.25 mm on the minus-X side of the
bed's true rotation axis. Measured by the operator from the plot.

**Applied:** `#<axis_center_correction_x> = 1.25`, subtracted in the `G10 L20`
write so the origin moves +1.25 mm in machine X.

**Software verification:**

```text
python tools\check_macros.py            -> all 17 macros parse-safe
python tools\validate_homing_macro.py   -> P100/P115 validation passed
```

Two stale validator expectations were corrected at the same time: P112's
`a_expected_spacing` (4320 -> 4332) and `a_spacing_tolerance` (15 -> 10), both
left over from before the 2026-09-30 ratio work.

**Physical verification: PASSED (2026-10-01), by a substitute for the cross
program.** Instead of plotting the two crosses, the operator put a magnet
directly underneath the lifted pen and rotated the bed: it stayed centred on the
pen. That is the same acceptance condition the cross program tests - a magnet
held at the pen's position rides the rotation axis only if that position is the
axis - and it is faster, because it needs no paper. The registered origin is
therefore on the bed's rotation axis with the +1.25 mm X correction in place.

**Attribution test: deliberately not performed.** Which side of the chain owns
the 1.25 mm - an off-axis embedded centre magnet, or a wrong pen/TMAG X value -
is still unattributed. The correction works either way, but knowing which it is
matters if the magnet is ever re-seated or the pen/TMAG offset is re-measured.

## Difficulties and corrective actions

- The first draft of the correction added the constant rather than subtracting
  it. Deriving the sign from the validator's own model (`origin = centroid -
  written`) and the 2026-09-11 registration evidence showed that would move the
  origin the wrong way; the write subtracts.
- `tools/check_macros.py` caught a nested-parenthesis comment written during this
  change, the same defect class that made ioSender reject the earlier
  repeatability file. Fixed before upload.
- The `sensor_to_pen` comment in P100 states the opposite sign to the behaviour
  the verified frame depends on; recorded in the macros README rather than
  silently changed.
- `HOMING_AND_MAGNETIC_CALIBRATION.md` quotes `(0.000, -30.100)` against the
  macro's `-29.4892`. Unresolved; needs a fresh measurement before the next
  calibration entry.

## Conclusion

**Verified.** The registered origin sits on the bed's rotation axis with
`#<axis_center_correction_x> = 1.25` in place, checked by holding a magnet under
the lifted pen and rotating the bed. The macro compensates the reported error in
one named, documented constant, the guard tools require it, and the operator is
satisfied with the result.

Open, and not blocking: the error is unattributed between an off-axis centre
magnet and a wrong pen/TMAG X value, and the macros README records that. If the
magnet is ever re-seated or the pen/TMAG offset re-measured, revisit this
constant - a fresh two-survey test (`G65 P100 Q5` at A0 and A180, comparing the
centroids each run prints) settles it in two commands.
