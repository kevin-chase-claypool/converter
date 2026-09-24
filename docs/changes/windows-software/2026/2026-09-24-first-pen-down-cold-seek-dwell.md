---
id: WSW-20260924-013
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
tags:
  - converter
  - pen-dwell
  - cold-seek
  - gp2
  - first-plot
---

# Give the program's first pen-down a cold-seek dwell

## Summary

Added `Pen down first ms` (`pen_down_first_ms`, default 10000). The converter
now emits a longer `G4` after the program's **first** `M3` and keeps the
existing `Pen down ms` (3500) for every later pen-down, so grblHAL no longer
begins the first stroke while the pen is still descending.

## Reason

The toolhead parks on the GP2 lift switch. On power-up it drives up for up to
`BOOT_LIFT_TIME_MS` (3000 ms) until GP2 asserts, and `M5` never brings it back
down: `CLEARANCE_LIFT` short-circuits straight to `LIFTED` whenever GP2 is
already active. So a plot begins with the pen fully retracted, and the first
`M3` takes the toolhead's **cold** path — 25 ms coarse pulses, a
`HOME_RELEASE_TARE_SETTLE_MS` (1000 ms) release-tare wait, a full 64-sample
tare, then the rest of the approach. Measured at about 7 s on the installed
mechanism.

The converter's dwell was a flat 3500 ms for every `M3`. That covers the warm
seek (2-3 s from the ~1 mm `M5` clearance) but not the cold one, so the
controller expired the dwell and started the first draw move roughly 3-4 s
before contact. At the 700 mm/min default feed that is about 40-50 mm of path
drawn in the air, which is what the operator saw as "a big chunk of print XYA
movement has already occurred."

Only the first pen-down is affected. Every later `M5` lifts just
`PEN_CLEAR_EXTRA_LIFT_MS` (57 ms, about 1 mm), so subsequent `M3` seeks are
warm and fit inside the existing dwell.

## Implementation

- `settings.py`: new `pen_down_first_ms: float = 10000.0`, validated as
  non-negative and exposed as the **Pen down first ms** field in the Pen group.
- `gcode.py`: new `pen_down_first_duration_ms(settings)`; `append_pen_dwell`
  takes `is_first_down`; `contours_to_gcode` and `build_preview_moves` each
  track a `first_pen_down_pending` flag so the emitted program and the preview
  timeline agree.
- The GP27 `G65 P115` handshake path is untouched: it returns before any dwell
  is appended, so the new value cannot affect it.

The 10000 ms default is the measured ~7 s plus margin for the release-tare
settling, the hold acquisition, and the pen-clamp position changes that alter
the retract distance. It is a fixed open-loop delay, not an acknowledgment;
the `P115` handshake is still the eventual replacement.

## Verification

- `python -m unittest discover -s software\tests` — 22 tests pass.
- Default settings, two-contour input, emitted G-code starts the first stroke
  with `M3` / `G4 P10` / `G1 F700` and the second with `M3` / `G4 P3.5`.
- `build_preview_moves` reports `pen_down` durations of 10000 ms then 3500 ms,
  matching the emitted program.
- `settings_from_values({"pen_down_first_ms": "8000"})` round-trips to 8000.0.
- Bench confirmation is outstanding: the first stroke of a real plot must
  begin on paper with no leading air-drawn segment.

## Struggles and rejected approaches

Doubling `pen_down_ms` for the whole program was rejected — it would add the
cold-seek margin to every one of the hundreds of strokes in a filled drawing.
A program-opening `M3`/`M5` warm-up pair was also considered; it costs the same
wall time as the longer first dwell and adds two more toolhead transitions
without improving the outcome.

## Risks and follow-up

- The 10000 ms figure is open-loop. If a future pen clamp or carriage change
  lengthens the cold travel beyond it, the leading segment goes airborne
  again. The real fix is the `P115`/GP27 acknowledgement, which removes the
  fixed dwell entirely.
- Starting a program with the pen already off GP2 wastes the extra first-dwell
  time. That is a one-off cost, not a correctness problem.
- Related open firmware item: the cold path is the one approach where
  `coarse_phase` runs unconditionally with no force gate until GP2 releases,
  which makes the first pen-down both the slowest and the least-protected
  approach in the controller.

## Files

- `software/converter_core/settings.py`: new setting, UI field, validation.
- `software/converter_core/gcode.py`: first-pen-down dwell in program and preview.
- `software/README.md`: documented the setting and its 3500/10000 split.
