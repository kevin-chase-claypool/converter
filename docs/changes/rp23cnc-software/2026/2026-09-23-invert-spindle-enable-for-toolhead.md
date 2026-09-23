---
id: RPSW-20260923-015
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - f05
  - m3m5
  - spindle
  - toolhead
  - polarity
related:
  - HW-20260806-002
---

# Invert the grblHAL spindle enable to match the toolhead input

## Summary

The RP23CNC now sets `$16=1` (invert spindle enable) so `M3` pulls the spindle
`ENA` output low and `M5` leaves it high. Through the PC817C interface that
makes `M3` engage and `M5` lift, and the toolhead no longer drives the pen down
when the controller powers up.

## Reason

The toolhead's M3/M5 input is an active-low optocoupler: `ENA` low lights U1,
which pulls GP29 low, which the firmware reads as `M3`. On the bench, powering
the RP23CNC drove the pen down with no `M3` issued — the spindle `ENA` output
held the optocoupler on at idle. Confirmed by disconnecting the `ENA` wire
(no engagement) and by the toolhead `cmd=M3` at rest. The default grblHAL
spindle-enable polarity is active-high, which is inverted from this interface.

## Implementation

- Set `$16=1` on the RP23CNC (`Setting_SpindleInvertMask`, bit 0 = spindle
  enable). grblHAL exposes this as a runtime setting; no hardware change was
  required and the optocoupler board was left as built.
- `$16` is flagged reboot-required, so the controller must be reset for it to
  take effect.
- Recorded the setting in `firmware/grblhal/config/machine-settings.md`.

## Verification

- `$16` queries back as `1` after the write.
- After a reset, the toolhead sits `LIFTED` / `cmd=M5` at controller power-up
  instead of driving down.
- `M3` drives the pen down; `M5` lifts it. See
  `docs/report/lab-notes/2026-09-23-f-05-spindle-enable-polarity.md`.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

Modifying the optocoupler input to be sourcing-driven was rejected: it works,
but grblHAL already provides a runtime invert, so the fix belongs in controller
configuration. Flipping the toolhead flag `CMD_ACTIVE_HIGH_IS_M3` was rejected
because it would make the pen drop whenever the controller is unpowered, which
inverts the fail-safe. The first stabilization build had assumed active-low
sinking and was wrong.

## Risks and follow-up

Not yet recorded: the `ENA` meter levels at idle/`M3`/`M5`, and the unexplained
mid-session power event where the RP23CNC stopped powering up on 12 V with the
selector already on `SWC`, then recovered without a documented cause. Re-check
both before production. `F-05A` (`P115`/`PRB` acknowledgement) remains open.

## Files

- `firmware/grblhal/config/machine-settings.md`: record `$16=1` and the other verified settings.
- `firmware/grblhal/README.md`, `firmware/README.md`: note the verified M3/M5 polarity.
- `docs/hardware/WIRING_TABLE.md`: `TH-001A` polarity now verified.
- `docs/integration/INTERFACES.md`: M3/M5 polarity established.
- `docs/testing/TEST_PLAN.md`, `docs/project/ROADMAP.md`: F-05 result.
- `docs/report/lab-notes/2026-09-23-f-05-spindle-enable-polarity.md`: bench evidence.
