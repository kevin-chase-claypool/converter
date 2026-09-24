---
id: WSW-20260923-003
date: 2026-09-23
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core
tags:
  - gcode
  - pen-plot
  - defaults
  - toolhead
related:
  - WSW-20260923-002
  - RPSW-20260923-016
---

# Set converter defaults for the installed toolhead

## Summary

The converter's default feed rate, theta tangential speed, and pen-up/down
dwells now match the installed Theta toolhead, so a fresh conversion produces a
usable file without hand-editing settings.

## Reason

The shipped defaults were placeholders. `pen_down_ms` was 600 ms, but the
toolhead's M3 seek takes about 1.2 s warm and ~2.9 s from GP2, so the drawing
move fired while the pen was still descending and nothing was drawn before the
M5 retracted. `pen_up_ms` was 300 ms against an M5 that takes ~0.46 s. The
1200 mm/min feed also disturbed the force hold on long strokes.

## Implementation

- `settings.py`: `feed_rate` 1200 -> 700, `theta_tangential_speed_mm_min`
  1200 -> 700, `pen_up_ms` 300 -> 800, `pen_down_ms` 600 -> 3500, in both the
  `Settings` dataclass and the `TEXT_FIELD_GROUPS` UI defaults.

The dwells are sized for this toolhead's measured actuation; a different
toolhead or actuator would need its own values.

## Verification

- A fresh `Settings()` now reports feed 700, tangential 700, up 800, down 3500,
  expand-strokes off, and the generated program uses `G4 P0.8` / `G4 P3.5`.
- `test_coordinate_frames.py` (3 tests) and `test_theta_feed.py` (19 tests)
  pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

Leaving the defaults short and requiring per-job edits was rejected: every fresh
conversion would silently produce a non-drawing file. Sizing `pen_down_ms` to
cover only the warm seek (~1.2 s) was also rejected, because the first stroke of
a job starts from GP2 and needs the cold time.

## Risks and follow-up

`pen_down_ms` of 3500 ms is generous; with the centerline fix the sample is only
about 20 pen-down strokes, so it costs roughly a minute. The probe-based GP27
handshake (`P115`) would replace these fixed dwells with the actual actuation
completion once commissioned.

## Files

- `software/converter_core/settings.py`: default values and UI field defaults.
