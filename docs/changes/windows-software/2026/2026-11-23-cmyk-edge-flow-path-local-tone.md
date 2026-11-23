---
id: WSW-20261123-004
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - continuous-tone
  - path-local
  - block-artifact
  - portrait
related:
  - WSW-20261123-003
---

# Remove block matrix from edge-flow tone

## Summary

Edge-flow tone breaks now follow distance along each individual streamline.
The output no longer uses a shared two-dimensional threshold grid, so
neighbouring streamlines do not switch ink at common square-block boundaries.

## Reason

The first continuous-tone implementation preserved the yellow-to-magenta
highlight ramp, but its `4-8 mm` threshold cells made the preview read as a
matrix of rectangular blocks. The cells were uniform in page space even though
the streamlines crossed them at different orientations.

## Implementation

- The tone threshold is now a deterministic function of:
  - accumulated arc length through the current streamline;
  - a hash derived from that streamline's seed, layer, and starting cell;
  - the owning ink layer.
- Adjacent paths therefore receive independent tone-break phases. The
  `4-8 mm` value controls the approximate segment scale, not a visible page
  lattice.
- Streamlines still follow the shared strength-gated luminance field, and each
  ink retains its own tone mask, fallback angle, layer range, and four-file
  output.

## Verification

- A new regression proves that two streamlines have different threshold
  sequences at the same distances and that each sequence continues to vary
  along its path.
- The continuous tone-ramp regression still passes across six brightness
  levels from `0.12` to `0.55`.
- All `117` CMYK tab tests pass.
- An `800 px` software render at `1.2 mm` effective pitch and three flow
  layers shows irregular tonal breaks along the face, clothing, wood, and
  background without the previous square lattice.
- Complete converter discovery passes `637` tests with one expected
  OpenGL-context skip.
- No physical four-pass edge-flow sheet has been printed.

## Struggles and rejected approaches

Smaller paper-space cells reduced block size but increased speckle. Keeping
the 2D lattice and only changing its phase still left visible alignment.
Whole-path acceptance removed the blocks but over-inked whenever a path
crossed from highlight into shadow.

## Risks and follow-up

The apparent stroke fragmentation depends on pen width, final pitch, paper,
and ink spread. A physical edge-flow sheet remains the next validation gate.

## Files

- `software/converter_core/structure_tensor.py`: path-local tone threshold and
  arc-length run splitting.
- `software/tests/test_cmyk_tab.py`: path-local threshold regression.
- `software/README.md`: current no-matrix behavior.
- `docs/proposals/flow-field-cmyk.md`: current path-local tone method.
- `docs/project/ENGINEERING_LOG.md`: rejected cell-lattice evidence.
