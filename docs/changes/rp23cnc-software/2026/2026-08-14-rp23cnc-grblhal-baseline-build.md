---
id: RPSW-20260814-004
date: 2026-08-14
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - hardware/RP2040_RP23U5XBB.json
  - hardware/firmware.uf2
  - firmware/grblhal/config/build-record.md
tags:
  - rp23cnc
  - rp23u5xbb
  - grblhal
  - firmware-build
  - web-builder
related:
  - E-17
  - F-01
  - F-05
---

# RP23U5XBB grblHAL baseline build prepared

## Summary

Prepared, saved, and checksummed a Web Builder grblHAL UF2 for the received
RP23U5XBB V1.01 controller. The build has four axes, native USB, PWM spindle,
SD-card/Ymodem support, and the installed W5500 network module services.

## Evidence and configuration

The saved Web Builder JSON and `firmware.uf2` are retained in `hardware/`.
The authoritative build options, size, and SHA-256 are recorded in
`firmware/grblhal/config/build-record.md`.

## Verification

E-17 passed its magnified solder inspection and unpowered 12 V-to-ground and
5 V-to-ground no-short tests. F-01 then passed: native USB `$I` identified the
expected grblHAL/RP23U5XBB build, XYZA axes, W5500, and SD/Ymodem support.

## Risks and follow-up

Keep all 12 V, motor-driver, motor, and PC817 controller-side wires detached
for F-03/F-04. Do not connect the PC817 controller-side harness until F-05
establishes actual ENA/Aux0 polarity and current behavior.
