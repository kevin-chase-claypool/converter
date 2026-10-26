# E-02 TB6600 factory switch observation - 2026-08-15

## Objective

Record the received TB6600 six-switch factory state before selecting the final
microstep and motor-current settings.

## Observation

The project owner reported the factory state as:

| Switch | State |
|---|---|
| SW1 | OFF |
| SW2 | ON |
| SW3 | OFF |
| SW4 | ON |
| SW5 | OFF |
| SW6 | OFF |

Using the received driver's printed table, photographed on 2026-08-15, and the
B0FQ5GBNZ1 product-label image inspected on 2026-08-19:

- SW1/SW2/SW3 = OFF/ON/OFF selects 8 microsteps, 1600 pulses/revolution.
- SW4/SW5/SW6 = ON/OFF/OFF selects 2.0 A.

## Disposition

E-02 is **partial**. The factory configuration is now recorded, but all three
received driver labels/tables and switch numbering must be visually confirmed.

The selected 17HS15-1504S-X1 motors are rated 1.5 A per phase. The listing
label identifies its 1.5 A row as SW4 ON, SW5 OFF, SW6 ON. For the initial
axis-specific microstepping configuration, set X/Y to 16× (SW1 OFF, SW2 OFF,
SW3 ON) and A to 8× (SW1 OFF, SW2 ON, SW3 OFF). Do not change settings while a
driver is powered.

## Correction

An earlier same-day transcription incorrectly read the microstep row as 4. A
later project record then incorrectly transcribed the 1.5 A row as ON/ON/OFF.
The B0FQ5GBNZ1 listing label resolves both errors: 16× is OFF/OFF/ON, 8× is
OFF/ON/OFF, and 1.5 A is ON/OFF/ON.

## Follow-up

Complete E-02 photographs and then E-04 conservative current setup before
attaching a motor to an energized driver.

## Correction - 2026-10-26

The current B0FQ5GBNZ1 product images show the complete six-switch table:

| Current / peak | SW4 | SW5 | SW6 |
|---|---|---|---|
| 1.5 A / 1.7 A | ON | ON | OFF |
| 2.8 A / 2.9 A | OFF | OFF | ON |

The product table also retains:

- `8x`: SW1/SW2/SW3 = OFF/ON/OFF.
- `16x`: OFF/OFF/ON.

This supersedes the earlier `1.5 A = ON/OFF/ON` transcription in this note.
The physical label on each received driver remains the final authority because
generic TB6600 clones use incompatible tables.
