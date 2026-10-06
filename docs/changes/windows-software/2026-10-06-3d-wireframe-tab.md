---
id: WSW-20261006-004
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/three_d_tab.py
tags:
  - user-interface
  - generators
  - 3d
related:
  - WSW-20261006-001
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# 3D Wireframe generator tab

## Summary

The converter now has a **3D Wireframe** tab that loads an OBJ or STL mesh,
projects it orthographically at a chosen orientation, removes hidden lines
with a z-buffer, previews the result, and hands the SVG to the Convert tab.

## Reason

The app had no 3D input path; the survey lists `fogleman/ln` and
`Viewport.js` (both MIT) as the community's vector-3D references. This is a
non-duplicate capability.

## Implementation

- `software/generator_tabs/three_d_tab.py` (`TITLE = "3D Wireframe"`):
  OBJ parsing (fan-triangulated polygons), ASCII and binary STL parsing,
  rotation matrix, orthographic projection fitted to the page, triangle
  rasterization into a z-buffer, and edge sampling with a 3x3 neighbourhood
  depth test. Styles: hidden-line wireframe, silhouette outlines, all edges.
- Controls: model file, style, yaw/pitch/roll, target width, sample step,
  page size, margin, line width.
- Output is SVG through `host.use_svg`; the tab never writes G-code.
- Attribution: `three_d_NOTICE.md`.

## Verification

- `python -m unittest discover -s software\tests -p "test_three_d_tab.py" -v`
  -> 6 tests pass: OBJ cube parse, binary STL parse, deterministic output,
  occlusion culling, SVG/XML, and the tab hand-off.
- Full suite: `python -m unittest discover -s software\tests` -> 221 tests
  pass.

## Struggles and rejected approaches

- A first cube probe could not prove culling: in an axis-aligned orthographic
  cube the hidden edge is collinear with a visible edge. The test now uses a
  plate with a small triangle floating behind it, where the hidden edge has no
  visible twin.
- Edges that project exactly onto a silhouette boundary needed a 3x3
  neighbourhood maximum in the depth test; a single-pixel sample saw the
  background and left boundary edges fully drawn.

## Risks and follow-up

- Triangle count is capped at 40,000 and z-buffer rasterization is a Python
  loop per triangle; large meshes are refused rather than hanging the tab.
- Hidden-line removal is a sampled z-buffer approximation; no face hatching or
  anti-aliasing yet.
- STL parsing assumes the binary layout `84 + 50*n`; malformed files fall back
  to ASCII parsing and report an error if no triangles are found.
- Owner review of the visual output is the next required step.

## Files

- `software/generator_tabs/three_d_tab.py`: tab, loaders, projection, and
  hidden-line renderer.
- `software/generator_tabs/three_d_NOTICE.md`: MIT attributions.
- `software/tests/test_three_d_tab.py`: parser, culling, and tab tests.
