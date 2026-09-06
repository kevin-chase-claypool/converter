---
id: WSW-20260905-003
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - docs/integration/IOSENDER_CONVERTER_COMPATIBILITY_REVIEW.md
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
  - firmware/grblhal/macros/P100.macro
tags:
  - iosender
  - grblhal
  - gcode
  - p100
  - integration-review
related:
  - WSW-20260905-002
  - F-02
  - F-05
  - M-06
---

# Record ioSender-to-converter compatibility review

## Summary

Recorded an evidence-based compatibility review for the desired workflow:
convert SVG, run `G65 P100 Q0` in ioSender, then stream the drawing without
manual G-code edits.

## Reason

The project requires a self-contained converter program and a commissioned
controller/toolhead state before direct streaming is safe. Documentation had
not yet collected the current converter defaults, P100 gates, parser evidence,
and rotary-feed validation risk in one review.

## Implementation

Added `docs/integration/IOSENDER_CONVERTER_COMPATIBILITY_REVIEW.md`, linked
from the documentation map. It compares emitted G-code against ioSender and
grblHAL documentation, repository parser evidence, P100 source, installed
build configuration, and outstanding machine tests.

## Verification

- Inspected the converter's actual default output: it emits `G0 Z5` and
  `G1 Z0`, not M3/M5, because `Use Z axis` defaults enabled.
- Inspected `P100.macro`: Q0 is deliberately locked with
  `#<commissioned> = 0`.
- Inspected the installed baseline build configuration: `PROBE_ENABLE=0`, while
  P100 requires probing and macro/NGC capabilities.
- Consulted official ioSender and grblHAL sources for sender role, supported
  G-code, G94 mode, and rotary-feed configuration history.

## Struggles and rejected approaches

Treating ioSender as a layer that can repair missing modal commands or disabled
controller features was rejected. ioSender streams the program; the converter
must establish its own modes and the controller/toolhead commissioning gates
must pass independently.

## Risks and follow-up

Do not enable direct P100-to-print operation yet. Required follow-up is to
correct the converter's M3/M5 default and self-contained preamble, rerun the
parser dry run, commission P100/toolhead gates, complete X calibration, and
run M-06 combined-motion validation.

## Files

- `docs/integration/IOSENDER_CONVERTER_COMPATIBILITY_REVIEW.md`: canonical
  compatibility evidence and readiness checklist.
- `docs/README.md`: links the review from the documentation map.
- `docs/project/ROADMAP.md`: records the newly discovered converter preamble
  task and direct-print gate.
