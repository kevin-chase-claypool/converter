---
id: WSW-20261006-021
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs
tags:
  - user-interface
  - navigation
related:
  - WSW-20261006-012
  - WSW-20261006-018
---

# Replace the tab bar with an All tools dashboard

## Summary

The top tab bar is gone. The window now has a compact navigation bar and an
**All tools** dashboard: a scrollable set of grouped cards (Core, Line art,
3D, Patterns, Text & layout), one card per tool. Opening a card shows that
tool's settings page; the navigation bar shows the tool name with an
**All tools** button to go back. Adding tools no longer widens anything.

## Reason

Ten tools already filled the top bar edge to edge, and the owner expected the
list to keep growing. A dashboard keeps the navigation constant-height and
makes every tool discoverable in one screen, without giving up the narrow
settings column plus full preview layout.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the `QTabBar`/tab host was replaced by the
  existing `QStackedWidget` plus index 0 = **All tools** dashboard and index 1
  = Convert. `build_dashboard()` renders one `QPushButton` card per tool,
  grouped in `QGroupBox` rows; `show_tool(title)` switches pages and updates
  the navigation bar; `tools_button` appears only away from the dashboard.
- Generator tab classes declare `GROUP` and `DESCRIPTION`; the loader records
  them with each page for the cards.
- Preview/Save semantics are unchanged: a generator page previews 1:1, the
  Convert page uses the Artwork row, and the dashboard refuses Preview/Save
  with "Open a tool... first".
- `software/tests/test_generator_tabs.py` was rewritten for the dashboard:
  default tool, navigation bar above the import row, tool order, card/back
  navigation, dashboard preview guard, per-tool scale, stale switching, and
  the static-chrome checks.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 16 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 265 tests
  pass.
- Offscreen renders at 1400x950: the dashboard shows the five groups with
  cards and no back button; a tool page shows the back button plus the tool
  name, the tool's controls, and the unchanged preview panel.

## Struggles and rejected approaches

- Keeping the tab bar with scroll arrows was rejected: it still grows and
  hides tools.
- A pure tree sidebar was deferred in favour of the card dashboard, which the
  owner chose; the dashboard is a stack page, so a tree can replace it later
  without touching the tool pages.

## Risks and follow-up

- The dashboard occupies the settings column while open; tool pages are one
  click away through the back button, and Ctrl+shortcut support is not added.

## Files

- `software/qt_svg_to_gcode.pyw`: dashboard, navigation bar, show_tool.
- `software/generator_tabs/*_tab.py`, `_tab_common.py`: GROUP/DESCRIPTION.
- `software/tests/test_generator_tabs.py`: dashboard navigation tests.
- `software/README.md`, `software/generator_tabs/README.md`: navigation docs.
