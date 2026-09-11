# Lab Note: 2026-09-11 - P100 Q1 GP27/U3 PRB handshake

## Objective

Confirm the installed GP27/U3 path reaches the RP23CNC PROBE SIG input under
a sufficiently long asserted interval, then verify that the controller-resident
non-motion P100 Q1 macro automatically detects both assertion and release.

## Configuration

- Toolhead firmware: firmware/pen_pressure/p100_handshake_test/p100_handshake_test.ino.
- Controller input: blue J1.6 A_HOME conductor at RP23CNC PROBE SIG;
  J1.5 CTRL_GND remains at PROBE GND.
- Controller configuration: $6=1; TB6600 fuses remain removed.
- Macro files: P100.macro and P105.macro on the controller SD card.

## Verification

1. With the toolhead released and the magnet away, telemetry reached
   DISARMED baseline=1 detected=0 arm=0.
2. G65 P105 held READY_ACK. While READY_ACK baseline=1 detected=0 arm=1,
   PROBE SIG measured 173.4 mV relative to PROBE GND.
3. At P105 completion the command released Aux0; telemetry progressed through
   WAIT_REARM to DISARMED, and the controller P indication returned blank.
4. G65 P100 Q1 produced Pn:ZAP during assertion, Pn:ZA after release, and
   the message P100 Q1 readiness handshake passed followed by ok.

## Result

The complete installed GP27 -> R5 -> U3 -> blue conductor -> PROBE SIG path is
working as a controller-visible low-side return. No U3-path resoldering is
indicated. The automated Q1 macro is verified only as a non-motion
readiness/release gate.

## Remaining boundaries

Do not run Q2–Q4 as a continuation of this result. They remain separately
commissioning-gated: Q2 includes physical homing; Q3/Q4 include magnetic
motion and coordinate registration.
