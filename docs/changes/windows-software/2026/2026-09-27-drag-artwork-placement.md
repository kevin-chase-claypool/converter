---
id: WSW-20260927-007
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
tags:
  - converter
  - preview
  - placement
  - bed
  - drag
  - g54
related:
  - WSW-20260927-004
---

# Drag the artwork on the bed to place it

## Summary

The artwork can be moved off the bed center before conversion. Dragging in the
preview moves the part, the placement is written to two new settings
(`Artwork offset X mm`, `Artwork offset Y mm`), and the next build places the
artwork there.

## Reason

`plan_program` centers the artwork's *bounding box* on the registered bed center.
That is not the same as its visual center for artwork with stray marks or an
asymmetric outline - the F15 cutaway lands visibly down and to the left of the
bed center for exactly that reason - and there was no way to correct it. The
requested control is the one the owner knows from a slicer: grab the part and
move it.

## Implementation

- `software/converter_core/settings.py`: `artwork_offset_x_mm` and
  `artwork_offset_y_mm`, both signed, plus UI fields in Preview settings. The
  validator only requires them to be finite, since negative is meaningful.
- `software/converter_core/gcode.py`: `plan_program` places the artwork's center
  at that offset from the bed center. The reachable disc is fixed on the bed, so
  clipping is expressed in artwork coordinates about
  `source_center - offset`, and the placement is applied when the contours move
  into the bed frame. With `(0, 0)` this is byte-for-byte the previous behaviour.
- `software/qt_svg_to_gcode.pyw`: the vertex shader takes a `shift` uniform, and
  **left-drag now moves the artwork** while Shift+left, middle, and right drag
  pan the view. While dragging, the shader shifts the artwork and its tool path
  so the part moves immediately, and the bed and reach circles stay pinned to the
  bed center. A `placementChanged` signal writes the drag back into the two
  settings fields, so the next Preview picks it up.

The preview tracks two values: `placement`, where the artwork should sit, and
`planned_offset`, what the current plan already bakes in. Their difference is
what the shader applies, so a freshly built preview shows zero shift and a drag
measures from the planned position.

## Verification

- Planner, `stripe_stroke_test.svg`: offset `(0, 0)` gives x[-36.765, 36.765]
  y[-19.350, 19.350]; offset `(10, -5)` gives x[-26.765, 46.765]
  y[-24.350, 14.350] - exactly a +10 / -5 translation with the contour count
  unchanged at 59.
- Preview state, offscreen: `set_planned_offset((10, -5))` leaves placement
  `(10, -5)` and delta `(0, 0)`; a following `set_placement((25, -5))` gives
  delta `(15, 0)`; `on_placement_changed(12.5, -7.25)` writes `'12.50'` and
  `'-7.25'` into the fields.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 48
  tests. The 5 new cases in `software/tests/test_artwork_placement.py` cover the
  centered default, an exact translation, translation-only (every point moves by
  the same delta), and the signed and non-finite validator paths.
- `python -m py_compile` passes for all three changed modules.

**Not verified:** the GLSL change. Adding `uniform vec2 shift` and
`(p + shift) - center` to the vertex shader needs a real OpenGL context to
compile, and the environment used for this work has none, so the shader was
reviewed by eye and everything around it was tested offscreen. Confirm on first
run that the preview still draws; if the shader failed to compile the widget
prints `OpenGL vertex shader failed` and shows a blank view.

## Struggles and rejected approaches

- The first reading was that the preview would need a full rebuild per drag
  frame. It does not: the shift uniform moves the displayed geometry, and only
  the re-render needs the planner.
- Moving the bed and reach circles to follow the drag was rejected. They mark
  fixed machine geometry, so they stay on the bed center; only the artwork moves.
  This needed no change, because `preview_center` is already `plan["center"]`,
  which is the bed center.
- Repurposing the existing left-drag pan for placement and leaving panning
  unreachable was rejected; Shift+left, middle, and right drag now pan.

## Risks and follow-up

- While dragging, the displayed artwork is the *existing* plan translated. The
  reach clip is not re-evaluated, so a part dragged past the green circle will
  look out of bounds until Preview is pressed - and Preview is what actually
  trims it. The circle is the truth during a drag.
- The red machine-frame pen-down overlay shifts with the drag too, so it is
  equally stale until a re-render.
- The offset is a placement of the artwork's bounding-box center, not a free
  transform: there is no rotation or per-part support, and the bed's own
  registration is untouched. Placing the artwork does not change G54.
- Typing into the two fields updates the next build but not the live view; only
  dragging gives immediate feedback.

## Files

- `software/converter_core/settings.py`: placement settings and fields.
- `software/converter_core/gcode.py`: placement applied in `plan_program`.
- `software/qt_svg_to_gcode.pyw`: shader shift, drag gesture, field sync.
- `software/tests/test_artwork_placement.py`: new coverage.
- `software/README.md`: documents the gesture and the fields.
