---
id: WSW-20261030-003
date: 2026-10-30
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/bed_compensation.py
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
  - software/generator_tabs/cmyk_tab.py
  - tools/check_cmyk_wave_spacing.py
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-set.json
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - bed-compensation
  - projected-mesh
  - final-machine-coordinates
  - ben2
related:
  - WSW-20261030-002
  - ADR-009
  - docs/research/2026-10-30-row-locked-bed-compensation.md
---

# Row-lock Wave bed compensation instead of disabling it

## Summary

CMYK **Wave screen - equidistant rows** now keeps the active
bed-compensation profile and applies it as a row-locked final transform. The
complete measured field is projected onto displacement common to every
parallel row. The output remains an exact uniform lattice while retaining the
compatible positional correction. Canonical Ben2 files now carry active
profile `18bfb4ed1c33` in all four inks.

## Reason

The previous `WSW-20261030-002` workaround cleared the compensation path to
preserve row pitch. That passed the machine-space audit but rejected the
required bed correction. Applying the raw field preserved more correction but
changed Ben2 adjacent gaps by `0.224830-0.323477 mm`.

An arbitrary two-dimensional displacement cannot preserve every pairwise
source distance. The constrained solution is to retain only the displacement
component that is invariant across rows at each along-row coordinate.

## Implementation

- Added `RowLockedBedCompensation` and
  `row_locked_bed_compensation()` to `bed_compensation.py`. The full profile is
  sampled across the measured angular slices; correction vectors are resolved
  in the effective paper-screen frame and averaged across the perpendicular
  row coordinate.
- Added internal `row_locked_compensation` and
  `row_lock_screen_angle_deg` settings. The CMYK analysis worker supplies the
  correct `15/75/0/45 deg` angle for cyan/magenta/yellow/black.
- Changed the Wave spacing guard from **skip bed compensation** to
  **row-lock bed compensation**. Unchecking it retains the raw field and warns
  that pitch may change.
- G-code headers record the source-profile fingerprint, projected maximum,
  full-field maximum, row angle, and `row-locked projection`.
- Version-3 set manifests record `row_locked_projection`, per-ink angles,
  projection sampling, profile fingerprint, and full correction maximum.
- `check_cmyk_wave_spacing.py` now accepts only row-locked compensated sets,
  verifies the G-code header and active profile identity, and continues to
  measure final emitted machine `X/Y`.

## Verification

The preserved raw-compensated Ben2 set (the acceptance failure) measures:

| Ink | Minimum | Maximum | Spread |
|---|---:|---:|---:|
| Cyan | `1.807922 mm` | `2.048475 mm` | `0.240553 mm` |
| Magenta | `1.819102 mm` | `2.050997 mm` | `0.231895 mm` |
| Yellow | `1.731065 mm` | `2.054542 mm` | `0.323477 mm` |
| Black | `1.810685 mm` | `2.035515 mm` | `0.224830 mm` |

The new canonical row-locked final-machine audit at 199 columns:

| Ink | Minimum | Median | Maximum | Spread |
|---|---:|---:|---:|---:|
| Cyan | `1.914045 mm` | `1.915527 mm` | `1.916477 mm` | `0.002432 mm` |
| Magenta | `1.914134 mm` | `1.915541 mm` | `1.916389 mm` | `0.002255 mm` |
| Yellow | `1.915396 mm` | `1.915465 mm` | `1.915511 mm` | `0.000115 mm` |
| Black | `1.914453 mm` | `1.915525 mm` | `1.915994 mm` | `0.001541 mm` |

- `tools/check_cmyk_wave_spacing.py` passes all four canonical files.
- `tools/check_macros.py` parses all four canonical files.
- `tools/check_gcode_motion.py --strict` passes all four with zero A motion.
- The four emitted programs contain active row-lock headers naming
  `18bfb4ed1c33`.
- The row-lock fingerprint formatter now uses the angle-list string with a
  `%s` placeholder. A regression exercises the fingerprint directly; the
  previous `%d` placeholder raised `TypeError` on the first application
  preview and prevented G-code planning.
- The complete converter suite passes `588` tests with one expected
  OpenGL-context skip.
- Projected 0-degree correction RMS by screen angle is cyan `0.348369 mm`,
  magenta `0.384489 mm`, yellow `0.331569 mm`, and black `0.370416 mm`, versus
  raw fields of approximately `0.465-0.475 mm`.
- Projected maximum correction is cyan `0.549282 mm`, magenta `0.678172 mm`,
  yellow `0.558554 mm`, and black `0.614273 mm`.

Canonical SHA-256:

- Cyan: `ca6c785d2219c8b278060b9cf223456a937fe532d190cd6b68d05e78104b36db`
- Magenta: `d61e028c7f0c65591bf23f19d814498710d47881abed0f9a421bc126645d78c0`
- Yellow: `7c356ebdd26d9d6d8f8db5508e5a763c9009af6064333d829b268f24d503d9e6`
- Black: `d68abc16fbe8642ed04b372bd27ae2f4a3e70fc496a09dd5242707593e7816a0`

## Struggles and rejected approaches

No-compensation output passed spacing but did not satisfy the requirement.
Raw compensation reproduced the observed failure. As-rigid-as-possible
deformation reduces distortion but does not enforce the `0.005 mm` row bound.
Inverse-warping the source so the raw field lands on a lattice numerically
applies every vector while cancelling its intended physical correction.

The first final-machine investigation also used the wrong acceptance plane:
inverse compensation returned the undisturbed paper lattice. This change
measures the coordinates actually emitted to grblHAL.

## Risks and follow-up

The row-locked map intentionally drops the raw field's row-normal variation.
It retains `50.9-65.5 %` of raw displacement energy depending on ink angle; it
is not equivalent to applying the raw mesh unchanged. The current automated
acceptance is XY-only. A physical comparison print of all four canonical files
must confirm that the retained correction improves placement and does not
reintroduce visible row drift.

## Files

- `software/converter_core/bed_compensation.py`: row-locked field projection.
- `software/converter_core/gcode.py`: final transform integration and header.
- `software/converter_core/settings.py`: internal projection controls.
- `software/generator_tabs/cmyk_tab.py`: guard semantics, per-ink angle, and
  manifest metadata.
- `software/tests/test_bed_compensation.py`: projection and emitted-row tests.
- `software/tests/test_cmyk_tab.py`: guard, manifest, and worker-angle tests.
- `tools/check_cmyk_wave_spacing.py`: compensated-set acceptance.
- `software/tests/test_check_cmyk_wave_spacing.py`: row-lock manifest tests.
- `samples/gcode/Ben2/*`: active row-locked canonical set and manifest.
- `docs/research/2026-10-30-row-locked-bed-compensation.md`: feasibility and
  retained-energy evidence.
