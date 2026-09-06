---
id: WSW-20260905-006
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - gcode
  - validation
  - safety
  - iosender
related:
  - WSW-20260905-002
  - WSW-20260905-003
  - F-02
  - M-06
---

# Make the production preview safe and complete

## Summary

Removed the XY-only preview/export mode, made the command pane display the
complete generated program, and added conversion preflight validation.

## Reason

The prior "Preview mode: omit theta axis" setting also removed `A` words from
saved G-code, which was inappropriate for a production X/Y/A plotter. The
preview command pane was a shortened reconstruction rather than the exact file
that Save G-code writes. The review also found that invalid motion or bed
geometry values could reach conversion without a clear early error.

## Implementation

- Removed the XY-only mode from the settings, UI, preview, and G-code paths.
  All production programs retain planned A-axis motion.
- The preview worker now generates the same complete G-code text used by Save
  G-code. The command pane displays that text, including modal setup, comments,
  M3/M5 commands, G4 dwells, and M2; preview moves map back to their matching
  program lines for playback selection.
- Core validation rejects invalid rates, scale, tolerance, A ratio/name, bed
  dimensions, margins, delays, and non-finite values before preview or export.
- The runtime display now uses planned draw duration rather than the visual
  playback-speed setting. Rapid timing remains explicitly marked as an estimate
  until M-06 verifies installed grblHAL rapid behavior.

## Verification

- `python -m unittest discover -s software\tests -v`
- Generated the three representative SVG inputs and confirmed finite,
  self-contained X/Y/A programs with M3/M5 and M2.
- `python tools\docs_index.py --write`
- `python tools\docs_index.py --check`

## Struggles and rejected approaches

Keeping the XY-only option as a hidden viewer convenience was rejected because
its output could be saved and streamed accidentally. A separate viewer export
could be considered later, but it is not part of the production converter.

## Risks and follow-up

The preview is now a complete program representation, but it is not a motion
controller simulator. F-02 and M-06 remain the required installed-controller
checks; rapid timing in particular must not be treated as measured evidence.

## Files

- `software/converter_core/settings.py`: production-setting validation and mode removal.
- `software/converter_core/gcode.py`: always emit planned A-axis words.
- `software/qt_svg_to_gcode.pyw`: complete command listing and controller-time estimate.
- `software/tests/test_theta_feed.py`: production-output and validation coverage.
- `software/README.md`: current converter operation and timing guidance.
