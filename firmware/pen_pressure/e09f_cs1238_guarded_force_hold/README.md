# E-09F guarded CS1238 force-hold test

This temporary test uses the accepted E-09C precision-weight CS1238 profile to
perform a supervised installed-pen seek/hold and pen-clear check. It is not the
production toolhead firmware: it does not use GP29/M3/M5, GP27, or magnetic
logic, and it does not authorize drawing.

## Power and serial path

Flash through USB-C only while the external toolhead rail is disconnected.
Then unplug USB-C, restore the external 6 V/5 V toolhead rail, and use the
existing 3.3 V USB-to-TTL adapter:

- Adapter `RXD` ← Pro Micro `GP20` TX
- Adapter `TXD` → Pro Micro `GP21` RX
- Adapter `GND` → `TOOL_GND`
- Adapter `VCC` remains disconnected

Open Arduino IDE Serial Monitor on the adapter COM port at 115200 baud. It
must be the only application holding that port. Keep the physical 6 V cutoff
reachable and put the kitchen scale below the installed pen.

## Commands

| Command | Action |
|---|---|
| `?` | Print help and status. |
| `t` | Collect a 64-sample clear-state tare with the pen off the scale. |
| `a` | Arm one automatic test; reset each direction's 30-pulse budget. |
| `s` | Seek/hold the calibrated 40–60 g raw band for five seconds. |
| `c` | From contact, lift in 5 ms steps to the 3 g clear band, then issue one 100 ms air-gap pulse. |
| `r` | Print a 16-sample CS1238 raw mean and tare delta. |
| `x` | Stop/sleep/disarm immediately. |

The sketch has a 30 second automatic-test timeout, a 70 g raw hard limit, 30
pulses per direction, 500 ms settling between corrections, and GP2 LIFT_HOME
blocking before every UP pulse. It sleeps the driver after every pulse.

## Procedure

1. With the pen clear, send `t`, then `a`.
2. Send `s`; watch the scale and serial output. Use `x` or the physical cutoff
   immediately if the motion is implausible.
3. A pass prints `HOLD_COMPLETE`; record scale range, correction count, any
   faults, and whether it stayed approximately 40–60 g.
4. With the scale still under the pen, send `a`, then `c`. Verify the pen
   clears the scale/paper after the explicit 100 ms air-gap pulse without
   reaching the LIFT_HOME switch. A pass prints `CLEAR_COMPLETE`.

This is a one-cycle qualification. It does not establish normal M3/M5 behavior;
T-01H still requires actual tip-gap measurement and repeated clear cycles.
