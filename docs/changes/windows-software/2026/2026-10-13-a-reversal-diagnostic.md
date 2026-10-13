---
id: WSW-20261013-012
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_a_reversal_diagnostic.py
  - samples/gcode/a-reversal-diagnostic.gcode
tags:
  - a-axis
  - backlash
  - reversal
  - diagnostic
related:
  - WSW-20261013-011
  - WSW-20261013-009
---

# A-axis reversal diagnostic program

## Summary

New generator `tools/make_a_reversal_diagnostic.py` and sample
`samples/gcode/a-reversal-diagnostic.gcode`: one plot that separates the
possible causes of the bed's reversal error - mechanical play, lost steps,
belt wind-up, rate dependence, and pen-drag torque - using out/back arc
pairs, tick/soak/tick cumulative-loss tests, and a sharpie witness on the
pinion and the bed rim.

## Reason

The bed-fixed full plot is flawless (`WSW-20261013-011`), so the outline
defect is the bed's **reversing** behaviour, and the operator explicitly
wants the A axis fixed, not routed around. Smooth rotation is already proven
clean (r=100 mark test at F30000); the remaining question is which part of
the reverse path loses the position.

## Implementation

- Stations 1-3: three out/back arc pairs (3 cycles of +/-5 bed degrees) at
  r = 60 mm at 3000 / 6000 / 12000 motor deg/min. The gap between the out and
  return arc is the lost motion per reversal at that rate; a rate-dependent
  gap means elastic wind-up or driver torque, a flat gap means mechanical
  play.
- Station 4: the same at r = 85 mm, 3000 deg/min. A pure angular error scales
  the gap with radius; belt slop at the rim shows as a roughly constant arc
  gap instead.
- Station 5 (pen up): a tick at r=70, psi=0, then 30 cycles of +/-2 bed
  degree reversals at 6000, then the tick again. Any offset between the two
  ticks is **cumulative** loss (lost steps or slip in the drivetrain), not
  elastic recovery.
- Station 6 (pen down): the same structure with 20 cycles of +/-1 bed degree
  with the pen down so drag torque is applied; the scribble sits at psi=225
  while the ticks at psi=180 stay readable.
- The file header instructs marking sharpie witnesses before running: across
  the 60T pinion/motor face, across the bed rim/frame, and one belt tooth
  against one rim tooth. A moved pinion witness = fault at/before the pinion
  (grub screw or lost steps); witnesses steady while ticks offset = fault
  between pinion and bed (tension, rim fastening); a whole-pitch step on the
  tooth witness = the belt jumped one GT2 tooth - 2 mm at the rim, which is
  exactly 0.5 bed degree and matches the measured defect signature.

## Verification

- Self-check on generation: 128 A moves and 120 direction reversals; A stays
  inside 0..60.2 motor degrees; the program uses the standard preamble, pen
  macros and park postamble, so it runs like a plot.
- The generator now asserts every emitted line is parenthesis-balanced: the
  first sample shipped with an unterminated header comment that made ioSender
  refuse the file on load, and the balance check caught a second instance
  while fixing it. The committed sample carries the corrected header.
- Bench reading is done by eye/caliper on the ticks and arc pairs (a flat
  photo works too); expected run time is a few minutes.
- **Bench result (2026-10-13, photo PXL_20261013_231214763).** All seven
  stations drew. Measured line widths (~11.1 px/mm): single-pass baseline
  5.6-6.1 px at the fastest stations, and the 3000 deg/min stations are only
  ~1 px wider - that is ink flow, and it runs the *opposite* way to backlash
  (a gap grows with rate). No separated out/back lines anywhere; the
  per-reversal bed error is bounded at roughly 0.1 mm at the rim. The soak
  ticks (60 pen-up + 40 pen-down reversals) coincide within <1 px (~0.09 mm
  at r=70) - cumulative loss < 0.08 bed degree over 100 reversals, i.e.
  under 0.001 deg per reversal. **Conclusion: the A drivetrain is clean for
  isolated reversals.** Backlash, lost steps and belt slip are ruled out as
  the outline-smear source; the difference between the clean tests and the
  smeared plots must be state those tests do not exercise. Prime suspect
  now: bed height varying with bed ANGLE (rotational runout) - the fixed-bed
  plot holds one angle and is flawless, the diagnostic turns only +/-5 deg,
  the real plot sweeps the full circle.

## Risks and follow-up

- Measure once as-is, make the drivetrain adjustment, measure again - the
  arc-gap and tick-offset numbers are the before/after metrics.
- Cross-check any fix with the two-pen headback pair (`WSW-20261013-009`):
  the two colours must coincide once the reversal error is gone.

## Files

- `tools/make_a_reversal_diagnostic.py`: generator and self-check.
- `samples/gcode/a-reversal-diagnostic.gcode`: the diagnostic program.
