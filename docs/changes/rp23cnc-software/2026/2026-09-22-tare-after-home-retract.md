---
id: RPSW-20260922-023
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - cs1238
  - tare
  - contact-seek
related:
  - RPSW-20260922-022
  - T-02
---

# Tare Only After Home Retract

## Summary

The integrated toolhead now waits to collect its live 64-sample CS1238 tare
until boot or fault recovery has reached the GP2 full-retract position. M3 is
blocked until that clear-home tare is valid.

## Reason

The fast-seek trace began at 38,281 normalized raw while reporting
`lift_home=1`; its tare had changed from 249,630 to 301,607 raw. The prior
firmware initiated tare before its boot lift completed, so a loaded startup
position could shift every later force threshold.

## Implementation

- Remove the startup tare request from `begin()`.
- On the first GP2 assertion in `LIFTING`—at boot or after `c`—stop/sleep the
  motor and start a fresh tare.
- Reject M3 with a visible fault if it is requested before `tare_valid`.
- Keep routine M5 separate: it does not silently retare after every stroke.

## Verification

- The recorded trace provides the red evidence for a loaded startup tare.
- Arduino RP2350 compilation/link produced the `.elf`, `.bin`, and `.uf2`
  artifacts for the updated sketch. The CLI process did not return after
  artifact generation and was stopped; no compiler error was reported.
- Documentation-index checks: pending after this edit.
- Hardware confirmation requires a new post-flash snapshot at GP2 showing a
  near-zero normalized force after `tare_valid=1`, followed by T-02.

## Struggles and rejected approaches

Requiring the operator to manually send `t` after every startup was rejected:
the reliable condition is physical GP2 home, which firmware can observe. A
routine M5 retare was also rejected because it would change the force reference
between strokes and conceal normal drift/clearance behavior.

## Risks and follow-up

GP2 indicates the mechanical maximum retract, not an independently measured
zero-force fixture. If the toolhead still carries a meaningful load at GP2,
T-01J must resolve the mechanical cause. Confirm the post-home baseline before
the next M3 test; do not use this change for production drawing.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  post-home tare sequencing and M3 guard.
- `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`:
  operator-visible tare behavior.
- `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`:
  trace evidence and follow-up.
