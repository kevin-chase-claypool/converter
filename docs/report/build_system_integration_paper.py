from __future__ import annotations

import math
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "report" / "System_Integration_Robotics_Paper.md"
OUTPUT = ROOT / "docs" / "report" / "System_Integration_Robotics_Paper.docx"
ASSETS = ROOT / "docs" / "report" / "paper_assets"

NAVY = "#22364D"
BLUE = "#4278A6"
PALE_BLUE = "#EDF3F8"
PALE_GREEN = "#EDF5EC"
PALE_GOLD = "#F7F1E5"
PALE_GRAY = "#F4F6F8"
MID_GRAY = "#6B7480"
DARK = "#20242A"
WHITE = "#FFFFFF"

FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
WORD_BODY_FONT = "Times New Roman"
WORD_HEAD_FONT = "Arial"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = NAVY,
    radius: int = 28,
    width: int = 4,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = NAVY, width: int = 7) -> None:
    if start[0] != end[0] and start[1] != end[1]:
        raise ValueError(f"Arrow must be straight: {start} -> {end}")
    if end[0] < start[0] or end[1] < start[1]:
        raise ValueError(f"Arrow must point east or south: {start} -> {end}")
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = max(24, int(width * 3))
    left = (
        end[0] - head * math.cos(angle - math.pi / 6),
        end[1] - head * math.sin(angle - math.pi / 6),
    )
    right = (
        end[0] - head * math.cos(angle + math.pi / 6),
        end[1] - head * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, left, right], fill=color)


def _center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str = DARK,
    spacing: int = 10,
    max_lines: int | None = None,
) -> None:
    lines = _wrap(draw, text, font, box[2] - box[0] - 40)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
    metrics = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_h = max((m[3] - m[1] for m in metrics), default=font.size)
    total_h = len(lines) * line_h + max(0, len(lines) - 1) * spacing
    y = box[1] + (box[3] - box[1] - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + spacing


def _interface_label(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text(
        (center[0] - width / 2, center[1] - height / 2 - bbox[1]),
        text,
        font=font,
        fill=NAVY,
    )


def create_system_architecture() -> Path:
    img = Image.new("RGB", (2400, 1260), WHITE)
    draw = ImageDraw.Draw(img)
    title_font = _font(62, True)
    box_font = _font(45, True)
    body_font = _font(36)
    label_font = _font(32, True)
    section_font = _font(34, True)

    draw.text((80, 46), "INTERFACES AND SUBSYSTEM OWNERSHIP", font=title_font, fill=NAVY)

    boxes = {
        "operator": (45, 210, 435, 500),
        "host": (645, 210, 1075, 500),
        "motion": (1285, 210, 1715, 500),
        "motion_stage": (1925, 210, 2355, 500),
        "toolhead": (1285, 720, 1715, 1000),
        "result": (1925, 720, 2355, 1000),
    }
    fills = {
        "operator": PALE_GRAY,
        "host": PALE_BLUE,
        "motion": PALE_BLUE,
        "motion_stage": PALE_GREEN,
        "toolhead": PALE_GOLD,
        "result": PALE_GREEN,
    }
    labels = {
        "operator": ("Operator and artwork", "Artwork  |  constraints  |  start and stop"),
        "host": ("Host planning black box", "SVG and settings  |  ordered G-code"),
        "motion": ("Motion control black box", "G-code  |  X Y A planning  |  registration"),
        "motion_stage": ("Motion and actuation", "Gantry and rotating bed  |  X Y A"),
        "toolhead": ("Force toolhead black box", "Seek contact  |  hold force  |  clear"),
        "result": ("Physical result", "Pen  |  paper  |  ink"),
    }
    for key, box in boxes.items():
        _rounded_box(draw, box, fills[key])
        title, body = labels[key]
        _center_text(draw, (box[0] + 20, box[1] + 22, box[2] - 20, box[1] + 155), title, box_font)
        _center_text(draw, (box[0] + 25, box[1] + 165, box[2] - 25, box[3] - 24), body, body_font, MID_GRAY)

    _arrow(draw, (435, 365), (645, 365), width=10)
    _arrow(draw, (1075, 365), (1285, 365), width=10)
    _arrow(draw, (1715, 365), (1925, 365), width=10)
    _arrow(draw, (1500, 500), (1500, 720), width=10)
    _arrow(draw, (2180, 500), (2180, 720), width=10)
    _arrow(draw, (1715, 860), (1925, 860), width=10)

    _interface_label(draw, (540, 315), "artwork", label_font)
    _interface_label(draw, (1180, 315), "G-code", label_font)
    _interface_label(draw, (1820, 315), "STEP / DIR", label_font)
    _interface_label(draw, (1585, 600), "M3 / M5", label_font)
    _interface_label(draw, (2045, 600), "ready / fault", label_font)
    _interface_label(draw, (1820, 805), "force", label_font)

    bottom_y = 1070
    draw.text((55, 1028), "CROSS CUTTING SYSTEMS", font=section_font, fill=NAVY)
    support = [
        ((45, bottom_y, 750, 1225), "Registration and feedback", "Home switches  |  TMAG5273  |  load cell  |  readiness"),
        ((790, bottom_y, 1495, 1225), "Power and safety", "Protected rails  |  opto isolation  |  E-stop  |  bounded force and timeouts"),
        ((1535, bottom_y, 2355, 1225), "Structure and cabling", "Frame  |  drag chains  |  strain relief  |  protective earth"),
    ]
    for box, title, body in support:
        _rounded_box(draw, box, PALE_GRAY, outline=MID_GRAY, radius=22, width=3)
        draw.text((box[0] + 28, box[1] + 25), title, font=section_font, fill=NAVY)
        _center_text(draw, (box[0] + 22, box[1] + 70, box[2] - 20, box[3] - 18), body, body_font, MID_GRAY)

    path = ASSETS / "figure_01_system_architecture.png"
    img.save(path, dpi=(300, 300))
    return path


def create_machine_overview() -> Path:
    source = ROOT / "docs" / "report" / "Theta_Pen_Plotter_Summer_Progress_Update" / "slide-1.png"
    image = Image.open(source).convert("RGB")
    image = image.crop((0, 0, image.width, int(image.height * 0.84)))
    image = ImageOps.expand(image, border=18, fill=WHITE)
    path = ASSETS / "cover_machine_overview.png"
    image.save(path, dpi=(300, 300))
    return path


def create_commissioning_sequence() -> Path:
    img = Image.new("RGB", (2000, 1120), WHITE)
    draw = ImageDraw.Draw(img)
    title_font = _font(52, True)
    step_font = _font(39, True)
    test_font = _font(26, True)
    body_font = _font(32)

    draw.text((80, 55), "DEPENDENCY ORDER FOR INTEGRATION TESTS", font=title_font, fill=NAVY)
    steps = [
        ("1", "Electrical integrity", "Inspect, isolate, verify polarity", "E-03  |  E-14  |  E-19"),
        ("2", "Controller and axes", "Verify commands, scale, and return", "F-03  |  M-03  |  M-05"),
        ("3", "Homing and registration", "Establish machine and bed frames", "M-07  |  P112  |  P113"),
        ("4", "Toolhead force behavior", "Calibrate, seek, hold, and clear", "E-09C  |  E-09F  |  T-01H"),
        ("5", "Tool state handshake", "Require a fresh physical completion", "F-05  |  F-05A"),
        ("6", "Physical accuracy", "Measure the sheet and close the loop", "M-12  |  M-13"),
    ]
    positions = [(70, 175), (1010, 175), (70, 485), (1010, 485), (70, 795), (1010, 795)]
    card_w = 920
    card_h = 245
    number_font = _font(50, True)
    for index, ((number, title, body, tests), (x1, y1)) in enumerate(zip(steps, positions)):
        box = (x1, y1, x1 + card_w, y1 + card_h)
        fill = PALE_BLUE if index % 2 == 0 else PALE_GRAY
        _rounded_box(draw, box, fill)
        circle = (x1 - 2, y1 + 62, x1 + 122, y1 + 186)
        draw.ellipse(circle, fill=NAVY, outline=NAVY, width=4)
        bbox = draw.textbbox((0, 0), number, font=number_font)
        draw.text(
            (
                circle[0] + (circle[2] - circle[0] - (bbox[2] - bbox[0])) / 2,
                circle[1] + (circle[3] - circle[1] - (bbox[3] - bbox[1])) / 2 - 6,
            ),
            number,
            font=number_font,
            fill=WHITE,
        )
        draw.text((x1 + 145, y1 + 30), title, font=step_font, fill=NAVY)
        draw.text((x1 + 145, y1 + 90), body, font=body_font, fill=DARK)
        draw.text((x1 + 145, y1 + 151), tests, font=test_font, fill=BLUE)

    _arrow(draw, (990, 298), (1008, 298), color=MID_GRAY, width=5)
    _arrow(draw, (540, 420), (540, 483), color=MID_GRAY, width=5)
    _arrow(draw, (540, 730), (540, 793), color=MID_GRAY, width=5)

    path = ASSETS / "figure_02_commissioning_sequence.png"
    img.save(path, dpi=(300, 300))
    return path


def create_registration_artifact() -> Path:
    source = (
        ROOT
        / "docs"
        / "report"
        / "lab-notes"
        / "assets"
        / "2026-10-23-m-12-bed-compensation-frame-error.jpg"
    )
    image = Image.open(source).convert("RGB")
    image.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
    image = ImageOps.expand(image, border=16, fill=WHITE)
    path = ASSETS / "figure_03_registration_artifact.jpg"
    image.save(path, quality=92, subsampling=0, dpi=(300, 300))
    return path


def create_force_calibration() -> Path:
    base = (
        ROOT
        / "firmware"
        / "pen_pressure"
        / "e07d_cs1238_known_mass_calibration"
        / "pc_logger"
        / "results"
        / "run_2026-09-22_09-10-46"
    )
    curve = Image.open(base / "calibration_curve.png").convert("RGB")
    curve = ImageOps.expand(curve, border=18, fill=WHITE)
    path = ASSETS / "figure_04_force_calibration.png"
    curve.save(path, dpi=(300, 300))
    return path


def create_error_chart() -> Path:
    img = Image.new("RGB", (1900, 1050), WHITE)
    draw = ImageDraw.Draw(img)
    title_font = _font(46, True)
    label_font = _font(30)
    tick_font = _font(28)
    legend_font = _font(27)

    draw.text((95, 48), "POST REPAIR BED ERROR REDUCTION", font=title_font, fill=NAVY)
    left, top, right, bottom = 165, 175, 1780, 870
    y_max = 3.2

    def yp(value: float) -> int:
        return int(bottom - (value / y_max) * (bottom - top))

    for tick in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        y = yp(tick)
        draw.line((left, y, right, y), fill="#D8DEE5", width=2)
        draw.text((70, y - 17), f"{tick:.1f}", font=tick_font, fill=MID_GRAY)

    draw.line((left, top, left, bottom), fill=NAVY, width=4)
    draw.line((left, bottom, right, bottom), fill=NAVY, width=4)
    draw.text((25, 105), "Error mm", font=label_font, fill=NAVY)

    groups = [
        ("Overall RMS", 1.744, 0.218),
        ("Maximum", 2.965, 0.591),
    ]
    group_centers = [570, 1300]
    bar_w = 250
    for (label, baseline, compensated), cx in zip(groups, group_centers):
        for offset, value, color in (
            (-150, baseline, "#8EA2B5"),
            (150, compensated, BLUE),
        ):
            x1 = cx + offset - bar_w // 2
            x2 = cx + offset + bar_w // 2
            y1 = yp(value)
            draw.rounded_rectangle((x1, y1, x2, bottom - 2), radius=8, fill=color)
            draw.text((x1 + 45, y1 - 44), f"{value:.3f}", font=tick_font, fill=DARK)
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((cx - (bbox[2] - bbox[0]) / 2, bottom + 35), label, font=label_font, fill=DARK)

    draw.rounded_rectangle((1260, 60, 1300, 100), radius=4, fill="#8EA2B5")
    draw.text((1315, 58), "Baseline", font=legend_font, fill=DARK)
    draw.rounded_rectangle((1515, 60, 1555, 100), radius=4, fill=BLUE)
    draw.text((1570, 58), "Compensated", font=legend_font, fill=DARK)

    path = ASSETS / "figure_05_error_improvement.png"
    img.save(path, dpi=(300, 300))
    return path


def create_completed_plot() -> Path:
    source = (
        ROOT
        / "docs"
        / "report"
        / "lab-notes"
        / "assets"
        / "2026-10-25-m-13-full-sheet-wave-matrix.jpg"
    )
    image = Image.open(source).convert("RGB")
    image.thumbnail((1000, 1300), Image.Resampling.LANCZOS)
    image = ImageOps.expand(image, border=16, fill=WHITE)
    path = ASSETS / "figure_06_completed_plot.jpg"
    image.save(path, quality=92, subsampling=0, dpi=(300, 300))
    return path


def create_figures() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    create_system_architecture()
    create_machine_overview()
    create_commissioning_sequence()
    create_registration_artifact()
    create_force_calibration()
    create_error_chart()
    create_completed_plot()


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for match in re.finditer(r"<!--([A-Z]+):\s*(.*?)-->", text):
        metadata[match.group(1)] = match.group(2).strip()
    return metadata


def set_cell_border(cell, color: str = "D9D9D9", size: str = "6") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top: int = 90, start: int = 100, bottom: int = 90, end: int = 100) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_row_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)


def set_inline_alt(inline_shape, title: str, description: str) -> None:
    doc_pr = inline_shape._inline.docPr
    doc_pr.set("title", title)
    doc_pr.set("descr", description)


def set_run_font(run, name: str, size: float | None = None, bold: bool | None = None, color: str = "000000") -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color.replace("#", "").upper())


def clear_paragraph_borders(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    borders = p_pr.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        p_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "between", "bar"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "nil")


def add_inline_markup(paragraph, text: str, base_size: float = 11.0) -> None:
    pattern = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")
    cursor = 0
    for match in pattern.finditer(text):
        if match.start() > cursor:
            run = paragraph.add_run(text[cursor:match.start()])
            set_run_font(run, WORD_BODY_FONT, base_size)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, WORD_BODY_FONT, base_size, bold=True)
        elif token.startswith("*"):
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, WORD_BODY_FONT, base_size)
            run.italic = True
        else:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, "Consolas", base_size - 0.5)
        cursor = match.end()
    if cursor < len(text):
        run = paragraph.add_run(text[cursor:])
        set_run_font(run, WORD_BODY_FONT, base_size)


def configure_document(doc: Document, metadata: dict[str, str]) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.78)
    section.bottom_margin = Inches(0.78)
    section.left_margin = Inches(0.88)
    section.right_margin = Inches(0.88)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.38)
    section.different_first_page_header_footer = True

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = header.add_run("Systems Integration in Robotics")
    set_run_font(run, WORD_HEAD_FONT, 8.5, False, "000000")

    add_page_number(section.footer.paragraphs[0])

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = WORD_BODY_FONT
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    normal._element.rPr.rFonts.set(qn("w:ascii"), WORD_BODY_FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), WORD_BODY_FONT)

    for name, size in (("Title", 24), ("Subtitle", 13.5)):
        style = styles[name]
        style.font.name = WORD_HEAD_FONT
        style.font.size = Pt(size)
        style.font.bold = name == "Title"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style._element.rPr.rFonts.set(qn("w:ascii"), WORD_HEAD_FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), WORD_HEAD_FONT)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style.paragraph_format.space_before = Pt(8 if name == "Title" else 0)
        style.paragraph_format.space_after = Pt(8 if name == "Title" else 0)

    for name, size, before, after in (
        ("Heading 1", 16, 16, 7),
        ("Heading 2", 13, 12, 5),
        ("Heading 3", 11.5, 10, 4),
    ):
        style = styles[name]
        style.font.name = WORD_HEAD_FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style._element.rPr.rFonts.set(qn("w:ascii"), WORD_HEAD_FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), WORD_HEAD_FONT)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.line_spacing = 1.0

    for style_name in ("List Bullet",):
        style = styles[style_name]
        style.font.name = WORD_BODY_FONT
        style.font.size = Pt(11)
        style.paragraph_format.line_spacing = 1.12
        style.paragraph_format.space_after = Pt(2)

    props = doc.core_properties
    props.title = metadata.get("TITLE", "System Integration Paper")
    props.subject = metadata.get("SUBTITLE", "Systems Integration in Robotics")
    props.author = metadata.get("AUTHOR", "")
    props.keywords = metadata.get("KEYWORDS", "")
    props.comments = "Final course paper generated from the repository evidence record."


def add_title_page(doc: Document, metadata: dict[str, str]) -> None:
    for _ in range(4):
        doc.add_paragraph()
    course = doc.add_paragraph()
    course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = course.add_run(metadata.get("COURSE", "Systems Integration in Robotics"))
    set_run_font(run, WORD_HEAD_FONT, 10.5, True, "000000")

    title_p = doc.add_paragraph(style="Title")
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(8)
    title_p.paragraph_format.space_after = Pt(8)
    clear_paragraph_borders(title_p)
    title_run = title_p.add_run(metadata.get("TITLE", ""))
    set_run_font(title_run, WORD_HEAD_FONT, 24, True, "000000")

    subtitle_p = doc.add_paragraph(style="Subtitle")
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    clear_paragraph_borders(subtitle_p)
    title_run = subtitle_p.add_run(metadata.get("SUBTITLE", ""))
    set_run_font(title_run, WORD_HEAD_FONT, 13.5, False, "000000")

    hero_value = metadata.get("HERO", "")
    hero = ROOT / hero_value if hero_value else None
    if hero and hero.exists():
        image_p = doc.add_paragraph()
        image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_p.paragraph_format.space_before = Pt(16)
        image_p.paragraph_format.space_after = Pt(8)
        inline = image_p.add_run().add_picture(str(hero), width=Inches(6.85))
        set_inline_alt(
            inline,
            "Conceptual CAD view of the plotter",
            "Rotating circular bed, XY gantry, cable chain, and force-controlled toolhead.",
        )

    for _ in range(3):
        doc.add_paragraph()
    author = doc.add_paragraph()
    author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = author.add_run(metadata.get("AUTHOR", ""))
    set_run_font(run, WORD_HEAD_FONT, 12, True, "000000")

    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run(metadata.get("DATE", ""))
    set_run_font(run, WORD_HEAD_FONT, 10.5, False, "000000")

    doc.add_page_break()


def add_figure(doc: Document, image: Path, caption: str, width: float, number: int) -> None:
    if not image.exists():
        raise FileNotFoundError(f"Missing figure: {image}")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    inline = p.add_run().add_picture(str(image), width=Inches(width))
    set_inline_alt(inline, caption.split(".")[0], caption)

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    number_run = cap.add_run(f"Figure {number}. ")
    set_run_font(number_run, WORD_BODY_FONT, 9.0, True, "4D5560")
    run = cap.add_run(caption)
    set_run_font(run, WORD_BODY_FONT, 9.0, False, "4D5560")
    run.italic = True


def add_table(doc: Document, caption: str, widths: list[float], rows: list[list[str]], number: int) -> None:
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cap.paragraph_format.keep_with_next = True
    cap.paragraph_format.space_before = Pt(7)
    cap.paragraph_format.space_after = Pt(5)
    number_run = cap.add_run(f"Table {number}. ")
    set_run_font(number_run, WORD_HEAD_FONT, 10, True, NAVY)
    run = cap.add_run(caption)
    set_run_font(run, WORD_HEAD_FONT, 10, True, NAVY)

    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    total_width = sum(widths)
    for col_idx, width in enumerate(widths):
        for row_idx in range(len(rows)):
            cell = table.cell(row_idx, col_idx)
            cell.width = Inches(width)
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    for row_idx, row_values in enumerate(rows):
        row = table.rows[row_idx]
        set_row_cant_split(row)
        if row_idx == 0:
            set_repeat_table_header(row)
        for col_idx, value in enumerate(row_values):
            cell = row.cells[col_idx]
            if row_idx == 0:
                set_cell_shading(cell, NAVY)
            elif row_idx % 2 == 0:
                set_cell_shading(cell, "F3F6F9")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = paragraph.add_run(value.strip())
            set_run_font(
                run,
                WORD_HEAD_FONT if row_idx == 0 else WORD_BODY_FONT,
                8.5 if row_idx > 0 else 8.75,
                row_idx == 0,
                "FFFFFF" if row_idx == 0 else "111111",
            )

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)


def parse_table_block(lines: list[str], start: int) -> tuple[str, list[float], list[list[str]], int]:
    header = lines[start].strip()
    parts = [part.strip() for part in header[len("TABLE:") :].split("|")]
    caption = parts[0]
    widths = [float(value.strip()) for value in parts[1].split(",")] if len(parts) > 1 else []
    rows: list[list[str]] = []
    idx = start + 1
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        raw = lines[idx].strip().strip("|")
        cells = [cell.strip() for cell in raw.split("|")]
        if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            rows.append(cells)
        idx += 1
    if not widths:
        widths = [6.6 / len(rows[0])] * len(rows[0])
    return caption, widths, rows, idx


def add_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    add_inline_markup(p, text)


def add_reference(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.32)
    p.paragraph_format.first_line_indent = Inches(-0.32)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(4)
    add_inline_markup(p, text, base_size=9.5)


def build_document(metadata: dict[str, str], body_text: str) -> None:
    doc = Document()
    configure_document(doc, metadata)
    add_title_page(doc, metadata)

    lines = body_text.splitlines()
    idx = 0
    figure_number = 0
    table_number = 0
    while idx < len(lines):
        line = lines[idx].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            idx += 1
            continue
        if stripped == "PAGEBREAK":
            doc.add_page_break()
            idx += 1
            continue
        if stripped.startswith("FIGURE:"):
            payload = stripped[len("FIGURE:") :]
            parts = [part.strip() for part in payload.split("|")]
            image = ROOT / parts[0]
            caption = parts[1]
            width = float(parts[2]) if len(parts) > 2 else 5.8
            figure_number += 1
            add_figure(doc, image, caption, width, figure_number)
            idx += 1
            continue
        if stripped.startswith("TABLE:"):
            caption, widths, rows, idx = parse_table_block(lines, idx)
            table_number += 1
            add_table(doc, caption, widths, rows, table_number)
            continue
        if stripped.startswith("# "):
            heading = stripped[2:].strip()
            p = doc.add_paragraph(style="Heading 1")
            if doc.paragraphs and heading in {"Appendix A Evidence Register", "Appendix B Relationship to ABET Student Outcomes", "Appendix C Reproducibility and Configuration Boundary"}:
                p.paragraph_format.page_break_before = True
            run = p.add_run(heading)
            set_run_font(run, WORD_HEAD_FONT, 16, True)
            idx += 1
            continue
        if stripped.startswith("## "):
            p = doc.add_paragraph(style="Heading 2")
            run = p.add_run(stripped[3:].strip())
            set_run_font(run, WORD_HEAD_FONT, 13, True)
            idx += 1
            continue
        if stripped.startswith("### "):
            p = doc.add_paragraph(style="Heading 3")
            run = p.add_run(stripped[4:].strip())
            set_run_font(run, WORD_HEAD_FONT, 11.5, True)
            idx += 1
            continue
        if stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline_markup(p, stripped[2:])
            idx += 1
            continue
        if stripped.startswith("REF:"):
            add_reference(doc, stripped[4:].strip())
            idx += 1
            continue

        paragraph_lines = [stripped]
        idx += 1
        while idx < len(lines):
            nxt = lines[idx].strip()
            if (
                not nxt
                or nxt == "PAGEBREAK"
                or nxt.startswith("#")
                or nxt.startswith("FIGURE:")
                or nxt.startswith("TABLE:")
                or nxt.startswith("- ")
                or nxt.startswith("REF:")
                or nxt.startswith("<!--")
            ):
                break
            paragraph_lines.append(nxt)
            idx += 1
        add_paragraph(doc, " ".join(paragraph_lines))

    doc.save(OUTPUT)


def main() -> None:
    create_figures()
    text = SOURCE.read_text(encoding="utf-8")
    metadata = parse_metadata(text)
    build_document(metadata, text)
    print(OUTPUT)


if __name__ == "__main__":
    main()
