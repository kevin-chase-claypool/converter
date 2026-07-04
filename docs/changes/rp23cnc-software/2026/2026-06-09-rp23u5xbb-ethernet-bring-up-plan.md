---
id: RPSW-20260609-001
date: 2026-06-09
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: planned
components:
  - firmware/grblhal
  - RP23U5XBB
  - Wiz850io
tags:
  - grblhal
  - ethernet
  - w5500
  - firmware-build
related:
  - E-16
  - E-17
  - F-01
---

# RP23U5XBB Ethernet Bring-Up Plan

## Summary

Added a board-specific implementation sequence for assembling the Wiz850io
adapter, generating a reproducible grblHAL build, flashing through USB, proving
DHCP/Telnet operation, and then configuring the plotter's X/Y/A contract.

## Reason

The received RP23CNC board and Ethernet kit move the project from generic
controller selection into physical assembly and firmware bring-up. The upstream
manual contains several non-obvious requirements that must be preserved before
coding starts.

## Implementation

The new plan records the correct RP23U5XBB Web Builder target, four-axis
requirement for A-axis support, W5500 builder selection for the Wiz850io module,
recommended network services, USB recovery path, first-run input inversion,
settings capture, and criteria for introducing custom plugin code.
It explicitly identifies board creator Phil Barrett's
[`RP23CNC`](https://github.com/phil-barrett/RP23CNC) repository as the canonical
source for current board documentation, schematics, and revision files.

## Verification

- Reviewed the official 50-page RP23CNC user manual for versions 1.0/1.01.
- Reviewed the official 8-page RP23U5XBB assembly instructions.
- Inspected the supplied Ethernet-module photograph: the visible Wiznet W5500
  marking and two six-pin rows match the manual's Wiz850io-format requirement.
- Inspected front and back board photographs: front silkscreen confirms the
  received controller is `RP23U5XBB V1.01`; visible connector population was
  recorded without treating overview photographs as a complete solder or
  continuity inspection.
- Cross-checked the plan against repository architecture, interfaces, wiring,
  test plan, roadmap, and firmware documents.
- Physical assembly, firmware generation, flashing, and Ethernet tests remain
  pending.

## Struggles and rejected approaches

The reported board name `RP23U5BB` does not match the official `RP23U5XBB`
name, so the plan does not assume a revision from the text alone. Starting with
a source-code fork was rejected because the supported Web Builder path can
establish the baseline with less risk and better reproducibility.

## Risks and follow-up

Confirm the exact PCB revision and W5500 module before power. Telnet and FTP are
unencrypted and must remain on a trusted private network. Do not copy temporary
input or enable-inversion settings into the final machine without wiring and
output tests.

## Files

- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: authoritative bring-up sequence.
- `firmware/grblhal/README.md`: link and current task update.
- `firmware/README.md`: subsystem status and plan link.
- `docs/project/ENGINEERING_LOG.md`: planning milestone and unresolved gates.
