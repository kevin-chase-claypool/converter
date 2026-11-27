# ADR-014: Render simulated CMYK pen strokes as triangle ribbons

- Status: accepted and implemented
- Date: 2026-11-27

## Context

The CMYK ink simulation draws generated contours at physical pen width. The
OpenGL preview originally used wide `GL_LINES`. At deep zoom, each segment is
rasterized as an independent rectangle, so a repeating notch appears at every
join. The generated geometry is smooth in a high-resolution raster of the same
coordinates; the artifact is introduced by the live preview.

Combining contours into `GL_LINE_STRIP` calls does not solve the problem.
Separate contours still need separate strips, and transparent bridge vertices
cannot be hidden by the ink-simulation multiply blend because that blend mode
ignores source alpha. A single strip also creates large crossing triangles
between contour jumps.

## Decision

Simulated CMYK ink strokes are represented by one aggregated triangle mesh:

- Each segment emits two triangles at half the configured pen width.
- Adjacent segments share a normalized miter normal at their common endpoint.
- Miter length is capped to avoid unbounded spikes at sharp turns.
- Distinct contours never receive connecting geometry.
- Visible layers are aggregated into one `GL_TRIANGLES` draw call. Hidden
  layers are omitted when the preview cache is rebuilt.
- The OpenGL surface requests multisampling for triangle-edge antialiasing.
- Non-simulation preview centerlines keep the existing line renderer.

## Consequences

- Thick preview strokes have continuous joins at every zoom level without
  changing generated Wave geometry or G-code.
- Separate contours remain visibly separate, including under multiply blending.
- The mesh uses six vertices per segment instead of two line endpoints. The
  current `142,387`-move Wave preview remains responsive, but combined
  four-ink memory and build time at the densest preview remain a follow-up
  benchmark.
- The preview improvement is visual verification only. It does not establish
  ink spread, registration, striation, or other physical print behavior; a
  sparse physical coupon remains required.
