# PC817C minimum-wire through-hole build

This is the current construction map for the 40.16 × 22.65 mm, 14-column by
6-row perfboard. Columns are `A`–`N`, rows are `1`–`6`, and the pitch is
2.54 mm. All components are through-hole.

Open [`pc817-perfboard-v2-minwire.kicad_pcb`](pc817-perfboard-v2-minwire.kicad_pcb)
in KiCad 10 for the routed view. The two copper layers are a clear electrical
map. On perfboard, reproduce each net with short solder bridges where adjacent
and insulated underside wire where a crossing or longer run is required.

## Terminal order

| Pin | J1 controller side (`A1`–`A6`) | J2 toolhead side (`N1`–`N6`) |
|---:|---|---|
| 1 | `CTRL_5V` | `GP29` |
| 2 | `ENA` | `TOOL_3V3` |
| 3 | NC | `GP28` (`HOME_ARM`) |
| 4 | `AUX0` | `TOOL_GND` |
| 5 | `CTRL_GND` | NC |
| 6 | `A_HOME` | `GP27` |

The unusual order is intentional: it aligns each connector pin with its
channel and eliminates long cross-board wires. Label both terminal blocks;
never infer a pin from its position after rotating the board.

## Components and placement

| Ref | Part | Placement/orientation |
|---|---|---|
| U1 | PC817C DIP-4 | `F1/F2/I2/I1`; notch toward row 1 |
| U2 | PC817C DIP-4 | `F3/F4/I4/I3`; notch toward row 1 |
| U3 | PC817C DIP-4 | `I6/I5/F5/F6`; **rotated 180°**, notch toward row 6 |
| R1, R2 | 680 Ω, ¼ W axial | `B1–D1`, `B3–D3` |
| R3, R4 | 10 kΩ, ¼ W axial | `K1–M1`, `K3–M3` |
| R5 | 390 Ω, ¼ W axial | `J5–M5` |
| R6 | 0 Ω link or direct wire | `B6–E6`; the tested assembly passed the 12 V / 2.2 kΩ test |
| D1, D2 | 1N4148, standing | D1 `E1–E2`, D2 `E3–E4`; stripe/cathode at E1/E3 |
| D3 | 1N4148, axial | `J6–M6`; stripe/cathode at M6 |
| C1, C2 | 47 nF, radial, non-polar | C1 `J1–J2`, C2 `J3–J4` |
| J1, J2 | 1×6 2.54 mm screw terminal | J1 `A1–A6`, J2 `N1–N6` |

C3 is intentionally omitted from the minimum-wire module. It was conventional
100 nF rail bypassing in the earlier map, but the nearby Pro Micro already
decouples its 3.3 V rail and C1/C2 remain as the two signal filters. If later
bench testing shows local rail noise, add 100 nF directly across J2
`TOOL_3V3`/`TOOL_GND`; do not silently add it to unrelated signal pads.

## Complete net list

Every pad on a row below must be electrically common; different rows must not
be continuous.

| Net | Join these pads |
|---|---|
| `CTRL_5V` | `A1`, `B1`, `B3` |
| `ENA` | `A2`, `E2`, `F2` |
| `LED1_A` | `D1`, `E1`, `F1` |
| `AUX0` | `A4`, `E4`, `F4` |
| `LED2_A` | `D3`, `E3`, `F3` |
| `CTRL_GND` | `A5`, `F5` |
| `A_HOME` | `A6`, `B6` |
| `A_HOME_SW` | `E6`, `F6` |
| `GP29` | `I1`, `J1`, `K1`, `N1` |
| `TOOL_3V3` | `M1`, `M3`, `N2` |
| `GP28` | `I3`, `J3`, `K3`, `N3` |
| `TOOL_GND` | `I2`, `J2`, `I4`, `J4`, `I5`, `J6`, `N4` |
| `LED3_A` | `I6`, `J5`, `M6` |
| `GP27` | `M5`, `N6` |

`A3` and `N5` are NC. The Pro Micro direct-header harness is documented in
[`PRO_MICRO_JST_HARNESS.md`](PRO_MICRO_JST_HARNESS.md): its `RST` position is
also NC. Install a direct wire or a 0 Ω R6 link between
`A_HOME` and `A_HOME_SW`; the installed U3 sample passed the specified load
test. Re-test if U3 is replaced.

## Isolation and channel behavior

- U1: controller `CTRL_5V → R1 → U1 LED → ENA`; asserted U1 pulls GP29 to
  `TOOL_GND`. R3 supplies the local 3.3 V pullup.
- U2: controller `CTRL_5V → R2 → U2 LED → AUX0`; asserted U2 pulls GP28 to
  `TOOL_GND`. R4 supplies the local 3.3 V pullup.
- U3: toolhead `GP27 → R5 → U3 LED → TOOL_GND`; asserted U3 connects
  `A_HOME_SW` to `CTRL_GND`. The fitted R6/direct wire joins that switch node
  to the RP23CNC `A_HOME` terminal.
- D1–D3 are reverse-parallel clamps across the three internal PC817 LEDs. They
  do not carry the normal forward signal current.

`CTRL_GND` and `TOOL_GND` must never be wired together. Optical coupling is the
only connection between those electrical domains.

## Build and test order

1. Dry-fit J1/J2 and confirm the right-side mounting-hole clearance.
2. Fit U1/U2 in the normal orientation and U3 rotated 180 degrees.
3. Fit the resistors, standing D1/D2, axial D3, C1/C2, and the R6/direct A_HOME
   link.
4. Wire one complete net at a time from the table. Mark it off only after both
   continuity within that net and isolation from neighboring nets pass.
5. With power off, confirm `CTRL_GND` to `TOOL_GND` is open-circuit.
6. Power only the tool side. GP29 and GP28 should be near 3.3 V idle. Grounding
   ENA/AUX0 on a separately powered 5 V controller-side test supply should pull
   the corresponding GPIO near 0 V.
7. Test U3 with an isolated bench supply: `+12 V → 2.2 kΩ → A_HOME`, supply
   negative to `CTRL_GND`, and drive GP27 from the Pro Micro. Expect about 12 V
   idle and below roughly 0.4 V asserted. The tested assembly measured 0.2 V
   asserted.
8. Repeat all three functional tests after the board is mounted and before
   connecting it to RP23CNC.
