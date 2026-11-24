---
id: WSW-20261124-001
date: 2026-11-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/converter_core/settings.py
  - software/converter_core/cmyk.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_screen_chaining.py
tags:
  - cmyk
  - edge-flow
  - pen-up
  - pen-down-chain
  - x-theta
  - y-theta
  - print-time
  - screen-geometry
related:
  - WSW-20261123-019
---

# Chain adjacent screen contours after Xθ/Yθ planning

## Summary

Generated CMYK screen marks now keep the pen down across adjacent same-ink
contours in the planner's final Xθ/Yθ order when the paper-space gap is inside
the existing **Keep pen down** limit. Real gaps remain pen-ups.

## Reason

The previous chain pass ran before motion planning. The Xθ/Yθ planner then
reordered and reversed the resulting contours, often placing their endpoints
next to one another, but the emitter still inserted `M5`, travel, and `M3`
between every contour. On the current Ben3 set, 1,899-2,118 pen-down strokes
remained per ink even though 73-77% of the consecutive planner transitions had
endpoints within the existing 5 mm chain gap.

## Implementation

- Added `ScreenTrail`, a list subtype that marks only generated screen marks as
  eligible for post-planning chaining.
- Serialized the tag as `data-screen-chain="1"` and restored it after SVG
  parsing. Ordinary SVG strokes remain untagged, preserving the rule that the
  converter never joins unrelated artwork across blank paper.
- CMYK passes now propagate the **Keep pen down** gap into
  `Settings.screen_chain_gap_mm`.
- After the existing contour planner chooses order and direction, a transition
  bridge compares the actual coordinated X/Y/A draw connector with lift,
  travel, and lower time. It keeps the pen down only when drawing is faster.
- The bridge decision is shared by G-code emission and preview timing, so the
  displayed time and saved program describe the same strokes.
- The set manifest records `planner_order: true` and the connector-versus-lift
  cost model.

## Verification

- `python -m unittest discover -s software\tests -v`: 680 tests passed with one
  expected OpenGL-context skip.
- Dedicated tests verify same-ink chaining, gap rejection, unchanged Xθ/Yθ
  planner order, cost rejection when lift/travel is cheaper, SVG tag round-trip,
  pen-offset tag preservation, rotating-connector subdivision, preview time
  reduction, and preview/G-code agreement.
- Replaying the current Ben3 planner order through the new bridge decision
  predicts:

  | Ink | Current `M3` | Predicted `M3` | Bridges |
  |---|---:|---:|---:|
  | Black | 1,919 | 620 | 1,299 |
  | Cyan | 2,118 | 510 | 1,608 |
  | Magenta | 1,942 | 579 | 1,363 |
  | Yellow | 1,898 | 524 | 1,374 |

  These are projections from the existing emitted contour order, not
  regenerated files because the source `IMG_0514.JPG` is not in this
  repository.

## Struggles and rejected approaches

- Raising the gap alone would reduce pen-ups but draw longer arbitrary
  connectors and can visibly alter the image.
- Reordering contours separately for chaining would discard the established
  Xθ/Yθ cost model. The bridge therefore runs after that planner.
- Enabling bridging for all SVG strokes was rejected. It would repeat the
  2026-09-30 mandala defect by connecting unrelated line art across blank
  paper.
- Treating the large line count as the problem was rejected. Most blocks are
  segment subdivisions within a stroke; the real cost is the number of
  `M3`/`M5` transitions.

## Risks and follow-up

- Connectors up to the selected gap add same-ink ink wherever adjacent marks
  are joined. A physical comparison should check facial detail, local density,
  and colour balance before accepting the regenerated four-pass set.
- A closed contour, a gap larger than the configured limit, or a connector
  slower than lift/travel/lower still causes a pen-up.
- The predicted counts use the existing planner order. Regeneration is needed
  to produce the final files and confirm their actual `M3` count.

## Files

- `software/converter_core/geometry.py`: tagged screen contour and SVG
  round-trip.
- `software/converter_core/settings.py`: post-planner chain-gap setting and
  validation.
- `software/converter_core/cmyk.py`: serialize the screen-chain tag.
- `software/converter_core/gcode.py`: shared cost-aware bridge decision,
  emission, preview, and bridge statistics.
- `software/generator_tabs/cmyk_tab.py`: pass the existing **Keep pen down**
  gap into the planner and tag generated marks.
- `software/tests/test_screen_chaining.py`: focused regression coverage.
- `software/tests/test_cmyk_tab.py`: UI/manifest/tag propagation coverage.
- `software/README.md`: current chaining behavior.
- `docs/project/ROADMAP.md`: current implementation and pending bench status.
