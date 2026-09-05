# Lab Note: 2026-09-05 - RP23CNC USB source-selector recovery

## Objective

Restore RP23CNC USB recognition before the TB6600 STEP/DIR/ENA signal test.

## Configuration and symptom

- Controller: Brookwood Design RP23CNC / RP23U5XBB V1.01
- Selector: front-side `SWC USB` 5 V source jumper
- Symptom: laptop did not recognize the RP23CNC when USB was connected
- TB6600 motors: not part of this diagnostic

## Procedure

1. Confirmed that the selector was on `SWC` while the RP23CNC main 12 V input
   was not supplying the board.
2. With power removed, moved the selector to `USB`.
3. Reconnected the USB-C data cable to the laptop.

## Result

USB recognition returned after selecting `USB`. This establishes that the
previous non-recognition was caused by selecting the onboard switching-converter
source without applying the required 12 V main input.

## Interpretation and limits

The RP23CNC USB command path is available for the upcoming TB6600 signal test.
This result does not verify STEP, DIR, or ENA behavior. For the planned test
with the RP23CNC powered from the 12 V main supply and USB used for ioSender,
return the selector to `SWC` before applying power.

## Next action

Run E-03 one TB6600 at a time with motors disconnected, using the RP23CNC
signal common as the oscilloscope reference.
