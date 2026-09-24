# Lab Note: 2026-09-24 - first integrated-firmware P113 magnetic registration

## Objective

Confirm that the **production** toolhead firmware - the integrated dual-core
build with `MAGNETIC_CALIBRATION_VALID = true`, not the bench handshake sketch -
completes the full `G65 P113` registration: arm/release/re-arm, the center
serpentine raster, the centroid approach, the two-footprint outer A scan, and
both deferred `G54` writes.

This closes the PENDING verification in `RPSW-20260924-001` and supplies the
measured `MPos`/`G54` record that E-18, M-08, and M-09 were waiting on.

## Configuration

- Hardware revisions: SparkFun Pro Micro RP2350 toolhead with the PC817C
  interface board; RP23CNC / `RP23U5XBB` V1.01.
- Wiring/pin map: RP23CNC `Aux 0` -> PC817C `J1.4`/U2 -> toolhead `GP28`;
  toolhead `GP27` -> PC817C `J1.6`/U3 -> RP23CNC `PROBE SIG`. See
  `WIRING_TABLE.md` rows `MAG-003`, `MAG-003A`, and `TH-001A-RT`.
- Firmware commit/build: toolhead `61549e1`
  (`firmware/pen_pressure/pro_micro_rp2350_toolhead`, supervised
  `MECHANICAL_PRELOAD_MODE = true`, `MAGNETIC_CALIBRATION_VALID = true`,
  `LIFT_REFERENCE_VALID = false`, `PEN_CLEAR_VALID = false`). RP23CNC macros
  at `61549e1` with `macros/P100.macro` and `macros/P113.macro` as committed.
- grblHAL settings: `$6=1`, `$16=1`, `$20=$40=1`, `$21=0`,
  `$110=$111=1500` mm/min, `$120=$121=500` mm/s^2, `$130=455.000` mm,
  `$131=446.000` mm.
- Converter settings/sample: none; this was a command-driven commissioning run.
- Instruments: none. Positions are controller-reported `MPos`; field
  magnitudes are toolhead-reported TMAG5273 milli-tesla values.

## Code, commands, and configuration used

```text
ioSender console (RP23CNC):
  G65 P113          production HOME + REGISTER wrapper
  ?                 status report; read the MPos field

Arduino IDE Serial Monitor (toolhead service UART):
  v                 toggle the 1 s live stream
  p                 one status snapshot
  c                 clear a latched fault
```

P100 Q0 constants in effect for this run:

```text
sensor_to_pen_x  = 0.0            scan_min_x = -280.0   scan_max_x = -180.0
sensor_to_pen_y  = -29.4892       scan_min_y = -266.0   scan_max_y = -166.0
row_pitch        = 5.0            scan_feed  = 2000.0 (installed cap 1500)
outer_machine_x  = -10.5          a_expected_spacing = 4320.0 +/- 15.0
```

## Procedure

1. Pen installed and lifted, no paper under the tip; center and outer bed
   magnets installed.
2. Toolhead powered and streaming. Confirmed `fault=none`, `lift_home=1`,
   `mag=DISARMED`, and `commission=[dir:1 pressure:1 lift:0 mag:1]`, which
   proves the gated integrated build was the one running.
3. Issued `G65 P113` from the ioSender console and let it run without further
   operator input. P113 issued M5, its settle dwell, the single physical
   `$H`, then `G65 P100 Q0`.
4. Captured the ioSender console and the toolhead live stream.

## Results

Completed with no alarm and no rejected validation:

```text
[MSG:P100 outer magnet registered as G54 A0]
[MSG:P100 center registered so G54 X0 Y0 is pen-at-center]
[MSG:P100 HOME + REGISTER complete]
[MSG:P113 HOME + REGISTER wrapper complete]
ok
```

### Center raster and centroid (M-08)

| Quantity | Value |
|---|---|
| Raster | 21 rows, 5 mm pitch, X `-280...-180`, Y `-266...-166` |
| TMAG centroid, machine `MPos` | X `-232.138`, Y `-219.475` |
| `G54` written | X `-232.136`, Y `-189.980`, Z `0.000`, A `5649.193` |
| Parked position after `G54 G0 X0 Y0 A0` | X `-232.138`, Y `-189.975`, A `5649.306` |

The 29.489 mm +Y park displacement from the centroid is the applied
`sensor_to_pen` offset and matches the macro constant, so the parked pen tip -
not the TMAG - is the point the `G54` origin names.

Operator confirmation, 2026-09-24: at the final `G54 G0 X0 Y0` park position
the pen tip was **perfectly centered over the center magnet**. This is the
physical counterpart to the numeric centroid and closes the M-08 acceptance
criterion for the automated path.

### Outer index (M-09)

TMAG held on the outer scan line at X `-10.500`, Y `-219.475` throughout:

| Footprint | Entry A | Exit A | Width | Center |
|---|---:|---:|---:|---:|
| First | `1264.951` | `1369.576` | `104.625` | `1317.2635` |
| Second | `5597.106` | `5701.281` | `104.175` | `5649.1935` |

- Measured center-to-center spacing `4331.930` A motor degrees against the
  `4320 +/- 15` gate: a `+11.930` degree deviation, i.e. 79.5% of the
  tolerance budget consumed.
- `G54 A0` was written at the second-pass center `5649.193`; the axis settled
  at `MPos` A `5649.306`, a `0.113` motor-degree display delta.
- Radial scan line length: bed center X `-232.138` to outer scan X `-10.500`,
  i.e. `221.638` mm (`8.726` in) against the nominal `8.9` in outer magnet
  radius.

### Magnetic path evidence (E-18), same session

From the toolhead service stream covering the arm/scan attempts:

- The arm cycled `DISARMED -> READY_ACK -> WAIT_REARM -> SCAN_ACTIVE ->
  DISARMED` on each `M65 P0`/`M64 P0` pair, so the two-phase handshake and the
  3 s re-arm window behaved as designed.
- TMAG detection crossed cleanly: `delta` `0.257 -> 3.117 -> 30.287 ->
  41.853` mT, with the `MAG_DETECTED` status bit (`0x000001ef`) set at the
  crossing, then returning to `0.019-0.092` mT far-field with the bit clear.
- `cs1238_rejects` stayed at `0` and CS1238 acquisition was suspended only
  while the verified-lifted magnetic scan was active, resuming on release.

## Difficulties and corrective actions

An earlier P113 attempt in the same session ended in a toolhead `mag=FAULT`
exactly `300,000` ms after `SCAN_ACTIVE` began. That matches
`MAG_MAX_ARM_TIME_MS` in `toolhead_config.h` exactly, so the arm watchdog -
not a `P100` validation - aborted it; `fault=none` in the same snapshots
confirms the pressure controller was healthy and the fault was magnetic-only.
In that attempt the raster took roughly 172 s just to first reach the magnet,
leaving very little of the 300 s window for the remainder of Q0.

The run recorded above completed inside the window. The window size and raster
duration remain a real robustness problem; see Risks.

## Interpretation

The production integrated firmware runs the whole P113 path end to end: the
GP28/GP27 handshake arms and releases correctly, the TMAG5273 threshold and
status bit track a real magnet, the raster produces a valid centroid, the
two-footprint A scan validates against the spacing gate, and both `G54` writes
land only after their own survey passes.

`G54 X0 Y0` consequently means pen-at-bed-center and `G54 A0` means the
locating angular index for this machine, both derived from magnet evidence
rather than from a manual visual alignment. This is a repeatable measured
result, not just a functional smoke test: the A spacing reproduced the earlier
2026-09-11 observation (`4331.818` vs `4331.930`, a `0.112` motor-degree
difference) and the X centroid reproduced to `0.013` mm.

## Decisions and next action

- `MAGNETIC_CALIBRATION_VALID` stays `true`. `LIFT_REFERENCE_VALID` and
  `PEN_CLEAR_VALID` are untouched by this run and remain `false`.
- `RPSW-20260924-001` moves `implemented -> verified`.
- The operator confirmed the parked pen tip perfectly centered over the center
  magnet at the final `G54 X0 Y0`, so the automated P100 Q0 registration now
  has the same physical acceptance the 2026-09-11 manual reference had. M-08
  and M-09 are accepted; no manual re-referencing step remains in the startup
  path.
- Open robustness items:
  1. The A spacing gate consumed 79.5% of its `+/- 15` degree budget and the
     last two independent measurements agree at about `+11.9`, so the gate has
     only ~3 degrees of margin. Either re-derive `a_expected_spacing` from
     measured evidence or widen the gate deliberately; do not keep a nominal
     `4320` that the installed hardware never produces.
  2. `MAG_MAX_ARM_TIME_MS = 300000` is too close to a full Q0 duration. Raise
     the watchdog or shorten the raster (row pitch, scan square, or feed)
     before relying on unattended `P113`.
- Next: run the first converter-generated plot on this registered frame.

## Related records

- Change note: `RPSW-20260924-001`.
- Current-state design: `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`.
- Test plan: E-18, M-08, M-09 in `docs/testing/TEST_PLAN.md`.
- Prior evidence: `docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`.
