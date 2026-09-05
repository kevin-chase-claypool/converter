---
id: HW-20260905-002
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - X/Y/A TB6600 signal harnesses
  - docs/hardware/WIRING_TABLE.md
  - docs/testing/TEST_PLAN.md
tags:
  - tb6600
  - step
  - direction
  - enable
  - e-03
  - commissioning
related:
  - HW-20260903-001
  - F-03
  - E-03
---

# Verify installed TB6600 signal response

## Summary

Completed E-03 for all three installed TB6600 signal harnesses. The RP23CNC
accepted G-code and produced the expected enable, direction, and step behavior
through the common-cathode wiring pattern.

## Reason

Continuity and the earlier unloaded RP23CNC output test established the wiring
paths and source signals, but the installed-driver inputs still needed a
powered response check before motor phases were connected.

## Implementation

- Kept the documented common-cathode topology: each axis `G` return is shared
  by `PUL-`, `DIR-`, and `ENA-`; `Stp`, `Dir`, and `En` land on the matching
  positive terminals.
- Confirmed the observed active-low `ENA+` state, held opposite `DIR+`
  states, and approximately 5 V `PUL+` activity.
- Recorded the result as an installed-driver bench verification rather than a
  motor-motion qualification.

## Verification

- Exact sequence: `G91`, `G0 A10 F60`, `G0 A-10 F60`, `G90`.
- Each command returned `ok`; A moved 150 -> 160 -> 150 in the status reports.
- A-axis readings: `ENA+` approximately 4.82 V idle and 0 V while moving;
  `DIR+` approximately 0 V for positive A and 4.82 V for negative A;
  `PUL+` oscilloscope maximum approximately 5.22 V.
- Owner reports that X and Y matched the A-axis signal response.
- Detailed evidence: `docs/report/lab-notes/2026-09-05-e-03-tb6600-installed-signal-response.md`.

## Struggles and rejected approaches

The ioSender console initially appeared to show only command echoes. The test
was repeated with command replies visible and one command at a time. An early
meter reading was taken from `ENA+` while diagnosing direction; the terminal
was corrected to `DIR+` before accepting the direction result. No wiring
change was made.

## Risks and follow-up

This pass does not verify motor-phase order, driver current or microstep DIP
settings, loaded motion, thermal margin, or physical direction. Proceed with
E-04 and M-01 under current-limited power. The status reports also showed
`Pn:ZA`; verify those input states before full-machine homing.

## Files

- `docs/report/lab-notes/2026-09-05-e-03-tb6600-installed-signal-response.md`: raw commands and measurements.
- `docs/testing/TEST_PLAN.md`: E-03 disposition.
- `docs/hardware/WIRING_TABLE.md`: promoted installed-driver signal rows.
- `docs/project/ENGINEERING_LOG.md`: milestone entry.
