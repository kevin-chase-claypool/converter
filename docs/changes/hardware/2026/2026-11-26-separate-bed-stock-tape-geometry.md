---
id: HW-20261126-001
date: 2026-11-26
category: hardware
affected_categories:
  - hardware
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - tools/export_cmyk_headless.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_reach_guard.py
  - software/tests/test_theta_feed.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_check_cmyk_wave_spacing.py
  - samples/gcode/bed-error-compensation-2026-11-26-dense-v3-368mm-stock-extrapolated.json
  - samples/gcode/bed-error-analysis-dense-v3-368mm-stock-extrapolated.json
  - software/README.md
  - docs/hardware/MECHANICAL_FRAME.md
  - docs/HANDOFF.md
  - docs/integration/INTERFACES.md
  - docs/decisions/ADR-012-bed-stock-and-tape-margin.md
  - docs/project/ROADMAP.md
  - docs/testing/TEST_PLAN.md
tags:
  - rotating-bed
  - paper-stock
  - tape-margin
  - printable-area
  - bed-compensation
  - gantry-reach
  - physical-validation-pending
related:
  - ADR-012
  - ADR-009
  - WSW-20261101-005
---

# Separate bed, stock, and tape-margin geometry

## Summary

The converter now models the installed print geometry as an **18-inch rotating
bed**, **15-inch round stock**, and a **14.5-inch drawing circle**. The
remaining 0.5-inch diameter is a 0.25-inch tape margin on every stock edge.
Preview draws the bed, stock, and reachable drawing circles separately.

## Reason

The previous `Bed dia mm` field represented the paper stock rather than the
physical bed. It modeled 15-inch stock as a 15-inch bed, then used a 6.35 mm
margin and a 180 mm gantry cap to produce a 14.173-inch effective circle. That
did not match the installed 18-inch bed and gave the operator no accurate tape
band or 14.5-inch drawing boundary in Preview.

The project owner confirmed the intended dimensions:

- bed: `18 in` / `457.2 mm`;
- stock: `15 in` / `381.0 mm`;
- drawing area: `14.5 in` / `368.3 mm`;
- stock margin: `0.25 in` / `6.35 mm` on every edge.

## Implementation

- Added independent `stock_diameter_mm`; `bed_diameter_mm` now means the
  physical rotating bed. The internal `bed_margin_mm` field is labeled
  **Stock margin mm** in the Machine settings.
- Artwork clipping uses `stock_diameter_mm / 2 - bed_margin_mm`, then applies
  the gantry and bed-compensation limits. The physical bed continues to own
  machine geometry and safe parking distance.
- Preview adds a separate stock circle between the outer 18-inch bed circle
  and the inner drawing/reach circle.
- Default planning radius is now the owner-specified `184.15 mm`.
- New profile `745e3d264cc5` preserves every measured sample and correction
  from profile `18bfb4ed1c33` while extending the declared local-affine
  coverage from `165.1` to `184.15 mm`.
- The active profile reserves its `1.142 mm` maximum correction inside the
  reach, so nominal artwork clipping is `183.008 mm`; the final corrected XY
  envelope remains capped at `184.15 mm`.
- Every program header records bed diameter, stock diameter, stock margin, and
  drawing radius. CMYK set identity includes those fields.
- Validation rejects stock larger than the physical bed and margins that
  consume the complete stock radius.

## Verification

- Defaults resolve to bed `457.2 mm`, stock `381.0 mm`, margin `6.35 mm`,
  drawing diameter `368.3 mm`, and reach radius `184.15 mm`.
- The regenerated profile differs from the prior expanded profile only in
  `coverage_radius_mm`; all 728 measured samples and corrections are
  byte-equivalent as JSON values.
- New profile fingerprint is `745e3d264cc5`; maximum correction remains
  `1.141625 mm`, and the tested boundary correction at `184.15 mm` is
  `1.105188 mm`, below the 5 mm bound.
- Reach, planner clipping, compensation, CMYK integration, Wave diagnostics,
  and complete converter discovery pass. The complete suite passes `758` tests
  with one expected OpenGL-context skip.
- A real headless Golden Sunset CMYK export passes transactional publication
  with the new default profile and reach. All four programs pass
  `check_gcode_motion.py --strict`, with no bare rotating `G0` and maximum
  drawing-step rotation `6.80 deg` against the `15 deg` cap.
- No full-disc physical plot has verified the owner-selected 184.15 mm reach.

## Struggles and rejected approaches

Keeping the 15-inch value as `Bed dia` would make the Preview outer circle the
paper edge rather than the physical bed. Setting the bed to 18 inches without
a separate stock value would let the planner draw beyond the 15-inch paper.
Using the requested 14.5-inch circle with the old 180 mm default would continue
clipping it to 14.173 inches, while raising the reach without extending the
compensation profile would reject outer points beyond the profile coverage.

## Risks and follow-up

The 184.15 mm default is larger than the prior conservative 180 mm planning
radius. Before a production full-disc plot, run HOME + REGISTER and verify the
live +Y soft-limit envelope, current bed centre, tape clearance, and drag-chain
clearance. The outer `19.05 mm` compensation annulus remains extrapolated and
requires the existing eight-angle edge-band print.

## Files

- `software/converter_core/settings.py`: independent bed/stock defaults,
  margin labeling, validation, and new default profile.
- `software/converter_core/gcode.py`: stock-based clipping.
- `software/qt_svg_to_gcode.pyw`: separate stock circle in Preview.
- `software/tests/`: default geometry, reach, compensation, and CMYK regressions.
- `samples/gcode/`: regenerated 368.3 mm stock profile and analysis.
- `software/README.md`, hardware/interface/roadmap/test documents, and ADR-012:
  current geometry, ownership, and safety gate.
