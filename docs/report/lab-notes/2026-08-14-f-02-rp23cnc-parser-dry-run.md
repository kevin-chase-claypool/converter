# Lab Note: 2026-08-14 - F-02 RP23CNC parser dry run

## Objective

Verify that the flashed grblHAL baseline accepts the G-code subset emitted by
the converter before any driver, motor, or toolhead-control wiring is attached.

## Safe test configuration

- USB connected to ioSender.
- `ISO 12V` input supplied so the control-input state remains `IDLE`.
- Main 12 V machine power off.
- TB6600 drivers, motors, and PC817 controller-side wires disconnected.

## Commands and exact result

Each line was sent separately through ioSender MDI.

```text
G21
ok
G90
ok
G0 X0 Y0 A0 F100
ok
G1 X0 Y0 A0 F100
ok
M3
ok
G4 P0.1
ok
M5
ok
M2
[MSG:Pgm End]
ok
[GC:G1 G54 G17 G21 G90 G94 G49 G98 G50 M5 M9 T0 F100 S0.]
ok
```

## Result

F-02 passed. The controller accepted millimeter units, absolute positioning,
zero-distance coordinated `G0`/`G1` XYZA moves, M3/M5 tool commands, a
seconds-based dwell, and program end. The final modal report shows `G21`,
`G90`, feed `F100`, and safe tool state `M5`. No drivers, motors, or toolhead
interface were attached, so no physical machine movement occurred.

## Difficulties and corrective actions

None during this test. The earlier first-run Alarm 10 was cleared before the
test by supplying `ISO 12V`, applying the documented control-input inversion,
and unlocking the controller.

## Next action

Perform F-03: identify and measure the unpowered STEP/DIR/ENABLE outputs before
connecting any TB6600 driver inputs.
