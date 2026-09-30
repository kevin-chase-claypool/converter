---
id: WSW-20260930-004
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - raster
  - tracing
  - application
  - design
related:
  - WSW-20260930-003
  - software/README.md
---

# Add the Kaleidoscope Converter app

## Summary

A second host app, `software/qt_kaleidoscope.pyw`, launched by
`kaleidoscope.bat`, imports an SVG, PNG or JPG, mirrors it into N kaleidoscope
divisions, and saves the same G-code contract as the main converter. The whole
motion pipeline is reused: only source handling, the mirror construction and a
flat preview are new.

## Reason

The operator wanted to invent designs rather than only convert finished
artwork: import a picture, choose a division count, and plot the result. The
existing app's OpenGL preview and single-source pipeline were the wrong shape
for that, but its planner, polar kinematics, fill and emitter are exactly right,
so the new app is a thin design layer over `converter_core/`.

## Implementation

- `converter_core/kaleidoscope.py` (new, no Qt):
  - `trace_raster` turns a PNG/JPG into closed contours by marching squares over
    the thresholded pixels, visiting only boundary cells, then simplifies with
    an iterative Douglas-Peucker pass.
  - `clip_to_wedge` clips contours to the half-wedge `0..180/divisions` degrees
    with half-plane bisection.
  - `kaleidoscope` places the wedge `2 * divisions` times around the circle,
    reflecting alternate copies, so the sectors tile 360 degrees exactly;
    `mirror=False` repeats without reflection for a pinwheel.
  - `normalize_source` centres the source on the apex (bounding-box centre or an
    explicit offset) and scales its longer side to a target size in millimetres.
- `qt_kaleidoscope.pyw` (new, PySide6): source picker, divisions, mirror,
  rotation, apex offset, threshold/invert/trace detail, source size,
  fit-to-reach, tolerance, fill spacing, feed rate and theta tangential speed; a
  flat bed-frame preview with the bed circle, reach circle and sampled wedge;
  and Save G-code through `plan_program` + `contours_to_gcode`.
- SVG sources keep the main app's two-pass behaviour: a fill-free probe sizes the
  artwork, then the geometry is parsed again at the final scale so the fill is
  generated at the on-paper spacing.
- `software/converter_core/__init__.py` exports the new module, and
  `software/README.md` and `docs/README.md` document the app.

## Verification

- New `software/tests/test_kaleidoscope.py`: raster tracing (one rectangle ->
  one closed contour whose spans match the rectangle, blank image -> nothing,
  inverted trace), wedge clipping (all clipped points stay inside 0..45 degrees,
  the outside corner is cut), mirror symmetry about the wedge axis, and clean
  G-code (one `M3` per contour, no keep-down bridges, end park present).
- All nine test modules pass.
- Headless Qt run (`QT_QPA_PLATFORM=offscreen`): the window constructs with
  12 divisions and mirror on; a traced circle at 12 divisions gives 24 contours
  and 227 G-code lines with 16 pen cycles at 8 divisions and no bridges; the
  spirit-logo SVG gives 400 contours and 33,675 lines with no bridges.

## Struggles and rejected approaches

- Reusing the main app's OpenGL polar preview was rejected: it is built around
  the simulated machine motion, and a kaleidoscope needs a flat design view.
- Hatching the raster (the main app's image-tone path) was rejected for v1
  because that renderer lives in the main window rather than the core; tracing
  into closed contours instead means the normal fill can still shade a shape,
  and true photo-tone shading is recorded as follow-up.
- The first `clip_to_wedge` draft read `points.index(point)` to find the previous
  point; it now tracks the previous point explicitly.

## Risks and follow-up

- Raster tracing is a threshold outline, not a tone renderer: a photo becomes
  blobs unless the threshold and fill are tuned. Tone shading through the Qt
  renderer is the recorded next step.
- The apex is typed, not dragged, and the preview has no playback.
- The wedge samples one slice of the source; content outside the wedge is
  discarded by design, so `Rotate source` and `Apex offset X/Y` are the tools for
  choosing what is sampled.

## Files

- `software/converter_core/kaleidoscope.py`: tracing, wedge clipping, mirror
  repeats, normalisation.
- `software/converter_core/__init__.py`: export the module.
- `software/qt_kaleidoscope.pyw`: the app.
- `kaleidoscope.bat`: launcher.
- `software/tests/test_kaleidoscope.py`: unit tests.
- `software/README.md`, `docs/README.md`: documentation map and current state.
- `docs/project/ENGINEERING_LOG.md`, `docs/project/ROADMAP.md`: record and
  follow-ups.
