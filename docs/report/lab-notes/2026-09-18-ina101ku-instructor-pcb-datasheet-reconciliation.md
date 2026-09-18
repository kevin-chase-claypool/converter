# INA101KU instructor load-cell PCB: datasheet reconciliation

**Date:** 2026-09-18
**Scope:** Identify what can be concluded from the supplied PCB-layout and board photographs, and what still requires a power-off continuity test before wiring the Pico 2.

## Evidence boundaries

The two supplied images are PCB-layout/trace artwork and photographs of the instructor's board. They show a surface-mount INA101KU, a rear five-position terminal block labelled `OUT`, `5V`, `+V`, `-V`, `GND`, a 100 kOhm trim potentiometer, a fixed 4.3 kOhm resistor, bypass capacitors, and a four-pad load-cell footprint. The images do not provide a complete netlist, pin numbers, or a verified bridge-wire map. A visible trace is therefore treated as design evidence, not as a substitute for a DMM measurement on the physical board.

## Official INA101 facts

The TI/Burr-Brown INA101 datasheet identifies `INA101KU` as the SOL-16 package (datasheet pp. 2-3). In the SOL-16 top-view pinout, the functional pins are: pin 1 `Output`, pin 2 `+VCC`, pin 3 `-Input`, pins 4/5 `Gain Sense 1`/`Gain Set 1`, pins 6/7 offset adjust, pin 9 `Common`, pin 10 `-VCC`, pin 11 `+Input`, pins 12/13 `Gain Sense 2`/`Gain Set 2`, and pins 14/15 internal amplifier outputs. Pins 8 and 16 are NC.

The data sheet specifies the gain relationship `G = 1 + 40 kOhm/RG` and says that the external gain resistor is connected to the gain-set network. If the board's marked 4.3 kOhm resistor is that `RG`, its nominal gain is:

```text
G = 1 + 40,000 / 4,300 = 10.30 V/V
```

The datasheet also shows optional 100 kOhm trim circuits for offset adjustment. Consequently, the board's 100 kOhm potentiometer should not be assumed to be a gain control. The fixed 4.3 kOhm part is the stronger candidate for the gain-setting resistor; the potentiometer's actual role must be confirmed by continuity to the INA101 offset-adjust pins.

The INA101 operating supply range is ±5 V to ±20 V, with ±15 V used for the data-sheet specifications. Its `Common` pin is the output reference and should be a low-impedance reference; the data sheet normally shows it grounded. The amplifier output is not intrinsically limited to Pico-safe voltage: the output can swing toward either supply, subject to headroom. A Pico ADC input must therefore be connected only after the board output has been measured relative to board `GND`/`Common` under the intended load.

Primary source: [TI INA101 data sheet](https://www.ti.com/lit/ds/symlink/ina101.pdf), especially the SOL-16 pinout and gain/offset application figures on pp. 2-6.

## What the board images support

The rear connector labels are the board's external interface, not INA101 pin names. The most consistent functional interpretation is:

| Board terminal | Current interpretation | Confidence and limitation |
|---|---|---|
| `OUT` | Conditioned INA101 output to the Pico ADC through the planned protection/series resistor | High from label; output voltage range still must be measured. |
| `+V` | Positive INA101 supply rail | High from label and the INA101 pin function; exact board net must still be proven. |
| `-V` | Negative INA101 supply rail | High from label and the INA101 pin function; exact board net must still be proven. |
| `GND` | Board signal/common reference, likely INA101 `Common` and bridge return | Plausible, but do not join it to another ground until continuity and supply polarity are checked. |
| `5V` | Board-specific 5 V connection, most likely bridge excitation positive | The layout routes the labelled connector into the load-cell area, and a strain-gauge bridge needs excitation. This is not an INA101 supply pin. Confirm by continuity and voltage tests. |

The four-pad `load cell` footprint shown in the layout and underside photograph indicates that the reference strain gauge is part of this instructor board assembly. Therefore the test wiring should use the rear green terminal block; do not infer an additional user-accessible sensor connector from the footprint. The bridge's individual `E+`, `E-`, `A+`, and `A-` mapping remains an internal board-design question unless the instructor provides the netlist.

The likely supply arrangement remains one series-linked, bipolar bench supply: `+5 V` to board `+V`, 0 V to board `GND`, and `-5 V` to board `-V`. If continuity proves that the board `5V` terminal is bridge excitation, branch that terminal from the same +5 V rail. This is one physical supply arrangement with two positive-side board connections, not evidence for a third supply. Keep `5V` disconnected until the mapping is verified.

## Required verification before Pico connection

With all supplies and the Pico disconnected:

1. Identify the terminal columns on the actual rear green connector and record left-to-right order; do not rely on a rotated photograph.
2. Continuity-map `+V`, `-V`, `GND`, and `OUT` to the INA101 SOL-16 pins above. Confirm `GND` reaches pin 9 (`Common`) and that `OUT` reaches pin 1.
3. Measure between the gain-set pins (4/5 and 12/13 as applicable to the board's trace implementation) to determine whether the 4.3 kOhm resistor is `RG`. Record the resistance at both 100 kOhm trim extremes and identify which INA101 offset-adjust pins the trim touches.
4. Continuity-map `5V` to the bridge excitation node(s), and measure the bridge resistance between the internal load-cell pads. Do not power a guessed bridge connection.
5. With a current-limited ±5 V supply and no Pico connected, measure `OUT` to board `GND` at no load and throughout the intended force range. It must remain inside 0-3.3 V before it can reach Pico ADC0. If it does not, add an explicitly designed divider/level-shift stage or use an external ADC; do not clip the signal at the Pico input.
6. Connect board `GND` to Pico `AGND` only after the above checks pass. Record actual rail voltages, output baseline, output span, gain-trim position, and sensor orientation in the calibration metadata.

This evidence does not change the existing raw-data requirement: the Pico should retain timestamped raw ADC values, while the reference-channel calibration to force is performed later during analysis.
