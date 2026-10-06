# Generator tab fidelity audit

Date: 2026-10-06

## Question

Have the generator tabs lost options that their upstream tools offer? The
owner noticed the ports looked simplified and asked for an audit.

## Method

Upstream sources were fetched on 2026-10-06 and read option-by-option:
`msurguy/flow-lines`, `LingDong-/linedraw`, `fogleman/ln`,
`RobMakesThings/Viewport.js`, `ttencate/harmonograph`, `vishnubob/snowflake`,
`cadin/plotter-text`, `piebro/substitution-system`, and
`cadin/plotter-postcard`. This note records the gaps; the larger ones are
tracked in `docs/project/ROADMAP.md`.

## Result

The tabs are simplified relative to upstream, and some options were missing.
Two cheap gaps were restored in this batch (Line Draw simplify/resolution,
Postcard message text), two attributions were corrected (Flow Field is an
adaptation of the placement method, not the formula UI; Snowflake is not the
upstream lattice simulation), and the remaining gaps are listed below.

| Tab | Upstream options | Our options | Gap |
|---|---|---|---|
| Flow Field | Formula input for x/y, integration time, separation distance, line parameters, SVG export | Procedural noise, image-gradient, or formula field (angle or vector, with presets), seed, noise scale, octaves, spacing, step, max steps, page, line width, scale | Formula-driven fields restored 2026-10-06 (`WSW-20261006-023`); separation distance is still derived from spacing; favorites/permalink are web-app features (N/A). |
| Line Draw | Contour/hatch modes, hatch size, contour simplify, resolution, optional OpenCV, Perlin sketch style | Modes, edge threshold, hatch spacing/tone, jitter, min length, **simplify (restored)**, **resolution (restored)**, seed | Perlin-noise sketch style missing (ours is uniform jitter); OpenCV acceleration N/A; hatch is in mm rather than patch pixels. |
| 3D Wireframe | Sphere/cube/cone/cylinder/shard/terrain primitives, OBJ/STL, vector texturing, CSG, PNG/SVG, camera eye/center/up, perspective, colours | OBJ/STL, orthographic projection, yaw/pitch/roll, hidden-line/silhouette/all edges, sample step, target width, line width, scale | Perspective camera, primitives/terrain, surface hatching, CSG, and colour handling are missing. |
| Harmonograph | Pendulum lengths p/q, disk/paper/rotation radii, amplitudes A/B, phase offsets u/v, per-axis damping R/S, frequencies f/g and difference h, pen width, resolution, Bezier smoothing | Frequency X/Y, one phase, one damping, turns, samples, curves, curve size | The physical two-pendulum + rotating-disk model (per-axis amplitude/phase/damping, difference frequency) and Bezier smoothing are missing. |
| Snowflake | Mesoscopic lattice-growth simulation (Gravner-Griffeath), PyPy engine, potrace exports | Independent radial branch generator (arms, depth, angle, scale, jitter) | Not a port: the upstream is a simulation; our tab is an independent dendritic generator. Attribution corrected. |
| Truchet | None used (concept; the subreddit repo had no license) | Tile size, arcs/diagonals/mixed, arc segments, seed | No upstream options to preserve. |
| Text | Custom SVG fonts + data.json, kerning pairs, font editor, drawText/drawTextCentered | Hershey simplex, size, tracking, line spacing, alignment, page | Custom font import and kerning-pair support are missing. |
| Substitution | Palette colours, random rules, iterations; vpype pixelart plotting (pen width, overdraw, upscale, layers) | Palette size, iterations, seed, boundary/diagonal styles | Explicit palette editing and per-colour layer export are missing (multi-pen feature). |
| Postcard | Paper size, pen thickness, caption/message/address, text size, line height, margins, per-pen layers, PNG preview | Page presets, divider, address lines, stamp, caption, **message (restored)**, address, text size, tracking, margins, line width | Per-pen layers (multi-pen) missing; PNG preview is covered by the in-app preview. |

## Restored in this batch

- Line Draw: **Simplify** (px) and **Resolution** (px) controls; the hardcoded
  0.75 px simplification and 900 px cap became settings.
- Postcard: **Message** text block in the left column, the upstream's third
  text field (it already had caption and address).

## Attribution corrections

- Flow Field: documented as an adaptation of the evenly-spaced streamline
  placement method; the upstream formula UI and field sources are not ported.
- Snowflake: documented as an independent branch generator inspired by the
  upstream art; the upstream mesoscopic lattice model is not reproduced.

## Not restored (tracked in the roadmap)

Line Draw Perlin sketch style; 3D perspective, primitives, texturing and CSG;
harmonograph's physical pendulum model and Bezier smoothing; snowflake lattice
simulation; Text custom fonts and kerning; Substitution palette editing and
colour layers.

## Tools added after this audit

The next r/plotterart list batch added three more permissive ports:
SquiggleCam (msurguy, MIT), Pixel Art (vpype-pixelart, MIT), and Wobble
(cadin/line-wobbler, Unlicense). Plotterfun remains queued: it is a
multi-algorithm suite and needs its own batch rather than a partial port.
