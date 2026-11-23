---
id: WSW-20261123-013
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - user-interface
  - layout
  - preview
  - ink-simulation
  - settings
related:
  - WSW-20261006-011
  - WSW-20261007-006
  - WSW-20261007-022
---

# Auto-size the settings pane and set preview defaults

## Summary

The host converter now opens with the settings column wide enough for its
visible controls, grows that column when a wider settings group is opened, and
does not show a horizontal scrollbar for those controls. **Ink simulation
(multiply)** starts checked. **Red motion lines** starts unchecked.

## Reason

The settings controls required about 610 px, but the preview's bottom strip put
every checkbox and fit action in one horizontal row. That row required about
974 px, so the splitter could not give the settings column enough width without
being dragged at every launch. The operator also requested the CMYK overprint
simulation as the normal preview and wanted the machine-path overlay out of the
way by default.

## Implementation

- The preview checkbox and fit/profile actions now occupy two rows, reducing
  the preview's minimum width without hiding any control.
- The main window measures the visible sidebar content plus its scrollbar,
  grows the settings pane to that width after the window opens, and repeats the
  adjustment when a collapsible settings group is opened. It only grows the
  pane, so a manual splitter choice is not undone by collapsing a group.
- Motion lines start off in the OpenGL preview, sidebar checkbox, preview
  checkbox, and View menu. Ink simulation starts on in the OpenGL preview and
  its preview checkbox.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  passes `41` tests with one expected OpenGL-context skip.
- `python -m unittest discover -s software\tests` passes `658` tests with the
  same expected skip.
- Offscreen at `1500 x 950`, the initial split is `626 / 858`, the sidebar
  horizontal-scroll maximum is `0`, and the preview minimum width is `542`.
- Opening **Theta kinematics** grows the split to `764 / 720` and still leaves
  the horizontal-scroll maximum at `0`.
- An offscreen screenshot confirms both preview-default checkboxes have the
  requested state and the settings controls remain visible.

## Struggles and rejected approaches

Widening only the sidebar was insufficient: the one-row preview strip held the
splitter at about 510 px of settings width even at a 1500 px window. Shrinking
or hiding the preview controls was rejected because each remains useful.

## Risks and follow-up

The automatic fit grows the pane as wider groups open but does not shrink it
again, so the operator keeps control of the splitter after it has made room.
Small windows can still use the horizontal sidebar scrollbar when the total
width cannot contain both the visible controls and the preview floor.

## Files

- `software/qt_svg_to_gcode.pyw`: pane fitting, preview layout, and defaults.
- `software/tests/test_generator_tabs.py`: default and automatic-width
  regressions.
- `software/README.md`: current UI behavior.
