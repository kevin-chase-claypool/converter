---
id: WSW-20261123-010
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
  - fine-detail
  - keylines
  - sharpening
related:
  - WSW-20261123-003
  - WSW-20261123-006
  - WSW-20261123-007
  - WSW-20261123-009
  - docs/proposals/flow-field-cmyk.md
---

# Strengthen Fine detail edge separation and sharpening

## Summary

Fine detail now does more than reduce pitch and layer count. It enables a
`60 %` unsharp mask at `1.5 mm` on paper and quiets C/M/Y coverage beside the
strongest coherent Black keylines. The result preserves more eye, nostril,
mouth, tooth, and collar structure without returning to the five-layer,
wide-smoothing portrait.

## Reason

The previous Fine detail render reduced tensor blur successfully, but color
streamlines still crossed directly beside the Black keylines. In the physical
overprint, those neighboring colors can bury the single Black boundary. The
photo had also lost some fine luminance contrast before screening because
Fine detail did not alter sharpening.

## Implementation

- Fine detail enables Unsharp mask at `60 %`, radius `1.5 mm`.
- The edge-confidence field is now used in two roles: stronger continuous
  coverage on the Black plate, and `65 %` lower tone coverage beside the same
  high-confidence boundaries on C/M/Y.
- The color plates remain independently seeded and tone-gated away from those
  edges. There is no shared color mask or synthetic outline.
- Active state now also requires the expected sharpening controls. The
  reversible snapshot includes sharpening checkbox, amount, and radius.
- The keyline control label identifies the paired edge separation.

## Verification

- A synthetic coherent edge regression verifies that color-edge quieting
  reduces ink length while preserving the under-keyline Black result.
- Per-ink capture verifies C/M/Y receive `0.65` edge quieting and Black does
  not; Black alone receives the continuous keyline boost.
- Fine detail tests verify `60 %` / `1.5 mm` sharpening, active-state tracking,
  exact toggle restoration, snapshot round-trip, and legacy fallback.
- A `600 px` software comparison shows the keylined-and-sharpened face with
  clearer eye, nostril, lip, tooth, and collar boundaries than the keyline-only
  version, while retaining the source color density.
- All `126` CMYK tab tests pass. Complete converter discovery passes `646`
  tests with one expected OpenGL-context skip.

## Struggles and rejected approaches

Sharpening alone improved only small high-frequency changes and did not
separate competing color strokes from Black. Color quieting alone left the
source's eye and mouth contrast slightly soft. The combined change is
intentionally modest; a larger sharpening amount created texture noise in the
blurred background.

## Risks and follow-up

The values are software-selected from this portrait and synthetic edges.
Physical ink spread can still fill narrow color gaps, so a four-pass sheet is
required. Background texture remains driven by the image rather than a
subject mask.

## Files

- `software/converter_core/structure_tensor.py`: local color-edge quieting.
- `software/converter_core/cmyk.py`: Edge-flow keyline and quieting plumbing.
- `software/generator_tabs/cmyk_tab.py`: Fine-detail sharpening, active-state
  requirements, and per-plate quieting.
- `software/tests/test_cmyk_tab.py`: edge-quieting and preset regressions.
- `software/README.md`: current operator behavior and settings.
- `docs/proposals/flow-field-cmyk.md`: current edge and sharpening parameters.
- `docs/project/ENGINEERING_LOG.md`: comparison and verification evidence.
