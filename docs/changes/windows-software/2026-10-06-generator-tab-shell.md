---
id: WSW-20261006-001
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
  - generators
  - converter
related:
  - docs/research/2026-10-06-r-plotterart-svg-generators.md
---

# Generator tab shell in the main converter window

## Summary

The main converter window now hosts a tab bar. The existing conversion
workspace is the first tab, **Convert**, and each generator integration added
under `software/generator_tabs/` appears as its own tab. This is the UI
foundation for the permissively licensed r/plotterart generator survey; no
second application or launcher is created.

## Reason

The 2026-10-06 survey identified generator features worth bringing into the
app, and the project owner required each generator to get its own tab with no
duplicated features. The existing window had no tab host, so the shell had to
exist before generator tabs could be added in parallel and merged.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `build_ui` wraps the existing root widget in
  a `QTabWidget` and adds it as the **Convert** tab; `load_generator_tabs`
  discovers `software/generator_tabs/*_tab.py` modules and adds one tab each.
  `use_svg(path, preview=False)` is the single entry point that loads a
  generator's SVG into the Convert tab; `generator_status` writes the status
  line. A tab that fails to import or construct is logged and skipped.
- `software/generator_tabs/__init__.py`: the discovery loader and the tab
  contract.
- `software/generator_tabs/README.md`: the contract, host entry points, and
  third-party attribution rules.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  passes both shell tests: Convert is the first tab, and `use_svg` refuses a
  missing output path instead of loading it.
- Generator tabs themselves are verified by their own change notes.

## Struggles and rejected approaches

- A second launcher (`converter2.bat`) and a duplicated GUI were rejected:
  the owner asked for tabs only if a new UI was necessary, and the existing
  three-pane window already carries the preview and G-code pipeline, so the
  tab host is an additive shell instead.
- Registering each generator by editing a shared import list was rejected
  because parallel generator work would conflict on the same file; the
  auto-discovering `*_tab.py` contract keeps each tab additive.

## Risks and follow-up

- The generator tab bar adds a small amount of vertical chrome above the
  existing layout; the window was already sized 1500x950.
- `software/generator_tabs/` importing a module happens on the UI thread
  during startup; heavy generator imports should stay lazy inside the tab.
- The next three generator tabs (flow field, line draw, 3D wireframe) are
  tracked in `docs/project/ROADMAP.md`.

## Files

- `software/qt_svg_to_gcode.pyw`: tab host, discovery call, and the
  `use_svg` / `generator_status` host entry points.
- `software/generator_tabs/__init__.py`: tab discovery and error isolation.
- `software/generator_tabs/README.md`: author contract.
- `software/tests/test_generator_tabs.py`: shell regression tests.
- `software/README.md`: user-facing description of the tab bar.
