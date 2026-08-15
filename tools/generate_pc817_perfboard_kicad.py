"""Generate KiCad's all-through-hole 14 x 6 perfboard assembly layout.

This board intentionally has no copper tracks: it documents component holes and
the ratsnest for the insulated underside point-to-point wiring in
hardware/pc817-interface/PERFBOARD_BUILD.md.
"""

from pathlib import Path


OUT = Path("hardware/pc817-interface/pc817-perfboard-v1.2.kicad_pcb")
PITCH = 2.54
X0, Y0 = 3.57, 4.975  # A1; centred 14 x 6 field within 40.16 x 22.65 mm.
COLS = "ABCDEFGHIJKLMN"
NETS = [
    "", "CTRL_5V", "CTRL_GND", "ENA", "AUX0", "A_HOME", "TOOL_3V3",
    "TOOL_GND", "GP8", "GP10", "GP9", "LED1_A", "LED2_A", "LED3_A",
    "A_HOME_SW",
]
NET_ID = {net: index for index, net in enumerate(NETS)}
footprints: list[str] = []


def cell(col: str, row: int) -> tuple[float, float]:
    return X0 + COLS.index(col) * PITCH, Y0 + (row - 1) * PITCH


def effects(size: float = 0.8) -> str:
    return f"(effects (font (size {size} {size}) (thickness 0.13)))"


def pad(number: str, x: float, y: float, net: str, rect: bool = False) -> str:
    shape = "rect" if rect else "circle"
    return (f'(pad "{number}" thru_hole {shape} (at {x} {y}) (size 2 2) '
            f'(drill 1) (layers "*.Cu" "*.Mask") '
            f'(net {NET_ID[net]} "{net}"))')


def screw_terminal(ref: str, col: str, nets: list[str], title: str) -> None:
    x, y = cell(col, 1)
    parts = [
        f'(footprint "Perfboard_ScrewTerminal_1x06_2.54mm" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 0 -1.8) (layer "F.SilkS") {effects(0.75)})',
        f'  (property "Value" "{title}" (at 0 12.2) (layer "F.Fab") {effects(0.7)})',
        '  (attr through_hole)',
        '  (fp_rect (start -2.15 -1.35) (end 2.15 14.05) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_circle (center 0 -1.75) (end 0.48 -1.75) (stroke (width 0.25) (type default)) (fill solid) (layer "F.SilkS"))',
    ]
    for index, net in enumerate(nets, start=1):
        parts.append('  ' + pad(str(index), 0, (index - 1) * PITCH, net, index == 1))
    parts.append(')')
    footprints.append("\n".join(parts))


def opto(ref: str, row: int, nets: list[str]) -> None:
    # Every PC817 uses this unrotated top-notch orientation. In particular U3
    # is not mirrored or rotated: pin 1/2 are on F, pin 4/3 on I.
    x, y = cell("F", row)
    parts = [
        f'(footprint "Perfboard_PC817_DIP4" (layer "F.Cu") (at {x} {y} 0)',
        f'  (property "Reference" "{ref}" (at 3.81 1.1) (layer "F.SilkS") {effects(0.75)})',
        f'  (property "Value" "PC817C" (at 3.81 2.65) (layer "F.Fab") {effects(0.7)})',
        '  (attr through_hole)',
        '  (fp_rect (start -1.25 -1.25) (end 8.87 3.79) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_arc (start 2.65 -1.25) (mid 3.81 -0.1) (end 4.97 -1.25) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_circle (center 0 -1.75) (end 0.48 -1.75) (stroke (width 0.25) (type default)) (fill solid) (layer "F.SilkS"))',
        '  ' + pad("1", 0, 0, nets[0], True),
        '  ' + pad("2", 0, PITCH, nets[1]),
        '  ' + pad("3", 7.62, PITCH, nets[2]),
        '  ' + pad("4", 7.62, 0, nets[3]),
        ')',
    ]
    footprints.append("\n".join(parts))


def axial(ref: str, col: str, row: int, value: str, nets: list[str], *, diode: bool = False, dnp: bool = False) -> None:
    x, y = cell(col, row)
    body = "Diode_DO35" if diode else "Resistor_Axial"
    attr = "  (attr through_hole dnp)" if dnp else "  (attr through_hole)"
    parts = [
        f'(footprint "Perfboard_{body}_P7.62" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 3.81 0) (layer "F.SilkS") {effects(0.7)})',
        f'  (property "Value" "{value}" (at 3.81 1.65) (layer "F.Fab") {effects(0.65)})',
        attr,
        '  (fp_rect (start 1.15 -0.95) (end 6.47 0.95) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
    ]
    if diode:
        parts.append('  (fp_line (start 5.2 -0.95) (end 5.2 0.95) (stroke (width 0.38) (type default)) (fill none) (layer "F.SilkS"))')
    parts.extend([
        '  ' + pad("1", 0, 0, nets[0], True),
        '  ' + pad("2", 7.62, 0, nets[1]),
        ')',
    ])
    footprints.append("\n".join(parts))


def capacitor(ref: str, row: int, value: str, nets: list[str]) -> None:
    x, y = cell("J", row)
    parts = [
        f'(footprint "Perfboard_Radial_Capacitor_P2.54" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 1.27 0) (layer "F.SilkS") {effects(0.7)})',
        f'  (property "Value" "{value}" (at 1.27 1.85) (layer "F.Fab") {effects(0.65)})',
        '  (attr through_hole)',
        '  (fp_rect (start -0.9 -1.25) (end 3.44 1.25) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
        '  ' + pad("1", 0, 0, nets[0], True),
        '  ' + pad("2", PITCH, 0, nets[1]),
        ')',
    ]
    footprints.append("\n".join(parts))


def mounting(ref: str, x: float, y: float) -> None:
    footprints.append("\n".join([
        f'(footprint "Perfboard_MountingHole_2.7" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at -2 0 90) (layer "F.SilkS") {effects(0.65)})',
        '  (attr exclude_from_pos_files exclude_from_bom)',
        '  (fp_circle (center 0 0) (end 1.65 0) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask"))',
        ')',
    ]))


screw_terminal("J1", "A", ["CTRL_5V", "CTRL_GND", "ENA", "AUX0", "A_HOME", ""], "RP23CNC 1x06 screw")
screw_terminal("J2", "N", ["TOOL_3V3", "TOOL_GND", "GP8", "GP10", "GP9", ""], "PRO MICRO 1x06 screw")
opto("U1", 1, ["LED1_A", "ENA", "TOOL_GND", "GP8"])
opto("U2", 3, ["LED2_A", "AUX0", "TOOL_GND", "GP10"])
opto("U3", 5, ["LED3_A", "TOOL_GND", "CTRL_GND", "A_HOME_SW"])
axial("R1", "B", 1, "680R", ["CTRL_5V", "LED1_A"])
axial("D1", "B", 2, "1N4148", ["ENA", "LED1_A"], diode=True)
axial("R2", "B", 3, "680R", ["CTRL_5V", "LED2_A"])
axial("D2", "B", 4, "1N4148", ["AUX0", "LED2_A"], diode=True)
axial("R5", "B", 5, "390R", ["GP9", "LED3_A"])
axial("D3", "B", 6, "1N4148", ["TOOL_GND", "LED3_A"], diode=True)
axial("R3", "J", 1, "10k", ["GP8", "TOOL_3V3"])
axial("R4", "J", 3, "10k", ["GP10", "TOOL_3V3"])
axial("R6", "J", 5, "0R DNP", ["A_HOME_SW", "A_HOME"], dnp=True)
capacitor("C1", 2, "47nF", ["GP8", "TOOL_GND"])
capacitor("C2", 4, "47nF", ["GP10", "TOOL_GND"])
capacitor("C3", 6, "100nF", ["TOOL_3V3", "TOOL_GND"])
mounting("H1", 37.62, 1.80)
mounting("H2", 37.62, 20.85)


board = [
    '(kicad_pcb (version 20240108) (generator pcbnew)',
    '  (general (thickness 1.6))',
    '  (paper "A4")',
    '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen") (44 "Edge.Cuts" user))',
    '  (setup (pad_to_mask_clearance 0))',
]
board.extend(f'  (net {index} "{net}")' for index, net in enumerate(NETS))
board.extend('  ' + fp.replace('\n', '\n  ') for fp in footprints)
board.append('  (gr_rect (start 0 0) (end 40.16 22.65) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts"))')
board.append('  (gr_text "PC817C PERFBOARD — ALL THT" (at 20.08 1.25) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.14))))')
board.append('  (gr_text "1x06 SCREW TERMINALS • PIN 6 NC • R6 DNP" (at 20.08 21.45) (layer "F.SilkS") (effects (font (size 0.65 0.65) (thickness 0.11))))')
board.append(')')
OUT.write_text("\n".join(board) + "\n", encoding="utf-8")
print(f"Wrote {OUT}")
