# Lab Note: 2026-08-14 - E-17 RP23CNC pre-power inspection

## Objective

Establish that the received RP23U5XBB V1.01 controller is safe for its first
USB-only firmware flash and baseline boot.

## Configuration

- Hardware: Brookwood Design RP23CNC / RP23U5XBB V1.01
- External connections: USB and 12 V supply disconnected during inspection
- Instruments: magnifying glass and digital multimeter in continuity mode

## Code, commands, and configuration used

```text
No firmware was running. This was an unpowered visual and continuity test.
```

## Procedure

1. Inspected all accessible solder joints under magnification.
2. With the board unpowered, measured the main 12 V input positive to negative
   terminals in continuity mode.
3. With the board unpowered, measured the labeled 5 V source-selector rail to
   board ground in continuity mode.

## Results

- Solder joints appeared complete and free of visible bridges under magnification.
- Main 12 V input positive to negative: no continuity beep.
- 5 V rail to ground: no continuity beep.
- Disposition: E-17 passed. USB-only first flash may proceed with all 12 V,
  drivers, motors, and PC817 controller-side wires disconnected.

## Difficulties and corrective actions

None encountered.

## Interpretation

The pre-power inspection found no visible solder defect or low-resistance rail
short. It does not verify functional I/O; that begins with F-01 after flashing.

## Decisions and next action

Flash the archived RP23U5XBB grblHAL baseline UF2 through BOOTSEL using USB
only, capture the boot banner, and record F-01 results.
