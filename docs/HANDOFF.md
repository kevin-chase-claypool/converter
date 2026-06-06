# Converter Handoff

> For a shorter onboarding path, read [`START_HERE.md`](START_HERE.md) first.
> Hardware integration planning is split into `architecture/`, `hardware/`,
> `integration/`, `project/`, `testing/`, and `decisions/` so future AI sessions
> do not have to reconstruct the current design from this long history.

Project root: `C:\Users\jacks\Documents\Claude\converter`

Repo layout (reorganized into components):
- `software/` — host SVG→G-code app
  - `qt_svg_to_gcode.pyw` — Qt/OpenGL UI (primary)
  - `converter_core/settings.py` — machine settings and UI field metadata
  - `converter_core/geometry.py` — SVG parsing, transforms, hatching, clipping helpers
  - `converter_core/kinematics.py` — bed/tool transforms, theta planning, contour ordering
  - `converter_core/gcode.py` — G-code emission and preview move generation
  - `svg_to_gcode.pyw` — compatibility shim for old imports / command-line conversion
  - `qt_debug.log` — runtime errors after closing the app
- `firmware/` — RP23CNC motion controller config/firmware (grblHAL) + pen-pressure MCU
  (separate from `software/`)
- `docs/` — this handoff + the System Integration report (`docs/report/`)
- `samples/` — example `svg/` inputs and `gcode/` outputs
- `converter.bat` (repo root) — launcher; `cd`s into `software/` and runs the app

## Machine model

XY gantry + rotating bed driven by a stepper with a 60T motor pulley → 720T bed pulley (12:1).
`Settings.theta_drive_ratio = 12` reflects this. The bed center is taken as the bbox center of the
loaded SVG contours; rotation about that center maps bed-local coords → machine coords via
`bed_to_machine(point, bed_theta, center)`.

The pen tip is offset from the hall sensor (= the commanded XY) by
`tool_offset_x_mm, tool_offset_y_mm` (defaults `34.544, -13.538`). G-code commands the hall sensor;
the pen tip lands at `command + tool_offset`.

## G-code output reference (what the firmware must parse)

The converter emits a tiny fixed subset — not full G-code:

| Token | Meaning |
|---|---|
| `(...)` | comment line — skip |
| `G21` | units = mm (emitted once) |
| `G90` | absolute coordinates (emitted once) |
| `G0 X.. Y.. [A..] [Z..] [F..]` | rapid / **travel** (pen up) |
| `G1 X.. Y.. [A..] [Z..] [F..]` | feed / **draw** (pen down) |
| `F..` | feed rate mm/min (modal) |
| `M3` / `M5` | pen down / pen up (non-Z mode) |
| `G1 Z{work}` / `G0 Z{safe}` | pen down / up (Z mode only) |
| `M2` | end of program |

**Critical caveat:** the `A` word is already in **motor-shaft degrees** — the converter multiplied
bed degrees by `theta_drive_ratio` (12). Firmware must convert `A` straight to motor steps and
**not** reapply the 12:1. (Alternatively set `theta_drive_ratio = 1` in the converter so `A` carries
bed degrees and the firmware owns the ratio — pick exactly one place.)

For a force-controlled pen, use **M3/M5 mode, not Z mode** (uncheck "Use Z axis"): Z mode commands an
explicit pen height that would fight the pressure loop. M3/M5 only says "engage / lift".
**Current UI/default gotcha:** `Settings.include_z` and the "Use Z axis" checkbox currently default
to `True`, so pressure-control test jobs must explicitly uncheck "Use Z axis" before generating
G-code. If this is left on, the generated file will use `G0/G1 Z...` pen moves instead of `M5/M3`
and will skip the `G4` pressure-settle dwell used by the pen-pressure handshake.

## Implemented

### Kinematics / G-code
- **Current theta solution: r-theta axis-cost resolver (`theta_resolver="rtheta"`).**
  This is the preferred/default kinematic solution in `converter_core/settings.py` and the Qt UI.
  For each draw segment, the planner uses the common r-theta axis-lock idea twice:
  - `x_theta`: solve the endpoint bed angle so machine **Y** stays fixed; the tool move is X + theta.
  - `y_theta`: solve the endpoint bed angle so machine **X** stays fixed; the tool move is Y + theta.
  The converter then does the cost analysis the project actually wants: score the realized
  `x_theta` move and the realized `y_theta` move independently, then emit whichever is cheaper for
  that segment. The emitted G-code comment is the chosen axis (`(x_theta)` or `(y_theta)`).
  `xy_theta` is not used.
- **R-theta cost currency:** each candidate axis move is scored as full coordinated motion,
  `hypot(xy_mm, theta_weight * motor_deg)`, where `motor_deg = bed_deg * theta_drive_ratio`.
  `theta_weight` defaults to `1.0`, so one motor degree is treated like one mm in the GRBL-style
  vector feed metric. The preview estimate/playback uses the same `motion_length`, so theta-heavy
  plans show up in the simulated total time. `round_bias`, `smoothness_factor`, and
  `theta_smooth_window` are legacy DP/greedy tuning knobs, not the main control path for `rtheta`.
- **Legacy resolvers:** `theta_resolver="dp"` and `"greedy"` remain selectable for comparison, but
  they are not the current preferred kinematic solution. Historical DP notes below are retained as
  design history and fallback behavior.

  Historical DP/greedy notes below in this subsection describe fallback behavior, not the default
  `rtheta` path:
- Theta-mode strategies: `fixed`, `tangent`, `min_rotation`, `x_theta`, `y_theta`,
  `optimized` (auto-pick). **`xy_theta` is gone as a label** — G-code segments are always labeled
  `x_theta` or `y_theta` based on which gantry axis carried the larger share of the realized
  machine move (`|dx|` vs `|dy|`). **Every draw segment uses the theta axis**: the DP/greedy
  candidate pool is **tangent flips + axis-lock roots**, no hold-steady grid. Tangent candidates
  give continuous theta sweep through curves (bed rotates with the segment direction → curves
  render as curves on the bed, not polylines, even at coarse tolerances); axis-lock candidates
  give pure-X (`y_theta`) or pure-Y (`x_theta`) machine motion with theta sweeping alongside,
  whichever is cheaper than tracking. This is the deliberate "speed-for-smoothness" trade: a
  hold-steady grid pool measured ~6× faster on the heraldic SVG (3.3 min vs 19.3 min) but kept
  the bed stationary for 94% of segments, contradicting the design intent that theta is the
  curve-smoothing axis. Survey of open-source polar plotters (Sandify, polargraph, Smac Planner)
  found no equivalent cost-analysis to compare against — pure r-theta machines have no choice
  in θ (kinematically determined by target XY), so they don't optimize what we optimize.
- **Per-segment theta cost (`candidate_cost`) is physical + rounding-aware.** In `optimized` mode
  the x_theta and y_theta generators are *pooled* into one candidate set and every angle is scored
  identically — no per-strategy `dx`/`dy`/`hypot` split. Cost =
  `hypot(xy_mm, theta_weight·motor_deg) + round_bias·tangent_deviation·ratio`, where rotation is
  priced in **motor degrees** (bed° × 12) so the slow bed is charged honestly, and
  `tangent_deviation` (mod 180) rewards orientations near the path tangent. `theta_weight` default
  is `1.0` (one motor-deg ≈ 1 mm of XY in the GRBL feed metric). `round_bias` (Settings, default
  0.05; "Curve round bias" in the UI) still dials cost↔roundness within the pool: 0 = whichever
  candidate has the shorter move, higher = whichever is closer to the tangent. Straights have a
  constant tangent so high bias leaves them stable (no needless rotation). `smoothness_factor`
  (Settings, default 1.0; "Smoothness factor" in the UI) multiplies `round_bias` as a quick
  throughput knob: lower it below 1.0 to reduce theta tracking on rotation-heavy jobs, or set it
  to 0 to disable the tangent-rounding bias without changing the stored `round_bias`. This replaced the old
  `xy_cost + theta_weight·Δθ(bed°)` cost that priced rotation as ~1°≈1 mm and therefore almost
  always picked axis-locked moves, flattening curves.
- **Theta resolver: Viterbi DP (legacy fallback) or greedy (fallback).** `plan_contour_thetas` centralizes
  per-contour theta selection and dispatches on `Settings.theta_resolver`. The **DP** path
  (`_plan_contour_thetas_dp`, default for the `optimized` theta_mode) globally minimizes coordinated
  motion over a principal-orientation lattice and replaces the old greedy+smoothing as the primary
  method — see the roadmap section below for the full design, gotchas, and the measured winding/motion
  wins. The **greedy** path (`_plan_contour_thetas_greedy`, `theta_resolver="greedy"`, and all explicit
  single-strategy theta_modes) is the old behavior: greedy per-point selection then a moving-average
  smooth (`smooth_sequence`, half-window `theta_smooth_window`, default 2). Both only change *how the
  bed is oriented while drawing* — drawn bed points are exact for any theta, so the artwork is
  unchanged. `theta_smooth_window` is still applied (as a final touch) by both paths. `theta_resolver`
  is exposed in the Qt UI ("Theta resolver"); the default `round_bias` is **0.05** (lowered from 1.0
  for the DP — see roadmap).
- Contour ordering is grid-bucketed nearest-neighbour: contour endpoints are indexed in a coarse
  bed-frame grid, each step evaluates the kinematic cost of only the ~12 nearest candidates (both
  directions), then a bounded 2-opt sweep (bed-frame endpoints, no re-simulation) fixes gross
  ordering mistakes. O(N) instead of the old O(N²) greedy-everything. On a 4,681-contour hatched
  job it plans in ~10 s; on the ArtFavor outline it cuts pen-up travel ~4× vs raw SVG order
  (2,475 mm vs 9,722 mm).
- **Monotonic theta** (`Settings.monotonic_theta`, default True, "Monotonic theta (r-theta style)"
  in the UI): borrows from how Sisyphus/r-theta sand tables handle inter-feature motion. Instead
  of always picking the next contour by shortest |Δθ| rotation, `contour_entry_cost` tracks the
  bed's running rotation direction (+1/-1, sign of the last inter-contour Δθ) and penalises
  candidates that would reverse it by `(360 - |Δθ|) × theta_weight` — the cost of going the long
  way around to keep spinning the same way. Effect on the heraldic SVG: travel direction
  reversals 22 → 18, motor rotation across travels 55 rev → 50 rev, total time -10s. **Trade-off
  (be aware):** monotonic ordering accumulates more *net* winding (peak motor excursion went
  from 42 rev → 55 rev in testing) because it stops oscillating. That's fine on a sand table
  (slip rings, no cables crossing the rotation axis) but raises the cable-wrap cost on our
  machine. The net-winding cap TODO further down becomes more important when this is on.
- Per-move `duration_ms` uses GRBL vector-feed math: `sqrt(xy_distance² + motor_theta_delta²) /
  rate × 60000`. Captures motor sweep time on rapids/travels that previously appeared instant.
- Concentric and lattice fill modes have pen-cycle-aware keep-down bridging. `bridge_motion`
  compares short contour-to-contour gaps against lift/travel/lower time and emits
  `G1 ... (keep-down bridge)` when drawing the connector is cheaper. Preview uses the same logic,
  so the estimate and saved G-code agree. Enabled for `concentric`, `triangular`, `diamonds`, and
  `hexagonal`; other artwork still avoids arbitrary connector drawing. Gap thresholds use the
  active pattern-specific size override when one is set, falling back to `Fill spacing mm`.
- Final park-NE move at job end.
- Renamed "rapid" → "travel" everywhere (settings, UI labels, move type strings, JS preview).

### Geometry
- `clip_contours_to_bed(contours, center, radius)` clips SVG segments at the bed circle, splitting
  contours where they exit and re-enter. Applied in both `contours_to_gcode` and
  `build_preview_moves`, locking the bed center from the *original* contour bbox before clipping.
- `bed_margin_mm` (default 6.35 ≈ 0.25") pulls the clip radius inward to keep the pen off the bed
  edge.
- Pen-width compensation (`compensate_pen_width`) insets/outsets closed contours by half the pen
  stroke width.
- Scaling, tolerance-based curve flattening, Y-flip, Z-axis pen vs M3/M5 modes.

### Fill hatching
- `hatch_polygon(polygon, spacing, angle)` runs a scanline fill and returns clipped line segments.
  Segment-level clipping is intentional: connector moves between scanlines can cross outside
  concave boundaries, so infill stays inside at the cost of more pen-up cycles.
- Triggered by any SVG element whose `fill` is not explicitly `none` / not fully transparent (SVG
  default = filled black). `hatch_spacing_mm` controls density (0 = disabled);
  `hatch_angle_deg` controls direction (default 45). `hatch_pattern` / "Fill pattern" selects
  OrcaSlicer-style sparse infill: `linear`, `crosshatch`, `diagonal`,
  `diagonal_crosshatch`, `diamonds`, `triangular`, `honeycomb`/`hexagonal`, `circles`, `dots`,
  `waves`, `gyroid`, `cubic`, or `concentric`.
  `linear` is always one parallel-line family; darker fills increase density by reducing spacing
  rather than adding unrelated angle families. Vector fills treat the pattern as a full layer and
  clip pattern segments to the filled contour boundary. OrcaSlicer references used for this model:
  the infill settings wiki and pattern settings wiki.
- Pattern-specific size overrides are available for the non-basic patterns:
  `triangle_size_mm`, `diamond_size_mm`, `hex_size_mm`, `circle_size_mm`, `dot_spacing_mm`,
  `wave_size_mm`, `gyroid_size_mm`, `cubic_size_mm`, and `concentric_spacing_mm`. Each defaults to
  0, which means "use Fill spacing mm"; the Qt row appears only for its selected pattern. The
  triangular generator propagates a true 60-degree lattice through the fill and clips lattice edges
  at the boundary; boundary cells can be partial, but interior edges stay on the three lattice
  directions. `diamonds` and `hexagonal` use shared-vertex/shared-edge lattices rather than stamped
  isolated cells. Lattice segment graphs are greedily chained into longer paths before planning, so
  shared edges/corners do not force one pen cycle per edge.
- Sparse infill clipping now uses `clip_segment_to_region`: generated line/cell/dot segments are
  intersected against all contours in the SVG element and retained only for even-odd-inside spans.
  Points exactly on polygon boundaries are treated as inside, and shape/dot pattern layers are
  generated beyond the region bounds before clipping so edge-crossing cells can be cut at the
  boundary instead of disappearing.
- Tone-driven SVG fill shading is implemented. `shade_levels` (Qt label "Shade levels", default 1)
  controls density steps for tone-driven fills. Fill darkness comes from luminance and opacity:
  white gets no hatch, gray gets lower-density infill, black gets denser infill. Missing fill still
  follows the SVG default black behavior.
- Raster shading is implemented in the Qt app (`Raster shading` checkbox). It uses `QSvgRenderer`
  to render the whole SVG to a transparent `QImage`, samples pixel darkness, and generates hatch
  segments for each shade threshold. This supports gradients, embedded raster images, and artwork
  whose visible tone is not represented as separate SVG fill colors. `Raster px/unit` controls render
  sampling resolution; the implementation caps the rendered max dimension at 2400 px to keep planning
  bounded. When raster shading is on, vector fill hatching is disabled and raster hatch contours are
  appended to the normal parsed vector contours.
- For closed line-art SVGs with raster shading on, `triangular`, `diamonds`, `hexagonal`, and
  `concentric` use a closed-centerline fallback: parse closed SVG centerlines without stroke
  expansion, rasterize them as an even-odd fill mask, then clip the lattice/rings to the exact
  `QPainterPath` boundary. This avoids sampling only dark stroke pixels and makes line-art behave
  like filled regions.
- Auto shading runs when the user selects an SVG in the Qt app. It renders a low-resolution tone
  preview and, if the 5th-to-95th percentile darkness range is meaningful, enables `Raster shading`
  and sets starter values (`Fill spacing mm = 4`, `Shade levels = 4`, `Shade angle step = 45`).
  Flat single-tone artwork is left alone so silhouettes do not unexpectedly become raster-shaded.
- Settings.hatch_spacing_mm / hatch_angle_deg / hatch_pattern and the pattern-specific size map are
  threaded through `parse_svg_geometry` / `element_contours`; `shade_levels` /
  `shade_angle_step_deg` are threaded through the same path. Qt's raw-contour cache key includes
  these fill-generation settings so changes invalidate the cache.

### Qt UI
- Sidebar settings are split into focused groups:
  - **Geometry** — scale, tolerance, Flip Y, and pen-stroke compensation.
  - **Shading** — fill spacing/angle/pattern, pattern-specific size fields, shade levels/angle
    step, raster shading, and raster sampling. Pattern-specific rows appear only when relevant;
    `Raster px/unit` appears only when raster shading is enabled.
  - **Motion** — draw/feed rate and travel rate.
  - **Theta kinematics** — theta axis/ratio/resolver/cost settings, plus monotonic theta.
  - **Pen** — Z heights, pen up/down simulation/dwell times, tool offsets, pen up/down commands, plus Use Z.
  - **Preview settings** — print speed (mm/s), bed dia/margin, pen stroke width, preview
    colors. "Print speed" now drives **both** the runtime estimate **and** the animation pacing:
    playback runs in **real time** (`PLAYBACK_RATE = 1.0` in `qt_svg_to_gcode.pyw`) with draw moves
    paced at print speed, so the on-screen toolhead moves at the real machine speed (~100 mm/s by
    default). **Both draw and travel pacing use XY length only** (`xy_length` on the move dict),
    not the full GRBL vector `hypot(xy, motor_deg)` — the bed follows the gantry within each
    move's XY time window rather than stretching the move to cover the motor sweep, so
    rotation-heavy moves don't crawl. Draws use the print-speed setting (mm/s); travels use
    `travel_rate` (mm/min). `motion_length` is kept on the move dict for engine reference. Pen
    moves still use their fixed engine `duration_ms`. Rationale: with the bed always using theta
    (no grid hold-steady), contour transitions involve substantial bed rotation; the GRBL vector
    model treats motor degrees as mm at the same rate, which made travels appear to crawl (one
    travel spinning 500° of motor at 50 deg/s = 10s of wait between contours). Reality is that
    the firmware motor runs much faster than the gantry's `travel_rate` deg/min would suggest, so
    playback now reflects what the user actually sees IRL. The playback timeline lives in
    `GLPreview.cumulative_ms` (built via `_playback_move_ms`); `progress_after_time` must use the
    same `_playback_move_ms` for the within-move fraction. Bump `PLAYBACK_RATE` to fast-forward
    long jobs, or scrub with the slider.
    **Update:** `_playback_move_ms` and the Qt estimated time use full `motion_length`
    (`hypot(xy, motor_deg)`) for draw moves so smoothness / theta-tracking changes affect the
    displayed simulation total. Travel playback/estimate is intentionally fixed at 100 mm/s using
    `xy_length`, independent of the emitted G-code `travel_rate`, so inter-segment travel animates
    at the expected machine travel speed.
  - **Other settings** — "Preview mode: omit theta axis" (the one knob that lives in both worlds —
    it also strips theta from the saved G-code).
- Layout is now a `QSplitter`: left sidebar (settings + Convert/Preview buttons), centre
  GL preview with playback controls / status / estimate stacked beneath, right command list.
  Files row collapsed to one strip. Log shrunk to 60 px. Preview now gets most of the window.
- Preview generation is manual: editing settings no longer re-runs the pipeline automatically.
  The user must press **Preview** to rebuild contours/moves after changing settings. Selecting an
  SVG updates the suggested G-code path and auto-shading starter values, then waits for Preview.
  `Print speed` still updates playback pacing for the already-built preview.
- Non-Z pen simulation/dwell timing is split by direction: `Pen up ms` / M5 defaults to 300 ms,
  and `Pen down ms` / M3 defaults to 600 ms. Saved G-code emits matching `G4` dwells after M5/M3.
  The old single `pen_cycle_ms` field remains in settings for compatibility but is no longer shown
  in the Qt Pen settings.

### OpenGL preview (`GLPreview`)
- Vertex shader does the rotate-around-center + bounds-to-NDC normalize. Uniforms: `center`
  (vec2), `theta` (float, set via `setUniformValue1f` to dodge the PySide6 int/float overload
  ambiguity), `bounds` (vec4), `color` (vec4).
- Static `QOpenGLBuffer`s for `bed_circle`, `bed_radius`, `debug_box`, `debug_cross`, `artwork`,
  `travel`, `motion`. One streaming dynamic VBO for per-frame overlays (crosshair, pen
  connector, tool marker, pen-tip box, active segment).
- `adjusted_bounds()` memoized against `(width, height, bounds_base)`; invalidated on resize and
  rebuild. `play_step` uses `update()` instead of `repaint()` so paints coalesce under the event
  loop.
- Bed rotation transform now matches the converter (artwork rotated by `+bed_theta` around
  `preview_center`, which is the original SVG-bbox center passed in via `set_preview(center=...)`).
- Pen-tip indicator (orange box) drawn at the unrotated machine-frame command point with all four
  sides closed (previously rendered only two sides because the buffer had 4 verts under GL_LINES).
- **Draw-progress shading:** the full artwork is drawn as a light tint (`drawing_color.lighter(185)`),
  then the portion drawn so far is overdrawn in the full `drawing_color`. Implemented with a static
  `drawn_path` VBO built in *draw order* (bed coords, from each draw move's `bed_start`/`bed_end`)
  plus a per-move prefix count (`draw_count_at_move`); paintGL just varies the GL_LINES vertex count
  by progress — no per-frame rebuild. The light/dark boundary sits where the pen currently is, so
  drawing progress is visible directly on the rotating image (machine view).

## Debugging history (resolved)
- `color_tuple()` was returning a `QVector4D` while callers unpacked it as a 4-tuple — produced
  a steady stream of `paintGL` exceptions in `qt_debug.log`. Returns a plain tuple now.
- Bed rotation sign was flipped (`-bed_theta` instead of `+bed_theta`), so artwork rotated the
  wrong way and the pen tip never tracked it.
- PySide6 `setUniformValue(int, float)` dispatched as `setUniformValue(int, int)` for scalar
  uniforms, sending `theta = 0` regardless. Fixed by using `setUniformValue1f` for the theta
  uniform.
- `glVertexAttribPointer(..., 0)` was brittle on the VBO-offset path — switched to
  `QOpenGLShaderProgram.setAttributeBuffer`, the PySide6-native API.

## Known soft spots
- The planner uses approximate (bed-frame) distance in the 2-opt sweep and evaluates only the ~12
  nearest candidates per step (`_PLANNER_CANDIDATE_COUNT`). Quality matched/beat the old greedy on
  test files; if a pathological job orders poorly, raising the candidate count or widening the
  2-opt window are the knobs.
- `has_visible_fill` follows SVG defaults: any element without an explicit `fill="none"` is
  treated as filled. Stroke-only line-art SVGs that don't set `fill="none"` will over-hatch when
  `Fill spacing mm > 0` — set the spacing to 0 or add `fill="none"` in the SVG to disable.
- Composite fill paths are hatched as one even-odd region, so holes/nested contours cut the sparse
  infill layer instead of being hatched independently. Regression smoke tests check that generated
  segment midpoints remain inside a compound region with a hole. Self-intersecting hand-drawn paths
  can still look odd if their even-odd region is ambiguous.
- `converter_core/` is the shared conversion **engine**. The old Tk UI has been removed; new UI work
  goes in `qt_svg_to_gcode.pyw`, while geometry, kinematics, planning, and G-code behavior stay in
  the focused core modules above. `svg_to_gcode.pyw` remains only as a compatibility shim.

## Goals / roadmap

### Converter (software, can be finished + verified in-app)

- **R-theta axis-cost resolver — current default.** `Settings.theta_resolver` now defaults to
  `"rtheta"` in the engine and Qt UI. For each draw segment, the planner solves the standard
  r-theta-style endpoint angle twice: `x_theta` keeps machine Y fixed and moves X+theta, while
  `y_theta` keeps machine X fixed and moves Y+theta. It scores both realized coordinated moves
  with the same physical cost (`hypot(xy, theta_weight*motor_deg)`) and emits whichever axis is
  cheaper. The old DP and greedy resolvers remain selectable via `Theta resolver` for comparison.

- **DP / Viterbi theta resolver — DONE.** `plan_contour_thetas` now dispatches on
  `Settings.theta_resolver` (default `"dp"`; `"greedy"` keeps the old per-segment path as a fallback).
  Current status: this DP section is historical/fallback documentation. It is selectable with
  `theta_resolver="dp"`, but the active default is `theta_resolver="rtheta"`.

  The DP runs for the auto theta_mode (`optimized`/`auto`/`select`); explicit single-strategy modes
  (`tangent`, `fixed`, `x_theta`, …) still use the greedy path. Public shape unchanged (returns
  `(thetas, strategies)`), so `build_preview_moves`, `contours_to_gcode`, `simulate_contour_exit` were
  untouched.

  **What it does** (`_plan_contour_thetas_dp`): a Viterbi shortest-path over a per-point lattice of
  **principal** bed orientations (mod 360). Per point the candidates are:
  - **tangent flips** (each adjacent segment's tangent line in both directions): bed angle
    follows the curve, theta sweeps smoothly within each segment.
  - **axis-lock roots** (orientations nulling one machine-axis delta to the previous nominal
    point): segment becomes pure-X or pure-Y gantry motion with theta sweeping.
  - **(disabled by default)** `_THETA_DP_GRID_DEG`: uniform orientation grid for hold-steady
    anchors. Set to 0 by design. Re-enabling it gives ~6× speedup but parks the bed across most
    segments. Kept as a knob for users who want speed over visible kinematics, but ships off.

  Edge cost (`_dp_edge_cost`) is the same physical+rounding currency as `candidate_cost`, but the
  motor term uses the **nearest-wrap** delta (`_wrap180`) between principal angles, so winding only
  accumulates through genuine continued rotation. After backtracking the principal sequence is
  reconstructed to continuous absolute angles via `unwrap_angle`. **Segment labels are assigned
  post-hoc** from realized `|dx|` vs `|dy|` so the G-code says `x_theta`/`y_theta` based on which
  gantry axis did the work — independent of which DP candidate (tangent or axis-lock) the
  angle came from. `theta_smooth_window` still applies as an optional final touch.

  **Measured numbers (heraldic SVG, 34 contours, hatch off, default tolerance 0.25, XY-only
  pacing for both draws and travels):**

  | pool | total | bed rotation | theta-active |
  |---|---|---|---|
  | axis-lock only | ~17 min | 109 rev | 100% |
  | **tangent + axis-lock (current)** | **13.8 min** | **94 rev** | **99.7%** |
  | + grid (hold-steady; off) | ~3 min | 4 rev | 6% |

  **Key gotchas (carried over from earlier iterations):**
  - Anchoring candidate windings to a tangent-following reference is wrong (the reference itself winds,
    so a low-winding solution falls outside the ±k·180 window). Use principal angles + nearest-wrap
    edges instead — winding is an emergent property of the path, not baked into the candidates.
  - **The hold-steady grid is a speed lever and a design choice, not a default.** Earlier iterations
    shipped with it on (`_THETA_DP_GRID_DEG = 45`); current ships with it at 0. Turning it on parks
    the bed for ~94% of segments — useful if a user wants throughput over kinematic visibility, but
    the project's stance is that theta is the curve-smoothing axis and should be active.

  **Result — DP strictly dominates the old greedy on the roundness↔motion frontier, and is faster**
  (0.25 tol, `theta_smooth_window=2`, 45° grid). Comparing at *matched roundness* (mean per-segment bow):

  | job | setting | bow | total rot | draw motion |
  |---|---|---|---|---|
  | ArtFavor | greedy bias 1.0 | 0.003 | 73 rev | 267k |
  | ArtFavor | **dp bias 0.02** | 0.002 | **30 rev** | **131k** |
  | ArtFavor | greedy bias 0 (faceted) | 0.000 | 20 rev | 77k |
  | ArtFavor | **dp bias 0 (faceted)** | 0.000 | **0.0 rev** | **19k** |
  | snowy | greedy bias 1.0 | 0.002 | 87 rev | 295k |
  | snowy | **dp bias 0.02** | 0.001 | **22 rev** | **102k** |

  Planning time dropped too (ArtFavor ~12 s greedy → ~9 s DP; snowy ~18 s → ~14 s). At full tracking
  (bow ≈ 0.12–0.15) DP and greedy converge (~628 / ~1000 rev) — that winding is genuine curvature, not
  waste. **`round_bias` is far more sensitive under DP** (it globally commits to tracking): the old
  greedy default 1.0 gave barely-rounded curves at ~73–87 rev, but DP bias 1.0 means heavily-rounded at
  ~617/963 rev. So the **default `round_bias` was lowered 1.0 → 0.05** (light rounding, ~92/57 rev —
  same look as the old default, less winding). `bias 0` is now near-zero bed rotation (rely on flatten
  tolerance for smoothness).

  Tuning knobs (module constants in `converter_core/kinematics.py`): `_THETA_DP_GRID_DEG` (0 by default —
  set to e.g. 45 to add hold-steady anchors; speeds prints up massively at the cost of bed
  parking), `_THETA_DP_DEDUPE_DEG` (merge threshold for near-duplicate candidates). Lattice is
  O(points·K²), K ≈ 6 here (2 tangent flips × 2 adjacent segments + ~2 axis-lock roots, deduped).

  **Not done / possible follow-up:** the DP minimizes per-contour coordinated motion but does **not**
  explicitly cap *net* winding across the whole job (cable-wrap). At light bias net stays low (~2–6 rev);
  if cable management ever needs a hard bound, add a net-winding penalty or a periodic unwind move.

- **Settings persistence** — machine constants (bed dia, tool offsets, theta ratio, feeds) reset to
  defaults every launch. Add JSON save/load (auto-load on startup, ideally named profiles per
  pen/material). Highest convenience-per-effort item; not yet started.
- **Calibration test-pattern generator** — emit a known square + circle + center cross so the real
  machine can be checked for scale, tool offset, and theta direction before committing to a big job.
  De-risks everything below; the kinematics have only ever been verified in the preview, never on
  hardware.
- **Fill refinements** — fill-mode toggle (outline only / fill only / both) and optional auto fill
  spacing tied to pen stroke width for gap-free solids.

### RP23CNC (RP2350) firmware — **decided: RP23CNC + grblHAL + Ethernet** (NOT started)
Hardware decision: use the **RP23CNC / RP23U5XBB 5-axis grblHAL controller** from Brookwood Design,
with the optional Ethernet adapter. This gives the project a ready RP2350 grblHAL controller instead
of a custom parser/motion board: X/Y/A step-dir outputs, opto-isolated limit inputs, probe/control
inputs, spindle/digital outputs, and USB/Ethernet transport.

Motion decision: drive the machine with **grblHAL** rather than a custom parser/motion planner.
grblHAL handles parsing this dialect, X/Y+A coordinated motion, acceleration/junction lookahead,
step generation, and M3/M5 as a spindle-enable output. The pen-pressure system is a separate
concern layered on top.

grblHAL setup tasks (config, not parser code):
1. Build/flash RP23CNC-compatible grblHAL with Ethernet enabled and X/Y/Z/A available.
2. `$` settings: steps/mm for X/Y; **A steps-per-unit = motor steps per degree** (the converter
   emits `A` in *motor* degrees — see G-code reference); per-axis max rate + acceleration.
3. Wire X/Y limit switches to opto-isolated limit inputs. Use a theta index/probe input for the
   bed index sensor once the homing scheme is finalized.
4. Wire grblHAL **spindle-enable output → pen pressure subsystem** as the override line:
   M3 = ENGAGE, M5 = LIFT.
5. **Settle handshake — DONE on the converter side.** `contours_to_gcode` now emits direction-specific
   dwells after M3/M5 in non-Z pen mode: M5 / `Pen up ms` defaults to `G4 P0.3`, and M3 /
   `Pen down ms` defaults to `G4 P0.6`, via `append_pen_dwell`. So grblHAL pauses for the pen to
   lift before travel and reach paper before drawing. The redundant per-contour-start M5 was also
   removed (pen is always already up there), so each actuation gets exactly one dwell and the G-code
   matches the preview. Closed-loop "wait for actual load-cell contact" is still a later upgrade via
   a grblHAL plugin that feed-holds until a contact input.
6. **Verify on hardware:** how grblHAL scales feed on a combined X/Y/**A** move vs the converter's
   `sqrt(xy² + motor_deg²)/F` pacing. Only affects speed/timing, not path shape.

Pen pressure system (independent of grblHAL):
- Closed loop: load cell → force PID → pen motor, holds target contact force and tracks paper/bed
  unevenness while drawing. Driven by the spindle-enable signal as a **mode override**:
  - `LIFT` (M5) = drive actuator open-loop to a safe retract height, force loop paused.
  - `ENGAGE` (M3) = release override; seek down slowly until the load cell trips, then hold force.
- **Placement:** run it on a **separate MCU** that listens to the spindle-enable line (cleanest
  first version, since grblHAL owns the RP23CNC motion timing). A grblHAL **plugin** on the same
  controller is the more integrated option later and is the only path that lets the pen system
  feed-hold grblHAL until contact is confirmed.
- **ENGAGE safety:** approach rate-limit, max-seek/stall guard (abort to LIFT if no contact = missing
  paper), force clamp, force LIFT on any fault / E-stop.

Open sub-decisions: transport (grblHAL SD-card plugin vs USB streaming from a host); load-cell
interface (HX711 vs ADC+amp); pressure-loop placement (separate MCU first, plugin later).

## Useful commands

Syntax check:

```powershell
python -m py_compile software\qt_svg_to_gcode.pyw software\svg_to_gcode.pyw software\converter_core\settings.py software\converter_core\geometry.py software\converter_core\kinematics.py software\converter_core\gcode.py software\converter_core\__init__.py
```

Launch:

- Double-click `converter.bat` (stdout/stderr → `software\qt_debug.log`)

Quick parse / planner timing (run from repo root):

```powershell
python -c "import sys, time; sys.path.insert(0, 'software'); import converter_core as c; s = c.Settings(); ct = c.parse_svg_geometry(r'<path>', 0.25, True, 1.0, 45.0); print(len(ct), 'contours'); t=time.time(); c.planned_contours(c.clip_contours_to_bed(ct, c.contour_center(ct), s.bed_diameter_mm/2 - s.bed_margin_mm), s, c.contour_center(ct)); print(f'{time.time()-t:.2f}s')"
```
