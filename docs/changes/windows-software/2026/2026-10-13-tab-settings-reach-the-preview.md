---
id: WSW-20261013-006
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - preview
  - pen-width
  - tolerance
related:
  - WSW-20261013-004
---

# Generator tab settings now reach the preview

## Summary

The preview, the motion analysis and the saved files now share one settings
object per tab. The CMYK tab's **Pen width** and **Path tolerance** override
the host values for all three, instead of only for the saved programs.

## Reason

Operator report (2026-10-13): "the pen width preview doesnt show the actual
width that i set. this is also affecting the preview". Root cause: the preview
path called `settings_for_source(tab)` directly, which applied only the
generic generator overrides (manual fit, scale 1.0, hatch off). The CMYK tab's
own overrides were applied later, on the save/analysis path only - so the ink
simulation drew the Geometry group's pen stroke (or its 0.3 mm default) rather
than the tab's 0.5/1.4 mm field, and the preview's planning used the host
tolerance rather than the tab's Path tolerance.

## Implementation

- `qt_svg_to_gcode.pyw`: `settings_for_source()` calls an optional
  `apply_tab_settings(settings)` hook on generator tabs after the generic
  overrides.
- `cmyk_tab.py`: implements `apply_tab_settings` returning
  `dataclasses.replace(settings, tolerance=..., pen_diameter_mm=...)`;
  `_effective_settings()` reuses it for the save/analysis path.

Result: `settings.pen_diameter_mm` matches the tab's Pen width wherever the
preview's ink simulation reads it, and `settings.tolerance` matches Path
tolerance for the subdivision used by the preview and by the emitted files.

## Verification

- `py_compile` clean for both files; 88 tests pass in `test_cmyk_tab` and
  `test_generator_tabs`.
- Bench check: with Ink simulation enabled, changing Pen width 0.5 -> 1.4
  should visibly change stroke width in the preview, and the preambles of
  saved layers should carry the same tolerance the preview planned with.

## Struggles and rejected approaches

Considered having the preview call `_effective_settings()` on the tab;
rejected because it duplicates the host's generator overrides and inverts the
ownership - the hook keeps one source of truth in the host.

## Risks and follow-up

- Normal (non-ink-simulation) preview still draws thin centre lines by design;
  the ink-simulation toggle is the view that shows real widths. If a
  width-accurate view is wanted by default, that is a separate preview design
  change.

## Files

- `software/qt_svg_to_gcode.pyw`: settings hook.
- `software/generator_tabs/cmyk_tab.py`: hook implementation.
- `docs/project/ENGINEERING_LOG.md`: session entry.
