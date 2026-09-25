---
id: WSW-20260924-015
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - preview
  - polar
---

# Show the artwork alone in the preview

## Summary

The preview now draws only the bed-frame artwork — upright and unrotated — and
no longer overlays the machine-frame gantry path, travel moves, crosshair, or
tool marker. Playback progress still shows as the artwork's strokes filling in
from the undrawn color.

## Reason

For a rotating-bed plotter the gantry's machine-frame path is a tangle of short
polar jogs. The preview drew that path (and pen-up travel, a crosshair, and a
tool marker, all in machine coordinates) on top of the artwork, and also rotated
the bed-attached artwork by the bed's final angle (over 90 degrees for a long
plot). The result read as a scribble of scratch lines over the text, even when
the artwork itself was correct — which is exactly what the operator reported as
"chickenscratch lines over the text."

## Implementation

- `paintGL` now sets the bed-rotation uniform to zero for the static bed
  geometry, so the artwork is shown upright in its own frame.
- Removed the static `travel` and `motion` draws and the dynamic
  active-segment, crosshair, pen-tip, and tool-marker draws that were all in
  machine coordinates.
- Kept the bed circle for scale reference and the overlay position readout.

The vertex buffers for the removed layers are still built but simply not drawn,
so no other code path changed.

## Verification

- `python -m py_compile software/qt_svg_to_gcode.pyw` passes.
- The 24 converter tests still pass (the change is UI-only and does not touch
  `converter_core`).

## Struggles and rejected approaches

Keeping the machine path but de-emphasising it was rejected: any overlay in
machine coordinates still reads as noise over the artwork. The machine view is
genuinely useful for debugging bed collisions, so it is a candidate to restore
behind an explicit opt-in toggle rather than drawn by default.

## Risks and follow-up

- The machine-frame path is no longer visible in the preview; if a future
  debugging task needs it, add a "show machine path" toggle instead of drawing
  it unconditionally.

## Files

- `software/qt_svg_to_gcode.pyw`
