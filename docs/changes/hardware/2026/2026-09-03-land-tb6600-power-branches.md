---
id: HW-20260903-002
date: 2026-09-03
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - HD064RT OUT6/OUT7/OUT8 branches
  - X/Y/A TB6600 drivers
tags:
  - tb6600
  - power-distribution
  - wiring
  - x-axis
  - y-axis
  - a-axis
related:
  - HW-20260819-004
  - HW-20260903-001
---

# Land TB6600 power branches

## Summary

Recorded the owner-reported physical landing of positive and return conductors
from HD064RT `OUT6`, `OUT7`, and `OUT8` to the X, Y, and A TB6600 drivers.

## Reason

The three driver power branches were allocated in the wiring and power-
distribution records; their physical conductors are now installed and need a
clear commissioning boundary before the drivers are energized.

## Implementation

- `OUT6` positive/return: X TB6600.
- `OUT7` positive/return: Y TB6600.
- `OUT8` positive/return: A TB6600.

The six branch conductors are owner-reported **20 AWG**. The owner-selected
starting fuse value for each of these three branches is **3 A**. This is a
selection record, not confirmation that the physical HD064RT fuse inserts are
fitted or correctly marked.

The master wiring table records these as `planned — wired, unverified`. No
terminal-label, polarity, fuse-marking, continuity, or powered-load result is
inferred from the physical landing report.

## Verification

Owner-reported wiring completion, conductor gauge, and fuse-value selection only. E-11 and the remaining power checks,
power-removed continuity inspection, fuse confirmation, and the staged E-03 /
M-01 bring-up remain open.

## Struggles and rejected approaches

None. The update deliberately does not promote the rows to
`continuity-checked` or `bench-verified` without measurements.

## Risks and follow-up

Before applying power, confirm each conductor is on the received driver's
actual `DC+`/`DC-` terminals, verify branch fuse markings and polarity, and
keep motor and signal wiring within the documented staged test sequence.

## Files

- `docs/hardware/WIRING_TABLE.md`: records all six landed branch conductors.
