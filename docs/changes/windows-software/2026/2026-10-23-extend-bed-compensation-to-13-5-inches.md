---
id: WSW-20261023-006
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/bed_calibration.py
  - tools/analyze_bed_error_calibration.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_cmyk_tab.py
  - samples/gcode/bed-error-compensation-2026-10-23-13p5in-extrapolated.json
tags:
  - bed
  - compensation
  - coverage
  - extrapolation
  - cmyk
related:
  - WSW-20261023-005
  - WSW-20261023-004
  - ADR-009
---

# Extend bed compensation coverage to 13.5 inches

## Summary

The default compensation profile now covers a `171.450 mm` radius
(`342.900 mm` / `13.5 in` diameter). It reuses the accepted correction samples
and extrapolates the outer annulus with the profile's existing local-affine
interpolation. The default artwork field is correspondingly limited to a
13.5-inch effective diameter.

## Reason

The prior default field was 13 inches (`165.100 mm` radius). A normal CMYK
preview attempted to place artwork at the 180 mm gantry/reach limit and was
rejected because the selected profile covered only 165.1 mm. The operator
requested a 13.5-inch usable diameter and explicitly accepted extrapolation
from the existing default mesh rather than waiting for another physical
calibration run.

## Implementation

- Added `--coverage-radius-mm` to `tools/analyze_bed_error_calibration.py` and
  an optional coverage argument to `analyze_measurements`; omitted values keep
  the original 165.1 mm generated test radius.
- Generated
  `bed-error-compensation-2026-10-23-13p5in-extrapolated.json`, fingerprint
  `4c8270de8a74`, from the accepted measurement CSV and bed mesh. It retains
  the original samples/corrections and declares 171.45 mm coverage.
- Changed the application default compensation path to that profile.
- Changed the default physical stock setting from 457.2 to 355.6 mm (14-inch
  round stock). With the existing 6.35 mm rim margin, the planner's default
  clip radius is 171.45 mm, matching the extended profile.
- The shared planner and therefore the Convert, generator-tab, CMYK, preview,
  and command-line paths use the same coverage and clipping.

## Verification

- Regenerating from `bed-error-map-2026-10-23.csv` with a 171.45 mm declared
  radius preserves the accepted fit: A=0 spatial error `0.292 mm` RMS /
  `0.537 mm` maximum, leave-one-out profile error `0.197 mm` RMS /
  `0.552 mm` maximum, and `66.1 %` improvement.
- The new profile's largest correction at the 171.45 mm boundary is
  `1.054 mm`, inside the 5 mm safety bound.
- A default planner test verifies that a 180 mm input is clipped to the
  171.45 mm field before compensation coverage is checked.
- The bed-compensation/photo suite passes all `28` tests, the CMYK tab suite
  passes all `64` tests including per-ink default-profile inheritance, and the
  full converter suite passes `486` tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Increasing only the declared radius would leave the default 457.2 mm bed
  and 180 mm reach active, so a 180 mm CMYK point would still fail. The stock
  diameter and rim margin were aligned with the requested effective diameter.
- Treating the extended annulus as newly measured was rejected. Only the
  inner 165.1 mm field has an independent compensated verification; the outer
  6.35 mm annulus is explicitly an extrapolation.
- Adding a per-job arbitrary coverage override was not needed for this
  request; the supported analyzer option creates an auditable profile
  instead of silently changing limits in the UI.

## Risks and follow-up

- The outer annulus from 165.1 to 171.45 mm is extrapolated, not
  independently verified. Print and measure an edge-band verification sheet
  before relying on the outer 6.35 mm for precision work.
- The default assumes 14-inch round stock with a 6.35 mm rim margin. A
  physically smaller sheet or a larger configured margin reduces the usable
  field even though the profile declares 171.45 mm.
- The original verified `2cdf3731de4a` profile remains available for
  comparisons within its measured 165.1 mm field.

## Files

- `software/converter_core/settings.py`: default 13.5-inch field and new
  compensation profile.
- `software/converter_core/bed_calibration.py`: configurable profile coverage
  radius.
- `tools/analyze_bed_error_calibration.py`: coverage-radius generation option.
- `samples/gcode/bed-error-compensation-2026-10-23-13p5in-extrapolated.json`
  and corresponding analysis JSON: extended default profile and evidence.
- `software/tests/test_bed_compensation.py` and
  `software/tests/test_cmyk_tab.py`: extrapolated coverage, clipping,
  default-profile, and per-ink inheritance regressions.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`: current
  behavior and extrapolation boundary.
