"""Render the proposed 40.16 x 22.65 mm PC817C interface module diagram."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parents[1] / "pc817-three-channel-module-proposal.png"
W, H = 2400, 1500
BG = "#f8fafc"
INK = "#18212b"
MUTED = "#50606f"
GREEN = "#146b4b"
GREEN_DARK = "#0b4d35"
GOLD = "#d58b14"
PALE = "#e9f4ed"
WARN = "#a93426"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(Path("C:/Windows/Fonts") / name, size)


def txt(d: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int = 26,
        color: str = INK, bold: bool = False, anchor: str = "la") -> None:
    d.text(xy, value, font=font(size, bold), fill=color, anchor=anchor)


def wire(d: ImageDraw.ImageDraw, points: list[tuple[int, int]], width: int = 4,
         color: str = INK) -> None:
    d.line(points, fill=color, width=width, joint="curve")


def resistor(d: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    wire(d, [(x, y), (x + 15, y)], 4)
    points = [(x + 15, y), (x + 27, y - 13), (x + 39, y + 13), (x + 51, y - 13),
              (x + 63, y + 13), (x + 75, y - 13), (x + 87, y + 13), (x + 99, y)]
    wire(d, points, 4)
    wire(d, [(x + 99, y), (x + 120, y)], 4)
    txt(d, (x + 10, y - 41), label, 21, GREEN_DARK, True)


def diode(d: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    d.polygon([(x, y - 11), (x, y + 11), (x + 20, y)], outline=INK, fill=BG)
    wire(d, [(x + 26, y - 14), (x + 26, y + 14)], 3)
    wire(d, [(x - 18, y), (x, y)], 3)
    wire(d, [(x + 26, y), (x + 44, y)], 3)
    txt(d, (x - 10, y + 20), label, 17, MUTED)


def opto(d: ImageDraw.ImageDraw, x: int, y: int, ref: str) -> None:
    d.rounded_rectangle((x, y, x + 150, y + 92), radius=10, fill="white", outline=INK, width=3)
    d.ellipse((x + 25, y + 29, x + 47, y + 51), outline=INK, width=3)
    d.polygon([(x + 53, y + 29), (x + 53, y + 51), (x + 72, y + 40)], outline=INK, fill="white")
    wire(d, [(x + 84, y + 22), (x + 84, y + 70)], 3)
    wire(d, [(x + 106, y + 58), (x + 129, y + 36)], 3)
    wire(d, [(x + 106, y + 58), (x + 137, y + 70)], 3)
    txt(d, (x + 75, y + 108), f"{ref} PC817C", 19, GREEN_DARK, True, "ma")


def ground(d: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    wire(d, [(x, y), (x, y + 12)], 3)
    wire(d, [(x - 16, y + 12), (x + 16, y + 12)], 3)
    wire(d, [(x - 11, y + 19), (x + 11, y + 19)], 3)
    wire(d, [(x - 5, y + 26), (x + 5, y + 26)], 3)
    txt(d, (x + 24, y + 7), label, 17, MUTED)


def capacitor(d: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    wire(d, [(x, y), (x, y + 16)], 3)
    wire(d, [(x - 16, y + 16), (x + 16, y + 16)], 3)
    wire(d, [(x - 16, y + 27), (x + 16, y + 27)], 3)
    wire(d, [(x, y + 27), (x, y + 43)], 3)
    txt(d, (x + 23, y + 8), label, 17, GREEN_DARK)


def connector(d: ImageDraw.ImageDraw, x: int, y: int, side: str, title: str, pins: list[str]) -> None:
    d.rounded_rectangle((x, y, x + 84, y + 230), radius=10, fill="#f1f0eb", outline=INK, width=3)
    txt(d, (x + 42, y - 28), title, 22, INK, True, "ma")
    for i, pin in enumerate(pins):
        py = y + 28 + i * 42
        d.ellipse((x + 29, py - 6, x + 41, py + 6), fill=GOLD, outline=INK)
        if side == "left":
            txt(d, (x - 12, py), f"{i + 1}  {pin}", 16, INK, anchor="ra")
        else:
            txt(d, (x + 98, py), f"{i + 1}  {pin}", 16, INK)
    # Side-entry housing and wire direction: this is intentionally visible so
    # the placement drawing cannot be confused with a vertical/top-entry header.
    if side == "left":
        d.rounded_rectangle((x - 42, y + 62, x + 13, y + 168), radius=7, fill="#e2dfd4", outline=INK, width=3)
        for py in range(y + 78, y + 153, 18):
            wire(d, [(x - 74, py), (x - 42, py)], 3, "#d7b65a")
        d.polygon([(x - 96, y + 115), (x - 74, y + 104), (x - 74, y + 126)], fill="white")
        wire(d, [(x - 74, y + 115), (x - 99, y + 115)], 3, "white")
    else:
        d.rounded_rectangle((x + 71, y + 62, x + 126, y + 168), radius=7, fill="#e2dfd4", outline=INK, width=3)
        for py in range(y + 78, y + 153, 18):
            wire(d, [(x + 126, py), (x + 158, py)], 3, "#d7b65a")
        d.polygon([(x + 180, y + 115), (x + 158, y + 104), (x + 158, y + 126)], fill="white")
        wire(d, [(x + 158, y + 115), (x + 183, y + 115)], 3, "white")


def draw_schematic(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle((55, 158, 1210, 1415), radius=18, fill="white", outline="#b9c5d0", width=3)
    txt(d, (86, 200), "Circuit schematic — all three isolation channels", 34, INK, True)
    txt(d, (86, 239), "All values are proposed. The A_HOME output remains unpopulated until E-18 passes.", 20, WARN)
    txt(d, (96, 302), "Controller domain", 23, GREEN_DARK, True)
    txt(d, (926, 302), "Pro Micro domain", 23, GREEN_DARK, True)
    wire(d, [(87, 320), (1170, 320)], 2, "#c3ced8")

    # Channel 1.  The controller output is a low-side sink: +5 V through the
    # LED path is enabled when ENA is low, so module logic preserves M3/M5 sense.
    y = 438
    txt(d, (92, y), "J1-1  +5V", 23, INK, True, "lm")
    resistor(d, 245, y, "R1 680 Ω")
    opto(d, 455, y - 47, "U1")
    wire(d, [(365, y), (455, y)])
    wire(d, [(605, y), (705, y), (705, y - 77)])
    txt(d, (714, y - 87), "+3V3", 18, GREEN_DARK, True)
    resistor(d, 765, y - 77, "R3 10 kΩ")
    wire(d, [(705, y), (1020, y)])
    capacitor(d, 905, y, "C1 47 nF")
    ground(d, 905, y + 43, "Pro GND")
    txt(d, (1032, y), "J2-3  GP8", 23, INK, True, "lm")
    wire(d, [(530, y + 46), (530, y + 76), (230, y + 76)])
    txt(d, (92, y + 76), "J1-3  ENA (sink)", 20, INK, True, "lm")
    txt(d, (260, y + 104), "D1 1N4148W anti-parallel to U1 LED; ~5.6 mA at 5V", 17, MUTED)
    txt(d, (92, y + 132), "M3 high → GP8 high; M5 low → GP8 low", 19, MUTED)

    # Channel 2.
    y = 705
    txt(d, (92, y), "J1-1  +5V", 23, INK, True, "lm")
    resistor(d, 245, y, "R2 680 Ω")
    opto(d, 455, y - 47, "U2")
    wire(d, [(365, y), (455, y)])
    wire(d, [(605, y), (705, y), (705, y - 77)])
    txt(d, (714, y - 87), "+3V3", 18, GREEN_DARK, True)
    resistor(d, 765, y - 77, "R4 10 kΩ")
    wire(d, [(705, y), (1020, y)])
    capacitor(d, 905, y, "C2 47 nF")
    ground(d, 905, y + 43, "Pro GND")
    txt(d, (1032, y), "J2-4  GP10", 23, INK, True, "lm")
    wire(d, [(530, y + 46), (530, y + 76), (230, y + 76)])
    txt(d, (92, y + 76), "J1-4  AUX0 (sink)", 20, INK, True, "lm")
    txt(d, (260, y + 104), "D2 1N4148W anti-parallel to U2 LED; ~5.6 mA at 5V", 17, MUTED)
    txt(d, (92, y + 132), "AUX0 high → GP10 high; AUX0 low → GP10 low", 19, MUTED)

    # Channel 3 reverse direction.
    y = 1003
    txt(d, (92, y), "J2-5  GP9", 23, INK, True, "lm")
    resistor(d, 245, y, "R5 390 Ω")
    opto(d, 455, y - 47, "U3")
    wire(d, [(365, y), (455, y)])
    wire(d, [(605, y), (826, y)])
    d.rounded_rectangle((826, y - 20, 901, y + 20), radius=4, fill="#fff6df", outline=GOLD, width=3)
    txt(d, (864, y), "R6", 18, INK, True, "mm")
    txt(d, (864, y + 34), "0 Ω DNP", 15, WARN, anchor="ma")
    wire(d, [(901, y), (1020, y)])
    txt(d, (1032, y), "J1-5  A_HOME", 23, INK, True, "lm")
    wire(d, [(530, y + 46), (530, y + 75), (333, y + 75), (333, y + 104)])
    ground(d, 333, y + 104, "Pro GND")
    wire(d, [(605, y + 46), (705, y + 46), (705, y + 75)])
    ground(d, 705, y + 75, "CTRL GND")
    diode(d, 405, y + 75, "D3 1N4148W; ~5.4 mA at 3.3V")
    txt(d, (92, y + 132), "GP9 high → U3 pulls A_HOME low. Populate R6 only after controller-input test E-18.", 19, WARN)

    d.rounded_rectangle((91, 1218, 1172, 1360), radius=10, fill=PALE, outline="#93bba7", width=2)
    txt(d, (115, 1250), "Two fully isolated domains", 22, GREEN_DARK, True)
    txt(d, (115, 1282), "Controller: J1 +5V / CTRL GND / ENA / AUX0 / A_HOME     •     Toolhead: J2 +3V3 / Pro GND / GP8 / GP10 / GP9", 18, INK)
    txt(d, (115, 1314), "C3: 100 nF from J2 +3V3 to Pro GND. Use INPUT for GP8/GP10; R3/R4 define the state. No 5V may reach a Pro Micro GPIO.", 18, INK)


def draw_layout(d: ImageDraw.ImageDraw) -> None:
    bx, by, bw, bh = 1320, 258, 1000, 564  # Exactly 40.16:22.65 aspect ratio.
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=23, fill=GREEN, outline=GREEN_DARK, width=8)
    # Dimension arrows.
    wire(d, [(bx, by - 60), (bx + bw, by - 60)], 3)
    d.polygon([(bx, by - 60), (bx + 22, by - 70), (bx + 22, by - 50)], fill=INK)
    d.polygon([(bx + bw, by - 60), (bx + bw - 22, by - 70), (bx + bw - 22, by - 50)], fill=INK)
    txt(d, (bx + bw // 2, by - 92), "40.16 mm / 1.581102 in", 25, INK, True, "ma")
    wire(d, [(bx - 112, by), (bx - 112, by + bh)], 3)
    d.polygon([(bx - 112, by), (bx - 122, by + 22), (bx - 102, by + 22)], fill=INK)
    d.polygon([(bx - 112, by + bh), (bx - 122, by + bh - 22), (bx - 102, by + bh - 22)], fill=INK)
    txt(d, (bx - 150, by + bh // 2), "22.65 mm", 22, INK, True, "mm")

    connector(d, bx + 25, by + 166, "left", "J1 controller — 90°", ["+5V", "CTRL GND", "ENA", "AUX0", "A_HOME"])
    connector(d, bx + bw - 109, by + 166, "right", "J2 toolhead — 90°", ["+3V3", "Pro GND", "GP8", "GP10", "GP9"])

    # Three DIP-4 packages arranged along the long axis.
    for x, ref, sub in [(1480, "U1", "M3/M5"), (1745, "U2", "HOME_ARM"), (2010, "U3", "A_HOME")]:
        d.rounded_rectangle((x, by + 150, x + 170, by + 355), radius=8, fill="#202934", outline="#0d141c", width=5)
        d.arc((x + 11, by + 162, x + 47, by + 198), 90, 270, fill="#dfe8ed", width=4)
        for px in (x - 11, x + 181):
            for py in (by + 184, by + 248, by + 312, by + 376):
                d.rounded_rectangle((px, py, px + 20, py + 15), radius=3, fill="#ccd6dd", outline="#6c7b86")
        txt(d, (x + 85, by + 230), ref, 25, "white", True, "ma")
        txt(d, (x + 85, by + 266), "PC817C", 19, "white", anchor="ma")
        txt(d, (x + 85, by + 391), sub, 17, "white", True, "ma")

    # SMD component field.
    parts = [(1514, "R1"), (1594, "D1"), (1674, "R3"), (1754, "C1"),
             (1845, "R2"), (1925, "D2"), (2005, "R4"), (2085, "C2"),
             (2176, "R5"), (2256, "D3")]
    for x, label in parts:
        d.rounded_rectangle((x, by + 445, x + 50, by + 477), radius=4, fill="#e7d6a7", outline="#7f6942", width=2)
        txt(d, (x + 25, by + 492), label, 15, "white", True, "ma")
    d.rounded_rectangle((2023, by + 502, 2087, by + 535), radius=4, fill="#fff6df", outline=GOLD, width=2)
    txt(d, (2055, by + 545), "R6 DNP", 14, "white", True, "ma")
    d.rounded_rectangle((2110, by + 502, 2174, by + 535), radius=4, fill="#d7e9ed", outline="#527c87", width=2)
    txt(d, (2142, by + 545), "C3", 14, "white", True, "ma")
    txt(d, (bx + bw // 2, by + 40), "PCB top view — 40.16 × 22.65 mm fabrication envelope", 20, "white", True, "ma")
    txt(d, (bx + bw // 2, by + 70), "0603 passives / SOD-123 diodes on component side", 19, "white", True, "ma")

    d.rounded_rectangle((1320, 866, 1000 + 1320, 1170), radius=16, fill="white", outline="#b9c5d0", width=3)
    txt(d, (1352, 906), "Fit and build constraints", 28, INK, True)
    constraints = [
        "• 2-layer PCB, 1.6 mm FR-4; board has no mounting holes in this envelope.",
        "• Use JST SM05B-GHS-TB(LF)(SN) 5-pin 1.25 mm side-entry (90°) headers.",
        "• Keep J1 control wires as twisted/shielded pairs; locate module beside Pro Micro.",
        "• R1/R2 target 5.6 mA; R5 targets 5.4 mA. Confirm source/sink current on the bench.",
        "• R6 is deliberately DNP: install only after RP23CNC A-home input is bench-verified.",
        "• This is a placement-feasibility drawing, not Gerbers or a fabrication release."
    ]
    for i, item in enumerate(constraints):
        txt(d, (1360, 956 + i * 36), item, 20, INK)


def main() -> None:
    image = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(image)
    txt(d, (W // 2, 48), "PC817C three-channel isolated interface module — proposed compact layout", 43, INK, True, "ma")
    txt(d, (W // 2, 99), "For RP23CNC ↔ SparkFun Pro Micro RP2350 | Design status: proposed; verify controller terminals and E-18 before wiring", 23, WARN, anchor="ma")
    draw_schematic(d)
    draw_layout(d)
    image.save(OUT, dpi=(300, 300))
    print(OUT)


if __name__ == "__main__":
    main()
