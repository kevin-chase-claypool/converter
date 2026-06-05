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

- `G21` (mm), `G90` (absolute)
- `G0` travel moves (pen up), `G1` draw moves (pen down)
- `X Y` in mm; `A` = **motor-shaft degrees** (already multiplied by `Theta ratio`)
- `M5` / `M3` pen up / down (or `Z` moves if "Use Z axis" is enabled), with a
  `G4` settle dwell after each (from `Pen cycle ms`) for the firmware handshake
- `M2` at end

The exact dialect and the firmware-facing caveats are documented in
[`../docs/HANDOFF.md`](../docs/HANDOFF.md) → "G-code output reference".

## Settings groups (Qt app)

- **Geometry** — scale, tolerance, Flip Y, and pen-stroke compensation.
- **Shading** — fill spacing/angle/pattern, shade levels/angle step, raster shading, and
  raster sampling resolution.
- **Motion** — draw/feed rate and travel rate.
- **Theta kinematics** — theta axis/ratio/resolver/cost settings (`Theta ratio`
  defaults to 12 for the 60T→720T pulley pair).
- **Pen** — Z heights, pen cycle, tool offsets, pen up/down commands, and Use Z.
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
- **Preview settings** — print speed (estimate), bed diameter/margin, pen stroke
  width, and three preview colors: **Undrawn** (artwork not yet drawn), **Drawn**
  (the drawn portion / final color), and **Motion** (active move + toolpath).
- **Other settings** — "Preview mode: omit theta axis" (also strips the `A` word
  from saved G-code; useful for online viewers like NC Viewer / gcode.ws).

## Notes for this machine

- Leave **Use Z axis** unchecked and keep `Pen up cmd = M5`, `Pen down cmd = M3` —
  pen height is owned by the force-control loop, not commanded Z.
- `Bed margin mm` (default 6.35 ≈ 0.25") clips artwork inside the bed edge so the
  pen never reaches the rim.
- Set `Fill spacing mm > 0` to hatch filled regions; `0` disables hatching.
- `Fill pattern` selects the generated infill: `crosshatch`, `linear`,
  `triangular`, `hexagonal`, or `dots`. Line-based patterns are clipped to the
  filled SVG contour; dots are placed inside the filled contour.
- `Shade levels > 1` turns SVG fill color into hatch density: darker fills receive
  more hatch angles, starting at `Fill angle deg` and stepping by `Shade angle step`.
- `Raster shading` renders the whole SVG to a tone map first, then generates hatch
  layers from pixel darkness. Use this for gradients, embedded images, or any SVG
  where tone is visible but not represented as separate filled vector regions.
  `Raster px/unit` controls sampling resolution; higher is more accurate and slower.
- When an SVG is selected, the Qt app samples a low-resolution render. If meaningful
  tone variation is detected, it automatically enables raster shading and sets
  practical starter values (`Fill spacing mm = 4`, `Shade levels = 4`,
  `Shade angle step = 45`). Flat single-tone art is left unchanged.
