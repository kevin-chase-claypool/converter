# Host software — SVG → G-code converter

Converts `.svg` artwork into `.gcode` for the XY + rotating-bed (theta) machine,
with a live preview of the simulated machine motion.

- `qt_svg_to_gcode.pyw` — the primary app: PySide6 + OpenGL preview, playback,
  and all conversion settings in one window.
- `converter_core/` — the conversion engine split by responsibility:
  settings, SVG geometry, kinematics/planning, and G-code/preview move emission.
- `svg_to_gcode.pyw` — a compatibility shim for older imports and simple
  `input.svg output.gcode` command-line conversion.
- `qt_kaleidoscope.pyw` — the sibling app: imports an SVG, PNG or JPG, mirrors
  it into N kaleidoscope divisions, and saves the same G-code contract.
  Launched by `..\kaleidoscope.bat`; it reuses `converter_core/` unchanged.
  Its second tab, **Maps**, embeds a local copy of `piebro/plotting-maps` for
  turning OpenStreetMap exports into plotter SVGs.

## Run

```powershell
python qt_svg_to_gcode.pyw
```

or double-click `..\converter.bat` from the repo root. Runtime errors are written
to `qt_debug.log` in this folder.

Requires `PySide6` (`pip install PySide6`). The kaleidoscope's **Maps** tab
also needs Qt WebEngine, which ships in the full `PySide6` wheel
(`PySide6-Addons`); without it the tab reports the missing module instead of
failing the app.

The first two lines of `qt_debug.log` (and of the window's log pane) name the
converter core and the active A-axis guard, e.g.
`[A guard: park above 10 deg/segment, 20000 motor deg/min, travel rotations fed]`.
A window opened before a core change keeps the old planner in memory, so that
line is how a stale instance is told from a current one.

To check a *saved* file instead of the running app:

```powershell
python ..\tools\check_gcode_motion.py ..\samples\gcode\my-job.gcode --strict
```

It reports the largest bed rotation inside one drawing move, the largest A rate
demanded, whether any pen-up move carries rotation as a bare `G0` rapid, and the
worst commanded bed-path bow with its radius - measured from the file, so it
answers "did this program get the guard?" without guessing.

Two repeatability programs exist for measuring the machine itself, both safe to
Cycle Start with the pen loaded:

- `..\samples\gcode\a-repeatability-test.gcode` - the bed: a radial tick, two
  bed revolutions out and two back with the pen down, the tick again, at
  r = 100 mm and r = 160 mm. Ticks on top of each other means the bed returned.
- `..\samples\gcode\y-repeatability-test.gcode` - the heavy gantry axis: a tick
  across the axis, five runs out and back at 3000 / 6000 / 12000 / 20000 mm/min
  with the pen up, the tick again per rung. The top rung is what a `G0` pen-up
  travel actually runs at, because grblHAL ignores the `F` word on a rapid.
  Regenerate either with the matching tool in `..\tools\`
  (`make_a_repeatability_test.py`, `make_xy_repeatability_test.py --axis X`).

## Generator tabs

The window has the standard **File / Tools / View / Help** menu bar. **File**
opens the artwork (Ctrl+O), sets the G-code destination (Ctrl+Shift+S), saves
G-code (Ctrl+S), and exits. **Tools** is the tool selector: **All Tools**
(Ctrl+T) opens the card dashboard (Core, Line art, 3D, Patterns, Text &
layout), **Convert** is Ctrl+1, and the other tools follow in menu order with
Ctrl+2...Ctrl+0. **View** toggles the machine reach guide, pen-down path, and
log, and controls preview zoom; **Help** has the shortcut list (F1) and About.
The status bar shows the current artwork and G-code paths. Tools are
contributed by `software/generator_tabs/*_tab.py` modules and discovered at
startup, one page per tool; a broken tool is reported in the log instead of
stopping the app.

Import, **Preview / Cancel / Save G-code**, and the OpenGL preview panel are
static window furniture: they stay visible on every tab. Pressing **Preview**
builds the active tab - Convert previews the Artwork row's file, while Flow
Field, Line Draw, and 3D Wireframe build their own SVG from their controls -
and that result runs through the same converter pipeline into the shared
preview panel. **Save G-code** exports the active tab's result. Switching tabs
never rebuilds anything; it marks the visible preview as belonging to another
tab until Preview is pressed again.

Tool authors: the contract and the host entry points are documented in
[`generator_tabs/README.md`](generator_tabs/README.md). Ported or vendored
third-party code keeps its license and attribution in a sibling
`<name>_NOTICE.md`.

Current tools:

- **Flow Field** - evenly spaced streamlines from a procedural noise field or
  an image's luminance gradient. Controls: source, artwork (from the static
  Artwork row), invert, image cutoff, seed, noise scale, octaves, spacing,
  step, max steps, line width, page size, margin, artwork scale.
- **Line Draw** - raster image to edge-traced contours plus luminance hatch.
  Controls: artwork (from the static Artwork row), invert, mode
  (contours / hatch / both), edge
  threshold, hatch spacing, hatch tone, sketch jitter, minimum length, line
  width, seed, page size, margin, artwork scale.
- **3D Wireframe** - OBJ or STL mesh to orthographic hidden-line vector art.
  Controls: model file, style (hidden-line wireframe / silhouette / all
  edges), yaw, pitch, roll, target width, sample step, page size, margin,
  line width, artwork scale.
- **Harmonograph** - damped Lissajous figures from two decaying oscillations,
  one to four curves. Controls: seed, frequency X/Y, phase, damping, turns,
  samples, curves, curve size, page size, margin, line width, artwork scale.
- **Snowflake** - radial dendritic snowflakes with jittered branches.
  Controls: seed, arms, branch depth, arm length, branch angle, branch scale,
  angle jitter, length jitter, page size, margin, line width, artwork scale.
- **Truchet** - Truchet tiles as quarter arcs, diagonals, or mixed. Controls:
  seed, tile size, style, arc segments, page size, margin, line width,
  artwork scale.
- **Text** - monoline single-stroke text using the vendored public-domain
  Hershey simplex font. Controls: text lines, text size, tracking, line
  spacing, alignment, page size, margin, line width, artwork scale.
- **Substitution** - 2x2 colour-substitution pattern from a seeded palette,
  drawn as colour boundaries or one diagonal per cell. Controls: seed,
  colours, iterations, style, page size, margin, line width, artwork scale.
- **Postcard** - plottable postcard back: border, centre divider, stamp box,
  address guide lines, and optional caption/address text. Controls: page
  preset, divider, address lines, line spacing, stamp size, caption, address,
  text size, tracking, page size, margin, line width, artwork scale.

Image-driven tabs read the file already loaded in the static Artwork row
instead of repeating the import control.
Every generator tab has an **Artwork scale** control (10-1000%) that scales its
result about the page centre.
The Text tab (and the Postcard tab's caption/address) uses the vendored
public-domain Hershey simplex font in `generator_tabs/fonts/`; its use terms
are in `generator_tabs/fonts/NOTICE.md`.
Generator pages are previewed **1:1** with the auto fit skipped, so that
Artwork scale sets the physical drawing size; imported artwork on the Convert
tab still uses the selected Fit mode.
Generator tab controls fill the settings column, with the tab's hint and
status text stacked below them; the settings column has a 280 px floor so it
cannot be crushed by the preview.

The artwork/G-code file row (with **Save G-code**), the **Preview** and
**Cancel** buttons in the preview panel under the playback controls, and the
OpenGL preview itself (status, estimate, progress, fit/clip controls) are
window furniture outside the tab widget, so they stay visible whichever tab is
active. The preview fills the whole area to the right of the feature settings
pane; only the settings sidebar belongs to the Convert tab.

## Kaleidoscope Converter

`qt_kaleidoscope.pyw` (or `..\kaleidoscope.bat`) builds an N-fold mirrored
design from an SVG, PNG or JPG and emits the same program contract as the main
app.

- **Same planner, same A-axis guard.** This window has no kinematics of its
  own: `output_settings()` starts from `converter.Settings()` and the program is
  produced by `plan_program` + `contours_to_gcode`, so it inherits every
  converter rule including the bed-parking guard (no segment rotating the bed
  more than 15 deg) and the 20000 motor deg/min assumed A limit. It therefore
  needs a **restart** after a converter-core change, exactly like the main app;
  the startup log names the loaded build (`Converter core <version>: A-axis
  guard active ...`) and the same line goes to `kaleidoscope_debug.log`.
- **Control column.** Every group is open at once, so the column of controls is
  taller than a laptop window. It lives in a scroll area - scroll it down to
  reach `Build preview` and `Save G-code...`. The sidebar is never narrower than
  the widest row needs, so the vertical bar is the only one that appears and no
  label or spin box is cut off.
- **Source.** SVG geometry goes through the same parser, fill and clipping as
  the main app. A raster image is traced by marching squares into closed
  contours (`converter_core.kaleidoscope.trace_raster`), so a traced region can
  also be filled by the normal fill settings; `Image threshold`,
  `Treat light pixels as ink` and `Trace detail` control that trace.
- **Random pattern.** Tick `Generate a random pattern instead of artwork` to
  draw the source with the built-in generator instead of importing one. `Seed`
  (with `New seed`) selects a design and `Intricacy` (1-10) deepens every layer;
  the amount of drawing only ever grows with it. The pattern is composed in the
  current wedge the way an engraved mandala is drawn - a layered centre (nested
  rosette, ray spokes, bead rows), then shape rings of shaded leaves, tulips,
  lenses, topographic bundles, feathers, scallops, chevrons, rayed fans, diamond
  mesh, lace scales and bead rows, with separator bundles, stud flowers and dot
  rows between them, closed by a scalloped multi-line rim. Detail counts are
  driven by physical spacing - contour fills, studs, dots, barbs and hatch lines
  are placed one every few millimetres along the arc - so the design gets
  complicated the way an engraving does rather than by repeating one texture.
  The bead rows, stud flowers and dotted rings are ornaments rather than
  structure, so they have their own spacing: `Ornament spacing` (1.0-8.0,
  default 2.0) is how far apart they sit as a multiple of the engraved
  hatching's pitch. 1.0 packs them edge to edge and reads as printed wallpaper,
  2.0 is the sparse default, and 4.0 or more leaves a few ornaments per band.
  That is the control for how wallpaper-like a design looks; the shaded
  leaves, lenses, separators and rim arcs keep their own spacing. It maps to
  `random_pattern(ornament_pitch=...)`, whose default is
  `generative.ORNAMENT_PITCH`.
  The result is clipped, mirrored, offset, auto-fitted and saved exactly like an
  imported image, so one seed plus the other controls reproduces the same
  G-code. The seed changes the *structure*, not just the phases: it picks one of
  five composition styles (`floral`, `geometric`, `woven`, `beaded`, `mixed`),
  the ring count, the band-width ladder, how much of the disc the centre and rim
  take, how tightly each layer packs, and whether a shape repeats once or twice
  per wedge - the style name is shown next to the seed. Counts, radii and phases
  come from mathematical sequences (golden angle, Weyl, van der Corput,
  Fibonacci, primes), not from unseeded noise.
  Drawn shapes are hatched the way an engraved botanical plate is: a leaf is an
  irregular outline with nested contour lines, radial ribs every few
  millimetres and a centre vein, so the pattern reads as hand-drawn line work
  instead of empty mechanical rings.
  `Region overlay` sets how much neighbouring radial regions share: 0 tiles the
  rings edge to edge, 0.2 (the default) braids them slightly, 0.5 and up
  interpenetrate heavily. The bands grow as they overlap so the disc stays
  covered and no shape is stretched - each ring simply draws a larger version
  of itself. This is the knob for making a design look denser and more complex
  without adding more rings.
- **Natural motifs.** `Motif folder...` loads a folder of black-on-white
  PNG/JPG shapes - leaves, shells, fish, feathers - and `Use natural motifs in
  patterns` swaps them in for the drawn shape rings while the separators, studs
  and rim stay. Each ring draws from a pool of one to three motifs, so the seed
  *combines* natural shapes around the ring rather than repeating one; a share
  of the copies overlays a smaller second motif to form a hybrid, alternating
  copies can be mirrored, and every copy is deliberately larger than its band
  and drifts in and out of it so the shapes overlap their neighbours. The ring
  count drops in this mode so the motifs stay large enough to recognise. The
  `Image threshold`, `Treat light pixels as ink` and `Trace detail` settings
  apply to the motifs too (use invert for white-on-black artwork); traced
  motifs are cached until the file or those settings change, and only the
  motifs the current seed will place are traced. `Seed` decides which motifs,
  how many copies, their orientation, tilt, mirroring and packing.
  Two sets ship ready to use (see `..\motifs\README.md`): `..\motifs\nature`
  holds 150 real organism silhouettes from PhyloPic - birds, cats, elephants,
  fish, dolphins, insects, jellyfish, plants - with per-file credits, and
  `..\motifs\nature-drawn` holds the earlier code-drawn set.
  `..\tools\fetch_phylopic_motifs.py` fetches more organisms,
  `..\tools\make_nature_motifs.py` redraws the drawn set, and
  `..\tools\fetch_nature_motifs.py` pulls free silhouettes from Wikimedia
  Commons. In motif mode each shape is drawn with two smaller nested copies
  inside it, so real outlines read as engraving rather than as flat cut-outs.
  Intricacy 10 is a full engraving: in a 12-division 181.3 mm frame it draws
  about 13,500 mirrored contours and 310,000 points, roughly 390,000 G-code
  lines and 13,500 pen cycles; the build takes about a second and saving the
  program about twenty. Lower levels are proportionally lighter. The
  artwork-only controls (open button, threshold, invert, trace detail) are
  disabled while this mode is on.
- **Kaleidoscope.** The source is centred on the apex and clipped to a
  half-wedge of `180 / Divisions` degrees, then placed `2 * Divisions` times
  around the circle, alternating mirrored copies so 360 degrees tile exactly.
  With `Mirror alternate sectors` off the wedge repeats without reflection,
  which gives a pinwheel instead of mirror symmetry. `Rotate source` chooses
  which slice the wedge samples.
- **Image placement.** `Image offset X/Y` moves the source inside the fixed
  frame, in millimetres of the finished design, and the same values can be set
  by dragging in the preview: the wedge, the design bounds and the machine
  limits stay where they are and only the image moves. Content pushed outside
  the frame is clipped, so a drag can empty the wedge — the preview and log show
  that immediately.
- **Printable bounds.** `Bed diameter`, `Bed margin` and `Gantry reach radius`
  are typed values that feed both the preview and the planner, with the
  resulting `Bed allows … / reach allows …` shown underneath. `Fit radius` is
  the radius the design is fitted to and clipped at; `Fit design to bounds`
  scales `Source size` so the design's natural radius matches it, and
  `Auto-fit after a division or rotation change` keeps it matched while the
  design changes. The default 181.3 mm is 0.98 x the 185 mm reach, and the
  planner still clips the saved program at the real printable limit if a typed
  bound is larger. `Source size` and every bound field are free numbers: the
  old 400 mm source cap and 300 mm bound caps were arbitrary guards, and the
  spin boxes now accept up to 1,000,000 mm (the fit radius is what actually
  keeps the plot on the bed). Auto-fit only ever rewrites `Source size`, so a
  huge source is scaled down to the fit radius before it is clipped and planned.
  Typed numbers are never rewritten by auto-fit: changing the seed, the
  intricacy, the divisions or the fit radius scales the drawing internally
  (the scale is printed in the log and the bounds note) and leaves every field
  exactly as entered. `Fit design to bounds` is the one button that writes a
  fitted value into `Source size`.
- **Output.** `Tolerance`, `Fill spacing`, `Feed rate` and
  `Theta tangential speed` are the same settings as the main app, and the saved
  file uses the same preamble, pen contract, clipping and end-of-print park.
  Fill spacing stays `0` (outlines only) by default.
  `Pen tip diameter` records the physical tip - the machine's Sakura Pigma
  Micron 005 is 0.20 mm, which is also the default. It sets the pen-width
  compensation applied to imported SVG artwork (the artwork is shrunk by one
  tip width so the outside of the stroke lands on the intended outline), the
  gap fill bridging tolerates, and is written into the saved program's header.
  Generated patterns and traced images are not compensated.
  `Tolerance` is the accuracy budget: the emitter subdivides each draw move so
  the commanded path stays within that many millimetres of the intended line on
  the bed. It binds hardest where the bed rotates most per millimetre - tight
  curves near the centre and long sweeping arcs - so a coarse value shows up as
  wobble in the middle of a mandala, and **on a coarse value the rows themselves
  are commanded to drift into their neighbours**: measured with
  `tools\check_gcode_motion.py`, programs saved at `Tolerance 1.0` carried bows
  of 1.2-1.9 mm against a 2 mm row pitch (62-95 % of a pitch), while 0.15 bounds
  it to 0.15 mm (7 %) for about 0.15 % more moves. Keep it at 0.1-0.15 unless a
  source is so detailed that the extra points cost too much. Saving a program logs the worst deviation
  the file actually contains and where it sits; on a 212k-move mandala, going
  from 1.0 mm to 0.1 mm costs about 0.1 % more moves and cuts the worst
  deviation from 0.9 mm to 0.1 mm.
- **Remembered setup.** The app saves its settings to
  `kaleidoscope_settings.json` next to the script (git-ignored) whenever it
  closes and whenever a motif folder is chosen: the motif folder, source path,
  seed, intricacy, divisions, mirror, rotation, source size, image offsets,
  threshold, trace detail, every printable bound, tolerance, fill spacing, feed
  rates and the mode checkboxes all come back on the next launch. On a first
  run with no settings file, the motif folder defaults to `samples\png` if that
  folder exists (otherwise `motifs\nature`) and both **Use natural motifs in
  patterns** and **Generate a random pattern** are ticked, so the app opens on
  a pattern built from those images. A file that would trace into more than 200
  contours or 4,000 points is skipped with a log line - that means it is a
  whole drawing rather than a single shape, and the affected ring falls back to
  the drawn families.
- **Motifs in use.** `Motifs in use` caps how many images from the folder a
  design may draw on, and it defaults to **10**: the app picks that many at
  random from the folder - `New selection` draws a different random set - and
  only those are traced, offered to the generator and cached. A folder of 150
  organisms therefore costs about ten traces instead of the whole set, which is
  what keeps the launcher from grinding through every PNG. Raise the number if
  you want a wider palette, lower it for a tighter look; the choice, the
  selection and the folder all come back on the next launch.
- **Preview view.** The preview is a flat bed-frame view — bed circle, reach
  circle, the sampled wedge and the design — with the same camera gestures as
  the main app: the wheel zooms about the cursor (10 % to 2000 %), `Shift`-drag
  or middle/right-drag pans, and the `+` / `-` / `Reset view` buttons with
  `Ctrl` `+` / `-` / `0` do the same from the keyboard. A plain drag still
  moves the image inside the fixed frame, and that drag is scaled by the zoom,
  so it stays accurate when you are zoomed in. The current zoom is shown next
  to the buttons and in the preview's status line. There is no OpenGL playback;
  use the main app when you want the simulated machine motion.

### Maps tab

The window opens on the **Kaleidoscope** tab and also carries a **Maps** tab: a
vendored, offline copy of
[`piebro/plotting-maps`](https://github.com/piebro/plotting-maps) (MIT), which
turns an OpenStreetMap export into a plotter SVG.

- **A separate plotting function, not a mode.** The tab owns its controls and
  its output. `Download Map` opens a normal save dialog and writes an ordinary
  SVG; nothing there changes the kaleidoscope source, design, settings or
  G-code, and nothing from the kaleidoscope feeds the map.
- **Offline by construction.** `plotting_maps/` holds the page with its own
  `d3` and `proj4` copies and no analytics, so the tab never reaches the
  network. See `plotting_maps/README.md` for the pinned upstream commit, the
  local modifications and the licence notes.
- **How to use it.** On openstreetmap.org use *Export → Manually select a
  different area → Overpass API* to download an `.osm`, then **Upload OSM
  Export** in the tab, set the paper size, zoom and drag the map into place,
  and **Download Map**. The saved SVG is an ordinary vector file that can be
  loaded into either app or any other tool.
- **Lazy start.** The web view is created the first time the tab is opened, so
  the kaleidoscope starts as quickly as before and an environment without
  WebEngine can still plot.

## What it emits

- `G21` (mm), `G90` (absolute), `G94` (units/minute feed), `G17` (XY plane),
  and `G54` (the registered work-coordinate frame)
- a header comment recording the bed ratio, theta offset, feeds, tolerance and
  the A-axis limits the planner assumed (`(A limits assumed 15000 motor
  deg/min, 3000 motor deg/s^2)`), so a program can always be traced back to its
  motion settings - compare that line with the controller's `$$` after any
  settings change, because a converter assumption above what the controller
  allows makes the emitted feeds unachievable and the time estimate optimistic
  (`tools\make_theta_calibration.py` writes a plot that measures the
  bed's real ratio: a circle plus a two-turn spiral, where a wrong ratio shows
  as an offset that doubles on the second lap)
- the bed is re-registered at every contour by default: the planner subtracts
  whole revolutions from the bed angles, which leaves every drawn point where it
  was but keeps the commanded `A` within about one turn instead of letting it
  wind up over the program. On a machine with a small A-axis scale error the
  positional error grows with the commanded angle, so this removes most of the
  drift seen at high `A` values. The main app exposes it as
  `Re-register the bed each contour (keep A small)`; turn it off to reproduce
  older programs. It bounds the symptom, not a mis-calibrated A axis - the
  calibration plot above is still how the true ratio gets measured.
- pen-up travel is emitted as **fed `G1` moves, never `G0`**. A rapid ignores the
  program's `F` word and runs at the controller's `$110`/`$111` maxima, so a
  travel would run at whatever rate the controller is configured for - on this
  machine 8000 mm/min = 133 mm/s on the Y axis that carries most of the mass -
  while the preview, the time estimate and `Travel rate` all assumed 3000. Fed
  travel makes the machine do what the file says: the long crossings and the
  end-of-program park now run at the modelled rate, which is also the slowest
  and safest the gantry ever moves. The cost is small - the whole of `ben.gcode`'s
  1777 mm of pen-up travel takes 44 s at the modelled rate against 42 s if every
  move ran at the 8000 ceiling - and a bed re-registration spin still runs at
  the A rate cap, which is why its `F` is larger than `Travel rate`: the feed is
  the coordinated rate over a path that counts A motor degrees as millimetres.
- `G1` draw moves (pen down)
- `X Y` in mm in the machine's active work-coordinate frame; `A` =
  **motor-shaft degrees** (already multiplied by `Theta ratio`)
- `M5` / `M3` pen up / down by default. `Z` moves are available only when
  **Use Z axis** is deliberately enabled; do not enable it for this machine,
  whose controller's Z slot is unwired. **Wait for GP27 toolhead ready** is on
  by default, so each M3/M5 transition is acknowledged with the
  RP23CNC-resident `G65 P115` bounded macro instead of a fixed `G4` dwell;
  uncheck it to go back to the dwells if the controller is missing the handshake
  prerequisites. Its companion **Lift pen and continue if the GP27 handshake
  times out** is also on by default and turns a timeout into a logged warning
  plus a pen lift instead of a mid-print abort.
- `M2` at end

The converter normalizes the clipped SVG around its geometric center before
planning. That center is emitted as `G54 X0 Y0`, matching the pen-at-bed-center
frame registered by P100 (or the narrowly scoped temporary commissioning
reference). After the final pen-up the program ends with a `G53 G0` move to a
configured machine-coordinate park position (defaults to the homed rest
position). First it asserts Aux0/GP28 (`M65 P0`) to request a full retract to
the toolhead's GP2 lift-home switch, waits for the clear-ready acknowledgement
(`G65 P115 Q0` when the handshake is enabled, otherwise the fixed `G4 P3.0`
retract dwell), and releases Aux0 (`M64 P0`), so the pen is fully up before the
gantry clears the rotating bed.

The authoritative host-to-controller contract is
[`../docs/integration/INTERFACES.md`](../docs/integration/INTERFACES.md).

## Radius-aware A-axis feed

The converter must not treat the A-axis portion of `F` as a fixed bed-surface
speed. Because `A` is emitted in motor-shaft degrees and the measured bed
reduction is 12.0332:1, the A rate required for a target tangential pen speed
pen's instantaneous radius from the bed center:

```text
A_feed_motor_deg/min = (4331.97 × tangential_speed_mm/min) / (2π × radius_mm)
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

Each setting lives with the thing it changes. Only **Preview settings** is
display-only; every other group changes the emitted program.

- **Geometry** — scale, tolerance, artwork placement (see *Placing the
  artwork* below), Flip Y, pen-stroke compensation, and
  **Expand strokes to outlines** (off by default — a pen already marks its own
  width, so drawing each stroke's centerline once is correct and produces far
  fewer M3/M5 cycles than outlining the stroke width).
  **Fill wide strokes** (off by default) fills a stroke only when its width is
  at least **Stroke fill ratio** times the pen diameter: a stroke that wide is
  drawn as parallel passes spaced one pen diameter apart, while every thinner
  stroke stays a single centerline. This renders genuinely thick strokes solid
  without paying the outline penalty on thin ones.
  **Tolerance** also bounds how far a drawn move may bow from a straight
  bed-frame line: because the controller interpolates X/Y/A linearly across one
  move, a move that spans bed rotation is subdivided so each chord stays within
  tolerance of the intended path.
- **Fill** — everything about hatching the artwork: spacing (0 = outlines
  only), pattern, angle, `Fill source`, shade levels/angle step, the
  pattern-specific size fields, the image-tone sampling resolution, and
  **Keep pen down between fill trails** (off by default; it only ever joins
  generated fill trails, never the artwork's own strokes). See *Fill* below.
- **Motion** — draw/feed rate and travel rate. Values that cannot describe a
  meaningful X/Y/A program (for example, zero feed, a nonpositive theta ratio,
  an invalid A-axis name, or a bed margin that leaves no drawable area) are
  rejected before preview or save.
- **Machine** — the machine-side setup the program is clipped and parked
  against: `Bed dia mm`, `Bed margin mm`, `Gantry reach radius mm`, and the
  end-of-program `Park X/Y machine mm` in G53 machine coordinates.
- **Theta kinematics** — theta axis/ratio/resolver/cost settings (`Theta ratio`
  defaults to 12.03324, the measured effective ratio of the 60T→720T pulley
  pair).
  - **Theta mode** and **Theta resolver** are combos of the implemented
    strategies, so an unsupported value cannot be entered.
  - **Theta tangential speed mm/min** is the requested surface speed caused by
    A-axis bed rotation during drawing. It does not change X/Y-only output.
  - **Max bed step deg** (default `15`) is the hard limit on how far the bed may
    turn inside one drawing move. Exceeding it parks the bed and lets the gantry
    trace the move in X and Y, which is exact because the artwork is already
    clipped to the reachable disc. Lower it if a large turn mid-stroke leaves a
    drag mark, an ink blob where the machine decelerated into the corner, or a
    slight rotation of everything drawn after it; it can go to `0`, which parks
    the bed whenever a turn is needed. Cost: less rotation means more gantry
    travel, so plots get slower — measured on a dense 461-contour mandala,
    dropping 15 -> 10 deg took the total bed rotation from 30 to 52
    revolutions for the same drawing. The tuning ladder is 15 -> 10 -> 5: 15 is
    what the guard was designed around and is the current default, and 10 and 5
    are the field-tested steps down if a turn still marks the paper.
  - **Bed rotation is bounded where the machine cannot follow it.** The planner
    keeps the bed parked instead of swinging it when the axis-lock solution for
    a segment would rotate more than 15 deg, or when a stroke passes close
    enough to the bed centre that no pure-X or pure-Y machine move exists. Those
    strokes are traced by the gantry in X and Y, which is exact because the
    artwork is already clipped to the reachable disc - rotation buys no reach
    there, only risk. Pen-up moves that rotate the bed are emitted as fed moves
    (`G1 ... F... (travel)`), never as a `G0` rapid, so a `theta_wrap`
    re-registration of a whole revolution cannot outrun the A axis.
  - The converter assumes the A axis can hold **15,000 motor deg/min**
    (20.8 bed deg/s; 20,000 or 27.7 bed deg/s was verified on paper first, and
    the operator settled at 15,000 for margin) and
    **3,000 motor deg/s²** (250 bed deg/s²). Keep the controller's `$113`/`$123`
    equal to those: torque demand scales with acceleration, so `$123` is the
    setting that turns the bed's mass into force on the belt and motor.
- **Pen** — `Pen stroke mm` (the physical pen tip), Z heights, pen dwells, pen
  up/down commands, Use Z, and the two GP27 handshake options (both on by
  default since 2026-10-04; see `WSW-20261004-001`).
  - **Pen stroke mm** (`pen_diameter_mm`, default 0.3) is the real pen tip
    width. It drives ink-size reporting, pen-width compensation, the
    *Fill wide strokes* threshold, and the keep-down connector gap guard.
  - **Pen down ms** (`pen_down_ms`, default 2500) is the dwell after every
    `M3`. It covers the toolhead's warm contact seek, which starts from the
    ~1.2 mm `M5` clearance and finishes in 2-3 s.
  - **Pen down first ms** (`pen_down_first_ms`, default 10000) is the dwell
    after the program's **first** `M3` only. The toolhead parks on the GP2 lift
    switch, so that one has to travel the whole retract distance before it
    reaches paper — measured at about 7 s on the installed mechanism. Without
    the longer first dwell grblHAL starts the first stroke mid-descent and the
    leading section of the path is drawn in the air. Every later `M3` starts
    from the `M5` clearance height and uses `Pen down ms`. Starting a program
    when the pen is already off GP2 — for example right after a manual
    `M3`/`M5` warm-up — only wastes the extra first-dwell time.
  - Both GP27 options require the `P115.macro` file installed on the RP23CNC,
    GP27/U3-to-`PRB` polarity verified, the flashed toolhead carrying
    `GP27_NORMAL_STATUS_ENABLED` plus `GP27_TRANSITION_LOW_MS`, F-05A passed
    (2026-09-29), and the selected pen qualified for contact/clear. The
    handshake replaces fixed `G4` dwells with a bounded controller-side
    acknowledgement; it is not a host-PC serial wait. A strict P115 timeout
    raises error 39 and aborts the running program, which is why unchecking
    **Wait for GP27 toolhead ready** is the supported fallback. The first `M3`
    carries a longer `P115` completion bound derived from **Pen down first
    ms**, because that seek starts at the GP2 lift-home switch and takes about
    7 s.
  - **Lift pen and continue if the GP27 handshake times out** is on by default
    and emits `G65 P115 ... A<lift> W2` around each normal M3/M5 transition. A
    timeout then prints a controller warning, issues `M5` to lift the pen to
    the fail-safe state, dwells for the pen-up clearance, and lets the program
    continue instead of aborting. The end-of-print full-retract wait still
    warns and dwells (`W1`) without an extra lift. It only applies with
    **Wait for GP27 toolhead ready** enabled; it trades a mid-print abort for a
    lifted pen (a missed `M3` then draws that stroke in the air) plus a console
    warning, and it masks a genuinely stuck toolhead signal - uncheck it to
    stop on a fault instead of finishing the sheet.
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
- **Preview settings** — display only: playback speed, the motion estimate
  scale, and three preview colors: **Undrawn** (artwork not yet drawn), **Drawn**
  (the drawn portion / final color), and **Motion** (the generated `G1` X/Y
  pen-down path). **Show X/Y pen-down path** is on by default and overlays that
  generated path in the Motion color; turn it off when inspecting only the
  upright artwork. Pen-up travel, crosshairs, tool marker, and pen-tip footprint
  remain hidden.
- **Show machine reach guide** draws the `Gantry reach radius mm` boundary as a
  green circle around the bed center, and the preview status line reports the
  artwork radius against it. Both are measured before clipping, so artwork the
  reach cap would trim shows up as over-scale instead of quietly disappearing.
  The guide models the converter's reach radius only - it does not include the
  controller's G54 work offset, so it is not a machine-envelope check, and it is
  drawn only once a preview exists.
- **Over-scale artwork is called out, not just clipped.** A cropped plot still
  looks like a finished drawing, so when the measured artwork radius exceeds the
  reach cap the guide turns red and the preview states the ratio, e.g.
  `Artwork radius 1018.2 mm vs the 185.0 mm reach: most of the drawing is
  outside the drawable circle.` Two fits are offered next to that notice, each
  enabled only while it would still change something:
  - **Fill bed** sizes the bounding box to the drawable diameter, so the box
    edges touch the reach circle and the drawing fills the bed. The four corners
    fall outside the circle and are clipped - about 9% of the image area on a
    1440 x 1080 trace. It sizes in both directions, so a small drawing is
    enlarged to fill the bed.
  - **Fit inside** keeps every point of the drawing inside the reach circle, so
    nothing is clipped. The bounding box corners land on the ring and the box
    edges sit inside it, which leaves visible margin around the drawing. Like
    **Fill bed** it sizes in both directions, so a small drawing is enlarged to
    the largest size that still fits.
  Both fits also recenter the artwork on the bed center, clearing any manual or
  dragged `Artwork offset`. SVG document units are not millimetres: a trace
  exported as `width="1440" height="1080"` plots 1440 x 1080 mm at
  `Scale = 1.0`, which is roughly four times the drawable circle on this
  machine. For that file **Fill bed** lands at `Scale 0.2605`
  (375 x 281 mm) and **Fit inside** at `Scale 0.2085` (300 x 225 mm).
- **Fit mode.** `Scale` is normally set for you. The `Fit` setting next to it
  chooses how:
  - `Fill bed (auto)` (default) sizes the artwork's bounds to the drawable
    circle on every build.
  - `Fit inside (auto)` sizes it so every point stays inside the circle.
  - `Manual (use Scale)` uses the `Scale` field, which is the only mode where
    that field is editable.
  While an auto fit is active the `Scale` box is read-only and shows the scale
  the last build used, so nothing is hidden. The fit runs before planning, which
  means artwork authored at a physical size - a 200 mm drawing, for example -
  opens at the fitted size rather than its document size; choose `Manual` for
  literal sizes. The two buttons beside the preview select the fit as well as
  applying it, so one button press becomes the standing behaviour.
- **The preview says when it is out of date.** Building a preview is manual, so
  changing any setting that affects the plan marks the preview with
  `Settings changed since this preview - press Preview to rebuild it.` Playback
  speed, the motion estimate scale, and the preview display toggles do not.
- **Placing the artwork.** `Artwork offset X mm` and `Artwork offset Y mm` move
  the artwork's center away from the registered bed center, which is how a
  drawing whose bounding box is not its visual center gets positioned by hand.
  Both are signed and default to `0`. In the preview, **left-drag moves the
  artwork** and **Shift+left, middle, or right drag pans the view**; the wheel
  zooms and a double-click resets the zoom. Dragging updates the two fields, and
  pressing Preview re-plans with the new placement, including re-clipping to the
  reach circle. While dragging, the displayed part is the existing plan
  translated, so the reach circle - not the drawn artwork - is the authority on
  what will survive the next build.
- Pressing **Preview** shows the current build stage, percentage, and elapsed
  time. SVG parsing, motion planning, and clipping run in the background so the
  window remains responsive. The expensive contour/theta plan is built once and
  shared by the preview and complete command-list generation. Preview and Save
  G-code are temporarily disabled until that shared data is ready.
- Press **Cancel** during preview generation to stop an unexpectedly large job.
  Cancellation safely unwinds at geometry/planning checkpoints and keeps the
  last completed preview visible.
- The saved `.gcode` file is the complete generated program, including modal
  setup, M3/M5 commands, G4 dwell lines, comments, and M2. The in-app command
  list was removed; use **Save G-code** and open the file to inspect it.
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
- **Wait for GP27 toolhead ready** and **Lift pen and continue if the GP27
  handshake times out** are both checked by default (2026-10-04), matching how
  this commissioned machine is run. A default program emits `G65 P115 Q0` after
  the opening M5 and `G65 P115 Q1` after every subsequent M3/M5 transition,
  with the recover (`W2`/`W1`) arguments. That requires `P115.macro` on the
  RP23CNC, the GP27/U3-to-PRB wiring, and the flashed toolhead's
  `GP27_NORMAL_STATUS_ENABLED` plus `GP27_TRANSITION_LOW_MS`; if any of those is
  missing the program errors `39` mid-print. Uncheck **Wait for GP27 toolhead
  ready** to go back to the fixed `G4` dwells. F-05A passed on 2026-09-29; the
  roughly hourly timeout seen in real printing is still unexplained, so watch
  the console: with recover on, the macro prints `P115 WARNING ...`, issues
  `M5` to lift the pen, dwells, and continues on the next command.
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
- `Gantry reach radius mm` (default 185.0) caps the drawable circle at the
  gantry's reachable radius from the registered bed center. Because the bed
  rotates freely, the safe drawable area is this circle rather than the full
  bed; it keeps emitted coordinates inside the controller's X/Y envelope so
  artwork at the rim cannot trip `Alarm:2 - Soft limit`.
  The binding direction is **+Y**, and the edge is the controller's soft-limit
  envelope, not the switch: grblHAL sets a homed axis's envelope to
  `[max_travel + pulloff, -pulloff]` when hard limits are enabled, so `$27`
  (homing pull-off) shortens the homed end by that amount. With `$130=455`,
  `$131=451`, `$27=10` and the bed center registered at machine
  `-232.449, -195.270`, the enforced work limits are X `-212.551..222.449` and
  Y `-245.730..185.270` — so +Y is 185.270 mm from the bed center. Note that
  `$21` matters too: with hard limits off the pull-off term is zero and the +Y
  edge moves back to 195.27 mm. Re-derive this value after every HOME +
  REGISTER, since the bed center is what moves.
- **Fill.** `Fill spacing mm` sets the on-paper distance between fill lines.
  The default is `0` — outlines only — so a conversion never adds fill the
  artwork did not ask for. A positive value opts into hatching; keep it well
  under the smallest feature you want filled, because a coarse spacing leaves
  one or two short fragments inside a small closed shape. (Tone artwork with an
  embedded image or gradient gets a 4 mm starter automatically, since outlines
  only would draw nothing for a photo.)
- `Fill source` decides where the fill geometry comes from:
  - `Auto (recommended)` hatches the SVG's own shapes, and switches to image
    tone only when the artwork's tone lives somewhere the vector path cannot
    see it: an embedded `<image>`, a `url(#...)` gradient/pattern fill, or a
    photo imported directly (see below).
  - `SVG shapes (stays inside)` always hatches the SVG's own regions. Fill is
    clipped to those regions, so it cannot run over the outlines. A raster input
    has no vector regions, so it still resolves to image tone.
  - `Image tone (photos, gradients)` renders the SVG and hatches its pixels.
    It follows visible tone rather than vector regions, so a pass can overshoot
    an edge by up to `min(active spacing / 3, 1.0) mm` and hatch runs over dark
    outlines. `Raster px/unit` sets the sampling resolution; higher is more
    accurate and slower.
- **A photo or scan can be opened directly.** `Browse` accepts `.jpg`, `.jpeg`,
  `.png`, `.bmp`, `.webp`, `.tif` and `.gif` as well as `.svg`; no SVG wrapper
  is needed. The image is tone, so it always hatches from its pixels - a photo
  has no vector outlines for `SVG shapes` to use.
  - Do **not** convert the photo to a traced SVG first. A bitmap trace
    (VTracer, Inkscape "trace bitmap", most online converters) turns continuous
    tone into hundreds of flat shapes: the gradients are gone, `Fill source
    Auto` resolves to `SVG shapes` because that is all the file contains, and
    hatching each traced layer separately takes minutes. The app logs a
    `looks like a traced bitmap` warning when it sees more than forty filled
    elements and no image or gradient. Open the original `.jpg` instead: one
    fill reads the tone.
  - Tone is luminance: each pixel becomes `1 - (0.2126 R + 0.7152 G + 0.0722 B)`
    times its alpha, so a colour photo is converted to grey by the same rule a
    black-and-white print would use, and that grey drives the wave amplitude
    under `Fill pattern = gradient waves (sine_gradient)`. Dark features grow
    waves, light ones flatten them.
  - A raster is sampled at its own pixels (one view unit is one source pixel), so
    `Raster px/unit` does not apply; images wider than 2400 px are scaled down
    smoothly to that cap before sampling.
  - An auto fit has no outlines to measure, so it sizes the artwork from the
    image bounds. That needs the paper scale before the fill can be built at a
    millimetre spacing, which the preview thread resolves in one pass.
  - Practical starting point for a portrait: `Fill spacing 4`,
    `Fill pattern gradient waves (sine_gradient)`, `Gradient wave amplitude %`
    50, `Connect sine rows` on, `Fit = Fill bed`. A bed-filling photo is about
    74,000 points and four seconds; at `Fill spacing 3` it is about 131,000
    points and seven seconds.
- Any element fills the regions its **closed** outlines enclose, whether it
  declares a fill or is stroke-only. Open subpaths have no bounded interior and
  never receive fill, so fill cannot leak across artwork built from open
  segments (the Calder Hall and F15 plotter-ready exports, for example), and a
  filled-but-open path is not implicitly closed into a region whose boundary the
  pen never draws. Polyline artwork that *looks* closed still has to close its
  subpath — with `Z`, or by repeating the first point — for that region to fill.
- The Qt log reports what fill actually did after each preview, for example
  `Fill: 4 mm crosshatch, 172 hatch passes inside the SVG's own regions.` When
  there is nothing to hatch it says so and names the setting that would change
  the result.
- SVG presentation attributes are resolved through the element tree, so `fill`,
  `stroke`, `stroke-width`, `fill-opacity`, `stroke-opacity`, `visibility`, and
  `opacity` declared on a wrapping `<g>` apply to its children the way a
  renderer applies them. Line art that declares `fill="none"` on a group is
  therefore never treated as a solid silhouette, while an element that declares
  no fill anywhere still takes the SVG initial value of black. `display="none"`
  suppresses the element and its subtree, and `visibility="hidden"` or
  `"collapse"` is inherited.
- `Fill spacing`, the pattern size fields, and the curve `Tolerance` are treated
  as on-paper (machine-space) values. When the artwork is scaled below `1.0`,
  the fill and curve flattening are generated coarser in SVG space so the final
  on-paper density stays constant and the preview evaluates proportionally fewer
  contours instead of building a full-resolution lattice and shrinking it. The
  image-tone path applies the same conversion, so `Fill spacing 4` is 4 mm on
  paper whether the SVG is authored in millimetres or in a 1000-unit viewBox.
- `Fill pattern` selects the infill. In list order: `linear` (parallel lines),
  `crosshatch`, `gradient waves (sine_gradient)`, `diagonal`,
  `diagonal_crosshatch`, `triangular`, `cubic` (isometric), `diamonds`,
  `hexagonal`, `circles`, `dots`, `stipple` (tone dots), `halftone` (variable
  dots), `single line (tsp)`, `waves` (uniform sine rows), `gyroid`, and
  `concentric` (inset loops), and `terrain` (topographic contours). `waves` and
  `sine_gradient` draw the fill as sine
  rows instead of straight lines. `linear` is always one parallel-line family; darker fills
  increase density by reducing spacing, not by changing the pattern into another
  pattern. The vector fill path treats each pattern as a full layer and clips
  pattern segments to the filled contour boundary. Compound SVG paths are clipped
  as one even-odd region, so holes cut the infill layer.
- The three dot-family photo styles read the image tone directly, so like
  `sine_gradient` they are drawn at the requested pitch and ignore `Shade
  levels`:
  - `stipple` places blue-noise dots whose **density** follows tone - the
    hand-stippled portrait look. `Dot spacing mm` is the minimum gap between
    marks and each mark is a small dot (a circle about the pen tip across,
    never under 0.5 mm), so it survives the geometry filter at bed-filling
    scales. The field is deterministic, so the same photo always stipples the
    same way.
  - `halftone` places a fixed-pitch grid of dots whose **radius** follows tone
    (ink area tracks darkness, the printed-halftone look). `Fill angle deg`
    rotates the screen and `Dot spacing mm` sets the pitch.
  - `single line (tsp)` stipples the photo then walks the points
    nearest-neighbour into one continuous pen-down path - the single-line
    portrait style. `Dot spacing mm` is both the minimum point gap and the
    search grid size. It is a greedy tour, not an optimal one, so a very dense
    stipple still builds quickly.
- `Fill pattern = terrain` is the topographic-map fill: contour lines drawn the
  way a map draws a hillside, instead of `concentric`'s insets of the region's
  own outline.
  - **Image tone (photos, gradients): the picture's own shading is the
    terrain.** Darker pixels are higher ground, so the lines trace the faces
    and features of the photo - a topographic portrait - and a blown-out sky
    stays blank paper while hair and shadows fill with contours. `Fill
    spacing mm` sets the level interval from the image's own mean tone gradient
    (over its inked area), so a busy photo and a soft one both draw at roughly
    the requested pitch; the ladder always spans the ink's own tone range and
    keeps at least six bands, so a thin stroke is never lost between rungs.
    **Lines that would crowd closer than half the spacing are then skipped,
    longest line first**: a hard tone edge (an outline, a silhouette) is traced
    once or twice instead of stacking every level into a heavy band. Without
    that pass a portrait's average gap matches the request (4.2 mm at 4 mm);
    with it the portrait measures 5.7 mm because the crowded edge copies are
    gone, so a very outline-heavy drawing needs a smaller `Fill spacing` than
    a photo for the same ink coverage. `Terrain size mm` is the smoothing
    radius used before contouring - 0 follows `Fill spacing mm / 2`; larger
    values merge fine tone into broader landforms. `Shade levels` does not
    apply, because the tone is the elevation rather than a density multiplier.
  - **Flat SVG shapes (SVG shapes fill source): a synthetic height field.**
    A flat-filled element has no tone gradient inside it to trace, so the hills
    come from a deterministic fractal field and the fill still reads as
    terrain. `Terrain size mm` is then the width of one hill (0 follows
    `Fill spacing mm × 8`) and `Shade levels` tightens the contour interval to
    darken the fill, like the line patterns. The vector path clips the level
    sets to the filled shape, so a terrain fill cannot run over the artwork's
    outlines.
  - Cost is comparable to the other dense fills: the tone is sampled at half
    the contour pitch (never coarser than two source pixels) and the extracted
    segments are chained into long strokes, so one contour line is one pen-down
    move, not one per sample. The portrait above (532 x 563 px, fitted to the
    bed) loads in 0.38 s at 4 mm (825 contours, 22,000 points) and 0.8 s at
    2 mm (2,900 contours, 55,000 points), and the 4 mm program plans and saves
    in another 0.5 s (`tools\check_gcode_motion.py --strict` passes on it).
- The pattern combo lists readable labels over the stored values, so
  `sine_gradient` reads as `gradient waves (sine_gradient)` and `waves` as
  `waves (uniform sine rows)`; a settings file or a script still uses the short
  value, and either form can be typed. The gradient entry sits in the top three
  so it is visible without scrolling, and the log pane prints the converter
  core version on startup so a window left open across a change is obvious.
- Tone is amplitude **and** wiggle rate. This is SquiggleDraw's rule
  (`SquiggleDraw.pde`: `r = z/ystep*ymult` for the crest and
  `phase += z/xsmooth` for the frequency, where `z` is the pixel's darkness), so
  a dark area gets tall, tight waves and a light one gets flat, slow ones.
  `Gradient wave amplitude %` and `Gradient wave density %` are the two gains.
- `Fill pattern = sine_gradient` is the gradient fill: continuous adjacent
  sinusoids whose **amplitude follows the rendered tone**. Dark areas swell the
  waves until neighbouring rows just touch; light areas flatten them out. It
  reads a gradient as curvature, so it needs an image-tone source - `Fill source
  = Auto` already picks that for artwork with an embedded image or a
  `url(#...)` gradient/pattern fill. With `Fill source = SVG shapes` there is no
  rendered tone to read and the pattern falls back to a uniform sine hatch.
  - `Wave size mm` is the row pitch, in mm on paper. Left at `0` the rows
    follow `Fill spacing mm`; any non-zero value **overrides** `Fill spacing
    mm` for this pattern. It is the single scale for the whole wave: the
    wavelength is twice the row pitch and the crest height is
    `Gradient wave amplitude %` of the row pitch, so a 4 mm wave size gives
    4 mm rows, an 8 mm wavelength and 2 mm crests at the default 50 %.
    Measured on a 1000-unit artwork at `Fill spacing 4`: wave size 0 and 4 both
    give 4 mm rows / 8 mm waves / 2 mm crests and 65,026 points, wave size 2
    gives 2 / 4 / 1 mm and 262,236 points, and wave size 6 gives 6 / 12 / 3 mm
    and 29,192 points. The pitch drives the point count as `1 / pitch^2`, so it
    is the lever for build time.
  - `Gradient wave amplitude %` (default 50) is the crest height as a
    percentage of the row spacing. 50 makes the waves in a fully dark area
    touch the neighbouring row without crossing it; lower values keep the rows
    apart in the darkest areas.
  - `Gradient wave density %` (default 100) is how much darker tone tightens
    the squiggle, the way SquiggleDraw accumulates phase from brightness:
    `0` keeps one wavelength across the row and varies only the crest, `100`
    makes the darkest areas wiggle twice as fast as the lightest, `400` five
    times. A portrait reads best around `0`-`100`, where the tone is carried by
    crest height; higher values turn the photograph into texture, with dense
    squiggles in the shadows and long slow waves in the highlights.
  - `Connect sine rows` (on by default) joins the end of one row to the start
    of the next, so a gradient is drawn as one continuous pen-down serpentine.
    A join that would cross blank paper still breaks, so the pen lifts rather
    than drawing a mark outside the artwork.
  - `Shade levels` does not apply to this pattern: tone arrives as amplitude,
    not as extra fill families. A light gradient fades to flat hairlines rather
    than to nothing, because a hairline is the lightest mark the pen can make.
  - Render cost follows the point count, and the point count is
    `about 12 x width x height / (Fill spacing)^2` in SVG user units, so the
    spacing is the one control that matters: `Fill spacing 4` is about four
    times lighter than `2` and sixteen times lighter than `1`. A 4-6 mm spacing
    on a 1000-unit artwork builds in well under a second; 1-2 mm on the same
    artwork is hundreds of thousands of points to plan, preview and write out.
    An auto fit reads the artwork twice - once for the outlines it measures,
    then once to build the fill at the fitted scale - but the measuring pass
    carries no fill, so it costs milliseconds. `Fit = Manual` skips it.
- Consecutive passes are emitted head-to-tail, and the line families (`linear`,
  `crosshatch`, `diagonal`, `diagonal_crosshatch`, `cubic`) and the lattices
  `diamonds`/`triangular`/`hexagonal` keep the pen down between them when the
  connector is short. A dense fill is therefore drawn as one continuous zigzag
  instead of one pen cycle per pass. A connector is only drawn when it is within
  `max(Fill spacing x 0.85, Pen stroke mm x 6)`, so sparse hatching still gets
  separate passes and crosshatch still lifts between its two angle families.
  The preview draws those connectors, so a chained fill reads as one continuous
  serpentine rather than as separate strokes.
- The `waves`/`sine_gradient` rows in the vector path arrive as chained
  polylines: each sine row is one pen-down stroke rather than one contour per
  clipped sample. `sine_gradient` already emits continuous rows in the tone
  path, where `Connect sine rows` decides whether they are one stroke.
- The fill bleed margin is applied by pulling back the ends the clip creates,
  never by offsetting the region, so a pass cannot land outside the fill region.
  This matters for bitmap-traced artwork built from thousands of overlapping
  subpaths, where offsetting each subpath independently cannot preserve the
  even-odd region.
- `diamonds`, `triangular`, `hexagonal`, and `circles` each have a dedicated size
  field (`Diamond size mm`, `Triangle size mm`, and so on). When that field is
  left at `0`, the cell size falls back to `Fill spacing mm × 6` rather than
  `Fill spacing mm` alone, so an unset lattice does not degrade into an
  impractically dense (and slow) mesh.
- `Shade levels > 1` turns fill darkness into hatch density: darker fills receive
  denser spacing while preserving the selected fill pattern. Fill darkness comes
  from the fill colour, or from the stroke colour for closed line-art outlines.
  White and fully transparent elements are skipped, because a single pen cannot
  show them.
- [`../samples/svg/raster-shading-math.svg`](../samples/svg/raster-shading-math.svg)
  is an editable visual reference for the tone-to-hatch mathematics.
- [`../samples/svg/gradient-sine-demo.svg`](../samples/svg/gradient-sine-demo.svg)
  is a gradient sample: a linear fade, a radial orb and a vertical band. Select
  it with `Fill spacing 3`, `Fill pattern sine_gradient` and the default
  `Fill source Auto` to see tone as wave amplitude.
- When an SVG is selected, the Qt app inspects how the artwork declares its
  fill (filled elements, stroke-only elements, embedded images, paint servers)
  and says in the log what `Auto` will do with it. Tone-carrying artwork also
  gets tone-friendly starter values (`Shade levels = 4`, `Shade angle step = 45`),
  and gradient paint also logs a reminder that `Fill pattern = sine_gradient`
  plots it as continuous adjacent sinusoids.
