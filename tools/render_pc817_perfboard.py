"""Render the all-through-hole 14 x 6 perfboard placement and wiring map."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "pc817-interface" / "pc817-perfboard-layout-v1.png"
W, H = 2200, 1500
BG, INK, BOARD = "#f7f8fa", "#18212b", "#146b4b"
GOLD, COPPER, BLUE, RED = "#d99117", "#bc6c25", "#2364aa", "#aa2f2f"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    face = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(Path("C:/Windows/Fonts") / face, size)


def text(draw, xy, value, size=24, color=INK, bold=False, anchor="la"):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor=anchor)


def line(draw, points, color=INK, width=4):
    draw.line(points, fill=color, width=width, joint="curve")


def main() -> None:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    text(draw, (W // 2, 55), "PC817C ISOLATED INTERFACE — ALL-THROUGH-HOLE PERFBOARD", 42, bold=True, anchor="ma")
    text(draw, (W // 2, 106), "40.16 × 22.65 mm / 14 × 6 pad field / component side shown", 25, "#50606f", anchor="ma")

    bx, by, pitch = 150, 260, 105
    cols = list("ABCDEFGHIJKLMN")
    rows = list(range(1, 7))
    bw, bh = 13 * pitch + 80, 5 * pitch + 80
    draw.rounded_rectangle((bx - 40, by - 40, bx + bw, by + bh), 24, fill=BOARD, outline="#0b4d35", width=7)

    def pt(col: str, row: int):
        return bx + cols.index(col) * pitch, by + (row - 1) * pitch

    for col in cols:
        x, _ = pt(col, 1)
        text(draw, (x, by - 85), col, 24, "white", True, "ma")
    for row in rows:
        _, y = pt("A", row)
        text(draw, (bx - 82, y), str(row), 24, "white", True, "ma")
    for col in cols:
        for row in rows:
            x, y = pt(col, row)
            draw.ellipse((x - 16, y - 16, x + 16, y + 16), fill="#d4d9dc", outline="#5e6b74", width=3)
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill="#20252a")

    # Existing unplated mounting holes on the right short side, outside the
    # 14 x 6 electrical pad field. They are mechanical only.
    for ref, y in [("H1", by - 5), ("H2", by + 5 * pitch + 5)]:
        x = bx + bw - 28
        draw.ellipse((x - 23, y - 23, x + 23, y + 23), fill=BG, outline="#d4d9dc", width=5)
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill="#20252a")
        text(draw, (x + 33, y), ref, 16, "white", True, "la")

    # Headers.
    for ref, col, title, color in [("J1", "A", "RP23CNC 1x06 SCREW", RED), ("J2", "N", "PRO MICRO 1x06 SCREW", BLUE)]:
        x, _ = pt(col, 1)
        draw.rounded_rectangle((x - 42, by - 38, x + 42, by + 5 * pitch + 38), 12, outline=color, width=6)
        text(draw, (x, by - 130), ref, 28, color, True, "ma")
        text(draw, (x, by + 5 * pitch + 75), title, 19, color, True, "ma")
        for row in range(1, 7):
            _, y = pt(col, row)
            text(draw, (x + (-55 if col == "A" else 55), y), str(row), 18, "white", True, "ma")

    # DIP packages, pin layout is explicitly printed.
    for ref, top_row in [("U1", 1), ("U2", 3), ("U3", 5)]:
        x1, y1 = pt("F", top_row)
        x2, y2 = pt("I", top_row + 1)
        draw.rounded_rectangle((x1 - 36, y1 - 38, x2 + 36, y2 + 38), 14, fill="#202934", outline="#070b0f", width=5)
        mid_x = (x1 + x2) // 2
        draw.arc((mid_x - 23, y1 - 25, mid_x + 23, y1 + 21), 180, 360, fill="white", width=4)
        text(draw, ((x1 + x2) // 2, (y1 + y2) // 2 - 15), ref, 26, "white", True, "ma")
        text(draw, ((x1 + x2) // 2, (y1 + y2) // 2 + 19), "PC817C", 19, "white", anchor="ma")
        for col, row, pin in [("F", top_row, "1"), ("F", top_row + 1, "2"), ("I", top_row, "4"), ("I", top_row + 1, "3")]:
            x, y = pt(col, row)
            text(draw, (x, y + 44), pin, 16, "white", True, "ma")

    def axial(ref, start, end, value, color=COPPER, stripe=False):
        x1, y1 = pt(*start)
        x2, y2 = pt(*end)
        line(draw, [(x1, y1), (x2, y2)], color, 7)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        draw.rounded_rectangle((mx - 43, my - 20, mx + 43, my + 20), 7, fill="#deb36b" if not stripe else "#e8c97d", outline=INK, width=2)
        if stripe:
            draw.rectangle((mx + 23, my - 20, mx + 31, my + 20), fill="#222")
        text(draw, (mx, my - 48), f"{ref} {value}", 17, "white", True, "ma")

    axial("R1", ("B", 1), ("E", 1), "680Ω")
    axial("D1", ("B", 2), ("E", 2), "1N4148", stripe=True)
    axial("R2", ("B", 3), ("E", 3), "680Ω")
    axial("D2", ("B", 4), ("E", 4), "1N4148", stripe=True)
    axial("R5", ("B", 5), ("E", 5), "390Ω")
    axial("D3", ("B", 6), ("E", 6), "1N4148", stripe=True)
    axial("R3", ("J", 1), ("M", 1), "10kΩ")
    axial("R4", ("J", 3), ("M", 3), "10kΩ")
    axial("R6", ("J", 5), ("M", 5), "0Ω DNP", "#8c8c8c")

    for ref, a, b, value in [("C1", ("J", 2), ("K", 2), "47nF"), ("C2", ("J", 4), ("K", 4), "47nF"), ("C3", ("J", 6), ("K", 6), "100nF")]:
        x1, y1 = pt(*a); x2, y2 = pt(*b)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        draw.rectangle((mx - 22, my - 29, mx + 22, my + 29), fill="#d5e3d3", outline=INK, width=2)
        line(draw, [(x1, y1), (mx - 22, my)], "#d5e3d3", 5); line(draw, [(mx + 22, my), (x2, y2)], "#d5e3d3", 5)
        text(draw, (mx, my - 55), f"{ref} {value}", 17, "white", True, "ma")

    # Dimensioning.
    line(draw, [(bx, by - 50), (bx + 13 * pitch, by - 50)], INK, 3)
    text(draw, (bx + (13 * pitch) // 2, by - 86), "40.16 mm / 1.581 in", 24, INK, True, "ma")
    line(draw, [(bx - 160, by), (bx - 160, by + 5 * pitch)], INK, 3)
    text(draw, (bx - 205, by + (5 * pitch) // 2), "22.65 mm / 0.892 in", 22, INK, True, "mm")

    # Right panel: clear solder-side rules, no schematic ambiguity.
    px, py = 1810, 250
    draw.rounded_rectangle((px, py, 2160, 1335), 18, fill="white", outline="#b9c5d0", width=3)
    text(draw, (px + 25, py + 38), "UNDERSIDE WIRING", 30, INK, True)
    text(draw, (px + 25, py + 76), "Use insulated 30 AWG wire.", 20, "#50606f")
    text(draw, (px + 25, py + 105), "Each line is one net.", 20, "#50606f")
    wiring = [
        ("CTRL_5V", "A1 B1 B3"), ("CTRL_GND", "A2 I6"),
        ("ENA", "A3 F2 B2"), ("AUX0", "A4 F4 B4"),
        ("A_HOME", "A5 M5 (R6 OPEN)"), ("LED1_A", "E1 E2 F1"),
        ("GP8", "N3 I1 J1 J2"), ("TOOL_3V3", "N1 M1 M3 J6"),
        ("TOOL_GND", "N2 I2 I4 F6 K2 K4 K6 B6"),
        ("LED2_A", "E3 E4 F3"), ("GP10", "N4 I3 J3 J4"),
        ("LED3_A", "E5 E6 F5"), ("GP9", "N5 B5"),
        ("A_HOME_SW", "I5 J5"),
    ]
    for i, (net, pads) in enumerate(wiring):
        y = py + 155 + i * 58
        text(draw, (px + 25, y), net, 18, RED if "GND" not in net else BLUE, True)
        text(draw, (px + 25, y + 23), pads, 17, INK)
    text(draw, (px + 25, py + 1010), "Stripe toward E2/E4/E6.", 19, INK, True)
    text(draw, (px + 25, py + 1043), "R6: leave EMPTY.", 19, "#a93426", True)

    text(draw, (150, 1270), "Important: controller ground (CTRL_GND) and toolhead ground (TOOL_GND) must stay isolated.\n"
                              "Terminal 6 on each screw block is NC/spare. U1/U2 pull GP8/GP10 LOW when active.", 25, INK, bold=True)
    image.save(OUT, dpi=(300, 300))
    print(OUT)


if __name__ == "__main__":
    main()
