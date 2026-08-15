# Lab Note: 2026-08-10 - PC817 interface bench test

## Objective

Verify the hand-built PC817 interface's isolation behavior and determine
whether the installed U3 sample can sink a load comparable to RP23CNC `LIMA`.

## Configuration

- Hardware revisions: hand-built three-PC817C perfboard assembly
- Wiring/pin map: current terminal/net contract in
  `hardware/pc817-interface/PERFBOARD_BUILD.md`
- Firmware build: temporary GP9 toggle sketch on a Pro Micro RP2040
- Instruments: bench supply and digital multimeter
- U3 simulated controller load: bench `+12 V -> 2.2 kΩ -> A_HOME`, bench
  negative to `CTRL_GND`

## Procedure

1. Powered the tool side and toggled GP9 through U3 while measuring A_HOME to
   `CTRL_GND` under the 12 V / 2.2 kΩ load.
2. Tested U1 by grounding ENA to `CTRL_GND` and measuring GP8 to `TOOL_GND`.
3. Removed the ENA jumper and checked the idle GP8 voltage and local 3.3 V rail.
4. Inspected and repaired the assembly after U1 initially drew zero
   controller-side current and U2 initially failed to switch.
5. Used a Pro Micro RP2040 sketch with GP8/GPIO20 configured as external-pullup
   inputs to verify both states of U1 and U2.
6. Verified `CTRL_GND` to `TOOL_GND` was open-circuit after all repairs.

## Results

- U3 output measured approximately 12 V idle and 0.2 V asserted. The tested
  sample therefore sank about 5.4 mA under the simulated load.
- U1 initially drew 0.000 A because PC817 pin 2 was not connected. After pin 2
  was connected to ENA, asserted GP8 measured 54.7 mV.
- The later GP8 diagnosis found that the Pro Micro `3V3` and `GND` had not
  been connected to the tool-side terminal. Once connected, `TOOL_3V3` was
  3.3 V and board-side GP8 was 3.311 V with external loads removed. The U1
  test sketch reported HIGH with ENA open and LOW with ENA shorted to
  `CTRL_GND`.
- U2 initially did not switch. Its input LED measured 1.15 V while AUX0 was
  grounded, and a disconnected wire was then found and soldered. The U2 test
  subsequently passed: GPIO20 changed HIGH with AUX0 open to LOW with AUX0
  shorted to `CTRL_GND`.
- Final power-off test: `CTRL_GND` to `TOOL_GND` had no continuity.

## Interpretation

The installed assembly now passes all three channel tests and the isolation
test. The U3 result is valid for the tested PC817C/sample and load, but does
not change the generic PC817C CTR guarantee. These tests simulate low-side
controller outputs; they do not yet verify the actual RP23CNC ENA/Aux0 terminal
behavior or connect the real `LIMA` input.

## Decisions and next action

- The `A_HOME` to `A_HOME_SW` connection may be a direct wire or a 0 Ω R6 link;
  it was successfully tested at approximately 12 V idle and 0.2 V asserted.
- Keep the controller and tool grounds separate.
- Before connecting the RP23CNC harness, perform F-05 and verify the real
  ENA/Aux0 terminal polarity/current against the controller documentation.

Related: E-18 in `docs/testing/TEST_PLAN.md`, MAG-003/MAG-003B/TH-001B in
`docs/hardware/WIRING_TABLE.md`, and change `HW-20260810-001`.

## Superseding harness note

After this bench session, the project moved the Pro Micro connections from
GP8/GP9/GPIO20 to GP29/GP27/GP28 so the PC817 harness can occupy one physically
consecutive six-position header run. This note remains valid circuit evidence,
but it is not evidence for the new harness. Repeat U1, U2, U3, and isolation
checks after repinning; see `hardware/pc817-interface/PRO_MICRO_JST_HARNESS.md`.
