# E-11 main-supply no-load path test - 2026-08-20

## Objective

Confirm that the main 12 V supply reaches the HCDC HD064RT fuse-distribution
block with the indicated polarity and is passed through one output pair.

## Configuration

- Hardware revisions: MEISHILE `S-120-12` main supply and installed HCDC
  `HD064RT` fuse-distribution block.
- Wiring/pin map: supply output feeding the fuse-block input; downstream loads
  were not reported connected for this check.
- Instruments: DC-voltage meter, model and accuracy not recorded.

## Code, commands, and configuration used

```text
No firmware, software, or controller commands used.
```

## Procedure

1. Energized the main supply to feed the HD064RT fuse block.
2. Measured DC voltage at the fuse-block input.
3. Confirmed the observed positive and negative polarity matched the block
   markings.
4. Measured one fuse-block output pair.

## Results

- Fuse-block input: 12.05 VDC.
- One output pair: 12.05 VDC.
- The observed polarity matched the HD064RT `+` and `-` markings.

This is partial E-11 evidence. It verifies the no-load supply-to-distribution
path, not the complete supply characterization.

## Difficulties and corrective actions

None reported. The meter model/accuracy and the particular output pair were not
recorded, so they cannot be treated as traceable measurement details.

## Interpretation

The observed voltage is close to the intended 12 V nominal rail and no
polarity reversal was observed at the distribution block. This does not verify
the supply's terminal labeling, protective-earth bonding, adjustment range,
fitted fuse ratings, branch wiring, or loaded behavior.

## Decisions and next action

Keep downstream TB6600 and toolhead loads disconnected until their branch
terminals, fuses, and input behavior have been checked. Complete the remaining
E-11 checks: photograph the label, verify PE/chassis continuity with power
removed, measure at the supply output terminals, and document the safe `+V
ADJ` range without load.
