---
id: WSW-20261101-007
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/wave_rows.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_wave_x_theta_rows.py
  - tools/check_cmyk_wave_spacing.py
tags:
  - cmyk
  - wave-screen
  - equidistant
  - x-theta
  - y-theta
  - serpentine
  - row-lock
related:
  - WSW-20261101-003
  - WSW-20261101-006
  - ADR-009
---

# Preserve Wave row pitch under Xθ/Yθ

## Summary

CMYK **Wave screen - equidistant rows** now keeps its row-pitch guard in
rotating-bed mode. With explicit Rows ascending or Rows descending, every
parallel row shares one bed-angle schedule at the same along-row position, and
spacing-aware interpolation keeps the final paper gap within `0.005 mm`.

## Reason

The operator confirmed that the new Wave screen produces uniform rows with XY
only and requested the same behavior from Xθ/Yθ, including descending
serpentine order. A controlled `waves_even` coupon measured:

| Motion | Adjacent-row gap spread |
|---|---:|
| XY only | `0.0001 mm` |
| Xθ/Yθ, independent row plans | `0.06437 mm` |

The source rows were uniform. The defect occurred because each row received a
different A schedule, while grblHAL linearly interpolates X, Y, and A between
endpoints. Two parallel paper rows can therefore move closer together between
samples and return to the source separation at shared endpoints.

## Implementation

- `wave_row_theta_schedule()` builds a representative row in the final
  paper-screen frame, plans its angle once, and exposes that schedule by
  along-row position.
- Every Wave row in an explicit ascending/descending order samples the same
  `theta(along)` function. `wave_row_thetas()` preserves descending travel by
  sampling the schedule in the row's actual direction.
- The schedule remains enabled only for `waves_even` through the existing CMYK
  spacing guard, an explicit row order, and non-fixed Xθ/Yθ motion.
- The G-code and preview emitters add spacing-bounded A subdivisions. The
  bound is derived from nominal row pitch with
  `WAVE_ROW_INTERPOLATION_TOLERANCE_MM = 0.0005`.
- Set manifests record `row_theta_lock`, and the G-code frame header records
  `shared Wave row angles`.
- `tools/check_cmyk_wave_spacing.py` now decodes both XY-only point streams and
  Xθ/Yθ interpolated segments. Rotating sets must carry the shared-lock
  metadata and header.

## Verification

- The new regression exercises Rows ascending and Rows descending at all four
  CMYK screen angles.
- Final controlled paper-space gap spreads are:

  | Screen angle | Gap spread | A sweep |
  |---:|---:|---:|
  | `0°` | `0.000638 mm` | `53.50°` |
  | `15°` | `0.002383 mm` | `80.35°` |
  | `45°` | `0.001970 mm` | `61.15°` |
  | `75°` | `0.002153 mm` | `52.62°` |

- The synthetic emitted-move count rises from `1,824` to `2,735-2,982`
  depending on angle.
- An end-to-end synthetic set audit through
  `check_cmyk_wave_spacing.py` passes with `0.002743`, `0.002287`, `0.000684`,
  and `0.001968 mm` spread for cyan/magenta/yellow/black.
- The complete converter suite passes 606 tests with one expected
  OpenGL-context skip.
- The existing 199-column XY-only Ben2 audit still passes all four inks.
- Physical Xθ/Yθ print verification remains open.

## Struggles and rejected approaches

Keeping explicit row order without a shared angle schedule failed the spacing
test. Sharing the schedule but using a loose angular subdivision bound also
failed at 45° and 75° (`0.0081-0.0086 mm` spread). A `0.0005 mm` geometric
headroom bound is required to remain below the existing `0.005 mm` audit gate.

Returning to XY-only would guarantee pitch but discard the requested rotating
bed. Keeping independent A schedules and changing only tolerance also leaves
the interpolation defect in place.

## Risks and follow-up

The shared schedule adds G-code blocks and may increase print time by roughly
`50-65 %` on the controlled coupon; actual four-pass time must be measured.
The representative-row schedule assumes the equidistant Wave style's shared
carrier and vertical displacement. Planner optimized, XY-only, the legacy
diagnostic, and jobs with the spacing guard off retain their previous paths.

A physical four-pass Xθ/Yθ descending print is required. Save the set, run
`check_cmyk_wave_spacing.py`, verify `row_theta_lock: true`, and compare row
quality and elapsed time against the XY-only control.

## Files

- `software/converter_core/wave_rows.py`: shared Wave-row angle schedule and
  paper-space row pitch calculation.
- `software/converter_core/gcode.py`: row-schedule use, manifest-plan metadata,
  and spacing-aware G-code/preview subdivision.
- `software/generator_tabs/cmyk_tab.py`: guard text, summary, and manifest
  recording.
- `software/tests/test_wave_x_theta_rows.py`: two orders, four angles, A sweep,
  descending order, and final gap-spread regression.
- `software/tests/test_check_cmyk_wave_spacing.py`: rotating interpolation and
  shared-lock manifest coverage.
- `tools/check_cmyk_wave_spacing.py`: XY-only and Xθ/Yθ final-spacing audit.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: current behavior, verification, and test boundary.
