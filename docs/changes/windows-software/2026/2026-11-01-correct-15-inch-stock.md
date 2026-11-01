---
id: WSW-20261101-005
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: verified
components:
  - software/converter_core/settings.py
  - software/converter_core/bed_calibration.py
  - software/converter_core/rotation_calibration.py
  - samples/gcode/bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json
  - samples/gcode/bed-error-analysis-dense-v3-360mm-reach-extrapolated.json
tags:
  - bed-compensation
  - printable-canvas
  - stock-diameter
  - dense-v3
  - extrapolation
related:
  - WSW-20261101-002
  - ADR-009
---

# Correct the default stock diameter to 15 inches

## Summary

The converter now models the installed round stock as 15 inches rather than
14 inches. With the existing `6.35 mm` rim margin, the stock permits a
`368.300 mm` (14.5-inch) rim-clear diameter. The `180.000 mm` gantry-reach
radius is tighter, so the usable and compensation diameter is `360.000 mm`
(`14.173 inches`).

Default compensation profile `f85ec410dbac` retains the centered dense-v3
measurements and extends the local-affine field to the full 180 mm reach.

## Reason

The prior default used a 14-inch stock assumption and clipped the drawable
field at a `342.900 mm` (13.5-inch) diameter. The project owner confirmed the
actual sheets are 15 inches in diameter. Leaving the old default would discard
available stock area and generate calibration documents with the wrong stock
size.

## Implementation

- Changed `DEFAULT_BED_DIAMETER_MM` from `355.6` to `381.0 mm`.
- Kept the owner-selected `6.35 mm` rim margin.
- Made the default compensation diameter the smaller of the stock's rim-clear
  diameter and the `360.0 mm` gantry-limited diameter.
- Added a single `DEFAULT_MACHINE_REACH_RADIUS_MM` constant and used it for the
  default Machine setting.
- Generated profile
  `bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json`
  from the centered dense-v3 measurement CSV. It keeps every measured sample
  and correction through `165.100 mm` and declares `180.000 mm` coverage.
- Updated bed and rotation calibration generators to use 15-inch stock.
- Changed diagnostic generators to follow the application's current default
  compensation profile instead of a duplicated historical profile path.

## Verification

- The analyzer reproduced the centered dense-v3 fit: A0 spatial error
  `0.518 / 0.890 mm` RMS/max, A0 control `0.353 / 0.783 mm`, and
  leave-one-station-out `0.274 / 0.760 mm` with `50.2 %` improvement.
- Profile fingerprint: `f85ec410dbac`.
- Selected-angle maximum correction: `1.141625 mm`.
- Extreme correction at the 180 mm boundary: `1.056512 mm`, below the `5 mm`
  safety cap.
- The focused bed-compensation, CMYK, rotation-calibration, and Wave diagnostic
  suites pass 167 tests.
- The complete converter suite passes 602 tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Keeping the 13.5-inch profile would leave the stock area underused. Expanding
the profile to the stock's 184.15 mm rim-clear radius would describe motion the
gantry cannot reach. Retaining hardcoded calibration profile paths would let
diagnostic tools drift away from the application default.

## Risks and follow-up

Only the `165.100 mm` inner field is measured. The `14.900 mm` outer annulus is
local-affine extrapolation and remains unverified on paper. The roadmap's
stationary edge-band test must cover `165.100-180.000 mm` at all eight
calibrated angles before the outer field is treated as precision-qualified.

## Files

- `software/converter_core/settings.py`: default stock, reach, compensation
  diameter, profile path, and operator help.
- `software/converter_core/bed_calibration.py`: 15-inch calibration stock.
- `software/converter_core/rotation_calibration.py`: 15-inch rotation-test
  stock.
- `software/tests/test_bed_compensation.py`: 180 mm default-profile and planner
  boundary coverage.
- `software/tests/test_cmyk_tab.py`: current-profile integration.
- `software/tests/test_rotation_calibration.py`: 15-inch generated sheet.
- `software/tests/test_wave_rotation_isolation.py`: current-profile diagnostic
  fixture.
- `tools/make_cmyk_wave_coupon.py` and
  `tools/make_wave_rotation_isolation_test.py`: use the shared current profile.
- Expanded profile and analyzer report under `samples/gcode/`.
- `software/README.md`, `docs/integration/INTERFACES.md`, ADR-009, the roadmap,
  and the test plan: current behavior and remaining edge-verification risk.
