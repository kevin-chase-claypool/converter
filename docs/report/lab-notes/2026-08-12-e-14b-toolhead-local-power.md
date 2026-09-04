# Lab Note: 2026-08-12 - E-14B Toolhead Local Power

## Objective

Verify the newly assembled toolhead perfboard's local power branches before
connecting the permanent 6 V drag-chain harness or the N20 motor.

## Configuration

- Hardware: shared toolhead perfboard carrying the DRV8833 and Pololu S7V8F5;
  SparkFun Pro Micro RP2350 connected to the S7V8F5 output.
- Input: bench power supply set to 6.0 V, connected at the local two-pin JST.
- Motor: N20 disconnected; DRV8833 `OUT1` and `OUT2` intentionally open.
- Instruments: multimeter; exact numeric readings were not recorded.

## Procedure

1. Checked continuity of all installed power conductors.
2. Checked continuity of every currently wired Pro Micro logic conductor,
   including the DRV8833 logic interface.
3. Checked continuity between the S7V8F5 power/ground terminals and the Pro
   Micro power/ground terminals.
4. Connected a bench supply set to 6.0 V to the local two-pin JST.
5. Measured the DRV8833 and Pro Micro supply voltages with a multimeter.

## Results

- Power-conductor continuity: passed.
- All currently wired Pro Micro logic conductors: continuity passed.
- S7V8F5-to-Pro-Micro power and ground continuity: passed.
- The local JST delivered power to both the DRV8833 and S7V8F5 input.
- The DRV8833 and Pro Micro measured the expected supply voltages.
- **Follow-up correction:** the exact ACEIRMC B08RMWTDLM listing identifies
  `ULT` as the low-true sleep input and `EEP` as the protection/fault output.
  The installed GP6→`EEP` and GP7→`ULT` physical endpoints are therefore
  correct. The earlier *firmware* assignment was reversed; it now maps GP6 as
  `EEP` input and GP7 as `ULT` output. No solder rework is required.

## Interpretation

The local 6 V branch, the S7V8F5-to-Pro-Micro 5 V branch, and all currently
wired Pro Micro logic endpoints are connected with the intended topology. This
does not test the upstream D36V50F6, permanent drag-chain cable, PC817 ground
isolation, or behavior while the motor and sensors draw current. The DRV8833
sleep/fault pair must first be function-checked as E-14C, including the J2
sleep-control bridge.

The E-05 direction-test sketch is a one-shot boot test so it can be run from
the 6 V toolhead supply without simultaneously powering the Pro Micro through
a normal USB cable. Upload it with 6 V disconnected, unplug USB, then apply 6
V and observe the two short motion pulses.

## 2026-08-13 E-05 direction result

- With the N20 connected, the first command pulse retracted/lifted the pen and
  the reverse pulse moved it down. This verifies GP7/`ULT`, GP6/`EEP`,
  `IN1`/`IN2`, the selected driver channel, and the motor's basic bidirectional
  operation from the 6 V bench supply.
- The intermittent behavior was traced to an inadequately soldered DRV8833
  output pin, not the motor lead. The joint was repaired; the motor now runs
  reliably under the E-05 code. No-load current is still required before
  integrated operation.

## 2026-08-14 E-05 no-load current result

With the bench supply set to 6.0 V, the assembled toolhead drew 0.017 A idle.
The reliable N20 retract/lift pulse and the pen-down pulse each drew 0.043 A,
so the motor contribution was approximately 0.026 A in either direction. This
passes E-05. No manual stall test was performed; any later E-06 work must use a
defined mechanical condition and bench-supply current limit rather than hand
resistance.

## 2026-08-14 E-15A motor-motion rail result

With the 6.0 V bench input and N20 moving in both directions, DRV8833 `VM` to
`GND` remained near 6 V and the S7V8F5 5 V output to `TOOL_GND` remained near
5 V. The Pro Micro did not reset or restart. This passes E-15A for the current
motor-only configuration; sensor load, ripple, temperature, and the final
upstream D36V50F6 rail remain unmeasured.

## 2026-09-04 E-05 alignment correction

The owner clarified that the corrected **unloaded N20 motor-motion current is
0.009 A**. The earlier 0.043 A motion reading included extra mechanical load
because the lead screw was not nearly straight against the heat-set insert.
After correcting that alignment, 0.009 A is the appropriate unloaded-motion
baseline. The earlier 0.043 A result remains useful as evidence that the rail
survived a higher accidental alignment load, but it must not be used as the
normal unloaded N20 current. This correction does not replace the separate
spring-installed preload observation.

## Decisions and next action

Record exact voltage readings in the next powered session. Complete the
remaining E-14B inspection points, then test the D36V50F6 in E-14. Fit the N20
only after the 22 AWG motor pair is installed; then proceed to E-05 and T-01.
