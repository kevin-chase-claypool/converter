---
id: RPSW-20261014-002
date: 2026-10-14
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - tools/validate_homing_macro.py
tags:
  - grblhal
  - macro
  - p100
  - registration
  - calibration
  - drift
related:
  - RPSW-20261014-001
  - WSW-20261014-001
---

# Axis-centre correction refined from the line-replay test: Y 0.9 -> 0.3

## Summary

`P100.macro`'s `#<axis_center_correction_y>` drops from `0.9` to `0.3`; X
stays `2.45`. The basis is the tagged line-replay bench test, whose end-tag
direction the operator confirmed as machine +Y: the replay lines land on the
opposite side of the tags, so the drawn pattern is `e(180) = 2C` with
`C = (0, -0.6) mm` - the true rotation axis sits about 0.6 mm toward -Y of
the registered origin. Two runs reproduced the ladder (0.60/0.60/1.20 and
0.62/0.65/1.16 mm), and the correction is added to the registered origin, so
Y falls by 0.6.

If the centre magnet is actually on the axis, the park will now land about
0.6 mm off the magnet - that is the recorded magnet-versus-chain
attribution, not a fault, and the `G65 P100 Q5` A0/A180 test settles it.

## Reason

The morning pen-centre jog (`RPSW-20261014-001`) aligned the park to the
magnet as the operator judged it, but the line-replay test - which reads the
rotation directly by drawing the same bed-frame line at several bed angles -
still showed a reproducible 0.6 mm centre-offset ladder. The 2026-10-14
evening direction confirmation ("the direction that the line endmarks point
is the +Y") resolved the sign that photographs alone could not.

## Implementation

- `firmware/grblhal/macros/P100.macro`: the Y constant and its comment block
  now carry the line-replay measurement and the expected park shift.
- `tools/validate_homing_macro.py`: expected tokens re-pinned to `0.3`.
- Documentation: the macros README axis-centre section (including the
  magnet-check caveat), `firmware/README.md`, the lab note, and the
  engineering log.

## Verification

- `python tools\check_macros.py` - all macros parse-safe.
- `python tools\validate_homing_macro.py` - P100/P115 validation passed.
- `python tools\docs_index.py --write` / `--check` - indexes regenerated and
  valid.
- **Pending:** upload `P100.macro`, run `G65 P113`, then re-run
  `samples/gcode/a-line-replay-test.gcode`: the replays should collapse onto
  the reference within registration reproducibility (~0.1 mm). Also inspect
  where the park sits relative to the centre magnet and report the offset
  direction - that is the attribution datum.

## Struggles and rejected approaches

- Photo-only orientation could not resolve the sign of the offset (the two
  runs' sheets were placed differently). The fix was the operator's tag
  direction statement plus tagging the sheet for future runs.
- Considered folding the delta into `sensor_to_pen`; kept it in the
  axis-centre constant per the established convention - the write is
  numerically identical either way.

## Risks and follow-up

- The residual is a registration-frame property; it is only as repeatable as
  the registration itself (historically ~0.1 mm class).
- The magnet-versus-chain attribution remains open; `G65 P100 Q5` at
  A0/A180 is the two-command test.
- The X/Y scale-sheet measurement remains open (X-direction lengths read
  long by roughly 0.3-0.9 percent across photo and caliper samples).

## Files

- `firmware/grblhal/macros/P100.macro`: Y correction and comment.
- `tools/validate_homing_macro.py`: pinned expectation.
- `firmware/grblhal/macros/README.md`, `firmware/README.md`: current-state
  documentation.
- `docs/report/lab-notes/2026-10-14-line-replay-first-run.md`: bench note.
- `docs/project/ENGINEERING_LOG.md`: log entry.
