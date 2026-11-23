---
id: WSW-20261123-002
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
  - strength-gate
  - shared-luminance
  - per-ink-screen
  - four-file-output
related:
  - WSW-20261122-002
  - WSW-20261123-001
---

# Gate edge-flow guidance with structure strength

## Summary

Edge-flow now uses one shared processed-luminance guide for image form, with a
structure-strength gate. Strong coherent edges bend the streamlines; broad
tone, flat colour, and weak texture keep each ink's own fixed screen direction.
Cyan, magenta, yellow, and black still use independent coverage masks, seeds,
density layers, fallback angles, and G-code files.

## Reason

The previous per-ink tone fields made different colours pursue conflicting
contours. The normalized tensor also treated approximately `92 %` of the
portrait as edge-guided because coherence remained high in low-gradient areas.
The resulting preview stacked nested red, magenta, yellow, and black contour
bands over the face, unlike the reference print's shared form and fine
cross-direction screen.

The reference's colour directions are still distinct, but primarily where the
image has no strong structure. A shared luminance field preserves the one
portrait form while the classic cyan 15, magenta 75, yellow 0, and black 45
degree fallbacks retain the four-pen hatching.

## Implementation

- The CMYK tab passes the shared `depth` luminance field to every edge-flow
  plate. The per-ink tone remains authoritative for where that plate can draw.
- `trace_structure_streamlines()` blends toward the fixed angle using both
  directional coherence and tensor trace strength. A minimum trace scale
  prevents weak tone or JPEG noise from steering a plate uniformly.
- Weak coherent guidance now starts at `0.10` and reaches full guidance at
  `0.35`. Tensor trace below the strength floor remains on the screen angle.
- Per-ink seeds, fallback angles, six-layer density limit, shared page frame,
  preview, preflight, and four-file save contract are unchanged.
- The print-set manifest identifies
  `strength_gated_shared_luminance_structure_tensor`.

## Verification

- The existing diagonal-gradient regression still follows the strong image
  form after strength gating.
- A new weak-gradient regression falls back to the requested screen direction
  instead of treating a nearly flat tone change as structure.
- Existing flat-guide, equal-luminance colour boundary, independent-mask,
  per-ink screen-angle, scaling, page-frame, calibration, and four-file save
  regressions pass.
- All `114` CMYK tab tests pass.
- A 1200 px software render of `IMG_0514.JPG` completed in 14.11 s with
  pen-down marks C 4024, M 4697, Y 5968, and K 5284. It now shows a
  cross-direction hatch in low-structure face and background regions while the
  strong facial, hair, and clothing edges remain shape-following.
- No physical four-pass edge-flow sheet has been measured.

## Struggles and rejected approaches

Using each CMYK tone as its own guide made the coloured networks disagree
inside the same cheek, eye, and shirt surfaces. Restoring one luminance guide
without a strength gate still produced nearly all contour following. Increasing
the coherence threshold alone removed facial detail, because low-gradient
areas can remain highly coherent.

Sharing streamline occupancy, seeds, or a single fallback angle was not
reintroduced. Those approaches remove the four independent overlapping pen
programs and the reference's visible screen directions.

## Risks and follow-up

The strength floor and coherence blend are fixed algorithm constants rather
than user controls. They were selected from one portrait and synthetic
regressions, so a varied-image software sweep and a physical four-pass sheet
are still required. Pen width, effective pitch, layer count, ink order, and
paper spread may change the best threshold.

## Files

- `software/converter_core/cmyk.py`: shared-guide documentation and edge-flow
  handoff.
- `software/converter_core/structure_tensor.py`: tensor-strength gate and
  coherence blend.
- `software/generator_tabs/cmyk_tab.py`: shared luminance guide and manifest
  identifier.
- `software/tests/test_cmyk_tab.py`: weak-gradient fallback, shared-guide, and
  existing edge-flow regressions.
- `software/README.md`: current behavior and starting recipe.
- `docs/proposals/flow-field-cmyk.md`: implemented guide model.
- `docs/project/ROADMAP.md`: validation status.
- `docs/project/ENGINEERING_LOG.md`: implementation and rejected approaches.
