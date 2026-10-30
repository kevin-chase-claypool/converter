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

## ioSender configuration recovery

The repository keeps a validated ioSender `App.config` recovery snapshot in
`..\config\iosender\`, including the `HOME + REGISTER` and `PEN UP + PARK`
toolbar macros and direct Ethernet connection. Double-click
`..\backup-iosender-config.bat` after changing ioSender settings.
`..\restore-iosender-config.bat` restores the newest validated snapshot while
preserving the current file as `.before-restore-*`.

After changing controller settings, use **Settings: Grbl > Backup** in
ioSender first, then run the one-click backup so the complete `$$` and offset
files are refreshed.

The startup helper
`..\tools\install_iosender_config_backup_startup.ps1` backs up the last valid
config at every Windows sign-in. A failed or empty active config is rejected
and never replaces the last good backup. See
`..\config\iosender\README.md` for the complete procedure.

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
- `..\samples\gcode\headback-parked-test.gcode` - the back-of-head scallop
  stretch drawn twice with identical paper geometry: the upper copy turns the
  bed exactly as the real plot does (21 A-direction reversals), the lower copy
  parks the bed and draws in pure X/Y. For a two-pen overlay instead, run
  `make_headback_parked_test.py --split`: it writes
  `headback-test-bed.gcode` and `headback-test-parked.gcode`, which draw the
  same shape at the same spot so the second colour reveals where the two
  kinematics diverge. `headback-test-bed-slow.gcode` is the same bed copy at
  a quarter of its original feeds (`--split --feed-scale 0.25`) - if the slow
  copy lands on the parked copy, the plot's outline errors come from the
  streamed rate profile, not the geometry. Regenerate after re-plotting the
  source file.
- `..\samples\gcode\heraldic-bedfixed.gcode` - the full heraldic drawn with
  the bed **completely stationary** (Bed motion = `XY only`, A constant for
  the whole program). The decisive outline A/B: clean everywhere means the
  bed rotation is the smear source; still wobbly means the X/Y gantry or the
  pen. Regenerate from the app with **Bed motion = XY only**.
- `..\samples\gcode\a-reversal-diagnostic.gcode` - finds why the bed loses
  position on reversals: out/back arc pairs at three rates and two radii
  (mechanical play vs belt wind-up vs rate dependence), plus pen-up and
  pen-down tick/soak/tick stations (cumulative loss and drag torque). Mark a
  sharpie witness across the 60T pinion/motor face and the bed rim/frame
  before running. Regenerate with `..\tools\make_a_reversal_diagnostic.py`.
- `..\samples\gcode\a-ratio-deadband-test.gcode` - measures the effective
  bed ratio per quadrant (ticks before/after a commanded full revolution of
  A=4332 motor deg) and the approach-direction deadband (ticks arriving at
  A=0 from each side). A per-turn tick offset of ~1.75 mm at r=100 means the
  true ratio is the pure tooth count 12.000, not the calibrated 12.03324.
  Regenerate with `..\tools\make_a_ratio_deadband_test.py`.
- `..\samples\gcode\a-center-test.gcode` - one paper point visited at eight
  bed angles (45 deg steps) plus a four-pass single-angle control. All ticks
  coincident = the registered centre is on the physical axis; a spread ring
  measures a centre offset C directly (opposite ticks are 2|C| apart).
  Regenerate with `..\tools\make_a_center_test.py`.
- `..\samples\gcode\a-line-replay-test.gcode` - one origin line at A=0 (the
  reference, like the untouched screw in a 3D-printer bed-tilt adjustment)
  replayed at the quadrant bed angles, plus two A=0 control passes and a
  closing A=0 pass. Every replay must land on the origin: a constant parallel
  gap is that quadrant's offset, a fan opening at the ends is a rotation
  error. Lines are identified by a stepped end-length code - origin 140 mm,
  closing 128, controls 120, then 112/104/96 for 90/180/270 - and every pass
  also draws a 4 mm perpendicular tag at both ends, so it stays attributable
  even where the middles overlap (`--no-tags` draws bare lines). Draw with
  the finest pen (Micron 003) and read under a loupe or a close-up photo.
  Run after HOME + registration. Regenerate with
  `..\tools\make_a_line_replay_test.py`.
- `..\samples\gcode\rotation-center-calibration.gcode` - the calibration
  counterpart to the line replay. Run it after `G65 P113`. It uses 12 balanced
  stations: three repeats each of 0, 90, 180, and 270 degrees distributed in a
  4 x 3 lattice across 14-inch round stock. Each station has a longer A=0
  reference cross and a shorter angle replay separated by a known **20 mm
  baseline in both axes**, so wet parallel lines do not overlap. The printed
  sheet identifies every pair with an `ANGLE-REPLICATE` label such as `0-1` or
  `270-3`, marks each A=0 reference cross with a small L-shaped fiducial, and
  includes a direction key for machine +X/+Y. The furthest ink is about 154 mm
  from the registered centre. Enter the vertical-arm X gap and horizontal-arm
  Y gap for each printed station in the companion
  `..\samples\gcode\rotation-center-calibration.csv`, then run:

  ```powershell
  python ..\tools\fit_rotation_center.py --baseline-mm 20 --measurements-csv ..\samples\gcode\rotation-center-calibration.csv
  ```

  The fitter subtracts the baseline, averages the three A=0 controls, fits the
  remaining repeated angles, reports the residual centre vector `C`, the error
  left by the centre-offset model, and replacement P100
  `axis_center_correction_x/y` constants. Apply the constants in P100 rather
  than compensating again in generated G-code. Regenerate with
  `..\tools\make_rotation_center_calibration.py`. The completed first dense
  sheet and its independent repeat photo are retained as
  `..\samples\gcode\rotation-center-calibration-2026-10-23.csv` and
  `..\samples\gcode\rotation-center-calibration-2026-10-23-repeat.csv`.
- `..\samples\gcode\pen-clear-no-drag-30.gcode` - one-page T-01H diagnostic
  for intermittent pen-up drag. It draws 30 isolated witness strokes and jogs
  between them at `F300`, `F1000`, and `F3000`, using normal `M3`/`M5` plus the
  `P115` acknowledgement around every stroke. Run after `G65 P113` on ordinary
  paper at normal plotting height; one initial Cycle Start completes the test.
  Any line between witnesses is a failed pen-up clearance. Regenerate with
  `..\tools\make_pen_clear_test.py`.
- `..\samples\gcode\bed-error-map.gcode` - the full-field residual calibration
  for the position-dependent error left after registration. Run it after
  `G65 P113` with one Pigma Micron 005 (0.20 mm) for all nine passes. Its
  37 stations cover rings at 50, 95, and 150 mm on a 13-inch test field
  inside 14-inch round stock. Pass 1 is the A=0 spatial reference; passes
  2-8 replay the same fixed positions at 45/90/135/180/225/270/315 degrees;
  pass 9 is an A=0 control after the rotations. Each replay occupies a
  separate 10 mm lane, so wet lines do not overwrite the reference.
  Four large fiducials remove common photo scale/rotation/translation, and
  every station has a printed number. The program returns to A=0 and pauses
  at eight `M0`s; let the ink dry before Cycle Start. It uses no pen swap and
  does not change G54.

  A denser refinement uses the same nine-angle protocol with 91 stations at
  roughly 30 mm nearest-neighbour spacing. The current v3 layout uses 3 mm
  L arms, 6 mm lanes, 1.8 mm labels placed 14 mm inward, and four smaller outer
  fiducials. The wider lanes increase the closest edge separation within a
  station to `1.2426 mm`:

  ```powershell
  python ..\tools\make_bed_error_calibration.py --layout dense-91-v3
  ```

  That writes `bed-error-map-dense-91-v3.gcode` and its 823-row companion CSV.
  The dense layout covers radii 30/60/90/120/148.5 mm with a 13-inch planned
  extent. It remains a candidate calibration until a physical sheet is
  measured, independently compensated, and passes the same M-12 gates; it does
  not replace the current default automatically. Pass `--layout dense-91-v2`
  only when reprocessing the rejected v2 photo. Pass `--layout dense-91-v3`
  for a new physical sheet; the analyzer detects the layout from the
  measurement CSV. The original `dense-91` geometry is retained only to read
  its issued files; its 7 mm lanes cross 13 station labels. The v2 5 mm lanes
  did not cross labels but produced threshold-dependent station coordinates
  and failed every M-12 profile gate. Neither historical layout should be
  printed again.

  The manual v3 program needs one initial Cycle Start plus a resume press at
  each of its eight `M0` pauses: nine activations total. To run automatically
  with five seconds between passes, generate the separate auto variant:

  ```powershell
  python ..\tools\make_bed_error_calibration.py `
    --layout dense-91-v3 --pass-dwell-seconds 5
  ```

  That writes `bed-error-map-dense-91-v3-auto.gcode` and its matching CSV. The
  auto file replaces every `M0` with `G4 P5`, returns to A=0 with the pen raised
  between passes, and needs only the initial Cycle Start. A dwell of zero is
  accepted when truly continuous pass changes are required; the manual `M0`
  program remains the default.

  The centered v3 sheet produced profile `18bfb4ed1c33` (coverage
  `165.100 mm`, maximum correction `1.142 mm`):
  `bed-error-compensation-2026-10-29-dense-v3-centered.json`.
  A0 spatial error is `0.518 mm` RMS / `0.890 mm` maximum and
  leave-one-station-out is `0.274 / 0.760 mm` with `50.2 %` improvement. Its
  independent `bed-error-verify-dense-91-v3-centered-auto.gcode` print improved
  every angle-stage RMS and reduced aggregate RMS from `0.550` to `0.486 mm`,
  but its `1.171 mm` maximum and `11.6 %` improvement miss the gates.
  The project owner explicitly promoted `18bfb4ed1c33` anyway. The application
  now defaults to the measured 13-inch field with a 12.7 mm bed margin; this is
  an owner override, not a gate-qualified pass.

  For a v3 overhead photo, start with the dense image scale and a light blur:

  ```powershell
  python ..\tools\measure_bed_error_photo.py dense-v3.jpg `
    --layout dense-91-v3 --threshold 55 --fiducial-threshold 40 `
    --blur-radius 6 `
    --measurement-out ..\samples\gcode\bed-error-map-dense-91-v3-measured.csv `
    --diagnostic-out ..\samples\gcode\bed-error-map-dense-91-v3-photo.json `
    --overlay-out ..\samples\gcode\bed-error-map-dense-91-v3-overlay.jpg
  ```

  Review the overlay, then repeat at nearby station thresholds. Do not fit the
  sheet until the same station coordinates survive those repeats and the
  diagnostics account for all 819 expected station marks. If drag marks merge
  components, add `--seed-diagnostic` with a reviewed photo JSON from the same
  camera setup.

  Prepare and tape the sheet before `G65 P113`. Do not lift, retape, or adjust
  the sheet after the first drawing mark: that moves the calibration frame and,
  even if the fiducials remain visible, makes the result invalid. If a bubble
  forms or the sheet shifts during the run, abort and use a fresh sheet.

  Photograph the whole sheet from above. The photo tool finds the four
  fiducials, 333 station Ls, and 74 label glyphs, fits the sheet transform, and
  fills every `measured_x_mm`/`measured_y_mm` field:

  ```powershell
  python ..\tools\measure_bed_error_photo.py cal.jpg `
    --measurement-out ..\samples\gcode\bed-error-map-measured.csv
  ```

  The photo may be rotated; the tool selects the best non-mirrored fiducial
  orientation and tolerates a small number of extra ink specks. Review the
  generated overlay to confirm measured points sit on the shared L corners.
  Each fiducial is a V, so the tool selects the common arm junction rather than
  a nearby tip; a biased seed can no longer change the sheet scale by choosing
  the wrong fiducial endpoint. Compact overhead photos are accepted when a
  fiducial spans at least 32 px and has at least 80 ink pixels, but still
  require a multi-threshold overlay review because their station marks have
  fewer pixels.
  If a larger scan makes 16 px-wide station-number glyphs look like station
  marks, raise `--minimum-station-dimension` to `17`. A wider working circle or
  perspective-dependent matching distance may also be needed; review the
  overlay before accepting any changed threshold.

  The 2026-10-26 post-repair sheet required:

  ```powershell
  python ..\tools\measure_bed_error_photo.py cal.jpg `
    --measurement-out ..\samples\gcode\bed-error-map-measured.csv `
    --threshold 20 --blur-radius 18 `
    --minimum-station-dimension 17 --maximum-assignment-px 23 `
    --mask-center-fraction 0.5,0.5 --mask-radius-fraction 0.47
  ```

  If long pen-up drag marks connect separate components, add
  `--seed-diagnostic <previous-photo.json>` so the matcher uses expected local
  geometry and tolerates the extra fragments.

  Then analyse the completed sheet:

  ```powershell
  python ..\tools\analyze_bed_error_calibration.py `
    --measurements ..\samples\gcode\bed-error-map-measured.csv `
    --bed-mesh ..\samples\gcode\bed-mesh.csv
  ```

  The analyzer rejects missing rows, reports A=0 spatial error and A=0
  control repeatability separately, removes the common sheet pose, fits all
  seven intermediate-angle fields, performs leave-one-station-out validation, correlates
  the result with the optional bed mesh, and writes
  `bed-error-analysis.json`. The
  `..\samples\gcode\bed-error-compensation-2026-10-29-dense-v3-centered.json`
  profile is preselected in **Machine > Bed compensation JSON** and covers a
  measured `165.100 mm` radius (`330.200 mm` / `13.0 in` diameter). **Browse...**
  selects a replacement; **Default** restores that profile; clearing the path
  disables compensation. The profile is a machine-XY correction added after
  the existing planner chooses the bed angle and after P100 registration; it
  does not change artwork geometry or candidate selection. Its coverage is
  checked before planning, each correction is capped at 5 mm, and blanking
  the path restores byte-identical uncompensated output.

  Interactive **Preview** uses a fast nominal X/Y path while an active bed
  profile is applied to the saved G-code. Enable **Exact compensated preview
  (slow)** in the Machine group when the displayed machine coordinates must
  match the file. This matters on dense CMYK pages: the combined 2026-10-23
  preview had 8,699 contours, and exact compensation probing made its move
  construction take minutes instead of seconds. The status bar states which
  preview mode was used.

  Exact compensation first checks four points across each source segment. If
  the correction is comfortably flat for the active Tolerance, it uses one
  segment immediately; otherwise it falls back to the original 16-point
  curvature check. This preserves the existing subdivision decisions on the
  installed profile while removing most repeated local-affine evaluations.

  After fitting, generate a compensated verification sheet with:

  ```powershell
  python ..\tools\make_bed_error_calibration.py `
    --compensation ..\samples\gcode\bed-error-compensation.json
  ```

  That writes `bed-error-verify.gcode` and a matching CSV.

  To declare a larger field by extrapolating the same measured correction
  samples, add `--coverage-radius-mm 171.45` to
  `analyze_bed_error_calibration.py`. The declared radius cannot exceed the
  calibration stock radius, and extending it does not add new measurements.

  Compare a compensated verification photo with the original measurements:

  ```powershell
  python ..\tools\analyze_bed_error_calibration.py `
    --measurements ..\samples\gcode\bed-error-verify-measured.csv `
    --compare-to ..\samples\gcode\bed-error-map-measured.csv `
    --report-out ..\samples\gcode\bed-error-verify-analysis.json
  ```

  A compensated verification sheet is evidence of the residual left after the
  selected profile, not a new uncompensated calibration sheet. Do not fit it as
  a replacement profile; that would reinterpret the correction the profile was
  supposed to apply as new machine error.

  **Previous four-angle result (2026-10-23):** the original sheet resolved exactly
  4 fiducials, 185 station Ls, and 74 label glyphs. A=0 spatial error was
  `0.292 mm` RMS / `0.537 mm` maximum, the A=0 control after rotation was
  `0.176 mm` RMS / `0.369 mm` maximum, and leave-one-station-out profile
  prediction was `0.197 mm` RMS / `0.552 mm` maximum with a `66.1 %`
  improvement. The first profile (`911d2694c8c9`) failed its compensated print
  because its angle correction was not rotated from bed frame to machine
  frame. The verified core profile is
  `..\samples\gcode\bed-error-compensation-2026-10-23.json` (fingerprint
  `2cdf3731de4a`, `165.100 mm` radius). Its independent compensated
  verification reduced overall station RMS from `0.581` to `0.338 mm`,
  maximum from `1.309` to `0.752 mm`, and error by `41.9 %`; all M-12 gates
  passed. The default `13p5in-extrapolated` variant reuses those correction
  samples and extends the local-affine field to `171.450 mm`. The outer
  `6.350 mm` annulus is extrapolated, not measured; its maximum boundary
  correction is `1.054 mm`, below the 5 mm safety bound. Recalibrate after any
  bed, paper-support, toolhead, carriage, pen-clamp, or registration change.
  The first eight-angle sheet was measured on 2026-10-24. A=0 spatial error was
  `0.306 mm` RMS / `0.540 mm` maximum and leave-one-station-out prediction was
  `0.297 mm` RMS / `1.032 mm` maximum with `58.0 %` improvement. The
  `1.032 mm` maximum failed the `0.90 mm` gate, dominated by the A=90 and
  post-rotation A=0 control fields. Its independent compensated verification
  reduced overall RMS only from `0.708` to `0.639 mm` (`9.8 %`) while maximum
  rose from `1.453` to `1.574 mm`; A270 and A315 became materially worse. The
  verification therefore failed, and candidate `eda33445701f` is rejected.
  Extraction at three threshold/blur settings produced the same result.
  `bed-error-verify-2026-10-24-eight-angle.gcode`, its photo/measurement,
  overlay, and comparison report are retained as failed-test evidence. The
  post-repair full-field fit on 2026-10-26 passed at `0.324 / 0.626 mm` A0
  spatial error, `0.209 / 0.373 mm` A0 control, and `0.212 / 0.503 mm`
  leave-one-station-out error. Its independent compensated sheet then reduced
  overall RMS from `1.744` to `0.218 mm`, maximum from `2.965` to `0.591 mm`,
  and improved every angle stage; all M-12 verification gates passed. The
  prior default was profile `4bad792e35ad`; its measured inner field was
  independently verified, while its outer `6.350 mm` annulus was extrapolated.
  The current owner-selected default is centered dense-v3 profile
  `18bfb4ed1c33`, which covers only the measured 13-inch field and does not
  include that outer annulus.
- `..\samples\gcode\a-tilt-pairs-test.gcode` - four separated line pairs for
  a caliper-read bed-tilt check: each pair is the same paper segment drawn
  twice, once at A=0 (the longer 80 mm constant line) and once at that
  pair's angle (the shorter 66 mm test line); the two should land on top of
  each other. A zigzag label above each pair counts the angle - 1 tooth =
  control, 2 = 90 deg, 3 = 180, 4 = 270 - and the control pair is the
  constant quadrant the others are read against. Measure the middle gap and
  both end overhangs with calipers; adjust the rail ends until the pairs
  collapse onto the control. Fits the sheet already on the bed and clears
  the earlier test's ink. Regenerate with
  `..\tools\make_a_tilt_pairs_test.py`.
- `..\samples\gcode\xy-scale-check.gcode` - measures the X/Y axis scale
  directly with the bed parked (the program contains no A words): a 200 mm
  ruler along each machine axis with marks every 50 mm, plus a 120 mm square
  in the +X/+Y quadrant. Drag a steel rule over the rulers - an interval
  that is long or short by the same fraction everywhere means `$100` (X) or
  `$101` (Y) steps-per-mm is off by that fraction (new steps/mm = old x
  drawn / commanded); unequal square diagonals mean X/Y skew. Needs a
  >= 205 x 205 mm sheet (8.5x11 in portrait fits, centred). Regenerate with
  `..\tools\make_xy_scale_check.py`.
- `..\samples\gcode\wave-rotation-isolation-base.gcode` and
  `wave-rotation-isolation-low-a-accel.gcode` - one-sheet CMYK wave diagnostic.
  The first file prints parked A0 plus `+5`, `+10`, `+14.5` baseline,
  reduced-feed `+14.5`, and `-14.5` degree cases. Keep the sheet mounted, set
  `$123=600`, and run the second file for its own parked control and
  reduced-acceleration `+14.5` degree case. Regenerate both with
  `..\tools\make_wave_rotation_isolation_test.py`.
- `..\samples\gcode\cmyk-pen-alignment.gcode` - five crosses (centre and
  four corners at +-75 mm) with the bed parked, for comparing the four CMYK
  pens. Register once, then run this **same file unchanged** once per pen on
  one sheet without re-registering; the crosses must land on one another.
  Any per-pen gap is that pen's XY tip offset relative to the first pen,
  which the single stored P100 pen offset cannot correct. Regenerate with
  `..\tools\make_cmyk_pen_alignment.py`.
- `..\samples\gcode\cmyk-wave-coupon.gcode` - single-run black-pen diagnostic
  for an already-mounted 14-inch sheet. It prints sixteen `54 x 28 mm` patches
  covering C15, M75, Y0 and K45 from left to right. The upper eight patches
  test Wave screen - phase-locked depth above equidistant rows with A parked;
  the lower eight repeat the comparison with production Xtheta/Ytheta planning.
  One Cycle Start completes the file. It uses the production `3.36 mm`
  on-paper pitch, `0.8 mm` pen, `F700`, bed compensation, and `0.05 mm` Path
  tolerance. Regenerate with `..\tools\make_cmyk_wave_coupon.py`.
- `..\samples\gcode\cmyk-wave-pitch-coupon.gcode` - single-run `195 x 144 mm`
  black-pen pitch matrix for ordinary paper. It tests `2.80`, `3.36`, and
  `4.20 mm` pitch at C15/M75/Y0/K45 with production rotating-bed planning,
  compensation, `F700`, and a `0.8 mm` pen. One Cycle Start completes all
  twelve patches. Regenerate with
  `python tools\make_cmyk_wave_coupon.py --multi-pitch`.
- `..\samples\gcode\cmyk-wave-letter-test.gcode` - one-run black-pen
  implementation check for portrait 8.5 x 11 paper with A parked. Four columns
  cover C15/M75/Y0/K45. Three rows test phase-locked depth at `2.80`, `3.36`,
  and `4.20 mm`; the fourth row is an equidistant `3.36 mm` control. The field
  is `200 x 200 mm`, and one Cycle Start completes all sixteen patches.
  Regenerate with `python tools\make_cmyk_wave_coupon.py --letter`.
- `..\samples\gcode\bed-compensation-motion-test.gcode` - one-run
  compensated-versus-uncompensated XY/A tracking test for ordinary paper and a
  black `0.8 mm` Pigma Micron. Eleven cases compare parked-A horizontal and
  vertical controls, compensated/uncompensated normal and reverse A sweeps,
  Y-dominant motion, inner-radius motion, and a repeat of the highest-risk
  compensated case. Every case redraws the same path at requested
  `F350`, `F700`, and `F1200`, with forward/reverse traces, rotating pen-up
  round trips, A0 witness crosses, and a global frame recheck that should all
  overlay. Regenerate with
  `python tools\make_bed_compensation_motion_test.py`.

## Generator tabs

The window has the standard **File / Tools / View / Help** menu bar. **File**
opens the artwork (Ctrl+O), sets the G-code destination (Ctrl+Shift+S), saves
G-code (Ctrl+S), and exits. **Tools** is the tool selector: **All Tools**
(Ctrl+T) opens the card dashboard (Core, Line art, 3D, Patterns, Text &
layout), **Convert** is Ctrl+1, and the other tools follow in menu order with
Ctrl+2...Ctrl+0. **View** toggles the machine reach guide, pen-down path, and
log, and controls preview zoom. The preview panel also has a **Red motion
lines** checkbox next to Fill bed / Fit inside that toggles the same pen-down
overlay without leaving the preview (it stays in sync with the sidebar
checkbox and the View menu), plus an **Ink simulation (multiply)** checkbox
for CMYK previews: the ink layers multiply over the paper white in plot
order, like translucent pens, so the preview shows the finished overprint
instead of painting each layer opaquely. Simulation strokes draw at the real
pen width, and a stroke thinner than a screen pixel fades toward white by the
fraction of a pixel it covers, so the fit-to-window view keeps the density
the paper will get (zoom in for full-strength strokes). Mixing only happens
where strokes overlap: keep the effective pitch (Dot pitch x Artwork scale,
then the tone-adaptive factor of 1-3x) at or below the pen width for full
coverage. An **Ink profile...** button loads
the `*-profile.json` written by `tools\cmyk_calibrate.py`, so the simulation
multiplies your pens' measured transmittances instead of the display ink
colours. **Help** has the shortcut list
(F1) and About.
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
tab until Preview is pressed again. Multi-layer tools (CMYK) keep that static
Preview for the overlaid view; exact per-ink programs are planned when
**Save 4 G-code files** is pressed and are written through one save dialog
owned by the window.

Tool authors: the contract and the host entry points are documented in
[`generator_tabs/README.md`](generator_tabs/README.md). Ported or vendored
third-party code keeps its license and attribution in a sibling
`<name>_NOTICE.md`.

Current tools:

**Photo-based** (need an image from File > Open Artwork):

- **Line Draw** - raster image to edge-traced contours plus luminance hatch.
  Controls: artwork (from the static Artwork row), invert, mode
  (contours / hatch / both), edge
  threshold, hatch spacing, hatch light/mid/dark thresholds (upstream
  linedraw levels 144/64/16), sketch jitter, minimum length, simplify,
  resolution, line width, seed, page size, margin, artwork scale.
- **CMYK** - RGB to CMYK separation with gray-component replacement, screened
  as one layer per ink pen. Controls: artwork (from the static Artwork row),
  an **Auto (photo)** button that analyzes the image and sets auto levels,
  brightness, contrast, saturation, GCR, a starting gamma, and a modest
  luminance-sharpening preset.
  - For Wave screen, Auto uses an exposure-preserving color path. It reads the
    source's midtone, tonal span, and high-chroma percentile, then keeps normal
    photos near neutral saturation/contrast instead of pushing them to the
    darkest edge of the generic screen model. This preserves the sky,
    highlights, and colour separation in the preview. If the current pitch
    would make each solid row cover too much of the page, Auto opens it to at
    least `3.4` pen widths; every resulting row remains exactly equidistant.
  - For other screen styles, tone controls come from a detail search over the
    real curve chain: maximum mid tone-weighted gradient with a clipping
    penalty, plus a target print mean clamped to the printable `0.30-0.75`
    window. That search also models the rectilinear row coverage.
  - Auto only changes Dot pitch for Wave screen and never sets rows closer than
    the operator's current choice. **Match pen** remains the explicit action
    for setting one pen width at the current artwork scale.
  auto levels (default on: stretch the image's 1st-99th luminance percentiles
  so low-key photos use the full tonal range), saturation, contrast,
  brightness, luminance sharpening (default on: unsharp-mask amount and
  on-paper radius), ink gamma, black (GCR), resolution, per-ink weights, screen style
  (halftone dots / stipple dots / line screen / crosshatch levels / wave screen
  with equidistant rows / interference (gyroid) / single line (TSP) /
  topographic contours / rectilinear fill),
  dot pitch (with a **Match pen** button that sets it to one pen width at
  the current artwork scale), dot size, solid dots (spiral-filled so each
  mark reads as a dot, not a ring), hatch levels, overdraw, pen width, max
  marks per ink, seed, preview and write checkboxes per layer, page size,
  margin, artwork scale, and registration corner crosses (all four inks
  draw the same four margin crosses so pass alignment can be checked).
  Resolution keeps the source image's longest side up to that many pixels
  and never upsamples, so it accepts high-resolution sources (the control is
  effectively uncapped; memory grows with the source size you keep).
  Shipped defaults are the owner's tuned rectilinear set: auto levels on,
  rectilinear fill at 0.10 mm pitch (its light-tone stretch opens the pitch
  up to 7x, so highlights and mid tones keep paper while dark tones fuse
  solid, and the pitch follows the tone the row actually inks and eases
  between rows so it does not step where the subject meets the background),
  saturation 115 %, contrast 285 % (the soft S-curve keeps
  steepening up to 300 % instead of clipping), brightness 170 %
  (shadow-weighted lift), ink gamma 1.40 (about a third less ink in the mid
  tones), unsharp mask on at 70 % with a 1.5 mm radius, black (GCR)
  95 %, hatch levels 8, artwork scale 280 %, dot size 100 % with solid dots
  off (both only affect the dot screens), 40000 marks per ink, 10000 px
  resolution, C/M/Y/K weights 100/100/100/100 %.
  **Sharpen** applies its unsharp mask after auto levels and before the
  saturation, contrast, brightness, and separation curves. The mask derives
  detail from luminance and applies that same detail to all three RGB
  channels, preserving the source ink balance. Its radius is in final
  on-paper millimetres, so changing Resolution does not change the physical
  feature scale being emphasized. Lower the amount if edges ring; the
  calibration sheet does not use image processing. The preview checkboxes decide which inks the shared OpenGL preview
  draws, and they apply instantly: every layer stays loaded, so toggling a
  checkbox never re-screens or re-plans. For CMYK previews the preview data
  area also reports the per-ink M3 (pen-down) counts as
  `C: n M: n Y: n K: n`, counted from the planned program.
  Preview deliberately defers exact per-ink G-code generation until save so a
  completed preview does not sit behind four large planners. Pressing **Save
  4 G-code files** starts each checked ink's exact program through the same
  pipeline as Convert - including the r-theta solver, the tab's **Kinematics**
  choice, and bed compensation - then reports each file's split (or
  `XY only`) and calibrated time. While save-time planning runs, the shared
  preview **Cancel** button changes to **Cancel planning** and cancels the
  active CMYK worker.
  **Save 4 G-code files** writes
  `<name>-cyan.gcode`, `-magenta`, `-yellow` and `-black` from one base name.
  The r-theta axis-cost solver and the M3/M5 pen contract are inherited
  unchanged, so each ink is as cost-efficient as a normal Convert program;
  the tab's **Bed motion** bullets (Xθ/Yθ or XY only) apply to all four ink
  programs and to the calibration sheet.
  The Kinematics group's **Center hold** (default 60 mm diameter, i.e. a
  30 mm radius) parks the bed for drawing inside that circle, where A-axis
  rate limiting and scrub otherwise make fine rows wobble; set `0` to let
  the bed rotate everywhere.
  The four programs share one **page frame**: they are planned around the
  page centre rather than each ink's own bounding box, so **Artwork scale**
  changes the printed size while leaving the four passes co-registered
  (2026-10-20 fix, `WSW-20261020-001`). The optional corner crosses are now
  only a machine-alignment check - tick them to see the four passes overlap
  on paper, not to make the programs align.
  **Running the four passes:** call `G65 P113` once before the set (HOME +
  REGISTER), then run the files back to back. Each file begins with `G54`
  and its own first fed travel to its start point, and ends with a full pen
  retract and the `G53 ... (park home)` move, so no manual "start point"
  jog is needed. Do **not** re-home, re-register, or change work offsets
  (`G10`/`G92`) between passes - that starts a new frame and shifts the
  remaining colors. `?` and `$G` are the non-motion checks: expect `Idle`
  and the same G54 work offset before each pass. If a reset or re-home
  happens mid-set, re-register and restart the set.
  **Pen alignment and offsets:** **Pen alignment** holds a measured X/Y
  correction for each ink. The values are paper-space corrections, applied
  after Artwork scale and to that ink's registration crosses as well, so a
  corrected pen brings its crosses onto the reference. They apply to the
  artwork programs and the preview; the calibration sheet keeps its
  geometric layout so its scan manifest stays valid. Use
  `samples/gcode/cmyk-pen-alignment.gcode` once per pen (one registration,
  no re-registration between pens), enter each pen's measured displacement
  relative to cyan, and press **Use measured offsets**; the tab applies the
  opposite sign automatically. A single X/Y offset corrects translation
  only - a rotation or a fan in the measured crosses is a frame/A/bed
  problem, not a pen offset.
  **Pass summary and preflight:** before saving, the tab shows the page,
  shared frame, Bed motion, centre hold, row-spacing guard, crosses and pen
  offsets, then runs the motion preflight on each ink. It checks the bed-step
  cap, the A-rate limit, bare `G0` rotations and moves that exceed the Path
  tolerance;
  hard violations block Save and warnings go to the log. A successful
  artwork save also writes a version-3 `<name>-set.json` beside the four files
  with the source hash, page and motion mode, bed-compensation profile,
  complete image/screen recipe, sharpening amount and radius, effective pitch,
  pen offsets, per-ink
  preflight results, and SHA-256 hashes for all four G-code files.
  Line, wave, gyroid, TSP and contour styles are the fast continuous-mark
  alternatives to dot styles: they draw far fewer pen-lift cycles, while the
  overdraw control darkens any style by redrawing each mark up to three times
  with a sub-pen offset. **Wave screen - equidistant rows** is the only Wave
  screen exposed by the CMYK selector. It translates one common
  luminance-shaped waveform to every row with no row-specific vertical
  movement, so adjacent centre spacing remains exactly the configured pitch.
  **Preserve exact row pitch (skip bed compensation)** is enabled by default
  for this style. It clears the Machine-tab displacement profile from the
  effective Wave job because an arbitrary correction field changes otherwise
  uniform row spacing in final machine X/Y. Other screen styles still inherit
  the selected profile. Unchecking the guard explicitly opts into retaining
  bed-position correction at the cost of potentially non-uniform rows. The
  saved set manifest records both the effective empty compensation path and
  `preserve_exact_row_pitch: true`.
  Verify a saved set with
  `python ..\tools\check_cmyk_wave_spacing.py <name>-set.json`; it checks all
  four manifest hashes and their final-machine adjacent-row spread.
  The emitted finite segments preserve the `0.8 mm` pen plus `0.25 mm` paper
  gap at their actual shortest distance; there is no additional fixed fraction
  of the pitch reserved between rows. Changing Dot pitch or Artwork scale
  changes the geometry rather than selecting a coupon-specific behavior. A
  pitch smaller than the pen envelope is rejected with a planning error because
  no legal row spacing exists at that scale.
  Regression coverage spans `2.80`, `3.36`, and `4.20 mm` at all four CMYK
  screen angles. With the spacing guard active, the normal artwork path uses
  exact row pitch. Legacy stored values `waves` and `waves_zero` are promoted
  to the equidistant geometry unless a diagnostic tool explicitly requests
  `allow_variable_wave_spacing=True`; that opt-in exists only to generate
  comparison coupons. **Path tolerance** controls how densely each sine is
  sampled in paper space, so emitted chords follow the shape instead of
  appearing as visible facets.
  While the CMYK page is active the shared OpenGL preview draws each visible
  ink in its own colour - not yet drawn marks in a pale tint, the drawn path in
  full ink - so the four layers can be judged overlaid the way they will mesh
  on paper. The red machine-motion overlay and every other tool keep their
  existing single-colour preview.
  **Test sheet** (Calibration group) replaces Preview and Save with a
  calibration page instead of the artwork: per-ink coverage and overdraw
  ladders, a dot-size, line-pitch, or hatch-level ladder, a GCR ramp,
  dense full-tone mixes (pairs, triple, and the C+M+Y+K quad) and single-ink
  spots at the same tight spacing, blank paper, and four corner fiducials;
  the only printed text is a two-line identification header
  (page, margin, screen), because the cell values live in the manifest. The
  **Sheet screen** box defaults to matching your Screen style (line screen
  and crosshatch included), so the ladders calibrate the marks you actually
  print; line sheets draw continuous strokes and need far fewer pen cycles
  than dot screens. Save writes `<name>-calibration-*.gcode` plus
  `<name>-calibration.json`; plot the four files in C, M, Y, K order, scan
  the sheet flat, and run
  `python tools\cmyk_calibrate.py scan.png --manifest <name>-calibration.json`
  to report paper-relative ink transmittances and a multiply-model check for a
  print-matching preview. Ladder cells print raw tone; raise the pitch for a
  faster calibration plot. The full print-scan-analyze handoff (including
  analyzing a scan with no manifest) is
  [`../docs/testing/CMYK_CALIBRATION.md`](../docs/testing/CMYK_CALIBRATION.md).
- **SquiggleCam** - one continuous squiggle per row from image tone (full
  upstream setting set): line count, frequency, amplitude, brightness,
  contrast, min/max brightness, pixel spacing, resolution, black-background
  inversion, page, line width, artwork scale.
- **Pixel Art** - pixel-art paths in `big` (5x5 spiral), `line` (runs), or
  `snake` (connected) mode, from vpype-pixelart: pixel pitch, overdraw, max
  grid, alpha threshold, ignore-white, page, line width, artwork scale.
- **Plotterfun** - the complete upstream `mitxela/plotterfun` web app (22
  algorithms) vendored under `software/plotterfun_vendor/` and embedded with
  QtWebEngine. Load the image and choose the algorithm inside the page, then
  press **Export SVG to plot**; requires PySide6-Addons.
- **Layers** - splits the imported SVG by stroke/fill colour into per-layer
  SVGs; pick a layer to preview and plot one pen at a time. The source SVG's
  own dimensions are preserved.
- **Stipple / TSP** - density stippling with weighted Lloyd relaxation and
  route-optimized TSP art. Controls: invert, density gamma, points, Lloyd
  passes, seed, style (dots / TSP line / both), dot size, 2-opt passes, page
  size, margin, line width, artwork scale.
- **Vector Trace** - clean outline tracing for logos and silhouettes.
  Controls: Otsu/manual threshold, trace-light-regions, simplify, smoothing,
  minimum area, fill (outlines / hatch / both), hatch spacing and angle, page
  size, margin, line width, artwork scale.

**Algorithm only** (generate from parameters; optional files noted):

- **Flow Field** - evenly spaced streamlines from a procedural noise field, an
  image's luminance gradient, or a user formula (angle f(x,y) or vector dx/dy,
  with presets). Controls: source, preset, formula mode, formulas, artwork
  (from File > Open Artwork), invert, image cutoff, seed, noise scale,
  octaves, spacing, step, max steps, line width, page size, margin, artwork
  scale. Optional image-edge source; works standalone on noise or formulas.
- **3D Wireframe** - OBJ or STL mesh to orthographic hidden-line vector art.
  Built-in primitives (cube, sphere, cylinder, cone, terrain plane) and a
  perspective camera. Controls: source, file/primitive, style
  (hidden-line wireframe / silhouette / all edges), yaw, pitch, roll,
  projection, camera distance, target width, sample step, page size, margin,
  line width, artwork scale. Works from the built-in primitives; a mesh file
  is optional.
- **Harmonograph** - damped Lissajous figures from two decaying oscillations,
  or the upstream physical two-pendulum + rotating-disk model. Controls:
  model, pivot/arm geometry, rotating-disk frequency, amplitudes, phases,
  per-axis damping, frequencies, duration, samples, smoothing, page size,
  margin, line width, artwork scale; the simple model keeps seed, frequency
  X/Y, phase, damping, turns, samples, and curve count.
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
  address guide lines, and optional caption/message/address text. Controls:
  page preset (default upstream 7x5 in landscape), divider, address lines,
  line spacing, stamp size, caption, message, address, text size, tracking,
  page size, margin, line width, artwork scale.
- **Wobble** - hand-drawn wobble applied to the current preview contours
  (line-wobbler): frequency, amplitude, frequency jitter, seed, endpoint
  wobble toggles, margin, line width, artwork scale. Runs on the current
  preview contours, so preview another tool first.
- **Voronoi** - bounded Voronoi cells with optional Lloyd relaxation.
  Controls: points, seed, relaxation, style (cell boundaries / site dots /
  both), dot size, page size, margin, line width, artwork scale.
- **Path Prep** - vpype-style cleanup of the current preview contours:
  linemerge, deduplicate, reloop, and linesort. Controls: merge angle and
  tolerance, duplicate tolerance, gap closing, sort/reverse, 2-opt passes,
  margin, line width, artwork scale. Preview another tool first.
- **Reaction-Diffusion** - Gray-Scott patterns extracted as contour lines.
  Controls: grid, steps, feed/kill, diffusion A/B, seeds and seed size, seed,
  contour level and level count, page size, margin, line width, artwork
  scale.

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

The menu bar, status bar, **Preview** and **Cancel** buttons in the preview
panel, and the OpenGL preview itself (status, estimate, progress, fit/clip
controls) are window furniture outside the tool pages, so they stay visible
whichever tool is active. The preview fills the whole area to the right of the
feature settings pane; only the settings sidebar belongs to the Convert page.

### Recommended starting settings

These defaults are tuned for a 200 x 200 mm page, a 0.3 mm pen, and the 1:1
preview. They also appear in the app under **Help > Recommended Settings**.
Photo-based tools need an image via File > Open Artwork; algorithm-only tools
work with no input (optional mesh/image sources are noted below).

| Tool | Start from | Notes |
|---|---|---|
| Convert | Fit bed (auto), Fill spacing 3 mm, linear or crosshatch, feed 700 / travel 3000 mm/min | Imported artwork; Save G-code once the preview looks right. |
| Flow Field | Noise source, scale 60 mm, octaves 3, spacing 3 mm, step 1 mm, 400 steps | Spacing 3 mm is dense; use 4 mm for a first plot. |
| Line Draw | Both modes, edge 35 %, hatch 2 mm, levels 144/64/16, jitter 0.25 mm, simplify 0.75 px, resolution 900 px | Needs an image in the Artwork row. |
| CMYK | Auto levels on, rectilinear fill at 0.10 mm pitch, saturation 115 %, contrast 285 %, brightness 170 %, ink gamma 1.40, black (GCR) 95 %, 40000 marks/ink, resolution 10000 px, weights 100/100/100/100 %, artwork scale 280 % | Needs an image; Preview plans each ink in the background and Save writes four files. Dense photo screens take hours to plot; raise pitch or lower Max marks/ink for a faster pass. |
| 3D Wireframe | Cube, size 2, detail 24, hidden-line wireframe, yaw 35 / pitch -25, perspective 4x radius, target width 140 mm, sample 0.7 mm | Works with no file; switch Source to File for OBJ/STL. |
| Harmonograph | Physical model: d 900 / c 800 / p 900 / q 700 mm, A 10 / B 10 deg, R 0.001 / S 0.001, f 0.300 / g 0.302 Hz, disk 0.0008 Hz, 300 s, 12k samples | Upstream defaults; the simple model is a lighter alternative. |
| Snowflake | 6 arms, depth 3, length 45 %, branch angle 35 deg, branch scale 55 %, jitter 8 deg / 15 % | Raise depth for finer detail; cap is 5. |
| Truchet | Quarter arcs, tile 12 mm, 10 arc segments, margin 6 mm | Diagonal and mixed styles use the same grid. |
| Text | Size 12 mm, tracking 0.4 mm, line spacing 140 %, alignment left | Uses the bundled Hershey simplex font. |
| Substitution | 3 colours, 4 iterations (32 x 32), colour boundaries, margin 6 mm | Each extra iteration quadruples the path count. |
| Postcard | 7x5 in landscape, margin 8 mm, line spacing 9 mm, stamp 25 x 30 mm, text 6 mm, tracking 0.2 mm | Matches the upstream default page. |
| SquiggleCam | 50 rows, frequency 150, amplitude 1.0, spacing 4 px, resolution 700 px, brightness 0, contrast 0, min 0 / max 255 | Needs an image; lower frequency raises the wiggle. |
| Pixel Art | Mode big, pitch 0.6 mm, max grid 96, alpha 128, ignore white | Paths auto-fit the page; big mode needs 5x the pitch per pixel, line mode is denser. |
| Wobble | Frequency 3 mm, amplitude 0.5 mm, jitter 20 %, seed 7, endpoint wobble on | Preview a tool first; Wobble processes those contours. |
| Plotterfun | Load an image inside the page, pick an algorithm, keep its defaults, then Export SVG to plot | Requires QtWebEngine (PySide6-Addons). |
| Voronoi | 120 points, seed 7, relax 1, cell boundaries, margin 6 mm | Raise relax for even cells; site dots show the seeds. |
| Path Prep | Merge 5 deg / 0.05 mm, duplicate 0.05 mm, close gaps 0.2 mm, sort on | Preview a tool first; cleans those contours. |
| Layers | Pick a colour layer (or All colours) from an imported SVG | One layer per pen; the source dimensions are kept. |
| Stipple / TSP | 600 points, 3 Lloyd passes, gamma 1.0, dots + TSP, dot 0.6 mm, 5 2-opt passes | TSP mode gives one continuous line; raise 2-opt passes for shorter travel. |
| Reaction-Diffusion | Grid 128, 4000 steps, f 0.037, k 0.060, Da 0.16, Db 0.08, one seed of 8, level 0.20 | Raise steps for finer detail; grid 128 keeps the build quick. |
| Vector Trace | Otsu, simplify 1 px, smoothing 1, min area 6 px2, outlines | Add hatch at 1.5 mm / 45 deg for filled shapes. |

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
  SVG Bézier curves now flatten adaptively: the converter recursively
  subdivides a curve only until its control hull is within `Tolerance`, instead
  of giving every cubic a fixed eight-step minimum. On the dense 7,298-path
  mandala, the same `0.25 mm` accuracy reduced planned drawing points from
  `560,957` to `60,762` and the saved file from `605,725` to `105,604` lines.
  Geometry version: `2.7-adaptive-curves`.
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
  against: `Bed dia mm`, `Bed margin mm`, `Gantry reach radius mm`,
  `Bed compensation JSON` (the verified profile by default), and the
  end-of-program `Park X/Y machine mm` in G53 machine coordinates, plus
  **Exact compensated preview (slow)**. The profile contains measured residual
  `correction(theta, bed_xy)` machine-XY vectors. It is applied to saved G-code
  after the planner selects theta and after P100's registration; interactive
  preview uses nominal X/Y unless exact preview is enabled. P100 is not
  rewritten. Artwork points outside the profile's stated measured coverage are
  rejected before preview or save. Between measured bed angles, the converter
  rotates both neighboring corrections back into the bed frame, interpolates
  there, and rotates the result into machine XY. New compensated G-code carries
  an `angular interpolation bed-frame` header marker.
- **Theta kinematics** — theta axis/ratio/resolver/cost settings (`Theta ratio`
  defaults to 12.03324, the measured effective ratio of the 60T→720T pulley
  pair).
  - **Bed motion** is the kinematic either/or, as two bullets:
    **Xθ/Yθ (rotating bed, fast)** runs the per-segment solver (the
    production default), and **XY only (bed parked, precise)** holds one bed
    angle so the gantry draws the whole artwork in X and Y. XY only removes
    every bed-angle error (tilt, runout, reversal drag) from the print at the
    cost of gantry travel; the bed parks at `Theta offset` degrees (0 keeps
    the artwork axes on the machine axes). **Theta resolver** stays a combo
    of the implemented solver strategies for Xθ/Yθ, so an unsupported value
    cannot be entered.
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
  - **Bed reversal park mm** (default `2.5`) parks the bed across stretches
    where its own planned direction would reverse within that distance of pen
    travel. Smooth curves never reverse and keep the bed turning; the rule
    targets scalloped and zigzag edges, where reversing the 12:1 bed every
    couple of millimetres smears the outline. The two-pen A/B overlay measured
    a ~0.5 deg net angular error plus ~0.5 mm local distortion on the
    back-of-head scallop when it turned, and a perfect match when parked. On
    the heraldic sample with this rule it parks 420 mm of the 4298 mm pen path
    (9.8%), all in the zigzag patches; `0` disables it.
  - **Center hold diameter mm** (default `60`, a 30 mm radius) parks the bed
    for drawing points inside that circle. Near the bed centre a straight
    paper move needs a huge bed rotation - at r = 10 mm and 700 mm/min the A
    axis would need about 48,000 motor deg/min against a 30,000 limit - so
    the A axis is saturated, reverses often, and scrubs the pen. The gantry
    draws the held moves exactly; the bed is brought back toward the planned
    angle under the same Max bed step gate after leaving the region. `0`
    restores the old behavior and lets the bed rotate everywhere.
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
    ~2.28 mm `M5` clearance and finishes in 2-3 s.
  - **Pen up ms** (`pen_up_ms`, default 1000) is the dwell after every
    `M5`/`M3` lift. The toolhead clears in about 0.46 s measured; the extra
    margin covers the release and the settle before the next travel. With the
    GP27 handshake on, the same value is the `A` fallback dwell the `P115`
    recovery path uses when a handshake times out.
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
  reach circle. Placement is saved beside the artwork as
  `<artwork-file>.theta-layout.json` and restored when that same file is
  imported again; editing the fields, dragging, or closing the app updates it.
  A Fit still deliberately resets the placement to zero. While dragging, the
  displayed part is the existing plan
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
- The **Bed motion** bullets select the kinematics for every generated
  program: **Xθ/Yθ** rotates the bed per segment (fast), **XY only** parks
  the bed so the gantry draws the artwork unchanged (precise; the bed cannot
  add tilt, runout, or reversal error). XY-only programs still carry their
  A words - at one constant value - so ioSender and the controller see the
  same program shape either way. The CMYK tab carries its own copy of the
  two bullets for its four ink programs and its calibration sheet.
- The converter does not apply a pen/TMAG XY tool offset. Generated XY positions
  remain in the machine work-coordinate frame; the controller's commissioning
  macro `P100` owns magnetic center registration, the measured `pen - TMAG`
  offset, and `G54 X0 Y0` so work zero means pen tip at bed center.
- P100 also remains the owner of the physical registration centre and A index.
  The bed-compensation profile is a separate residual map and the converter
  loads the owner-promoted 13-inch centered dense-v3 profile by default; clear the path to
  disable it or use **Browse...** to select a replacement. Wave-screen jobs
  with the default spacing guard bypass this profile because the correction
  field is not row-pitch preserving; uncheck the guard only when positional
  correction is more important than equidistant rows. Its fiducial fit
  removes common translation, rotation, and scale before fitting. Do not place
  the same residual offset in both P100 and the profile. A saved compensated
  program records the profile fingerprint and correction bound in its header.
  Fast preview intentionally displays nominal machine points; enable **Exact
  compensated preview (slow)** when preview/saved-coordinate parity is needed.
- SVG document coordinates are not machine coordinates. The converter centers
  the clipped artwork at G54 zero; a document centered at `(100,100)`, for
  example, emits drawing coordinates around `(0,0)`, not `(100,100)`.
- `Bed dia mm` defaults to `355.6 mm` (14-inch round stock). With the default
  `Bed margin mm` of `12.7 mm` (0.5"), the effective `330.2 mm` (13-inch)
  diameter matches the measured compensation coverage.
- `Gantry reach radius mm` (default 180.0) caps the drawable circle at the
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
