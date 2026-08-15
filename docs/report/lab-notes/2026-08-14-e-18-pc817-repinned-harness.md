# Lab Note: 2026-08-14 - E-18 PC817 repinned-harness verification

## Objective

Repeat the PC817 isolation and channel tests after moving the toolhead interface
from the earlier GP8/GPIO20/GP9 arrangement to GP29/GP28/GP27.

## Configuration

- Hardware: hand-built three-PC817C perfboard; SparkFun Pro Micro RP2350
- Wiring: J2.1 GP29, J2.3 GP28, J2.6 GP27, J2.2 TOOL_3V3, J2.4 TOOL_GND
- Instruments: digital multimeter; supplies remain disconnected for this stage

## Code, commands, and configuration used

```text
No firmware or command was used in this unpowered isolation/static-voltage stage.
```

## Procedure

1. Disconnected the 6 V toolhead supply, Pro Micro USB-C, UART adapter, and
   controller-side test supplies.
2. Measured continuity between J1.5 CTRL_GND and J2.4 TOOL_GND.
3. Powered the toolhead side and measured J2.2 TOOL_3V3 and J2.1 GP29 relative
   to J2.4 TOOL_GND, with controller-side terminals unpowered.

## Results

- J1.5 CTRL_GND to J2.4 TOOL_GND: no continuity beep.
- TOOL_3V3 to TOOL_GND: 3.3 V.
- GP29 to TOOL_GND, idle: 2.739 V, a valid logic-HIGH level.
- Disposition: repinned-harness pre-check passed. U1, U2, and U3 had already
  passed functional bench switching on the identical perfboard circuit before
  the Pro Micro pins were moved. The current harness had separately passed
  continuity for GP29, GP28, and GP27. Repeating the channel switching solely
  because of the pin reassignment is not required.

## Difficulties and corrective actions

None encountered in this stage.

## Interpretation

The required galvanic separation survives the repinned harness, and U1's
tool-side pullup is present. The lower-than-rail idle voltage is still safely
HIGH for the RP2350. Together with the documented prior U1/U2/U3 switching
test and the harness continuity checks, the PC817 board and its new tool-side
pin assignment are accepted for bench use.

## Decisions and next action

Keep the controller and tool grounds separate. The next required validation is
the real RP23CNC terminal integration: F-05 must establish the actual ENA and
Aux0 sink/polarity behavior, and the installed controller's LIMA input must be
verified before connection.
