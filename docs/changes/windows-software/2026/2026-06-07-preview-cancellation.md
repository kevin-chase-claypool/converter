---
id: WSW-20260607-005
date: 2026-06-07
category: windows-software
affected_categories:
  - windows-software
status: verified
components:
  - software/qt_svg_to_gcode.pyw
  - software/converter_core/cancellation.py
  - software/converter_core/geometry.py
  - software/converter_core/kinematics.py
  - software/converter_core/gcode.py
tags:
  - preview
  - cancellation
  - threading
  - safety
related:
  - WSW-20260607-001
---

# Preview Cancellation

## Summary

Preview generation can now be cancelled while SVG geometry, fill patterns,
motion planning, clipping, or preview moves are being generated.

## Reason

Large files normally require substantial processing, but an accidentally tiny
fill spacing or other unreasonable setting can create an unexpectedly long
job. Previously the user had to wait, force-close the application, or risk an
out-of-memory failure.

## Implementation

- Added a Cancel button beside Preview that is enabled only while generation is
  active.
- Added a thread-safe cancellation event to `PreviewWorker`.
- Added a dedicated `OperationCancelled` exception and cooperative checkpoints
  throughout SVG parsing, dense vector and raster fills, contour ordering,
  theta planning, bed clipping, and preview move emission.
- Cancellation unwinds the worker normally instead of forcibly terminating the
  thread.
- The most recent completed preview remains installed after cancellation.
- Geometry-cache updates are transactional: newly generated contours and their
  key are installed only after the entire build completes.
- Closing the window during generation requests cancellation and asks the user
  to close again after the worker has finished.

## Verification

- Compiled the Qt app and all changed converter-core modules.
- Core cancellation test interrupted dense gyroid geometry generation.
- Core cancellation test interrupted planning of a 5,000-point contour.
- Offscreen Qt integration test built the sample's 527-command preview, started
  a second delayed preview, cancelled it, restored all controls, and confirmed
  the prior preview remained unchanged.
- Cache-integrity testing confirmed a cancelled build with changed settings
  leaves the prior contour cache and cache key intact.
- `git diff --check`
- `python tools\docs_index.py --check`

## Struggles and rejected approaches

- Forced `QThread` termination was rejected because it can leave Python, Qt,
  OpenGL, or geometry-cache state inconsistent.
- Cancelling only at stage boundaries was rejected because unreasonable fill
  settings can spend most of their runtime inside one nested generation loop.

## Risks and follow-up

- Cancellation is cooperative, so completion depends on reaching a checkpoint.
  Checkpoints cover the known expensive loops, but a single external Qt render
  or XML parse call cannot be interrupted mid-call.
- Save G-code remains synchronous and does not yet expose cancellation. This
  change is scoped to Preview.

## Files

- `software/qt_svg_to_gcode.pyw`: Cancel button, worker event, status handling,
  and raster/fallback checkpoints.
- `software/converter_core/cancellation.py`: shared cancellation contract.
- `software/converter_core/geometry.py`: SVG, fill, and clipping checkpoints.
- `software/converter_core/kinematics.py`: ordering and theta checkpoints.
- `software/converter_core/gcode.py`: preview move checkpoints.
