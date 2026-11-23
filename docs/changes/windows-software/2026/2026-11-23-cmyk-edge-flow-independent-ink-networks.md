---
id: WSW-20261123-001
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/structure_tensor.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - structure-tensor
  - per-ink-screen
  - streamline
  - four-file-output
  - portrait
related:
  - WSW-20261122-002
  - WSW-20261122-003
  - WSW-20261122-004
---

# Keep edge-flow CMYK as four independent ink networks

## Summary

Edge-flow now follows the same four-pen model as the other CMYK screens. Cyan,
magenta, yellow, and black each derive a direction field from their own
processed tone image, use their own fixed fallback screen angle, and are saved
as four independent, page-registered G-code programs. The preview still
multiplies the four layers to show the combined print.

This supersedes the shared processed-RGB guide and common streamline network
described by `WSW-20261122-003` and `WSW-20261122-004`.

## Reason

The reference conversion shows different line directions and densities for the
four inks. Zooming the source print made that especially clear in flat
background areas, where a conventional rotated screen appears, and in the
portrait, where each ink follows a different tone distribution. The previous
implementation forced every ink through the union of all four tone masks and
one shared geometry. That removed some color fringing but also collapsed the
reference's four-screen behavior and made the result read as one contour mask.

The requested output contract is four overlapping G-code files, matching the
existing CMYK feature. A combined preview is acceptable; a flattened combined
program is not.

## Implementation

- `prepare_image_tones()` no longer creates the shared `flow_rgb` and
  `flow_coverage` arrays. Wave screening still receives the common luminance
  `depth` field.
- `screen_channel(style="edge_flow")` now uses the current ink's tone as its
  default guide and traces against that same tone mask.
- The CMYK tab passes each channel's processed tone explicitly, offsets the
  seed per ink, and supplies the classic cyan 15, magenta 75, yellow 0, and
  black 45 degree fallback angles.
- The four layers retain the shared page frame, artwork scale, registration
  crosses, pen offsets, preview, bed compensation, and save preflight. Save
  still writes four separate G-code files.
- Edge-flow keeps the paper-space pen-envelope conversion for nonzero Artwork
  scale and the larger seed-candidate budget that prevents a fine requested
  pitch from being silently coarsened by the mark cap.

## Verification

- A flat-field regression proves that a 0 degree plate traces horizontally and
  a 90 degree plate traces vertically with the same seed and tone.
- A two-mask regression proves the independent plates no longer force one
  plate's visible path to be a subset of another plate's network.
- A UI regression captures all four screen calls and verifies distinct 2D tone
  guides, per-ink seeds, classic screen angles, paper-space pen widths, and no
  shared coverage array.
- The scaled-page regression now runs in edge-flow mode and verifies that all
  four planned programs keep the same source/page center.
- The save regression verifies four distinct files for the scaled edge-flow
  workflow.
- All 113 CMYK tab tests pass.
- Complete converter discovery passes 633 tests with one expected
  OpenGL-context skip.
- A 1200 px software render of `IMG_0514.JPG` shows separate colored
  streamline networks and the expected rotated fallback directions. It
  completed in 18.61 s with pen-down marks C 4542, M 5307, Y 6295, and K 6137.
  This is software evidence only; no physical four-pass edge-flow sheet has
  been measured.

## Struggles and rejected approaches

The shared processed-RGB tensor preserved chroma-only boundaries, but it was
based on an incorrect assumption that all four pens should trace one common
centerline network. Using the same seed alone did not align ink-specific growth
or stopping rules, so the next attempt also shared occupancy and tone union.
That reduced multicolor fringing but removed the independent screen directions
visible in the reference.

Keeping the shared network and giving every plate the 45 degree black fallback
was also rejected: it made flat regions collapse to one hatch direction and
contradicted the observed four-color print.

## Risks and follow-up

Separate tone fields can produce colored edge fringes where similar structures
drift apart, and JPEG chroma noise can steer a plate locally. Flow smoothing
and the per-ink image controls remain the tuning levers. The physical test
still must establish pitch, smoothing, layer count, pen order, overlay
registration, and total plotting time for the actual pen set and paper.

## Files

- `software/converter_core/cmyk.py`: removed shared edge-flow guide/coverage
  construction and restored per-ink channel guides.
- `software/converter_core/structure_tensor.py`: per-plate tracing and
  fine-pitch candidate budget.
- `software/generator_tabs/cmyk_tab.py`: per-ink guide, seed, and screen-angle
  handoff plus current manifest identifier.
- `software/tests/test_cmyk_tab.py`: independent-network, direction, scaling,
  page-frame, and four-file save regressions.
- `software/README.md`: current four-pen behavior and starting recipe.
- `docs/project/ROADMAP.md`: physical validation remains open.
- `docs/project/ENGINEERING_LOG.md`: implementation and rejected-approach
  record.
