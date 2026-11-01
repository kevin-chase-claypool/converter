---
id: WSW-20261101-002
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - samples/gcode/bed-error-compensation-2026-11-01-dense-v3-13p5in-extrapolated.json
tags:
  - bed-compensation
  - printable-canvas
  - dense-v3
  - extrapolation
  - cmyk
related:
  - WSW-20261101-001
  - ADR-009
---

# Expand the default printable canvas to 13.5 inches

## Summary

The converter's default 14-inch round stock now uses a 0.25-inch rim margin,
increasing the printable diameter from 13.0 to 13.5 inches
(`330.2` to `342.9 mm`). The default compensation profile retains the complete
centered dense-v3 measurement field and extends its declared correction radius
from `165.100` to `171.450 mm`.

The CMYK Jeep settings were not changed. Its Wave style, pitch, tone controls,
XY-only motion, and local settings remain operator-owned and independent of
the machine-canvas defaults.

## Reason

The project owner requested a 0.5-inch larger printable diameter while keeping
the current Jeep CMYK recipe. A default bed margin of 0.5 inch had made the
existing measured 13.0-inch compensation field the limiting canvas.

## Implementation

- Changed the default bed margin from `12.7` to `6.35 mm`.
- Set the application default drawable and compensation diameter to
  `13.5 * 25.4 = 342.9 mm`.
- Generated profile `057313c41e21` from the centered dense-v3 measurement CSV
  with the existing `171.450 mm` local-affine coverage option. The measured
  samples and corrections are unchanged from `18bfb4ed1c33`; only the declared
  radial coverage changes.
- The extreme correction at the new declared boundary is `0.962080 mm`, below
  the existing 5 mm safety cap.
- Left CMYK image-processing and screen controls unchanged.

## Verification

- `py -3.13 -m unittest software.tests.test_bed_compensation`: 43 tests pass.
- `py -3.13 -m unittest software.tests.test_cmyk_tab`: 101 tests pass.
- The analyzer reproduced the source dense-v3 fit: A0 spatial error
  `0.518 / 0.890 mm` RMS/max, A0 control `0.353 / 0.783 mm`, and
  leave-one-station-out `0.274 / 0.760 mm` with `50.2 %` improvement.
- The generated profile fingerprint is `057313c41e21` and its measured
  maximum correction remains `1.142 mm`.

## Struggles and rejected approaches

Increasing only the bed diameter or reducing only the margin would have left
planning clipped at the old `165.1 mm` profile coverage. Reusing the older
`4bad792e35ad` 13.5-inch profile was rejected because it would discard the
newer centered dense-v3 measurements. Changing CMYK defaults was rejected
because the owner explicitly asked to preserve the Jeep recipe.

## Risks and follow-up

The dense-v3 measurements extend only to the `148.5 mm` station ring and had
already declared `165.1 mm` coverage. The new outer `6.35 mm` annulus is
therefore extrapolated, not measured. Before treating the edge as
precision-qualified, run M-12 edge-band verification over `165.1-171.45 mm`
at all eight calibrated angles and meet the roadmap's stated error gates.

## Files

- `software/converter_core/settings.py`: default margin, diameter, profile,
  and operator tooltips.
- `software/tests/test_bed_compensation.py`: default-profile and expanded
  boundary regressions.
- `software/tests/test_cmyk_tab.py`: current-profile inheritance expectations.
- `samples/gcode/bed-error-compensation-2026-11-01-dense-v3-13p5in-extrapolated.json`:
  expanded default compensation profile.
- `samples/gcode/bed-error-analysis-dense-v3-13p5in-extrapolated.json`:
  analyzer report for the expanded profile.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`,
  `docs/testing/TEST_PLAN.md`, and `docs/project/ROADMAP.md`: current behavior,
  verification status, and unverified-annulus risk.
