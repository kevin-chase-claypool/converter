---
id: WSW-20261127-001
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode_registration.py
  - software/converter_core/gcode_overlay.py
  - software/converter_core/gcode.py
  - software/converter_core/geometry.py
  - software/converter_core/cmyk.py
  - software/converter_core/motion_check.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_gcode_overlay.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - gcode
  - registration
  - fiducial
  - overlay
  - pen-offset
  - compensation-inversion
  - save-guard
  - manifest
  - physical-validation-pending
related:
  - WSW-20261126-010
  - WSW-20261126-014
  - ADR-009
  - ADR-013
---

# Gate CMYK release on pointwise G-code registration

## Summary

CMYK artwork sets now contain four named corner crosses and a hard
software-registration gate. Save analyzes the final emitted `G1` points,
recovers each mark in the bed frame by reversing `A` and bed compensation,
removes the declared per-ink pen offset, and compares matched mark centres
across inks.

A set is blocked before any target file is written if marks are missing or
duplicated, IDs/counts differ, translation/rotation/scale geometry disagrees,
pen offsets are not applied exactly once, or the shared G54/compensation/
planning-radius/final-scale/A-schedule identity differs. The written files are
then read back from disk and audited again before Save can report success.

The pass report is labelled **software registration PASS**. A physical
four-pen overlay remains pending and separate.

## Reason

A physical CMYK set showed yellow and magenta shifted and cyan about `10 mm`
off. The saved file set had registration crosses disabled. The prior overlay
audit passed because it checked only program identity, G54 frame, reach,
hashes, gross bounds, and centres; it could not distinguish a whole-program
translation from pointwise alignment.

## Implementation

- Added `RegistrationMarkTrail` and SVG data attributes so stable mark IDs,
  pre-offset centres, arm identity, and pen offsets survive parsing, Y flip,
  scale, page-frame placement, clipping, planning, and G-code emission.
- Emit named horizontal/vertical arm comments into final G-code. New common
  headers record final fitted scale and an A-planning identity digest derived
  from the shared theta mode, ratio, limits, resolver, smoothing, hold, wrap,
  and row-order settings.
- Added `gcode_registration.py`, which parses pen-down moves between `M3` and
  `M5`, divides motor-shaft `A` by the emitted theta ratio, inverts the active
  row-locked or raw compensation transform, and combines arm midpoints.
- Require four non-collinear mark IDs, identical ID sets in every selected ink,
  and one shared G54/profile/reserve/planning-radius/final-scale/A-schedule
  identity.
- Reject a software maximum residual over `0.10 mm` or RMS over `0.05 mm`.
  Translation is limited directly by `0.10 mm`; rotation and scale limits are
  derived from `0.10 mm` at the measured corner radius. This is 11 % of the
  current `0.90 mm` pen and tighter than the verified physical compensation
  field's approximately `0.218 mm` RMS / `0.591 mm` maximum.
- Check each declared pen offset against both configured metadata and one
  application in recovered geometry.
- Run registration/identity preflight before export and repeat the full audit
  from the written files. A post-write failure marks the save as failed rather
  than success while preserving the files for diagnosis.
- Advance set manifests to version 6 and record `registration_audit`,
  `software_registration_passed`, `physical_overlay`, and per-ink matched
  count, centroid, translation, rotation, scale, RMS, maximum residual,
  pen-offset error, and pass/fail.
- Extend the PNG overlay with recovered common-frame mark centres and residual
  vectors.
- Enable corner crosses by default. Calibration sheets retain their separate
  fiducial workflow and are not subject to the artwork-set gate.

## Verification

- Added a red regression that reproduced the old false PASS with cyan
  translated by `10 mm`; the new gate rejects it.
- Matching fixed-bed and rotating-bed four-ink sets recover four common marks
  and pass, including inversion of the default bed-compensation profile.
- Regressions reject `0.10 deg` rotation, `0.1 %` scale, a changed mark
  identity, a double-applied `0.75,-0.20 mm` pen offset, and missing marks.
- A correctly applied single pen offset still passes.
- Save integration verifies that missing registration geometry blocks before
  export and that post-write corruption produces `Save verification FAILED`.
- Set-identity tests verify final-scale and A-schedule mismatches are rejected.
- The focused CMYK suite passes `132` tests.
- Complete converter discovery passes `681` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Comparing all drawing paths was rejected because each ink intentionally has
  different image content and mark counts.
- Comparing only bounding boxes or centroids was rejected because unequal ink
  coverage and whole-program translation can look identical in those metrics.
- Trusting header identity alone was rejected; the pass now depends on parsed
  final movement geometry after transform inversion.
- Using the prior `1.21 mm` Wave pitch or changing waveform period would not
  address a whole-program `10 mm` shift.

## Risks and follow-up

- This is software-command geometry, not paper measurement. Pen-tip offsets,
  sheet motion, bed flatness, contact pressure, ink spread, and physical overlay
  remain unverified.
- The `0.10 mm` software bound is intentionally tighter than the current
  physical residual; a software pass cannot be promoted to a physical claim.
- Fresh files from this commit or later must run with one `G65 P113` HOME +
  REGISTER and no re-registration or sheet shift between passes. Start with an
  XY-only four-pen comparison, then repeat on the rotating-bed Wave job.
- The default compensated outer annulus remains physically unverified.

## Files

- `software/converter_core/gcode_registration.py`: mark parsing, compensation
  inversion, common-frame comparison, tolerances, and audit report.
- `software/converter_core/gcode_overlay.py`: combined identity/registration
  report and residual-vector visualization.
- `software/converter_core/geometry.py`,
  `software/converter_core/cmyk.py`: registration mark tags and SVG round trip.
- `software/converter_core/gcode.py`,
  `software/converter_core/motion_check.py`: mark comments, final-scale and
  A-schedule headers, and identity validation.
- `software/converter_core/settings.py`,
  `software/generator_tabs/cmyk_tab.py`: default-on crosses, pre-write gate,
  post-write re-audit, manifest v6, and failure reporting.
- `software/tests/test_gcode_overlay.py`,
  `software/tests/test_cmyk_tab.py`,
  `software/tests/test_program_set_identity.py`,
  `software/tests/test_generator_tabs.py`,
  `software/tests/test_theta_feed.py`: regressions and updated G-code contract.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`,
  `docs/decisions/ADR-013-gcode-registration-gate.md`,
  `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`, and generated
  change indexes: current behavior, decision, verification, and pending
  physical test.
