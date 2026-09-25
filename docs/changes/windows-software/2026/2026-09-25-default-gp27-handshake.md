---
id: WSW-20260925-001
date: 2026-09-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
tags:
  - converter
  - gp27
  - handshake
---

# Default the GP27 handshake on

## Summary

`toolhead_status_handshake` now defaults to `true`, so the converter emits the
`G65 P115` acknowledgement macro after each M3/M5 transition instead of the
fixed `G4` dwells, without the operator ticking the checkbox.

## Reason

The handshake was validated on the commissioned machine (P115.macro installed,
GP27/U3-to-PRB wired, toolhead `GP27_NORMAL_STATUS_ENABLED` true), so keeping it
opt-in was a needless extra step.

## Implementation

- `settings.py`: `toolhead_status_handshake` default `false -> true`, and the
  UI checkbox default set to checked.

## Verification

- The 24 converter tests pass (two M-06 pen-free tests were updated to opt out
  explicitly, since they use empty pen commands).
- A default `Settings()` program emits `G65 P115 Q0` after the opening M5 and
  `G65 P115 Q1` after subsequent M3/M5 transitions.

## Risks and follow-up

- The program now depends on `P115.macro` being present on the RP23CNC and the
  GP27 wiring being intact; if either is missing, prints error `39`. Unchecking
  the box restores the fixed-dwell fallback.

## Files

- `software/converter_core/settings.py`
- `software/README.md`
- `software/tests/test_theta_feed.py`
