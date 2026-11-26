---
id: WSW-20261126-010
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode_overlay.py
  - software/converter_core/__init__.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_gcode_overlay.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - gcode
  - overlay
  - post-save
  - bounding-envelope
  - identity
  - audit
  - visualization
---

# Add a post-save CMYK G-code overlay audit

## Summary

After CMYK G-code files are written, the converter reads all selected programs
back from disk and creates a common-frame PNG overlay plus a JSON audit report.
The audit checks the saved files, rather than only the in-memory planning
results.

## Reason

The planner now validates CMYK set identity before Save, but the operator still
needed a direct post-publication view of the actual files. A shared header can
prove frame/profile identity without showing whether the emitted X/Y paths
occupy the expected common envelope.

## Implementation

- `write_cmyk_gcode_overlay()` parses pen-down `G1` segments and re-runs
  `analyse_gcode()` on every saved ink file.
- The saved programs are revalidated through `validate_program_set_identity()`
  against the current frame center, compensation profile, reach, and expected
  Wave row angles.
- A 1400-pixel machine-frame PNG renders all four inks together with the raw
  reach circle, effective planning circle, center axes, and per-ink bounding
  boxes. Dense paths are stride-decimated only for drawing; metrics use every
  parsed segment.
- A JSON report records pass/fail, identity, errors, per-ink bounds, centers,
  maximum radii, ink envelopes, row angles, and source paths.
- CMYK Save generates `<name>-overlay.png` and `<name>-overlay.json` after
  writing the G-code, reports PASS/BLOCKED in the UI/log, and includes the
  overlay report in `<name>-set.json`.
- Calibration-sheet saves retain their existing calibration manifest and do not
  use the artwork overlay path.

## Verification

- Overlay tests generate four real G-code files, confirm PASS, verify the
  rendered PNG and JSON, and confirm all four inks are audited.
- A mismatched frame still produces a diagnostic overlay but marks the audit
  BLOCKED and records the mismatch.
- The CMYK set-manifest regression verifies the overlay report is embedded and
  the expected PNG/JSON artifacts exist.
- The complete affected CMYK, generator, reach, identity, and overlay modules
  pass `162` tests with one expected OpenGL-context skip. Complete converter
  discovery passes `642` tests with one expected OpenGL-context skip, and
  Python compilation passes.

## Struggles and rejected approaches

Reusing the live OpenGL preview was rejected because it can show nominal or
pre-save coordinates and does not prove what reached disk. Drawing only the
headers was rejected because registration crosses and path extents need a
visual check. Requiring identical ink bounding boxes was rejected because CMYK
plates intentionally contain different coverage; the shared frame and target
envelope are the correct invariants.

## Risks and follow-up

The PNG is a host-coordinate diagnostic, not evidence of physical overlay
registration or pen-seat alignment. It cannot model bed-angle error, paper
movement, pen spread, or re-registration between files. Plot all four files
after one P100 registration for physical verification.

## Files

- `software/converter_core/gcode_overlay.py`: saved-file parser, identity
  audit, metrics, PNG renderer, and JSON report.
- `software/converter_core/__init__.py`: public converter export.
- `software/generator_tabs/cmyk_tab.py`: post-save overlay execution, status,
  and manifest linkage.
- `software/tests/test_gcode_overlay.py`: pass and mismatch overlay
  regressions.
- `software/tests/test_cmyk_tab.py`: Save integration and manifest coverage.
- `software/README.md`: current post-save artifacts and interpretation.
- `docs/project/ROADMAP.md`: software-overlay completion and remaining physical
  validation boundary.
