---
id: WSW-20261101-003
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/kinematics.py
  - software/converter_core/settings.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - contour-order
  - row-sweep
  - striation
  - planner
related:
  - WSW-20261101-001
  - WSW-20261101-002
  - ADR-009
---

# Add monotonic row ordering for CMYK Wave output

## Summary

The CMYK Kinematics group now offers **Planner optimized**, **Rows ascending**,
and **Rows descending** for both Wave styles. The two row modes sweep complete
row bands in a serpentine direction, preventing the generic travel optimizer
from returning to a disconnected fragment in an earlier row band.

## Reason

Wave rows are generated in source order, but `planned_contours()` feeds every
fragment into a spatial nearest-endpoint search followed by a bounded 2-opt
pass. A controlled four-row, two-island grid reproduces the behavior: source
indices `0,1,2,3,4,5,6,7` are emitted as `0,6,5,3,1,7,2,4`. The operator reports
that visible striations concentrate when the pen makes these quadrant returns
to finish an earlier row.

## Implementation

- Added the validated `contour_order` setting with `optimized`,
  `rows_ascending`, and `rows_descending` values.
- Wave-only CMYK controls select the mode; non-Wave and calibration styles
  force the established planner-optimized order.
- Every generated Wave row carries its exact row index through SVG parsing as
  `data-wave-row`. Ascending and descending modes group those rows, preserve
  their overall direction, and alternate each row's along-row direction.
- The row modes bypass the nearest-endpoint ordering and 2-opt pass. Fragments
  are sorted and oriented within their actual row band, so a split row finishes
  before the pen enters the next row.
- Set manifests record the effective `screen.contour_order`.
- Planner-optimized remains the default so existing jobs and travel estimates
  are unchanged until the operator selects a row mode.

## Verification

- The new `software.tests.test_contour_order` regression proves optimized mode
  can reorder the controlled row grid, Wave rows retain their source identity,
  and ascending/descending modes emit the expected serpentine G-code contour
  order.
- CMYK-tab tests cover control availability, per-style activation, settings
  propagation, and manifest recording.
- The focused contour-order and CMYK-tab suites pass `111` tests.
- The complete converter suite passes `601` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Inferring row bands from final path coordinates was rejected because wave
amplitude, partial ink coverage, and clipping can shift a fragment's measured
centre enough to cross into a neighbouring band. Preserving the generator's
actual source order avoids that ambiguity. Applying row order to every screen
style was rejected because only Wave guarantees a meaningful row-major source
sequence.

## Risks and follow-up

Strict row order can add pen-up travel across blank areas. A static contour-gap
estimate for the current Jeep recipe ranged from `-1.7` to `+4.6 minutes` per
ink, or about ten minutes across the four passes at `F3000`, versus planner
optimized. The setting therefore remains opt-in. Print the same layer with
optimized and ascending order on one fixed sheet; keep the row order only if
the quadrant-return striation improves enough to justify the measured time.

## Files

- `software/converter_core/settings.py`: validated contour-order setting.
- `software/converter_core/cmyk.py`: tags each generated row and serializes
  its `data-wave-row` identity.
- `software/converter_core/geometry.py`: preserves row-tagged contours through
  SVG parsing and geometry transforms.
- `software/converter_core/kinematics.py`: source-order contour path.
- `software/generator_tabs/_tab_common.py`: preserves contour tags while
  applying artwork scale.
- `software/generator_tabs/cmyk_tab.py`: Wave-only control and manifest field.
- `software/tests/test_contour_order.py`: ordering and G-code regressions.
- `software/tests/test_cmyk_tab.py`: UI, settings, and manifest coverage.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: operator procedure, tradeoff, and status.
