---
id: HW-20260823-005
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - MEISHILE S-120-12 AC terminals
  - X-axis motor cable shield
tags:
  - mains
  - protective-earth
  - shielding
  - wiring
related:
  - HW-20260823-004
---

# Verify mains terminal and X sheath landing

## Summary

The red/blue/green AC terminal convention and the X sheath protective-earth
landing are verified.

## Reason

Mains conductor identity must be verified by supply terminal marking before
power is applied.

## Implementation

Red is landed at printed `L`, blue at printed `N`, and the green wall-earth
conductor plus green X sheath/drain at the protective-earth symbol terminal.

## Verification

Owner verified the terminal markings and physical landings with power removed.

## Struggles and rejected approaches

Wire color alone was not accepted; the printed terminal markings were used for
the verification.

## Risks and follow-up

PE-to-chassis continuity, X sheath isolation from `-V` and motor phases,
enclosure protection, and powered E-11 checks remain open.

## Files

- `docs/hardware/WIRING_TABLE.md`: marks the verified landing scope.
- `docs/report/lab-notes/2026-08-23-mains-terminal-and-x-sheath-verification.md`:
  records the evidence boundary.
