---
id: WSW-20261126-012
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/converter_core/gcode_overlay.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - row-lock
  - preflight
  - save-guard
  - user-interface
  - pen-offset
related:
  - WSW-20261030-003
  - WSW-20261126-010
  - ADR-009
---

# Block saves that do not guarantee Wave row pitch

## Summary

The CMYK tab now shows a conspicuous red, amber, or green row-pitch status
beside the Wave controls. Save is blocked before planning when the selected
configuration cannot preserve equidistant rows. The final G-code is also
checked for the required row-locked projection and shared row-angle headers.
Saving a deliberate nonuniform comparison now requires an explicit diagnostic
override.

## Reason

A printed legacy Wave screen crowded visibly even though the selected bed mesh
was active. The saved job used `waves_zero`, raw bed compensation, and no shared
A schedule. The UI showed only a muted pass-summary sentence, allowed Save, and
then reported a green identity/reach overlay as `PASS`. Nothing in that path
checked the user's actual requirement: uniform Wave rows.

The same preflight exposed a second defect: applying a per-ink pen offset
rebuilt Wave contours as plain lists, discarding `data-wave-row`. That silently
disabled the shared A schedule for the offset ink.

## Implementation

- The Screen group has a styled **Row-pitch status**:
  - green only for production equidistant rows, row-lock compensation, and a
    shared rotating-bed row order;
  - red for legacy Wave, disabled spacing guard, or planner-optimized row
    order;
  - amber only after the operator enables the nonpersistent diagnostic
    override.
- Save rejects an unsafe Wave configuration before starting the background
  planner. Final-analysis and write-time preflight repeat the check.
- Generated G-code must contain `row-locked projection` when compensation is
  active and `shared Wave row angles` when the bed rotates. Missing headers
  block Save.
- Pen-offset translation uses the original contour type, preserving
  `WaveTrail.wave_row_index` through the layer rebuild.
- The set manifest records `row_pitch_preflight` with `enforced`,
  `diagnostic_override`, `blocked`, or `not_applicable` status.
- The overlay audit is now labelled **identity/reach** and records its explicit
  scope. Its PASS no longer implies row-spacing validation.

## Verification

- New regressions cover the red legacy state, pre-planning Save rejection,
  explicit amber diagnostic override, green equidistant state, missing G-code
  row-lock headers, Wave-tag preservation through pen offsets, and manifest
  status.
- The affected CMYK, overlay, rotating-row, and spacing modules pass 123 tests.
- The complete converter suite passes 648 tests with one expected OpenGL skip.
- Offscreen UI inspection shows the Row-pitch status as a full-width red or
  green panel, with the diagnostic checkbox visible only for unsafe output.

## Struggles and rejected approaches

- Leaving the old pass-summary sentence as the only warning was rejected; it
  was visually indistinguishable from ordinary preflight status.
- Treating the identity/reach overlay as a spacing result was rejected because
  that audit never measures row gaps.
- Running the full final-coordinate spacing checker synchronously on every Save
  was rejected as too expensive for the interactive workflow. The UI instead
  proves the row-lock contract in the emitted headers; the existing checker
  remains the measured final-coordinate audit.
- Allowing legacy output without an explicit override was rejected because it
  makes the known nonuniform path the silent default.

## Risks and follow-up

- The green UI status proves the configured and emitted row-lock contract. It
  is not a physical pitch measurement, and mechanical A-axis error remains
  possible.
- The diagnostic override intentionally permits nonuniform rows and should be
  used only for controlled comparisons.
- The measured spacing checker remains the authoritative final-coordinate
  audit before a production comparison print.

## Files

- `software/generator_tabs/cmyk_tab.py`: visible status, save guard, final
  G-code validation, manifest record, and Wave-tag preservation.
- `software/converter_core/gcode_overlay.py`: explicit identity/reach audit
  scope and title.
- `software/tests/test_cmyk_tab.py`: regression coverage for all new states and
  the pen-offset tag defect.
- `software/README.md`: current operator workflow and status meanings.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification record.
