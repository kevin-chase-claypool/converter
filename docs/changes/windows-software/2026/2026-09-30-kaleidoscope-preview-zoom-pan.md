---
id: WSW-20260930-012
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - preview
  - interface
related:
  - WSW-20260930-011
  - software/README.md
---

# Kaleidoscope: zoom and pan the preview like the main converter

## Summary

The Kaleidoscope Converter's preview now has a camera. The wheel zooms about the
cursor from 10 % to 2000 %, `Shift`-drag or middle/right-drag pans, and
`+` / `-` / `Reset view` buttons with `Ctrl` `+` / `-` / `0` do the same from
the keyboard. A plain drag still moves the image inside the fixed frame, and
that drag is scaled by the zoom so it stays accurate when zoomed in. The zoom
level is shown next to the buttons and in the preview's status line.

## Reason

The operator asked to "be able to zoom and pan like i could in converter". The
main converter's preview already zooms with the wheel (0.1-20x), pans on
Shift/middle/right drag and resets with a button; the kaleidoscope preview had
none of that.

## Implementation

- `qt_kaleidoscope.pyw`, `DesignPreview`:
  - Keeps a camera: `zoom` (0.1-20) and `pan` in design millimetres, with
    `to_screen` / `to_design` / `screen_delta_to_mm` helpers. Painting, the bed
    and reach circles, the fit-bound circle, the wedge lines and the design all
    go through the same transform, so the whole scene zooms together.
  - `wheelEvent` zooms by 1.15 per notch and anchors the zoom on the cursor by
    re-deriving `pan` from the design point that was under the pointer, so the
    detail you are pointing at stays put.
  - `mousePressEvent` keeps the existing plain-drag-moves-the-image behaviour
    and routes `Shift`, middle and right drags to panning; `mouseMoveEvent`
    converts an image drag through the current zoom.
  - `zoom_in` / `zoom_out` / `reset_view` / `set_zoom` plus a `viewChanged`
    signal drive the on-screen controls.
  - The preview draws faint origin axes and a status line with the zoom
    percentage and the gestures.
- `KaleidoscopeWindow` gained a **Preview view** row (`-`, `+`, `Reset view`,
  zoom label), `Ctrl` `+` / `-` / `0` shortcuts, and a startup hint in the log.

## Verification

- New `software/tests/test_preview_view.py` (7 tests, skipped when PySide6 is
  absent): screen/design round trip at three zoom and pan combinations, a zoom
  that keeps the design point under the cursor, clamping to 0.1-20x, image
  drags shrinking in millimetres as the view zooms, panning following the drag,
  `reset_view` returning to the whole bed, and `viewChanged` emissions.
- All eleven test modules pass.
- Headless window run: round trip exact to 1e-6 at 4x; an anchored 4x zoom keeps
  (-114.956897, 162.171336) fixed under the pointer; a 100 px drag is 25.7 mm at
  4x against 102.6 mm at 1x; the zoom label reads 400 %; reset returns to 100 %
  and pan (0, 0). Render checked at 6x in `samples/png/preview_zoom.png`.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Making the wheel zoom about the view centre (as the main app does) was
  rejected in favour of anchoring on the cursor: both are one line different,
  and anchoring is what makes zooming to inspect a seam useful.
- Rebinding plain left-drag to panning was rejected: the operator previously
  asked for a plain drag to move the image inside the divisions, so panning
  takes the modifier and the extra mouse buttons instead.

## Risks and follow-up

- There is no on-screen zoom slider or keyboard focus hint; the buttons, the
  wheel and the shortcuts are the documented paths.
- Zooming is view-only. Saved G-code is unaffected by the camera, which is
  intended but worth remembering when checking a design against the bed.

## Files

- `software/qt_kaleidoscope.pyw`: camera state, wheel/pan/drag handling, view
  controls and shortcuts.
- `software/tests/test_preview_view.py`: view transform tests.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
