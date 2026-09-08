# Lab Note: 2026-09-08 - E-19 ioSender NC E-stop configuration

## Objective

Record the controller control-input configuration after SW1 NC-A was reported
wired to RP23CNC `ESTOP SIG`/`GND` and before the live E-stop test.

## Evidence

The project owner supplied an ioSender 2.0.47 `Settings: Grbl` screenshot with
`Control signals` selected. It shows:

- Setting `14`, `Invert control inputs: 6`.
- Feed hold selected.
- Cycle start selected.
- E-stop clear (not selected).

This matches the expected NC E-stop configuration: `$14=6` retains the
existing Feed Hold and Cycle Start choices while clearing the E-stop inversion.

## Result and remaining test

The configuration snapshot was followed by a live press test. With the
controller initially `IDLE`, pressing SW1 caused ioSender to show `ALARM:10`,
assert the E-stop signal indicator, and report `MSG:Emergency stop, clear then
reset to continue`. This verifies the wired NC contact invokes the controller
Halt/E-stop input.

The test remains partial: it does not yet prove unpowered switch continuity,
release behavior, Reset/Unlock recovery, or absence of automatic restart.
Complete those checks with the pen removed and no job running before marking
E-19 verified.
