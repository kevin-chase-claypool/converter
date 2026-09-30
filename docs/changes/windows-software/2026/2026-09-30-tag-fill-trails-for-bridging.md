---
id: WSW-20260930-002
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/converter_core/gcode.py
  - software/converter_core/kinematics.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_infill_bridging.py
tags:
  - infill
  - bridge
  - pen-up
  - correctness
  - preview
related:
  - WSW-20260924-007
  - docs/HANDOFF.md
---

# Keep pen-down bridging off by default and tag generated fill trails

## Summary

The keep-down bridge now needs the new **Keep pen down between fill trails**
setting (shipped off) and only applies between contours produced by the fill
code, which carry a `FillTrail` tag through the geometry pipeline. The artwork's
own open strokes can no longer be stitched together, so connectors are never
drawn across blank paper.

## Reason

The 2026-09-30 mandala print showed pen-down zig-zag connectors in white space.
`mom.gcode` contained 1,687 `(keep-down bridge)` moves in 367 chains (the
largest: 13 bridges over a 23 mm span), after the pre-fit generation had zero.
The 2026-09-24 rule *"keep the pen down only between infill trails"* was
implemented as *"both contours are open"*, which cannot tell a fill trail from a
line-art Mandala's own open strokes (ticks, petals, fan ribs). The 2026-09-29
fit rescale (1.0 -> 0.964) then shrank those gaps under the `0.85 * fill
spacing` guard, so the bridges appeared all at once.

## Implementation

- `geometry.py`: new `FillTrail(list)` marker plus `retag_contour`. Fill output
  is tagged where it is generated, and the tag is preserved across every
  transform that rebuilds a contour: element matrix, Y flip, scale,
  pen-width compensation, bed clipping, plan-frame placement, point filtering
  and path reversal. The tag is metadata only; it draws nothing.
- `gcode.py`, `kinematics.py`: `bridge_motion` returns early unless
  `keep_down_bridges` is on, and both emission paths require *both* contours to
  be `FillTrail`s. Preview and saved G-code use the same rule.
- `settings.py`: `keep_down_bridges` (default `False`), a Fill-group checkbox,
  and a tooltip; `qt_svg_to_gcode.pyw` reads the checkbox into settings and
  marks the preview stale when it changes.
- `software/README.md` and `docs/HANDOFF.md` describe the new rule and default.

## Verification

- All eight test modules pass. New tests: bridging is off by default (a dense
  fill then costs one pen cycle per contour), and two artwork strokes 2 mm
  apart are never bridged even with the option on.
- Real-artwork smoke test on `samples/svg/spirit-logo-purple-rgb.svg`: with the
  option on and fill off (spacing 0) there are **0** bridges; with fill on
  (spacing 3 mm) there are 68 bridges and 569 `M3` lines, against 0 bridges and
  637 `M3` lines with the option off.
- `python -m py_compile` passes for the changed modules, and
  `python tools\docs_index.py --write/--check` pass.

## Struggles and rejected approaches

The first cut lost the tag whenever a path was reversed (`list(reversed(...))`),
which dropped most of the dense-fill chains (46 pen cycles instead of 4); the
tests caught it and the reversal now retags. A geometry-only guard (for example
"bridge only if the gap is under 1 mm") was rejected: the mandala's stroke ends
sit inside every such threshold, so only provenance can separate artwork from
fill.

## Risks and follow-up

- A future transform that rebuilds a contour without `retag_contour` silently
  costs pen cycles (safe). A transform that ever *adds* the tag to artwork
  contours would reintroduce the defect, so new transforms need a test.
- Bridging ships off: the mandala job costs about 48 minutes of extra pen
  cycles until a print verifies the tagged path well enough to enable it.
- Enabling it is per-job via the checkbox; nothing about the default changes
  the emitted geometry other than fewer, safer connectors.

## Files

- `software/converter_core/geometry.py`: `FillTrail`, `retag_contour`, tag
  preservation and fill-side tagging.
- `software/converter_core/gcode.py`: settings gate and `FillTrail` requirement
  in both emission paths.
- `software/converter_core/kinematics.py`: keep the tag when a path is reversed
  or re-ordered.
- `software/converter_core/settings.py`: `keep_down_bridges`, checkbox, tooltip.
- `software/qt_svg_to_gcode.pyw`: checkbox wiring.
- `software/tests/test_infill_bridging.py`: default-off and never-bridge-strokes
  tests.
- `software/README.md`, `docs/HANDOFF.md`: current behavior.
- `docs/project/ENGINEERING_LOG.md`, `docs/project/ROADMAP.md`: record and
  follow-up.
