---
id: WSW-20260930-022
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
tags:
  - pen
  - interface
  - gcode
related:
  - WSW-20260930-021
  - software/README.md
---

# Pen tip diameter for the installed Pigma Micron 005

## Summary

The machine plots with a Sakura Pigma Micron 005, whose tip is 0.20 mm; the
converter had been assuming 0.30 mm. The default is now 0.20 mm, the
Kaleidoscope Converter has a `Pen tip diameter` field of its own (it previously
used the default silently), the value is remembered with the rest of the setup,
and every saved program records it in the header.

## Reason

"in kaleidoscope i dont see an option for pen tip diameter like we had in
converter", followed by "im using a 005 pigma micron". The value matters in
three places: pen-width compensation for imported SVG artwork, the gap fill
bridging tolerates (`pen x 6`), and ink reporting. At 0.20 mm vs 0.30 mm the
compensation error was 0.10 mm of artwork size - small, but it is the kind of
systematic offset the project is trying to eliminate.

## Implementation

- `converter_core/settings.py`: `pen_diameter_mm` default 0.30 becomes 0.20,
  with the pen named in a comment, and the UI spec default follows.
- `qt_kaleidoscope.pyw`: new `Pen tip diameter` spin box (0-5 mm, 0.05 mm
  steps, two decimals) in the Output group, initialised from the shared
  default, passed through `output_settings()` into the planner, and saved with
  the other remembered numbers. Its tooltip says what it does and does not
  affect.
- `converter_core/gcode.py`: the header line now also records the pen width,
  e.g. `(feed 700.0 mm/min, travel 3000.0 mm/min, tolerance 0.250 mm, pen
  0.20 mm)`.
- `docs/hardware/BOM.md`: the Micron 005 is listed as toolhead hardware with
  the note to keep the converter value in step with the fitted pen.
- `software/tests/test_pen_width.py` (new): the default is 0.20 mm, pen-width
  compensation shrinks a 100 mm square by exactly the tip width for 0.20/0.30/
  0.50 mm, compensation can be switched off, and the header records the width.

## Verification

- `python software\tests\test_pen_width.py` passes all four tests.
- Kaleidoscope window check: the spin box reads 0.20 mm, `settings.pen_diameter_mm`
  is 0.20, and the emitted header reads
  `(feed 700.0 mm/min, travel 3000.0 mm/min, tolerance 0.250 mm, pen 0.20 mm)`.
- All twelve test modules pass; `docs_index --write/--check` pass.

## Struggles and rejected approaches

- Adding the field to the kaleidoscope app without changing the default was
  rejected: the operator's pen is a known, fixed 0.20 mm tip, so the shared
  default should describe the real machine.
- Changing the core default without adding the field was rejected for the same
  reason in reverse - the value has to be visible where it is used.

## Risks and follow-up

- Swapping to a different tip size (01 = 0.25 mm, 03 = 0.35 mm) needs the field
  and the BOM updated together; nothing detects the pen automatically.
- Fill spacing is still 0 by default, so the bridging tolerance remains inert
  until fills are switched on.

## Files

- `software/converter_core/settings.py`, `software/converter_core/gcode.py`.
- `software/qt_kaleidoscope.pyw`: the field, its plumbing and its persistence.
- `software/tests/test_pen_width.py`, `software/tests/test_theta_feed.py`.
- `docs/hardware/BOM.md`, `software/README.md`,
  `docs/project/ENGINEERING_LOG.md`.
