---
id: WSW-20261123-014
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
  - generator-tabs
  - cmyk
  - settings
related:
  - WSW-20261123-013
  - WSW-20261006-011
---

# Fit the active generator's settings column

## Summary

Switching to a generator tab now sizes the left settings column to that tab's
visible controls. The **CMYK** tab, whose Screen group needs about 850 px,
widens automatically instead of opening in a clipped column with a horizontal
scrollbar.

## Reason

The previous automatic width calculation only measured the Convert sidebar.
The app therefore opened correctly on Convert, but selecting **CMYK** kept the
old pane width. Its long checkbox labels and controls were cut off, forcing the
operator to drag the splitter wider.

## Implementation

- The width calculation now inspects the active stack page. Convert continues
  to use its collapsible sidebar; generator pages measure their own control
  widget plus the vertical scrollbar, frame, and page margins.
- Tool changes schedule the same one-shot pane fit used at startup. The pane
  still only grows, preserving an operator's wider splitter choice.
- CMYK's content now fits at `852 px`; the resulting left pane is `880 px`
  wide at the default unmaximized `1500 x 950` window.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  passes `42` tests with one expected OpenGL-context skip.
- `python -m unittest discover -s software\tests` passes `659` tests with the
  same expected skip.
- Offscreen at `1500 x 950`, switching from Convert to CMYK changes the split
  from `626 / 858` to `880 / 604`, the CMYK horizontal-scroll maximum is `0`,
  and the preview remains wider than its `542 px` minimum.
- An offscreen CMYK screenshot confirms the settings controls fill the widened
  left column without clipping.

## Struggles and rejected approaches

Applying the Convert sidebar width to every generator was insufficient because
their controls live in independent tab pages. Permanently making every tool as
wide as CMYK was rejected because it would unnecessarily reduce the preview on
the smaller generator tabs.

## Risks and follow-up

The pane only grows as tools change, so the preview keeps the narrower width
until the operator drags the splitter or restarts. A window too small to hold
both the active controls and the preview minimum still falls back to the
sidebar's horizontal scrollbar.

## Files

- `software/qt_svg_to_gcode.pyw`: active-tab width calculation and tool-switch
  fit.
- `software/tests/test_generator_tabs.py`: CMYK pane-width regression.
- `software/README.md`: current generator-column behavior.
