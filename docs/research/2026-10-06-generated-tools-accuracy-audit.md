# Generated tools accuracy audit

Date: 2026-10-06

## Question

Do the implemented generator tools match their upstream sources, and what can
be fixed now?

## Method

Each tool was compared against the upstream source fetched on 2026-10-06.
Findings are marked **fixed** (changed in this batch), **documented** (an
intentional, stated adaptation), or **open** (tracked in the roadmap).

## Per-tool findings

| Tool | Source | Finding | Status |
|---|---|---|---|
| Flow Field | msurguy/flow-lines (MIT), anvaka/streamlines | Upstream is formula-driven; the tab now has the formula source with a safe evaluator, plus noise and image fields. Placement is a local implementation (jittered seeding, segment-distance spacing) rather than a line-by-line port of anvaka/streamlines; separation is derived from spacing. | Formula **fixed**; placement difference **documented** |
| Line Draw | LingDong-/linedraw (MIT) | Hatching now ports `hatch()`: patch grid, thresholds 144/64/16, one/two horizontal strokes plus the anti-diagonal, chain merging, and smooth-noise jitter. The upstream `-j` shear is omitted. Contours still use Sobel/NMS/RDP rather than upstream `find_edges` + dot connection + every-8th-point decimation. | Hatch **fixed**; contour pipeline **open** |
| 3D Wireframe | fogleman/ln (MIT), Viewport.js (MIT) | Perspective projection and built-in primitives (cube, sphere, cylinder, cone, terrain plane) added; hidden-line z-buffer unchanged. Still missing: CSG, surface/vector texturing, eye/center/up camera, colour handling. | Perspective + primitives **fixed**; CSG/texturing **open** |
| Harmonograph | ttencate/harmonograph (MIT) | The upstream physical model is now ported verbatim (d, c, p, q, A, B, u, v, R, S, f, g, h) with duration/samples; Chaikin smoothing stands in for the SVG Bezier option. The simple Lissajous remains as a second model. | **Fixed** |
| Snowflake | vishnubob/snowflake (MIT) | Upstream is a mesoscopic lattice-growth simulation; the tab is an independent dendritic branch generator. No code was copied; the notice states this. | **Documented**; lattice port **open** |
| Truchet | Public-domain tile concept | Two opposite quarter-arcs per tile or one of two diagonals; no upstream code exists to match. | Matches the concept |
| Text | Hershey simplex (public domain) + cadin/plotter-text (Unlicense) | Parser follows the published `.jhf` format (bearings, `" R"` pen-up, ASCII 32+ line order) and glyph shapes were render-verified. Custom font import and kerning pairs from plotter-text are not implemented. | Font verified; custom fonts **open** |
| Substitution | piebro/substitution-system (MIT) | Rule generation matches upstream (2x2 random replacement per palette colour, 2x2 start, doubling per iteration). Rendering is a single-pen adaptation; palette editing and per-colour layers are missing. | Algorithm matches; layers **open** |
| Postcard | cadin/plotter-postcard (Unlicense) | Layout concept matches; default page is now the upstream 7x5 in landscape and caption/message/address are all present. Per-pen layers and exact upstream text metrics are not ported. | Defaults **fixed**; layers/metrics **open** |
| SquiggleCam | msurguy/SquiggleCam (MIT) | Row loop, brightness/contrast formulas, thresholds, phase accumulation, and amplitude verified line-by-line against `App.vue`; resolution control added for the upstream canvas width/height. | **Fixed** |
| Pixel Art | abey79/vpype-pixelart (MIT) | `big` trajectory/offset, `line` runs with overdraw, and `snake` walk verified against `pixelart.py`; singletons become ticks. Colour layers are fused for the single pen; snake start/direction order is deterministic where upstream iterates a set. | Modes verified; layers **documented** |
| Wobble | cadin/line-wobbler (Unlicense) | Subdivision, perpendicular amplitude, parallel frequency-jitter, and endpoint toggles match `calculatePoints()`. Endpoint wobble applies to each contour's ends (not every segment end) so pen joints stay continuous. | **Documented** |

## Fixed in this batch

- Harmonograph: physical two-pendulum + rotating-disk model (default) with all
  upstream parameters.
- 3D Wireframe: perspective camera and cube/sphere/cylinder/cone/terrain
  primitives.
- Line Draw: upstream patch hatching (144/64/16 levels, horizontal +
  anti-diagonal strokes, chain merge).
- SquiggleCam: resolution control.
- Postcard: upstream default page (7x5 in landscape).

## Remaining gaps (roadmap)

3D CSG/texturing/colour; Line Draw's upstream contour pipeline; snowflake
lattice simulation; Text custom fonts and kerning; Substitution/Postcard/Pixel
Art per-colour layers. Plotterfun is not a port: the complete upstream web
app is vendored and embedded as one tab (`WSW-20261006-028`).
