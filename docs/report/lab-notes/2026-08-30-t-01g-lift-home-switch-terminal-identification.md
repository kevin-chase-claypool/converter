# T-01G — Planned LIFT-Home Switch Terminal Identification

**Date:** 2026-08-30
**Status:** planned; no electrical connection or powered test has been completed.

## Proposed configuration

- Microswitch terminals selected: `1` and `3`.
- Intended behavior: open when released; closed when pressed (COM/NO pair).
- Planned circuit: one terminal to Pro Micro RP2350 `GP2`, the other to
  `TOOL_GND`; firmware input uses `INPUT_PULLUP`, so pressed reads LOW.
- The dry contact is non-polar: either selected terminal may be the `GP2` end.
- The third switch terminal is unused. Do not connect 5 V, the 6 V motor rail,
  or PC817C `CTRL_GND`.

## Mechanical intent

The switch will be fixed to the upper toolhead structure. A block/flag on the
moving linear-rail carriage will press it at the proposed `LIFT_HOME` reference
of `x_lift = 0.535 in` spring compression. It is used only at boot, recovery,
or an explicit service action; ordinary high-cycle M5 operations stop from the
load-cell release threshold plus a separate calibrated clearance pulse. A
distinct mechanical backstop remains required after the electrical trigger and
before spring solid height.

## Required verification

1. Confirm with a meter that terminals `1` and `3` are open released and close
   only when pressed.
2. Verify `GP2` reads HIGH released and LOW pressed with `INPUT_PULLUP`.
3. Perform ten slow guarded retracts, recording trigger and release positions.
4. Verify missing-switch timeout stops the retract command.

## Result

Terminal numbers were identified by the owner. The electrical behavior,
mechanical trigger position, debounce, repeatability, and timeout behavior
remain T-01G evidence to collect.
