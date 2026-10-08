---
id: WSW-20261007-018
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/__init__.py
  - software/generator_tabs/README.md
  - software/tests/test_generator_tabs.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - preview
  - opengl
  - user-interface
related:
  - WSW-20261007-003
  - WSW-20261007-004
---

# Filter CMYK preview layers live instead of re-rendering

## Summary

The CMYK Preview checkboxes now apply immediately. Every ink layer is loaded
into the shared OpenGL preview once; unchecking an ink hides its artwork,
drawn path, and motion lines by zero-alpha filtering, with no re-screening
and no new G-code plan. Previously a checkbox change only took effect on the
next Preview press, which rebuilt the combined SVG, re-ran the r-theta
planner for the preview program, and restarted the background four-ink
planning - even though the screened layers were already cached.

The background planner also now skips when nothing but visibility changed:
`start_analysis` reuses a fresh analysis for the current control key.

## Reason

Owner: "is it not possible to uncheck and get an immediate removal of that
color (CMY or K) with respect to the preview? Why is it having to render the
entirety?" The per-ink screening was already cached, but the preview
pipeline conflated visibility with building a new program.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `GLPreview.set_visible_inks()` and a
  `visible_inks` set on `set_preview`; `ink_vertex_colors` gives hidden inks
  zero alpha; `rebuild_cache` filters travel, motion, and drawn-path
  segments so a hidden ink leaves nothing behind. New host hook
  `update_preview_visibility()` applies the active tab's checkbox set.
- `software/generator_tabs/cmyk_tab.py`: checkboxes notify the host on
  toggle; `preview_layers()` returns all four layers and
  `preview_visible_inks()` reports the checked set; `build_svg` writes all
  four layers so the preview plan covers every ink regardless of visibility;
  hiding every layer is now allowed (blank preview).
- `software/generator_tabs/README.md`, `__init__.py`: contract notes for the
  new optional hook.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 378
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  zero-alpha hiding in `ink_vertex_colors`, live GL filtering (artwork and
  drawn-path alphas), the host hook applying the previewed tab's set, all
  layers loading regardless of checkboxes, and the tab notifying the host on
  toggle.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Keeping the checkbox filter in `build_svg` (the old approach) was the
  root cause: any visibility change looked like a content change.
- Skipping planning on every Preview was rejected: the preview program
  still drives the progress slider and motion overlay; it is now planned
  once over all four inks and visibility is purely a drawing filter.

## Risks and follow-up

- The combined preview plan always contains all four inks, so the progress
  slider spans hidden inks' moves too; this is a display-only trade for
  instant toggling.
- The per-ink background planning still runs on the first Preview of a new
  control state (by design); repeats are skipped.

## Files

- `software/qt_svg_to_gcode.pyw`: live visibility filtering, host hook.
- `software/generator_tabs/cmyk_tab.py`: hooks and all-layer preview load.
- `software/generator_tabs/README.md`, `__init__.py`: contract.
- `software/tests/test_generator_tabs.py`, `test_cmyk_tab.py`: coverage.
