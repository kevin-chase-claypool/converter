# Host software — SVG → G-code converter

Converts `.svg` artwork into `.gcode` for the XY + rotating-bed (theta) machine,
with a live preview of the simulated machine motion.

- `qt_svg_to_gcode.pyw` — the primary app: PySide6 + OpenGL preview, playback,
  command list, and all conversion settings in one window.
- `converter_core/` — the conversion engine split by responsibility:
  settings, SVG geometry, kinematics/planning, and G-code/preview move emission.
- `svg_to_gcode.pyw` — a compatibility shim for older imports and simple
  `input.svg output.gcode` command-line conversion.

## Run

```powershell
python qt_svg_to_gcode.pyw
```

or double-click `..\converter.bat` from the repo root. Runtime errors are written
to `qt_debug.log` in this folder.

Requires `PySide6` (`pip install PySide6`).

## What it emits

- `G21` (mm), `G90` (absolute), `G94` (units/minute feed), `G17` (XY plane),
  and `G54` (the registered work-coordinate frame)
- `G0` travel moves (pen up), `G1` draw moves (pen down)
- `X Y` in mm in the machine's active work-coordinate frame; `A` =
  **motor-shaft degrees** (already multiplied by `Theta ratio`)
- `M5` / `M3` pen up / down by default. `Z` moves are available only when
  **Use Z axis** is deliberately enabled; do not enable it for this machine,
  whose controller's Z slot is unwired. M3/M5 moves include a
  `G4` settle dwell after each (from `Pen cycle ms`) for the firmware handshake
- `M2` at end

The converter normalizes the clipped SVG around its geometric center before
planning. That center is emitted as `G54 X0 Y0`, matching the pen-at-bed-center
frame registered by P100 (or the narrowly scoped temporary commissioning
reference). The final NE park target is on the configured drawable circle, not
outside it on a diagonal.

The authoritative host-to-controller contract is
[`../docs/integration/INTERFACES.md`](../docs/integration/INTERFACES.md).

## Radius-aware A-axis feed

The converter must not treat the A-axis portion of `F` as a fixed bed-surface
speed. Because `A` is emitted in motor-shaft degrees and the bed reduction is
12:1, the A rate required for a target tangential pen speed depends on the
pen's instantaneous radius from the bed center:

```text
A_feed_motor_deg/min = (4320 × tangential_speed_mm/min) / (2π × radius_mm)
```

`Feed rate` remains the requested maximum X/Y component speed. The additional
**Theta tangential speed mm/min** setting is the requested bed-surface speed
for draw segments that include A motion. For each segment, the converter uses
the average endpoint radius, limits the requested A rate using the installed
RP23CNC profile (`$113 = 80000` motor-deg/min and `$123 = 6000`
motor-deg/s²), and derives one coordinated `F` from the longer X/Y or A
component duration. X/Y-only output remains unchanged.

At the exact bed center, rotation has zero tangential effect. The converter
therefore uses the capped angular move required by the theta plan without
dividing by zero and reports zero achieved tangential speed. The acceleration
limit is a conservative rest-to-rest segment bound; grblHAL can carry speed
through adjacent blocks, so M-06 hardware validation is still required before
relying on estimated execution time at high speed.

Preview draw moves use this same planner and retain the resulting feed, radius,
achieved tangential speed, and limiting reason in their move data. Generated
G-code and preview blocks therefore agree. Unit tests cover inverse-radius
rates, forward/reverse motion, both A limits, center handling, unchanged
X/Y-only output, and preview/G-code parity.

## Settings groups (Qt app)

- **Geometry** — scale, tolerance, Flip Y, and pen-stroke compensation.
- **Shading** — fill spacing/angle/pattern, shade levels/angle step, raster shading, and
  raster sampling resolution.
- **Motion** — draw/feed rate and travel rate. Values that cannot describe a
  meaningful X/Y/A program (for example, zero feed, a nonpositive theta ratio,
  an invalid A-axis name, or a bed margin that leaves no drawable area) are
  rejected before preview or save.
- **Theta kinematics** — theta axis/ratio/resolver/cost settings (`Theta ratio`
  defaults to 12 for the 60T→720T pulley pair).
  - **Theta tangential speed mm/min** is the requested surface speed caused by
    A-axis bed rotation during drawing. It does not change X/Y-only output.
- **Pen** — Z heights, pen cycle, pen up/down commands, and Use Z.
  - **Curve round bias** (`round_bias`, default 0.05) trades lowest-cost motion vs.
    well-rounded curves. `0` = pick the cheapest theta per segment (tends to
    axis-lock, flatter curves); higher values bias theta toward the path tangent so
    the bed rotation rounds curves (≈`tangent` mode at large values). Straights stay
    straight at any value.
  - **Theta resolver** (`theta_resolver`, default `rtheta`) uses a per-segment
    r-theta solve for `x_theta` and `y_theta`, scores both coordinated moves, and
    emits the cheaper axis choice. `dp` and `greedy` remain available as fallback
    experiments.
  - **Smoothness factor** (`smoothness_factor`, default 1.0) controls the speed vs.
    theta-smoothing trade. Lower it below `1.0` to reduce tangent tracking, reduce
    the final theta smoothing window, and expose hold-steady DP candidates for
    shorter rotation-heavy jobs. Use broad values such as `0.75`, `0.5`, or `0.25`;
    `0` is the fastest / least-smoothed setting.
  - **Theta smooth** (`theta_smooth_window`, default 2) moving-average half-window
    applied to the per-contour bed-orientation sequence. Removes bed jitter / erratic
    axis-locking; `0` disables it. Does not change the drawn shape — only how the bed
    is oriented while drawing.
- **Preview settings** — playback speed (visualization only), bed diameter/margin, pen stroke
  width, and three preview colors: **Undrawn** (artwork not yet drawn), **Drawn**
  (the drawn portion / final color), and **Motion** (active move + toolpath).
  The fixed pen-tip/contact footprint is a high-contrast green square so it
  remains distinct from the artwork, motion path, and crosshair.
- Pressing **Preview** shows the current build stage, percentage, and elapsed
  time. SVG parsing, motion planning, and clipping run in the background so the
  window remains responsive. The expensive contour/theta plan is built once and
  shared by the preview and complete command-list generation. Preview and Save
  G-code are temporarily disabled until that shared data is ready.
- Press **Cancel** during preview generation to stop an unexpectedly large job.
  Cancellation safely unwinds at geometry/planning checkpoints and keeps the
  last completed preview visible.
- The command list is the complete generated G-code program, including modal
  setup, M3/M5 commands, G4 dwell lines, comments, and M2. It is not a
  shortened preview-only command list.
- The controller-time estimate uses emitted draw-feed plans and configured pen
  dwell durations. Its **Motion estimate scale** is display-only: the current
  default `0.467368` comes from the pen-free M-06 radius sweep (`75.05 s`
  observed / `160.58 s` model). It scales draw and rapid-motion time only;
  pen dwells and emitted feeds/G-code are unchanged. The UI shows both the
  calibrated estimate and the unscaled model time. Repeat timing evidence
  before changing this machine-specific calibration.
- During playback, pen-up travel moves animate from their lift point to their
  destination using the configured travel-rate model. The highlighted rapid path
  grows only as far as the moving toolhead instead of appearing all at once.

## Notes for this machine

- Leave **Use Z axis** unchecked and keep `Pen up cmd = M5`, `Pen down cmd = M3` —
  pen height is owned by the force-control loop, not commanded Z.
- The converter has no XY-only export mode: every generated production program
  retains its planned A-axis words.
- The converter does not apply a pen/TMAG XY tool offset. Generated XY positions
  remain in the machine work-coordinate frame; the controller's commissioning
  macro `P100` owns magnetic center registration, the measured `pen - TMAG`
  offset, and `G54 X0 Y0` so work zero means pen tip at bed center.
- SVG document coordinates are not machine coordinates. The converter centers
  the clipped artwork at G54 zero; a document centered at `(100,100)`, for
  example, emits drawing coordinates around `(0,0)`, not `(100,100)`.
- `Bed margin mm` (default 6.35 ≈ 0.25") clips artwork inside the bed edge so the
  pen never reaches the rim.
- Set `Fill spacing mm > 0` to hatch filled regions; `0` disables hatching.
- `Fill pattern` selects OrcaSlicer-style sparse infill: `linear`, `crosshatch`,
  `diagonal`, `diagonal_crosshatch`, `diamonds`, `triangular`, `honeycomb`,
  `circles`, or `dots`. `linear` is always one parallel-line family; darker fills
  increase density by reducing spacing, not by changing the pattern into another
  pattern. The vector fill path treats each pattern as a full layer and clips
  pattern segments to the filled contour boundary. Compound SVG paths are clipped
  as one even-odd region, so holes cut the infill layer.
- `Shade levels > 1` turns SVG fill color into hatch density: darker fills receive
  denser spacing while preserving the selected fill pattern.
- `Raster shading` renders the whole SVG to a tone map first, then generates hatch
  layers from pixel darkness. Use this for gradients, embedded images, or any SVG
  where tone is visible but not represented as separate filled vector regions.
  `Raster px/unit` controls sampling resolution; higher is more accurate and slower.
- [`../samples/svg/raster-shading-math.svg`](../samples/svg/raster-shading-math.svg)
  is an editable visual reference for the tone-to-hatch mathematics.
- When an SVG is selected, the Qt app samples a low-resolution render. If meaningful
  tone variation is detected, it automatically enables raster shading and sets
  practical starter values (`Fill spacing mm = 4`, `Shade levels = 4`,
  `Shade angle step = 45`). Flat single-tone art is left unchanged.
