---
id: WSW-20260607-001
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
status: verified
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - ui
  - threading
  - progress
  - elapsed-time
related:
  - docs/HANDOFF.md
---

# Preview Build Progress and Responsive Processing

## Summary

The Preview action now shows a percentage bar, current processing stage, and
elapsed time. Preview generation runs in a worker thread so the Windows UI
continues repainting instead of appearing frozen.

## Reason

Large SVG and fill-planning jobs previously ran synchronously on the GUI thread.
After pressing Preview, the user could not distinguish active processing from
a stalled application or estimate how far the operation had progressed.

## Implementation

- Added a `PreviewWorker` using `QThread`.
- Reports coarse, real processing stages: SVG parsing, motion planning, bed
  clipping, and OpenGL preparation.
- Displays progress percentage and live elapsed time below the Preview controls.
- Disables Preview and Save G-code while preview data and the shared geometry
  cache are being built.
- Prevents the window from closing while a preview worker is active.
- Restores controls after success or failure and reports the final command count.

The percentages represent stage completion rather than a per-contour estimate.
This avoids displaying false precision for algorithms whose cost varies
substantially with SVG structure and selected fill pattern.

## Verification

- `python -m py_compile software\qt_svg_to_gcode.pyw`
- `git diff --check`
- Offscreen PySide6 integration run using `samples/svg/sample.svg`.
- Result: preview reached 100%, generated 527 commands, restored Preview and
  Save controls, and reported `Preview ready: 527 commands.`
- A delayed geometry-load run confirmed that elapsed time and the active
  `Parsing SVG geometry` stage update while processing is in progress.

## Struggles and rejected approaches

- The first progress-bar attribute reused the existing `preview_progress` name,
  which stores playback position as a float. The integration test caught the
  collision; the widget was renamed `preview_build_bar`.
- Geometry parsing previously appended directly to the Qt log. That cross-thread
  UI write was removed because widgets must only be changed from the GUI thread.
- A decorative indeterminate spinner was rejected because it would not answer
  which processing stage is active.

## Risks and follow-up

- Progress is intentionally stage-based, so a complex planning stage can remain
  at one percentage for most of the runtime.
- Cancellation is not implemented. Closing is blocked until the current worker
  finishes to avoid destroying Qt objects during active processing.
- If users need finer progress later, the geometry and planner APIs should gain
  callback-based item counts rather than estimating progress in the UI layer.

## Files

- `software/qt_svg_to_gcode.pyw`: worker lifecycle, progress UI, elapsed timer,
  control locking, and preview installation.
- `software/README.md`: user-facing preview behavior.
- `docs/HANDOFF.md`: current Qt UI behavior and implementation caveats.
