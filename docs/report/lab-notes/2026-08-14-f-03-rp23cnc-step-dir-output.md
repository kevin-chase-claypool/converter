# Lab Note: 2026-08-14 - F-03 RP23CNC STEP/DIR/ENABLE output check

## Objective

Identify and verify the RP23CNC's bare X/Y/A STEP, DIR, and ENABLE outputs
before any TB6600 input or motor is connected.

## Safe configuration

- USB and the isolated-input 12 V supply connected.
- Main 12 V machine power off.
- All TB6600 inputs, motors, and PC817 controller-side wiring disconnected.
- Measurements referenced only to the `GND` terminal in the same axis output
  group; no isolated-input ground was used as a meter reference.

## X-axis observations so far

The meter's black probe was on X output-group `GND`.

### X DIR

With the red probe on X `DIR`, commands were sent one at a time:

```text
M5
G91
G0 X10 F60
G0 X-10 F60
G90
```

Observed: `DIR` was 0 V through the positive move, changed to 5 V during the
negative move, and remained at 5 V afterward. `G90` did not change it.

### X STEP

With the red probe on X `STEP`, idle and `G91` were 0 V. Each 10-second X move
briefly produced approximately 50 mV on the DC meter; it returned to 0 V after
the move and after `G90`.

### X ENABLE

With the red probe on X `EN`/`ENA`, the idle value was 5 V. `G91` and `G90`
did not change it. During either `G0 X10 F60` or `G0 X-10 F60`, it changed to
0 V and returned to 5 V when motion completed.

## Interpretation

The X direction output holds the commanded direction level, and the DC meter
observed the expected low average of short STEP pulses. X `EN` is active-low:
5 V idle and 0 V while motion is commanded. A multimeter cannot prove pulse
width or edge timing; a frequency-capable meter, logic analyzer, or oscilloscope
would provide stronger pulse evidence. The Y and A groups remain to be checked.

## Y-axis observations

With the black probe on Y output-group `GND`:

| Signal | Idle | `G0 Y10 F60` | `G0 Y-10 F60` | Result |
|---|---:|---:|---:|---|
| `DIR` | 0 V | 0 V | 5 V, held after move | Direction level changes correctly. |
| `STEP` | 0 V | about 50 mV briefly | about 50 mV briefly | DC-meter average indicates pulse activity only while moving. |
| `EN`/`ENA` | 5 V | 0 V during move, then 5 V | 0 V during move, then 5 V | Active-low enable. |

## A-axis observations

With the black probe on A output-group `GND`:

| Signal | Idle | `G0 A10 F60` | `G0 A-10 F60` | Result |
|---|---:|---:|---:|---|
| `DIR` | 0 V | 0 V | 5 V, held after move | Direction level changes correctly. |
| `STEP` | 0 V | about 50 mV briefly | about 50 mV briefly | DC-meter average indicates pulse activity only while moving. |
| `EN`/`ENA` | 5 V | 0 V during move, then 5 V | 0 V during move, then 5 V | Active-low enable. |

## Final result

F-03 passed for X, Y, and A. Every tested axis has the same observed output
contract: `DIR` is a held 0/5 V direction level, `STEP` is a 5 V pulse train
whose DC average appears only during motion, and `EN` is active-low (5 V idle,
0 V while motion is commanded). The test used no powered or connected stepper
driver, motor, or PC817 controller-side harness.

The DC meter is sufficient to establish preliminary STEP activity but does not
measure pulse width, exact amplitude, or edge quality. The TB6600 input test
will independently verify the final connection topology and real motion.

## Next action

Perform F-04 limit-input behavior and polarity testing before attaching motor
drivers. Then perform E-03 with one TB6600 input circuit and its actual
connection topology.
