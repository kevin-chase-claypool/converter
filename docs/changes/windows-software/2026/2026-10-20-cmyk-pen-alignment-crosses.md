---
id: WSW-20261020-002
date: 2026-10-20
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_cmyk_pen_alignment.py
  - samples/gcode/cmyk-pen-alignment.gcode
tags:
  - cmyk
  - alignment
  - pen-offset
  - diagnostic
related:
  - WSW-20261020-001
---

# CMYK pen-alignment crosses: one file run once per pen

## Summary

New generator `tools/make_cmyk_pen_alignment.py` and sample
`samples/gcode/cmyk-pen-alignment.gcode`: five 10 mm crosses (centre and
four corners at +-75 mm) drawn with the bed parked at A = 0. Run the same
file unchanged once per CMYK pen on one sheet; coincident crosses mean the
pens share a tip offset, and per-pen gaps are the XY offsets that the single
stored P100 pen offset cannot correct.

## Reason

The 2026-10-20 CMYK misalignment investigation separated saved-file framing
(fixed with the shared page frame) from physical pass-to-pass offsets. The
CMYK layers themselves cannot measure the remaining pen effect: each ink is
a different screen angle and tone map, so comparing yellow and magenta
strokes is not a registration check. The four corner crosses are a shared
landmark, but the artwork print also has per-ink content around them; a
dedicated same-file cross test isolates the pen/machine offset alone.

## Implementation

- `tools/make_cmyk_pen_alignment.py` emits the five crosses with the
  standard M3/M5 and GP27 handshakes, constant A = 0, the usual full-retract
  trailer and park-home move.
- Stations: centre, top-left, top-right, bottom-left, bottom-right at
  +-75 mm; each cross has 10 mm arms; maximum radius 109.7 mm.
- Self-checks: balanced parentheses, ten strokes, all A values 0, radius
  within the configured reach.

## Verification

- Generator self-checks pass (`10 strokes, A constant at 0.0, max radius
  109.7 mm`).
- `python tools\check_gcode_motion.py samples\gcode\cmyk-pen-alignment.gcode
  --strict` passes: 0 deg bed rotation, 0 A rate, no pen-up rotation.

## Struggles and rejected approaches

- Rejected using the CMYK artwork layers for this measurement: per-ink
  screen angles and tone maps make stroke comparison meaningless, and the
  framing fix now guarantees a shared frame, so the remaining unknown is the
  pen tip position.

## Risks and follow-up

- The test measures XY tip offset at five points; a rotated pen (angled
  seat) shows as a rotation rather than a translation. Paper or tape
  movement between pens also contaminates the result, so keep the sheet
  untouched.
- If per-pen gaps are consistent, the next step is either repeatable pen
  seating or per-ink XY offsets in the CMYK tab. Bench run pending.

## Files

- `tools/make_cmyk_pen_alignment.py`: generator and self-checks.
- `samples/gcode/cmyk-pen-alignment.gcode`: the generated test program.
- `software/README.md`: listed with the machine-measurement programs.
