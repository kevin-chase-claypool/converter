---
id: WSW-20261122-001
date: 2026-11-22
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
tags:
  - cmyk
  - registration
  - row-lock
  - bed-compensation
  - shared-translation
  - g54
  - p100
related:
  - WSW-20261030-003
  - ADR-009
  - docs/research/2026-10-30-row-locked-bed-compensation.md
---

# Normalize CMYK row-lock translation across all four inks

## Summary

CMYK Wave files now remove the angle-specific global translation of each
row-locked bed-compensation projection on one deterministic common domain.
All four inks substitute the same zero translation. They retain the same G54
frame, their intentional `15/75/0/45 deg` screen angles, and their
position-varying along-row correction.

The CMYK worker prepares the complete four-angle projection set once, before
planning any ink, and passes the matching immutable projection into each
layer. A saved set manifest records the normalization domain, raw per-angle
means, the common zero vector, and why P100 remains authoritative.

## Reason

Every file already selected the same controller-registered G54 frame. The
defect was inside the default row-lock transform: evaluating the same measured
field on four different screen axes produced different spatial mean vectors.
Identical paper coordinates therefore received different final machine
coordinates.

On the supplied default profile `f85ec410dbac`, the old parked-bed emission
regression measured a `0.059483 mm` cyan-to-yellow centroid separation on an
identical common-domain point set. Disabling compensation or sharing the raw
profile made the separation zero but did not meet the row-lock requirement.

## Implementation

- `RowLockedBedCompensation` normalizes every measured bed-angle slice on a
  deterministic 65-by-65 bed-frame grid clipped to the compensation coverage
  disk.
- The raw projection mean is subtracted independently for each ink slice.
  The added common vector is `(0, 0)`.
- Zero is intentional. The calibration fiducial fit already removed common
  sheet translation; restoring the arithmetic mean of four projections would
  add a joint translation that P100 already owns.
- `row_locked_bed_compensation_set()` builds all four screen-angle projections
  once, independent of channel processing order.
- The row-lock state is immutable derived data passed through internal
  settings, excluded from settings persistence and comparison. G-code planning
  validates its profile fingerprint and screen angle before use.
- Translation normalization applies a constant per angle and ink. It therefore
  cannot change adjacent-row distance within a projected field.

This change does not alter P100 registration, G54, controller motion, A-axis
calibration, pen geometry, or the input profile.

## Verification

- The new emission regression failed before the fix at `0.059483 mm` and now
  holds cyan/magenta/yellow/black means within `0.0002 mm` on the same point
  set. The remaining difference includes three-decimal G-code quantization.
- An independent default-profile audit measured normalized correction means
  below `3e-15 mm` at every measured bed angle on the common domain.
- `test_wave_x_theta_rows.py` exercises both XY-only and Xθ/Yθ output, all four
  CMYK screen angles, both ascending and descending row order, with and
  without the default compensation profile. Every adjacent-row spread remains
  `<= 0.005 mm`.
- Raw shared-profile output remains byte-identical across the four screen-angle
  settings.
- Building the four-angle projection set from reversed input order produces
  the same per-angle fingerprints.
- The saved manifest version is now 4 and records `shared_zero_mean`
  normalization rather than only the legacy row-lock mode.
- The focused bed-compensation, CMYK-tab, rotating-row, and manifest-checker
  suites pass 158 tests. The complete converter discovery suite passes 623
  tests with one expected OpenGL-context skip. Documentation indexing and link
  validation pass for all 508 change notes.

Software-only cross measurements on four software corner crosses at
`(+/-75, +/-75) mm` are:

| Ink | Old correction centroid mm | Normalized centroid mm |
|---|---|---|
| C | `(0.209524, 0.098000)` | `(0.029121, -0.042789)` |
| M | `(-0.043377, 0.231899)` | `(-0.007348, 0.006409)` |
| Y | `(0.198440, 0.075544)` | `(-0.012840, -0.014403)` |
| K | `(0.103333, 0.236177)` | `(0.019470, 0.024378)` |

The normalized correction fields still differ locally. Relative to yellow,
the remaining default-profile local RMS/max differences are:

- Cyan: `0.125914 / 0.443952 mm`.
- Magenta: `0.328551 / 0.753089 mm`.
- Black: `0.219316 / 0.533614 mm`.

These are not overlay residuals measured on paper; they show why this milestone
must not be described as complete local warp or full four-ink overlay
correction.

## Struggles and rejected approaches

Per-channel planning could not determine a shared translation without
duplicating all four expensive projections or depending on processing order.
The implementation therefore prepares all four normalized projections once.

Adding the arithmetic mean of the four raw means was rejected because it would
move the whole CMYK set relative to P100 even though the profile fit already
removed common registration translation. Disabling row-lock compensation,
changing G54, or adding a fixed job offset would either lose the compatible
bed correction or violate the established registration ownership.

## Risks and follow-up

The common translation removes only the systematic per-ink global XY
translation. It does not remove all local differences between the four
projected fields. The measured local residual above remains a physical overlay
risk.

A fresh four-file set with registration crosses must be generated in a new
converter process and run after one HOME + REGISTER without re-registration.
The physical test must compare the old and normalized sets, record the four
cross centroids, adjacent-row quality, and residual local distortion, and must
not claim full local correction unless those measurements support it.

## Files

- `software/converter_core/bed_compensation.py`: common-domain normalization,
  deterministic projection set, and metadata.
- `software/converter_core/gcode.py`: prepared-projection validation and header.
- `software/converter_core/settings.py`: internal immutable handoff field.
- `software/generator_tabs/cmyk_tab.py`: once-per-set preparation and manifest
  metadata.
- `software/tests/test_bed_compensation.py`: red-green emission regression,
  deterministic order, raw behavior, and common-domain means.
- `software/tests/test_cmyk_tab.py`: worker set preparation and manifest tests.
- `software/tests/test_wave_x_theta_rows.py`: compensated fixed-bed/Xθ-Yθ row
  quality coverage.
- `tools/check_cmyk_wave_spacing.py`: version-4 manifest validation for the
  common zero translation.
- `software/tests/test_check_cmyk_wave_spacing.py`: manifest normalization
  regression.
- `software/README.md`: current shared-translation behavior and limits.
- `docs/decisions/ADR-009-post-registration-bed-compensation.md`: architecture
  decision update.
- `docs/research/2026-10-30-row-locked-bed-compensation.md`: cross-channel
  diagnosis and normalization analysis.
- `docs/report/lab-notes/2026-11-22-cmyk-shared-row-lock-translation-software.md`:
  software geometry evidence and pending physical protocol.
- `docs/project/ROADMAP.md`: implementation status and remaining physical gate.
- `docs/project/ENGINEERING_LOG.md`: diagnosis and implementation event.
