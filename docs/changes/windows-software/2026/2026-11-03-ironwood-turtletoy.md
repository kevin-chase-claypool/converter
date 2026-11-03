---
id: WSW-20261103-001
date: 2026-11-03
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - samples/turtletoy/ironwood.js
  - samples/preview/ironwood.png
  - tools/render_turtletoy.js
  - software/tests/test_turtletoy_ironwood.py
tags:
  - generative-art
  - turtletoy
  - svg
  - plotter-art
  - woodcut
  - single-pen
related: []
---

# Add the Ironwood lumberjack Turtletoy sketch

## Summary

Added **Ironwood**, a self-contained Turtletoy woodcut scene that can be pasted
directly into `turtletoy.net/turtle/new`, plus a rendered preview and local
API-compatible execution harness.

## Reason

The project owner asked for a more masculine Turtletoy creation depicting a
lumberjack and his axe resting at a chopping block.

## Implementation

- `samples/turtletoy/ironwood.js` uses only the documented `Canvas`, `Turtle`,
  and `walk(i)` interfaces.
- A bearded, broad-shouldered lumberjack wears a knit cap and crosshatched
  flannel.
- His right hand rests on a long axe handle ending in a hatched steel head
  planted in an end-grain chopping block.
- Procedural pine silhouettes and a geometric rising-sun crown frame the
  portrait.
- Adjustable Turtletoy comments expose beard, shirt, and wood hatching density,
  the background tree count, and the deterministic scene seed.
- `tools/render_turtletoy.js` executes a Turtletoy sketch against a local mock
  of the public API and exports the captured strokes for preview/testing.

## Verification

- The sketch passes `node --check`.
- The Turtletoy-compatible runner produces `272` strokes and `1,734` points.
- The bounds are approximately `-95.8..79.25` vertically and `-95..96`
  horizontally, inside Turtletoy's native `-100..100` canvas.
- The checked-in preview was rasterized from the exact captured stroke stream.
- `software.tests.test_turtletoy_ironwood` checks self-containment, executes
  the sketch, validates the output bounds, and verifies the expected geometry
  counts.

## Struggles and rejected approaches

An earlier radial fern study became overly tangled once rendered through the
actual turtle path model. A softer moth design was replaced after the requested
direction changed to a lumberjack scene. Embedding a completed SVG was rejected
because the request is specifically for a code-box Turtletoy creation.

## Risks and follow-up

The default artwork is plotter-ready but its density may need adjustment for a
heavier pen. The sliders can reduce crosshatching without changing the scene.
The first physical print should use XY-only motion and fill disabled.

## Files

- `samples/turtletoy/ironwood.js`: paste-ready Turtletoy source.
- `samples/turtletoy/ironwood.md`: adjustable controls and plot guidance.
- `samples/preview/ironwood.png`: preview of the checked-in sketch.
- `tools/render_turtletoy.js`: local API-compatible execution and SVG capture.
- `software/tests/test_turtletoy_ironwood.py`: syntax/execution regression.
- `software/README.md`: discovery link for the standalone Turtletoy artwork.
