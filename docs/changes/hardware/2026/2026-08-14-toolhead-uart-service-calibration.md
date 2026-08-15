---
id: HW-20260814-002
date: 2026-08-14
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
  - docs/hardware/WIRING_TABLE.md
tags:
  - toolhead
  - uart
  - hx711
  - calibration
related:
  - docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md
---

# Toolhead UART Service Calibration Fixture

## Summary

Added a temporary GP20/GP21 UART service interface and a safe E-07B pen-tip
calibration sketch. It permits serial telemetry and short motor commands while
the toolhead runs from its local 6 V supply.

## Reason

The Pro Micro USB-C port is also a power input, so it cannot be used as the PC
serial connection while the local buck already powers the board. Direct masses
on the gray load-cell-mounted block demonstrated sensor operation but did not
provide repeatable mechanical calibration.

## Implementation

`e07b_hx711_actuator_steps.ino` maps hardware UART1 TX/RX to GP20/GP21 through
the Arduino-Pico `Serial2` object. It uses only the project owner's DSD TECH
SH-U09C2 USB-to-TTL adapter's GND, RXD, and TXD pins; its VCC pin is explicitly
unconnected. Commands make one 5-100 ms motor pulse and then sleep the DRV8833;
they also report/tare the HX711.

## Verification

The sketch compiled successfully:

```powershell
& 'C:\Program Files\Arduino CLI\arduino-cli.exe' compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\e07b_hx711_actuator_steps
```

No physical UART harness or motor-powered E-07B run has occurred yet.

## Struggles and rejected approaches

An ordinary USB-C cable connected during local toolhead power would create a
second 5 V source. Generic USB "data blockers" block data instead of solving
that problem, and a cable advertised only as "no Power Delivery" does not by
itself prove VBUS isolation. The isolated controller-side `CTRL_GND` remains
outside this service connection.

The first sketch used `Serial1`, which compiles but selects UART0 in the
Arduino-Pico core. UART0 cannot be routed to GP20; the observed GP20-low and
no-telemetry result exposed that mistake. The implementation now uses `Serial2`
for UART1.

## Risks and follow-up

Confirm adapter logic is set to 3.3 V and leave VCC open. Verify GP20/GP21
continuity before applying 6 V. Run and document E-07B with a digital scale;
do not derive a force calibration from the nonrepeatable gray-block mass tests.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: safe test firmware.
- `docs/hardware/WIRING_TABLE.md`: temporary service UART map.
- `docs/testing/TEST_PLAN.md`: E-07 next method.
- `docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md`: planned setup and safety record.
