# Lab Note: 2026-09-22 - Integrated lift drive did not reach GP2

## Objective

Check the corrected integrated motor polarity and determine why the controller
still failed to reach the GP2 maximum-retract switch.

## Configuration

- Firmware: corrected supervised `pro_micro_rp2350_toolhead` build after the
  phase-selection fix.
- Runtime: external toolhead rail and GP20/GP21 UART1 at 115200 baud.
- Observed configuration: `commission=[dir:1 pressure:1 lift:0 mag:0]`.

## Code, commands, and configuration used

```text
Observed telemetry:
pressure=FAULT cmd=M5 fault=GP2 lift-home not reached during retract
cs1238_raw=269488 cs1238_filtered=269299 cs1238_delta=-2978
lift_home=0 mag=DISARMED status=0x00000473
```

## Procedure

1. Boot the corrected integrated build with the pen clear and GP2 reachable.
2. Observe the bounded automatic retract.
3. Stop on the controller's GP2 timeout fault.

## Results

The controller still reported `lift_home=0` after the 700 ms retract timeout.
The DRV8833 fault flag remained clear and the CS1238 samples continued, so the
failure was not an ADC or driver-protection fault. The integrated lift command
was using PWM 70/255, while the validated E-09E UP pulses use full phase drive.

## Difficulties and corrective actions

The first correction fixed the phase selection but left the integrated lift
command at a low PWM that may not overcome static friction in the installed
mechanism. `PWM_LIFT` was changed to 255 to match E-09E's full-drive 5–100 ms
UP pulses. The corrected sketch compiled successfully; no further motion test
was run on this build yet.

## Interpretation

The bounded fault behaved safely, but GP2 has not yet been proven under the
integrated controller. The next retry must use the full-drive lift build and
keep the physical cutoff reachable.

## Decisions and next action

Flash the full-drive build, boot with the pen clear, and verify that GP2
asserts before the timeout. If it still does not, stop and return to a direct
E-09E direction test rather than increasing the timeout blindly.
