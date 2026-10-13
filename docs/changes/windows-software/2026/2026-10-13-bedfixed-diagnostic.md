---
id: WSW-20261013-011
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - samples/gcode/heraldic-bedfixed.gcode
tags:
  - a-axis
  - diagnostic
  - outline
  - fixed-bed
related:
  - WSW-20261013-010
  - WSW-20261013-009
---

# Bed-fixed full-plot diagnostic sample

## Summary

`samples/gcode/heraldic-bedfixed.gcode`: the full heraldic drawn with the bed
**completely stationary** (Theta mode `fixed`, A constant at 0 for the whole
program, 6242 draw moves). This is the decisive A/B for the "outline all
around the lion" report: if the parked plot prints clean everywhere, the bed
rotation is the smear source; if it still wobbles, the bed is exonerated and
the search moves to the X/Y gantry and the pen.

## Reason

The bed-reversal parking rule (`WSW-20261013-010`) was expected to remove the
outline defects, but the operator reports the outline is still wrong all
around the lion, and the rule only parked part of the suspected stretch at
their feed settings. Rather than keep tuning the partial rule blind, plot the
extreme: no bed motion at all.

## Implementation

- Regenerated with the operator's plotting settings (manual 0.5 scale, feed
  350, tolerance 0.05) and the existing **Theta mode = Fixed** feature - no
  code change. The app's Theta mode combo can produce the same program; the
  file is committed so the bench test needs no app restart.

## Verification

- Parsed the generated program: 6242 draw moves, every comment label
  `fixed`, the A word constant at 0.000 through the whole draw - the bed
  never turns.
- The drawn geometry is identical to the operator's normal file (same bed
  bbox x -83.5..83.5, y -87.9..87.9; max radius 112.8 mm, inside the 180 mm
  reach), so the comparison against the latest print is apples to apples.
- Estimated plotting time ~13-15 min at 350 mm/min; the gantry carries all
  motion, so raise Feed rate for a faster second pass if the first is clean.
- Bench result PENDING: print on a **fresh** sheet and compare the outline
  against the latest print.

## Risks and follow-up

- If clean: the A drivetrain (belt tension, pulley grub screws, 12:1
  coupling, driver current) is the next mechanical target, and Fixed mode is
  immediately usable for quality-critical plots.
- If still wobbly: run the existing `y-repeatability-test.gcode` and an X
  equivalent for the gantry, and re-check the pen mount.

## Files

- `samples/gcode/heraldic-bedfixed.gcode`: the full-parked program.
