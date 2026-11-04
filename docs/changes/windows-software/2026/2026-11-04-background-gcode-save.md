---
id: WSW-20261104-001
date: 2026-11-04
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_background_save.py
tags:
  - converter
  - save
  - qt
  - ui-freeze
  - background-worker
  - exact-compensation
  - responsiveness
related:
  - WSW-20261023-007
---

# Generate and save G-code without freezing the converter

## Summary

The single-file **Save G-code** path now reads the active artwork, plans the
motion, applies exact bed compensation, subdivides the program, and writes the
file on a background worker. The Qt window remains responsive and shows the
current save stage, percentage, and elapsed time.

## Reason

An imported SVG that appeared to freeze the converter was still being processed
on the Qt GUI thread. On the active artwork and settings, reading took
`0.052 s`, planning took `0.161 s`, and exact compensated G-code generation
took `14.108 s`; the entire synchronous save path took `14.320 s` and wrote
`25,586` lines / `1,208,817` bytes. Windows therefore treated the window as
not responding even though the converter had not deadlocked.

Dense artwork can make that synchronous interval much longer, so the user
interface must not depend on generation finishing before it can repaint or
accept input.

## Implementation

- Added a `ConvertWorker` QObject with the same Qt thread lifecycle as the
  existing preview worker.
- The worker snapshots the active source path, output path, and settings on
  the GUI thread before starting.
- Parsing, exact planning, bed compensation, G-code subdivision, and file
  writing now run in the worker thread.
- The shared preview progress controls report **Reading artwork**,
  **Planning exact G-code**, and **Writing G-code** during saves.
- Preview and Save G-code cannot run concurrently. Closing cancels an active
  save and delays shutdown until the worker finishes.
- Save cancellation is checked around parsing, planning, and immediately
  before writing. A request observed by that final check leaves the output
  file untouched.

## Verification

- `py -3 -m unittest software.tests.test_background_save -v` passes. A
  deliberately slow exact-G-code generator leaves `convert()` able to return
  immediately; the worker later writes the complete test program. A second
  case runs the real background path and verifies the saved program carries
  the selected bed-compensation fingerprint.
- `py -3 -m unittest software.tests.test_generator_tabs -v` passes 40 tests
  with one expected OpenGL-context skip.
- `py -3 -m unittest discover -s software\tests` passes all `618` tests with
  the same one expected skip.
- `py -3 -m py_compile software\qt_svg_to_gcode.pyw` passes.

## Struggles and rejected approaches

The original implementation reran the complete exact save pipeline directly in
`MainWindow.convert()`. The existing preview worker reduced perceived delay but
did not protect the separate Save path. Leaving the operation synchronous and
only changing the status text would not have let Qt process input or repaint.

## Risks and follow-up

The current worker cannot interrupt inside the exact G-code emission loop; a
cancel request during that interval is honored only after generation returns.
The UI remains responsive, but the wait before cancellation completes is
proportional to the remaining generation time. Moving cancellation checks into
the emitter is a separate optimization that requires a focused core test.

## Files

- `software/qt_svg_to_gcode.pyw`: background save worker, lifecycle,
  progress, cancellation, and save/preview exclusion.
- `software/tests/test_background_save.py`: regression proving Save no longer
  blocks the GUI thread.
- `software/README.md`: current save progress and cancellation behavior.
