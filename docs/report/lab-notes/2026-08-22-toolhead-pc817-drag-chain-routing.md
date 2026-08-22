# Toolhead PC817 drag-chain routing - 2026-08-22

## Objective

Record the physical routing milestone for the planned controller-side PC817
toolhead harness without treating it as an electrical connection or test.

## Configuration

- Moving interface: three-channel PC817C toolhead module, controller-side J1
  terminal block.
- Routed conductors: RP23CNC `5V`, spindle `ENA`, `Aux 0`, controller-side
  `GND`, and `LIMA`/`A_HOME` through the drag chains.
- J1 mapping: J1.1 `CTRL_5V`, J1.2 `ENA`, J1.4 `AUX0`, J1.5 `CTRL_GND`, and
  J1.6 `A_HOME`; J1.3 remains intentionally unused.

## Result

The owner reported that all five planned controller-side PC817 conductors were
routed through the drag chains. No endpoint termination, continuity test,
controller-output measurement, powered test, or motion test was reported.

## Required next action

With power removed, label and continuity-check each conductor end-to-end, then
confirm `CTRL_GND` has no continuity to `TOOL_GND`. Keep the RP23CNC-side
`ENA`, `Aux 0`, and `LIMA` ends disconnected until the F-05/E-18 controller
and isolation checks authorize connection.
