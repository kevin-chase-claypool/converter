"""Monoline text generator tab.

Draws single-stroke Hershey Simplex text (public-domain font data, see
`fonts/NOTICE.md`) as plotter paths, with size, tracking, line spacing,
alignment, and artwork scale.
"""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QPlainTextEdit

from ._hershey import text_polylines
from ._tab_common import GeneratorTab, double_spin, scale_polylines


TITLE = "Text"
ORDER = 70


class TextTab(GeneratorTab):
    NAME = "text"

    def __init__(self, host):
        super().__init__(host)
        content = self.add_group("Text")
        self.text = QPlainTextEdit()
        self.text.setPlainText("HELLO\nPLOTTER")
        self.text.setFixedHeight(70)
        content.addRow("Lines", self.text)
        self.size = double_spin(12, 3, 80, 1, 1, " mm")
        content.addRow("Text size", self.size)
        self.tracking = double_spin(0.4, -2.0, 10.0, 0.2, 2, " mm")
        content.addRow("Tracking", self.tracking)
        self.line_spacing = double_spin(140, 100, 250, 5, 0, " %")
        content.addRow("Line spacing", self.line_spacing)
        self.align = QComboBox()
        self.align.addItem("Left", "left")
        self.align.addItem("Center", "center")
        self.align.addItem("Right", "right")
        content.addRow("Align", self.align)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(10, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 200, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def build_svg(self):
        text = self.text.toPlainText().rstrip("\n")
        if not text.strip():
            raise ValueError("Enter some text to draw.")
        page_w = self.page_w.value()
        margin = self.margin.value()
        size = self.size.value()
        align = self.align.currentData()
        if align == "center":
            origin_x = page_w / 2.0
        elif align == "right":
            origin_x = page_w - margin
        else:
            origin_x = margin
        polylines = text_polylines(
            text,
            origin_x,
            margin + size,
            size,
            tracking_mm=self.tracking.value(),
            line_spacing_pct=self.line_spacing.value(),
            align=align,
        )
        polylines = scale_polylines(
            polylines,
            self.scale_pct.value() / 100.0,
            page_w,
            self.page_h.value(),
        )
        return self.write_result(
            polylines,
            page_w,
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} text strokes.",
        )


def create_tab(host):
    return TextTab(host)
