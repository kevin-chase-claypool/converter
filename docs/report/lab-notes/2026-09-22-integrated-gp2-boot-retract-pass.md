# Lab Note: 2026-09-22 - Integrated GP2 boot retract pass

## Objective

Verify that the supervised integrated Pro Micro build retracts the toolhead to
the GP2 maximum-UP switch and stops there.

## Configuration

- Hardware: Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238, TMAG5273,
  and GP2 lift-home switch.
- Wiring: GP2 normally-open contact to local `TOOL_GND`; telemetry/commands on
  UART1 GP20/GP21 at 115200 baud.
- Firmware: `pro_micro_rp2350_toolhead`, repository commit `022d640`.
- Build settings: full lift drive (`PWM_LIFT=255`), supervised mechanical
  preload mode, 3000 ms boot lift timeout.
- Commissioning telemetry: `dir:1 pressure:1 lift:0 mag:0`.

## Code, commands, and configuration used

```text
Firmware: firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino
Boot behavior: LIFTING continues UP until GP2 reports pressed, or 3000 ms elapses.
Key telemetry after reset:
13:34:45.476 -> Theta toolhead service UART ready
13:34:55.665 -> pressure=LIFTING cmd=M5 fault=none lift_home=0 samples=497
13:34:56.655 -> pressure=LIFTED cmd=M5 fault=none lift_home=1 samples=997
```

## Procedure

1. Flash the supervised integrated build with external motor power disconnected.
2. Reconnect the external rail and UART1, with the pen clear and GP2 reachable.
3. Observe the startup lift and recurring status telemetry.

## Results

The new boot began in `LIFTING` with `lift_home=0`, then reached `LIFTED` with
`lift_home=1` and `fault=none` by the next one-second telemetry sample. Later
records remained `LIFTED`, `lift_home=1`, and `fault=none`. Earlier FAULT lines
in the supplied serial buffer preceded the new `Theta toolhead service UART
ready` line and were from the previous boot.

## Difficulties and corrective actions

The previous build attempt had stopped with `GP2 lift-home not reached during
retract`. The timeout was extended to 3000 ms while GP2 remained the immediate
stop condition. The next boot reached GP2 successfully.

## Interpretation

The integrated boot retract and semantic GP2 state now work together: the
controller drives UP from the released state and stops at the pressed/home
state. This proves the observed boot-to-switch behavior, but the telemetry
still reports `lift:0`, so the separate formal lift-reference commissioning
gate remains unset.

## Decisions and next action

Proceed to one supervised M3 test: after confirming `pressure=LIFTED`,
`lift_home=1`, and `fault=none`, send `e` over UART1. Observe the 100 ms DOWN
preload followed by CS1238 moving-average force control. Send `l` to end that
single test; keep the physical cutoff accessible.
