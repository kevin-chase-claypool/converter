# Lab Note: 2026-09-30 - mom print reach-fit verification

## Objective

The 2026-09-29 engineering-log entry predicted that the 189.81 mm `mom.gcode`
artwork "will be clipped" by the new 185.0 mm reach cap, and a later diagnosis
repeated that the printed fan tips were cut off. Verify against the two files
that actually exist whether the printed program lost outer artwork.

## Configuration

- `samples/gcode/mom.gcode` (2026-09-29 12:44) - the regenerated program that
  was printed and photographed on 2026-09-30.
- `samples/gcode/mom_resume_56877.gcode` (2026-09-29 12:21) - a resume cut from
  the earlier, unfitted generation, so it preserves the artwork's pre-fit
  geometry at its original scale.
- No source SVG for this artwork exists on the machine.

## Code, commands, and configuration used

Both files were parsed in bed-local coordinates, `(u,v) = R(-A/12) * (X,Y)`,
using each line's own `A` value. No machine was moved and no setting was
changed; this is a file comparison only.

## Procedure

For every `G1` point in both files, compute the bed-local coordinates, then
compare the bounding box, the per-axis span ratio (a uniform scale test), the
bbox centre (a placement-offset test), the maximum radius from the bed centre,
and the number of points and contour endpoints lying on the 185.0 mm cap.
Whole-pattern registration over translation sampled at scales 0.94-1.01 was
used as a cross-check.

## Results

| Quantity | resume (pre-fit) | `mom.gcode` (printed) |
|---|---|---|
| Bounding box | 376.814 x 376.819 mm, centred (0.000, 0.000) | 363.217 x 363.222 mm, centred (1.570, -1.590) |
| Span ratio | 1.0 (reference) | 0.96392 in both axes |
| Max radius from bed centre | 189.812 mm | 185.0000 mm = the cap |
| G1 points beyond 185 mm | 15,987 | 0 (7 points within 0.002 mm of the cap) |
| Contour endpoints on the cap | 0 | 8 |

Whole-pattern registration peaks at 0.965 with a 0.66 correlation and falls to
0.19 at scale 1.0, consistent with the bbox ratio.

## Difficulties and corrective actions

An earlier read of this pair assumed the 185.0001 mm maximum meant clipping at
scale 1.0. The per-axis span ratio and the bbox centre show a uniform 0.96392
scale plus a (1.570, -1.590) mm shift instead, which the point-level cap counts
confirm: a clipped copy would have kept the inner geometry at scale 1.0 and
left many contour endpoints on the cap circle.

## Interpretation

- The printed program is the **complete artwork, uniformly scaled to 96.4% and
  shifted about 2.2 mm**, produced by the default Fill-bed auto-fit plus a small
  placement offset. It is not a clipped copy.
- The reach cap removed essentially nothing: the outermost point sits exactly on
  185.000 mm and only eight contour endpoints lie on that circle.
- The 2026-09-29 prediction was therefore not borne out. The fit rescales before
  the planner clips, so an over-size artwork is reduced rather than truncated.
- Consequence: the print is complete but 3.6% smaller than the SVG's nominal
  size. The +Y work limit is 185.27 mm from the bed centre, so a 189.81 mm
  artwork cannot be printed 1:1 while centred on the bed. A 1:1 print would need
  envelope-aware bed-angle planning - choosing the bed angle so that
  out-of-circle points are drawn toward the roomier -Y and +X directions - which
  the current r-theta planner does not do.

## Evidence boundary

The two G-code files share a generation lineage but only the resume preserves
the pre-fit geometry; there is no independent copy of the source artwork, and
the photograph was not used for measurement.
