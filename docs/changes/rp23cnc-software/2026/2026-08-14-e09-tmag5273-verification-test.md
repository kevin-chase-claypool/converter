---
id: RPSW-20260814-003
date: 2026-08-14
category: rp23cnc-software
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/e09_tmag5273_verification/e09_tmag5273_verification.ino
  - docs/testing/TEST_PLAN.md
  - docs/report/lab-notes/2026-08-14-e-09-tmag5273-verification.md
tags:
  - tmag5273
  - i2c
  - qwiic
  - toolhead
related:
  - RPSW-20260814-002
---

# Add E-09 TMAG5273 Intended-Wiring Test

## Summary

Added a quiet service-UART E-09 sketch for the toolhead TMAG5273's final
Qwiic/I2C path.

## Reason

The sensor must be verified locally before its readings are used for bed-center
and A-axis reference logic in E-18.

## Implementation

The sketch starts its GP20/GP21 `Serial2` harness before touching I2C. Command
`i` then explicitly configures I2C SDA as GPIO17 and SCL as GPIO16 and checks
the TMAG5273 at its default address `0x22`. This preserves serial diagnostics if the Qwiic
bus is held low or miswired. On-demand vector and 20-sample magnitude-stability
reports are available after successful initialization; the motor driver is
never enabled.

## Verification

Compiled for `rp2040:rp2040:sparkfun_promicrorp2350`. After the GP16/SDA and
GP17/SCL correction, E-09 verified identity, stable stationary readings, and
far/near/return magnitude values of 0.24/7.51/7.44 mT.

## Struggles and rejected approaches

Continuous streaming was avoided so far/reference/near readings can be copied
without serial-monitor scrolling.

## Risks and follow-up

Use the E-09 far/near values as conservative initial threshold guidance only;
final scan geometry and E-18 determine production threshold/hysteresis.

## Files

- `firmware/pen_pressure/e09_tmag5273_verification/e09_tmag5273_verification.ino`: E-09 test firmware.
- `docs/testing/TEST_PLAN.md`: E-09 execution status.
- `docs/report/lab-notes/2026-08-14-e-09-tmag5273-verification.md`: procedure and results record.
