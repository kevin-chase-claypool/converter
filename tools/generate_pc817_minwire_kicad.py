"""Generate the compact, routed PC817 perfboard/PCB reference layout.

The physical envelope and 2.54 mm grid match the existing 14 x 6 perfboard.
All parts are through-hole.  U3 is rotated 180 degrees so the isolation barrier
remains vertical and its reverse-direction signal does not cross the board.
"""

from pathlib import Path
from shutil import copyfile


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware" / "pc817-interface"
OUT = HARDWARE / "pc817-perfboard-v2-minwire.kicad_pcb"
SCH_TEMPLATE = HARDWARE / "pc817-perfboard-v1.2.kicad_sch"
SCH_OUT = HARDWARE / "pc817-perfboard-v2-minwire.kicad_sch"
PRO_TEMPLATE = HARDWARE / "pc817-perfboard-v1.2.kicad_sch.kicad_pro"
PRO_OUT = HARDWARE / "pc817-perfboard-v2-minwire.kicad_pro"

PITCH = 2.54
X0, Y0 = 3.57, 4.975
COLS = "ABCDEFGHIJKLMN"
NETS = [
    "", "CTRL_5V", "CTRL_GND", "ENA", "AUX0", "A_HOME",
    "TOOL_3V3", "TOOL_GND", "GP29", "GP28", "GP27",
    "LED1_A", "LED2_A", "LED3_A", "A_HOME_SW",
]
NET_ID = {name: index for index, name in enumerate(NETS)}
footprints: list[str] = []
segments: list[str] = []


def cell(col: str, row: int) -> tuple[float, float]:
    return X0 + COLS.index(col) * PITCH, Y0 + (row - 1) * PITCH


def effects(size: float = 0.8) -> str:
    return f"(effects (font (size {size} {size}) (thickness 0.13)))"


def pad(number: str, x: float, y: float, net: str, rect: bool = False) -> str:
    shape = "rect" if rect else "circle"
    net_expr = f'(net {NET_ID[net]} "{net}")' if net else ''
    return (
        f'(pad "{number}" thru_hole {shape} (at {x} {y}) (size 2 2) '
        f'(drill 1) (layers "*.Cu" "*.Mask") {net_expr})'
    )


def screw_terminal(ref: str, col: str, nets: list[str], title: str) -> None:
    x, y = cell(col, 1)
    parts = [
        f'(footprint "Perfboard_ScrewTerminal_1x06_2.54mm" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 0 -1.8) (layer "F.SilkS") {effects(0.75)})',
        f'  (property "Value" "{title}" (at 0 12.2) (layer "F.Fab") {effects(0.65)})',
        '  (attr through_hole)',
        '  (fp_rect (start -2.15 -1.35) (end 2.15 14.05) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_circle (center 0 -1.75) (end 0.48 -1.75) (stroke (width 0.25) (type default)) (fill solid) (layer "F.SilkS"))',
    ]
    for index, net in enumerate(nets, start=1):
        parts.append('  ' + pad(str(index), 0, (index - 1) * PITCH, net, index == 1))
    parts.append(')')
    footprints.append("\n".join(parts))


def opto(ref: str, col: str, row: int, nets: list[str], rotation: int = 0) -> None:
    x, y = cell(col, row)
    parts = [
        f'(footprint "Perfboard_PC817_DIP4" (layer "F.Cu") (at {x} {y} {rotation})',
        f'  (property "Reference" "{ref}" (at 3.81 1.1 {rotation}) (layer "F.SilkS") {effects(0.75)})',
        f'  (property "Value" "PC817C" (at 3.81 2.65 {rotation}) (layer "F.Fab") {effects(0.65)})',
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


def axial(
    ref: str,
    col: str,
    row: int,
    value: str,
    nets: list[str],
    *,
    diode: bool = False,
    span: float = 7.62,
    reverse_pads: bool = False,
) -> None:
    x, y = cell(col, row)
    kind = "Diode_DO35" if diode else "Resistor_Axial"
    parts = [
        f'(footprint "Perfboard_{kind}_P{span:.2f}" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at {span / 2} 0) (layer "F.SilkS") {effects(0.8)})',
        f'  (property "Value" "{value}" (at {span / 2} 1.65) (layer "F.Fab") {effects(0.62)})',
        '  (attr through_hole)',
        f'  (fp_rect (start 1.05 -0.90) (end {span - 1.05} 0.90) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
    ]
    if diode:
        # Pad 1 and the heavy line are the cathode/banded end.
        parts.append(f'  (fp_line (start {span - 2.42} -0.90) (end {span - 2.42} 0.90) (stroke (width 0.38) (type default)) (layer "F.SilkS"))')
        parts.append('  ' + pad("2", 0, 0, nets[0], True))
        parts.append('  ' + pad("1", span, 0, nets[1]))
    else:
        if reverse_pads:
            parts.append('  ' + pad("2", 0, 0, nets[0], True))
            parts.append('  ' + pad("1", span, 0, nets[1]))
        else:
            parts.append('  ' + pad("1", 0, 0, nets[0], True))
            parts.append('  ' + pad("2", span, 0, nets[1]))
    parts.append(')')
    footprints.append("\n".join(parts))


def capacitor(ref: str, col: str, row: int, value: str, nets: list[str], *, vertical: bool = False) -> None:
    x, y = cell(col, row)
    parts = [
        f'(footprint "Perfboard_Radial_Capacitor_P2.54" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 1.27 0) (layer "F.SilkS") {effects(0.7)})',
        f'  (property "Value" "{value}" (at 1.27 1.85) (layer "F.Fab") {effects(0.62)})',
        '  (attr through_hole)',
        ('  (fp_rect (start -1.25 -0.9) (end 1.25 3.44) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))'
         if vertical else
         '  (fp_rect (start -0.9 -1.25) (end 3.44 1.25) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))'),
        '  ' + pad("1", 0, 0, nets[0], True),
        '  ' + pad("2", 0 if vertical else PITCH, PITCH if vertical else 0, nets[1]),
        ')',
    ]
    footprints.append("\n".join(parts))


def vertical_diode(ref: str, col: str, row: int, nets: list[str]) -> None:
    """Standing DO-35 diode; pad 1/banded cathode is the upper grid pad."""
    x, y = cell(col, row)
    footprints.append("\n".join([
        f'(footprint "Perfboard_Diode_DO35_Vertical_P2.54" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 0 1.27 90) (layer "F.SilkS") {effects(0.8)})',
        f'  (property "Value" "1N4148" (at 1.8 1.27 90) (layer "F.Fab") {effects(0.62)})',
        '  (attr through_hole)',
        '  (fp_rect (start -0.9 -0.9) (end 0.9 3.44) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_line (start -0.9 0.55) (end 0.9 0.55) (stroke (width 0.38) (type default)) (layer "F.SilkS"))',
        '  ' + pad("1", 0, 0, nets[0], True),
        '  ' + pad("2", 0, PITCH, nets[1]),
        ')',
    ]))


def mounting(ref: str, x: float, y: float) -> None:
    footprints.append("\n".join([
        f'(footprint "Perfboard_MountingHole_2.7" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at -2 0 90) (layer "F.SilkS") {effects(0.65)})',
        '  (attr exclude_from_pos_files exclude_from_bom)',
        '  (fp_circle (center 0 0) (end 1.65 0) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask"))',
        ')',
    ]))


def trace(net: str, start: tuple[float, float], end: tuple[float, float], layer: str = "B.Cu", width: float = 0.25) -> None:
    sx, sy = start
    ex, ey = end
    segments.append(
        f'(segment (start {sx:.3f} {sy:.3f}) (end {ex:.3f} {ey:.3f}) '
        f'(width {width}) (layer "{layer}") (net {NET_ID[net]}))'
    )


# Terminal orders are selected to align each external wire with its channel.
screw_terminal("J1", "A", ["CTRL_5V", "ENA", "", "AUX0", "CTRL_GND", "A_HOME"], "RP23CNC")
screw_terminal("J2", "N", ["GP29", "TOOL_3V3", "GP28", "TOOL_GND", "", "GP27"], "PRO MICRO")

opto("U1", "F", 1, ["LED1_A", "ENA", "TOOL_GND", "GP29"])
opto("U2", "F", 3, ["LED2_A", "AUX0", "TOOL_GND", "GP28"])
# Rotated: pin 1=I6, pin 2=I5, pin 3=F5, pin 4=F6.
opto("U3", "I", 6, ["LED3_A", "TOOL_GND", "CTRL_GND", "A_HOME_SW"], 180)

axial("R1", "B", 1, "680R", ["CTRL_5V", "LED1_A"], span=5.08, reverse_pads=True)
vertical_diode("D1", "E", 1, ["LED1_A", "ENA"])
axial("R2", "B", 3, "680R", ["CTRL_5V", "LED2_A"], span=5.08, reverse_pads=True)
vertical_diode("D2", "E", 3, ["LED2_A", "AUX0"])
axial("R6", "B", 6, "0R LINK", ["A_HOME", "A_HOME_SW"])

axial("R3", "K", 1, "10k", ["GP29", "TOOL_3V3"], span=5.08, reverse_pads=True)
capacitor("C1", "J", 1, "47nF", ["GP29", "TOOL_GND"], vertical=True)
axial("R4", "K", 3, "10k", ["GP28", "TOOL_3V3"], span=5.08, reverse_pads=True)
capacitor("C2", "J", 3, "47nF", ["GP28", "TOOL_GND"], vertical=True)
axial("R5", "J", 5, "390R", ["LED3_A", "GP27"])
axial("D3", "J", 6, "1N4148", ["TOOL_GND", "LED3_A"], diode=True)

mounting("H1", 37.62, 1.80)
mounting("H2", 37.62, 20.85)

# Controller-side paths.  Each signal is confined to its own row pair.
trace("CTRL_5V", cell("A", 1), cell("B", 1), "F.Cu")
trace("CTRL_5V", cell("B", 1), cell("B", 3), "F.Cu")
trace("LED1_A", cell("D", 1), cell("F", 1))
trace("ENA", cell("A", 2), cell("E", 2))
trace("ENA", cell("E", 2), cell("F", 2))
trace("LED2_A", cell("D", 3), cell("F", 3))
trace("AUX0", cell("A", 4), cell("E", 4))
trace("AUX0", cell("E", 4), cell("F", 4))
trace("CTRL_GND", cell("A", 5), cell("F", 5))
trace("A_HOME", cell("A", 6), cell("B", 6))
trace("A_HOME_SW", cell("E", 6), cell("F", 6))

# Tool-side channel 1.  The pull-up rail uses F.Cu; the signal uses B.Cu.
trace("GP29", cell("I", 1), cell("K", 1))
trace("GP29", cell("J", 1), cell("K", 1))
trace("GP29", cell("K", 1), (28.97, 3.25))
trace("GP29", (28.97, 3.25), (35.80, 3.25))
trace("GP29", (35.80, 3.25), cell("N", 1))
trace("TOOL_3V3", cell("M", 1), (33.00, 6.50), "F.Cu")
trace("TOOL_3V3", (33.00, 6.50), cell("N", 2), "F.Cu")

# Tool-side channel 2.  Detour above R4 keeps the signal clear of its pull-up pad.
trace("GP28", cell("I", 3), cell("K", 3))
trace("GP28", cell("J", 3), cell("K", 3))
trace("GP28", cell("K", 3), (29.10, 8.55))
trace("GP28", (29.10, 8.55), (35.20, 8.55))
trace("GP28", (35.20, 8.55), cell("N", 3))
trace("TOOL_3V3", cell("M", 1), cell("M", 3), "F.Cu")

# Tool ground is a short local tree.  It never touches controller ground.
trace("TOOL_GND", cell("I", 2), cell("J", 2), "F.Cu")
trace("TOOL_GND", cell("I", 2), (22.20, 7.515), "F.Cu")
trace("TOOL_GND", (22.20, 7.515), (22.20, 13.90), "F.Cu")
trace("TOOL_GND", (22.20, 13.90), cell("J", 4), "F.Cu")
trace("TOOL_GND", cell("I", 4), cell("J", 4), "F.Cu")
trace("TOOL_GND", cell("J", 4), cell("N", 4), "F.Cu")
trace("TOOL_GND", cell("I", 5), (22.20, 15.135), "F.Cu")
trace("TOOL_GND", (22.20, 15.135), (22.20, 13.90), "F.Cu")
trace("TOOL_GND", cell("I", 5), cell("J", 6), "F.Cu")

# Reverse-direction home channel.  Rotating U3 makes every connection local.
trace("LED3_A", cell("I", 6), (23.89, 19.30))
trace("LED3_A", (23.89, 19.30), (34.05, 19.30))
trace("LED3_A", (34.05, 19.30), cell("M", 6))
trace("LED3_A", cell("I", 6), cell("J", 5))
trace("GP27", cell("M", 5), cell("N", 6))

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
board.append('  (gr_text "PC817C MIN-WIRE V2" (at 20.08 1.25) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.14))))')
board.append('  (gr_text "U3 ROTATED 180° • J2.3 = GP28" (at 20.08 21.45) (layer "F.SilkS") (effects (font (size 0.63 0.63) (thickness 0.11))))')
board.extend('  ' + segment for segment in segments)
board.append(')')
OUT.write_text("\n".join(board) + "\n", encoding="utf-8")

# Preserve the self-contained modern schematic while correcting the exposed
# RP2350 pin names and the now-bench-verified A_HOME link status.
schematic = SCH_TEMPLATE.read_text(encoding="utf-8")
schematic = schematic.replace("pc817-perfboard-v1.2", "pc817-perfboard-v2-minwire")
schematic = schematic.replace("GP10", "GPIO20")
schematic = schematic.replace("0R DNP", "0R LINK")
schematic = schematic.replace(
    "R6 MUST REMAIN DNP until E-18 verifies the RP23CNC A-home input.",
    "Fit R6 only for the specific U3 sample that passes the 12 V / 2.2 k bench test.",
)
schematic = schematic.replace('(date "2026-08-06")', '(date "2026-08-10")')
schematic = schematic.replace('(rev "0.1")', '(rev "2.0-minwire")')
schematic = schematic.replace("perfboard build", "minimum-wire perfboard build")


def form_bounds(text: str, start: int) -> tuple[int, int]:
    """Return bounds for the s-expression beginning at start."""
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise ValueError("unterminated s-expression")


def replace_embedded_connector(text: str) -> str:
    library = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector_Generic.kicad_sym")
    lib_text = library.read_text(encoding="utf-8")
    lib_start = lib_text.index('(symbol "Conn_01x06"')
    _, lib_end = form_bounds(lib_text, lib_start)
    connector = lib_text[lib_start:lib_end].replace(
        '(symbol "Conn_01x06"', '(symbol "Connector_Generic:Conn_01x06"', 1
    )
    old_start = text.index('(symbol "Connector_Generic:Conn_01x05"')
    _, old_end = form_bounds(text, old_start)
    return text[:old_start] + connector + text[old_end:]


def update_connector_instance(text: str, ref: str, pin6_uuid: str) -> str:
    marker = f'(property "Reference" "{ref}"'
    prop = text.index(marker)
    start = text.rfind("\n\t(symbol\n", 0, prop) + 2
    _, end = form_bounds(text, start)
    block = text[start:end]
    block = block.replace('Connector_Generic:Conn_01x05', 'Connector_Generic:Conn_01x06')
    insert = (
        f'\t\t(pin "6"\n'
        f'\t\t\t(uuid "{pin6_uuid}")\n'
        f'\t\t)\n'
    )
    block = block.replace('\t\t(instances\n', insert + '\t\t(instances\n', 1)
    return text[:start] + block + text[end:]


schematic = replace_embedded_connector(schematic)
schematic = update_connector_instance(
    schematic, "J1", "df36abef-1f69-4ace-9f4f-06af4c26c1b6"
)
schematic = update_connector_instance(
    schematic, "J2", "78051c6d-c231-48b5-8dc2-3e76e8bd0500"
)

# Re-map connector labels to the physical six-position terminal order.
label_changes = [
    ('CTRL_GND', 'ENA', '58.42', '73.66', '0'),
    ('ENA', 'NC_J1_3', '58.42', '76.2', '0'),
    ('A_HOME', 'CTRL_GND', '58.42', '81.28', '0'),
    ('TOOL_3V3', 'GP8', '217.17', '71.12', '180'),
    ('TOOL_GND', 'TOOL_3V3', '217.17', '73.66', '180'),
    ('GP8', 'GPIO20', '217.17', '76.2', '180'),
    ('GPIO20', 'TOOL_GND', '217.17', '78.74', '180'),
    ('GP9', 'NC_J2_5', '217.17', '81.28', '180'),
]
for old, new, x, y, angle in label_changes:
    schematic = schematic.replace(
        f'(label "{old}"\n\t\t(at {x} {y} {angle})',
        f'(label "{new}"\n\t\t(at {x} {y} {angle})',
        1,
    )


def remove_form_containing(text: str, kind: str, marker: str) -> str:
    marker_at = text.find(marker)
    if marker_at < 0:
        return text
    if text.startswith(f"({kind}", marker_at):
        start = marker_at
    else:
        start = text.rfind(f"\n\t({kind}", 0, marker_at) + 2
    _, end = form_bounds(text, start)
    return text[:start] + text[end:]


# NC terminals are true no-connects, not a shared or named electrical net.
schematic = remove_form_containing(
    schematic, "wire", "(xy 45.72 76.2) (xy 58.42 76.2)"
)
schematic = remove_form_containing(schematic, "label", '(label "NC_J1_3"')
schematic = remove_form_containing(
    schematic, "wire", "(xy 229.87 81.28) (xy 217.17 81.28)"
)
schematic = remove_form_containing(schematic, "label", '(label "NC_J2_5"')


def remove_symbol_by_reference(text: str, ref: str) -> str:
    marker_at = text.index(f'(property "Reference" "{ref}"')
    start = text.rfind("\n\t(symbol\n", 0, marker_at) + 2
    _, end = form_bounds(text, start)
    return text[:start] + text[end:]


# C3 is optional rail bypassing, not part of the minimum-wire build. The Pro
# Micro already decouples its local 3.3 V rail; C1/C2 remain as input filters.
schematic = remove_symbol_by_reference(schematic, "C3")
schematic = remove_form_containing(
    schematic, "wire", "(xy 203.2 105.41) (xy 203.2 107.95)"
)
schematic = remove_form_containing(
    schematic, "wire", "(xy 203.2 97.79) (xy 203.2 95.25)"
)
schematic = remove_form_containing(schematic, "label", "(at 203.2 107.95 0)")
schematic = remove_form_containing(schematic, "label", "(at 203.2 95.25 0)")
schematic = remove_form_containing(
    schematic, "text", 'C3: place near J2 / Pro Micro 3.3 V and ground.'
)

connector_pin6 = '''
	(no_connect (at 45.72 76.2) (uuid "fdfe4181-43e4-42d9-970e-cfc56764899d"))
	(no_connect (at 229.87 81.28) (uuid "dc09f496-e6e1-4bc1-9f91-d82897da669e"))
\t(wire
\t\t(pts
\t\t\t(xy 45.72 83.82) (xy 58.42 83.82)
\t\t)
\t\t(stroke (width 0) (type default))
\t\t(uuid "06a0f64b-e402-4dc6-bb32-3fdc50b81d0c")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 229.87 83.82) (xy 217.17 83.82)
\t\t)
\t\t(stroke (width 0) (type default))
\t\t(uuid "fa48efea-cfbe-4782-b47a-3620949057d3")
\t)
\t(label "A_HOME"
\t\t(at 58.42 83.82 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "c9869352-2ec7-412a-ab75-20ab78502a82")
\t)
\t(label "GP9"
\t\t(at 217.17 83.82 180)
\t\t(effects (font (size 1.27 1.27)) (justify right bottom))
\t\t(uuid "a31ba4ce-470f-4163-af87-fc939c799f8c")
\t)
'''
first_instance = schematic.index('\n\t(symbol\n\t\t(lib_id "Connector_Generic:Conn_01x06")')
schematic = schematic[:first_instance] + connector_pin6 + schematic[first_instance:]
# The legacy template used GP8/GP10/GP9. The direct right-side harness uses
# consecutive exposed A3/A2/A1 GPIOs instead: GP29/GP28/GP27.
schematic = schematic.replace("GP8", "GP29")
schematic = schematic.replace("GPIO20", "GP28")
schematic = schematic.replace("GP9", "GP27")
SCH_OUT.write_text(schematic, encoding="utf-8")

if PRO_TEMPLATE.exists():
    copyfile(PRO_TEMPLATE, PRO_OUT)

print(f"Wrote {OUT}")
print(f"Wrote {SCH_OUT}")
print(f"Wrote {PRO_OUT}")
print(f"Placed {len(footprints)} footprints and {len(segments)} routed segments")
