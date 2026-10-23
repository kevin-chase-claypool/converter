---
id: WSW-20261023-001
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/converter_core/motion_check.py
  - tools/check_gcode_motion.py
tags:
  - cmyk
  - alignment
  - pen-offset
  - preflight
  - motion-check
related:
  - WSW-20261020-001
  - WSW-20261020-002
---

# CMYK per-ink offsets, measured alignment and save preflight

## Summary

The CMYK tab now carries per-ink X/Y pen corrections, converts measured
alignment crosses into those corrections, and shows a pass summary with a
motion preflight before saving. Artwork sets write a `<name>-set.json`
manifest recording the frame, bed motion, centre hold, offsets, files and
per-ink checks. Calibration sheets deliberately keep their geometric layout.

## Reason

The shared page frame made the four saved files co-registered, but physical
pen seating/tip differences can still shift a pass. The pen-alignment crosses
measure that displacement, and the operator needs a way to apply the measured
values and to see the remaining machine-level risks before a four-pass print.
The existing `check_gcode_motion.py` analysis was only available after a file
was already saved; the same checks now run in the app.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: **Pen alignment** group with X/Y
  correction spin boxes for C/M/Y/K and measured-displacement fields relative
  to cyan. **Use measured offsets** sets each correction to the opposite of
  the measured displacement; cyan is the reference. Offsets are applied to
  the scaled layer marks and to that ink's registration crosses, leaving the
  shared page frame unchanged. The calibration sheet does not apply them.
- The tab shows a **Pass summary** (page, frame, bed motion, centre hold,
  crosses, offsets) and updates it after planning with preflight results.
  Hard violations (bed-step cap, A-rate limit, bare `G0` rotation) block Save;
  over-tolerance moves are warnings.
- `software/converter_core/motion_check.py`: the file-parsing analysis from
  `tools/check_gcode_motion.py` is now a core function usable on generated
  text or files, with over-tolerance counting. The file analysis reads the
  tolerance printed in the program header.
- `tools/check_gcode_motion.py`: thin CLI wrapper over the core analysis; it
  now also reports moves exceeding the file's stated tolerance.
- Successful artwork saves write a set manifest beside the four G-code files;
  calibration sheets continue to write their existing calibration manifest.

## Verification

- New `software/tests/test_motion_check.py` covers clean programs, bed-step
  violations, bare `G0` rotation, over-tolerance counting and the file
  wrapper.
- New CMYK tests cover per-ink translation (only the selected ink moves),
  measured-to-correction sign conversion, unchanged shared frame with
  offsets, calibration-sheet isolation, pass summary/preflight wording,
  blocking Save on a hard violation, and the set manifest contents.
- Full suite: 437 tests pass (1 skipped).
- `python tools\check_gcode_motion.py samples\gcode\Ben1\IMG_0514-cmyk-yellow.gcode`
  reads the file's 0.050 mm tolerance and reports one move at 0.056 mm
  (the subdivision cap); the hard A guards pass. This file predates the
  centre-hold change and is used only as a real-world parser check.

## Struggles and rejected approaches

- Per-ink offsets were not applied by changing the frame centre: that would
  move the whole page and undo the shared frame. They translate only that
  ink's marks.
- The calibration sheet does not receive pen offsets: its scan manifest and
  patch rectangles assume the geometric page layout.
- The uncommitted `sharpen_pct`/`sharpen_radius_mm` work in `cmyk.py` was
  left untouched; it is not part of this milestone.

## Risks and follow-up

- A single X/Y correction fixes translation only. Measured crosses that fan
  or rotate indicate frame/A/bed error and need the separate bed/flatness
  investigation, not a larger offset.
- Offsets are not persisted across app launches yet (settings persistence is
  the later P2 milestone), but they are recorded in the set manifest so a
  saved set is reproducible.
- Bench acceptance is pending: print the pen-alignment crosses with the four
  pens, enter the measured values, print a CMYK set, and confirm the passes
  overlay within the remaining machine tolerance.

## Files

- `software/generator_tabs/cmyk_tab.py`: offsets, measured helper, summary,
  preflight and set manifest.
- `software/converter_core/motion_check.py`: shared motion analysis.
- `software/converter_core/__init__.py`: export the analysis.
- `tools/check_gcode_motion.py`: CLI uses the core analysis and reports
  tolerance violations.
- `software/tests/test_motion_check.py`, `software/tests/test_cmyk_tab.py`:
  coverage.
- `software/README.md`: current-state instructions.
