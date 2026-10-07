---
id: WSW-20261007-003
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/geometry.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
tags:
  - cmyk
  - opengl
  - preview
  - color-separation
  - generator-tabs
related:
  - WSW-20261007-001
  - WSW-20261007-002
---

# Draw the CMYK preview per ink colour

## Summary

When the active tool is **CMYK**, the shared OpenGL preview now draws every
visible layer in that ink's own colour: not-yet-drawn marks appear in a pale
tint of the ink and the drawn portion in the full ink colour (cyan #00a6d6,
magenta #d6009a, yellow #f0c400, black #222222). The four layers overlay the
way they will mesh on paper, and the preview-layer checkboxes still decide
which inks are shown. The red machine-motion overlay and every other tool keep
their existing single-colour preview.

## Reason

After the CMYK tool shipped, the project owner asked to see the four layers
overlaid in colour to judge how the inks mesh. The shared preview drew all
contours in one drawing colour because colours were lost when the SVG was
parsed into contour geometry.

## Implementation

- `software/converter_core/cmyk.py`: `InkTrail` (a list subclass carrying an
  ``ink`` channel) and `tag_ink(contours, ink)`.
- `software/converter_core/geometry.py`: `retag_contour` now rebuilds the
  source type and copies its attributes instead of normalizing to
  `FillTrail`/list, so ink tags ride through scaling, pen compensation and bed
  clipping. `FillTrail` keep-down-bridging behaviour is unchanged.
- `software/qt_svg_to_gcode.pyw`:
  - `MainWindow.load_preview_contours` is the preview-fill entry point. When
    the active tab implements `preview_layers()`, it returns ordered
    `(ink, svg_path)` pairs; each layer SVG is loaded separately and tagged,
    preserving the combined-SVG contour order. Other tabs take the original
    single-file path.
  - `PreviewWorker.run` uses that method; `analyze_program` still loads each
    layer's SVG untagged for G-code.
  - The preview shader gained an `ink_color` vertex attribute and a
    `use_vertex_color` uniform (`mix(color, vcolor, use)`); the shader sources
    are module constants so they can be compile-tested.
  - `ink_vertex_colors(contours, moves)` builds the `artwork_color` and
    `drawn_path_color` buffers (pale ink for artwork, full ink for the drawn
    path in move order) and returns `(None, None)` for untagged artwork, so
    every other tool draws exactly as before.
  - `GLPreview.draw_static` binds the colour buffer and attribute 1 only when
    the per-ink colours are present; bed circles, reach guides, travel and the
    red motion overlay keep uniform colours.
- `software/generator_tabs/cmyk_tab.py`: `build_svg` caches which layers the
  checkboxes left visible and `preview_layers()` returns their
  `(ink, path)` pairs from cached state (safe for the preview thread). The
  contract is documented in `generator_tabs/README.md`.

## Verification

- 345 tests pass (1 skipped: the shader-compile test skips when
  `QT_QPA_PLATFORM=offscreen` cannot create a GL context).
- New coverage: ink tags survive scaling and bed clipping; `ink_vertex_colors`
  maps contour tags and move indices to the pale/full RGBA arrays and falls
  back to `(None, None)` untagged; the GL preview builds `artwork_color` /
  `drawn_path_color` buffers with matching vertex counts and omits them for
  untagged artwork; the CMYK tab reports its visible layers; and
  `load_preview_contours` tags all four inks.
- Shader compile/link verified against a real OpenGL context on this machine:
  vertex OK, fragment OK, link clean, `use_vertex_color` uniform found.
- Off-screen full-window dry run through the real preview pipeline: GL program
  linked, preview belonged to the CMYK tab, 175 contours / 2102 moves with
  inks {c, m, y, k}, and 2800 artwork colour vertices matched 2800 artwork
  vertices.
- `tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- `retag_contour` originally rebuilt any tagged contour as a plain
  `FillTrail`, which discarded `InkTrail` and its attribute; the fix preserves
  the source type generally (with a `FillTrail` fallback) so both tag kinds
  survive.
- QOpenGLWidget under `QT_QPA_PLATFORM=offscreen` never creates a context, so
  the shader test skips there; the shaders were compiled once on the real WGL
  context instead of relying on the skip.
- Colouring by contour identity after planning was rejected: bed clipping can
  split contours, so the ink tag rides on the contour object itself and the
  drawn path is coloured through each draw move's contour index.

## Risks and follow-up

- Keep-down bridges would disable the per-ink colours (fallback to the
  single-colour preview); CMYK contours are plain `InkTrail`s, so the planner
  never bridges them.
- The red machine-motion overlay is intentionally not tinted; it remains the
  G-code sanity check.
- Colours are display-only; the G-code contract is unchanged. Paper meshing
  still depends on pen choice, overdraw and registration.

## Files

- `software/converter_core/cmyk.py`: `InkTrail`, `tag_ink`.
- `software/converter_core/geometry.py`: tag-preserving `retag_contour`.
- `software/qt_svg_to_gcode.pyw`: preview loader, shader, colour buffers.
- `software/generator_tabs/cmyk_tab.py`: `preview_layers`.
- `software/generator_tabs/README.md`, `software/generator_tabs/__init__.py`:
  host contract.
- `software/tests/test_cmyk_tab.py`, `software/tests/test_generator_tabs.py`:
  coverage.
- `software/README.md`: CMYK preview documentation.
