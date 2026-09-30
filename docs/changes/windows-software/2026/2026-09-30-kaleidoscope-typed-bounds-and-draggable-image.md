---
id: WSW-20260930-005
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - bounds
  - dragging
  - interface
related:
  - WSW-20260930-004
  - software/README.md
---

# Kaleidoscope: typed printable bounds and a draggable image

## Summary

The Kaleidoscope Converter now takes the printable bounds as typed numbers
(`Bed diameter`, `Bed margin`, `Gantry reach radius`) plus a typed `Fit radius`,
offers `Fit design to bounds` and an auto-fit option, and lets the source image
be dragged inside a *fixed* design frame: the wedge, the design bound and the
machine limits stay where they are and only the image moves.

## Reason

The operator asked for three things: fit the design to the printable bounds that
were already measured, be able to type those numbers rather than accept a
built-in constant, and move the image within its division without moving the
kaleidoscope or changing its bounds.

## Implementation

- `converter_core/kaleidoscope.py`:
  - `clip_to_wedge` and `kaleidoscope` take an optional `radius`, which trims the
    design to a disc. That disc is the fixed frame: the design can never grow
    past it, so dragging the image cannot move the bounds.
  - Closed loops are now opened at a boundary crossing before half-plane
    clipping. The previous version dropped the piece that wrapped around the
    start point, so dragging an image whose loop started outside the wedge could
    empty the design.
  - Degenerate clipped pieces (zero-length) are dropped, and the boundary
    bisection returns the bracket midpoint instead of whichever end happened to
    be "kept", which removes a hair-outside point at the wedge edge.
- `qt_kaleidoscope.pyw`:
  - New **Printable bounds** group with typed bed diameter, bed margin and reach
    radius, a typed `Fit radius`, `Fit design to bounds`, an auto-fit option and
    a note showing what the bed and the reach each allow.
  - `Image offset X/Y` is expressed in millimetres of the finished design and is
    applied after normalisation, so it maps one-to-one to a preview drag.
  - The preview emits drag deltas; the window moves the offsets by that delta
    and rebuilds without re-fitting, so the frame is untouched.
  - Fit is two-pass: build without the radius clip to measure the design's
    natural extent, scale `Source size` so it matches the fit radius, then
    rebuild with the clip in place.

## Verification

- New tests: a 200 mm bar trimmed into a 120 mm frame never exceeds it, and a
  closed loop that starts outside the wedge keeps both boundary crossings
  (the wrap-around regression). All nine test modules pass.
- Headless Qt run: with `Fit radius` 180 the design clips to exactly 180.0 mm;
  dragging by (-60, +25) moves the offset to (-60, +25) and keeps the design at
  117.7 mm inside the same 180 mm frame; typing `Fit radius` 140 and pressing
  fit gives a design clipped at exactly 140.0 mm.
- `python tools\docs_index.py --write/--check` pass.

## Struggles and rejected approaches

- Applying the offset by moving the *apex* (the old `Apex offset` fields) was
  rejected: it changed the sampled wedge in source units, which is not what a
  drag should mean and made the numbers hard to reason about.
- Re-fitting on every drag was rejected: the operator wants the frame fixed and
  the image to move, so a drag rebuilds without re-fitting and the clip trims
  whatever leaves the frame.

## Risks and follow-up

- A drag can move the image so far that the wedge samples nothing; the design
  goes empty with only the preview and log to say so. An explicit warning is
  recorded as roadmap follow-up.
- The typed bounds are preview and planning inputs; the planner still enforces
  the real printable limit on the saved program, so a deliberately larger typed
  bound is clipped with a log line rather than honoured.

## Files

- `software/converter_core/kaleidoscope.py`: radius frame, closed-loop clipping,
  degenerate-piece filtering.
- `software/qt_kaleidoscope.pyw`: bounds group, fit radius, drag handling.
- `software/tests/test_kaleidoscope.py`: radius and wrap-around tests.
- `software/README.md`, `docs/project/ROADMAP.md`,
  `docs/project/ENGINEERING_LOG.md`: current state and follow-ups.
