---
id: WSW-20261024-008
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
tags:
  - artwork
  - placement
  - restart
  - reimport
  - cmyk
related:
  - WSW-20261024-007
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Preserve artwork placement across reopen and reimport

## Summary

The converter now saves each artwork's X/Y placement beside the source file
and restores it when that same file is imported again. Closing and reopening
the application no longer silently returns a placed image to the bed centre.

## Reason

Dragging artwork in the preview updates the two `Artwork offset` fields, but
the application previously kept those values only in the running process.
After a converter restart, reimporting the source reset both fields to zero.
This interrupted the CMYK regeneration workflow because the placed image no
longer occupied the same bed-space location.

The placement for `IMG_0514.JPG` was recovered from the existing yellow
G-code and its temporary layer SVG. The matching first contour gives
`X=19.81 mm`, `Y=-29.65 mm`.

## Implementation

- Placement is stored in `<artwork-file>.theta-layout.json` beside the source.
- Selecting or adopting a file restores its saved X/Y placement.
- Preview dragging schedules an atomic sidecar save after 250 ms.
- Editing either offset or closing the application also saves the current
  placement.
- A Fit operation intentionally resets placement to zero and updates the
  sidecar.
- Missing, unreadable, or invalid sidecars leave the normal zero placement
  unchanged and report the problem in the converter log.

## Verification

- Added a regression that saves `X=19.81`, `Y=-29.65`, reopens the
  application, restores the sidecar, and confirms both fields and the preview
  retain those values.
- `python -m unittest -v software.tests.test_generator_tabs`: 39 tests pass
  with one expected OpenGL-context skip.
- Full converter discovery passes 506 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Asking the operator to re-place the image by eye is not reproducible.
- Global application settings would apply one placement to every artwork and
  would make test and project state leak together.
- Rewriting the existing G-code was rejected because it would not preserve a
  reproducible placement for the next regeneration.

## Risks and follow-up

- The source directory must be writable. If the sidecar cannot be saved, the
  converter logs the failure and G-code remains otherwise unaffected.
- This change persists artwork X/Y placement, not every generator control.
  CMYK page, scale, pitch, and screening settings still need their current
  values when generating a new set.

## Files

- `software/qt_svg_to_gcode.pyw`: sidecar save/restore and import hooks.
- `software/tests/test_generator_tabs.py`: reopen/reimport regression.
- `software/README.md`: placement persistence behavior.
- `docs/project/ENGINEERING_LOG.md`: session evidence and recovered placement.
