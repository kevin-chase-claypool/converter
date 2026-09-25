---
id: WSW-20260925-002
date: 2026-09-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
tags:
  - converter
  - pen-dwell
---

# Lower the pen-down dwell default to 2500 ms

## Summary

`pen_down_ms` default changed from 3500 ms to 2500 ms, matching the faster warm
seek on the installed carriage.

## Implementation

- `settings.py`: `pen_down_ms` default 3500 -> 2500 and the UI field default.

## Verification

- The 24 converter tests pass (they set `pen_down_ms` explicitly where it
  matters).

## Files

- `software/converter_core/settings.py`
- `software/README.md`
