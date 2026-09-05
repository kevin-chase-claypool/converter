---
id: HW-20260905-006
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - Y-axis TB6600 and 17HS15-1504S-X1 motor
  - GT2 gantry drive
tags:
  - y-axis
  - dimensional-calibration
  - steps-per-mm
  - commissioning
related:
  - M-03
  - HW-20260905-005
  - docs/report/lab-notes/2026-09-05-m-03-y-axis-dimensional-calibration.md
---

# Verify Y-axis dimensional calibration

## Summary

The Y-axis passed a 100 mm physical travel check with `$101=80.000000`
steps/mm. Caliper measurement was exactly 100 mm, and the matched reverse move
returned exactly to the reference mark.

## Reason

The calculated 80 steps/mm baseline needed physical verification before using Y
coordinates for dimensionally meaningful plotting. An earlier test was invalid
because the controller was in absolute mode and `$101` was still 250.

## Implementation

The operator restored `$101=80`, established `G21`, `G94`, and `G91`, verified
the modal state with `$G`, and ran matched `Y100`/`Y-100` moves at `F120`.

## Verification

- `G1 Y100 F120` measured exactly 100 mm with calipers.
- `G1 Y-100 F120` returned exactly to the starting reference mark.
- No steps-per-mm correction was required.
- M-03 passed for the conducted Y-axis dimensional check; X remains open.

## Struggles and rejected approaches

The initial long movement was not used as calibration evidence: it was issued
in `G90` from a nonzero coordinate with `$101=250`, so the controller moved to
an absolute target and used an incorrect scale. The test was repeated after
restoring `$101=80` and explicitly confirming `G91`.

## Risks and follow-up

This validates one 100 mm unloaded Y span; it does not establish X accuracy,
full-frame belt backlash, or pen-loaded dimensional error. Perform the same
check on X before coordinated plotting tests.

## Files

- `docs/report/lab-notes/2026-09-05-m-03-y-axis-dimensional-calibration.md`:
  records the commands, modal-state correction, measurement, and result.
- `docs/testing/TEST_PLAN.md`: records Y's M-03 pass and the remaining X work.
- `docs/integration/INTERFACES.md`: updates the X/Y calibration status.
- `firmware/README.md`: updates the motion commissioning status.
- `firmware/grblhal/config/build-record.md`: records Y's validated baseline.
- `docs/project/ENGINEERING_LOG.md`: records the completed Y calibration
  milestone.
