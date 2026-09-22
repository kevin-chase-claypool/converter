---
id: RPSW-20260922-005
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger
tags:
  - e-09e
  - uart
  - usb-to-ttl
  - power-safety
related:
  - docs/integration/INTERFACES.md
  - RPSW-20260922-003
---

# Route E-09E runtime through service UART

## Summary

Moved E-09E runtime communications from Pro Micro USB-C to its existing
GP20/GP21 service UART, removing an unsafe second-5-V-source assumption.

## Reason

The Pro Micro's 5 V input is hardwired to the external 6 V-to-5 V toolhead
power path. USB-C cannot be connected concurrently without verified isolation
from VBUS backfeed.

## Implementation

- E-09E now uses UART1 at 115200 baud with `GP20` TX and `GP21` RX.
- The Windows application accepts the USB-to-TTL adapter COM port as the E-09E
  test port and clearly distinguishes it from E-07D native USB calibration.
- Documents the established adapter wiring: RXD ← GP20, TXD → GP21, GND →
  TOOL_GND, adapter VCC disconnected.

## Verification

- Recompile the E-09E SparkFun Pro Micro RP2350 sketch.
- Run the Windows application unit checks and documentation index.

## Struggles and rejected approaches

Native USB runtime was rejected because it would put PC USB 5 V alongside the
hardwired external 5 V rail. A data-only cable was not assumed because its
device-enumeration behavior and VBUS arrangement are not verified here.

## Risks and follow-up

USB-C remains flash-only and must be used with the external rail disconnected.
Confirm the adapter is set to 3.3 V logic and its VCC lead is not connected
before the powered E-09E test.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`:
  UART1 runtime transport.
- `docs/integration/INTERFACES.md`: service-UART/power contract.
