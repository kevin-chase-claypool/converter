---
id: WSW-20260927-004
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - preview
  - gantry-reach
  - scaling
  - soft-limit
  - g54
related:
  - WSW-20260926-002
---

# Draw the gantry reach in the preview and report the artwork radius

## Summary

The preview now draws the gantry's reachable radius as a green boundary around
the bed center, toggled by **Show machine reach guide** in Preview settings, and
the preview-ready message reports the artwork radius against that reach. Both
are measured before clipping, so artwork the reach cap trims is visible rather
than silently disappearing.

## Reason

Two problems prompted this.

Choosing a scale for a drawing required guessing whether the artwork stayed
inside the area the gantry can actually reach. `plan_program` already clips to
`machine_reach_radius_mm`, so the limit was enforced but invisible: artwork past
the radius was quietly removed rather than shown as over-scale.

Separately, ioSender's **Program limits** panel was read as a machine-envelope
check and is not one. It reads every coordinate literally, so the closing
`G53 G0 X-10 Y-436 (park home)` line - machine coordinates, deliberately outside
the work frame - is reported as if it were a work coordinate. On a real file
that made the panel claim a 597 mm Y span on a 451 mm machine. The tell is that
the span exceeds `$130`/`$131`.

## Implementation

`software/qt_svg_to_gcode.pyw`:

- `GLPreview.rebuild_cache()` builds a `reach_circle` buffer of radius
  `machine_reach_radius_mm` about the preview center, alongside the existing
  grey bed circle. Nothing is drawn when the reach is `0`, which is the
  converter's "no cap" value.
- `paintGL` draws it in `#15803d` when `show_machine_reach` is set, and the
  buffer is registered in the static VBO list.
- `MainWindow.reach_summary()` computes the artwork's radius about its own
  center from `raw_contours` - the pre-clip geometry - and reports either that
  it is inside the reach or by how much it exceeds it. The result goes to the
  preview log and the status line.
- A **Show machine reach guide** checkbox controls the overlay.

## Verification

Offscreen smoke test against a real `GLPreview` and `MainWindow`:

- the `reach_circle` buffer holds 480 vertices (240 segments) and every vertex
  sits exactly `191.4000` mm from the preview center;
- `reach_summary()` reports "artwork radius 200 mm exceeds 100 mm by 100 mm; the
  excess is clipped" for an over-scale input and "artwork radius 40 mm is inside
  100 mm" for an in-scale one.

- `python -m py_compile software\qt_svg_to_gcode.pyw` passes.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 37
  tests.

## Struggles and rejected approaches

- The first smoke test appeared to show a wrong guide radius (241.4 mm) and a
  readout that never said "exceeds". Both were faults in the test, not the code:
  the radius was measured from the origin rather than the preview center, and
  the over-scale fixture was a 200 mm line, whose radius about its own center is
  only 100 mm. Measuring from the center fixed both readings.
- Reading the envelope from the controller (`$130`, `$131`) and the work offset
  was rejected for this change. The converter drives neither; it would need new
  settings and would guess at a G54 that P100/P113 owns.

## Risks and follow-up

- The guide shows `machine_reach_radius_mm`, the converter's own model of the
  gantry's tightest reach from the registered bed center. It is **not** a full
  machine-envelope check: it does not include the work offset (G54), so it cannot
  report where the program will land in machine coordinates. The G53 park move
  is outside its scope entirely.
- The reach radius only stays correct while the magnetic registration holds. If
  the bed center moves, the value must be recomputed, which the roadmap already
  notes for the setting itself.
- The preview only draws the guide once a preview exists, because `paintGL`
  returns early without contours. Choosing a scale before the first preview
  still relies on the status line from the previous one.

## Files

- `software/qt_svg_to_gcode.pyw`: guide buffer, checkbox, radius report.
- `software/README.md`: documents the guide and its limit.
