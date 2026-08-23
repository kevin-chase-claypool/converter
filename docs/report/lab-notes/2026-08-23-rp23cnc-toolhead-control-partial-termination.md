# Lab Note: 2026-08-23 - RP23CNC toolhead-control partial termination

## Objective

Record the owner-reported controller-side termination progress for the PC817C
toolhead-control harness without implying electrical verification.

## Observation

The owner supplied an annotated image of the PC817C interface board and
reported that its lime-circled controller-side terminals are now wired at the
RP23CNC:

- J1.1 `CTRL_5V`
- J1.2 `ENA`
- J1.4 `AUX0`
- J1.5 `CTRL_GND`

J1.6 `A_HOME` was not circled and remains unconnected at the controller. The
proposed `PRB` endpoint remains uninstalled and test-gated.

## Evidence boundary

This is an owner report plus a board-side image only. It does not establish
the exact RP23CNC terminal labels, conductor continuity, control/tool-ground
isolation, ENA/AUX0 polarity or current, controller output behavior, or any
energized operation.

## Required next action

With power removed, continuity-check the four installed conductors and confirm
`CTRL_GND` remains isolated from `TOOL_GND`. Then perform F-05/E-18 before
energizing the interface. Leave J1.6 disconnected from `PRB`; it remains
assigned to `LIMA` unless and until F-08 passes.
