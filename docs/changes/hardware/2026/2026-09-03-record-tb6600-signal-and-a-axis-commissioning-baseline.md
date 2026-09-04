---
id: HW-20260903-001
date: 2026-09-03
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/integration/INTERFACES.md
  - docs/testing/TEST_PLAN.md
tags:
  - tb6600
  - stepper
  - a-axis
  - calibration
  - homing
related:
  - HW-20260815-002
  - HW-20260815-003
---

# Record TB6600 signal and A-axis commissioning baseline

## Summary

Recorded the supplied common-cathode RP23CNC-to-TB6600 signal pattern in the
master wiring table and consolidated the useful X/Y and A-axis starting
calculations for commissioning.

## Reason

The project already contained the supplied TB6600 schematic, but the master
wiring table incorrectly retained the signal endpoints as TBD. The A-axis
discussion also established useful bounds for interpreting its 12:1 reduction,
edge resolution, and two-revolution index-search duration.

## Implementation

- Each RP23CNC axis `G` is the local return for its TB6600 `PUL-`, `DIR-`, and
  `ENA-` terminals; `Stp`, `Dir`, and `En` connect to `PUL+`, `DIR+`, and
  `ENA+` respectively.
- The X/Y initial setting remains 80.000000 steps/mm at 16 microsteps and a
  20-tooth, 2 mm-pitch GT2 motor pulley. An opposite 20-tooth belt pulley is
  an idler and does not create another ratio.
- Corrected the interface document's stale 1.5 A DIP row to `SW4 ON`,
  `SW5 OFF`, `SW6 ON`, matching the current E-02/E-04 record.
- The 60-tooth motor pulley and 720-tooth bed pulley establish 12:1 reduction.
  At 8 microsteps, A remains 4.444444 steps per commanded motor-shaft degree,
  19,200 pulses per bed revolution, and 0.01875 degrees per pulse.
- A two-bed-revolution index search has a constant-speed time of
  `120 / bed_RPM` seconds. Its actual speed remains a loaded-motion
  commissioning result.

## Verification

Checked the supplied `plotter-wiring-schematic.svg` and
`plotter-pinout-schematic.html` against the updated MOT rows. Arithmetic was
checked from 200 full motor steps/revolution, the selected microstep settings,
and the recorded pulley tooth counts. E-03, M-01 through M-05, and the final
installed-silkscreen comparison remain required.

## Struggles and rejected approaches

The earlier table wording treated an already-supplied wiring pattern as an
unresolved topology. This was corrected without claiming a powered driver
test. Changing A microstepping solely to pursue speed was rejected: rate and
acceleration are first commissioned independently, and a DIP change requires
recalculation and re-verification.

## Risks and follow-up

Do not use the isolated-input ground as an axis signal return. Confirm labels,
fuses, DIP settings, and the actual driver response with power removed or
current-limited as the test requires. The production A scan rate must be based
on loaded M-01/M-02 evidence, including acceleration and reliable index
detection.

## Files

- `docs/hardware/WIRING_TABLE.md`: authoritative TB6600 signal endpoints.
- `docs/integration/INTERFACES.md`: A-axis resolution and scan-time guidance.
- `docs/testing/TEST_PLAN.md`: E-03 acceptance condition.
