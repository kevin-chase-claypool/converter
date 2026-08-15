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

Using the printed driver table previously supplied for this driver style:

- SW1/SW2/SW3 = OFF/ON/OFF selects 4 microsteps, 800 pulses/revolution.
- SW4/SW5/SW6 = ON/OFF/OFF selects 2.0 A.

## Disposition

E-02 is **partial**. The factory configuration is now recorded, but all three
received driver labels/tables and switch numbering must be visually confirmed.

The selected 17HS15-1504S-X1 motors are rated 1.5 A per phase. If each received
driver's printed table matches the recorded table, use the 1.5 A row before the
first motor-power test: SW4 ON, SW5 OFF, SW6 ON. Do not change settings while a
driver is powered.

## Follow-up

Complete E-02 photographs and then E-04 conservative current setup before
attaching a motor to an energized driver.
