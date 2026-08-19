---
id: HW-20260819-002
date: 2026-08-19
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/hardware/BOM.md
  - docs/testing/TEST_PLAN.md
  - docs/project/ROADMAP.md
tags:
  - tb6600
  - dip-switch
  - microstepping
  - current-limit
  - x-axis
  - y-axis
  - a-axis
related:
  - docs/report/lab-notes/2026-08-15-e-02-tb6600-factory-switch-observation.md
---

# Correct TB6600 Axis Switch Settings

## Summary

Corrected the B0FQ5GBNZ1 TB6600 DIP-switch mapping and recorded the initial
axis-specific configuration: X/Y at 16× microstepping, A at 8×, and every
17HS15 motor at 1.5 A per phase.

## Reason

The project had conflicting transcriptions of the current-switch table. Direct
inspection of the supplied Amazon listing's product-label image showed that the
1.5 A row is SW4/SW5/SW6 = ON/OFF/ON, not ON/ON/OFF. It also supplies the
listing-specific 16× row needed for the fine X/Y axes.

## Implementation

The exact initial settings are:

| Axis | SW1 | SW2 | SW3 | Microstepping | SW4 | SW5 | SW6 | Current |
|---|---|---|---|---:|---|---|---|---:|
| X | OFF | OFF | ON | 16× | ON | OFF | ON | 1.5 A/phase |
| Y | OFF | OFF | ON | 16× | ON | OFF | ON | 1.5 A/phase |
| A | OFF | ON | OFF | 8× | ON | OFF | ON | 1.5 A/phase |

This yields 80 steps/mm for X/Y's 20-tooth GT2 pulleys and 19,200 pulses per
bed revolution for A's 12:1 reduction under the motor-shaft-degree converter
contract.

## Verification

The B0FQ5GBNZ1 listing product-label image was directly inspected on
2026-08-19. It lists: 8× = OFF/ON/OFF, 16× = OFF/OFF/ON, and 1.5 A = ON/OFF/ON.
No powered driver or motor test has occurred; E-02/E-04 remain partial/open.

## Struggles and rejected approaches

Earlier records conflicted on the 1.5 A row, and a generic TB6600 mapping
cannot settle a clone's labeling. The source specific to the purchased ASIN
supersedes that transcription.

## Risks and follow-up

Before energizing, visually compare all three physical labels with this table
and change switches only with their drivers de-energized. E-03 must establish
input polarity, E-04 must inspect all settings, and M-01 through M-05 must
verify direction, heating, speed, and calibration.

## Files

- `docs/hardware/BOM.md`: authoritative purchased-driver configuration.
- `docs/testing/TEST_PLAN.md`: E-02/E-04 expected settings.
- `docs/project/ROADMAP.md`: Phase 3 baseline.
- `docs/report/lab-notes/2026-08-15-e-02-tb6600-factory-switch-observation.md`:
  corrected label evidence.
