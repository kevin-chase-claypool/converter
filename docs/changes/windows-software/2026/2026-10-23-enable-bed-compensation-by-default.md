---
id: WSW-20261023-005
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/svg_to_gcode.pyw
  - software/tests/test_bed_compensation.py
  - samples/gcode/bed-error-compensation-2026-10-23.json
tags:
  - bed
  - compensation
  - defaults
  - planner
  - profile
related:
  - WSW-20261023-004
  - ADR-009
---

# Enable verified bed compensation by default

## Summary

The desktop converter now starts with the bench-verified bed-compensation
profile selected. The Machine-tab path remains editable, **Browse...** selects
a replacement profile, **Default** restores the verified profile, and clearing
the path explicitly disables compensation.

## Reason

Profile `2cdf3731de4a` passed the independent M-12 verification and is the
current calibration for the installed machine. Requiring the operator to
select the same JSON after every application start made it easy to save an
uncompensated program unintentionally.

## Implementation

- Added `DEFAULT_BED_COMPENSATION_PATH`, resolved from the repository location
  rather than the process working directory, so launching the converter from
  another folder still finds the shipped profile.
- The Machine group initializes **Bed compensation JSON** to that path, making
  the verified correction part of normal GUI planning without changing the
  shared planner or grblHAL.
- Added a **Default** button beside **Browse...** so a deliberately selected
  alternate profile can be reverted without restarting the application.
- Updated the plain command-line shim to start from `default_settings()`, which
  includes the same verified profile.
- Low-level `Settings()` construction remains uncompensated unless a caller
  supplies a path; this preserves explicit test and diagnostic planning while
  the application and CLI defaults apply the verified calibration.

## Verification

- The two new regression tests confirm that the Machine-field defaults load
  profile fingerprint `2cdf3731de4a`, emit its header in normal G-code, and
  that an explicitly empty path still emits no compensation.
- `py -m unittest discover -s software\tests -p "test_bed_*.py" -v` ran 25
  tests successfully.
- The full suite `py -m unittest discover -s software\tests -v` ran 482 tests
  with one OpenGL-context skip.

## Struggles and rejected approaches

- Changing the `Settings()` dataclass field itself to the profile path was
  rejected because many low-level diagnostic tests intentionally construct an
  uncompensated planner. The application default belongs at the UI/CLI entry
  point, where operators normally begin.
- A repository-relative display path would fail when the app is launched from
  another working directory. The default is resolved from the installed
  repository location; a browsed replacement remains an absolute path.

## Risks and follow-up

- The default profile is valid only for the bed, paper support, carriage,
  toolhead, pen clamp, and P100 registration that produced the accepted M-12
  verification. Browse to a newly measured profile after any relevant change.
- If the shipped profile is missing, planning reports the existing explicit
  profile-read error instead of silently producing an uncompensated program.
- The specialized Kaleidoscope application is unchanged; this default applies
  to the main desktop converter, its generator tabs, and the command-line
  shim.

## Files

- `software/converter_core/settings.py`: verified default path, editable field
  default, and production `default_settings()`.
- `software/qt_svg_to_gcode.pyw`: Default reset button and companion method.
- `software/svg_to_gcode.pyw`: command-line entry point uses production
  defaults.
- `software/tests/test_bed_compensation.py`: default-on and explicit-off
  regressions.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`: current
  configuration and replacement/disable instructions.
