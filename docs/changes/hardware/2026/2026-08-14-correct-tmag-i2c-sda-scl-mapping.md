---
id: HW-20260814-003
date: 2026-08-14
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/e09_tmag5273_verification/e09_tmag5273_verification.ino
  - docs/hardware/WIRING_TABLE.md
tags:
  - tmag5273
  - i2c
  - qwiic
  - wiring-correction
related:
  - RPSW-20260814-003
---

# Correct TMAG5273 I2C SDA/SCL Mapping

## Summary

Corrected the toolhead TMAG5273 I2C mapping to GP16/SDA and GP17/SCL.

## Reason

E-09 verified 3.3 V power and idle-high bus lines but blocked immediately when
the TMAG I2C transaction began. Review of the installed Arduino RP2350 board
definition and RP2350 I2C0 functions showed the earlier GP17/SDA and GP16/SCL
assignment was reversed.

## Implementation

E-09 now configures `Wire` with GP16 as SDA and GP17 as SCL. The current wiring
table marks both conductors as rework-required until the two signal wires are
swapped. Sensor 3.3 V and ground remain unchanged.

## Verification

The corrected E-09 sketch compiles for
`rp2040:rp2040:sparkfun_promicrorp2350`. After the physical signal swap, E-09
identified the TMAG5273 and measured stable far/near/return magnitudes of
0.24/7.51/7.44 mT.

## Struggles and rejected approaches

The official hardware overview describes the Qwiic signals in an order that
conflicted with the installed Arduino core's `PIN_WIRE0_SDA=16` and
`PIN_WIRE0_SCL=17` definitions. Electrical idle-high checks alone could not
detect the crossed SDA/SCL pair.

## Risks and follow-up

Final magnetic scan geometry must still select production threshold/hysteresis;
the E-09 3.5 mT / 1.0 mT values are deliberately conservative starting points.

## Files

- `firmware/pen_pressure/e09_tmag5273_verification/e09_tmag5273_verification.ino`: corrected Wire pin setup.
- `docs/hardware/WIRING_TABLE.md`: corrected authoritative I2C wiring.
- `docs/report/lab-notes/2026-08-14-e-09-tmag5273-verification.md`: failure and correction record.
