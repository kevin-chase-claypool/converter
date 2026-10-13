---
id: WSW-20261013-009
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - tools/make_headback_parked_test.py
  - samples/gcode/headback-parked-test.gcode
  - samples/gcode/headback-test-bed.gcode
  - samples/gcode/headback-test-parked.gcode
tags:
  - a-axis
  - reversal
  - backlash
  - outline
  - verification
related:
  - RPSW-20261001-001
  - 2026-10-13-a-limits-raised-to-30000
---

# Back-of-head bed-parked A/B test

## Summary

New generator `tools/make_headback_parked_test.py` and its outputs: the
back-of-head scallop stretch of the heraldic outline is turned into test
programs built from identical bed-frame geometry. The combined program
`headback-parked-test.gcode` draws two copies side by side (bed turning vs
bed parked). `--split` instead writes two programs - `headback-test-bed.gcode`
(original bed motion, 21 A-direction reversals) and
`headback-test-parked.gcode` (pure X/Y, A frozen) - that draw at the **same
spot** so a second pen colour overlays the first; the divergence between the
colours is the kinematic error.

## Reason

The 350 mm/min heraldic print was measured on a flat photo: along bed
x 14-34, y 44-74 the outer outline stroke has no ink at its commanded
position (median paper dip 6 grey levels; 80 % of stations show no line
within +-0.4 mm) while the neighbouring inner stroke prints exactly on its
command. The nearest ink sits ~1.4 mm toward the inner line. That stretch
contains 16 A-direction reversals in 40 mm - the highest reversal density in
the drawing - with planned feeds up to 8156 on the tiny moves. Bed-centre and
ratio errors were ruled out (<= 10 % of the deviation variance), as was a
global frame slip (per-stroke implied rotation < 0.4 deg).

## Implementation

- The tool extracts the two pen-down runs covering that window from the
  source program (inner line and outer scalloped line, with their pen-up
  travel between) and rebuilds each move from the source bed points:
  copy 1 follows the original `A` trajectory at a translated paper position;
  copy 2 uses the identical bed points with `A` frozen at the final angle,
  so the machine draws the same paper shape with pure X/Y motion.
- Both copies are emitted with the source's pen macros (`M3`/`M5` plus the
  `G65 P115` handshakes) and the standard preamble/postamble, so the file
  runs like any plot program. Copy 1 self-positions with a rapid
  re-registration (`G0 X Y A`), copy 2 never emits an `A` word.
- Copy-2 feeds per move reproduce the original paper speed of the matching
  move (clamped to 80-2500 mm/min) so only the kinematics differ.
- `--split` mode reuses the same construction with both copies at
  `COPY1_CENTER`; each split file is self-contained (the parked file commands
  `G0 A<a_end>` first, so it draws correctly even when run first).

## Verification

- Tool self-check: the output contains exactly four pen-down runs; every
  reconstructed bed point of all four runs matches the source geometry to
  0.0001 mm; copy 1 carries 21 A-direction reversals; copy 2's A range is
  0.000 deg. Estimated drawing time: copy 1 ~2.1 min, copy 2 ~0.6 min.
- Split mode self-check: each file has two pen-down runs, both matching the
  source geometry to 0.0001 mm; the bed file carries 21 A reversals, the
  parked file an A range of 0.000 deg.
- Bench: plot on a fresh sheet and compare the outline band width of the two
  copies. Expected if A-reversal lag is the cause: copy 2 (parked) keeps the
  full 2.5-2.8 mm band while copy 1 pinches toward the inner line.

## Risks and follow-up

- If both copies pinch the same way, the defect is not the bed reversals and
  the next suspects are pen drag and the X/Y axes at those segment lengths.
- If only copy 1 pinches, the converter follow-up is to prefer the parked
  strategy when a stretch's reversal density exceeds a threshold.

## Files

- `tools/make_headback_parked_test.py`: generator and self-check.
- `samples/gcode/headback-parked-test.gcode`: generated test program.
- `samples/gcode/headback-test-bed.gcode` and
  `samples/gcode/headback-test-parked.gcode`: the two-pen overlay pair.
- `software/README.md`: listed with the other repeatability programs.
