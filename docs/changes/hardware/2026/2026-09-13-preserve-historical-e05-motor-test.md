---
id: HW-20260913-007
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e05_historical_03f6c00
tags:
  - n20
  - drv8833
  - e-05
  - regression-test
related:
  - HW-20260913-006
  - 03f6c00
---

# Preserve historical E-05 motor test

## Summary

The exact historical E-05 source from commit `03f6c00` is available as its own
Arduino sketch for an A/B reproduction against the replacement 1000 RPM N20.

## Reason

The historical test was reported to move the prior N20 bidirectionally, while
the current E07B test did not visibly move the replacement motor. The owner
requested the whole prior pin assignment and code path before considering
driver/perfboard rework.

## Implementation

The source is copied verbatim: GP7 is the driven-high legacy sleep output, GP6
is the `INPUT_PULLUP` legacy fault input, and it automatically performs a
500 ms first-direction pulse followed by a 500 ms reverse pulse after 2 s.
It lives in a separate folder and does not overwrite the current corrected
E-05 or E07B sketches.

## Verification

- Source content was recovered from commit `03f6c00`.
- Compile and physical A/B result remain pending.

## Struggles and rejected approaches

A shortened, repinned comparison was rejected because it would not reproduce
the historic test the owner requested.

## Risks and follow-up

The historical sketch has no inter-pulse abort and runs both directions. Before
boot, provide enough travel for both 500 ms motions. A pass does not alone
prove GP7 is sleep: the legacy GP6 `INPUT_PULLUP` can also leave the confirmed
EEP sleep input high. Compare the result with current E07B duration behavior.

## Files

- `firmware/pen_pressure/e05_historical_03f6c00/e05_historical_03f6c00.ino`: preserved historical source.
- `firmware/pen_pressure/README.md`: identifies intended use and safety boundary.
