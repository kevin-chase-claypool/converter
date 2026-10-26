---
id: HW-20261026-001
date: 2026-10-26
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - hardware/y-stepper
  - hardware/a-stepper
  - hardware/TB6600
  - firmware/grblhal/config/machine-settings.md
tags:
  - stepper
  - tb6600
  - ldo
  - 42sth48-2804ah
  - microstep
  - motor-current
related:
  - HW-20260819-002
---

# Plan 2.8 A LDO motors for Y and A

## Summary

The project owner selected LDO `42STH48-2804AH` motors for both Y and A. The
most appropriate TB6600 configuration keeps Y at 16x and A at 8x while setting
both drivers to their 2.8 A current row.

## Reason

The LDO motor is rated at 2.8 A/phase, considerably above the previous
17HS15 motors' 1.5 A. Using the previous current setting would substantially
reduce available torque. Copying Y's microstep setting to A is also
unnecessary: A already has a 12:1 mechanical reduction, while Y drives a
20-tooth GT2 pulley directly.

The current B0FQ5GBNZ1 listing images show a different current table from the
earlier repository transcription. In particular, the 2.8 A row is
`SW4 OFF`, `SW5 OFF`, `SW6 ON`.

## Implementation

Official motor specification from the LDO product page:

| Parameter | Value |
|---|---:|
| Step angle | 1.8 deg +/- 5% |
| Rated voltage | DC 1.96 V/phase |
| Rated current | DC 2.8 A/phase |
| Phase resistance | 0.7 ohm +/- 20% |
| Phase inductance | 0.6 mH +/- 20% |
| Holding torque | 4.2 kg-cm |
| Leads | 4 |
| Insulation class | H, 180 C |

Planned driver settings:

| Axis | SW1 | SW2 | SW3 | Microstep | SW4 | SW5 | SW6 | Current |
|---|---|---|---|---:|---|---|---|---:|
| Y | OFF | OFF | ON | 16x | OFF | OFF | ON | 2.8 A |
| A | OFF | ON | OFF | 8x | OFF | OFF | ON | 2.8 A |

Keep the current controller setting `$103=4.44444` because A remains at 8x.
Keep Y at `$101=80.000000` because Y remains at 16x. Existing max-rate and
acceleration settings remain the commissioning baseline until loaded tests
show that they require adjustment.

Leave the X driver unchanged for this work. Its physical label and programmed
current should be checked separately because the previous repository table did
not match the current listing images.

## Verification

- The official LDO product page was read on 2026-10-26:
  <https://ldomotion.com/products/ldo42sth482804ah-s80>
- The B0FQ5GBNZ1 product images were inspected on 2026-10-26:
  <https://www.amazon.com/dp/B0FQ5GBNZ1>
- The product table maps `2.8 A / 2.9 A peak` to `OFF/OFF/ON`.
- No motor has been installed or energized as part of this planning change.

## Struggles and rejected approaches

- The repository previously recorded the 1.5 A row as `ON/OFF/ON`; the current
  product images show it as `ON/ON/OFF`.
- Matching Y's 16x microstep on A was rejected because it doubles pulse demand
  without demonstrating useful resolution at the already-reduced bed drive.
- The old 1.5 A setting was rejected because it would operate a 2.8 A motor at
  approximately half its rated phase current.

## Risks and follow-up

- Confirm the physical driver label before setting DIP switches. Generic
  TB6600 clones ship incompatible tables.
- Change switches only while both TB6600 and motor power are off.
- Verify the LDO motor's actual lead colors and coil pairs before connection;
  do not assume they match the previous motor.
- Run low-speed Y and A tests first. Record supply current, winding/phase
  current if safely measurable, motor and driver temperature, direction, and
  lost-step behavior.
- Two 2.8 A motors increase electrical and thermal load. Re-check the 12 V
  supply, the selected 3 A branch fuses, TB6600 heatsinking, and connector
  temperature under realistic simultaneous XY/A motion.
- After installation, run a small jog, M-04 `A360`, `G65 P113`, and the
  rotation-center verification before a drawing job.

## Files

- `docs/hardware/BOM.md`: records the planned LDO motors and corrected driver table.
- `docs/testing/TEST_PLAN.md`: updates E-02/E-04 expected settings.
- `docs/report/lab-notes/2026-08-15-e-02-tb6600-factory-switch-observation.md`:
  preserves and corrects the earlier switch-table observation.
