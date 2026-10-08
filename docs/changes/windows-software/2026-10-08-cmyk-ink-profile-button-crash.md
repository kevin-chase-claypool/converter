---
id: WSW-20261008-013
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
tags:
  - cmyk
  - preview
  - crash
  - ink-profile
related:
  - WSW-20261007-007
---

# Ink profile button no longer kills the app

## Summary

Pressing **Ink profile...** took the application down instead of opening a
file picker. The button was wired straight to `load_ink_profile(path=None)`,
and Qt hands a clicked slot its `checked` flag - so `path` arrived as
`False`, the dialog was skipped, and the loader read file descriptor 0
instead of a profile. The button now uses a dedicated `choose_ink_profile`
slot that ignores the flag, and `load_ink_profile` refuses any argument that
is not a path.

## Reason

Owner report: "the ink profile... button crashes the app". The last line of
`software/qt_debug.log` is Python's warning for exactly that call:
`qt_svg_to_gcode.pyw:4014: RuntimeWarning: bool is used as a file descriptor`
followed by `with open(path, "r", encoding="utf-8") as handle:`.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the button connects to
  `choose_ink_profile(_checked=False)`, which opens the picker and calls
  `load_ink_profile(path)`. The loader now raises `TypeError` for non-path
  arguments, so a future signal mis-wiring is visible instead of fatal.

## Verification

- `open(False, "r", encoding="utf-8")` was checked on this Python 3.13.13
  under both `python` and `pythonw`: it opens file descriptor 0 with the
  RuntimeWarning instead of raising, so the press never reached a profile
  file - the app log ends with that warning at the moment of the press. The
  exact way the Qt process then went down could not be reproduced outside
  the app.
- `python -m unittest discover -s software\tests -p "test_*.py"`: 399 tests
  pass, 1 skipped (the pre-existing headless shader compile). The new test
  clicks the real button with a stubbed `QFileDialog` and asserts the
  measured colours reach `gl_preview.sim_ink_colors`, and that
  `load_ink_profile(False)` raises instead of opening fd 0.

## Struggles and rejected approaches

- The profile JSON path was inspected first; the trailing RuntimeWarning in
  the app log pointed at the slot signature instead. Keeping the dialog
  inside `load_ink_profile` and sniffing a bool argument was rejected: the
  signal flag should never be able to look like a path.

## Risks and follow-up

- The other preview buttons (`Fit inside`, `Fill bed`, `Play`, `Pause`,
  `Preview`, `Cancel`) take no positional arguments, so they cannot hit the
  same trap.

## Files

- `software/qt_svg_to_gcode.pyw`: split the picker out of the loader; guard
  the loader.
- `software/tests/test_generator_tabs.py`: button-click regression test.
