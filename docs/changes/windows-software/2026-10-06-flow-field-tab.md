---
id: WSW-20261006-002
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/flow_field_tab.py
tags:
  - user-interface
  - generators
  - flow-field
related:
  - WSW-20261006-001
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Flow Field generator tab

## Summary

The converter now has a **Flow Field** tab that generates evenly spaced
streamlines from a procedural noise field or from an image's luminance
gradient, previews them, and hands the SVG to the Convert tab.

## Reason

The r/plotterart survey's highest-value non-duplicate gap was flow-field line
art. The converter already had fixed-shape fills (waves, gyroid, terrain,
halftone, and so on) but no streamline placement; the permissive upstream is
`msurguy/flow-lines` (MIT).

## Implementation

- `software/generator_tabs/flow_field_tab.py` (`TITLE = "Flow Field"`):
  fractal value-noise field or image luminance-gradient field, jittered-grid
  seeding, forward and reverse Euler integration, and a spatial hash of
  accepted segments so candidates respect a point-to-segment separation.
- Controls: field source, optional image path, invert, image cutoff, seed,
  noise scale, octaves, spacing, step, max steps, line width, page size and
  margin.
- Output is SVG through `host.use_svg`; the tab never writes G-code.
- Attribution: `flow_field_NOTICE.md`.

## Verification

- `python -m unittest discover -s software\tests -p "test_flow_field_tab.py" -v`
  -> 4 tests pass: determinism, cross-streamline spacing, SVG/XML, and the tab
  hand-off to a fake host.
- Full suite: `python -m unittest discover -s software\tests` -> 221 tests
  pass.
- Headless window check prints the tab bar as
  `['Convert', 'Flow Field', 'Line Draw', '3D Wireframe']`.

## Struggles and rejected approaches

The first separation check compared candidate points only against previously
accepted points. Two streamlines could still cross between samples, which the
spacing test caught at 1.82 mm against a 2.4 mm gate. The check now measures
point-to-segment distance against segments stored in a spatial hash, so
crossings are rejected.

## Risks and follow-up

- Integration is pure Python; a dense full page (small spacing, long steps)
  takes seconds, and the tab caps accepted points at 250,000.
- Image mode needs Pillow (already installed for the app's raster import).
- Owner review of the visual output is the next required step.

## Files

- `software/generator_tabs/flow_field_tab.py`: tab and algorithm.
- `software/generator_tabs/flow_field_NOTICE.md`: MIT attribution.
- `software/tests/test_flow_field_tab.py`: algorithm and tab tests.
