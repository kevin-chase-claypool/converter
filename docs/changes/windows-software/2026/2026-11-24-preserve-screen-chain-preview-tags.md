---
id: WSW-20261124-002
date: 2026-11-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/tests/test_screen_chaining.py
tags:
  - cmyk
  - preview
  - pen-up
  - screen-trail
  - ink-trail
  - metadata
related:
  - WSW-20261124-001
---

# Preserve screen-chain tags in the CMYK preview

## Summary

CMYK preview contours now keep their `ScreenTrail` eligibility when they are
tagged for ink colour. Preview bridges retain the originating ink's colour
rather than falling back to the single-colour renderer. The preview M3 count
and time estimate include the same post-planner keep-down bridges as the saved
G-code.

## Reason

Save-time planning parsed the generated layer SVG directly and kept the
`ScreenTrail` type, so the Ben3 yellow G-code dropped from `1,898` to `456`
`M3` commands. Preview planning then called `tag_ink()`, which converted every
contour to a plain `InkTrail`; that discarded the screen-chain tag. The UI
therefore still reported pre-bridge counts and time, making the successful file
optimization appear to have done nothing.

The GPU preview also deliberately returned `(None, None)` from
`ink_vertex_colors()` whenever any keep-down bridge was present. Once the
preview tag was preserved, that fallback rendered every plate with the default
blue colour instead of the four process inks.

## Implementation

`tag_ink()` now copies a tagged contour as its original subtype, preserves its
attributes, and adds `ink`. Plain lists still become `InkTrail` for the colour
renderer. `ScreenTrail` therefore reaches preview planning unchanged, while the
preview still knows which ink should be drawn.

Per-ink vertex colours now include bridge moves using the bridge's contour
index, so a connector is rendered in the same ink as the lines it joins.

## Verification

- A focused regression asserts that `tag_ink(ScreenTrail, "y")` returns a
  `ScreenTrail` carrying `ink="y"`.
- A renderer regression includes a `keep_down_bridge` draw move and verifies
  that its vertices receive the originating contour's cyan colour instead of
  falling back to the uniform preview colour.
- The existing screen-chain tests verify that preview planning emits
  keep-down bridges, reduces pen-cycle time, and matches emitted G-code.
- The complete converter suite passes 682 tests with one expected
  OpenGL-context skip.
- The saved Ben3 files were generated at 2026-11-24 10:53 and contain
  `540/565/564/456` `M3` commands for K/C/M/Y. Yellow contains 1,323
  `(keep-down bridge)` moves.
- The application must be restarted to load this source change, then Preview
  and Save must be run again so the displayed counts use the fixed preview
  path.

## Struggles and rejected approaches

- Regenerating the files was rejected as a fix because the save path was
  already using the bridge. Only the preview's tag propagation was wrong.
- Treating the raw block count as the primary metric was rejected. Each bridge
  replaces `M5 + travel + M3` with one or a few connector moves, so the
  multi-thousand-line reduction is smaller than the much larger reduction in
  pen cycles and dwell time.

## Risks and follow-up

- An already loaded ioSender file is not a refresh of the newly overwritten
  file; reopen the saved G-code after running Save again.
- Physical print time, connector ink, density, and colour balance remain
  unverified.

## Files

- `software/converter_core/cmyk.py`: preserve tagged contour subtypes when
  adding ink metadata.
- `software/qt_svg_to_gcode.pyw`: keep per-ink colour buffers when bridge
  moves are present.
- `software/tests/test_generator_tabs.py`: renderer regression for bridge ink.
- `software/tests/test_screen_chaining.py`: regression for preview tag
  preservation.
- `software/README.md`: current count and time-estimate behavior.
- `docs/project/ROADMAP.md`: current preview/save verification state.
