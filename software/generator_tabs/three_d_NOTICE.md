# 3D Wireframe tab - third-party notice

The 3D Wireframe tab re-implements the hidden-line vector rendering approach of
two MIT-licensed projects:

- **fogleman/ln** (https://github.com/fogleman/ln) - depth-tested 3D line art.
- **RobMakesThings/Viewport.js** (https://github.com/RobMakesThings/Viewport.js)
  - vector rendering of 3D scenes.

Both upstream projects are licensed under the MIT License; their license texts
ship in the respective repository `LICENSE` files. The Python implementation in
`three_d_tab.py` (OBJ/STL loading, orthographic projection, z-buffer edge
visibility) was written for this repository; no upstream source code was
copied. Attribution is kept here because the rendering approach comes from the
upstream work.
