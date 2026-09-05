---
id: HW-20260905-001
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC / RP23U5XBB V1.01
  - 5 V source selector
  - USB bring-up
tags:
  - rp23cnc
  - usb
  - power-selector
  - tb6600
related:
  - E-17
  - E-03
---

# RP23CNC USB source-selector bring-up

## Summary

Restored laptop recognition of the RP23CNC by selecting the USB side of the
front `SWC USB` 5 V source selector during USB-only operation.

## Reason

The board was not recognized when `SWC` was selected without 12 V applied to the
RP23CNC main input. The selector choice needed to be recorded before beginning
the TB6600 signal test.

## Implementation

The current power rule is:

- `USB` for USB-only board power.
- `SWC` when the main 12 V input powers the onboard switching converter; USB
  can then remain connected for ioSender data.

The selector is unrelated to TB6600 signal logic and must only be moved while
power is removed.

## Verification

- With `SWC` selected and 12 V absent, USB recognition failed.
- After moving the selector to `USB` with power removed, USB recognition
  returned.
- Evidence: `docs/report/lab-notes/2026-09-05-rp23cnc-usb-source-selector.md`.

## Struggles and rejected approaches

The initial assumption that USB would power the board regardless of selector
position was incorrect. Ethernet is not needed for this recovery or for the
upcoming TB6600 signal test.

## Risks and follow-up

Before the TB6600 test, use `SWC` only if the RP23CNC main 12 V input is
energized. E-03 STEP/DIR/ENA waveform verification remains open.

## Files

- `docs/hardware/POWER_DISTRIBUTION.md`: records source-selector behavior.
- `docs/report/lab-notes/2026-09-05-rp23cnc-usb-source-selector.md`: records
  the bench symptom and recovery.
