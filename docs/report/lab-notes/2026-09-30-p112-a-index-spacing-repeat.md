# Lab Note: 2026-09-30 - P112 outer A-index spacing repeat

## Objective

Re-measure the installed A-axis spacing for one bed revolution with the
non-registering `G65 P112` outer-index survey, to decide whether the repeatable
`+11.8` motor-degree deviation from the nominal 4320 is a stable effective
ratio or a one-off detection artifact. The measurement feeds the roadmap item
"Re-derive the outer A index spacing budget" and the 2026-09-30 converter ratio
change (`WSW-20260930-001`).

## Configuration

- RP23CNC/grblHAL as installed, `$103 = 4.44444`, hard limits on.
- Integrated toolhead firmware with the magnetic interface enabled; TMAG at the
  fixed installed height, center and outer bed magnets installed.
- Pen installed and lifted; no paper under the tip. Hand on the power cutoff.
- ioSender console, with `MPos` and `PRB` reports captured.

## Code, commands, and configuration used

```text
G65 P111        physical X/Y home
G65 P100 Q5     center-magnet raster, parks TMAG at the computed centroid
G65 P112        outer-index survey, no G54 write
```

G54 work offset in force during the run (from `WCO`):
`X -232.399, Y -195.169, A 21585.285`.

## Procedure

One `G65 P112` run was issued from the Q5 centroid with no intervening jog. The
macro drove the TMAG along +X to G53 `X -10.5` at `Y -225.725`, armed the
magnetic threshold, made two bounded `G38.3`/`G38.5` entry/exit captures, and
parked at the pass-two centre. The four probe reports were read from the
ioSender console.

## Results

| Probe | A (motor-deg) |
|---|---:|
| Pass 1 entry | 21529.373 |
| Pass 1 exit | 21635.123 |
| Pass 2 entry | 25861.976 |
| Pass 2 exit | 25966.826 |

- Footprint widths: `105.750` and `104.850` motor-degrees (gate: > 0 and
  <= 120).
- Footprint centres: `21582.248` and `25914.401`.
- **Center-to-center spacing: `4332.153` A motor-degrees per bed revolution.**
- Against the gate in force at the time (`4320 +/- 15`) that is a `+12.153`
  deviation, consuming 81% of the tolerance; the macro completed and parked at
  `MPos:-10.500,-225.725,0.000,25914.402`.

Three independent within-run surveys now agree:

| Date | Spacing | Deviation | Source |
|---|---:|---:|---|
| 2026-09-11 | 4331.818 | +11.818 | `P112`, two footprints |
| 2026-09-24 | 4331.930 | +11.930 | `P100 Q0` outer stage |
| 2026-09-30 | 4332.153 | +12.153 | this note, `P112` |

Mean `4331.967`, total spread `0.335` motor-degrees.

Cross-check from the stored work offset: the G54 A offset in force
(`21585.285`, written at the previous registration's pass-two centre) lies
`3.037` motor-degrees from this run's first-pass centre (`21582.248`). That is
0.25 bed-degrees, about 0.8 mm at r = 185 mm, and it mixes the earlier
registration's different scan line (`Y -219.475` on 2026-09-24 versus
`Y -225.725` today), so it is a session-scatter estimate, not a spacing
measurement.

## Difficulties and corrective actions

The macro validates the spacing but does not print its value (its messages are
literals). The number above was reconstructed from the four `PRB` reports using
the macro's own definition: `spacing = center2 - center1` with
`center = (entry + exit) / 2` on the A component. That is the same source the
2026-09-24 table used.

## Interpretation

- The spacing is measured as the difference between two identical observations
  of the same magnet on the same scan line one revolution apart, so any
  constant detection offset cancels. The three runs repeat to 0.335
  motor-degrees total spread.
- A wrong `$103`, microstep setting, or motor step angle would scale the count
  by a factor near 2 or 0.5, not 1.0028. The measurement is therefore an
  effective mechanical ratio, not an electronics scale error.
- Effective ratio: `4331.967 / 360 = 12.03324` motor-degrees per bed degree,
  i.e. `+0.277%` over the nominal 12:1.
- Consequence for the 2026-09-30 mandala print (`mom.gcode`): its 341.3 degrees
  of accumulated bed winding put the drawn geometry up to 0.95 bed-degrees from
  where the converter thought it was, about 2.5 mm at r = 150 mm and 3.0 mm at
  r = 185 mm. That matches the ghosting seen in that print.

## Decisions and next action

1. Converter `theta_drive_ratio` set to `12.03324`; the radius-aware A feed
   constant becomes `4331.97` motor-degrees per bed revolution automatically.
2. P100/P112/P103 gate re-derived to `4332 +/- 10` (spread 0.335 justifies a
   tight band; the old `4320 +/- 15` is superseded).
3. Not yet done: the magnet-independent pointer check (mark the rim, command
   `G91 G0 A4320`, expect a ~1 degree shortfall) and a first print with the new
   ratio. Existing G-code files were emitted with the old ratio and must be
   regenerated before reprinting.
