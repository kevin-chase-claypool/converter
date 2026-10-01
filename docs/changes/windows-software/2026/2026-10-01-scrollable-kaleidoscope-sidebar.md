---
id: WSW-20261001-005
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_kaleidoscope.pyw
tags:
  - kaleidoscope
  - interface
  - usability
related:
  - WSW-20261001-003
  - software/README.md
---

# The kaleidoscope control column scrolls instead of running off the window

## Summary

The left-hand column of the kaleidoscope app - `Source`, `Kaleidoscope`,
`Printable bounds` and `Output` - is taller than the window once every group is
open, and the build and save buttons were pushed past the bottom edge. The
column now lives in a scroll area: the window can be any height, the rows keep
their width, and scrolling reaches `Build preview` and `Save G-code...`. Only
the vertical bar appears; the sidebar is never narrower than its own minimum
width, so nothing is clipped horizontally.

## Reason

Operator, over a screenshot of the column running past the bottom of the
window: "this is getting very crowded, make it scrollable."

## Implementation

- `software/qt_kaleidoscope.pyw`:
  - The four control groups, which were added straight into the central layout,
    are now wrapped in a `QScrollArea` stored as `self.sidebar`, with
    `setWidgetResizable(True)` so the rows stay as wide as the viewport. This is
    the same pattern the main converter's sidebar has used since it grew past
    one screen.
  - The scroll area's minimum width is the panel's own minimum size hint plus
    one scrollbar extent, which is what keeps the horizontal bar from appearing
    next to the vertical one when the vertical bar takes its share of the
    viewport.
  - The column keeps its natural width and the preview keeps the rest, so the
    bed view is unchanged in size.
- `software/tests/test_preview_view.py`: new `SidebarScrollTests`.
- `software/README.md`: the kaleidoscope section describes the scrolling
  control column.

## Verification

- `SidebarScrollTests` builds the real window at 1100x420, asserts that the
  four groups sit inside a widget-resizable `QScrollArea`, that a short window
  has a non-zero vertical range, and that after scrolling to the bottom both
  `Build preview` and `Save G-code...` are fully inside the viewport.
- Offscreen renders of the window at 1100x720 and 1200x560: the column keeps its
  width, the vertical range is 0-513 and 0-673 respectively, the horizontal
  range is 0-0, and the buttons at the bottom of the column are reachable by
  scrolling.
- All thirteen `software/tests` modules pass (133 tests before this change,
  135 with the two new ones).
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Making the groups collapsible (as the main converter's sidebar does) was
  rejected for now: it hides controls behind a second interaction, while
  scrolling keeps every control exactly where it was and only changes how the
  overflow is reached.
- A fixed minimum width taken from the style's scrollbar metric was two pixels
  short of the viewport once the vertical bar appeared, which left a permanent
  horizontal scrollbar with a 0-2 range. Using the vertical bar's own size hint
  plus the frame width removes it.

## Risks and follow-up

- The column is still the tallest thing in the window, so the build and save
  buttons start below the fold on a short window. If that proves annoying on the
  plotter PC, the next step is a fixed footer holding those two buttons rather
  than more scrolling.
- The minimum width is sampled once at construction from
  `panel.minimumSizeHint()`. Labels whose text can grow at runtime
  (`Motif folder...`, the bounds note) all have word wrap, so they cannot widen
  the panel past it.

## Files

- `software/qt_kaleidoscope.pyw`: `self.sidebar`, the scroll-area minimum width.
- `software/tests/test_preview_view.py`: `SidebarScrollTests`.
- `software/README.md`: the control-column entry.
- `docs/project/ENGINEERING_LOG.md`: this session's entry.
