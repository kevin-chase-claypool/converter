---
id: WSW-20261124-004
date: 2026-11-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_artwork_placement.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - artwork-placement
  - registration
  - manifest
  - gcode-header
  - physical-validation-pending
related:
  - WSW-20261124-003
  - WSW-20261024-008
  - WSW-20261101-004
---

# Record artwork placement in CMYK outputs

## Summary

CMYK set manifests now record the global artwork placement, and every G-code
program with a non-zero placement records the same X/Y values in its header.
A later multi-pass set can therefore be checked against the placement used by
the earlier passes before any machine motion.

## Reason

The regenerated cyan and black files appeared shifted relative to the already
printed yellow and magenta shoulders. A bed-frame raster comparison of the
earlier and regenerated four-ink programs found the same `+3.5 mm X`,
`+27.5 mm Y` correction for every ink after moving the earlier files onto the
new files. That common translation is consistent with the previous `-3.17 mm`
X and `-28.74 mm` Y artwork placement being omitted, not with chaining,
reach-guard clipping, pen offsets, or an ink-specific mechanical shift.

The G-code did not state its placement and the version-4 set manifest omitted
it, so four internally valid programs could silently belong to different
paper-space frames.

## Implementation

- `contours_to_gcode()` writes
  `(artwork placement X,Y mm)` when either placement component is non-zero.
- The CMYK set manifest adds `artwork_placement_mm: [x, y]` beside the shared
  frame record.
- The additions are backward-compatible within the existing version-4 set
  schema; older manifests remain readable and simply lack the field.

## Verification

- Focused regressions assert the non-zero G-code header and the manifest field.
- The original red run failed on both missing fields and passed after the
  implementation.
- The mixed-print comparison loop reports the same translation on C, M, Y, and
  K, ruling out a channel-specific screen or pen-offset change.
- Physical alignment remains unverified until all four plates are regenerated
  with the saved placement and inspected together.

## Struggles and rejected approaches

- Treating the shoulder motion as a reach-guard or chaining defect was rejected
  because those changes do not produce one common translation across all four
  independently screened inks.
- Approximate direct post-processing of the saved machine coordinates was
  rejected because it would preserve the old planner decisions and risk
  conflicting with the already-applied bed compensation. The set must be
  regenerated in the correct placement before theta planning.

## Risks and follow-up

The provenance fields make a placement mismatch detectable; they do not decide
which placement the operator intended. The next four-file save must be checked
for `-3.170, -28.740 mm` in every header and the matching manifest before the
operator starts the machine. Do not resume the mixed four-pass sheet unless
the earlier printed frame can be reproduced exactly.

## Files

- `software/converter_core/gcode.py`: writes non-zero placement into the
  program header.
- `software/generator_tabs/cmyk_tab.py`: records placement in the set manifest.
- `software/tests/test_artwork_placement.py`: header regression.
- `software/tests/test_cmyk_tab.py`: manifest regression.
- `software/README.md`: current regeneration and pre-print check.
