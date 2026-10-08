---
id: WSW-20261007-022
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - preview
  - opengl
  - ink-simulation
related:
  - WSW-20261007-003
  - WSW-20261007-007
  - WSW-20261007-018
---

# Add an ink-simulation (multiply) preview for CMYK

## Summary

The preview panel gains an **Ink simulation (multiply)** checkbox. With it
on, tagged CMYK artwork is composited the way translucent pens actually
overprint: the solid ink layers multiply over the paper white in plot order
(C x M x Y x K), instead of the default render, which paints each layer
opaquely and lets the last layer win. Hidden inks multiply by white (a
no-op), so the live layer checkboxes keep working, and every other tool's
preview is unchanged.

## Reason

Owner: "colors dont appear to be combining well. inspect." Inspection: the
separation is behaving as designed (max GCR with auto levels off collapses
cyan in warm areas), but at the owner's 0.30 mm pitch - about one pen width -
every ink layer covers the whole area (nearly solid films), so the opaque
per-layer preview flattened toward the last-drawn inks. The actual print
multiplies the four films and reads much darker/muddier. This is the
print-simulation preview the calibration work was building toward.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `GLPreview.set_ink_simulation()`;
  `rebuild_cache` also builds `artwork_solid_color` (full-strength ink
  colours, multiply-neutral white for hidden inks via the new
  `ink_vertex_colors(hidden_white=...)`); `paintGL` switches to
  `glBlendFunc(GL_DST_COLOR, GL_ZERO)` for the artwork pass in simulation
  mode and restores normal alpha blending for the guides; `draw_static`
  accepts a `color_name` so the geometry can bind the solid colour buffer.
  The new `artwork_solid_color` VBO is registered at GL init.
- Preview panel: the **Ink simulation (multiply)** checkbox next to Red
  motion lines; `software/README.md` documents it.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 386
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  the checkbox lives in the preview panel and drives
  `gl_preview.ink_simulation`, and the solid colour buffer keeps visible
  inks at full alpha while hidden inks become white/zero-alpha (multiply
  neutral) with the pale buffer still hiding them.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Reusing the drawn-path buffer for the simulation was rejected: it only
  covers the progress prefix, so scrubbing the slider would erase the
  simulated print. The solid colour array is built once per preview instead.
- A custom shader was rejected for v1: `GL_DST_COLOR` multiply blending
  gives the same result with no new shader state.

## Risks and follow-up

- The simulation uses the display ink colours, not yet the measured
  calibration profile; once a plotted sheet is analyzed, those profile
  numbers can replace them for an exact match. Overdraw and paper texture
  are not simulated.
- Colour management is approximate: the multiply happens in the widget's
  framebuffer space, the usual caveat for on-screen print previews.

## Files

- `software/qt_svg_to_gcode.pyw`: multiply pass, solid colours, checkbox.
- `software/tests/test_generator_tabs.py`: toggle and colour-buffer tests.
- `software/README.md`: preview panel documentation.
