---
id: WSW-20261006-016
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs
tags:
  - user-interface
  - generators
related:
  - WSW-20261006-015
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Add Harmonograph, Snowflake, and Truchet tabs

## Summary

The next three non-duplicate generator tabs are in the converter:
**Harmonograph** and **Snowflake** ported from MIT-licensed sources found in
the r/plotterart survey, and **Truchet** implemented from the classic tile
concept. The tab bar is now Convert, Flow Field, Line Draw, 3D Wireframe,
Harmonograph, Snowflake, Truchet.

## Reason

The survey's next-ranked permissive, non-duplicate candidates were
`ttencate/harmonograph` (damped Lissajous curves) and `vishnubob/snowflake`
(radial branch generator). The sub's Truchet repositories had no license, so
that tab uses the public-domain tile concept instead of their code.

## Implementation

- `harmonograph_tab.py`: one to four damped Lissajous curves with frequency
  X/Y, phase, damping, turns, sample count, curve size, page, line width, and
  artwork scale.
- `snowflake_tab.py`: recursive arms with branch depth, angle, scale, and
  angle/length jitter, plus page, line width, and artwork scale.
- `truchet_tab.py`: square grid of quarter-arc or diagonal tiles (arcs,
  diagonals, or mixed), tile size, arc segments, page, line width, and
  artwork scale.
- `software/generator_tabs/__init__.py`: tabs now read an explicit `ORDER`
  constant so the three original tabs keep their positions and the new tabs
  follow in the order above.
- Attribution: `harmonograph_NOTICE.md`, `snowflake_NOTICE.md`,
  `truchet_NOTICE.md`.

## Verification

- `python -m unittest discover -s software\tests -p "test_harmonograph_tab.py" -v`
  -> 4 pass; `test_snowflake_tab.py` -> 4 pass; `test_truchet_tab.py` -> 5
  pass; each builds SVG through `build_svg()`.
- Shell test asserts the exact tab order above; the per-tab scale test covers
  all six generator pages.
- Full suite: `python -m unittest discover -s software\tests` -> 244 tests
  pass.
- Offscreen render: seven compact tabs fit the top bar, and the Harmonograph
  page fills the settings column with the shared preview on the right.

## Struggles and rejected approaches

- Alphabetical discovery put Harmonograph between Flow Field and Line Draw;
  the `ORDER` constant was added instead of renaming files.
- Monoline text was deferred: it needs a vendored single-stroke font dataset,
  which is a larger licensing and asset addition than these three.

## Risks and follow-up

- Snowflake branch count grows as `2^(depth+1)`, so depth is capped at 5 per
  arm; Truchet tile count grows with the page area, so large pages with small
  tiles produce many paths.

## Files

- `software/generator_tabs/harmonograph_tab.py`, `snowflake_tab.py`,
  `truchet_tab.py`: tabs and algorithms.
- `software/generator_tabs/*_NOTICE.md`: attribution.
- `software/generator_tabs/__init__.py`: ordered discovery.
- `software/tests/test_harmonograph_tab.py`, `test_snowflake_tab.py`,
  `test_truchet_tab.py`: coverage.
- `software/README.md`: tab list.
