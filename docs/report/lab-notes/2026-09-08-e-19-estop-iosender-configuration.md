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

The owner then twist-released SW1, selected Reset, and selected Unlock. The
follow-up ioSender screenshot shows `MSG:Caution: Unlocked` and state `IDLE`.
No motion was reported. This passes the release, deliberate recovery, and
no-automatic-restart portions of E-19.

With all power removed, the owner meter-tested NC-A terminal `1`–`2`: the
meter beeped when the mushroom was released and did not beep when it was
pressed. This is the required normally-closed contact behavior. NC-B remains
unused and individually insulated.

E-19 passed: the physical NC contact, RP23CNC E-stop/Halt input, deliberate
Reset/Unlock recovery, and no-automatic-restart behavior are verified. This
does not change the design boundary: SW1 is a controller-signal stop and does
not remove motor or toolhead 12 V.
