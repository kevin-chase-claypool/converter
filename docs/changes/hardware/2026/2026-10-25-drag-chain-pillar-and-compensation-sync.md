---
id: HW-20261025-001
date: 2026-10-25
category: hardware
affected_categories:
  - hardware
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - hardware/y-drag-chain
  - hardware/northeast-pillar
  - tools/make_bed_compensation_motion_test.py
  - samples/gcode/bed-compensation-motion-test.gcode
tags:
  - m-06
  - m-13
  - bed-compensation
  - rotary
  - drag-chain
  - tracking
related:
  - ADR-009
  - HW-20261011-001
---

# Drag-chain pillar repair and compensated XY/A test

## Summary

The operator removed a stepped obstruction from the Y drag-chain path by
replacing the northeast rail pillar with a straight version. The XY-only print
then appeared flawless. With the mechanical striation cause substantially
identified, a five-case one-sheet diagnostic was added to isolate the remaining
combined X/Y/A tracking concern while keeping bed compensation enabled.

## Reason

Earlier wave-screen errors varied with position, feed, and mechanical load but
did not reproduce as a static G-code geometry error. The drag chain had been
forced to climb onto the northeast pillar during Y travel. The resulting
friction is a credible cause for the historical striations.

The rotating-bed file still needs to establish whether any remaining error is
from compensation-induced planner dynamics, mixed linear/rotary feed handling,
or residual A-axis mechanics. The source review found that grblHAL already
executes X/Y/A in one coordinated block; `$701` changes feed interpretation,
not synchronization.

## Implementation

- Replaced the stepped northeast pillar so the Y drag chain follows straight
  3030 extrusion for the full print travel. This is an operator-reported
  physical change; exact dimensions and part identity were not captured.
- Added `tools/make_bed_compensation_motion_test.py`.
- Generated `samples/gcode/bed-compensation-motion-test.gcode`.
- The one-file program compares XY-only, rotating uncompensated, rotating
  compensated, and slow/fast variants with the same bed-space path and A
  schedule. Every case includes both rotating pen-up travel and forward/reverse
  pen-down traces.
- Kept compensation active and unchanged. No controller setting or production
  converter behavior was changed.

## Verification

- Targeted regression tests pass for shared geometry, shared A schedule,
  compensated inverse decoding, rotating pen-up coverage, no pauses, one
  program end, and existing motion guards.
- Current G-code preflight: PASS; maximum drawing-block rotation `0.19 deg`,
  maximum demanded A rate `54 motor deg/s`, `0` bare rotated `G0` moves, and
  `0` moves over the stated `0.15 mm` path tolerance.
- Generator output is deterministic. The committed test G-code SHA-256 is
  `ED48632808AFBC46FEDE13000B948E5D4006B39ABE5D0F336FE8644AD3C7C203`.
- The operator reports the XY-only version is now visually flawless.
- No compensated-versus-uncompensated physical sheet has been run yet.

## Struggles and rejected approaches

- Earlier work treated wave-row spacing and small geometry errors as sufficient
  causes. Those fixes improved the source but did not explain the full
  mechanical failure.
- A rotation/acceleration matrix did not reproduce the error at `$123=6000`
  versus `600`; changing acceleration alone was not accepted as the cause.
- Source inspection rejected the theory that bed compensation creates an
  independent A-axis clock. Compensation does affect the machine-space path and
  therefore dynamics, but each emitted move remains a common endpoint command.
- Enabling `$701=1` was not used as a speculative fix. It would change mixed
  feed semantics and invalidate the current converter's feed calculation.

## Risks and follow-up

- The XY-only observation is operator-reported and lacks a before/after photo
  or mechanical measurement.
- Residual A-axis belt compliance, torque loss, backlash, or another mechanical
  drag source can still produce a rotating-only error.
- Run the new ordinary-paper black-pen test before another long CMYK layer.
- Interpret the five cases per the test plan. Only compensated cases failing
  would justify a converter feed/subdivision change.
- The existing compensated-profile calibration remains valid; this milestone
  does not replace or refit it.

## Files

- `tools/make_bed_compensation_motion_test.py`: reproducible paired diagnostic.
- `samples/gcode/bed-compensation-motion-test.gcode`: one-run physical test.
- `software/tests/test_bed_compensation_motion_test.py`: geometry and guard
  regression coverage.
- `docs/research/2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md`:
  primary-source research and hypotheses.
- `docs/hardware/MECHANICAL_FRAME.md`: current Y drag-chain and pillar
  configuration.
- `docs/report/lab-notes/2026-10-25-m-13-drag-chain-pillar.md`: mechanical
  evidence.
- `docs/report/lab-notes/2026-10-25-m-06-compensation-sync-test-plan.md`:
  physical-test procedure and interpretation.
