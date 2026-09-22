---
id: RPSW-20260922-006
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
tags:
  - e-09e
  - uart
  - arduino-ide
  - kitchen-scale
  - safety
related:
  - RPSW-20260922-005
  - docs/integration/INTERFACES.md
---

# Add E-09E Serial Monitor shortcuts

## Summary

E-09E can now be run directly from Arduino IDE Serial Monitor, avoiding the
optional Windows application's connection path for the supervised kitchen-scale
check.

## Reason

The Windows application remained at `Connecting...` on the adapter COM port.
The test only requires single bounded pulse commands and a readable CS1238 raw
value, so an immediate manual serial interface is simpler and more diagnosable.

## Implementation

- Added immediate short commands: `t`, `a`, `d`, `u`, `r`, `x`, `[`, `]`, and
  `?`.
- `[` and `]` adjust a selected 10–100 ms pulse duration in 10 ms steps.
- Startup and `?` print the concise command list plus status.
- Retained the existing long commands for script/capture compatibility.
- Documented Arduino IDE Serial Monitor as the preferred manual E-09E path.

## Verification

- `arduino-cli compile --build-path work\\e09e-monitor-build --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e09e_cs1238_pen_scale_pulse` produced the `.uf2`, `.elf`, and `.bin` artifacts.
- No powered N20 pulse or scale result is claimed.

## Struggles and rejected approaches

The Windows application was not used as a required intermediary because its
adapter-port connection did not complete. USB-C runtime remains rejected: the
Pro Micro's external 5 V rail is hardwired and must not be paralleled with an
unverified USB VBUS path.

## Risks and follow-up

Only one program may own the adapter COM port. Verify the Serial Monitor `?`
response before arming, begin at 10 ms, and record the raw value and stable
kitchen-scale reading near 50 g. This does not enable production force control.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`: immediate supervised serial commands.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/README.md`: manual test procedure.
- `firmware/pen_pressure/README.md`: E-09E interface summary.
- `docs/integration/INTERFACES.md`: UART ownership and command contract.
- `docs/testing/TEST_PLAN.md`: E-09C manual operation path.
