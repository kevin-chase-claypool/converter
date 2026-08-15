"""Generate the compact, two-layer PC817 interface PCB from fixed design rules.

The layout uses through-hole PC817Cs and 2.54 mm headers. 0805 passives are
placed on the component side except for the three SOD-123 clamp diodes, which
are placed on the bottom to preserve clearance around the DIP packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot
from pathlib import Path


# Never overwrite the board that may be open in PCB Editor. Rev 0.2 is a
# separate, reviewable placement/net-assignment snapshot.
OUT = Path("hardware/pc817-interface/pc817-interface-v0.2.kicad_pcb")
STEP = 0.127  # 5 mil grid; every 2.54 mm connector coordinate lands on it.
WIDTH, HEIGHT = 40.16, 22.65
CLEARANCE = 0.30

NETS = [
    "", "CTRL_5V", "CTRL_GND", "ENA", "AUX0", "A_HOME", "TOOL_3V3",
    "TOOL_GND", "GP8", "GP10", "GP9", "LED1_A", "LED2_A", "LED3_A",
    "A_HOME_SW",
]
NET_ID = {name: index for index, name in enumerate(NETS)}


@dataclass(frozen=True)
class Pad:
    ref: str
    number: str
    x: float
    y: float
    net: str
    layers: tuple[str, ...]
    radius: float


pads: list[Pad] = []
footprints: list[str] = []


def effects(size: float = 0.85) -> str:
    return f"(effects (font (size {size} {size}) (thickness 0.13)))"


def add_pad(ref: str, number: str, x: float, y: float, net: str,
            layers: tuple[str, ...], radius: float) -> None:
    pads.append(Pad(ref, number, x, y, net, layers, radius))


def header(ref: str, x: float, y: float, net_names: list[str], label: str) -> None:
    body = [
        f'(footprint "RA_Header_1x05_2.54mm" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 0 -1.9 0) (layer "F.SilkS") {effects()})',
        f'  (property "Value" "{label}" (at 0 12.4 0) (layer "F.Fab") {effects()})',
        '  (attr through_hole)',
        '  (fp_rect (start -1.35 -1.35) (end 1.35 11.51) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_circle (center 0 -1.75) (end 0.45 -1.75) (stroke (width 0.22) (type default)) (fill solid) (layer "F.SilkS"))',
    ]
    for i, net in enumerate(net_names, start=1):
        py = (i - 1) * 2.54
        shape = "rect" if i == 1 else "circle"
        body.append(f'  (pad "{i}" thru_hole {shape} (at 0 {py}) (size 2 2) (drill 1) (layers "*.Cu" "*.Mask") (net {NET_ID[net]} "{net}"))')
        add_pad(ref, str(i), x, y + py, net, ("F", "B"), 1.0)
    body.append(')')
    footprints.append("\n".join(body))


def opto(ref: str, x: float, y: float, nets: list[str]) -> None:
    body = [
        f'(footprint "PC817_DIP4" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 3.81 -1.65 0) (layer "F.SilkS") {effects()})',
        f'  (property "Value" "PC817C" (at 3.81 4.12 0) (layer "F.Fab") {effects()})',
        '  (attr through_hole)',
        '  (fp_rect (start -1.25 -1.25) (end 8.87 3.79) (stroke (width 0.22) (type default)) (fill none) (layer "F.SilkS"))',
        '  (fp_circle (center 0 -1.72) (end 0.48 -1.72) (stroke (width 0.22) (type default)) (fill solid) (layer "F.SilkS"))',
    ]
    positions = [(0, 0), (0, 2.54), (7.62, 2.54), (7.62, 0)]
    for i, ((px, py), net) in enumerate(zip(positions, nets), start=1):
        shape = "rect" if i == 1 else "circle"
        body.append(f'  (pad "{i}" thru_hole {shape} (at {px} {py}) (size 1.85 1.85) (drill 0.9) (layers "*.Cu" "*.Mask") (net {NET_ID[net]} "{net}"))')
        add_pad(ref, str(i), x + px, y + py, net, ("F", "B"), 0.93)
    body.append(')')
    footprints.append("\n".join(body))


def smd(ref: str, value: str, x: float, y: float, nets: list[str], bottom: bool = False) -> None:
    layer = "B.Cu" if bottom else "F.Cu"
    silk = "B.SilkS" if bottom else "F.SilkS"
    side = "B" if bottom else "F"
    body = [
        f'(footprint "{value}_0805" (layer "{layer}") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at 0 -1.35 0) (layer "{silk}") {effects(0.7)})',
        f'  (property "Value" "{value}" (at 0 1.35 0) (layer "{side}.Fab") {effects(0.65)})',
        '  (attr smd)',
        f'  (fp_rect (start -1.2 -0.75) (end 1.2 0.75) (stroke (width 0.18) (type default)) (fill none) (layer "{silk}"))',
    ]
    for i, (px, net) in enumerate(((-0.95, nets[0]), (0.95, nets[1])), start=1):
        body.append(f'  (pad "{i}" smd roundrect (at {px} 0) (size 1.25 1.15) (layers "{layer}" "{side}.Paste" "{side}.Mask") (roundrect_rratio 0.2) (net {NET_ID[net]} "{net}"))')
        add_pad(ref, str(i), x + px, y, net, (side,), 0.67)
    body.append(')')
    footprints.append("\n".join(body))


def mounting(ref: str, x: float, y: float) -> None:
    footprints.append("\n".join([
        f'(footprint "MountingHole_2.5mm" (layer "F.Cu") (at {x} {y})',
        f'  (property "Reference" "{ref}" (at -2.1 0 90) (layer "F.SilkS") {effects(0.7)})',
        '  (attr exclude_from_pos_files exclude_from_bom)',
        '  (fp_circle (center 0 0) (end 1.65 0) (stroke (width 0.25) (type default)) (fill none) (layer "F.SilkS"))',
        '  (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask"))',
        ')',
    ]))


header("J1", 2.54, 5.08, ["CTRL_5V", "CTRL_GND", "ENA", "AUX0", "A_HOME"], "RP23CNC 2.54mm RA")
header("J2", 37.62, 5.08, ["TOOL_3V3", "TOOL_GND", "GP8", "GP10", "GP9"], "PRO MICRO 2.54mm RA")
opto("U1", 13.97, 3.81, ["LED1_A", "ENA", "TOOL_GND", "GP8"])
opto("U2", 13.97, 10.16, ["LED2_A", "AUX0", "TOOL_GND", "GP10"])
opto("U3", 13.97, 16.51, ["LED3_A", "TOOL_GND", "CTRL_GND", "A_HOME_SW"])

smd("R1", "680R", 8.55, 3.81, ["CTRL_5V", "LED1_A"], bottom=True)
smd("R2", "680R", 8.55, 10.16, ["CTRL_5V", "LED2_A"], bottom=True)
smd("R5", "390R", 8.55, 16.51, ["GP9", "LED3_A"], bottom=True)
smd("R3", "10k", 26.10, 3.81, ["GP8", "TOOL_3V3"])
smd("R4", "10k", 26.10, 10.16, ["GP10", "TOOL_3V3"])
smd("R6", "0R_DNP", 26.10, 16.51, ["A_HOME_SW", "A_HOME"])
smd("D1", "1N4148W", 11.10, 5.30, ["LED1_A", "ENA"], bottom=True)
smd("D2", "1N4148W", 11.10, 11.65, ["LED2_A", "AUX0"], bottom=True)
smd("D3", "1N4148W", 11.10, 18.00, ["LED3_A", "TOOL_GND"], bottom=True)
smd("C1", "47nF", 26.10, 5.65, ["GP8", "TOOL_GND"], bottom=True)
smd("C2", "47nF", 26.10, 12.00, ["GP10", "TOOL_GND"], bottom=True)
smd("C3", "100nF", 31.20, 16.51, ["TOOL_3V3", "TOOL_GND"], bottom=True)
mounting("H1", 37.62, 1.80)
mounting("H2", 37.62, 20.85)


def grid_point(x: float, y: float) -> tuple[int, int]:
    return round(x / STEP), round(y / STEP)


def mm(point: tuple[int, int]) -> tuple[float, float]:
    return point[0] * STEP, point[1] * STEP


max_x, max_y = grid_point(WIDTH, HEIGHT)
blocked: dict[str, set[tuple[int, int]]] = {"F": set(), "B": set()}


def mark_disc(layer: str, x: float, y: float, radius: float) -> None:
    cx, cy = grid_point(x, y)
    r = round(radius / STEP)
    for ix in range(cx - r, cx + r + 1):
        for iy in range(cy - r, cy + r + 1):
            if 0 <= ix <= max_x and 0 <= iy <= max_y and hypot(ix - cx, iy - cy) * STEP <= radius:
                blocked[layer].add((ix, iy))


# Board edge and all component copper are hard obstacles until their own net is routed.
for layer in blocked:
    for ix in range(max_x + 1):
        for iy in range(max_y + 1):
            x, y = mm((ix, iy))
            if x < 0.55 or x > WIDTH - 0.55 or y < 0.55 or y > HEIGHT - 0.55:
                blocked[layer].add((ix, iy))
for pad in pads:
    for layer in pad.layers:
        mark_disc(layer, pad.x, pad.y, pad.radius + CLEARANCE)
for x, y in [(37.62, 1.80), (37.62, 20.85)]:
    for layer in blocked:
        mark_disc(layer, x, y, 1.75)


def unmask_net(net: str) -> None:
    for pad in pads:
        if pad.net != net:
            continue
        for layer in pad.layers:
            cx, cy = grid_point(pad.x, pad.y)
            r = round((pad.radius + CLEARANCE) / STEP)
            for ix in range(cx - r, cx + r + 1):
                for iy in range(cy - r, cy + r + 1):
                    if hypot(ix - cx, iy - cy) * STEP <= pad.radius + CLEARANCE:
                        blocked[layer].discard((ix, iy))


def astar(start: tuple[int, int, int], goal: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    def h(node: tuple[int, int, int]) -> int:
        return abs(node[0] - goal[0]) + abs(node[1] - goal[1]) + (0 if node[2] == goal[2] else 12)

    q: list[tuple[int, int, tuple[int, int, int]]] = []
    heappush(q, (h(start), 0, start))
    previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start: None}
    cost = {start: 0}
    while q:
        _, current_cost, node = heappop(q)
        if node == goal:
            path = []
            while node is not None:
                path.append(node)
                node = previous[node]
            return list(reversed(path))
        x, y, layer_index = node
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (x + dx, y + dy, layer_index)
            layer = ("F", "B")[layer_index]
            if not (0 <= candidate[0] <= max_x and 0 <= candidate[1] <= max_y) or (candidate[0], candidate[1]) in blocked[layer]:
                continue
            new_cost = current_cost + 1
            if new_cost < cost.get(candidate, 10**9):
                cost[candidate] = new_cost
                previous[candidate] = node
                heappush(q, (new_cost + h(candidate), new_cost, candidate))
        other = 1 - layer_index
        candidate = (x, y, other)
        layer = ("F", "B")[other]
        if (x, y) not in blocked[layer]:
            new_cost = current_cost + 12
            if new_cost < cost.get(candidate, 10**9):
                cost[candidate] = new_cost
                previous[candidate] = node
                heappush(q, (new_cost + h(candidate), new_cost, candidate))
    raise RuntimeError(f"No route from {start} to {goal}")


segments: list[str] = []
vias: list[str] = []


def add_route(net: str, path: list[tuple[int, int, int]]) -> None:
    width = 0.35 if net in {"CTRL_5V", "CTRL_GND", "TOOL_3V3", "TOOL_GND"} else 0.25
    index = 0
    while index < len(path) - 1:
        start = path[index]
        following = path[index + 1]
        if following[2] != start[2]:
            vx, vy = mm((start[0], start[1]))
            vias.append(f'(via (at {vx:.3f} {vy:.3f}) (size 0.80) (drill 0.40) (layers "F.Cu" "B.Cu") (net {NET_ID[net]}))')
            index += 1
            continue
        dx, dy = following[0] - start[0], following[1] - start[1]
        end_index = index + 1
        while end_index < len(path) - 1:
            candidate = path[end_index + 1]
            current = path[end_index]
            if candidate[2] != start[2] or (candidate[0] - current[0], candidate[1] - current[1]) != (dx, dy):
                break
            end_index += 1
        end = path[end_index]
        sx, sy = mm((start[0], start[1]))
        ex, ey = mm((end[0], end[1]))
        layer = ("F.Cu", "B.Cu")[start[2]]
        segments.append(f'(segment (start {sx:.3f} {sy:.3f}) (end {ex:.3f} {ey:.3f}) (width {width}) (layer "{layer}") (net {NET_ID[net]}))')
        index = end_index
    for x, y, layer_index in path:
        mark_disc(("F", "B")[layer_index], *mm((x, y)), CLEARANCE + width / 2)


route_order = [
    "LED1_A", "LED2_A", "LED3_A", "A_HOME_SW", "CTRL_GND", "CTRL_5V",
    "TOOL_3V3", "ENA", "AUX0", "A_HOME", "GP8", "GP10", "GP9",
]
# Placement is intentionally released before routing.  The prior scripted
# autoroute crossed nets in this unusually small through-hole/SMD mixed layout;
# a later routing pass must be reviewed in the KiCad interactive router.


board = [
    '(kicad_pcb (version 20240108) (generator "pc817-pcb-generator")',
    '  (general (thickness 1.6))',
    '  (paper "A4")',
    '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "b.Silkscreen") (37 "F.SilkS" user "f.Silkscreen") (44 "Edge.Cuts" user))',
    '  (setup (pad_to_mask_clearance 0))',
]
board.extend(f'  (net {i} "{net}")' for i, net in enumerate(NETS))
board.extend('  ' + footprint.replace('\n', '\n  ') for footprint in footprints)
board.extend([
    '  (gr_rect (start 0 0) (end 40.16 22.65) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts"))',
    '  (gr_text "PC817C INTERFACE REV 0.2" (at 20.08 1.05) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.12))))',
    '  (gr_text "J1 RP23CNC" (at 1.1 17.78 90) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.11))))',
    '  (gr_text "J2 PRO MICRO 3V3" (at 35.75 17.78 90) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.11))))',
    '  (gr_text "R6 DNP — VERIFY E-18" (at 20.08 21.45) (layer "F.SilkS") (effects (font (size 0.75 0.75) (thickness 0.12))))',
])
board.extend('  ' + segment for segment in segments)
board.extend('  ' + via for via in vias)
board.append('  (zone (net 7) (net_name "TOOL_GND") (layer "B.Cu") (hatch edge 0.5) (connect_pads (clearance 0.3)) (min_thickness 0.25) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy 0.55 0.55) (xy 39.61 0.55) (xy 39.61 22.10) (xy 0.55 22.10))))')
board.append(')')
OUT.write_text("\n".join(board) + "\n", encoding="utf-8")
print(f"Wrote {OUT} with {len(segments)} segments and {len(vias)} vias.")
