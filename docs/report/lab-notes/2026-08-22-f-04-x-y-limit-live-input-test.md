# F-04 X/Y limit live-input test - 2026-08-22

## Objective

Verify that the installed X and Y normally-closed roller limit switches reach
the intended RP23CNC limit inputs and report only when their respective switch
is pressed.

## Configuration

- Controller: RP23CNC / RP23U5XBB, connected to ioSender 2.0.47.
- X switch: HiLetgo KW12-3 `COM` to `LIM X SIG` (yellow); `NC` to `LIM X
  GND` (green).
- Y switch: HiLetgo KW12-3 `COM` to `LIM Y SIG` (yellow); `NC` to `LIM Y
  GND` (green).
- Controller settings: limit-input inversion `$5=0`; hard limits disabled
  (`$21=0`) for this reporting-only test.

## Procedure

1. Confirmed with a meter that each switch has `COM`-`NC` continuity with its
   lever released and an open circuit while pressed.
2. Confirmed the controller terminal labels `LIM X SIG/GND` and `LIM Y
   SIG/GND`.
3. Used ioSender's live Signals display with both switches released, then
   pressed each switch individually.

## Results

- With both switches released, X and Y were inactive in the Signals display.
- Pressing X made only X active; releasing it returned X inactive.
- Pressing Y made only Y active; releasing it returned Y inactive.
- No limit-input inversion is required: `$5=0` remains the recorded setting.

## Limitations and next action

This is partial F-04 evidence. Hard limits remain disabled while the unused
Z/A and future A-index inputs are unresolved. The test did not prove a
hard-limit alarm, a broken-wire response, permanent cable routing, or homing.
After unused inputs have deterministic inactive states, test one deliberate
hard-limit alarm with all motion hazards controlled before enabling `$21=1`.
