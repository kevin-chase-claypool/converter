# Lab Note: 2026-11-01 - M-13 Xθ/Yθ equidistant Wave-row audit

## Objective

Determine why the new equidistant Wave screen holds row pitch with XY-only
motion but not with the rotating bed, and verify a shared ascending/descending
row schedule before another physical print.

## Configuration

- Hardware revisions: RP23CNC XYZ gantry with rotating A bed; no mechanical
  change was made during this software audit.
- Wiring/pin map: unchanged.
- Firmware commit/build: geometry audit only; no machine motion was commanded.
- grblHAL settings: default theta ratio from the converter settings,
  `12.03324` A motor degrees per bed degree.
- Converter settings: `waves_even`, `4.000 mm` effective pitch, `0.80 mm` pen,
  Xθ/Yθ (`theta_mode = optimized`), center hold `0`, path tolerance `0.050 mm`,
  64 mm synthetic page.
- Row orders: ascending and descending.
- Screen angles: 0°, 15°, 45°, and 75°.
- Bed compensation: disabled for the isolated interpolation test; the same
  row-lock logic remains active separately in CMYK output.
- Instruments: converter regression and decoded emitted G-code samples.

The operator's physical context was an XY-only Wave print with acceptable row
equidistance and a request to obtain the same behavior under Xθ/Yθ with
descending serpentine rows.

## Code, commands, and configuration used

The audit was run at base commit `cf479d8` plus the rotating-row changes in
this session:

```powershell
py -3 -m unittest software.tests.test_wave_x_theta_rows -v
py -3 -m unittest discover -s software\tests
py -3 tools\check_cmyk_wave_spacing.py `
  samples\gcode\Ben2\PXL_20201128_211515508-cmyk-set.json
```

## Procedure

1. Generate the same equidistant Wave lattice at each CMYK screen angle.
2. Plan it once as XY-only and once as Xθ/Yθ.
3. Parse the emitted `X/Y/A` moves and sample the controller's linear
   interpolation between endpoints.
4. Reverse the commanded A rotation to recover paper-space coordinates.
5. At 81 columns, measure adjacent row gaps and compare their spread.
6. Implement a shared angle schedule and spacing-aware subdivision.
7. Repeat at all four angles in ascending and descending row order.

## Results

The original XY-only gap spread was `0.0001 mm`; the independent Xθ/Yθ plans
spread to `0.06437 mm`. Source geometry was therefore correct, but the rotating
path changed it.

After the shared schedule:

| Screen angle | Minimum | Maximum | Spread | A sweep |
|---:|---:|---:|---:|---:|
| `0°` | `3.94867 mm` | `3.94931 mm` | `0.000638 mm` | `53.50°` |
| `15°` | `3.94690 mm` | `3.94929 mm` | `0.002383 mm` | `80.35°` |
| `45°` | `3.94725 mm` | `3.94922 mm` | `0.001970 mm` | `61.15°` |
| `75°` | `3.94716 mm` | `3.94932 mm` | `0.002153 mm` | `52.62°` |

The nominal deviation from 4.000 mm before the rotating move is the screen's
paper-space sampling/cropping boundary; the invariant under test is the gap
spread, not a recalibration of the requested pitch.

The synthetic program contains `1,824` emitted `G1` blocks before the spacing
subdivision and `2,735-2,982` after it, depending on screen angle. Both row
orders preserve the expected ascending or descending contour sequence.

An end-to-end synthetic four-ink set through
`check_cmyk_wave_spacing.py` reports `0.002743`, `0.002287`, `0.000684`, and
`0.001968 mm` for cyan/magenta/yellow/black. The checker samples the linear
X/Y/A intervals and applies the same `0.005 mm` spread gate used by the
preserved XY-only Ben2 set.

## Difficulties and corrective actions

- The first implementation retained independent per-row A schedules. It kept
  row order but failed the gap test.
- A shared schedule with a `0.002 mm` interpolation budget still failed at 45°
  and 75° with `0.0081-0.0086 mm` spread.
- Tightening the geometric interpolation headroom to `0.0005 mm` brought all
  angles below the `0.005 mm` acceptance bound.

## Interpretation

Exact row pitch in Xθ/Yθ requires both conditions: every parallel row must use
the same bed angle at the same along-row coordinate, and each linear
X/Y/A command interval must be small enough that interpolation cannot collapse
the row separation. Row-order selection alone is insufficient.

## Decisions and next action

Keep the shared angle lock tied to the existing equidistant-row spacing guard.
The next physical step is a four-pass Xθ/Yθ descending print using the current
bed-compensation mesh. Save the set, run `check_cmyk_wave_spacing.py`, measure
elapsed time, and compare row quality against the XY-only control. See
`WSW-20261101-007`.
