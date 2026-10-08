---
id: WSW-20261007-019
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - preview
  - user-interface
related:
  - WSW-20261007-018
  - WSW-20261007-004
---

# Show per-ink M3 counts in the preview data area

## Summary

For a CMYK preview the preview data area now shows the number of M3
(pen-down) commands per ink, e.g. `M3s (pen down): C: 123 M: 456 Y: 789
K: 987`. The counts come from the planned preview program: every
`pen_down` move is attributed to the ink of its contour, and the letters use
the CMYK channel names (K, not B). Other tools' previews are unchanged and
the line stays hidden for untagged artwork.

## Reason

Owner: "in the preview data section i want to know the number of M3's for
each of the colors C:# , M:#, Y:#, K:#". Pen cycles dominate CMYK plot
time, so the per-ink count is the number to watch.

## Implementation

- `software/qt_svg_to_gcode.pyw`: new `engage_counts` label in the preview
  panel; `MainWindow.ink_engage_summary(contours, moves)` counts `pen_down`
  moves per tagged ink (returns ``""`` for untagged artwork);
  `preview_ready` shows or hides the line.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 379
  tests (1 skipped: the pre-existing headless shader compile). The new test
  counts M3s across two tagged inks and checks the untagged case returns an
  empty summary.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Using the channel-label initial produced "B: n" for black; the summary now
  uses the CMYK channel letters (C, M, Y, K) as requested.

## Risks and follow-up

- The count reflects the planned preview program (all four inks); hiding a
  layer in the preview does not change the counts, because the saved files
  still contain every ink.

## Files

- `software/qt_svg_to_gcode.pyw`: summary label and counter.
- `software/tests/test_generator_tabs.py`: counter coverage.
- `software/README.md`: preview data note.
