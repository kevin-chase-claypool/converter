---
id: WSW-20261006-025
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - generators
  - fidelity
  - audit
related:
  - docs/research/2026-10-06-generated-tools-accuracy-audit.md
---

# Tool accuracy audit and source-parity fixes

## Summary

Every generator tool was audited against its upstream source. Fixed in this
batch: the Harmonograph physical pendulum model, 3D perspective and built-in
primitives, Line Draw's upstream patch hatching, SquiggleCam's resolution
control, and the Postcard default page. Remaining differences are documented
in `docs/research/2026-10-06-generated-tools-accuracy-audit.md`.

## Reason

The owner asked for an accuracy audit against the sources and fixes where
possible, after finding earlier ports were simplified.

## Implementation

- `harmonograph_tab.py`: `harmonograph_pendulum_polylines()` ports the
  upstream `updateXY()` equations and exposes d, c, p, q, A, B, u, v, R, S,
  f, g, h plus duration, samples, and smoothing; the simple Lissajous remains
  as a second model.
- `three_d_tab.py`: `project_vertices(..., projection=, camera_distance=)`
  adds perspective; `cube_mesh`, `sphere_mesh`, `cylinder_mesh`,
  `cone_mesh`, and `terrain_mesh` add the primitive set; the tab gains Source
  and Camera groups.
- `line_draw_tab.py`: `_hatch_patches()` ports upstream `hatch()` (patch grid,
  144/64/16 thresholds, horizontal/anti-diagonal strokes, chain merging,
  smooth-noise jitter); the tab exposes the three thresholds.
- `squigglecam_tab.py`: resolution control; `postcard_tab.py`: 7x5 in
  landscape default matching upstream `printW`/`printH`.

## Verification

- New tests: Harmonograph physical model (deterministic, damped), 3D
  primitives and perspective magnification, and the tab builds for both.
- Full suite: `python -m unittest discover -s software\tests` -> 286 tests
  pass.

## Struggles and rejected approaches

- Porting the snowflake lattice simulation and 3D CSG in this batch was
  rejected: each is a large feature and the audit documents them rather than
  implying parity.
- The upstream linedraw `-j` shear in the hatch jitter is a one-pixel
  per-point artifact; the port keeps the noise jitter and omits the shear.

## Risks and follow-up

- Line Draw contours still use the local Sobel/NMS pipeline; matching the
  upstream `find_edges` + dot connection is a roadmap item.
- The harmonograph Bezier export option is approximated by Chaikin smoothing.

## Files

- `docs/research/2026-10-06-generated-tools-accuracy-audit.md`: full table.
- `software/generator_tabs/harmonograph_tab.py`, `three_d_tab.py`,
  `line_draw_tab.py`, `squigglecam_tab.py`, `postcard_tab.py`: fixes.
- `software/tests/test_harmonograph_tab.py`, `test_three_d_tab.py`: coverage.
- `software/README.md`: updated control lists.
