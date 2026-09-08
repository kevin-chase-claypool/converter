# Converter house-and-sun run with guarded soft limits - 2026-09-07

## Objective

Record the current X/Y soft-limit envelope, refreshed temporary work reference,
and a pen-free converter-generated X/Y/A execution and return check.

## Configuration

- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- X/Y home: east/south normally-closed switches; successful combined `$H` ended
  at `MPos:-10.000,-436.000,0.000,0.000` with `H:1,3`.
- Current X/Y calibration and working motion settings: `$100=80.00000`,
  `$101=80.00000` steps/mm; `$110=$111=1500` mm/min; and
  `$120=$121=500` mm/sec^2. The operator rechecked X by caliper and selected
  `$100=80.00000`; the earlier `79.71303` value is superseded.
- Guarded X/Y software envelope: `$20=1`, `$40=1`, `$130=455.000` mm, and
  `$131=446.000` mm. These are conservative observed-safe distances, not
  physical hard-switch locations. `$21=0`; hard-limit alarms remain disabled.
- A: `$103=4.44444` step/motor-degree, `$113=80000` motor-deg/min,
  `$123=6000` motor-deg/sec^2, and `$133=0` (continuous bed).
- Temporary G54 reference after the new Y envelope: the pen axis was returned
  to the known center location with `G53 G0 X-232.900 Y-191.200`, then
  `G10 L20 P1 X0 Y0` set `WCO:-232.900,-191.200,0.000,0.000`.
- A was previously manually set to G54 `A0`; this is a temporary visual angular
  reference, not M-09 magnetic index registration.
- Program: `samples/svg/kindergarten-house-sun.gcode`, generated pen-free. Its
  header is `G21 G90 G94 G17 G54`; it contains X/Y/A moves and no `M3` or `M5`.

## Procedure

1. Homed X/Y with `$H` after enabling the guarded X/Y software envelope.
2. Re-established the temporary center reference using the machine-coordinate
   center above and set G54 X/Y zero at the pen axis.
3. Streamed the converter-generated house-and-sun program without the pen or
   toolhead commands.
4. After program completion, returned with:

   ```gcode
   G90
   G54
   G0 X0 Y0 A0
   ```

## Results

- Homing completed without an alarm and reported X/Y homed (`H:1,3`).
- The converter-generated program completed.
- The final G54 return put the pen axis exactly back on the manually established
  bed-center mark, and the bed returned exactly to its manually established A0
  reference.
- No motion problem or skipped-step symptom was reported.
- Disposition: **pen-free converter-generated X/Y/A execution and reference
  return passed for this sample.**

## Limits and next action

- This does not measure actual runtime against preview time, verify all
  inner/middle/outer-radius geometry, or test a soft-limit rejection at each
  boundary. It also does not qualify a pen, M3/M5, P100, magnetic registration,
  or production drawing.
- Keep the envelope conservative until controlled near-boundary rejection and
  recovery checks are recorded. P100 must replace this temporary G54 reference
  before production drawing.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-03, M-06, and M-07
- [`HOMING_AND_MAGNETIC_CALIBRATION.md`](../../../firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md)
- [`kindergarten-house-sun.svg`](../../../samples/svg/kindergarten-house-sun.svg)
